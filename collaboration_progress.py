"""Recorded collaboration checkpoints; no inference about unrecorded conversation."""
from hashlib import sha256
import time

def reader_question(state,group,preview=False):
 artifacts=state.get('previewArtifacts' if preview else 'artifacts',{})
 for p in state['people']:
  if not p['active'] or p['group']!=group:continue
  task=next((t for t in state['plan']['tasks'] if p['slot'] in t['assignees']),{})
  a=artifacts.get(p['id'],{});text=a.get('question','').strip()
  if task.get('roleId')=='reader' and text and (a.get('questionSent') or any(a.get('submitted',{}).values())):
   return dict(id=sha256((p['id']+text).encode()).hexdigest()[:16],person=p['id'],name=p['name'] or 'Reader',text=text)
 return None

def details(state,group,e,preview=False):
 plan=state['plan'];phases=plan['phases'];live=plan['live'];people=[p for p in state['people'] if p['active'] and p['group']==group]
 responses=state.get('previewResponses' if preview else 'responses',{});team=state.get('previewAdaptive' if preview else 'adaptive',{}).get('teams',{}).get(str(group),{})
 changes=team.get('changes',[]);rules=plan.get('progress',{}).get('rules') or []
 from adaptive_backend import current_requests
 requests=current_requests(state,group,preview)
 individual=next((p for p in phases if p['kind']=='individual'),phases[0]);current=next((i for i,p in enumerate(phases) if p['id']==live.get('phaseId')),0)
 rule=next((r for r in rules if r['id']=='role-work'),{});threshold=rule.get('remainingMinutes',min(2,individual['minutes']))
 remaining=live.get('remaining') if live.get('paused') else individual['minutes']*60-(time.time()-(live.get('startedAt') or time.time()))
 due=live.get('started') and (current>phases.index(individual) or current==phases.index(individual) and remaining<=threshold*60)
 missing=[p for p in people if not responses.get(p['id'],{}).get(individual['id']+':submitted')]
 help_requests=[r for r in requests if r.get('requestKind')=='difficulty'];targets=list(dict.fromkeys([p['id'] for p in missing]+[r['person'] for r in help_requests]))
 def change_for(pattern):return next((c for c in reversed(changes) if c['pattern']==pattern),None)
 scaffold=change_for('scaffold');q=reader_question(state,group,preview);exchange=change_for('written-exchange');reason=change_for('reason-check')
 answers=[r['initial']['answer'] for r in e['rows'] if r['initial']];same=len(answers)==len(people) and len(answers)>1 and len(set(answers))==1
 linked=[]
 if q:
  linked=[dict(person=pid,**r) for c in changes if c['pattern']=='written-exchange' for pid,r in c.get('responses',{}).items() if r.get('shared') and r.get('respondsToQuestion')==q['id']]
 posts=[r for r in (reason or {}).get('responses',{}).values() if r.get('shared')];replies=[r for r in posts if r.get('reply') and r.get('replyTo')]
 def status(active,c,checked=False):
  if checked:return 'checked'
  if active:return 'attention'
  return 'collecting'
 role_status=status((due and missing) or help_requests,scaffold,not missing and not help_requests)
 peer_due=live.get('started') and current>=len(phases)-1
 peer_status='checked' if q and linked else 'attention' if q and peer_due else 'collecting'
 reason_status='checked' if same and posts and replies else 'attention' if same else 'collecting'
 return {
  'role-work':dict(code='R1',title='Each learner makes a contribution',status=role_status,expected=f'{len(people)} role contributions by the checkpoint.',observed=f'{len(people)-len(missing)} of {len(people)} role contributions saved.',why='The role-work checkpoint has been reached.' if due and missing else 'A learner requested help.' if help_requests else 'Waiting for the checkpoint.' if missing else 'All role contributions are saved.',requests=[r['text'] for r in help_requests],names=[p['name'] or 'Learner' for p in missing],targets=targets,pattern='scaffold',change=scaffold,suggestion='Offer smaller steps',response='Keep the role task. Break it into three short steps for the learner who needs help.'),
  'peer-use':dict(code='R2',title='Peer questions receive a response',status=peer_status,expected='Respond to the Reader’s question before submitting the shared critique.',observed=('1 linked response saved.' if linked else '0 linked responses saved.') if q else 'No shared Reader question yet.',why='The team has reached shared writing with an unanswered question.' if q and peer_due and not linked else 'Review the response against the question.' if linked else 'Waiting for a shared question and the final stage.',question=q,linked=linked,targets=[p['id'] for p in people],pattern='written-exchange',change=exchange,suggestion='Bring the question into shared writing',response='Show the unresolved question beside the critique and give teammates a direct response field.'),
  'answer-pattern':dict(code='R3',title='Agreement includes a check of reasoning',status=reason_status,expected='If all initial choices match, record a response to a contrasting claim and one peer check.',observed=f'All {len(answers)} chose the same answer. '+('A contrasting explanation and peer reply are saved.' if posts and replies else 'No completed contrast-and-reply exchange.') if same else 'Initial choices do not all match yet.',why='Agreement triggers a reasoning check; it is not a wrong answer.' if same else 'This conditional check is not triggered.',targets=[p['id'] for p in people],pattern='reason-check',change=reason,suggestion='Test a contrasting claim',response='Add one counterfactual. Ask for an explanation and a teammate’s response.',posts=len(posts),replies=len(replies))}
