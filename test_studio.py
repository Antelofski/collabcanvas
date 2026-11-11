"""Integration checks for role artifacts, concealment, and connected edits."""
import base64, json, tempfile, threading, unittest
from copy import deepcopy
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import server
from model import tasks_for

class StudioIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.base='http://127.0.0.1:'+str(cls.http.server_port)
        server.BASE=cls.base
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();server.initialize(Path(self.tmp.name)/'state.json')
        self.admin=server.STATE['admin'];p=deepcopy(server.STATE['plan'])
        p.update(planned=True,materialId='81',structure='Role Play',groupCount=2,groupSize=3,studio={'review':'summary','exchange':'compare'})
        p['tasks']=tasks_for('81','Role Play',3);p['interaction']['visibility']='after_group'
        self.req('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']})
        self.req('/api/host/deploy',{'planRev':server.STATE['planRev']})
        self.people=[p for p in server.STATE['people'] if p['active']]
    def tearDown(self):self.tmp.cleanup()
    def req(self,path,body=None,person=None,preview=False):
        headers={'Content-Type':'application/json'}
        if person:path+='?'+('preview=1&admin='+self.admin+'&person='+person['id'] if preview else 'token='+person['token'])
        else:headers['X-Admin-Token']=self.admin
        request=Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urlopen(request) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def artifact(self,p,record=None,version=0,preview=False,phase='read'):
        return self.req('/api/studio/save',{'artifact':record or {'beats':[{'id':'b1','frame':0,'text':'Area encodes people.','reason':'Check the unit.'}],'submitted':{}},'version':version,'phaseId':phase},p,preview)
    def prepare(self,group=0):
        for p in [p for p in self.people if p['group']==group]:
            task=next(t for t in server.STATE['plan']['tasks'] if p['slot'] in t['assignees'])
            self.req('/api/response',{'phaseId':'read','answers':{task['id']:'Independent answer'},'submitted':True},p)
    def test_peer_artifact_hidden_before_preparation(self):
        a,b=self.people[:2];self.artifact(a)
        status,view=self.req('/api/state',person=b)
        self.assertEqual(status,200);self.assertNotIn(a['id'],view['studioArtifacts'])
    def test_peer_artifact_visible_after_group_preparation(self):
        a,b=self.people[:2];self.artifact(a);self.prepare()
        _,view=self.req('/api/state',person=b)
        self.assertEqual(view['studioArtifacts'][a['id']]['beats'][0]['text'],'Area encodes people.')
    def test_other_team_never_receives_artifact(self):
        a=self.people[0];other=next(p for p in self.people if p['group']==1)
        self.artifact(a);self.prepare(0);self.prepare(1)
        _,view=self.req('/api/state',person=other);self.assertNotIn(a['id'],view['studioArtifacts'])
    def test_preview_is_separate(self):
        p=self.people[0];self.artifact(p,preview=True)
        _,real=self.req('/api/state',person=p);self.assertFalse(real['studioArtifacts'][p['id']])
    def test_stale_write_does_not_overwrite(self):
        p=self.people[0];self.assertEqual(self.artifact(p)[0],200)
        self.assertEqual(self.artifact(p)[0],400)
        self.assertEqual(server.STATE['artifacts'][p['id']]['version'],1)
    def test_own_identity_cannot_be_overridden(self):
        a,b=self.people[:2];status,_=self.req('/api/studio/save',{'person':b['id'],'phaseId':'read','version':0,'artifact':{'reflection':'Mine'}},a)
        self.assertEqual(status,200);self.assertNotIn(b['id'],server.STATE['artifacts'])
    def test_claim_edit_preserves_prior_work(self):
        a=self.people[0];self.artifact(a);before=deepcopy(server.STATE['artifacts'])
        status,candidate=self.req('/api/host/studio-propose',{'instruction':'Have the editor check each claim and return changes.','target':'editor-review'})
        self.assertEqual(status,200);self.assertEqual(candidate['plan']['studio']['review'],'claims')
        self.req('/api/host/plan',{'plan':candidate['plan'],'planRev':server.STATE['planRev']})
        self.assertEqual(server.STATE['artifacts'],before)
    def test_unsupported_edit_has_no_effect(self):
        before=deepcopy(server.STATE['plan']);status,_=self.req('/api/host/studio-propose',{'instruction':'Add an arbitrary physics engine.'})
        self.assertEqual(status,400);self.assertEqual(server.STATE['plan'],before)
    def test_questions_first_conceals_explanations_on_server(self):
        a,b=self.people[:2];self.artifact(a);self.prepare()
        p=deepcopy(server.STATE['plan']);p['studio']['exchange']='questions';self.req('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']})
        _,view=self.req('/api/state',person=b);self.assertNotIn('beats',view['studioArtifacts'].get(a['id'],{}));self.assertNotIn(a['id'],view['responses'])
        self.artifact(b,{'question':'What is the unit?','questionSent':True})
        _,view=self.req('/api/state',person=b);self.assertIn('beats',view['studioArtifacts'][a['id']])
    def test_invalid_frame_rejected(self):
        self.assertEqual(self.artifact(self.people[0],{'beats':[{'id':'b','frame':99,'text':'x'}]})[0],400)
    def test_rehearsal_seed_does_not_populate_class(self):
        self.req('/api/host/sample',{})
        self.assertTrue(server.STATE['previewArtifacts']);self.assertFalse(server.STATE.get('artifacts'))
    def test_clear_rehearsal_keeps_class_work(self):
        self.artifact(self.people[0]);self.req('/api/host/sample',{});self.req('/api/host/clear-sample',{})
        self.assertTrue(server.STATE['artifacts']);self.assertFalse(server.STATE['previewArtifacts'])
    def test_invalid_pdf_has_readable_error(self):
        status,body=self.req('/api/host/slides',{'name':'broken.pdf','data':base64.b64encode(b'not a PDF').decode()})
        self.assertEqual(status,400);self.assertIn('valid PDF',body['error'])

    def test_entry_describes_assigned_tasks_without_private_tokens(self):
        status,entry=self.req('/api/join?code='+server.STATE['code'])
        self.assertEqual(status,200)
        first=entry['people'][0]
        self.assertEqual(first['tasks'][0]['roleId'],'author')
        self.assertEqual(first['tasks'][0]['title'],'Story Author')
        self.assertNotIn('token',first)
        self.assertNotIn('responses',entry)
    def test_shared_entry_claim_routes_to_selected_group_and_role(self):
        reader=next(p for p in self.people if p['group']==1 and p['slot']==1)
        status,result=self.req('/api/join',{'code':server.STATE['code'],'name':'Demo reader','person':reader['id']})
        self.assertEqual(status,200)
        self.assertEqual(result['url'],'/s/'+reader['token'])
        _,view=self.req('/api/state',person=reader)
        self.assertEqual(view['person']['group'],1)
        self.assertEqual([t['roleId'] for t in view['plan']['tasks'] if reader['slot'] in t['assignees']],['reader'])
        self.assertEqual(self.req('/api/join',{'code':server.STATE['code'],'name':'Another learner','person':reader['id']})[0],409)

if __name__=='__main__':unittest.main()
