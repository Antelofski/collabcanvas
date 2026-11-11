"""Progress evidence, privacy, scoped support, and separate future plans."""
import unittest,json
from copy import deepcopy
import server
import test_workflow as _workflow
from collab_workflow import TEST_RUNS

class ProgressIntegration(unittest.TestCase):
 setUpClass=classmethod(_workflow.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_workflow.WorkflowIntegration.tearDownClass.__func__)
 setUp=_workflow.WorkflowIntegration.setUp
 tearDown=_workflow.WorkflowIntegration.tearDown
 req=_workflow.WorkflowIntegration.req
 def answer(self,p=None,answer='filter',kind='initial',phase='discuss',preview=False):return self.req('/api/progress/answer',dict(kind=kind,answer=answer,reason='The labels name a narrower group.',phaseId=phase),p or self.people[0],preview)
 def seed(self):
  for i,p in enumerate(self.people[:4]):self.assertEqual(self.answer(p,'time' if i<2 else 'filter')[0],200)
 def support(self):return self.req('/api/host/progress-support',dict(kind='support',group=0))
 def test_private_answers_and_reference_key_are_not_shared(self):
  self.answer();_,peer=self.req('/api/state',person=self.people[1]);self.assertEqual(peer['progress']['answers'],{})
  self.assertNotIn('answer',peer['progress']['questions']['initial'])
  self.assertNotIn('progressRecords',peer)
 def test_answer_is_immutable_and_cannot_impersonate(self):
  self.assertEqual(self.answer(answer='time')[0],200);self.assertEqual(self.answer()[0],400)
  _,view=self.req('/api/state',person=self.people[0]);self.assertEqual(view['progress']['answers']['initial']['answer'],'time')
 def test_initial_check_requires_its_phase_and_reason(self):
  self.assertEqual(self.answer(phase='read')[0],400)
  self.assertEqual(self.req('/api/progress/answer',dict(kind='initial',answer='filter',reason='',phaseId='discuss'),self.people[0])[0],400)
 def test_rehearsal_answers_do_not_affect_live_evidence(self):
  self.answer(preview=True);_,host=self.req('/api/host');self.assertEqual(host['progress']['teams'][0]['answered'],0);self.assertEqual(host['previewProgress']['teams'][0]['answered'],1)
 def test_evidence_computes_mismatch_from_real_answers(self):
  self.seed();_,host=self.req('/api/host');e=host['progress']['teams'][0];self.assertEqual((e['answered'],e['wrong'],e['status']),(4,2,'2 answers need review'))
 def test_support_is_group_scoped_and_targets_wrong_answers_only(self):
  self.seed();self.support()
  _,wrong=self.req('/api/state',person=self.people[0]);_,correct=self.req('/api/state',person=self.people[2]);_,other=self.req('/api/state',person=self.people[4])
  self.assertTrue(wrong['progress']['support']['needsFollowup']);self.assertFalse(correct['progress']['support']['needsFollowup']);self.assertIsNone(other['progress']['support']);self.assertNotIn('targets',wrong['progress']['support'])
  self.assertEqual(self.answer(self.people[2],'yes','followup')[0],400)
 def test_resolution_requires_recheck_and_teacher_judgment(self):
  self.seed();self.support();body=dict(kind='resolve',group=0,note='Checked both explanations against the labels.')
  self.assertEqual(self.req('/api/host/progress-support',body)[0],400)
  self.answer(self.people[0],'yes','followup');self.answer(self.people[1],'yes','followup')
  self.assertEqual(self.req('/api/host/progress-support',body)[0],200)
  _,host=self.req('/api/host');e=host['progress']['teams'][0];self.assertTrue(e['support']['resolved']);self.assertEqual(e['wrong'],2);self.assertEqual(e['followupCorrect'],2)
 def test_no_automatic_rubric_or_speech_judgment(self):
  self.assertEqual(self.req('/api/host/progress-support',dict(kind='review',group=0,rubric='needs-support',note=''))[0],400)
  self.assertEqual(self.req('/api/host/progress-support',dict(kind='review',group=0,rubric='needs-support',note='Reader question remains unanswered.'))[0],200)
 def test_future_drafts_preserve_running_plan_and_answers(self):
  self.seed();before=deepcopy(server.STATE['plan']);answers=deepcopy(server.STATE['progressRecords'])
  _,d=self.req('/api/host/progress-draft',dict(kind='next-activity',group=0));self.assertEqual(server.STATE['plan'],before);self.assertEqual(server.STATE['progressRecords'],answers)
  _,run=self.req('/api/host/progress-draft-preview',dict(id=d['draft']['id']));self.assertTrue(run['plan']['progress']['beforeDiscussion']);self.assertEqual(run['plan']['progress']['checkPhase'],'read')
  clone=TEST_RUNS[run['id']]['state'];self.assertNotIn('progressRecords',clone);self.assertEqual(server.STATE['progressRecords'],answers)
 def test_next_run_draft_contains_changed_briefs_and_archives_on_start(self):
  self.seed();_,d=self.req('/api/host/progress-draft',dict(kind='next-run',group=0));draft=server.STATE['progressDrafts'][-1];self.assertTrue(draft['plan']['studio']['adaptedBriefs'])
  before=server.STATE['code'];server.STATE['plan']['live']['started']=True
  self.assertEqual(self.req('/api/host/progress-draft-start',dict(id=d['draft']['id']))[0],400)
  server.STATE['plan']['live']['started']=False
  self.assertEqual(self.req('/api/host/progress-draft-start',dict(id=d['draft']['id']))[0],200);self.assertNotEqual(server.STATE['code'],before);self.assertFalse(server.STATE['deployment']['active']);self.assertNotIn('progressRecords',server.STATE);self.assertTrue(server.STATE['previousActivity'])
 def test_private_precheck_gates_group_reading_in_new_draft(self):
  self.seed();self.req('/api/host/progress-draft',dict(kind='next-activity',group=0));draft=server.STATE['progressDrafts'][-1];server.STATE['plan']=deepcopy(draft['plan']);server.STATE.pop('progressRecords',None)
  body=dict(section='opening',phaseId='read',version=0,record={'text':'We see filtering.'})
  self.assertEqual(self.req('/api/studio/group',body,self.people[0])[0],400);self.answer(phase='read');self.assertEqual(self.req('/api/studio/group',body,self.people[0])[0],200)
  _,unanswered=self.req('/api/state',person=self.people[1]);self.assertFalse(unanswered['studioGroup']['opening']['text'])
  self.answer(self.people[1],phase='read');_,answered=self.req('/api/state',person=self.people[1]);self.assertEqual(answered['studioGroup']['opening']['text'],'We see filtering.')
 def test_in_person_resolution_keeps_missing_followups_explicit(self):
  self.seed();self.support();status,_=self.req('/api/host/progress-support',dict(kind='resolve',inPerson=True,group=0,note='Asked both learners to explain the filter in person.'))
  self.assertEqual(status,200);_,host=self.req('/api/host');e=host['progress']['teams'][0];self.assertTrue(e['support']['resolved']);self.assertEqual(e['followupCount'],0);self.assertEqual(e['support']['reviewBasis'],'in-person observation')
 def test_acknowledging_help_keeps_learning_evidence(self):
  self.seed();self.req('/api/help',{'text':'Please check our reading.'},self.people[0]);self.assertFalse(server.STATE['requests'][-1].get('resolved'))
  self.assertEqual(self.req('/api/host/progress-support',dict(kind='help-reviewed',group=0))[0],200)
  self.assertTrue(server.STATE['requests'][-1]['resolved']);_,host=self.req('/api/host');self.assertEqual(host['progress']['teams'][0]['wrong'],2)
