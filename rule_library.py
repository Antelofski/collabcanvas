"""Seed dictionary of progress rules, grouped by the collaboration problem each rule watches.

Sources: the "Limitations and problems" section of the Wikipedia page on cooperative
learning, instructor feedback on the pilot, and the rules in the first prototype.
Every threshold is a starting value for the teacher to change. No model is called.

The library is instructor-level state. It survives a new activity and keeps:
  carry   "next time" decisions saved from an alert
  custom  rules the teacher wrote, offered again in later activities
  runs    a short record of each finished activity (rules, alerts, roster)
"""
from copy import deepcopy
import secrets, time

FAMILIES=[
 dict(id='loafing',name='Social loafing',problem='A member lets the team carry the work.',design='Give each role an output that a teammate needs for the next step.',caution='A missing or short contribution does not show low effort. Roles differ in output size.'),
 dict(id='reliance',name='Over-reliance on stronger students',problem='The group answer hides what one learner understands.',design='Keep one private individual question in every activity.',caution='One wrong choice is a reason to read the learner’s reason. It is not a grade.'),
 dict(id='divide',name='Divide and conquer',problem='Members split the task and never review each other’s part.',design='Add a step where a non-author reviews each part.',caution='Split work is fine when the parts come back together.'),
 dict(id='quiet',name='Quiet teams and unheard members',problem='A team does not interact, or a member’s point is passed over.',design='Give writing time before talk, and a private way to ask for help.',caution='Silence can be thinking time. Speech is not recorded.'),
 dict(id='pace',name='Task difficulty and pace',problem='The task is too hard, unclear, or too easy for the time.',design='Prepare a smaller-step version and an extension for each role.',caution='Slow progress has many causes: an unclear task, waiting for a peer, or careful work.'),
 dict(id='agreement',name='Agreement, majority and conflict',problem='Matching answers end the discussion, or a disagreement is dropped.',design='Collect private first answers before the discussion.',caution='Agreement is not a problem by itself. Do not create a dispute for its own sake.'),
 dict(id='processing',name='Peer feedback and group processing',problem='Feedback is polite but empty, and nobody reflects on the teamwork.',design='End each activity with a short private reflection.',caution='Peer ratings are social. Read them beside the work.'),
 dict(id='outsourcing',name='Outsourced thinking',problem='An answer arrives from outside the activity.',design='Ask for evidence that points to the material on screen.',caution='A paste can come from the learner’s own notes or an assistive tool. Only its length is recorded.'),
 dict(id='fatigue',name='Group fatigue',problem='The same role with the same teammates, again and again.',design='Rotate roles and groups across activities.',caution='This needs records from more than one activity.')]

def _n(key,label,default,low,high,step=1,unit=''):return dict(key=key,label=label,default=default,min=low,max=high,step=step,unit=unit,type='number')
def _b(key,label,default=False):return dict(key=key,label=label,default=default,type='flag')

# stage: where the rule is checked by default. needs: what the activity must provide.
# default: 'on', 'shared' (on when the activity has a shared product) or 'off'.
SEEDS=[
 dict(id='role-work',family='loafing',short='Contribution',title='Each learner makes a contribution',condition='submission',stage='individual',remaining=2,default='on',scope='team',detection='auto',
  expectation='Each learner saves one role contribution by the chosen checkpoint. A help request also prompts review.',
  evidence='Saved role submissions; no claim about spoken participation.',
  trigger='No saved contribution at the reminder time, or a request for help.',
  response='Visit the learner, clarify the task, or adjust their workload.',
  nextTime='If one role is late in most teams, shrink that role’s task.',adds='',pattern='scaffold'),
 dict(id='reading-check',family='reliance',short='Individual check',title='Each learner distinguishes filtering from time',condition='private_check',stage='check',default='on',scope='team',detection='auto',
  expectation='Each learner identifies a population filter and explains the reading.',
  evidence='A private multiple-choice answer and a short reason. An incorrect answer is flagged for review.',
  trigger='A private first answer that does not match the key.',
  response='Preview a frame comparison for this team, then assign a private follow-up.',
  nextTime='Put the private question before the discussion.',adds='One private question with a short reason.',pattern='comparison'),
 dict(id='peer-use',family='divide',short='Peer response',title='Peer questions receive a response',condition='teacher_review',stage='final',default='on',scope='team',detection='auto+teacher',
  expectation='Before submitting the shared critique, respond to each Reader question or explicitly record what remains unresolved.',
  evidence='Teacher inspects the Reader log and shared critique, or asks the team. No automatic rubric score.',
  trigger='The team reaches shared writing with an unanswered question.',
  response='Ask the Author or Checker to answer the unresolved question before revising.',
  nextTime='Add “reply to a peer” as a step before shared writing.',adds='',pattern='written-exchange'),
 dict(id='support-request',family='quiet',short='Support request',title='A learner asks for a different way to work',condition='support_request',stage='individual',default='on',scope='team',detection='self',
  expectation='Learners can request smaller steps or a written way to contribute.',
  evidence='An explicit private request. Silence or inactivity is not a diagnosis.',
  trigger='Any open request, including “my point was not discussed”.',
  response='Review the request, then preview step-by-step support or a written exchange.',
  nextTime='Start with individual writing before talk.',adds='A private menu: smaller steps, write first, my point was not discussed.'),
 dict(id='answer-pattern',family='agreement',short='Reasoning check',title='Agreement includes a check of reasoning',condition='answer_pattern',stage='check',default='on',scope='team',detection='auto',needs=['keyed'],
  expectation='When all initial choices match, record a response to a contrasting claim and one linked peer check.',
  evidence='All active team members saved the same private MCQ choice. Agreement alone is not a problem.',
  trigger='All first choices match and no contrast-and-reply exchange is saved.',
  response='Review reasons. Keep the activity, test the agreed claim, or add conceptual support.',
  nextTime='Group learners by different first answers.',adds='',pattern='reason-check'),
 dict(id='contribution-balance',family='loafing',short='Shared authorship',title='Shared work has more than one author',condition='contribution_balance',stage='final',default='off',scope='team',detection='auto',needs=['shared'],
  expectation='At least two members add to or edit the shared critique.',
  evidence='Who saved each change to the shared critique. One member may be typing for the team, so ask before judging.',
  trigger='Past the midpoint of shared writing, one member saved every part of the critique.',
  response='Ask for one round of turns: each member adds a point before the team finishes.',
  nextTime='Give each member a named section of the shared product.',adds='The shared critique shows who edited it.'),
 dict(id='random-explainer',family='loafing',short='Random explainer',title='Any member can explain the team’s answer',condition='random_explainer',stage='final',default='shared',scope='team',detection='auto+teacher',needs=['shared'],
  params=[_n('minutes','Alert when there is no explanation after',2,0.5,15,0.5,'min'),_n('minChars','Shortest explanation to accept',40,10,400,10,'characters')],
  expectation='One member, picked at random when the critique is saved, explains the team’s decision and one reason in private.',
  evidence='The picked member’s written explanation. The teacher reads it against the critique.',
  trigger='No explanation after {minutes} min, or one shorter than {minChars} characters.',
  response='Ask teammates to explain again, then pick another member.',
  nextTime='Tell the class about the random pick at the start.',adds='Everyone sees that one member will be picked. That member gets a private explanation box.'),
 dict(id='co-sign',family='divide',short='Second sign-off',title='Decisions have a second sign-off',condition='co_sign',stage='final',default='shared',scope='team',detection='auto',needs=['shared'],
  params=[_n('signoffs','Sign-offs needed from other members',1,1,4,1,''),_n('minutes','Alert when missing after',2,0.5,15,0.5,'min')],
  expectation='A member who did not save the critique reads it and signs off with one reason.',
  evidence='Sign-offs on the current version of the shared critique. Editing the critique asks for a new sign-off.',
  trigger='Fewer than {signoffs} sign-off(s) from another member {minutes} min after the critique is saved.',
  response='Remind the team that the critique needs a second reader before they finish.',
  nextTime='Turn sign-off on from the start for ranking and table tasks.',adds='A sign-off control under the shared critique: agree or would change, with one reason.'),
 dict(id='quiet-team',family='quiet',short='Quiet team',title='The team works together during shared stages',condition='quiet_team',stage='final',default='off',scope='team',detection='auto+teacher',custom=True,
  params=[_n('minutes','Alert after no shared activity for',3,1,20,0.5,'min')],
  expectation='During a shared stage the team edits its shared work or posts a one-line status.',
  evidence='Times of shared edits and status lines. Speech is not recorded; the team may be talking.',
  trigger='No shared edit or status for {minutes} min while the stage is live.',
  response='Visit the team, or add one round of turns.',
  nextTime='Add a mid-stage status line to the activity.',adds='A one-line team status above the shared work.',pattern='written-exchange'),
 dict(id='stalled-learner',family='pace',short='Stalled learner',title='No learner stalls mid-stage',condition='stalled_learner',stage='individual',default='on',scope='team',detection='auto',custom=True,
  params=[_n('minutes','Alert after no saved change for',4,1,20,0.5,'min')],
  expectation='Each learner saves some change during individual work until their role work is shared.',
  evidence='The time of each learner’s last saved change. Reading and thinking leave no trace.',
  trigger='No saved change for {minutes} min and the role work is not shared.',
  response='Read the draft. Offer smaller steps to that learner and keep the same goal.',
  nextTime='Start that task with a worked example.',adds='',pattern='scaffold'),
 dict(id='shared-blocker',family='pace',short='Shared blocker',title='One step does not block many learners',condition='shared_blocker',stage='individual',remaining=2,default='off',scope='class',detection='auto',
  params=[_n('share','Alert when this share of the class is missing the step',50,20,100,5,'%'),_n('teams','Or when this many teams ask for smaller steps',2,2,6,1,'teams')],
  expectation='Most learners get past each step of the activity.',
  evidence='Missing work at the checkpoint across the class, and requests for smaller steps.',
  trigger='{share}% of the class is missing the step at the checkpoint, or {teams} teams ask for smaller steps.',
  response='Clarify to the whole class and add time.',
  nextTime='Rewrite that step. This is a design problem, not a learner problem.',adds=''),
 dict(id='early-finish',family='pace',short='Early finish',title='An early finish gets a depth check',condition='early_finish',stage='final',default='off',scope='team',detection='auto',custom=True,
  params=[_n('share','Alert when this share of the stage time is left',50,10,90,5,'%')],
  expectation='A team uses the stage to reason, not only to fill fields.',
  evidence='The stage time left when the team first saved its work. Needs a live, timed stage.',
  trigger='The team finishes with more than {share}% of the stage time left.',
  response='Pick a member to explain the answer. Strong answer: give an extension. Weak answer: reopen it.',
  nextTime='Raise the task demand, or prepare an extension.',adds=''),
 dict(id='workload-balance',family='pace',short='Role workload',title='No role is behind in most teams',condition='workload_balance',stage='individual',remaining=2,default='off',scope='class',detection='auto',needs=['teams2'],
  params=[_n('share','Alert when the role is behind in this share of teams',50,30,100,5,'%')],
  expectation='Roles finish their work at similar times.',
  evidence='Which role had not shared work at the checkpoint, compared across teams.',
  trigger='The same role has not shared work at the checkpoint in more than {share}% of teams.',
  response='Add time, or move one sub-task to another role.',
  nextTime='Rebalance the role briefs.',adds=''),
 dict(id='shared-misconception',family='agreement',short='Shared wrong answer',title='A shared wrong answer goes to the teacher',condition='shared_misconception',stage='check',default='on',scope='team',detection='auto',needs=['keyed'],
  expectation='A team that shares one wrong first answer gets new information from the teacher, not more peer discussion.',
  evidence='All private first answers in the team. Discussion among learners who share a wrong answer tends to confirm it.',
  trigger='All first choices match and do not match the key.',
  response='Explain, or add a contrasting case. Then ask a new private question.',
  nextTime='Add the contrasting case to the material.',adds='',pattern='comparison'),
 dict(id='resolve-disagreement',family='agreement',short='Open disagreement',title='A minority view gets a reasoned response',condition='unresolved_difference',stage='final',default='off',scope='team',detection='auto+teacher',needs=['shared'],
  params=[_n('minChars','Shortest note to accept',20,5,400,5,'characters'),_n('overwrites','Count a field as contested after this many takeovers',3,2,10,1,'')],
  expectation='The shared critique says why the team rejected another reading, or records it as unresolved.',
  evidence='First choices that differ, an objection at sign-off, or a field that members keep overwriting, compared with the team’s “why not” note.',
  trigger='A recorded difference and no “why not” note of at least {minChars} characters.',
  response='Ask for three lines: reading A, reading B, and the evidence that would decide.',
  nextTime='Put a rule for disagreement in the brief.',adds='A “reading we rejected or left open” field under the shared critique.',pattern='written-exchange'),
 dict(id='specific-feedback',family='processing',short='Specific feedback',title='Peer feedback names a concrete example',condition='feedback_specific',stage='final',default='off',scope='team',detection='auto+teacher',
  params=[_n('minChars','Shortest feedback to accept',40,10,400,5,'characters')],
  expectation='Each piece of peer feedback points to one part of a peer’s work and gives a reason.',
  evidence='Sign-off notes, claim checks and replies to peers: their length and whether they name a target. Quality still needs a teacher’s read.',
  trigger='Feedback shorter than {minChars} characters, or with no target.',
  response='Ask for the example behind the judgment.',
  nextTime='Make the target a required field.',adds=''),
 dict(id='closing-pulse',family='processing',short='Closing check',title='Each learner gives a private closing check',condition='closing_pulse',stage='final',default='on',scope='team',detection='self',
  params=[_n('minutes','Open the check when this much time is left',2,0,15,0.5,'min')],
  expectation='At the end, each learner answers in private: Did you contribute? Was your work used? One thing to change.',
  evidence='Private answers, seen by the teacher only. Read them beside the team’s record.',
  trigger='A “No” answer, or every answer is “Yes” while another rule fired for the team.',
  response='Read it beside the team’s record. Talk to the learner in private.',
  nextTime='Change roles or groups. Use the “one thing to change” answers in the next plan.',adds='A three-question private check at the end of the last stage.'),
 dict(id='own-words',family='outsourcing',short='Pasted text',title='Answers are written in the interface',condition='pasted_text',stage='individual',default='off',scope='team',detection='auto',custom=True,
  params=[_n('minChars','Note a paste longer than',80,20,2000,10,'characters'),_b('block','Turn off paste in answer fields')],
  expectation='Learners write their answers in the answer fields.',
  evidence='The length of each paste into an answer field. The pasted text is not stored.',
  trigger='A paste of more than {minChars} characters into an answer field.',
  response='Ask the learner to explain the answer to a teammate.',
  nextTime='Turn off paste in answer fields.',adds='Learners are told that long pastes are noted by length. Optionally, paste is turned off.'),
 dict(id='rotation',family='fatigue',short='Rotation',title='Roles and teammates change across activities',condition='rotation',stage='first',default='off',scope='class',detection='auto',needs=['history'],
  params=[_n('times','Alert at this many times in the same role or team',3,2,10,1,'times')],
  expectation='A learner does not hold the same role with the same teammates many times.',
  evidence='Names, roles and teams from earlier activities in this library, matched by the name a learner enters.',
  trigger='A learner has the same role, or the same teammates, {times} times in a row of recorded activities.',
  response='No change during class.',
  nextTime='Rotate roles, regroup, or run a shorter version.',adds='')]

# Kept valid for plans saved by the first prototype. Not offered as new suggestions.
LEGACY=[
 dict(id='participation',family='quiet',short='Chance to contribute',title='Everyone has a chance to contribute',condition='teacher_review',stage='individual',default='off',scope='team',detection='teacher',
  expectation='Every learner can share an idea or ask for help.',evidence='Teacher observation or a private help request. Speech is not recorded.',trigger='A teacher observation.',
  response='Offer a written exchange, clarify a role, or visit the team.',nextTime='Start with individual writing before talk.',adds=''),
 dict(id='role-clarity',family='pace',short='Next step',title='Each learner knows their next step',condition='teacher_review',stage='individual',default='off',scope='team',detection='teacher',
  expectation='Each learner can state their own contribution and who needs it next.',evidence='Teacher asks the learner to describe their task, or reviews a request for clearer instructions.',trigger='A teacher observation.',
  response='Clarify the role brief and show the next handoff.',nextTime='Rewrite the brief for that role.',adds='')]

BY_ID={s['id']:s for s in SEEDS+LEGACY}
LEGACY_IDS=[s['id'] for s in LEGACY]
BY_CONDITION={s['condition']:s for s in SEEDS if s['condition']!='teacher_review'}
CUSTOM_DETECTORS=[s['condition'] for s in SEEDS if s.get('custom')]
ORDER=['role-work','reading-check','peer-use','support-request','answer-pattern','contribution-balance','random-explainer','co-sign','quiet-team','stalled-learner','shared-blocker','early-finish','workload-balance','shared-misconception','resolve-disagreement','specific-feedback','closing-pulse','own-words','rotation']

def seed_for(rule):
 """The library entry behind a stored rule: by id, or by detector for a teacher-written variant."""
 return BY_ID.get(rule.get('id')) or BY_CONDITION.get(rule.get('condition'))

def param_specs(condition):return (BY_CONDITION.get(condition) or {}).get('params',[])
def default_params(condition):return {p['key']:p['default'] for p in param_specs(condition)}
def clean_params(condition,raw):
 raw=raw if isinstance(raw,dict) else {};out={}
 for spec in param_specs(condition):
  value=raw.get(spec['key'],spec['default'])
  if spec['type']=='flag':out[spec['key']]=bool(value);continue
  try:value=float(value)
  except (TypeError,ValueError):value=spec['default']
  value=min(spec['max'],max(spec['min'],value))
  out[spec['key']]=int(value) if float(value).is_integer() else value
 return out

def capabilities(plan):
 """What this activity can support. Rules that need more are listed but cannot run."""
 return dict(shared=plan.get('studio',{}).get('flow')=='group-first',keyed=True,teams2=plan.get('groupCount',1)>=2,history=True)
NEEDS_TEXT=dict(shared='Needs a shared product. Use the group-first flow (discuss, work by role, write together).',keyed='Needs a private question with a key.',teams2='Needs at least two teams.',history='Needs records of earlier activities.')
def unavailable(plan):
 caps=capabilities(plan)
 return {s['id']:NEEDS_TEXT[n] for s in SEEDS for n in s.get('needs',[]) if not caps.get(n)}

def phase_for(plan,seed,legacy=None):
 phases=plan['phases'];individual=next((p for p in phases if p['kind']=='individual'),phases[0])
 if seed['stage']=='final':return phases[-1]
 if seed['stage']=='first':return phases[0]
 if seed['stage']=='check':
  pid=(legacy or {}).get('checkPhase',individual['id']);return next((p for p in phases if p['id']==pid),individual)
 return individual

def default_rules(plan):
 """The starter list for this activity, in a stable order."""
 legacy=plan.get('progress',{});legacy=legacy if isinstance(legacy,dict) else {}
 caps=capabilities(plan);off=unavailable(plan);rows=[]
 flags={'role-work':legacy.get('submissions',True),'reading-check':legacy.get('privateCheck',True),'peer-use':legacy.get('rubric',True)}
 for rid in ORDER:
  s=BY_ID[rid];phase=phase_for(plan,s,legacy)
  enabled=flags[rid] if rid in flags else (s['default']=='on' or s['default']=='shared' and caps['shared'])
  rows.append(dict(id=rid,title=s['title'],condition=s['condition'],phaseId=phase['id'],remainingMinutes=min(s.get('remaining',0),phase['minutes']),expectation=s['expectation'],evidence=s['evidence'],response=s['response'],nextTime=s['nextTime'],params=default_params(s['condition']),enabled=bool(enabled) and rid not in off,origin='suggested'))
 if legacy.get('participation'):
  s=BY_ID['participation'];phase=phase_for(plan,s,legacy)
  rows.append(dict(id=s['id'],title=s['title'],condition=s['condition'],phaseId=phase['id'],remainingMinutes=0,expectation=s['expectation'],evidence=s['evidence'],response=s['response'],nextTime=s['nextTime'],params={},enabled=True,origin='suggested'))
 return rows

# ---------------------------------------------------------------- instructor library
def library(state,create=False):
 if create:return state.setdefault('ruleLibrary',{'carry':[],'custom':[],'runs':[]})
 return state.get('ruleLibrary') or {'carry':[],'custom':[],'runs':[]}

def run_id(state):return state.get('runId') or 'first'

def apply_library(rows,plan,state):
 """Apply saved “next time” decisions and offer earlier custom rules. Never changes the activity that produced them."""
 lib=library(state);current=run_id(state);phases={p['id'] for p in plan['phases']};off=unavailable(plan)
 for c in lib.get('carry',[]):
  if c.get('fromRun')==current:continue
  row=next((r for r in rows if r['id']==c['ruleId']),None)
  if not row:continue
  if c.get('enable') and row['id'] not in off:row['enabled']=True
  if c.get('params'):row['params']=clean_params(row['condition'],{**row.get('params',{}),**c['params']})
  row['carried']=dict(id=c['id'],note=c.get('note',''),title=c.get('title',''),time=c.get('time'))
 for c in lib.get('custom',[]):
  if any(r['id']==c['id'] for r in rows):continue
  row=deepcopy(c);row['enabled']=False;row['origin']='custom'
  if row.get('phaseId') not in phases:
   seed=BY_CONDITION.get(row['condition']);row['phaseId']=phase_for(plan,seed)['id'] if seed else plan['phases'][-1]['id']
  row['remainingMinutes']=0;row['remembered']=True;rows.append(row)
 return rows

def carry_stored(plan,state):
 """For a new activity that starts from a saved rule list: add seeds it lacks (off) and apply the library."""
 rules=plan.get('progress',{}).get('rules')
 if rules is None:return
 have={r['id'] for r in rules}
 for row in default_rules(plan):
  if row['id'] not in have and row['id'] not in LEGACY_IDS:row['enabled']=False;rules.append(row)
 apply_library(rules,plan,state)
 for r in rules:r.pop('carried',None);r.pop('remembered',None)

def remember_custom(state,plan):
 """Teacher-written rules are kept so they can be offered in the next activity."""
 rules=plan.get('progress',{}).get('rules') or [];custom=[r for r in rules if r.get('origin')=='custom']
 if not custom and not state.get('ruleLibrary'):return
 lib=library(state,True);known={c['id']:c for c in lib['custom']}
 for r in custom:known[r['id']]={k:deepcopy(r[k]) for k in ['id','title','condition','phaseId','expectation','evidence','response','nextTime','params'] if k in r}
 lib['custom']=list(known.values())[-40:]

def add_carry(state,body,rules):
 rule=next((r for r in rules if r['id']==body.get('ruleId')),None)
 if not rule:raise ValueError('Choose a rule from this activity.')
 note=str(body.get('note','')).strip()[:1500]
 if not note:raise ValueError('Write what to do next time.')
 lib=library(state,True)
 entry=dict(id=secrets.token_hex(4),ruleId=rule['id'],ruleTitle=rule['title'],enable=bool(body.get('enable',True)),params=clean_params(rule['condition'],body.get('params') or rule.get('params')),note=note,observed=str(body.get('observed',''))[:600],group=body.get('group') if isinstance(body.get('group'),int) else None,title=state['plan'].get('title',''),fromRun=run_id(state),time=time.time())
 lib['carry']=[c for c in lib['carry'] if not (c['ruleId']==rule['id'] and c.get('fromRun')==entry['fromRun'])]+[entry]
 lib['carry']=lib['carry'][-60:]
 return entry

def forget_custom(state,rule_id):
 lib=library(state,True);lib['custom']=[c for c in lib['custom'] if c['id']!=rule_id]

def remove_carry(state,carry_id):
 lib=library(state,True);before=len(lib['carry']);lib['carry']=[c for c in lib['carry'] if c['id']!=carry_id]
 if len(lib['carry'])==before:raise ValueError('That note is no longer in the library.')

def run_summary(state,rules):
 """A compact record of a finished activity. Names are kept only for learners who joined."""
 people=[p for p in state.get('people',[]) if p.get('active') and p.get('claimed') and p.get('name')]
 if not people and not state.get('responses') and not state.get('artifacts'):return None
 tasks=state['plan'].get('tasks',[])
 def role(p):
  t=next((t for t in tasks if p['slot'] in t.get('assignees',[])),{});return t.get('roleId') or t.get('title') or 'Learner'
 log=state.get('ruleLog',[])
 return dict(id=run_id(state),time=time.time(),title=state['plan'].get('title',''),materialId=state['plan'].get('materialId'),structure=state['plan'].get('structure'),
  people=[dict(name=p['name'].strip(),group=p['group'],role=role(p)) for p in people],rules=[r['id'] for r in rules if r.get('enabled')],
  incidents=[{k:i.get(k) for k in ['ruleId','group','outcome']} for i in log][-300:])

def archive_run(state,rules):
 """Call before the activity is replaced. Returns the library to carry into the next activity."""
 summary=run_summary(state,rules)
 if summary or state.get('ruleLibrary'):
  lib=library(state,True)
  if summary:lib['runs']=[r for r in lib['runs'] if r['id']!=summary['id']]+[summary];lib['runs']=lib['runs'][-40:]
  return deepcopy(lib)
 return None

def stats(state):
 """Per rule: in how many earlier activities it was on, how often it fired and how often it was handled."""
 out={};current=run_id(state)
 for run in library(state).get('runs',[]):
  if run.get('id')==current:continue
  for rid in run.get('rules',[]):out.setdefault(rid,dict(runs=0,firedRuns=0,alerts=0,handled=0))['runs']+=1
  fired=set()
  for i in run.get('incidents',[]):
   row=out.setdefault(i['ruleId'],dict(runs=0,firedRuns=0,alerts=0,handled=0));row['alerts']+=1;fired.add(i['ruleId'])
   if i.get('outcome')=='handled':row['handled']+=1
  for rid in fired:out[rid]['firedRuns']+=1
 return out

# ---------------------------------------------------------------- plain-text matching
KEYWORDS={
 'role-work':['not submit','no submission','missing work','has not shared','did not finish','does not finish','unfinished','incomplete','no contribution','not contribut'],
 'reading-check':['misconception','misread','misunderstand','wrong answer','individual understanding','each student understand','each learner understand','on their own'],
 'peer-use':['unanswered','no reply','no response','not respond','ignore question','ignores question','question ignored','peer question'],
 'support-request':['ask for help','asks for help','need help','needs help','confused','lost','struggl','overwhelm'],
 'answer-pattern':['groupthink','agree too','everyone agrees','all agree','same answer','consensus','without discuss','no debate'],
 'contribution-balance':['one person','one member','one author','one student','only one','dominat','does all','does everything','writes everything','types everything','takes over','others watch','just watch','free rid','free-rid','freerid','loaf','slack','coast','everyone contributes','equal contribution','unequal'],
 'random-explainer':['explain the answer','can explain','able to explain','rely on','relies on','stronger student','strong student','smart','carried','carry','hitchhik','copy the answer','copies the answer','accountab'],
 'co-sign':['split the','divide','dividing','each other’s part',"each other's part",'never read','do not read',"don't read",'no one checks','nobody checks','review each other','second reader','sign off','sign-off','double check','double-check','stitch'],
 'quiet-team':['quiet','silent','silence','not talking','no one talks','nobody talks',"don't talk",'do not talk','no discussion','not interact','no interaction','not working together','not collaborat','working alone','work alone','awkward'],
 'stalled-learner':['stall','stuck','idle','inactive','no progress','not typing','has not typed','no change','nothing saved','behind','lagging','gives up','gave up','stops working','not doing anything','frozen'],
 'shared-blocker':['everyone is stuck','whole class','many students','most students','many learners','instructions unclear','unclear instruction','task unclear','unclear task','too hard','too difficult','bottleneck','same step'],
 'early-finish':['early','too fast','rush','speed','quickly','sped','too easy','finish fast','finished fast','done too soon','superficial','shallow'],
 'workload-balance':['workload','one role','role is too','role too','uneven role','unfair role','unbalanced','too much work','heavier'],
 'shared-misconception':['all wrong','whole group wrong','whole team wrong','same mistake','shared mistake','same wrong','wrong together','confidently wrong'],
 'resolve-disagreement':['disagree','conflict','minority','different opinion','dissent','overrul','dismiss','not heard','unheard','ignored','shut down','talked over'],
 'specific-feedback':['feedback','vague','generic','nice job','good job','polite','empty praise','concrete example'],
 'closing-pulse':['self report','self-report','reflection','reflect','exit ticket','how they felt','fair','did they contribute','group processing'],
 'own-words':['paste','pasting','copy','copied','chatgpt','gpt','ai tool','llm','own words','cheat','outsourc','generated','plagiar'],
 'rotation':['same group','same team','same role','rotate','rotation','tired','fatigue','bored','again and again','switch roles','switch teams'],
 'participation':['participat','engage','everyone has a chance','chance to contribute','left out','excluded','include everyone'],
 'role-clarity':['next step','what to do','unclear role','role is unclear','know their role']}
def match_text(text):
 """Suggest library rules for a concern written in plain words. Keyword matching only; the teacher confirms.
 A match on a rule whose signal can also drive a teacher-written rule is marked custom."""
 import re
 text=str(text or '').lower().replace('’',"'");found=[];by_id={s['id']:s for s in SEEDS+LEGACY}
 for rank,(rule_id,words) in enumerate(KEYWORDS.items()):
  hits=[w for w in words if re.search(r'(?<![a-z])'+re.escape(w.replace('’',"'")),text)]
  if hits:
   s=by_id[rule_id];c=s['condition']
   found.append(dict(ruleId=rule_id,condition=c,title=s['title'],family=s['family'],trigger=s['trigger'],evidence=s['evidence'],params=default_params(c) if c!='teacher_review' else {},matched=hits[:3],score=len(hits),custom=c in CUSTOM_DETECTORS,rank=rank))
 found.sort(key=lambda x:(-x['score'],x['rank']))
 return [{k:v for k,v in m.items() if k!='rank'} for m in found[:4]]

def public(plan,state):
 """Everything the rule planner needs that is not stored in the plan."""
 keys=['id','family','short','title','condition','scope','detection','trigger','adds','nextTime','expectation','evidence','response']
 seeds={s['id']:dict({k:s.get(k,'') for k in keys},params=deepcopy(s.get('params',[])),pattern=s.get('pattern',''),needs=s.get('needs',[]),default=s['default']) for s in SEEDS+LEGACY}
 lib=library(state)
 return dict(families=deepcopy(FAMILIES),seeds=seeds,order=ORDER,unavailable=unavailable(plan),
  customDetectors=[dict(condition=c,title=BY_CONDITION[c]['title'],trigger=BY_CONDITION[c]['trigger'],evidence=BY_CONDITION[c]['evidence'],adds=BY_CONDITION[c]['adds'],family=BY_CONDITION[c]['family'],params=deepcopy(BY_CONDITION[c].get('params',[]))) for c in CUSTOM_DETECTORS],
  carry=deepcopy(lib.get('carry',[])),stats=stats(state),runs=len(lib.get('runs',[])),runId=run_id(state))
