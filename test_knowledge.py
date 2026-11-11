"""Knowledge records stay individual, task-scoped, versioned and evidence-backed."""
from copy import deepcopy
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError
import server
import test_workflow as wf

class KnowledgeRecords(unittest.TestCase):
 setUpClass=classmethod(wf.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(wf.WorkflowIntegration.tearDownClass.__func__)
 setUp=wf.WorkflowIntegration.setUp
 tearDown=wf.WorkflowIntegration.tearDown
 req=wf.WorkflowIntegration.req
 def row(self,p=None,task='population-filter'):
  _,report=self.req('/api/host/knowledge-report');learner=next(r for r in report['learners'] if r['person']==(p or self.people[0])['id'])
  return next(t for t in learner['tasks'] if t['id']==task)
 def answer(self,answer='filter'):
  return self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer=answer,reason='My reading of the frame labels.'),self.people[0])
 def review(self,task='population-filter',**kw):
  t=self.row(task=task);return self.req('/api/host/knowledge-review',dict(person=self.people[0]['id'],task=task,evidenceKey=t['evidenceKey'],version=(t['review'] or {}).get('version',0),status='demonstrated',note='Checked this individual response.',nextCheck='Check a new example.',**kw))
 def test_missing_evidence_is_not_observed(self):
  self.assertEqual(self.row()['status'],'not-observed');self.assertEqual(self.row(task='role-analysis')['status'],'not-observed')
 def test_keyed_check_is_individual_and_task_scoped(self):
  self.answer();self.assertEqual(self.row()['status'],'demonstrated');self.assertEqual(self.row(self.people[1])['status'],'not-observed');self.assertEqual(self.row(task='role-analysis')['status'],'not-observed')
 def test_incorrect_check_is_retained_as_needing_support(self):
  self.answer('land');t=self.row();self.assertEqual(t['status'],'needs-support');self.assertIn('land area',t['evidence'][0]['text'])
 def test_text_submission_needs_content_review(self):
  server.STATE['artifacts']={self.people[0]['id']:{'reflection':'A completed but ungraded explanation.'}}
  self.assertEqual(self.row(task='role-analysis')['status'],'needs-check')
  self.assertEqual(self.review('role-analysis')[0],200);self.assertEqual(self.row(task='role-analysis')['status'],'demonstrated')
 def test_group_answer_does_not_become_everyones_knowledge(self):
  server.STATE['studioGroups']={'0':{'critique':{'message':'A correct shared answer.'}}}
  self.assertEqual(self.row()['status'],'not-observed')
 def test_no_unrecorded_mastery_and_no_empty_review(self):
  self.assertEqual(self.review()[0],400)
  self.answer();t=self.row()
  self.assertEqual(self.req('/api/host/knowledge-review',dict(person=self.people[0]['id'],task=t['id'],evidenceKey=t['evidenceKey'],status='demonstrated',note=''))[0],400)
 def test_new_evidence_requires_recheck_and_keeps_review_history(self):
  server.STATE['artifacts']={self.people[0]['id']:{'reflection':'First explanation'}};self.review('role-analysis')
  server.STATE['artifacts'][self.people[0]['id']]['reflection']='New explanation'
  task=self.row(task='role-analysis');self.assertTrue(task['reviewStale']);self.assertEqual(task['status'],'needs-check');self.assertEqual(len(server.STATE['knowledgeReviewHistory']),1)
 def test_snapshot_is_immutable_and_excludes_access_tokens(self):
  self.answer();_,saved=self.req('/api/host/knowledge-snapshot',{});sid=saved['snapshot']['id']
  _,snapshot=self.req('/api/host/knowledge-report?snapshot='+sid);old=deepcopy(snapshot['learners'])
  self.review();_,later=self.req('/api/host/knowledge-report?snapshot='+sid)
  self.assertEqual(later['learners'],old);self.assertTrue(later['readOnly']);self.assertNotIn(server.STATE['admin'],str(later));self.assertNotIn(self.people[0]['token'],str(later))
 def test_report_requires_instructor_access(self):
  with self.assertRaises(HTTPError) as raised:urlopen(self.base+'/api/host/knowledge-report')
  self.assertEqual(raised.exception.code,403)
if __name__=='__main__':unittest.main()
