"""Teacher-controlled additions to connected interfaces in the local InfoVis pilot.

No behavioural diagnosis or model call. Private checks never become peer posts.
"""
from copy import deepcopy
import hashlib, json, secrets, time

PATTERNS = {
 'scaffold': dict(title='Break the role task into three steps', short='Add step-by-step support',
   purpose='Reduce the amount to handle at once. Keep the same reading task.',
   prompt='Read the unit, identify the people counted, then explain the change.',
   fields=[['unit','What does one square count?'],['population','Who is included in the first and last frames?'],['interpretation','Why does the map get smaller?']],
   handoff='The shared note appears beside the team’s critique. The Editor can use it to check the final claim.'),
 'written-exchange': dict(title='Make room for a written exchange', short='Open a written exchange',
   purpose='Offer another way to contribute and respond to a peer.',
   prompt='Share a question or reading. Read a teammate’s contribution and respond to its reasoning.',
   fields=[['idea','Your question or reading'],['evidence','Which label or frame supports it?']],
   handoff='All team members receive the same exchange. Shared contributions and linked replies carry into the final critique.'),
 'reason-check': dict(title='Test an agreed answer', short='Compare reasons and test the claim',
   purpose='Check the reasoning behind agreement before adding more discussion.',
   prompt='Suppose a state has the same number of residents in every frame. Could its map still shrink? Use the labels to explain, then check a peer’s reason.',
   fields=[['idea','Your explanation'],['evidence','Which population labels support your explanation?']],
   handoff='Students explicitly share new explanations. Private answers stay private. The Editor uses the discussion to qualify the group claim.')
}

def store(state, preview=False):
 return state.setdefault('previewAdaptive' if preview else 'adaptive', {'teams':{}})

def people_in(state, group):
 return [p for p in state['people'] if p['active'] and p['group']==group]

def current_requests(state, group, preview=False):
 return [r for r in state.get('requests',[]) if r['group']==group and bool(r.get('preview'))==preview and not r.get('resolved')]

def fingerprint(state, group):
 progress=state.get('progressRecords',{})
 snapshot={'planRev':state['planRev'],'answers':[(p['id'],progress.get('answers',{}).get(p['id'],{}).get('initial')) for p in people_in(state,group)],
           'requests':current_requests(state,group), 'observations':progress.get('teams',{}).get(str(group),{}).get('ruleReviews',{})}
 ids=[p['id'] for p in people_in(state,group)]
 snapshot['roleWork']={pid:state.get('artifacts',{}).get(pid) for pid in ids}
 snapshot['submissions']={pid:state.get('responses',{}).get(pid) for pid in ids}
 snapshot['sharedWork']=state.get('studioGroups',{}).get(str(group))
 snapshot['additions']=[{k:c.get(k) for k in ['id','pattern','targets','reviewed','responses']} for c in state.get('adaptive',{}).get('teams',{}).get(str(group),{}).get('changes',[])]
 return hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest()

def host_team(state, group, preview=False):
 team=deepcopy(state.get('previewAdaptive' if preview else 'adaptive',{}).get('teams',{}).get(str(group),{}))
 team['requests']=deepcopy(current_requests(state,group,preview))
 team['evidenceKey']=fingerprint(state,group) if not preview else ''
 return team

def learner_view(state, person, preview=False):
 team=state.get('previewAdaptive' if preview else 'adaptive',{}).get('teams',{}).get(str(person['group']),{})
 result=[]
 for change in team.get('changes',[]):
  if person['id'] not in change['audience']:continue
  item={k:deepcopy(v) for k,v in change.items() if k not in ['audience','targets','responses','teacherNote','sourceEvidence']}
  item['assigned']=person['id'] in change['targets']
  item['own']=deepcopy(change.get('responses',{}).get(person['id'],{'version':0}))
  item['shared']=[dict(person=pid,**deepcopy(row)) for pid,row in change.get('responses',{}).items() if row.get('shared')]
  result.append(item)
 return dict(changes=result,requests=[dict(kind=r.get('requestKind','visit'),text=r['text']) for r in current_requests(state,person['group'],preview) if r['person']==person['id']])

def preview_change(state, body):
 from progress_backend import supported
 if not supported(state['plan']):raise ValueError('Adaptive additions currently support the InfoVis Role Play pilot.')
 group=body.get('group');kind=body.get('pattern')
 if not isinstance(group,int) or isinstance(group,bool) or not 0<=group<state['plan']['groupCount']:raise ValueError('Choose a valid team.')
 if kind not in PATTERNS:raise ValueError('Choose an available interface change.')
 people=people_in(state,group);ids=[p['id'] for p in people]
 targets=body.get('targets',ids)
 if not isinstance(targets,list) or not targets or len(targets)!=len(set(targets)) or any(pid not in ids for pid in targets):raise ValueError('Select current learners from this team.')
 if kind!='scaffold':targets=ids
 spec=deepcopy(PATTERNS[kind])
 if kind=='written-exchange':
  from collaboration_progress import reader_question
  question=reader_question(state,group)
  if question:spec.update(title='Respond to the Reader’s question',prompt='Read the question below. Respond with evidence, or explain what remains unresolved.',fields=[['idea','Your response to this question'],['evidence','Supporting label, frame, or remaining uncertainty']],sourceQuestion=question,handoff='The question and linked responses stay beside the shared critique.')
 return dict(pattern=kind,group=group,targets=targets,audience=ids,spec=spec,
             evidenceKey=fingerprint(state,group),planRev=state['planRev'])

def apply_change(state, body):
 proposal=preview_change(state,body)
 if body.get('evidenceKey')!=proposal['evidenceKey'] or body.get('planRev')!=state['planRev']:raise ValueError('The activity or evidence changed. Preview this change again.')
 note=str(body.get('note','')).strip()[:3000]
 if not note:raise ValueError('Record why this change fits the evidence.')
 team=store(state)['teams'].setdefault(str(proposal['group']),{})
 if any(c['pattern']==proposal['pattern'] and not c.get('reviewed') for c in team.get('changes',[])):raise ValueError('This addition is already active. Inspect its responses before adding it again.')
 change=dict(id=secrets.token_hex(5),**{k:proposal[k] for k in ['pattern','targets','audience','spec']},
             created=time.time(),phaseId=state['plan']['live']['phaseId'],responses={},teacherNote=note,
             sourceEvidence=proposal['evidenceKey'],reviewed=False)
 team.setdefault('changes',[]).append(change)
 return deepcopy(change)

def save_response(state, person, body, preview=False):
 team=store(state,preview)['teams'].get(str(person['group']),{})
 change=next((c for c in team.get('changes',[]) if c['id']==body.get('id')),None)
 if not change or person['id'] not in change['targets']:raise ValueError('This task is not assigned to you.')
 if change.get('reviewed'):raise ValueError('The teacher has reviewed this addition. Your saved response is kept.')
 old=change['responses'].get(person['id'],{'version':0})
 if body.get('version',0)!=old['version']:raise ValueError('Your response changed in another tab. Reload before saving.')
 values=body.get('values',{})
 if not isinstance(values,dict):raise ValueError('Write a response.')
 values={key:str(values.get(key,'')).strip()[:3000] for key,_ in change['spec']['fields']}
 shared=bool(body.get('shared'))
 if shared and not all(values.values()):raise ValueError('Complete each field before sharing with the team.')
 reply=str(body.get('reply','')).strip()[:3000];reply_to=body.get('replyTo') or ''
 if reply:
  peer=change['responses'].get(reply_to)
  if reply_to==person['id'] or not peer or not peer.get('shared'):raise ValueError('Choose a shared contribution from a teammate.')
 elif reply_to:raise ValueError('Write your reply first.')
 # A shared post cannot silently become private or be erased by a partial update.
 if old.get('shared') and not shared:raise ValueError('A shared contribution stays visible. Update it with Share.')
 record=dict(values=values,reply=reply,replyTo=reply_to,shared=shared,version=old['version']+1,time=time.time())
 q=change['spec'].get('sourceQuestion')
 if q and shared and person['id']!=q['person']:record['respondsToQuestion']=q['id']
 change['responses'][person['id']]=record
 return deepcopy(record)

def review_change(state, body):
 group=body.get('group');team=store(state)['teams'].get(str(group),{})
 change=next((c for c in team.get('changes',[]) if c['id']==body.get('id')),None)
 if not change:raise ValueError('Choose an existing interface addition.')
 note=str(body.get('note','')).strip()[:3000]
 if not note:raise ValueError('Describe what you checked and what remains uncertain.')
 change.update(reviewed=True,reviewNote=note,reviewedAt=time.time())
 for request in current_requests(state,group):
  if request['person'] in change['targets'] and request.get('requestKind') in (['difficulty'] if change['pattern']=='scaffold' else ['participation','unheard']):
   request.update(resolved=True,resolvedAt=time.time())
 change['reviewEvidenceKey']=fingerprint(state,group)
 return deepcopy(change)

def review_signal(state, body):
 group=body.get('group')
 if not isinstance(group,int) or not 0<=group<state['plan']['groupCount']:raise ValueError('Choose a valid team.')
 note=str(body.get('note','')).strip()[:3000]
 if not note:raise ValueError('Record why no interface change is needed.')
 if body.get('evidenceKey')!=fingerprint(state,group):raise ValueError('Evidence changed. Review it again.')
 store(state)['teams'].setdefault(str(group),{}).setdefault('decisions',[]).append(dict(evidenceKey=body['evidenceKey'],note=note,time=time.time()))
 return dict(ok=True)

def preview_session(state, body):
 from collab_workflow import TEST_RUNS
 # Unlike functional test fixtures, the preview preserves the existing work in a clone.
 clone=deepcopy(state);change=apply_change(clone,body);token=secrets.token_urlsafe(18)
 TEST_RUNS[token]={'state':clone,'created':time.time(),'planRev':state['planRev'],'report':None}
 return dict(id=token,change=change,people=[{k:v for k,v in p.items() if k!='token'} for p in people_in(clone,body['group'])])
