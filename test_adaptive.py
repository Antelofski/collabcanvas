"""Evidence-linked changes preserve work, privacy, group scope and teacher authority."""
from copy import deepcopy
import unittest
import server
import test_workflow as _wf
from progress_rules import suggested_rules
from collab_workflow import TEST_RUNS

class AdaptiveIntegration(unittest.TestCase):
 setUpClass=classmethod(_wf.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_wf.WorkflowIntegration.tearDownClass.__func__)
 setUp=_wf.WorkflowIntegration.setUp
 tearDown=_wf.WorkflowIntegration.tearDown
 req=_wf.WorkflowIntegration.req
 def proposal(self,pattern='scaffold',targets=None):
  status,p=self.req('/api/host/adaptive-preview',dict(group=0,pattern=pattern,targets=targets or [self.people[0]['id']]))
  self.assertEqual(status,200);return dict(p,note='Teacher reviewed the request and chose this support.')
 def apply(self,pattern='scaffold',targets=None):return self.req('/api/host/adaptive-apply',self.proposal(pattern,targets))
 def response(self,c,p=None,**kw):
  values={key:'A specific response using the population labels.' for key,_ in c['spec']['fields']}
  return self.req('/api/adaptive/response',dict(id=c['id'],values=values,shared=True,**kw),p or self.people[0])
 def test_preview_does_not_change_class(self):
  before=deepcopy(server.STATE);self.proposal();self.assertEqual(server.STATE,before)
 def test_stale_preview_is_rejected(self):
  p=self.proposal();self.req('/api/help',dict(requestKind='difficulty',text='Too much to handle.'),self.people[0]);self.assertEqual(self.req('/api/host/adaptive-apply',p)[0],400)
 def test_new_role_work_invalidates_preview(self):
  p=self.proposal();server.STATE.setdefault('artifacts',{})[self.people[0]['id']]={'reflection':'A new interpretation.'}
  self.assertEqual(self.req('/api/host/adaptive-apply',p)[0],400)
 def test_new_peer_response_invalidates_no_change_decision(self):
  for person in self.people[:4]:self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='filter',reason='A source-based reason.'),person)
  _,h=self.req('/api/host');self.req('/api/host/adaptive-keep',dict(group=0,evidenceKey=h['progress']['teams'][0]['adaptive']['evidenceKey'],note='The reasons are adequate.'))
  server.STATE.setdefault('artifacts',{})[self.people[0]['id']]={'reflection':'An unsupported claim in the new role contribution.'}
  _,h=self.req('/api/host');self.assertEqual(next(s for s in h['progress']['teams'][0]['signals']if s['id']=='answer-pattern')['status'],'attention')
 def test_scope_and_downstream_handoff(self):
  _,result=self.apply();change=result['change']
  _,owner=self.req('/api/state',person=self.people[0]);_,partner=self.req('/api/state',person=self.people[3]);_,other=self.req('/api/state',person=self.people[4])
  self.assertTrue(owner['progress']['adaptive']['changes'][0]['assigned']);self.assertFalse(partner['progress']['adaptive']['changes'][0]['assigned']);self.assertEqual(other['progress']['adaptive']['changes'],[])
  self.assertEqual(self.response(change)[0],200);_,partner=self.req('/api/state',person=self.people[3]);self.assertEqual(len(partner['progress']['adaptive']['changes'][0]['shared']),1)
 def test_private_draft_not_visible_to_peers(self):
  _,r=self.apply('written-exchange');c=r['change'];self.req('/api/adaptive/response',dict(id=c['id'],version=0,values={'idea':'Private preparation','evidence':''},shared=False),self.people[0])
  _,peer=self.req('/api/state',person=self.people[1]);self.assertEqual(peer['progress']['adaptive']['changes'][0]['shared'],[]);self.assertEqual(peer['progress']['adaptive']['changes'][0]['own'],{'version':0})
 def test_replies_must_address_a_shared_peer(self):
  _,r=self.apply('written-exchange');c=r['change'];self.response(c)
  self.assertEqual(self.response(c,self.people[1],replyTo=self.people[0]['id'],reply='The population label supports this reading.')[0],200)
  self.assertEqual(self.response(c,self.people[2],replyTo=self.people[2]['id'],reply='Self response.')[0],400)
 def test_unassigned_student_cannot_write(self):
  _,r=self.apply();self.assertEqual(self.response(r['change'],self.people[1])[0],400);self.assertEqual(self.response(r['change'],self.people[4])[0],400)
 def test_duplicate_active_change_and_stale_writes_rejected(self):
  _,r=self.apply();c=r['change'];self.assertEqual(self.apply()[0],400);self.assertEqual(self.response(c)[0],200);self.assertEqual(self.response(c)[0],400)
 def test_original_answers_and_artifacts_retained(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='Initial interpretation.'),self.people[0]);server.STATE['artifacts']={self.people[0]['id']:{'reflection':'Original note'}}
  before=deepcopy((server.STATE['progressRecords'],server.STATE['artifacts'],server.STATE['plan']));self.apply();self.assertEqual((server.STATE['progressRecords'],server.STATE['artifacts'],server.STATE['plan']),before)
 def test_reason_check_never_discloses_private_answers(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='PRIVATE REASON'),self.people[0]);self.apply('reason-check');_,peer=self.req('/api/state',person=self.people[1]);self.assertNotIn('PRIVATE REASON',str(peer['progress']['adaptive']))
 def test_explicit_request_not_inactivity(self):
  _,host=self.req('/api/host');s=next(s for s in host['progress']['teams'][0]['signals'] if s['id']=='support-request');self.assertEqual(s['status'],'collecting')
  self.req('/api/help',dict(requestKind='participation',text='I prefer to write first.'),self.people[0]);_,host=self.req('/api/host');s=next(s for s in host['progress']['teams'][0]['signals'] if s['id']=='support-request');self.assertEqual(s['people'],[self.people[0]['id']])
  _,peer=self.req('/api/state',person=self.people[1]);self.assertEqual(peer['progress']['adaptive']['requests'],[])
 def test_consensus_can_be_kept_after_review(self):
  for p in self.people[:4]:self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='filter',reason='Different explanation.'),p)
  _,host=self.req('/api/host');e=host['progress']['teams'][0];self.assertEqual(next(s for s in e['signals'] if s['id']=='answer-pattern')['status'],'attention')
  self.assertEqual(self.req('/api/host/adaptive-keep',dict(group=0,evidenceKey=e['adaptive']['evidenceKey'],note='Reasons use the correct labels; no more task needed.'))[0],200)
  _,host=self.req('/api/host');self.assertEqual(next(s for s in host['progress']['teams'][0]['signals'] if s['id']=='answer-pattern')['status'],'checked')
 def test_teacher_review_required(self):
  self.req('/api/help',dict(requestKind='difficulty',text='Need smaller steps.'),self.people[0]);_,r=self.apply();c=r['change'];self.response(c);self.assertFalse(server.STATE['requests'][0].get('resolved'))
  self.assertEqual(self.req('/api/host/adaptive-review',dict(group=0,id=c['id'],note=''))[0],400)
  self.assertEqual(self.req('/api/host/adaptive-review',dict(group=0,id=c['id'],note='Checked the three steps and the interpretation in person.'))[0],200);self.assertTrue(server.STATE['requests'][0]['resolved'])
 def test_preview_is_isolated_and_keeps_existing_work(self):
  server.STATE['artifacts']={self.people[0]['id']:{'reflection':'Original role work'}};before=deepcopy(server.STATE);_,run=self.req('/api/host/adaptive-preview-session',self.proposal())
  self.assertEqual(server.STATE,before);self.assertEqual(TEST_RUNS[run['id']]['state']['artifacts'],before['artifacts']);self.assertNotIn('adaptive',before)
 def test_test_fixture_clears_adaptations(self):
  self.apply();_,run=self.req('/api/host/test-start',{});self.assertNotIn('adaptive',TEST_RUNS[run['id']]['state'])
 def test_no_blank_or_out_of_team_targets(self):
  self.assertEqual(self.req('/api/host/adaptive-preview',dict(group=0,pattern='scaffold',targets=[]))[0],400);self.assertEqual(self.req('/api/host/adaptive-preview',dict(group=0,pattern='scaffold',targets=[self.people[4]['id']]))[0],400)
 def test_custom_rule_cannot_program_detector(self):
  p=deepcopy(server.STATE['plan']);rules=suggested_rules(p);rules.append(dict(rules[0],id='custom',condition='answer_pattern'));p['progress']={'rules':rules};self.assertEqual(self.req('/api/host/plan',dict(plan=p,planRev=server.STATE['planRev']))[0],400)

if __name__=='__main__':unittest.main()
