"""Executable progress signals versus teacher-reviewed, written criteria."""
from copy import deepcopy
import time, unittest
import server
import test_workflow as _wf
from progress_rules import suggested_rules

class RulePlanning(unittest.TestCase):
 setUpClass=classmethod(_wf.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_wf.WorkflowIntegration.tearDownClass.__func__)
 setUp=_wf.WorkflowIntegration.setUp
 tearDown=_wf.WorkflowIntegration.tearDown
 req=_wf.WorkflowIntegration.req
 def save(self,rules):
  plan=deepcopy(server.STATE['plan']);plan.setdefault('progress',{})['rules']=rules
  return self.req('/api/host/plan',dict(plan=plan,planRev=server.STATE['planRev']))
 def test_suggestions_use_current_phases_without_mutation(self):
  before=deepcopy(server.STATE);_,r=self.req('/api/host/progress-analyze',{})
  self.assertEqual(server.STATE,before)
  self.assertEqual(r['rules'][0]['phaseId'],'discuss');self.assertEqual(r['rules'][2]['phaseId'],'revise')
  self.assertIn('no model call',r['source'])
 def test_saved_rules_update_student_check_and_preserve_existing_work(self):
  rules=suggested_rules(server.STATE['plan']);server.STATE['responses'][self.people[0]['id']]={'discuss:note':'An existing finding'}
  rules[1]['phaseId']='read';self.assertEqual(self.save(rules)[0],200)
  _,student=self.req('/api/state',person=self.people[0]);self.assertEqual(student['progress']['phase'],'read')
  self.assertEqual(server.STATE['responses'][self.people[0]['id']]['discuss:note'],'An existing finding')
  rules[1]['enabled']=False;self.save(rules)
  _,student=self.req('/api/state',person=self.people[0]);self.assertTrue(student['progress']['config']['privateCheck'])
  _,host=self.req('/api/host');self.assertFalse(any(r['id']=='reading-check' for r in host['progress']['teams'][0]['signals']))
 def test_first_prototype_review_rules_gain_recorded_signals(self):
  rules=suggested_rules(server.STATE['plan'])
  for rid,condition in [('workload-balance','workload_balance'),('resolve-disagreement','unresolved_difference'),('specific-feedback','feedback_specific')]:
   row=next(r for r in rules if r['id']==rid);self.assertFalse(row['enabled']);self.assertEqual(row['condition'],condition)
   row.update(enabled=True,condition='teacher_review',expectation='Text saved by the first prototype.')
  rules.append(dict(rules[2],id='role-clarity',title='Each learner knows their next step',enabled=True))
  self.assertEqual(self.save(rules)[0],200)
  saved={r['id']:r for r in server.STATE['plan']['progress']['rules']}
  self.assertEqual(saved['specific-feedback']['condition'],'feedback_specific');self.assertNotIn('first prototype',saved['specific-feedback']['expectation'])
  _,host=self.req('/api/host');signals={s['id']:s for s in host['progress']['teams'][0]['signals']}
  self.assertEqual(signals['role-clarity']['status'],'needs-review');self.assertNotEqual(signals['specific-feedback']['status'],'needs-review')
  self.assertNotIn('workload-balance',signals);self.assertIn('workload-balance',[s['id'] for s in host['progress']['classSignals']])
 def test_rules_stored_by_the_first_prototype_are_upgraded_on_read(self):
  from progress_rules import effective_rules
  old=[dict(id='workload-balance',title='Workload fits the roles and time',condition='teacher_review',phaseId='discuss',remainingMinutes=0,expectation='Old',evidence='Old',response='Old',enabled=True,origin='suggested')]
  server.STATE['plan']['progress']={'rules':old};before=deepcopy(server.STATE)
  rule=effective_rules(server.STATE['plan'],server.STATE)[0]
  self.assertEqual(rule['condition'],'workload_balance');self.assertEqual(rule['params'],{'share':50});self.assertEqual(server.STATE,before)
  self.assertEqual(self.req('/api/host')[0],200)
 def test_rule_switch_preserves_collection_and_saved_answers(self):
  rules=suggested_rules(server.STATE['plan']);rules[1]['enabled']=False;self.save(rules)
  status,_=self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='My own reading.'),self.people[0])
  self.assertEqual(status,200)
  _,host=self.req('/api/host');self.assertEqual(host['progress']['teams'][0]['answered'],1)
  self.assertFalse(any(s['id']=='reading-check' for s in host['progress']['teams'][0]['signals']))
 def test_comparison_snapshots_preserve_work_without_applying(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='A saved reading.'),self.people[0])
  server.STATE['artifacts']={self.people[0]['id']:{'kept':'Existing role work'}}
  before=deepcopy(server.STATE)
  status,pair=self.req('/api/host/support-comparison',dict(group=0,pattern='comparison'))
  self.assertEqual(status,200);self.assertEqual(server.STATE,before)
  from collab_workflow import test_run
  left=test_run(pair['before'])['state'];right=test_run(pair['after'])['state']
  self.assertEqual(left['artifacts'],right['artifacts']);self.assertEqual(left['progressRecords']['answers'],right['progressRecords']['answers'])
  self.assertNotIn('support',left['progressRecords'].get('teams',{}).get('0',{}))
  self.assertEqual(right['progressRecords']['teams']['0']['support']['targets'],[self.people[0]['id']])
  self.assertNotIn('1',right['progressRecords']['teams'])
 def test_comparison_snapshots_are_read_only(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='Initial.'),self.people[0])
  _,pair=self.req('/api/host/support-comparison',dict(group=0,pattern='comparison'))
  path='/api/test/'+pair['after']+'?person='+self.people[0]['id']
  _,view=self.req(path+'&action=/api/state');self.assertTrue(view['instructorReadOnly'])
  status,_=self.req(path+'&action=/api/progress/answer',dict(kind='followup',answer='yes',reason='Do not write.'))
  self.assertEqual(status,400)
 def test_adaptive_comparison_adds_only_to_after_snapshot(self):
  before=deepcopy(server.STATE)
  status,pair=self.req('/api/host/support-comparison',dict(group=0,pattern='scaffold',targets=[self.people[0]['id']],note='Requested smaller steps.'))
  self.assertEqual(status,200);self.assertEqual(server.STATE,before)
  from collab_workflow import test_run
  self.assertFalse(test_run(pair['before'])['state'].get('adaptive',{}).get('teams'))
  self.assertEqual(test_run(pair['after'])['state']['adaptive']['teams']['0']['changes'][0]['targets'],[self.people[0]['id']])
 def test_custom_text_never_programs_an_automatic_detector(self):
  rules=suggested_rules(server.STATE['plan']);custom=dict(rules[2],id='custom-1',title='Check consensus',expectation='Each learner gives a reason.',origin='custom')
  rules.append(custom);self.assertEqual(self.save(rules)[0],200)
  _,host=self.req('/api/host');signal=next(r for r in host['progress']['teams'][0]['signals'] if r['id']=='custom-1')
  self.assertEqual(signal['status'],'needs-review')
  custom['condition']='private_check';self.assertEqual(self.save(rules)[0],400)
 def test_custom_observation_requires_evidence_and_is_team_scoped(self):
  rules=suggested_rules(server.STATE['plan']);rules.append(dict(rules[2],id='custom-1',title='Check consensus'))
  self.save(rules);body=dict(kind='rule-review',group=0,ruleId='custom-1',status='attention',note='')
  self.assertEqual(self.req('/api/host/progress-support',body)[0],400)
  body['note']='Two learners could not explain the label.';self.assertEqual(self.req('/api/host/progress-support',body)[0],200)
  _,host=self.req('/api/host');a,b=host['progress']['teams']
  self.assertEqual(next(r for r in a['signals'] if r['id']=='custom-1')['status'],'attention')
  self.assertEqual(next(r for r in b['signals'] if r['id']=='custom-1')['status'],'needs-review')
 def test_submission_reminder_respects_phase_and_time(self):
  self.save(suggested_rules(server.STATE['plan']))
  live=server.STATE['plan']['live'];live.update(started=True,paused=False,phaseId='discuss',startedAt=time.time())
  def status():
   _,host=self.req('/api/host');return host['progress']['teams'][0]['signals'][0]['status']
  self.assertEqual(status(),'collecting');live['startedAt']=time.time()-7*60;self.assertEqual(status(),'attention')
  live['phaseId']='read';self.assertEqual(status(),'collecting')
 def test_private_error_flag_does_not_wait_for_consensus_or_all_submissions(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='I read it as time.'),self.people[0])
  _,host=self.req('/api/host');signal=next(r for r in host['progress']['teams'][0]['signals'] if r['id']=='reading-check')
  self.assertEqual(signal['status'],'attention');self.assertEqual(signal['people'],[self.people[0]['id']])
 def test_support_preview_detects_changed_target_evidence(self):
  for p in self.people[:2]:self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='Time interpretation.'),p)
  self.assertEqual(self.req('/api/host/progress-support',dict(kind='support',group=0,expectedTargets=[self.people[0]['id']]))[0],400)
  self.assertNotIn('support',server.STATE['progressRecords']['teams']['0'])
 def test_editing_a_reviewed_rule_requires_a_fresh_observation(self):
  rules=suggested_rules(server.STATE['plan']);self.save(rules)
  self.req('/api/host/progress-support',dict(kind='rule-review',group=0,ruleId='peer-use',status='checked',note='I inspected their response.'))
  rules[2]['expectation']='Every unresolved question names a next step.';self.save(rules)
  _,host=self.req('/api/host');self.assertEqual(next(r for r in host['progress']['teams'][0]['signals'] if r['id']=='peer-use')['status'],'needs-review')
  self.assertEqual(len(server.STATE['progressRecords']['teams']['0']['ruleReviewHistory']),1)
 def test_support_keeps_artifacts_and_initial_answers(self):
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='Looks like time.'),self.people[0])
  server.STATE['artifacts']={self.people[0]['id']:{'reflection':'An existing role note'}}
  before=deepcopy(server.STATE['artifacts']);initial=deepcopy(server.STATE['progressRecords']['answers'])
  self.req('/api/host/progress-support',dict(kind='support',group=0))
  self.assertEqual(server.STATE['artifacts'],before);self.assertEqual(server.STATE['progressRecords']['answers'],initial)
 def test_live_instructor_inspection_reads_actual_work_but_cannot_save(self):
  person=self.people[0];self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='A saved class response.'),person)
  query='?preview=1&inspect=1&person='+person['id']
  _,view=self.req('/api/state'+query);self.assertTrue(view['instructorReadOnly']);self.assertFalse(view['preview'])
  self.assertEqual(view['progress']['answers']['initial']['answer'],'time')
  before=deepcopy(server.STATE['progressRecords'])
  self.assertEqual(self.req('/api/progress/answer'+query,dict(kind='initial',phaseId='discuss',answer='filter',reason='Do not save.'))[0],403)
  self.assertEqual(server.STATE['progressRecords'],before)
 def test_adaptation_moves_the_instrumented_check_with_saved_rules(self):
  self.save(suggested_rules(server.STATE['plan']))
  self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer='time',reason='A saved class response.'),self.people[0])
  _,r=self.req('/api/host/progress-draft',dict(kind='next-activity',group=0))
  draft=next(d for d in server.STATE['progressDrafts'] if d['id']==r['draft']['id'])
  from progress_backend import initial_phase
  self.assertEqual(initial_phase(draft['plan']),'read')
 def test_live_inspection_requires_instructor_access(self):
  from urllib.request import urlopen
  from urllib.error import HTTPError
  url=self.base+'/api/state?preview=1&inspect=1&person='+self.people[0]['id']
  with self.assertRaises(HTTPError) as raised:urlopen(url)
  self.assertEqual(raised.exception.code,403)
 def test_rule_stage_and_duplicate_validation(self):
  rules=suggested_rules(server.STATE['plan']);rules[0]['phaseId']='gone';self.assertEqual(self.save(rules)[0],400)
  rules=suggested_rules(server.STATE['plan']);rules.append(deepcopy(rules[0]));self.assertEqual(self.save(rules)[0],400)

if __name__=='__main__':unittest.main()
