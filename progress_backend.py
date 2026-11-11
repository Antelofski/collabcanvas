"""Observable progress and instructor-controlled support; no inferred speech or AI grading."""
from copy import deepcopy
import secrets, time
from progress_rules import effective_rules, suggested_rules, rule_signals, rule_fingerprint, FLAGS

QUESTIONS={
 'initial':dict(prompt='What makes the maps smaller across the story?',options=[['time','The same population falls over time.'],['filter','Each frame keeps a smaller group of people.'],['land','The states lose land area.']],answer='filter'),
 'followup':dict(prompt='Could a state shrink in this story even if its total population stayed constant?',options=[['yes','Yes. A later frame counts a narrower group of people.'],['no','No. A smaller map always means fewer residents over time.'],['geo','No. The maps show changes in land area.']],answer='yes')}

def supported(plan):return plan.get('materialId')=='81' and plan.get('structure')=='Role Play'
def config(plan):
 c={'privateCheck':True,'submissions':True,'rubric':True,'participation':False,**plan.get('progress',{})}
 if 'rules' in c:
  for rid,flag in FLAGS.items():c[flag]=any(r['id']==rid and r['enabled'] for r in c['rules'])
  reading=next((r for r in c['rules'] if r['id']=='reading-check'),None)
  if reading:c['checkPhase']=reading['phaseId']
 return c
def records(state,preview=False):return state.setdefault('previewProgress' if preview else 'progressRecords',{'answers':{},'teams':{},'events':[]})
def initial_phase(plan):return config(plan).get('checkPhase') or next((p['id'] for p in plan['phases'] if p['kind']=='individual'),plan['phases'][0]['id'])
def public_question(kind):return {k:deepcopy(v) for k,v in QUESTIONS[kind].items() if k!='answer'}
def learner_progress(state,person,preview=False):
 if not supported(state['plan']):return None
 r=records(state,preview);own=deepcopy(r['answers'].get(person['id'],{}));team=r['teams'].get(str(person['group']),{});support=deepcopy(team.get('support'))
 if support:
  support.pop('targets',None);support['needsFollowup']=person['id'] in team['support']['targets']
 from adaptive_backend import learner_view
 from collab_signals import instruments
 return dict(config=config(state['plan']),phase=initial_phase(state['plan']),answers=own,questions={k:public_question(k) for k in QUESTIONS},support=support,adaptive=learner_view(state,person,preview),instruments=instruments(state,person,preview))

def save_answer(state,person,body,preview=False):
 if not supported(state['plan']) or body.get('kind')=='initial' and not config(state['plan'])['privateCheck']:raise ValueError('Private checks are not enabled for this activity.')
 kind=body.get('kind');r=records(state,preview);team=r['teams'].get(str(person['group']),{})
 if kind not in QUESTIONS:raise ValueError('Choose a valid check.')
 if kind=='initial' and body.get('phaseId')!=initial_phase(state['plan']):raise ValueError('Open the private-check stage first.')
 if kind=='followup' and person['id'] not in team.get('support',{}).get('targets',[]):raise ValueError('No follow-up check is assigned to you.')
 answer=body.get('answer');reason=str(body.get('reason','')).strip()[:3000]
 if answer not in [x[0] for x in QUESTIONS[kind]['options']] or not reason:raise ValueError('Choose an answer and give a short reason.')
 own=r['answers'].setdefault(person['id'],{})
 if kind in own:raise ValueError('This answer is already saved. Your initial response is kept for comparison.')
 own[kind]=dict(answer=answer,reason=reason,correct=answer==QUESTIONS[kind]['answer'],time=time.time())
 return deepcopy(own[kind])

def evidence(state,group,preview=False):
 r=records(state,preview);people=sorted([p for p in state['people'] if p['active'] and p['group']==group],key=lambda p:p['slot']);team=r['teams'].get(str(group),{});answers=r['answers']
 rows=[]
 for p in people:
  role=next((t['title'] for t in state['plan']['tasks'] if p['slot'] in t['assignees']),'Learner')
  rows.append(dict(person=p['id'],name=p['name'] or role,role=role,initial=deepcopy(answers.get(p['id'],{}).get('initial')),followup=deepcopy(answers.get(p['id'],{}).get('followup'))))
 answered=sum(bool(x['initial']) for x in rows);wrong=sum(bool(x['initial']) and not x['initial']['correct'] for x in rows)
 followups=[x['followup'] for x in rows if x['followup']]
 phases=[x['id'] for x in state['plan']['phases'] if x['kind']=='individual'];responses=state.get('previewResponses' if preview else 'responses',{})
 submitted=sum(bool(phases) and all(responses.get(p['id'],{}).get(s+':submitted') for s in phases) for p in people)
 support=deepcopy(team.get('support'));review=deepcopy(team.get('review',{}))
 if support and support.get('resolved'):status='Reviewed by instructor'
 elif support:status='Support in progress'
 elif wrong and answered==len(people):status=f'{wrong} answers need review'
 elif answered:status=f'{answered} / {len(people)} checks saved'
 else:status='Waiting for private checks'
 result=dict(group=group,rows=rows,answered=answered,wrong=wrong,total=len(people),submitted=submitted,status=status,support=support,review=review,followupCount=len(followups),followupCorrect=sum(x['correct'] for x in followups))
 result['ruleReviews']=deepcopy(team.get('ruleReviews',{}))
 from collaboration_progress import details
 result['collaboration']=details(state,group,result,preview)
 result['signals']=rule_signals(state,group,result,preview)
 from adaptive_backend import host_team
 result['adaptive']=host_team(state,group,preview)
 return result

def host_progress(state,preview=False):
 if not supported(state['plan']):return None
 from collab_signals import class_signals
 from rule_library import public
 return dict(config=config(state['plan']),rules=effective_rules(state['plan'],state),suggestions=suggested_rules(state['plan'],state),suggestionSource='Seed dictionary of collaboration rules · fitted to this activity’s stages, roles and recorded evidence; no model call.',questions=deepcopy(QUESTIONS),teams=[evidence(state,g,preview) for g in range(state['plan']['groupCount'])],classSignals=class_signals(state,preview),library=public(state['plan'],state),log=deepcopy(state.get('ruleLog',[])[-80:]),drafts=[{k:deepcopy(v) for k,v in d.items() if k!='plan'} for d in state.get('progressDrafts',[])])

def intervene(state,body):
 group=body.get('group')
 if not isinstance(group,int) or not 0<=group<state['plan']['groupCount']:raise ValueError('Choose a valid team.')
 r=records(state);team=r['teams'].setdefault(str(group),{});kind=body.get('kind');now=time.time()
 if kind=='support':
  if body.get('expectedPlanRev',state['planRev'])!=state['planRev']:raise ValueError('The plan changed. Preview support again.')
  if team.get('support'):raise ValueError('This team already has a comparison task. Inspect the follow-up evidence.')
  e=evidence(state,group)
  targets=[x['person'] for x in e['rows'] if x['initial'] and not x['initial']['correct']]
  if not targets:raise ValueError('There are no initial answers needing this follow-up.')
  if 'expectedTargets' in body and sorted(body['expectedTargets'])!=sorted(targets):raise ValueError('The private-check evidence changed. Refresh the team and preview support again.')
  team['support']=dict(id=secrets.token_hex(4),title='Check the population filter',prompt='Compare frames 1 and 7. Read who each frame includes. Explain why the map can shrink without population falling over time.',targets=targets,created=now,resolved=False)
 elif kind=='resolve':
  support=team.get('support')
  if not support:raise ValueError('Open a support task before reviewing its outcome.')
  e=evidence(state,group);note=str(body.get('note','')).strip()[:3000]
  if not body.get('inPerson') and (e['followupCount']<len(support['targets']) or e['followupCorrect']<len(support['targets'])):raise ValueError('Review all assigned follow-up answers first. Use an observation note if more support is needed.')
  if not note:raise ValueError('Record what you checked before marking this addressed.')
  support.update(resolved=True,resolvedAt=now,note=note,reviewBasis='in-person observation' if body.get('inPerson') else 'follow-up answers and instructor review')
 elif kind=='help-reviewed':
  for request in state.get('requests',[]):
   if request.get('group')==group and not request.get('preview'):request.update(resolved=True,resolvedAt=now)
 elif kind=='rule-review':
  rule=next((r for r in effective_rules(state['plan'],state) if r['id']==body.get('ruleId') and r['enabled'] and r['condition']=='teacher_review'),None)
  if not rule:raise ValueError('Choose an enabled teacher-review rule.')
  status=body.get('status');note=str(body.get('note','')).strip()[:3000]
  if status not in ['attention','checked'] or not note:raise ValueError('Choose a status and record the evidence you observed.')
  record=dict(status=status,note=note,time=now,ruleFingerprint=rule_fingerprint(rule))
  team.setdefault('ruleReviewHistory',[]).append(dict(rule=deepcopy(rule),**record))
  team.setdefault('ruleReviews',{})[rule['id']]=record
 elif kind=='review':
  rubric=body.get('rubric','not-reviewed');participation=body.get('participation','not-reviewed');note=str(body.get('note','')).strip()[:3000]
  if rubric not in ['not-reviewed','needs-support','reviewed'] or participation not in ['not-reviewed','needs-support','reviewed']:raise ValueError('Choose a valid observation status.')
  if (rubric!='not-reviewed' or participation!='not-reviewed') and not note:raise ValueError('Add the evidence behind your observation.')
  team['review']=dict(rubric=rubric,participation=participation,note=note,time=now)
 else:raise ValueError('Choose a support action.')
 r['events'].append(dict(group=group,kind=kind,time=now));return evidence(state,group)

def create_draft(state,body):
 if not supported(state['plan']):raise ValueError('Adaptation drafts currently support the voting-story activity.')
 kind=body.get('kind');group=body.get('group',0)
 if kind not in ['next-activity','next-run']:raise ValueError('Choose when to use this draft.')
 if not isinstance(group,int) or not 0<=group<state['plan']['groupCount']:raise ValueError('Choose a valid team.')
 e=evidence(state,group)
 if not e['answered'] and not e['review'].get('note') and not any(r.get('note') for r in e['ruleReviews'].values()):raise ValueError('Collect checks or an instructor observation before preparing an adaptation.')
 p=deepcopy(state['plan']);p['live'].update(started=False,paused=False,phaseId=p['phases'][0]['id'],startedAt=None);p.setdefault('progress',{}).update(config(p))
 if kind=='next-activity':
  from collab_workflow import group_first_plan
  p=group_first_plan(p)
  p['progress']['checkPhase']=p['phases'][0]['id'];p['progress']['beforeDiscussion']=True
  for rule in p['progress'].get('rules',[]):
   if rule['id']=='reading-check':rule['phaseId']=p['phases'][0]['id']
  opening=max(1,round(p['budget']*5/18));final=max(1,round(p['budget']/3))
  p['phases'][0].update(title='Check, then discuss',minutes=opening,instruction='Answer the private reading check before opening the shared discussion. Compare frames 1 and 7, then record a group reading.')
  if len(p['phases'])>=3:p['phases'][1]['minutes']=max(1,p['budget']-opening-final);p['phases'][2]['minutes']=final
  title='Private check before discussion';changes=['Each learner answers before seeing the shared reading.','The opening discussion compares the population groups in frames 1 and 7.','All four role tools and the shared critique stay connected.']
 else:
  title='Clearer role briefs for the next run';changes=['Evidence Checker checks units, population groups, and the story’s date.','First-time Reader records a confusing transition and asks the Checker a question.','Critical Editor responds to the Reader and Checker before drafting the critique.']
  prompts={'checker':'Check the map unit, the population group in frames 1 and 7, and whether the story shows time or filtering. Explain one claim the map cannot support.','reader':'Find one transition that a first-time reader could mistake for change over time. Ask the Evidence Checker a specific question about its label.','editor':'Read the Reader’s question and the Checker’s findings. Explain which claim to keep, which to clarify, and what remains unresolved.'}
  for task in p['tasks']:
   if task.get('roleId') in prompts:task['prompt']=prompts[task['roleId']]
  p.setdefault('studio',{})['adaptedBriefs']=True
 draft=dict(id=secrets.token_hex(5),kind=kind,title=title,changes=changes,created=time.time(),sourcePlanRev=state['planRev'],group=group,evidence=e,plan=p)
 state.setdefault('progressDrafts',[]).append(draft)
 return {k:deepcopy(v) for k,v in draft.items() if k!='plan'}

def draft_session(state,draft_id):
 from collab_workflow import start_test
 d=next((d for d in state.get('progressDrafts',[]) if d['id']==draft_id),None)
 if not d:raise ValueError('This draft is unavailable.')
 clone=deepcopy(state);clone['plan']=deepcopy(d['plan']);return start_test(clone)


def support_comparison(state,body):
 """Read-only before/after snapshots preserving the same learners and existing work."""
 from collab_workflow import TEST_RUNS
 from adaptive_backend import preview_change,apply_change,fingerprint
 if not supported(state['plan']):raise ValueError('This pilot supports the voting-story activity.')
 group=body.get('group');pattern=body.get('pattern','comparison')
 if not isinstance(group,int) or isinstance(group,bool) or not 0<=group<state['plan']['groupCount']:raise ValueError('Choose a valid team.')
 before=deepcopy(state);after=deepcopy(state);proposal=None
 if pattern=='comparison':
  result=intervene(after,dict(kind='support',group=group,expectedTargets=body.get('targets', [r['person'] for r in evidence(state,group)['rows'] if r['initial'] and not r['initial']['correct']])))
  targets=result['support']['targets'];additionId=result['support']['id']
 else:
  proposal=preview_change(state,body)
  changed=apply_change(after,{**proposal,'note':body.get('note') or 'Instructor preview of the proposed support.'})
  targets=changed['targets'];additionId=changed['id']
 now=time.time();ids=[]
 for clone in [before,after]:
  token=secrets.token_urlsafe(18);TEST_RUNS[token]=dict(state=clone,created=now,planRev=state['planRev'],report=None,readOnly=True);ids.append(token)
 people=[{k:v for k,v in p.items() if k!='token'} for p in state['people'] if p['active'] and p['group']==group]
 return dict(before=ids[0],after=ids[1],people=people,targets=targets,additionId=additionId,proposal=proposal,planRev=state['planRev'],evidenceKey=fingerprint(state,group))
