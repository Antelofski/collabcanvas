"""Recorded collaboration signals and the detectors that read them.

Signals are facts the interface can record: when a learner last saved a change, who saved
each version of the shared critique, a sign-off, the length of a paste. Detectors turn
them into "expected / observed / why" for the teacher. Nothing here reads speech, judges
the quality of an answer, or labels a learner. Time-based checks run on class work only,
while the stage is live and not paused.
"""
from copy import deepcopy
import hashlib, json, secrets, time

PULSE_CHOICES=['yes','partly','no']

# ---------------------------------------------------------------- storage
def peek(state,preview=False):return state.get('previewSignals' if preview else 'signals') or {}
def store(state,preview=False):return state.setdefault('previewSignals' if preview else 'signals',{})
def team(state,group):return sorted([p for p in state['people'] if p['active'] and p['group']==group],key=lambda p:p['slot'])
def role_of(state,p):
 t=next((t for t in state['plan']['tasks'] if p['slot'] in t['assignees']),{});return t.get('title') or 'Learner'
def role_id(state,p):
 t=next((t for t in state['plan']['tasks'] if p['slot'] in t['assignees']),{});return t.get('roleId') or t.get('title') or 'learner'
def name_of(state,p):return (p.get('name') or '').replace(' (example)','').strip() or role_of(state,p)
def shared_flow(plan):return plan.get('studio',{}).get('flow')=='group-first'
def groups(state,preview=False):return state.get('previewStudioGroups' if preview else 'studioGroups') or {}
def critique(state,group,preview=False):
 rec=groups(state,preview).get(str(group),{}).get('critique') or {}
 return rec if rec.get('version') else None
def responses(state,preview=False):return state.get('previewResponses' if preview else 'responses') or {}
def artifacts(state,preview=False):return state.get('previewArtifacts' if preview else 'artifacts') or {}

def enabled(state):
 """Enabled rules by detector. The first enabled rule for a detector sets what students see."""
 from progress_rules import effective_rules
 from progress_backend import supported
 out={}
 if not supported(state['plan']):return out
 for r in effective_rules(state['plan'],state):
  if r.get('enabled'):out.setdefault(r['condition'],r)
 return out

def clock(seconds):
 seconds=max(0,int(round(seconds)));m,s=divmod(seconds,60)
 if not m:return f'{s} s'
 return f'{m} min' if s<10 or m>=10 else f'{m} min {s} s'
def num(x):return str(int(x)) if float(x).is_integer() else str(x)
def listing(names,limit=4):
 names=list(names)
 if len(names)<=1:return ''.join(names)
 if len(names)>limit:return ', '.join(names[:limit])+f' and {len(names)-limit} more'
 return ', '.join(names[:-1])+' and '+names[-1]

def stage_state(plan,phase_id,now=None):
 """Where the live class is relative to one stage."""
 now=now or time.time();phases=plan['phases'];live=plan['live']
 index=next((i for i,p in enumerate(phases) if p['id']==phase_id),0);phase=phases[index]
 current=next((i for i,p in enumerate(phases) if p['id']==live.get('phaseId')),0)
 started=bool(live.get('started'));here=started and current==index;total=phase['minutes']*60;remaining=None
 if here:
  remaining=live.get('remaining') if live.get('paused') else total-(now-(live.get('startedAt') or now))
  if remaining is None:remaining=total
 return dict(phase=phase,index=index,started=started,here=here,paused=here and bool(live.get('paused')),running=here and not live.get('paused'),past=started and current>index,remaining=remaining,total=total,since=live.get('clock') or live.get('startedAt') or now)

def touch(state,person,scope='own',preview=False,now=None):
 """Record that a learner changed something. Content is never stored here."""
 now=now or time.time();s=store(state,preview)
 row=s.setdefault('edits',{}).setdefault(person['id'],{'last':0,'count':0});row['last']=now;row['count']=row.get('count',0)+1
 if scope=='shared':s.setdefault('shared',{})[str(person['group'])]=now

def last_own(state,pid,preview=False):
 return max(peek(state,preview).get('edits',{}).get(pid,{}).get('last',0),artifacts(state,preview).get(pid,{}).get('updated',0) or 0)
def last_shared(state,group,preview=False):
 recs=groups(state,preview).get(str(group),{})
 return max([peek(state,preview).get('shared',{}).get(str(group),0)]+[r.get('updated',0) or 0 for r in recs.values() if isinstance(r,dict)])

def record_submit(state,person,phase_id,preview=False):
 """First time a learner shares work for a stage, with the stage time left if the class is live."""
 s=store(state,preview);row=s.setdefault('submits',{}).setdefault(person['id'],{})
 if phase_id in row:return
 entry=dict(time=time.time());st=stage_state(state['plan'],phase_id)
 if not preview and st['running']:entry.update(remaining=st['remaining'],total=st['total'])
 row[phase_id]=entry

def group_saved(state,person,section,old,new,preview=False):
 """Called after a shared record is saved: who changed which part, and the stage time left."""
 now=time.time();s=store(state,preview);g=str(person['group'])
 fields=[k for k in new if k not in ('version','updated','person') and new.get(k)!=old.get(k)]
 entry=dict(person=person['id'],time=now,fields=fields,version=new['version'])
 phase=next((p for p in state['plan']['phases'] if p.get('purpose')==section),None)
 if phase and not preview:
  st=stage_state(state['plan'],phase['id'],now)
  if st['running']:entry.update(remaining=st['remaining'],total=st['total'])
 log=s.setdefault('authors',{}).setdefault(g,{}).setdefault(section,[]);log.append(entry);del log[:-80]
 touch(state,person,'shared',preview,now)
 if section=='critique' and 'random_explainer' in enabled(state) and not s.get('explainer',{}).get(g):pick_explainer(state,person['group'],preview)

def pick_explainer(state,group,preview=False,by='system'):
 """Pick one member at random to explain the team's answer. Prefers someone who has not been picked and did not save the critique."""
 people=team(state,group);s=store(state,preview);g=str(group);old=s.setdefault('explainer',{}).get(g)
 joined=[p for p in people if p.get('claimed')] or people
 tried={h['person'] for h in (old or {}).get('history',[])}|({old['person']} if old else set())
 writer=(critique(state,group,preview) or {}).get('person')
 pool=[p for p in joined if p['id'] not in tried] or [p for p in joined if not old or p['id']!=old['person']] or joined
 pool=[p for p in pool if p['id']!=writer] or pool
 chosen=secrets.choice(pool);history=list((old or {}).get('history',[]))
 if old:history.append({k:old[k] for k in ['person','pickedAt','text','time','by'] if k in old})
 s['explainer'][g]=dict(person=chosen['id'],pickedAt=time.time(),by=by,history=history[-6:])
 return s['explainer'][g]

# ---------------------------------------------------------------- learner side
def pulse_open(state,person,rule,preview=False):
 plan=state['plan'];st=stage_state(plan,rule['phaseId']);mine=responses(state,preview).get(person['id'],{})
 if critique(state,person['group'],preview) or mine.get(rule['phaseId']+':submitted') or st['past']:return True
 return bool(st['here'] and st['remaining']<=rule['params'].get('minutes',2)*60)

def instruments(state,person,preview=False):
 """What the enabled rules add to this learner's interface, with only the data this learner may see."""
 on=enabled(state);s=peek(state,preview);g=str(person['group']);plan=state['plan'];people=team(state,person['group']);out={}
 names={p['id']:name_of(state,p) for p in people};shared=shared_flow(plan);crit=critique(state,person['group'],preview)
 if 'stalled_learner' in on or 'quiet_team' in on:out['heartbeat']=dict(seconds=15)
 if 'pasted_text' in on:out['paste']=dict(minChars=on['pasted_text']['params']['minChars'],block=bool(on['pasted_text']['params'].get('block')))
 if 'support_request' in on:out['unheard']=True
 if shared and ('contribution_balance' in on or 'co_sign' in on):
  log=s.get('authors',{}).get(g,{}).get('critique',[]);order=list(dict.fromkeys(e['person'] for e in log if e.get('fields')))
  if crit and not order and crit.get('person'):order=[crit['person']]
  out['authors']=dict(names=[names.get(pid,'A teammate') for pid in order],last=names.get((crit or {}).get('person'),''))
 if shared and 'co_sign' in on:
  rows=s.get('signoffs',{}).get(g,{});version=(crit or {}).get('version',0)
  out['signoff']=dict(required=min(int(on['co_sign']['params']['signoffs']),max(1,len(people)-1)),version=version,saved=bool(crit),writer=names.get((crit or {}).get('person'),''),
   canSign=bool(crit) and crit.get('person')!=person['id'],mine=deepcopy(rows.get(person['id'])),
   entries=[dict(name=names.get(pid,'A teammate'),agree=r['agree'],note=r['note'],current=r['version']==version,mine=pid==person['id']) for pid,r in rows.items() if pid in names])
 if shared and 'unresolved_difference' in on:
  note=s.get('open',{}).get(g) or {};out['whyNot']=dict(text=note.get('text',''),by=names.get(note.get('person'),''),saved=bool(note.get('text')))
 pick=s.get('explainer',{}).get(g)
 if shared and ('random_explainer' in on or pick):
  out['explainer']=dict(picked=bool(pick),name=names.get((pick or {}).get('person'),''),mine=bool(pick) and pick['person']==person['id'],text=pick.get('text','') if pick and pick['person']==person['id'] else '',done=bool(pick and pick.get('text')))
 if 'quiet_team' in on:
  line=s.get('status',{}).get(g) or {};out['status']=dict(phaseId=on['quiet_team']['phaseId'],text=line.get('text',''),by=names.get(line.get('person'),''),time=line.get('time'))
 if 'closing_pulse' in on:
  rule=on['closing_pulse'];out['pulse']=dict(phaseId=rule['phaseId'],open=pulse_open(state,person,rule,preview),mine=deepcopy(s.get('pulse',{}).get(person['id'])))
 return out

def learner_action(state,person,body,preview=False):
 """Learner events behind the instruments. Returns {'quiet': True} for events that need no disk write."""
 kind=body.get('kind');s=store(state,preview);g=str(person['group']);pid=person['id'];now=time.time();on=enabled(state)
 text=lambda key,limit:str(body.get(key,'')).strip()[:limit]
 if kind=='edit':
  touch(state,person,'shared' if body.get('scope')=='shared' else 'own',preview,now);return dict(ok=True,quiet=True)
 if kind=='paste':
  rule=on.get('pasted_text')
  try:chars=int(body.get('chars',0))
  except (TypeError,ValueError):chars=0
  if not rule or chars<rule['params']['minChars']:return dict(ok=True,noted=False,quiet=True)
  rows=s.setdefault('pastes',{}).setdefault(pid,[])
  rows.append(dict(time=now,chars=min(chars,1_000_000),field=text('field',120),blocked=bool(rule['params'].get('block'))));del rows[:-40]
  return dict(ok=True,noted=True)
 if kind=='signoff':
  if 'co_sign' not in on:raise ValueError('Sign-off is not part of this activity.')
  crit=critique(state,person['group'],preview)
  if not crit:raise ValueError('Save the shared critique first.')
  if crit.get('person')==pid:raise ValueError('Ask a teammate who did not save this version to sign off.')
  if body.get('version')!=crit['version']:raise ValueError('The critique changed. Read the new version, then sign off.')
  note=text('note',1500)
  if not note:raise ValueError('Give one reason.')
  s.setdefault('signoffs',{}).setdefault(g,{})[pid]=dict(version=crit['version'],agree=bool(body.get('agree')),note=note,time=now)
  touch(state,person,'shared',preview,now);return dict(ok=True)
 if kind=='whynot':
  if 'unresolved_difference' not in on:raise ValueError('This note is not part of this activity.')
  s.setdefault('open',{})[g]=dict(text=text('text',3000),person=pid,time=now);touch(state,person,'shared',preview,now);return dict(ok=True)
 if kind=='status':
  if 'quiet_team' not in on:raise ValueError('The status line is not part of this activity.')
  line=text('text',200)
  if not line:raise ValueError('Write one line first.')
  s.setdefault('status',{})[g]=dict(text=line,person=pid,time=now);touch(state,person,'shared',preview,now);return dict(ok=True)
 if kind=='explain':
  pick=s.get('explainer',{}).get(g)
  if not pick or pick['person']!=pid:raise ValueError('Another member was picked to explain.')
  answer=text('text',3000)
  if not answer:raise ValueError('Write your explanation first.')
  pick.update(text=answer,time=now);touch(state,person,'own',preview,now);return dict(ok=True)
 if kind=='pulse':
  rule=on.get('closing_pulse')
  if not rule or not pulse_open(state,person,rule,preview):raise ValueError('The closing check is not open yet.')
  if body.get('contributed') not in PULSE_CHOICES or body.get('used') not in PULSE_CHOICES:raise ValueError('Answer both questions.')
  s.setdefault('pulse',{})[pid]=dict(contributed=body['contributed'],used=body['used'],change=text('change',1500),time=now);return dict(ok=True)
 raise ValueError('Unknown action.')

# ---------------------------------------------------------------- detectors
def sig(status,expected,observed,why='',people=None,key='',records=None,**extra):
 return dict(status=status,expected=expected,observed=observed,why=why,people=people or [],key=key,records=records or [],**extra)

class Team:
 """Read-only view of one team for the detectors."""
 def __init__(self,state,group,evidence,preview=False,now=None):
  self.state=state;self.group=group;self.g=str(group);self.evidence=evidence;self.preview=preview;self.now=now or time.time()
  self.plan=state['plan'];self.people=team(state,group);self.s=peek(state,preview)
  self.names={p['id']:name_of(state,p) for p in self.people};self.responses=responses(state,preview);self.artifacts=artifacts(state,preview)
  self.critique=critique(state,group,preview)
 def stage(self,phase_id):return stage_state(self.plan,phase_id,self.now)
 def submitted(self,p,phase_id):return bool(self.responses.get(p['id'],{}).get(phase_id+':submitted'))
 def joined(self,p):return bool(p.get('claimed') or self.artifacts.get(p['id']) or self.responses.get(p['id']) or self.s.get('edits',{}).get(p['id']))
 def log(self,section):return self.s.get('authors',{}).get(self.g,{}).get(section,[])
 def answers(self):return [r['initial'] for r in self.evidence['rows'] if r['initial']]

def live_gate(t,rule,expected):
 """Shared gate for time-based checks. Returns a signal when the check cannot run now, else None."""
 st=t.stage(rule['phaseId'])
 if t.preview:return sig('waiting',expected,'Time-based checks run on class work, not on rehearsal data.')
 if st['past']:return sig('checked',expected,f'“{st["phase"]["title"]}” has ended.')
 if not st['here']:return sig('waiting',expected,f'Runs while “{st["phase"]["title"]}” is live.')
 if st['paused']:return sig('collecting',expected,'The class is paused, so this check is paused too.')
 return None

def d_stalled(t,rule):
 minutes=rule['params']['minutes'];expected=f'Each learner saves a change at least every {num(minutes)} min until their work for this stage is shared.'
 pending=[p for p in t.people if not t.submitted(p,rule['phaseId'])]
 if not pending:return sig('checked',expected,f'All {len(t.people)} learners shared their work for this stage.')
 gate=live_gate(t,rule,expected)
 if gate:return gate
 st=t.stage(rule['phaseId']);rows=[]
 active=[p for p in pending if t.joined(p)]
 for p in active:
  last=max(st['since'],last_own(t.state,p['id']));idle=t.now-last
  if idle>=minutes*60:rows.append((p,idle,last))
 if rows:
  return sig('attention',expected,'; '.join(f'{t.names[p["id"]]}: no saved change for {clock(idle)}' for p,idle,_ in rows)+'. Work for this stage is not shared.',f'{clock(st["remaining"])} left in “{st["phase"]["title"]}”. Reading and thinking leave no trace, so ask before judging.',
   people=[p['id'] for p,_,_ in rows],key='stalled:'+','.join(f'{p["id"]}:{int(last)}' for p,_,last in rows),records=[dict(name=t.names[p['id']],text=f'{role_of(t.state,p)} · no saved change for {clock(idle)}') for p,idle,_ in rows])
 waiting=len(pending)-len(active)
 return sig('collecting',expected,(f'{len(active)} learner{"" if len(active)==1 else "s"} still working; each saved a change in the last {num(minutes)} min.' if active else 'No learner has joined this team yet.')+(f' {waiting} place{"" if waiting==1 else "s"} not joined.' if waiting and active else ''))

def d_quiet(t,rule):
 minutes=rule['params']['minutes'];st=t.stage(rule['phaseId']);purpose=st['phase'].get('purpose')
 expected=f'The team edits its shared work or posts a status line at least every {num(minutes)} min.'
 saved=groups(t.state,t.preview).get(t.g,{}).get(purpose) if purpose in ('opening','critique') else None
 if saved and (saved.get('text') or saved.get('message')):return sig('checked',expected,'The team saved its shared work for this stage.')
 gate=live_gate(t,rule,expected)
 if gate:return gate
 if not any(t.joined(p) for p in t.people):return sig('collecting',expected,'No learner has joined this team yet.')
 own=max([last_own(t.state,p['id']) for p in t.people]+[0]) if st['phase']['kind']=='individual' else 0
 last=max(st['since'],last_shared(t.state,t.group),own);idle=t.now-last
 if idle>=minutes*60:
  return sig('attention',expected,f'No shared edit or status from this team for {clock(idle)}.',f'{clock(st["remaining"])} left in “{st["phase"]["title"]}”. Speech is not recorded; the team may be talking.',people=[p['id'] for p in t.people],key=f'quiet:{int(last)}')
 return sig('collecting',expected,f'Last shared activity {clock(idle)} ago.')

def d_balance(t,rule):
 expected='At least two members add to or edit the shared critique.'
 if not shared_flow(t.plan):return sig('waiting',expected,'This activity has no shared product.')
 if not t.critique:return sig('collecting',expected,'The shared critique has not been saved yet.')
 authors=list(dict.fromkeys(e['person'] for e in t.log('critique') if e.get('fields')))
 if not authors and t.critique.get('person'):authors=[t.critique['person']]
 names=[t.names.get(pid,'A teammate') for pid in authors]
 if len(authors)>=2:return sig('checked',expected,f'{len(authors)} members edited the shared critique: {listing(names)}.')
 st=t.stage(rule['phaseId'])
 due=not t.preview and (st['past'] or st['here'] and st['remaining']<=st['total']/2 or not st['started'] and t.now-(t.critique.get('updated') or t.now)>=120)
 observed=f'{names[0] if names else "One member"} saved every part of the shared critique. No other member has edited it.'
 if not due:return sig('collecting',expected,observed,'Checked at the midpoint of shared writing.')
 return sig('attention',expected,observed,'Shared writing is past its midpoint. One member may be typing for the team, so ask before judging.',people=[p['id'] for p in t.people],key=f'balance:{authors[0] if authors else ""}:{t.critique["version"]}',records=[dict(name=names[0] if names else 'One member',text=f'Saved {len(t.log("critique")) or 1} version{"" if (len(t.log("critique")) or 1)==1 else "s"} of the critique.')])

def d_cosign(t,rule):
 need=min(int(rule['params']['signoffs']),max(1,len(t.people)-1));minutes=rule['params']['minutes']
 expected=f'{need} member{"s" if need>1 else ""} who did not save the critique read{"" if need>1 else "s"} it and sign{"" if need>1 else "s"} off with one reason.'
 if not shared_flow(t.plan):return sig('waiting',expected,'This activity has no shared product.')
 if not t.critique:return sig('collecting',expected,'The shared critique has not been saved yet.')
 rows=t.s.get('signoffs',{}).get(t.g,{});version=t.critique['version'];writer=t.critique.get('person')
 current=[(pid,r) for pid,r in rows.items() if r['version']==version and pid!=writer and pid in t.names];stale=[pid for pid,r in rows.items() if r['version']!=version]
 records=[dict(name=t.names[pid],text=('Agrees: ' if r['agree'] else 'Would change something: ')+r['note']) for pid,r in current]
 base=f'Saved by {t.names.get(writer,"a member")}. {len(current)} of {need} sign-off{"s" if need>1 else ""} from another member.'+(f' {len(stale)} earlier sign-off{" was" if len(stale)==1 else "s were"} for an older version.' if stale else '')
 if len(current)>=need:
  objections=[pid for pid,r in current if not r['agree']]
  if objections:return sig('review',expected,base+f' {listing(t.names[p] for p in objections)} would change something.','Read the objection beside the critique.',people=objections,key=f'cosign:{version}:objection',records=records)
  return sig('checked',expected,base,records=records)
 st=t.stage(rule['phaseId']);waited=t.now-(t.critique.get('updated') or t.now)
 if t.preview or not (st['past'] or waited>=minutes*60):return sig('collecting',expected,base,f'Alerts {num(minutes)} min after the critique is saved.',records=records)
 return sig('attention',expected,base,f'The critique was saved {clock(waited)} ago.' if not st['past'] else 'The stage has ended.',people=[p['id'] for p in t.people if p['id']!=writer],key=f'cosign:{version}',records=records)

def d_explainer(t,rule):
 minutes=rule['params']['minutes'];least=int(rule['params']['minChars'])
 expected='A member picked at random explains the team’s decision and one reason, in private.'
 if not shared_flow(t.plan):return sig('waiting',expected,'This activity has no shared product.')
 pick=t.s.get('explainer',{}).get(t.g)
 if not pick:return sig('collecting',expected,'A member is picked when the team saves its critique.' if not t.critique else 'No member has been picked yet.')
 who=t.names.get(pick['person'],'A member');tried=len(pick.get('history',[]))
 if not pick.get('text'):
  waited=t.now-pick['pickedAt'];st=t.stage(rule['phaseId'])
  if t.preview or not (st['past'] or waited>=minutes*60):return sig('collecting',expected,f'{who} was picked. Waiting for the explanation.',people=[pick['person']])
  return sig('attention',expected,f'{who} was picked {clock(waited)} ago. No explanation saved.','The explanation is private to the learner and the teacher.',people=[pick['person']],key=f'explain:{pick["person"]}:none')
 records=[dict(name=who,text=pick['text'])];key=f'explain:{pick["person"]}:{int(pick["time"])}'
 if len(pick['text'])<least:return sig('attention',expected,f'{who}’s explanation is {len(pick["text"])} characters long.',f'Shorter than {least} characters. Ask teammates to explain again, then pick another member.',people=[pick['person']],key=key,records=records)
 return sig('review',expected,f'{who} saved an explanation'+(f' (pick {tried+1})' if tried else '')+'. Read it against the critique.','The system does not judge whether it is right.',people=[pick['person']],key=key,records=records)

def d_misconception(t,rule):
 from progress_backend import QUESTIONS
 expected='A team that shares one wrong first answer gets new information from the teacher, not more peer discussion.'
 answers=t.answers();total=len(t.people)
 if len(answers)<total or total<2:return sig('collecting',expected,f'{len(answers)} of {total} first answers saved.')
 chosen={a['answer'] for a in answers}
 if len(chosen)>1:return sig('inactive',expected,'First choices differ, so this rule is not triggered.')
 answer=answers[0]['answer'];label=lambda v:next((o[1] for o in QUESTIONS['initial']['options'] if o[0]==v),v)
 if answer==QUESTIONS['initial']['answer']:return sig('checked',expected,f'All {total} chose the keyed answer.')
 support=t.evidence.get('support') or {};observed=f'All {total} chose “{label(answer)}” The key is “{label(QUESTIONS["initial"]["answer"])}”'
 if support.get('resolved'):return sig('addressed',expected,observed+' The follow-up was reviewed.',people=[p['id'] for p in t.people],key='misconception:'+answer)
 if support:observed+=f' A comparison task was sent; {t.evidence.get("followupCount",0)} of {len(support.get("targets",[]))} follow-ups saved.'
 return sig('attention',expected,observed,'Discussion among learners who share a wrong answer tends to confirm it.',people=[p['id'] for p in t.people],key='misconception:'+answer,records=[dict(name=r['name'].replace(' (example)',''),text=r['initial']['reason']) for r in t.evidence['rows'] if r['initial']])

def differences(t,rule):
 """Recorded signs that the team does not fully agree."""
 found=[];answers=t.answers();chosen={}
 for a in answers:chosen[a['answer']]=chosen.get(a['answer'],0)+1
 if len(answers)>=2 and len(chosen)>1:found.append('First choices differ ('+' / '.join(str(n) for n in sorted(chosen.values(),reverse=True))+').')
 objections=[t.names[pid] for pid,r in t.s.get('signoffs',{}).get(t.g,{}).items() if not r['agree'] and pid in t.names]
 if objections:found.append(f'{listing(objections)} would change something at sign-off.')
 limit=int(rule['params']['overwrites']);turns={}
 last={}
 for e in t.log('critique'):
  for f in e.get('fields',[]):
   if f in last and last[f]!=e['person']:turns[f]=turns.get(f,0)+1
   last[f]=e['person']
 contested=[f for f,n in turns.items() if n>=limit]
 if contested:found.append(f'Members took over {len(contested)} part{"" if len(contested)==1 else "s"} of the critique from each other {limit} or more times.')
 from adaptive_backend import current_requests
 if any(r.get('requestKind')=='unheard' for r in current_requests(t.state,t.group,t.preview)):found.append('A member reported that their point was not discussed.')
 return found

def d_difference(t,rule):
 least=int(rule['params']['minChars']);expected='The shared critique says why the team rejected another reading, or records it as unresolved.'
 if not shared_flow(t.plan):return sig('waiting',expected,'This activity has no shared product.')
 found=differences(t,rule)
 if not found:return sig('inactive',expected,'No recorded difference: first choices match and no objection is saved.')
 if not t.critique:return sig('collecting',expected,' '.join(found)+' Waiting for the shared critique.')
 note=(t.s.get('open',{}).get(t.g) or {});text=note.get('text','')
 if len(text)>=least:return sig('review',expected,' '.join(found)+' The team recorded a rejected or open reading.','Read the note against the difference.',people=[p['id'] for p in t.people],key=f'difference:{t.critique["version"]}:{int(note.get("time",0))}',records=[dict(name=t.names.get(note.get('person'),'The team'),text=text)])
 return sig('attention',expected,' '.join(found)+' The critique has no note on the reading the team rejected or left open.','The critique is saved.',people=[p['id'] for p in t.people],key=f'difference:{t.critique["version"]}:none')

def feedback_items(t):
 """Peer feedback the interface records: sign-off notes, claim checks, and linked replies."""
 items=[]
 for pid,r in t.s.get('signoffs',{}).get(t.g,{}).items():
  if pid in t.names:items.append(dict(person=pid,kind='Sign-off note',text=r['note'],target=True))
 for p in t.people:
  for review in (t.artifacts.get(p['id'],{}).get('reviews') or {}).values():
   if isinstance(review,dict) and (review.get('status') or review.get('reason')):items.append(dict(person=p['id'],kind='Claim check',text=str(review.get('reason','')),target=True))
 store_key='previewAdaptive' if t.preview else 'adaptive'
 for change in t.state.get(store_key,{}).get('teams',{}).get(t.g,{}).get('changes',[]):
  for pid,r in change.get('responses',{}).items():
   if r.get('shared') and r.get('reply') and pid in t.names:items.append(dict(person=pid,kind='Reply to a peer',text=r['reply'],target=bool(r.get('replyTo'))))
 return items

def d_feedback(t,rule):
 least=int(rule['params']['minChars']);expected='Each piece of peer feedback points to one part of a peer’s work and gives a reason.'
 items=feedback_items(t)
 if not items:return sig('collecting',expected,'No peer feedback saved yet.')
 weak=[i for i in items if len(i['text'].strip())<least or not i['target']]
 if weak:
  return sig('attention',expected,f'{len(weak)} of {len(items)} feedback item{"" if len(items)==1 else "s"} {"is" if len(weak)==1 else "are"} shorter than {least} characters or name no target.','Length is only a prompt to read the feedback. It does not measure quality.',people=list(dict.fromkeys(i['person'] for i in weak)),
   key='feedback:'+hashlib.sha256(json.dumps([[i['person'],i['text']] for i in weak]).encode()).hexdigest()[:12],records=[dict(name=t.names[i['person']],text=f'{i["kind"]}: “{i["text"].strip() or "(empty)"}”') for i in weak[:6]])
 return sig('checked',expected,f'{len(items)} feedback item{" names" if len(items)==1 else "s name"} a target and give{"s" if len(items)==1 else ""} at least {least} characters of reason.','Quality still needs a teacher’s read.')

def d_pulse(t,rule):
 expected='Each learner answers three private questions at the end: Did you contribute? Was your work used? One thing to change.'
 rows=t.s.get('pulse',{});answered=[(p,rows[p['id']]) for p in t.people if p['id'] in rows]
 records=[dict(name=t.names[p['id']],text=f'Contributed: {r["contributed"]} · Work used: {r["used"]}'+(f' · To change: {r["change"]}' if r.get('change') else '')) for p,r in answered]
 if not answered:return sig('collecting' if any(pulse_open(t.state,p,rule,t.preview) for p in t.people) else 'waiting',expected,'No closing check saved yet.')
 low=[(p,r) for p,r in answered if 'no' in (r['contributed'],r['used'])]
 if low:
  parts=[t.names[p['id']]+' answered “No” to '+' and '.join(q for q,v in [('“Did you contribute?”',r['contributed']),('“Was your work used?”',r['used'])] if v=='no') for p,r in low]
  return sig('attention',expected,'; '.join(parts)+'.','Private to the teacher. Read it beside the team’s record and talk to the learner alone.',people=[p['id'] for p,_ in low],key='pulse:'+','.join(sorted(p['id'] for p,_ in low)),records=records)
 if len(answered)<len(t.people):return sig('collecting',expected,f'{len(answered)} of {len(t.people)} closing checks saved.',records=records)
 return sig('checked',expected,f'All {len(t.people)} closing checks saved. No “No” answer.',records=records,allYes=all(r['contributed']=='yes' and r['used']=='yes' for _,r in answered))

def d_paste(t,rule):
 least=int(rule['params']['minChars']);block=bool(rule['params'].get('block'));expected='Learners write their answers in the answer fields.'
 rows=[(p,e) for p in t.people for e in t.s.get('pastes',{}).get(p['id'],[]) if e['chars']>=least]
 if not rows:return sig('collecting',expected,f'No paste over {least} characters recorded.'+(' Paste is turned off in answer fields.' if block else ''))
 people=list(dict.fromkeys(p['id'] for p,_ in rows));per={}
 for p,e in rows:per.setdefault(p['id'],[]).append(e)
 parts=[f'{t.names[pid]}: {len(es)} paste{"s" if len(es)>1 else ""}, longest {max(e["chars"] for e in es)} characters'+(' (blocked)' if all(e.get('blocked') for e in es) else '') for pid,es in per.items()]
 return sig('review' if all(e.get('blocked') for _,e in rows) else 'attention',expected,'; '.join(parts)+'.','Only the length is recorded, not the text. A paste can come from the learner’s own notes or an assistive tool.',people=people,key=f'paste:{len(rows)}',
  records=[dict(name=t.names[p['id']],text=f'{e["chars"]} characters into “{e.get("field") or "an answer field"}”'+(' · blocked' if e.get('blocked') else '')) for p,e in rows[-6:]])

def finish_time(t,phase):
 """When the team finished a stage, with the stage time left at that moment. None if unknown."""
 purpose=phase.get('purpose')
 if purpose in ('opening','critique'):
  log=t.log(purpose);return log[0] if log else None
 rows=[t.s.get('submits',{}).get(p['id'],{}).get(phase['id']) for p in t.people]
 if not rows or not all(rows):return None
 return max(rows,key=lambda r:r['time'])

def d_early(t,rule):
 share=rule['params']['share'];st=t.stage(rule['phaseId']);phase=st['phase']
 expected=f'The team uses the stage to reason. Finishing with more than {num(share)}% of the time left prompts a depth check.'
 done=finish_time(t,phase)
 if not done:return sig('collecting' if st['here'] else 'waiting',expected,'The team has not finished this stage.')
 if 'remaining' not in done:return sig('waiting',expected,'The team finished outside a live, timed stage, so the time left is unknown.')
 left=done['remaining']/done['total'] if done['total'] else 0
 if left*100>share:return sig('attention',expected,f'The team finished “{phase["title"]}” with {clock(done["remaining"])} of {clock(done["total"])} left.','Fast can mean easy, or filled in without discussion. Ask one member to explain.',people=[p['id'] for p in t.people],key=f'early:{phase["id"]}:{int(done["time"])}')
 return sig('checked',expected,f'The team finished with {clock(max(0,done["remaining"]))} left.')

DETECTORS=dict(stalled_learner=d_stalled,quiet_team=d_quiet,contribution_balance=d_balance,co_sign=d_cosign,random_explainer=d_explainer,shared_misconception=d_misconception,unresolved_difference=d_difference,feedback_specific=d_feedback,closing_pulse=d_pulse,pasted_text=d_paste,early_finish=d_early)
CLASS_CONDITIONS=['shared_blocker','workload_balance','rotation']

def default_key(rule_id,people):return rule_id+':'+hashlib.sha256(json.dumps(sorted(people)).encode()).hexdigest()[:10]

def handled_marks(state,group):
 r=state.get('progressRecords') or {}
 return (r.get('class',{}) if group=='class' else r.get('teams',{}).get(str(group),{})).get('handled',{})

def apply_handled(state,group,signal,preview=False):
 """A teacher's "handled" mark holds until the evidence behind the alert changes."""
 if preview or signal['status'] not in ('attention','review'):return signal
 mark=handled_marks(state,group).get(signal['id'])
 if mark and mark.get('key')==signal['key']:signal.update(status='addressed',handled=dict(note=mark.get('note',''),time=mark.get('time')))
 return signal

def finish_team(state,group,signals,preview=False):
 """Cross-checks between rules, then the teacher's handled marks."""
 by={s['id']:s for s in signals};wrong=next((s for s in signals if s['condition']=='shared_misconception' and s['status'] in ('attention','addressed')),None)
 if wrong:
  for s in signals:
   if s['condition']=='answer_pattern' and s['status']=='attention':s.update(status='inactive',observed='All first choices match and are wrong. See “'+wrong['title']+'”.',why='More peer discussion is the wrong response to a shared wrong answer.',detail='All first choices match and are wrong. See “'+wrong['title']+'”.')
 fired=[s for s in signals if s['status'] in ('attention','addressed') and s['condition'] not in ('closing_pulse','support_request')]
 for s in signals:
  if s['condition']=='closing_pulse' and s['status']=='checked' and s.pop('allYes',False) and fired:
   s.update(status='review',observed=f'All answers are “Yes”, while “{fired[0]["title"]}” fired for this team.',why='Peer and self ratings are social. Read the answers beside the record.',key='pulse:allyes:'+fired[0]['id'])
  s.pop('allYes',None)
 for s in signals:
  s['detail']=(s['observed']+(' '+s['why'] if s.get('why') else '')).strip();apply_handled(state,group,s,preview)
 return signals

# ---------------------------------------------------------------- class-level detectors
def step_of(state,phase,preview=False):
 """For one stage: which learners (or teams) have completed its step."""
 purpose=phase.get('purpose');people=[p for p in state['people'] if p['active']]
 if purpose in ('opening','critique') and shared_flow(state['plan']):
  recs=groups(state,preview);done={p['id'] for p in people if (recs.get(str(p['group']),{}).get(purpose) or {}).get('version')}
  return done,'saved the shared '+('starting reading' if purpose=='opening' else 'critique')
 done={p['id'] for p in people if responses(state,preview).get(p['id'],{}).get(phase['id']+':submitted')}
 return done,'shared their work'

def checkpoint(state,rule,now):
 st=stage_state(state['plan'],rule['phaseId'],now);left=rule.get('remainingMinutes',0)*60
 return st,bool(st['past'] or st['running'] and st['remaining']<=left)

def c_blocker(state,rule,preview,now):
 share=rule['params']['share'];teams_needed=int(rule['params']['teams'])
 expected=f'Fewer than {num(share)}% of learners are missing a step at its checkpoint, and fewer than {teams_needed} teams ask for smaller steps.'
 from adaptive_backend import current_requests
 asked=[g for g in range(state['plan']['groupCount']) if any(r.get('requestKind')=='difficulty' for r in current_requests(state,g,preview))]
 if len(asked)>=teams_needed:
  return sig('attention',expected,f'{len(asked)} teams asked for smaller steps: '+listing(f'Team {g+1}' for g in asked)+'.','Several teams asking about the same task points at the task, not at the learners.',groups=asked,key='blocker:requests:'+','.join(map(str,asked)))
 st,due=checkpoint(state,rule,now);people=[p for p in state['people'] if p['active'] and (p.get('claimed') or not any(x.get('claimed') for x in state['people'] if x['active']))]
 done,verb=step_of(state,st['phase'],preview);missing=[p for p in people if p['id'] not in done]
 if preview:return sig('waiting',expected,'Time-based checks run on class work, not on rehearsal data.')
 if not st['started']:return sig('waiting',expected,'Runs when the class is live.')
 if not due:return sig('collecting',expected,f'{len(people)-len(missing)} of {len(people)} learners {verb} in “{st["phase"]["title"]}”.')
 if people and len(missing)*100>=share*len(people):
  teams_hit=sorted({p['group'] for p in missing})
  return sig('attention',expected,f'{len(missing)} of {len(people)} learners have not {verb} in “{st["phase"]["title"]}”.',('The stage has ended.' if st['past'] else f'{clock(st["remaining"])} left.')+' When many learners miss the same step, the step is the likely problem.',people=[p['id'] for p in missing],groups=teams_hit,key=f'blocker:{st["phase"]["id"]}:{len(missing)}')
 return sig('checked',expected,f'{len(people)-len(missing)} of {len(people)} learners {verb} by the checkpoint.')

def c_workload(state,rule,preview,now):
 share=rule['params']['share'];expected=f'No role is behind at the checkpoint in more than {num(share)}% of teams.'
 count=state['plan']['groupCount']
 if count<2:return sig('waiting',expected,'Needs at least two teams.')
 if preview:return sig('waiting',expected,'Time-based checks run on class work, not on rehearsal data.')
 st,due=checkpoint(state,rule,now)
 if not st['started']:return sig('waiting',expected,'Runs when the class is live.')
 if not due:return sig('collecting',expected,f'Checked with {num(rule.get("remainingMinutes",0))} min left in “{st["phase"]["title"]}”.')
 left=rule.get('remainingMinutes',0)*60;behind={};titles={};subs=peek(state,preview).get('submits',{});active=0
 for g in range(count):
  people=team(state,g)
  if not any(p.get('claimed') or responses(state,preview).get(p['id']) for p in people):continue
  active+=1
  for p in people:
   done=responses(state,preview).get(p['id'],{}).get(st['phase']['id']+':submitted');when=subs.get(p['id'],{}).get(st['phase']['id'],{})
   late=not done or ('remaining' in when and when['remaining']<left)
   rid=role_id(state,p);titles[rid]=role_of(state,p)
   if late:behind.setdefault(rid,[]).append(g)
 if active<2:return sig('collecting',expected,'Fewer than two teams have joined.')
 worst=max(behind,key=lambda r:len(behind[r])) if behind else None
 if worst and len(behind[worst])>=2 and len(behind[worst])*100>share*active:
  everyone=all(len(v)==len(behind[worst]) for v in behind.values()) and len(behind)==len(titles)
  if not everyone:
   return sig('attention',expected,f'The {titles[worst]} had not shared work at the checkpoint in {len(behind[worst])} of {active} teams.','The same role being late across teams points at the role’s task, not at those learners.',groups=sorted(set(behind[worst])),role=titles[worst],key=f'workload:{worst}:{len(behind[worst])}')
 return sig('checked',expected,'No single role is behind across teams.' if not behind else 'Late work is spread across roles, not tied to one role.')

def c_rotation(state,rule,preview,now):
 from rule_library import library,run_id
 times=int(rule['params']['times']);expected=f'No learner holds the same role, or works with the same teammates, {times} times.'
 runs=[r for r in library(state).get('runs',[]) if r.get('id')!=run_id(state)]
 if len(runs)<times-1:return sig('waiting',expected,f'{len(runs)} earlier activit{"y" if len(runs)==1 else "ies"} recorded. Needs {times-1}.')
 people=[p for p in state['people'] if p['active'] and p.get('claimed') and p.get('name')]
 if not people:return sig('waiting',expected,'Runs when learners have joined with a name.')
 fold=lambda n:n.replace(' (example)','').strip().casefold();hits=[];ids=[]
 for p in people:
  me=fold(p['name']);mates={fold(x['name']) for x in people if x['group']==p['group'] and x['id']!=p['id']}
  same_role=0;same_team=0
  for run in runs:
   past=next((x for x in run['people'] if fold(x['name'])==me),None)
   if not past:continue
   if past['role']==role_id(state,p):same_role+=1
   old={fold(x['name']) for x in run['people'] if x['group']==past['group'] and fold(x['name'])!=me}
   if mates and mates<=old:same_team+=1
  if same_role+1>=times:hits.append(f'{name_of(state,p)} is {role_of(state,p)} for time {same_role+1}');ids.append(p['id'])
  elif same_team+1>=times:hits.append(f'{name_of(state,p)} has the same teammates for time {same_team+1}');ids.append(p['id'])
 if hits:return sig('attention',expected,'; '.join(hits[:6])+('.' if len(hits)<=6 else f'; and {len(hits)-6} more.'),'Matched by the name each learner entered. Nothing changes during class.',people=ids,key='rotation:'+','.join(sorted(ids)))
 return sig('checked',expected,f'No repeat found across {len(runs)} earlier activit{"y" if len(runs)==1 else "ies"}.')

CLASS_DETECTORS=dict(shared_blocker=c_blocker,workload_balance=c_workload,rotation=c_rotation)

def class_signals(state,preview=False):
 from progress_rules import effective_rules,describe
 now=time.time();out=[]
 for rule in effective_rules(state['plan'],state):
  if not rule.get('enabled') or rule['condition'] not in CLASS_DETECTORS:continue
  result=CLASS_DETECTORS[rule['condition']](state,rule,preview,now)
  s=describe(rule,result);s['scope']='class';s['key']=s['key'] or default_key(rule['id'],s['people'])
  s['detail']=(s['observed']+(' '+s['why'] if s.get('why') else '')).strip();out.append(apply_handled(state,'class',s,preview))
 return out

# ---------------------------------------------------------------- teacher actions
def find_signal(state,group,rule_id):
 from progress_backend import evidence
 if group=='class':return next((s for s in class_signals(state) if s['id']==rule_id),None)
 return next((s for s in evidence(state,group)['signals'] if s['id']==rule_id),None)

def log_incident(state,group,signal,outcome=None,note=''):
 log=state.setdefault('ruleLog',[]);row=next((i for i in log if i['ruleId']==signal['id'] and i['group']==group and i['key']==signal['key']),None)
 if not row:
  row=dict(ruleId=signal['id'],title=signal['title'],group=group,key=signal['key'],observed=signal['observed'][:600],time=time.time(),outcome='open');log.append(row);del log[:-300]
 if outcome:row.update(outcome=outcome,note=note,closed=time.time())
 return row

def host_action(state,body):
 """Teacher actions on alerts. Returns (result, changed)."""
 from progress_backend import records,supported
 from progress_rules import effective_rules
 from rule_library import add_carry,remove_carry,forget_custom
 if not supported(state['plan']):raise ValueError('Progress rules in this pilot support the voting-story role play.')
 kind=body.get('kind');group=body.get('group');count=state['plan']['groupCount']
 def scope():
  if group=='class':return 'class'
  if not isinstance(group,int) or isinstance(group,bool) or not 0<=group<count:raise ValueError('Choose a valid team.')
  return group
 if kind=='seen':
  added=0
  for item in (body.get('items') or [])[:40]:
   g=item.get('group')
   if g!='class' and not (isinstance(g,int) and not isinstance(g,bool) and 0<=g<count):continue
   s=find_signal(state,g,item.get('ruleId'))
   if s and s['status']=='attention' and s['key']==item.get('key') and not any(i['ruleId']==s['id'] and i['group']==g and i['key']==s['key'] for i in state.get('ruleLog',[])):log_incident(state,g,s);added+=1
  return dict(ok=True,added=added),bool(added)
 if kind in ('handle','reopen'):
  g=scope();s=find_signal(state,g,body.get('ruleId'))
  if not s:raise ValueError('Choose an enabled rule.')
  r=records(state);holder=r.setdefault('class',{}) if g=='class' else r['teams'].setdefault(str(g),{})
  if kind=='reopen':
   holder.get('handled',{}).pop(s['id'],None);return dict(ok=True),True
  if s['status'] not in ('attention','review'):raise ValueError('This rule has no open alert.')
  if body.get('key')!=s['key']:raise ValueError('The evidence changed. Read it again before marking it handled.')
  note=str(body.get('note','')).strip()[:1500]
  holder.setdefault('handled',{})[s['id']]=dict(key=s['key'],note=note,time=time.time());log_incident(state,g,s,'handled',note)
  r['events'].append(dict(group=g,kind='rule-handled',rule=s['id'],time=time.time()));return dict(ok=True),True
 if kind=='explainer-pick':
  g=scope()
  if g=='class' or not critique(state,g):raise ValueError('The team has not saved a shared critique to explain.')
  pick=pick_explainer(state,g,False,'teacher');return dict(ok=True,person=pick['person']),True
 if kind=='carry':
  return dict(ok=True,carry=add_carry(state,body,effective_rules(state['plan'],state))),True
 if kind=='carry-remove':
  remove_carry(state,body.get('id'));return dict(ok=True),True
 if kind=='forget-custom':
  forget_custom(state,body.get('id'));return dict(ok=True),True
 raise ValueError('Choose an action.')

def rule_preview(state,body):
 """A read-only example classroom that shows what a rule adds to the student interface. Never changes the class."""
 from collab_workflow import TEST_RUNS
 from model import validate_plan
 from progress_backend import supported,QUESTIONS
 if not supported(state['plan']):raise ValueError('Progress rules in this pilot support the voting-story role play.')
 clone=deepcopy(state);plan=clone['plan'];plan.setdefault('progress',{})['rules']=deepcopy(body.get('rules') or [])
 live=plan['live'];clone['plan']=validate_plan(plan);clone['plan']['live']=live;plan=clone['plan']
 rule=next((r for r in plan['progress']['rules'] if r['id']==body.get('ruleId')),None)
 if not rule:raise ValueError('Choose a rule to preview.')
 rule['enabled']=True
 for key in ['artifacts','responses','studioGroups','posts','groupAnswers','feedback']:clone[key]={}
 for key in ['progressRecords','adaptive','signals','ruleLog']:clone.pop(key,None)
 clone['requests']=[];clone['deployment']={'active':True,'deployedAt':time.time()};plan['interaction']['mode']='async'
 people=team(clone,0);now=time.time();individual=[p['id'] for p in plan['phases'] if p['kind']=='individual']
 for i,p in enumerate(people):
  p['name']=['Maya','Eli','Noor','Leo','Ana'][i%5]+' (example)';p['claimed']=True
  clone['responses'][p['id']]={ph+':submitted':True for ph in individual}
  clone['artifacts'][p['id']]={'version':1,'updated':now,'submitted':{ph:True for ph in individual},'reflection':'Example role note.','observations':[],'beats':[],'checks':[]}
 viewer=people[1] if len(people)>1 else people[0];writer=people[0]
 if shared_flow(plan):
  clone['studioGroups']['0']={'opening':{'text':'The maps keep a smaller group of people in each frame.','version':1,'updated':now,'person':writer['id']},'critique':{'message':'Each frame keeps a narrower group of people.','misreading':'Readers may see the shrinking maps as a fall in population over time.','change':'Label who is counted in every frame.','version':1,'updated':now,'person':writer['id']}}
  clone['signals']={'authors':{'0':{'critique':[dict(person=writer['id'],time=now,fields=['message','misreading','change'],version=1)]}}}
  # The example shows only what the rules in this draft add. A member is picked to explain only when that rule is on.
  if any(r.get('enabled') and r['condition']=='random_explainer' for r in plan['progress']['rules']):clone['signals']['explainer']={'0':dict(person=viewer['id'],pickedAt=now,by='system',history=[])}
 phase=rule['phaseId']
 if rule['condition'] in ('co_sign','contribution_balance','random_explainer','unresolved_difference','closing_pulse','feedback_specific','early_finish'):phase=plan['phases'][-1]['id']
 token=secrets.token_urlsafe(18);TEST_RUNS[token]=dict(state=clone,created=now,planRev=state['planRev'],report=None,example=True)
 return dict(id=token,person=viewer['id'],phase=phase,people=[{k:v for k,v in p.items() if k!='token'} for p in people])
