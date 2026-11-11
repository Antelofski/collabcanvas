"""Independent tutorial storage and explicitly simulated classmates."""
import unittest,tempfile,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from copy import deepcopy
import server
import test_workflow as _workflow
from tutorial_backend import launch_tutorial, stop_practice

FAKE_SERVER="""
import json,sys
from http.server import BaseHTTPRequestHandler,HTTPServer
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  body=json.dumps({'tutorialSession':sys.argv[1]=='practice'}).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*a):pass
s=HTTPServer(('127.0.0.1',0),H);print(s.server_port,flush=True);s.serve_forever()
"""
def fake_server(kind):
 child=subprocess.Popen([sys.executable,'-c',FAKE_SERVER,kind],stdout=subprocess.PIPE,text=True);port=int(child.stdout.readline())
 return child,dict(pid=child.pid,port=port,admin='token')

class TutorialIntegration(unittest.TestCase):
 setUpClass=classmethod(_workflow.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_workflow.WorkflowIntegration.tearDownClass.__func__)
 setUp=_workflow.WorkflowIntegration.setUp
 tearDown=_workflow.WorkflowIntegration.tearDown
 req=_workflow.WorkflowIntegration.req
 def prepare(self):
  server.STATE['tutorialSession']=True;server.STATE['tutorialReturn']='http://127.0.0.1:8931/'
  self.people[0].update(claimed=True,name='Practice instructor')
  self.req('/api/studio/group',dict(section='opening',phaseId='read',version=0,record={'text':'The story filters people.'}),self.people[0])
 def test_restarting_stops_only_a_practice_classroom_it_started(self):
  practice,info=fake_server('practice');formal,other=fake_server('formal')
  try:
   self.assertFalse(stop_practice(other));self.assertFalse(stop_practice({**info,'pid':os.getpid()}));self.assertFalse(stop_practice({k:v for k,v in info.items() if k!='pid'}))
   self.assertIsNone(formal.poll());self.assertIsNone(practice.poll())
   self.assertTrue(stop_practice(info));self.assertIsNotNone(practice.wait(timeout=5));self.assertIsNone(formal.poll())
   self.assertFalse(stop_practice(info))
  finally:
   for child in (practice,formal):
    if child.poll() is None:child.kill()
    child.wait();child.stdout.close()
 def test_example_endpoint_rejects_real_classrooms(self):
  before=deepcopy(server.STATE)
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'peers'})[0],400)
  self.assertEqual(server.STATE,before)
 def test_framework_evidence_is_scoped_and_creates_a_real_rule_alert(self):
  server.STATE['tutorialSession']=True;self.people[0]['claimed']=True
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'framework-evidence'})[0],200)
  _,h=self.req('/api/host');e=h['progress']['teams'][0]
  self.assertEqual((e['submitted'],e['answered'],e['wrong']),(4,4,2))
  self.assertEqual(next(s for s in e['signals']if s['id']=='reading-check')['status'],'attention')
  self.assertEqual(h['progress']['teams'][1]['answered'],0)
  self.assertNotIn(self.people[4]['id'],server.STATE['artifacts'])
 def test_framework_recheck_requires_applied_support_and_preserves_initial_answers(self):
  server.STATE['tutorialSession']=True;self.people[0]['claimed']=True
  self.req('/api/host/tutorial-examples',{'kind':'framework-evidence'})
  before=deepcopy(server.STATE['progressRecords']['answers'])
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'framework-followups'})[0],400)
  self.req('/api/host/progress-support',{'kind':'support','group':0})
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'framework-followups'})[0],200)
  for pid,row in before.items():self.assertEqual(server.STATE['progressRecords']['answers'][pid]['initial'],row['initial'])
  _,h=self.req('/api/host');self.assertEqual(h['progress']['teams'][0]['followupCorrect'],2)
 def test_peers_require_claim_and_shared_input(self):
  server.STATE['tutorialSession']=True
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'peers'})[0],400)
  self.people[0]['claimed']=True
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'peers'})[0],400)
 def test_mock_peers_preserve_own_work_and_other_teams(self):
  self.prepare();own=self.people[0]
  self.req('/api/studio/save',dict(phaseId='discuss',version=0,artifact={'reflection':'My own draft'}),own)
  before=deepcopy(server.STATE['artifacts'][own['id']]);other=deepcopy(self.people[4:])
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'peers'})[0],200)
  self.assertEqual(server.STATE['artifacts'][own['id']],before);self.assertEqual(self.people[4:],other)
  for p in self.people[1:4]:self.assertIn('(example)',p['name']);self.assertTrue(server.STATE['responses'][p['id']]['discuss:submitted'])
  self.assertNotIn(self.people[4]['id'],server.STATE['artifacts'])
 def test_followup_examples_do_not_answer_for_the_user(self):
  self.prepare();own=self.people[0]
  self.req('/api/progress/answer',dict(kind='initial',answer='time',reason='Practice initial answer',phaseId='discuss'),own)
  self.req('/api/host/tutorial-examples',{'kind':'peers'});self.req('/api/host/progress-support',{'kind':'support','group':0})
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'followups'})[0],200)
  self.assertNotIn('followup',server.STATE['progressRecords']['answers'][own['id']])
  self.assertTrue(server.STATE['progressRecords']['answers'][self.people[1]['id']]['followup']['correct'])
 def test_new_activity_keeps_practice_isolation(self):
  self.prepare();self.assertEqual(self.req('/api/host/new',{})[0],200)
  self.assertTrue(server.STATE['tutorialSession']);self.assertEqual(server.STATE['tutorialReturn'],'http://127.0.0.1:8931/')
 def test_launcher_uses_independent_storage_and_new_credentials(self):
  before=deepcopy(server.STATE)
  with tempfile.TemporaryDirectory() as tmp:
   result=launch_tutorial(tmp,'http://127.0.0.1:8931/',spawn=False);practice=json.loads(Path(result['state']).read_text())
   self.assertTrue(practice['tutorialSession']);self.assertFalse(practice['plan']['planned']);self.assertEqual(practice['plan']['groupSize'],4)
   self.assertNotEqual(practice['admin'],server.STATE['admin']);self.assertEqual(server.STATE,before)

 def test_restarting_creates_empty_class_without_replacing_previous_run(self):
  with tempfile.TemporaryDirectory() as tmp:
   first=launch_tutorial(tmp,'http://127.0.0.1:8931/',reset=True,spawn=False)
   path=Path(first['state']);original=json.loads(path.read_text());original['plan']['planned']=True;original['responses']={'example':{'read:submitted':True}};path.write_text(json.dumps(original))
   second=launch_tutorial(tmp,'http://127.0.0.1:8931/',reset=True,spawn=False);fresh=json.loads(Path(second['state']).read_text())
   self.assertNotEqual(first['url'],second['url']);self.assertFalse(fresh['plan']['planned']);self.assertFalse(fresh['responses']);self.assertEqual(json.loads(path.read_text()),original)
