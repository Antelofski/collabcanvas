"""The three demo checks use recorded events, not inferred conversation."""
from copy import deepcopy
import time,unittest
import server
import test_workflow as _wf
from progress_rules import suggested_rules

class CollaborationChecks(unittest.TestCase):
 setUpClass=classmethod(_wf.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_wf.WorkflowIntegration.tearDownClass.__func__)
 tearDown=_wf.WorkflowIntegration.tearDown
 req=_wf.WorkflowIntegration.req
 def setUp(self):
  _wf.WorkflowIntegration.setUp(self)
  server.STATE['plan']['progress']={'collaborationChecks':True,'rules':suggested_rules(server.STATE['plan'])}
 def check(self,rule):
  _,h=self.req('/api/host');return h['progress']['teams'][0]['collaboration'][rule]
 def apply(self,pattern):
  _,p=self.req('/api/host/adaptive-preview',dict(group=0,pattern=pattern,targets=[self.people[1]['id']]))
  _,r=self.req('/api/host/adaptive-apply',dict(p,note='I inspected the recorded evidence.'))
  return r['change']
 def question(self,text='Does this comparison show political power?'):
  reader=self.people[1];server.STATE.setdefault('artifacts',{})[reader['id']]={'question':text,'questionSent':True,'submitted':{'discuss':True},'version':1}
 def test_no_missing_submission_alert_before_checkpoint_without_request(self):
  server.STATE['plan']['live'].update(started=True,phaseId='discuss',startedAt=time.time(),paused=False)
  self.assertEqual(self.check('role-work')['status'],'collecting')
  self.req('/api/help',dict(requestKind='difficulty',text='I need smaller steps.'),self.people[1])
  self.assertEqual(self.check('role-work')['status'],'attention')
 def test_due_missing_contribution_names_targets_without_labelling_disengagement(self):
  server.STATE['plan']['live'].update(started=True,phaseId='discuss',startedAt=time.time()-7*60,paused=False)
  for p in self.people[:4]:server.STATE['responses'][p['id']]={'discuss:submitted':p['slot']!=1}
  c=self.check('role-work');self.assertEqual(c['status'],'attention');self.assertEqual(c['targets'],[self.people[1]['id']]);self.assertNotIn('disengag',str(c))
 def test_peer_question_waits_for_final_stage(self):
  self.question();server.STATE['plan']['live'].update(started=True,phaseId='discuss')
  self.assertEqual(self.check('peer-use')['status'],'collecting')
  server.STATE['plan']['live']['phaseId']='revise'
  self.assertEqual(self.check('peer-use')['status'],'attention')
 def test_peer_reply_links_original_question_and_does_not_resolve_changed_question(self):
  self.question();server.STATE['plan']['live'].update(started=True,phaseId='revise')
  c=self.apply('written-exchange');self.assertIn('sourceQuestion',c['spec'])
  status,_=self.req('/api/adaptive/response',dict(id=c['id'],version=0,values={'idea':'Only the number of people.','evidence':'The legend counts people.'},shared=True),self.people[2]);self.assertEqual(status,200)
  self.assertEqual(self.check('peer-use')['status'],'checked')
  self.question('What is the unit in the first frame?')
  self.assertEqual(self.check('peer-use')['status'],'attention')
 def test_matching_answers_need_recorded_contrast_and_peer_check(self):
  for p in self.people[:4]:self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='filter',reason='The labels change who is counted.'),p)
  self.assertEqual(self.check('answer-pattern')['status'],'attention')
  c=self.apply('reason-check');values={'idea':'The subset can change without a population decrease.','evidence':'The frame labels describe population groups.'}
  self.req('/api/adaptive/response',dict(id=c['id'],version=0,values=values,shared=True),self.people[0])
  self.assertEqual(self.check('answer-pattern')['status'],'attention')
  self.req('/api/adaptive/response',dict(id=c['id'],version=0,values=values,shared=True,replyTo=self.people[0]['id'],reply='Your reason distinguishes population size from the counted subset.'),self.people[1])
  self.assertEqual(self.check('answer-pattern')['status'],'checked')
 def test_demo_data_cannot_be_loaded_into_formal_class(self):
  before=deepcopy(server.STATE);self.assertEqual(self.req('/api/host/tutorial-examples',dict(kind='collaboration-evidence'))[0],400);self.assertEqual(server.STATE,before)
if __name__=='__main__':unittest.main()
