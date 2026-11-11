"""Cross-person handoffs and isolated testing for the four-role activity."""
import unittest,json
from copy import deepcopy
import server
from collab_workflow import group_first_plan, TEST_RUNS
from model import tasks_for
import test_studio as _studio

class WorkflowIntegration(unittest.TestCase):
    setUpClass=classmethod(_studio.StudioIntegration.setUpClass.__func__)
    tearDownClass=classmethod(_studio.StudioIntegration.tearDownClass.__func__)
    req=_studio.StudioIntegration.req
    tearDown=_studio.StudioIntegration.tearDown
    def setUp(self):
        _studio.StudioIntegration.setUp(self)
        p=deepcopy(server.STATE['plan']);p['groupSize']=4;p['budget']=18;p['interaction']['mode']='async'
        p['tasks']=tasks_for('81','Role Play',4);p=group_first_plan(p)
        self.req('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']})
        self.people=sorted([p for p in server.STATE['people'] if p['active']],key=lambda p:(p['group'],p['slot']))
    def opening(self,p=None,version=0):
        return self.req('/api/studio/group',dict(section='opening',phaseId='read',version=version,record={'text':'Each step filters people.'}),p or self.people[0])
    def ready(self):
        for p in self.people[:4]:
            t=next(t for t in server.STATE['plan']['tasks'] if p['slot'] in t['assignees'])
            self.req('/api/response',dict(phaseId='discuss',answers={t['id']:'My finding'},submitted=True),p)
    def test_four_roles_and_edit_preserve_budget(self):
        p=server.STATE['plan'];self.assertEqual([t['roleId'] for t in p['tasks']],['author','reader','checker','editor'])
        self.assertEqual(sum(s['minutes'] for s in p['phases']),18)
        self.assertEqual([s['purpose'] for s in p['phases']],['opening','rolework','critique'])
    def test_group_reading_handoff_and_group_boundary(self):
        self.assertEqual(self.opening()[0],200)
        _,peer=self.req('/api/state',person=self.people[1]);_,other=self.req('/api/state',person=self.people[4])
        self.assertEqual(peer['studioGroup']['opening']['text'],'Each step filters people.')
        self.assertFalse(other['studioGroup']['opening']['text'])
    def test_role_submission_needs_group_starting_reading(self):
        status,_=self.req('/api/studio/save',dict(version=0,phaseId='discuss',artifact={'reflection':'A claim','submitted':{'discuss':True}}),self.people[0])
        self.assertEqual(status,400)
    def test_stale_shared_edit_is_rejected(self):
        self.opening();self.assertEqual(self.opening(self.people[1])[0],400)
        self.assertEqual(self.opening(self.people[1],version=1)[0],200)
    def test_shared_critique_requires_all_roles(self):
        body=dict(section='critique',phaseId='revise',version=0,record=dict(message='Filters people',misreading='Looks like time',change='Label filters'))
        self.assertEqual(self.req('/api/studio/group',body,self.people[0])[0],400)
        self.ready();self.assertEqual(self.req('/api/studio/group',body,self.people[0])[0],200)
        _,view=self.req('/api/state',person=self.people[1]);self.assertEqual(view['studioGroup']['critique']['message'],'Filters people')
    def test_editor_assessment_available_to_peers_after_submission(self):
        editor=self.people[3]
        self.req('/api/studio/save',dict(version=0,phaseId='discuss',artifact={'reflection':'Use the population unit.'}),editor)
        _,early=self.req('/api/state',person=self.people[0]);self.assertNotIn(editor['id'],early['studioArtifacts'])
        self.ready();_,after=self.req('/api/state',person=self.people[0]);self.assertEqual(after['studioArtifacts'][editor['id']]['reflection'],'Use the population unit.')
    def test_test_answers_never_change_class_or_rehearsal(self):
        before=deepcopy(server.STATE)
        _,run=self.req('/api/host/test-start',{})
        person=run['people'][0]
        path='/api/test/'+run['id']+'?person='+person['id']+'&action=%2Fapi%2Fstudio%2Fgroup'
        status,_=self.req(path,dict(section='opening',phaseId='read',version=0,record={'text':'Isolated test'}))
        self.assertEqual(status,200);self.assertEqual(server.STATE,before)
        self.assertEqual(TEST_RUNS[run['id']]['state']['studioGroups']['0']['opening']['text'],'Isolated test')
    def test_test_report_rejects_changed_plan(self):
        _,run=self.req('/api/host/test-start',{})
        p=deepcopy(server.STATE['plan']);p['title']='Changed';self.req('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']})
        status,_=self.req('/api/host/test-report',{'id':run['id'],'checks':[dict(name='A',status='passed')]})
        self.assertEqual(status,400)
