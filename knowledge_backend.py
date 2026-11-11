"""Task-scoped knowledge evidence. Only keyed checks receive automatic content judgments."""
from copy import deepcopy
import hashlib,json,secrets,time

STATUSES={'demonstrated':'Demonstrated on this task','needs-support':'Needs support','needs-check':'Needs checking','not-observed':'Not observed'}

def _digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def learner_record(state,p):
 plan=state['plan'];pid=p['id'];artifact=state.get('artifacts',{}).get(pid,{})
 own_answers=state.get('progressRecords',{}).get('answers',{}).get(pid,{})
 role=next((t for t in plan['tasks'] if p['slot'] in t['assignees']),{})
 role_id=role.get('roleId','');tasks=[]
 def add(tid,title,skill,evidence,status='needs-check',summary='',next_check='Ask the learner to explain a new example independently.'):
  if not evidence:status='not-observed'
  key=_digest(evidence);review=deepcopy(state.get('knowledgeReviews',{}).get(pid,{}).get(tid));stale=bool(review and review['evidenceKey']!=key)
  if review and not stale:status=review['status'];next_check=review.get('nextCheck') or next_check
  elif stale:status='needs-check'
  tasks.append(dict(id=tid,title=title,knowledge=skill,status=status,statusLabel=STATUSES[status],summary=summary or ('Saved individual work; content needs checking.' if evidence else 'No individual evidence saved for this task.'),evidence=deepcopy(evidence),evidenceKey=key,review=review,reviewStale=stale,nextCheck=next_check))
 if plan.get('materialId')=='81' and plan.get('structure')=='Role Play':
  from progress_backend import QUESTIONS
  ev=[]
  for kind in ['initial','followup']:
   a=own_answers.get(kind)
   if a:
    q=QUESTIONS[kind];label=next((text for value,text in q['options'] if value==a['answer']),a['answer'])
    ev.append(dict(source='Individual check' if kind=='initial' else 'Individual follow-up',text=label,reason=a['reason'],correct=a['correct'],time=a.get('time'),scope='individual'))
  latest=ev[-1] if ev else None
  add('population-filter','Explain why the maps shrink','Distinguish population filtering from change over time or land area.',ev,'demonstrated' if latest and latest['correct'] else 'needs-support',summary='Correct on this check'+(' after support.' if latest and latest['source']=='Individual follow-up' else '.') if latest and latest['correct'] else 'The saved choice does not identify population filtering.' if latest else '',next_check='Read a new sequence and explain who each frame counts.')
 role_titles={'author':('Explain the story’s message','Relate area, labels and sequence to a claim.'),'reader':('Identify and explain a confusing transition','Recognize a reading difficulty and formulate a question.'),'checker':('Check a visual claim','Use units and population labels to test a statement.'),'editor':('Evaluate the team’s claims','Judge whether the visual supports a claim.')}
 title,skill=role_titles.get(role_id,(role.get('title','Role task'),role.get('prompt','Explain the assigned task.')))
 ev=[]
 for key in ['beats','observations','checks']:
  for row in artifact.get(key,[]):
   text=row.get('text') or row.get('statement')
   if text:ev.append(dict(source='Role work',text=text,reason=row.get('reason',''),frame=row.get('frame'),scope='individual'))
 for key in ['question','reflection','revision','decision']:
  value=artifact.get(key)
  if isinstance(value,str) and value.strip():ev.append(dict(source='Role work',text=value,scope='individual'))
 for row in artifact.get('reviews',{}).values():
  if row.get('reason'):ev.append(dict(source='Claim review',text=row['reason'],scope='individual'))
 if not ev:
  for key,value in state.get('responses',{}).get(pid,{}).items():
   if isinstance(value,str) and value.strip():ev.append(dict(source='Role response',text=value,scope='individual'))
 add('role-analysis',title,skill,ev)
 team=state.get('adaptive',{}).get('teams',{}).get(str(p['group']),{})
 for change in team.get('changes',[]):
  if pid not in change['targets']:continue
  row=change.get('responses',{}).get(pid,{});values=row.get('values',{})
  if change['pattern']=='scaffold':
   for key,title in [('unit','Read the map unit'),('population','Identify the people counted'),('interpretation','Explain the narrowing population')]:
    text=values.get(key);ev=[dict(source='Smaller-step task',text=text,scope='individual',time=row.get('time'))] if text else []
    if ev and change.get('reviewed'):ev.append(dict(source='Teacher review of support',text=change['reviewNote'],scope='review',time=change.get('reviewedAt')))
    add('support-'+change['id']+'-'+key,title,dict(unit='Interpret area as a count of people.',population='Read the inclusion criteria in frame labels.',interpretation='Explain why a changing subset changes map area.')[key],ev,summary='Recorded after smaller-step support; review is task-specific.' if ev else '')
  else:
   ev=[]
   for key,label in change['spec']['fields']:
    if values.get(key):ev.append(dict(source=label,text=values[key],scope='individual',time=row.get('time')))
   if change['spec'].get('sourceQuestion') and ev:ev.insert(0,dict(source='Question addressed',text=change['spec']['sourceQuestion']['text'],scope='context'))
   if ev and change.get('reviewed'):ev.append(dict(source='Teacher review of exchange',text=change['reviewNote'],scope='review',time=change.get('reviewedAt')))
   add('exchange-'+change['id'],'Respond to a peer’s question' if change['pattern']=='written-exchange' else 'Explain a counterfactual','Use visual evidence to justify an interpretation.',ev)
   if change['pattern']=='reason-check':
    reply=[dict(source='Linked peer response',text=row['reply'],scope='individual',replyTo=row.get('replyTo'),time=row.get('time'))] if row.get('reply') else []
    add('peer-check-'+change['id'],'Check a peer’s explanation','Respond to a teammate’s reasoning with evidence.',reply)
 requests=[dict(text=r['text'],resolved=bool(r.get('resolved')),time=r.get('time')) for r in state.get('requests',[]) if r.get('person')==pid and not r.get('preview')]
 counts={status:sum(t['status']==status for t in tasks) for status in STATUSES}
 return dict(person=pid,name=p['name'] or 'Learner '+chr(65+p['slot']),group=p['group'],role=role.get('title','Learner'),claimed=p.get('claimed',False),tasks=tasks,counts=counts,supportRequests=requests)

def report(state,snapshot=None):
 if snapshot:
  saved=next((x for x in state.get('knowledgeReports',[]) if x['id']==snapshot),None)
  if not saved:raise ValueError('This saved report is unavailable.')
  result=deepcopy(saved['report']);result.update(snapshot=snapshot,savedAt=saved['created'],readOnly=True)
 else:
  result=dict(activity=state['plan']['title'],material=state['plan']['materialId'],generatedAt=time.time(),planRev=state['planRev'],readOnly=False,learners=[learner_record(state,p) for p in state['people'] if p['active']],basis='Individual task evidence from this activity. A completed task or group answer is not an estimate of individual mastery.')
 result['snapshots']=[dict(id=x['id'],created=x['created'],activity=x['report']['activity']) for x in state.get('knowledgeReports',[])]
 return result

def review(state,body):
 p=next((p for p in state['people'] if p['active'] and p['id']==body.get('person')),None)
 if not p:raise ValueError('Choose a current learner.')
 task=next((t for t in learner_record(state,p)['tasks'] if t['id']==body.get('task')),None)
 if not task:raise ValueError('Choose a current task.')
 if body.get('evidenceKey')!=task['evidenceKey']:raise ValueError('The evidence changed. Open this task again before reviewing.')
 status=body.get('status');note=str(body.get('note','')).strip()[:3000];next_check=str(body.get('nextCheck','')).strip()[:1500]
 if status not in STATUSES or not note:raise ValueError('Choose a status and record what you checked.')
 if status=='demonstrated' and not task['evidence']:raise ValueError('Save individual evidence before marking this task demonstrated.')
 own=state.setdefault('knowledgeReviews',{}).setdefault(p['id'],{});old=own.get(task['id'],{})
 if body.get('version',0)!=old.get('version',0):raise ValueError('Another review was saved. Reload before editing.')
 row=dict(status=status,note=note,nextCheck=next_check,evidenceKey=task['evidenceKey'],version=old.get('version',0)+1,time=time.time())
 own[task['id']]=row;state.setdefault('knowledgeReviewHistory',[]).append(dict(person=p['id'],task=task['id'],**deepcopy(row)))
 return deepcopy(row)

def save_snapshot(state):
 value=report(state);value.pop('snapshots',None)
 snapshot=dict(id=secrets.token_hex(6),created=time.time(),report=value)
 state.setdefault('knowledgeReports',[]).append(snapshot)
 return dict(id=snapshot['id'],created=snapshot['created'])
