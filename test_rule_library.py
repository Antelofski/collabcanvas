"""The seed rules run on recorded events: saves, sign-offs, paste lengths and timers. Nothing is inferred from silence."""
from copy import deepcopy
import time, unittest
import server
import test_workflow as _wf
from progress_rules import suggested_rules, effective_rules
from rule_library import SEEDS, FAMILIES, ORDER, unavailable, match_text

class RuleLibrary(unittest.TestCase):
 setUpClass=classmethod(_wf.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_wf.WorkflowIntegration.tearDownClass.__func__)
 setUp=_wf.WorkflowIntegration.setUp
 tearDown=_wf.WorkflowIntegration.tearDown
 req=_wf.WorkflowIntegration.req
 opening=_wf.WorkflowIntegration.opening
 ready=_wf.WorkflowIntegration.ready
 def save(self,rules):
  plan=deepcopy(server.STATE['plan']);plan.setdefault('progress',{})['rules']=rules
  return self.req('/api/host/plan',dict(plan=plan,planRev=server.STATE['planRev']))
 def turn_on(self,**params):
  """Enable rules by id (underscores for hyphens), optionally with thresholds."""
  rules=suggested_rules(server.STATE['plan'])
  for key,value in params.items():
   row=next(r for r in rules if r['id']==key.replace('_','-'));row['enabled']=value is not False
   if isinstance(value,dict):row['params'].update(value)
  status,body=self.save(rules);self.assertEqual(status,200,body)
 def host(self):return self.req('/api/host')[1]['progress']
 def signal(self,rule,group=0):return next(s for s in self.host()['teams'][group]['signals'] if s['id']==rule)
 def class_signal(self,rule):return next(s for s in self.host()['classSignals'] if s['id']==rule)
 def live(self,phase,ago=0,paused=False,remaining=None):
  server.STATE['plan']['live'].update(started=True,paused=paused,phaseId=phase,startedAt=time.time()-ago,clock=time.time()-ago,remaining=remaining)
 def join(self,*people):
  for i,p in enumerate(people):p.update(claimed=True,name=p.get('name') or ['Maya','Eli','Noor','Leo','Ana','Ben','Cy','Dee'][self.people.index(p)])
 def critique(self,person,version=0,message='Each frame keeps a narrower group.',misreading='A fall over time.',change='Label who is counted.'):
  return self.req('/api/studio/group',dict(section='critique',phaseId='revise',version=version,record=dict(message=message,misreading=misreading,change=change)),person)
 def share(self,people):
  for p in people:
   t=next(t for t in server.STATE['plan']['tasks'] if p['slot'] in t['assignees'])
   self.req('/api/response',dict(phaseId='discuss',answers={t['id']:'Done'},submitted=True),p)
 def collab(self,person,**body):return self.req('/api/collab',body,person)
 def answer(self,person,choice,reason='My reason.'):return self.req('/api/progress/answer',dict(kind='initial',phaseId='discuss',answer=choice,reason=reason),person)
 def action(self,**body):return self.req('/api/host/rule-action',body)

 # ---- dictionary
 def test_dictionary_covers_every_problem_family_in_a_stable_order(self):
  self.assertEqual(len(SEEDS),19);self.assertEqual({s['family'] for s in SEEDS},{f['id'] for f in FAMILIES})
  self.assertEqual(ORDER[:3],['role-work','reading-check','peer-use'])
  rules=suggested_rules(server.STATE['plan']);self.assertEqual([r['id'] for r in rules],ORDER)
  on={r['id'] for r in rules if r['enabled']}
  self.assertEqual(on,{'role-work','reading-check','peer-use','support-request','answer-pattern','random-explainer','co-sign','stalled-learner','shared-misconception','closing-pulse'})
  for s in SEEDS:
   for key in ['expectation','evidence','trigger','response','nextTime']:self.assertTrue(s[key],(s['id'],key))
 def test_rules_that_need_a_shared_product_are_unavailable_without_one(self):
  plan=deepcopy(server.STATE['plan']);plan['studio']['flow']='';off=unavailable(plan)
  self.assertEqual(set(off),{'contribution-balance','random-explainer','co-sign','resolve-disagreement'})
  self.assertFalse(any(r['enabled'] for r in suggested_rules(plan) if r['id'] in off))
  self.assertEqual(unavailable(server.STATE['plan']),{})
 def test_reads_never_change_the_classroom(self):
  self.turn_on(quiet_team=True,own_words=True,contribution_balance=True,shared_blocker=True,workload_balance=True,rotation=True,early_finish=True,resolve_disagreement=True,specific_feedback=True)
  self.join(*self.people[:4]);self.live('discuss',300);self.req('/api/host');self.req('/api/state',person=self.people[0]);before=deepcopy(server.STATE)  # the first read creates empty stores
  self.assertEqual(self.req('/api/host')[0],200);self.assertEqual(self.req('/api/state',person=self.people[0])[0],200)
  self.assertEqual(self.req('/api/host/progress-analyze',{})[0],200);self.assertEqual(server.STATE,before)
 def test_heartbeat_leaves_revision_and_adaptive_previews_untouched(self):
  from adaptive_backend import fingerprint
  rev=server.STATE['rev'];key=fingerprint(server.STATE,0)
  status,r=self.collab(self.people[0],kind='edit',scope='own');self.assertEqual(status,200);self.assertEqual(r,{'ok':True})
  self.assertEqual(server.STATE['rev'],rev);self.assertEqual(fingerprint(server.STATE,0),key)
  self.assertGreater(server.STATE['signals']['edits'][self.people[0]['id']]['last'],0)

 # ---- pace
 def test_stalled_learner_needs_a_live_stage_a_joined_learner_and_a_threshold(self):
  self.join(self.people[0]);self.assertEqual(self.signal('stalled-learner')['status'],'waiting')
  self.live('discuss',300);s=self.signal('stalled-learner')
  self.assertEqual(s['status'],'attention');self.assertEqual(s['people'],[self.people[0]['id']]);self.assertIn('Maya: no saved change for 5 min',s['observed'])
  self.collab(self.people[0],kind='edit',scope='own');self.assertEqual(self.signal('stalled-learner')['status'],'collecting')
  server.STATE['signals']={};self.live('discuss',paused=True,remaining=100);self.assertEqual(self.signal('stalled-learner')['status'],'collecting')
  self.live('discuss',300);self.ready();self.assertEqual(self.signal('stalled-learner')['status'],'checked')
 def test_stalled_threshold_is_the_teachers(self):
  self.turn_on(stalled_learner={'minutes':6});self.join(self.people[0]);self.live('discuss',300)
  self.assertEqual(self.signal('stalled-learner')['status'],'collecting')
 def test_time_checks_do_not_run_on_rehearsal_data(self):
  self.join(self.people[0]);self.live('discuss',300)
  s=next(s for s in self.req('/api/host')[1]['previewProgress']['teams'][0]['signals'] if s['id']=='stalled-learner')
  self.assertEqual(s['status'],'waiting')
 def test_quiet_team_counts_shared_edits_and_status_lines_not_speech(self):
  self.turn_on(quiet_team={'minutes':2});self.ready();self.join(*self.people[:4]);self.live('revise',150)
  s=self.signal('quiet-team');self.assertEqual(s['status'],'attention');self.assertIn('Speech is not recorded',s['why'])
  self.assertEqual(self.collab(self.people[1],kind='status',text='')[0],400)
  self.assertEqual(self.collab(self.people[1],kind='status',text='Comparing frames 1 and 7.')[0],200)
  self.assertEqual(self.signal('quiet-team')['status'],'collecting')
  _,view=self.req('/api/state',person=self.people[2]);self.assertEqual(view['progress']['instruments']['status']['text'],'Comparing frames 1 and 7.')
  self.critique(self.people[0]);self.assertEqual(self.signal('quiet-team')['status'],'checked')
 def test_early_finish_uses_the_stage_time_left_at_the_first_save(self):
  self.turn_on(early_finish=True);self.ready();self.live('revise',30);self.critique(self.people[0])
  s=self.signal('early-finish');self.assertEqual(s['status'],'attention');self.assertIn('left',s['observed'])
  server.STATE['signals']['authors']['0']['critique'][0]['remaining']=60;self.assertEqual(self.signal('early-finish')['status'],'checked')
 def test_early_finish_is_unknown_outside_a_timed_stage(self):
  self.turn_on(early_finish=True);self.ready();self.critique(self.people[0]);self.assertEqual(self.signal('early-finish')['status'],'waiting')
 def test_shared_blocker_is_a_class_level_alert(self):
  self.turn_on(shared_blocker=True);self.assertEqual(self.class_signal('shared-blocker')['status'],'waiting')
  self.join(*self.people);self.live('discuss',7*60);s=self.class_signal('shared-blocker')
  self.assertEqual(s['status'],'attention');self.assertEqual(s['scope'],'class');self.assertEqual(s['groups'],[0,1]);self.assertIn('8 of 8 learners',s['observed'])
  self.ready();s=self.class_signal('shared-blocker');self.assertEqual(s['status'],'attention');self.assertEqual(s['groups'],[1])
  self.share(self.people[4:]);self.assertEqual(self.class_signal('shared-blocker')['status'],'checked')
 def test_two_teams_asking_for_smaller_steps_is_a_shared_blocker(self):
  self.turn_on(shared_blocker=True)
  for p in [self.people[0],self.people[4]]:self.req('/api/help',dict(requestKind='difficulty',text='Smaller steps please.'),p)
  s=self.class_signal('shared-blocker');self.assertEqual(s['status'],'attention');self.assertIn('2 teams asked',s['observed'])
 def test_role_workload_compares_the_same_role_across_teams(self):
  self.turn_on(workload_balance=True);self.join(*self.people);self.live('discuss',60)
  self.share([p for p in self.people if p['slot']!=1]);self.assertEqual(self.class_signal('workload-balance')['status'],'collecting')
  self.live('discuss',7*60);s=self.class_signal('workload-balance');self.assertEqual(s['status'],'attention');self.assertIn('in 2 of 2 teams',s['observed']);self.assertIn('role’s task',s['why'])
 def test_everyone_late_is_not_a_role_problem(self):
  self.turn_on(workload_balance=True);self.join(*self.people);self.live('discuss',7*60)
  self.assertEqual(self.class_signal('workload-balance')['status'],'checked')

 # ---- loafing and divide-and-conquer
 def test_one_author_past_the_midpoint_prompts_a_question_not_a_verdict(self):
  self.turn_on(contribution_balance=True);self.ready();self.join(*self.people[:4]);self.live('revise',60);self.critique(self.people[0])
  self.assertEqual(self.signal('contribution-balance')['status'],'collecting')
  self.live('revise',4*60);s=self.signal('contribution-balance');self.assertEqual(s['status'],'attention');self.assertIn('Maya saved every part',s['observed']);self.assertIn('ask before judging',s['why'])
  self.critique(self.people[2],1,change='Label who is counted in each frame.')
  s=self.signal('contribution-balance');self.assertEqual(s['status'],'checked');self.assertIn('Maya and Noor',s['observed'])
  _,view=self.req('/api/state',person=self.people[1]);self.assertEqual(view['progress']['instruments']['authors']['names'],['Maya','Noor'])
 def test_sign_off_comes_from_a_non_author_and_tracks_the_version(self):
  self.ready();self.join(*self.people[:4]);self.assertEqual(self.signal('co-sign')['status'],'collecting')
  self.critique(self.people[0])
  self.assertEqual(self.collab(self.people[0],kind='signoff',version=1,agree=True,note='Looks right.')[0],400)
  self.assertEqual(self.collab(self.people[1],kind='signoff',version=1,agree=True,note='')[0],400)
  self.assertEqual(self.collab(self.people[1],kind='signoff',version=7,agree=True,note='Stale.')[0],400)
  self.assertEqual(self.signal('co-sign')['status'],'collecting')
  server.STATE['studioGroups']['0']['critique']['updated']-=200;self.assertEqual(self.signal('co-sign')['status'],'attention')
  self.assertEqual(self.collab(self.people[1],kind='signoff',version=1,agree=True,note='The labels in frames 1 and 7 support this.')[0],200)
  s=self.signal('co-sign');self.assertEqual(s['status'],'checked');self.assertIn('Agrees:',s['records'][0]['text'])
  self.critique(self.people[0],1,message='A new claim.');s=self.signal('co-sign');self.assertEqual(s['status'],'collecting');self.assertIn('older version',s['observed'])
  _,view=self.req('/api/state',person=self.people[1]);self.assertFalse(view['progress']['instruments']['signoff']['entries'][0]['current'])
 def test_an_objection_at_sign_off_goes_to_the_teacher(self):
  self.ready();self.join(*self.people[:4]);self.critique(self.people[0])
  self.collab(self.people[3],kind='signoff',version=1,agree=False,note='The change does not address frame 4.')
  s=self.signal('co-sign');self.assertEqual(s['status'],'review');self.assertEqual(s['people'],[self.people[3]['id']])
 def test_random_explainer_is_private_picked_once_and_read_by_the_teacher(self):
  self.ready();self.join(*self.people[:4]);self.assertEqual(self.signal('random-explainer')['status'],'collecting')
  self.critique(self.people[0]);pick=server.STATE['signals']['explainer']['0']['person'];self.assertNotEqual(pick,self.people[0]['id'])
  chosen=next(p for p in self.people if p['id']==pick);other=next(p for p in self.people[1:4] if p['id']!=pick)
  self.assertEqual(self.collab(other,kind='explain',text='Not mine.')[0],400)
  _,mine=self.req('/api/state',person=chosen);_,theirs=self.req('/api/state',person=other)
  self.assertTrue(mine['progress']['instruments']['explainer']['mine']);self.assertFalse(theirs['progress']['instruments']['explainer']['mine'])
  self.collab(chosen,kind='explain',text='Because.');self.assertEqual(self.signal('random-explainer')['status'],'attention')
  text='Each frame counts a narrower group, so the map shrinks without the population falling.'
  self.collab(chosen,kind='explain',text=text);s=self.signal('random-explainer');self.assertEqual(s['status'],'review');self.assertEqual(s['records'][0]['text'],text)
  _,theirs=self.req('/api/state',person=other);self.assertEqual(theirs['progress']['instruments']['explainer']['text'],'')
  self.critique(self.people[0],1,message='Edited.');self.assertEqual(server.STATE['signals']['explainer']['0']['person'],pick)
  status,r=self.action(kind='explainer-pick',group=0);self.assertEqual(status,200);self.assertNotEqual(r['person'],pick)
  self.assertEqual(len(server.STATE['signals']['explainer']['0']['history']),1)
 def test_a_missing_explanation_alerts_after_the_wait(self):
  self.turn_on(random_explainer={'minutes':1});self.ready();self.join(*self.people[:4]);self.critique(self.people[0])
  server.STATE['signals']['explainer']['0']['pickedAt']-=90;self.assertEqual(self.signal('random-explainer')['status'],'attention')

 # ---- agreement
 def test_a_shared_wrong_answer_goes_to_the_teacher_not_to_more_discussion(self):
  for p in self.people[:4]:self.answer(p,'time','It falls over time.')
  s=self.signal('shared-misconception');self.assertEqual(s['status'],'attention');self.assertEqual(len(s['records']),4)
  pattern=self.signal('answer-pattern');self.assertEqual(pattern['status'],'inactive');self.assertIn('wrong',pattern['observed'])
  self.assertEqual(self.signal('reading-check')['status'],'attention')
 def test_shared_right_or_mixed_answers_do_not_fire_the_misconception_rule(self):
  for p in self.people[:4]:self.answer(p,'filter')
  self.assertEqual(self.signal('shared-misconception')['status'],'checked');self.assertEqual(self.signal('answer-pattern')['status'],'attention')
  for p,choice in zip(self.people[4:],['time','filter','time','time']):self.answer(p,choice)
  self.assertEqual(self.signal('shared-misconception',1)['status'],'inactive')
 def test_a_recorded_difference_needs_a_why_not_note(self):
  self.turn_on(resolve_disagreement=True);self.ready();self.join(*self.people[:4])
  self.assertEqual(self.signal('resolve-disagreement')['status'],'inactive')
  for p,choice in zip(self.people[:4],['time','filter','filter','filter']):self.answer(p,choice)
  self.assertEqual(self.signal('resolve-disagreement')['status'],'collecting')
  self.critique(self.people[1]);s=self.signal('resolve-disagreement');self.assertEqual(s['status'],'attention');self.assertIn('First choices differ (3 / 1)',s['observed'])
  self.collab(self.people[1],kind='whynot',text='Too short');self.assertEqual(self.signal('resolve-disagreement')['status'],'attention')
  self.collab(self.people[1],kind='whynot',text='We rejected “falls over time” because every frame is the same year.')
  s=self.signal('resolve-disagreement');self.assertEqual(s['status'],'review');self.assertIn('same year',s['records'][0]['text'])
 def test_an_unheard_point_is_a_request_and_a_recorded_difference(self):
  self.turn_on(resolve_disagreement=True);self.ready();self.critique(self.people[0])
  self.assertEqual(self.req('/api/help',dict(requestKind='unheard',text='My point was not discussed.'),self.people[2])[0],200)
  self.assertEqual(self.signal('support-request')['people'],[self.people[2]['id']])
  self.assertIn('not discussed',self.signal('resolve-disagreement')['observed'])

 # ---- processing and outsourcing
 def test_feedback_length_prompts_a_read_and_is_not_a_quality_score(self):
  self.turn_on(specific_feedback=True);self.ready();self.join(*self.people[:4]);self.assertEqual(self.signal('specific-feedback')['status'],'collecting')
  self.critique(self.people[0]);self.collab(self.people[1],kind='signoff',version=1,agree=True,note='ok')
  s=self.signal('specific-feedback');self.assertEqual(s['status'],'attention');self.assertIn('does not measure quality',s['why'])
  self.collab(self.people[1],kind='signoff',version=1,agree=True,note='The misreading matches what I saw in frames 3 and 4.')
  self.assertEqual(self.signal('specific-feedback')['status'],'checked')
 def test_closing_check_opens_late_and_stays_private(self):
  self.join(*self.people[:4]);_,view=self.req('/api/state',person=self.people[1]);self.assertFalse(view['progress']['instruments']['pulse']['open'])
  self.assertEqual(self.collab(self.people[1],kind='pulse',contributed='yes',used='yes')[0],400)
  self.ready();self.critique(self.people[0])
  self.assertEqual(self.collab(self.people[1],kind='pulse',contributed='yes',used='maybe')[0],400)
  self.assertEqual(self.collab(self.people[1],kind='pulse',contributed='yes',used='no',change='Read my notes before writing.')[0],200)
  s=self.signal('closing-pulse');self.assertEqual(s['status'],'attention');self.assertEqual(s['people'],[self.people[1]['id']]);self.assertIn('Was your work used?',s['observed'])
  _,peer=self.req('/api/state',person=self.people[2]);self.assertIsNone(peer['progress']['instruments']['pulse']['mine'])
  self.assertNotIn('Read my notes',str(peer))
 def test_all_yes_is_cross_checked_against_the_record(self):
  self.turn_on(co_sign={'minutes':0.5});self.ready();self.join(*self.people[:4]);self.critique(self.people[0])
  for p in self.people[:4]:self.collab(p,kind='pulse',contributed='yes',used='yes')
  self.assertEqual(self.signal('closing-pulse')['status'],'checked')
  server.STATE['studioGroups']['0']['critique']['updated']-=200
  s=self.signal('closing-pulse');self.assertEqual(s['status'],'review');self.assertIn('Decisions have a second sign-off',s['observed'])
 def test_paste_records_length_only(self):
  self.turn_on(own_words={'minChars':80});secret='pasted answer text'
  _,view=self.req('/api/state',person=self.people[0]);self.assertEqual(view['progress']['instruments']['paste'],{'minChars':80,'block':False})
  _,r=self.collab(self.people[0],kind='paste',chars=20,field='Your finding',text=secret);self.assertFalse(r['noted']);self.assertEqual(self.signal('own-words')['status'],'collecting')
  _,r=self.collab(self.people[0],kind='paste',chars=412,field='Your finding',text=secret);self.assertTrue(r['noted'])
  s=self.signal('own-words');self.assertEqual(s['status'],'attention');self.assertIn('412 characters',s['observed']);self.assertNotIn(secret,str(server.STATE.get('signals')))
 def test_blocked_paste_is_shown_for_review(self):
  self.turn_on(own_words={'minChars':80,'block':True});self.collab(self.people[0],kind='paste',chars=300,field='Your finding')
  self.assertEqual(self.signal('own-words')['status'],'review')
 def test_instruments_follow_the_enabled_rules(self):
  _,view=self.req('/api/state',person=self.people[0]);self.assertEqual(set(view['progress']['instruments']),{'heartbeat','unheard','authors','signoff','explainer','pulse'})
  self.turn_on(co_sign=False,random_explainer=False,closing_pulse=False,stalled_learner=False,support_request=False)
  _,view=self.req('/api/state',person=self.people[0]);self.assertEqual(view['progress']['instruments'],{})
  self.assertEqual(self.collab(self.people[0],kind='signoff',version=1,agree=True,note='x')[0],400)

 # ---- fatigue
 def test_rotation_reads_earlier_activities_by_name(self):
  self.turn_on(rotation={'times':3});self.join(*self.people[:4]);self.assertEqual(self.class_signal('rotation')['status'],'waiting')
  team=[dict(name=p['name'],group=0,role=r) for p,r in zip(self.people[:4],['author','reader','checker','editor'])]
  server.STATE['ruleLibrary']={'carry':[],'custom':[],'runs':[dict(id='a',people=team,rules=[],incidents=[]),dict(id='b',people=team,rules=[],incidents=[])]}
  s=self.class_signal('rotation');self.assertEqual(s['status'],'attention');self.assertIn('Maya is Story Author for time 3',s['observed'])
  server.STATE['ruleLibrary']['runs'][1]['people']=[dict(name='Maya',group=1,role='reader'),dict(name='Zed',group=1,role='author')]
  self.assertNotIn('Maya',self.class_signal('rotation')['observed'])

 # ---- teacher actions and the library
 def test_handled_holds_until_the_evidence_changes(self):
  self.turn_on(own_words=True);self.collab(self.people[0],kind='paste',chars=300,field='Your finding');s=self.signal('own-words')
  self.assertEqual(self.action(kind='handle',group=0,ruleId='own-words',key='stale')[0],400)
  self.assertEqual(self.action(kind='handle',group=0,ruleId='own-words',key=s['key'],note='Asked Maya to explain it aloud.')[0],200)
  s=self.signal('own-words');self.assertEqual(s['status'],'addressed');self.assertEqual(s['handled']['note'],'Asked Maya to explain it aloud.')
  self.assertEqual(server.STATE['ruleLog'][0]['outcome'],'handled')
  self.collab(self.people[0],kind='paste',chars=500,field='Your finding');self.assertEqual(self.signal('own-words')['status'],'attention')
  self.assertEqual(self.action(kind='handle',group=1,ruleId='own-words',key='x')[0],400)
 def test_seen_alerts_are_logged_once(self):
  self.turn_on(own_words=True);self.collab(self.people[0],kind='paste',chars=300,field='Your finding');s=self.signal('own-words')
  item=dict(group=0,ruleId='own-words',key=s['key'])
  self.assertEqual(self.action(kind='seen',items=[item,item])[1]['added'],1);self.assertEqual(self.action(kind='seen',items=[item])[1]['added'],0)
  self.assertEqual(self.action(kind='seen',items=[dict(group=0,ruleId='own-words',key='other')])[1]['added'],0)
  self.assertEqual(len(self.host()['log']),1)
 def test_next_time_applies_to_the_next_activity_only(self):
  self.assertEqual(self.action(kind='carry',ruleId='contribution-balance',note='')[0],400)
  self.assertEqual(self.action(kind='carry',ruleId='stalled-learner',note='Four minutes was too long for this task.',params={'minutes':2},group=0)[0],200)
  self.assertEqual(self.action(kind='carry',ruleId='contribution-balance',note='One member wrote every critique. Turn this on.')[0],200)
  now={r['id']:r for r in self.host()['suggestions']};self.assertFalse(now['contribution-balance']['enabled']);self.assertEqual(now['stalled-learner']['params']['minutes'],4)
  self.join(self.people[0]);self.assertEqual(self.req('/api/host/new',{})[0],200)
  library=server.STATE['ruleLibrary'];self.assertEqual(len(library['carry']),2);self.assertEqual(len(library['runs']),1);self.assertEqual(library['runs'][0]['people'][0]['name'],'Maya')
  self.rebuild();later={r['id']:r for r in self.host()['suggestions']}
  self.assertTrue(later['contribution-balance']['enabled']);self.assertEqual(later['stalled-learner']['params']['minutes'],2)
  self.assertEqual(later['contribution-balance']['carried']['note'],'One member wrote every critique. Turn this on.')
  self.assertEqual(self.host()['library']['runs'],1)
  carry=self.host()['library']['carry'][0];self.assertEqual(self.action(kind='carry-remove',id=carry['id'])[0],200);self.assertEqual(len(self.host()['library']['carry']),1)
 def rebuild(self):
  from model import tasks_for
  from collab_workflow import group_first_plan
  p=deepcopy(server.STATE['plan']);p.update(planned=True,materialId='81',structure='Role Play',groupCount=2,groupSize=4,budget=18,studio={'review':'summary','exchange':'compare'})
  p['interaction']['mode']='async';p['tasks']=tasks_for('81','Role Play',4);p=group_first_plan(p)
  status,body=self.req('/api/host/plan',{'plan':p,'planRev':server.STATE['planRev']});self.assertEqual(status,200,body)
  self.req('/api/host/deploy',{'planRev':server.STATE['planRev']})
  self.people=sorted([p for p in server.STATE['people'] if p['active']],key=lambda p:(p['group'],p['slot']))
 def test_a_teacher_rule_can_use_a_ready_made_signal_and_is_remembered(self):
  rules=suggested_rules(server.STATE['plan']);base=next(r for r in rules if r['id']=='quiet-team')
  mine=dict(base,id='custom-quiet-opening',title='Opening talk gets going',phaseId='read',enabled=True,params={'minutes':1},origin='custom')
  self.assertEqual(self.save(rules+[dict(mine,condition='co_sign')])[0],400)
  self.assertEqual(self.save(rules+[mine])[0],200)
  self.join(*self.people[:4]);self.live('read',90);s=self.signal('custom-quiet-opening');self.assertEqual(s['status'],'attention');self.assertEqual(s['family'],'quiet')
  self.assertEqual(server.STATE['ruleLibrary']['custom'][0]['id'],'custom-quiet-opening')
  server.STATE['plan']['live'].update(started=False);self.req('/api/host/new',{});self.rebuild()
  offered=next(r for r in self.host()['suggestions'] if r['id']=='custom-quiet-opening');self.assertFalse(offered['enabled']);self.assertTrue(offered['remembered'])
  self.assertEqual(self.action(kind='forget-custom',id='custom-quiet-opening')[0],200)
  self.assertFalse(any(r['id']=='custom-quiet-opening' for r in self.host()['suggestions']))
 def test_plain_words_match_ready_signals_by_keyword_only(self):
  _,r=self.req('/api/host/rule-compile',dict(text='A student is stuck and has not typed anything'))
  self.assertEqual(r['matches'][0]['condition'],'stalled_learner');self.assertTrue(r['matches'][0]['custom']);self.assertIn('no model call',r['source'])
  self.assertEqual(match_text('Students respect each other'),[]);self.assertEqual(match_text('install the tool and relate it'),[])
 def test_plain_words_find_the_library_rule_before_a_new_one_is_written(self):
  top=lambda text:match_text(text)[0]
  self.assertEqual(top('one student writes everything and the others just watch')['ruleId'],'contribution-balance')
  self.assertEqual(top('They split the work and never read each other’s part')['ruleId'],'co-sign')
  self.assertEqual(top('feedback is vague, just nice job')['ruleId'],'specific-feedback')
  self.assertFalse(top('the same teams every week, students are bored')['custom'])
  from rule_library import KEYWORDS
  self.assertEqual(set(KEYWORDS),{s['id'] for s in SEEDS}|{'participation','role-clarity'})
 def test_past_runs_show_how_often_a_rule_fired(self):
  server.STATE['ruleLibrary']={'carry':[],'custom':[],'runs':[dict(id='a',people=[],rules=['co-sign','own-words'],incidents=[dict(ruleId='co-sign',group=0,outcome='handled'),dict(ruleId='co-sign',group=1,outcome='open')]),dict(id='b',people=[],rules=['co-sign'],incidents=[])]}
  stats=self.host()['library']['stats'];self.assertEqual(stats['co-sign'],dict(runs=2,firedRuns=1,alerts=2,handled=1));self.assertEqual(stats['own-words']['alerts'],0)
 def test_added_time_keeps_the_stage_and_moves_the_checkpoint(self):
  self.join(self.people[0]);self.live('discuss',7*60);self.assertEqual(self.signal('role-work')['status'],'attention')
  self.assertEqual(self.req('/api/host/live',dict(command='extend',minutes=3))[0],200)
  self.assertEqual(self.signal('role-work')['status'],'collecting');self.assertEqual(server.STATE['plan']['live']['phaseId'],'discuss')
  self.assertEqual(self.req('/api/host/live',dict(command='extend',minutes=60))[0],400)
 def test_student_preview_of_a_rule_is_isolated_from_the_class(self):
  rules=suggested_rules(server.STATE['plan']);before=deepcopy(server.STATE)
  status,run=self.req('/api/host/rule-preview',dict(rules=rules,ruleId='resolve-disagreement'));self.assertEqual(status,200,run);self.assertEqual(server.STATE,before)
  path='/api/test/'+run['id']+'?person='+run['person']
  _,view=self.req(path+'&action=/api/state');tools=view['progress']['instruments'];self.assertIn('whyNot',tools);self.assertTrue(view['studioGroup']['critique']['message'])
  self.assertEqual(self.req(path+'&action=/api/collab',dict(kind='whynot',text='A note written in the preview.'))[0],200)
  self.assertEqual(server.STATE,before)
  self.assertEqual(self.req('/api/host/rule-preview',dict(rules=rules,ruleId='missing'))[0],400)
 def test_student_preview_shows_only_what_the_draft_rules_add(self):
  rules=suggested_rules(server.STATE['plan'])
  for r in rules:r['enabled']=False
  _,run=self.req('/api/host/rule-preview',dict(rules=rules,ruleId='co-sign'));path='/api/test/'+run['id']+'?person='+run['person']+'&action=/api/state'
  self.assertEqual(sorted(self.req(path)[1]['progress']['instruments']),['authors','signoff'])
  _,run=self.req('/api/host/rule-preview',dict(rules=rules,ruleId='random-explainer'));path='/api/test/'+run['id']+'?person='+run['person']+'&action=/api/state'
  self.assertTrue(self.req(path)[1]['progress']['instruments']['explainer']['mine'])

 def test_walkthrough_example_fires_the_sign_off_rule_and_closes_with_a_teacher_note(self):
  """The data behind the tutorial steps: one author, no reader, an objection at sign-off, then a note and a decision for next time."""
  server.STATE['tutorialSession']=True;self.people[0]['claimed']=True;self.turn_on(co_sign=True)
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'rule-library-evidence'})[0],400)
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'collaboration-evidence'})[0],200)
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'rule-library-evidence'})[0],400)
  eli=self.people[1];server.STATE['responses'][eli['id']]['discuss:submitted']=True
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'rule-library-evidence'})[0],200)
  self.req('/api/host/live',dict(command='stage',phaseId='revise'))
  alert=self.signal('co-sign');self.assertEqual(alert['status'],'attention');self.assertIn('Saved by Maya',alert['observed'])
  self.assertEqual(self.signal('co-sign',1)['status'],'collecting')
  before=deepcopy(server.STATE['studioGroups']['0']['critique'])
  self.assertEqual(self.req('/api/host/tutorial-examples',{'kind':'rule-library-evidence'})[0],200)
  self.assertEqual(server.STATE['studioGroups']['0']['critique'],before)
  self.assertEqual(self.collab(eli,kind='signoff',version=1,agree=False,note='The first frame is not land area.')[0],200)
  read=self.signal('co-sign');self.assertEqual(read['status'],'review');self.assertEqual(read['people'],[eli['id']])
  self.assertEqual(self.req('/api/host/rule-action',dict(kind='handle',group=0,ruleId='co-sign',key=read['key'],note='Read with the team.'))[0],200)
  self.assertEqual(self.signal('co-sign')['status'],'addressed')
  self.assertEqual(self.req('/api/host/rule-action',dict(kind='carry',ruleId='co-sign',note='Sign-off from the start.',group=0,enable=True))[0],200)
  self.assertEqual([c['ruleId'] for c in self.host()['library']['carry']],['co-sign'])
if __name__=='__main__':unittest.main()
