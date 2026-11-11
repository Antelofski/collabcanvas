"""Checks sharing, role edits, and collision handling on an isolated class."""
import concurrent.futures, importlib.util, json, sys, tempfile, threading, unittest, urllib.error, urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer

sys.path.insert(0,str(Path(__file__).parent))
import server
from model import tasks_for

class ActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();server.initialize(Path(cls.temp.name)/'initial.json')
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.base='http://127.0.0.1:'+str(cls.http.server_port);server.BASE=cls.base
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()
    def setUp(self):
        server.initialize(Path(self.temp.name)/(self.id().split('.')[-1]+'.json'));self.admin=server.STATE['admin'];self.people=list(server.STATE['people'])
        server.STATE['plan']['planned']=True;server.STATE['deployment']=dict(active=True,deployedAt=1);server.save()
    def request(self,path,body=None,host=False):
        r=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'X-Admin-Token':self.admin} if host else {})})
        try:
            with urllib.request.urlopen(r) as response:
                b=response.read();return response.status,json.loads(b) if response.headers['Content-Type'].startswith('application/json') else b
        except urllib.error.HTTPError as e:
            raw=e.read()
            return e.code,json.loads(raw) if e.headers.get('Content-Type','').startswith('application/json') else raw
    def state(self,i=0):return self.request('/api/state?token='+self.people[i]['token'])[1]
    def plan(self,fn):
        p=json.loads(json.dumps(server.STATE['plan']));fn(p);return self.request('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']},True)
    def answer(self,i=0,submitted=True):return self.request('/api/response?token='+self.people[i]['token'],{'phaseId':'read','answers':{'task-'+str(i+1):'Reading '+str(i)},'submitted':submitted})
    def test_host_is_separate_from_learner_access(self):
        self.assertEqual(self.request('/api/host')[0],403);self.assertEqual(self.request('/api/host',host=True)[0],200)
        self.assertEqual(self.request('/runtime/state.json')[0],404)
    def test_draft_entry_is_closed_but_teacher_preview_works(self):
        self.request('/api/host/new',{},True)
        self.assertFalse(server.STATE['plan']['planned'])
        self.assertEqual(server.STATE['plan']['intent'],'')
        self.assertEqual(server.STATE['plan']['title'],'Untitled activity')
        person=server.STATE['people'][0]
        self.assertEqual(self.request('/api/join?code='+server.STATE['code'])[0],403)
        self.assertEqual(self.request('/api/state?token='+person['token'])[0],403)
        self.assertEqual(self.request('/api/state?preview=1&person='+person['id'],host=True)[0],200)
        self.assertEqual(self.request('/api/qr?target='+self.base+'/join',host=True)[0],409)
        self.assertEqual(self.request('/api/host/live',{'command':'start'},True)[0],400)
    def test_deployment_opens_entry_without_starting_class(self):
        server.STATE['deployment']['active']=False
        code,_=self.request('/api/host/deploy',{'planRev':server.STATE['planRev']},True)
        self.assertEqual(code,200)
        self.assertTrue(server.STATE['deployment']['active'])
        self.assertFalse(server.STATE['plan']['live']['started'])
        self.assertEqual(self.request('/api/join?code='+server.STATE['code'])[0],200)
        self.assertEqual(self.request('/api/state?token='+self.people[0]['token'])[0],200)
    def test_deployment_requires_generated_assigned_in_budget_pages(self):
        server.STATE['deployment']['active']=False
        for field,value,match in [('planned',False,'Generate'),('budget',1,'budget')]:
            original=server.STATE['plan'][field];server.STATE['plan'][field]=value
            status,result=self.request('/api/host/deploy',{'planRev':server.STATE['planRev']},True)
            self.assertEqual(status,400);self.assertIn(match,result['error']);server.STATE['plan'][field]=original
        server.STATE['plan']['tasks'][2]['assignees']=[]
        status,result=self.request('/api/host/deploy',{'planRev':server.STATE['planRev']},True)
        self.assertEqual(status,400);self.assertIn('Learner C',result['error'])
        self.assertEqual(self.request('/api/host/deploy',{'planRev':0},True)[0],409)
    def test_new_canvas_archives_and_restores_existing_work(self):
        self.answer(0);old_code=server.STATE['code'];old_id=self.people[0]['id']
        self.assertEqual(self.request('/api/host/new',{},True)[0],200)
        self.assertTrue(Path(server.STATE['previousActivity']).is_file())
        self.assertNotEqual(server.STATE['code'],old_code);self.assertEqual(server.STATE['responses'],{})
        self.assertEqual(self.request('/api/host/restore',{},True)[0],200)
        self.assertEqual(server.STATE['code'],old_code)
        self.assertEqual(server.STATE['responses'][old_id]['read:task-1'],'Reading 0')
    def test_annotation_assets_are_public_but_runtime_stays_private(self):
        for asset in ['rough.js','rough-notation.iife.js']:
            code, body = self.request('/assets/annotations/'+asset)
            self.assertEqual(code,200)
            self.assertGreater(len(body),1000)
        self.assertEqual(self.request('/vendor/qrcode/main.py')[0],404)
        self.assertEqual(self.request('/runtime/state.json')[0],404)
    def test_sharing_gate_is_enforced_by_server(self):
        self.answer(1);self.assertNotIn(self.people[1]['id'],self.state()['responses'])
        self.answer(0);self.assertIn(self.people[1]['id'],self.state()['responses'])
    def test_everyone_gate_waits_for_the_group(self):
        self.plan(lambda p:p['interaction'].update(visibility='after_group'))
        self.answer(0);self.answer(1);self.assertFalse(self.state()['peerVisible'])
        self.answer(2);self.assertTrue(self.state()['peerVisible'])
    def test_reassignment_retains_responses_and_updates_permissions(self):
        self.answer(0);self.plan(lambda p:p['tasks'][0].update(assignees=[1]))
        self.assertEqual(self.state()['responses'][self.people[0]['id']]['read:task-1'],'Reading 0')
        self.assertEqual(self.answer(0)[0],400)
    def test_group_save_detects_a_concurrent_edit(self):
        self.answer(0);self.request('/api/host/live',{'command':'stage','phaseId':'discuss'},True)
        path='/api/discussion?token='+self.people[0]['token'];body={'kind':'answer','text':'First explanation','version':0}
        self.assertEqual(self.request(path,body)[0],200)
        self.assertEqual(self.request(path,{**body,'text':'Stale overwrite'})[0],409)
        self.assertEqual(self.state()['groupAnswer']['text'],'First explanation')
    def test_join_claim_is_atomic(self):
        b={'code':server.STATE['code'],'name':'Test learner','person':self.people[0]['id']}
        with concurrent.futures.ThreadPoolExecutor(2) as pool:codes=list(pool.map(lambda _:self.request('/api/join',b)[0],range(2)))
        self.assertEqual(sorted(codes),[200,409])
    def test_reference_is_not_sent_before_release(self):
        self.assertEqual(self.state()['plan']['interaction']['reference'],'')
        self.request('/api/host/live',{'command':'reveal'},True)
        self.assertIn('gender composition',self.state()['plan']['interaction']['reference'])
    def test_preview_is_not_a_real_submission(self):
        self.request('/api/host/sample',{},True)
        self.assertFalse(self.state()['peerVisible']);self.assertEqual(server.STATE['responses'],{})
        self.assertTrue(server.STATE['previewResponses'])
    def test_preview_examples_follow_selected_material(self):
        self.plan(lambda p:p.update(materialId='81'))
        self.request('/api/host/sample',{},True)
        answers=str(server.STATE['previewResponses'])
        self.assertIn('population',answers)
        self.assertNotIn('middle-class jobs',answers)
    def test_export_embeds_material_and_excludes_peer_tokens(self):
        code,html=self.request('/api/export?token='+self.people[0]['token']);self.assertEqual(code,200)
        self.assertIn(b'data:image/png;base64,',html);self.assertNotIn(self.people[1]['token'].encode(),html)
        self.assertIn(b'localStorage',html)
    def test_resize_preserves_existing_links(self):
        token=self.people[0]['token'];self.plan(lambda p:p.update(groupCount=2,groupSize=2))
        self.assertEqual(len([p for p in server.STATE['people'] if p['active']]),4)
        self.assertEqual(self.state()['person']['id'],self.people[0]['id'])
        self.assertEqual(server.STATE['people'][0]['token'],token)
    def test_deleted_current_stage_moves_to_valid_stage(self):
        self.plan(lambda p:p.update(phases=p['phases'][1:]));self.assertEqual(self.state()['plan']['live']['phaseId'],'discuss')
    def test_invalid_plan_does_not_replace_activity(self):
        self.assertEqual(self.plan(lambda p:p.update(groupSize=0))[0],400);self.assertEqual(self.state()['plan']['groupSize'],3)
    def test_same_role_regrouping_changes_peer_set(self):
        self.plan(lambda p:(p.update(groupCount=2),p['interaction'].update(regroup='cross')))
        peers=self.state()['peers'];self.assertEqual(len(peers),2);self.assertEqual([x['slot'] for x in peers],[0,0])
    def test_qr_is_local_and_requires_host_access(self):
        self.assertEqual(self.request('/api/qr?target='+self.base+'/join')[0],403)
        code,svg=self.request('/api/qr?target='+self.base+'/join',host=True);self.assertEqual(code,200);self.assertIn(b'<svg',svg)
    def test_peer_review_has_a_recipient(self):
        self.plan(lambda p:p.update(structure='Peer Editing'))
        self.answer(0);self.request('/api/host/live',{'command':'stage','phaseId':'discuss'},True)
        self.request('/api/discussion?token='+self.people[0]['token'],{'kind':'post','text':'Support the claim with the axis unit.'})
        self.assertEqual(self.state()['posts'][0]['to'],self.people[1]['id'])

    def test_role_play_uses_distinct_roles_for_each_group_size(self):
        for size in range(2,6):
            tasks=tasks_for('81','Role Play',size)
            self.assertEqual(len(tasks),size)
            self.assertEqual({a for t in tasks for a in t['assignees']},set(range(size)))
            self.assertEqual(len({t['roleId'] for t in tasks}),size)
            self.assertTrue(all(t.get('handoff') for t in tasks))
    def test_analytic_groups_do_not_leave_extra_learners_unassigned(self):
        for size in range(2,6):
            tasks=tasks_for('83','Analytic Teams',size)
            self.assertEqual({a for t in tasks for a in t['assignees']},set(range(size)))
    def test_identical_questions_keep_separate_student_answers(self):
        self.plan(lambda p:p.update(structure='Think–Pair–Share',tasks=tasks_for('83','Think–Pair–Share',3)))
        for i,text in enumerate(['My first interpretation','A different interpretation']):
            self.request('/api/response?token='+self.people[i]['token'],{'phaseId':'read','answers':{'task-1':text},'submitted':True})
        self.assertEqual(self.state()['responses'][self.people[0]['id']]['read:task-1'],'My first interpretation')
        self.assertEqual(self.state(1)['responses'][self.people[1]['id']]['read:task-1'],'A different interpretation')
    def test_role_play_exchange_has_the_intended_peer(self):
        self.plan(lambda p:p.update(structure='Role Play',tasks=tasks_for('83','Role Play',3)))
        for i in range(3):self.answer(i)
        self.assertEqual(self.state(2)['reviewTo'],self.people[0]['id'])
        self.request('/api/host/live',{'command':'stage','phaseId':'discuss'},True)
        self.request('/api/discussion?token='+self.people[2]['token'],{'kind':'post','text':'Which unit supports this claim?'})
        self.assertEqual(self.state(0)['posts'][0]['to'],self.people[0]['id'])
    def test_personal_exchange_notes_do_not_replace_a_group_answer(self):
        self.answer(0);self.answer(1)
        self.request('/api/host/live',{'command':'stage','phaseId':'discuss'},True)
        for i,text in enumerate(['A checked a unit','B changed a claim']):
            code,_=self.request('/api/response?token='+self.people[i]['token'],{'phaseId':'discuss','answers':{'discuss':text},'submitted':True})
            self.assertEqual(code,200)
        self.assertEqual(self.state()['responses'][self.people[0]['id']]['discuss:discuss'],'A checked a unit')
        self.assertEqual(self.state(1)['responses'][self.people[1]['id']]['discuss:discuss'],'B changed a claim')
        self.assertNotIn('discuss:discuss',self.state(1)['responses'][self.people[0]['id']])
        self.assertEqual(self.state()['groupAnswer']['text'],'')
    def test_offline_versions_keep_roles_and_all_story_frames(self):
        self.plan(lambda p:p.update(materialId='81',structure='Role Play',tasks=tasks_for('81','Role Play',3)))
        _,a=self.request('/api/export?token='+self.people[0]['token'])
        _,c=self.request('/api/export?token='+self.people[2]['token'])
        self.assertIn(b'Story Author',a)
        self.assertIn(b'Critical Editor',c)
        self.assertEqual(a.count(b'data:image/jpeg;base64,'),7)

if __name__=='__main__':unittest.main(verbosity=2)
