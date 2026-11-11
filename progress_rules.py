"""Activity-specific rule suggestions and observable checks.

This local pilot does not call a model. Rules come from the seed dictionary in
rule_library. A rule the teacher writes uses teacher review or one of the ready-made
signals; free text never creates a new automatic detector.
"""
from copy import deepcopy
import time, json, hashlib
from rule_library import BY_ID, BY_CONDITION, CUSTOM_DETECTORS, default_rules, apply_library, clean_params, seed_for, unavailable

FLAGS={'role-work':'submissions','peer-use':'rubric','participation':'participation'}
MAX_RULES=40
INDIVIDUAL_ONLY=['submission','stalled_learner','workload_balance']
TEXT=['title','expectation','evidence','response','nextTime']

def suggested_rules(plan,state=None):
    rows=default_rules(plan)
    return apply_library(rows,plan,state) if state is not None else rows

def upgrade(rule,plan):
    """Bring a rule saved by an earlier version up to the current dictionary."""
    seed=BY_ID.get(rule.get('id'))
    if seed and rule.get('condition')!=seed['condition']:
        rule['condition']=seed['condition']
        for key in TEXT:rule[key]=seed[key]
        phase=next((p for p in plan['phases'] if p['id']==rule.get('phaseId')),None)
        if phase:rule['remainingMinutes']=min(seed.get('remaining',0),phase['minutes'])
    rule['params']=clean_params(rule.get('condition'),rule.get('params'))
    if 'nextTime' not in rule:rule['nextTime']=(seed_for(rule) or {}).get('nextTime','')
    rule.setdefault('origin','suggested' if seed else 'custom')
    return rule

def effective_rules(plan,state=None):
    stored=plan.get('progress',{}).get('rules')
    if stored is None:return suggested_rules(plan,state)
    return [upgrade(r,plan) for r in deepcopy(stored)]

def validate_rules(plan):
    progress=plan.get('progress',{})
    if not isinstance(progress,dict):raise ValueError('Invalid progress settings.')
    phases={p['id'] for p in plan['phases']}
    if progress.get('checkPhase') and progress['checkPhase'] not in phases:raise ValueError('Choose an existing private-check stage.')
    if 'rules' not in progress:return
    rows=progress['rules']
    if not isinstance(rows,list) or len(rows)>MAX_RULES:raise ValueError(f'Use up to {MAX_RULES} progress rules.')
    seen=set();clean=[];off=unavailable(plan)
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid progress rule.')
        rule={k:str(row.get(k,'')).strip()[:limit] for k,limit in [('id',80),('title',160),('phaseId',60),('condition',40),('expectation',1500),('evidence',1500),('response',1500),('nextTime',1500)]}
        if not rule['id'] or rule['id'] in seen or rule['phaseId'] not in phases:raise ValueError('Each rule needs a unique ID and an existing stage.')
        if not rule['title'] or not rule['expectation'] or not rule['evidence']:raise ValueError('Describe the rule, expectation, and evidence.')
        seed=BY_ID.get(rule['id']);phase=next(p for p in plan['phases'] if p['id']==rule['phaseId'])
        if seed:
            if rule['condition'] not in (seed['condition'],'teacher_review'):raise ValueError('This rule uses a fixed signal. Write a new rule to use a different one.')
            if rule['condition']!=seed['condition']:
                # Saved by the first prototype as a teacher-review rule. It now has a recorded signal.
                rule['condition']=seed['condition']
                for key in TEXT:rule[key]=seed[key]
                row={**row,'remainingMinutes':min(seed.get('remaining',0),phase['minutes'])}
        elif rule['condition']!='teacher_review' and rule['condition'] not in CUSTOM_DETECTORS:
            raise ValueError('A rule you write uses teacher review or one of the ready-made signals. Free text cannot create a new automatic detector.')
        rule['origin']='suggested' if seed else 'custom'
        rule['enabled']=bool(row.get('enabled',True)) and rule['id'] not in off
        rule['remainingMinutes']=float(row.get('remainingMinutes',0));rule['params']=clean_params(rule['condition'],row.get('params'))
        if not 0<=rule['remainingMinutes']<=phase['minutes']:raise ValueError('The reminder must fall within its stage.')
        if rule['condition']=='submission' and phase['kind']!='individual':raise ValueError('Role-submission checks belong to a role-work stage.')
        if rule['condition'] in INDIVIDUAL_ONLY and phase['kind']!='individual':raise ValueError(f'“{rule["title"]}” belongs to a role-work stage.')
        seen.add(rule['id']);clean.append(rule)
    progress['rules']=clean
    for rid,flag in FLAGS.items():progress[flag]=any(r['id']==rid and r['enabled'] for r in clean)
    reading=next((r for r in clean if r['id']=='reading-check'),None)
    if reading:progress['checkPhase']=reading['phaseId']

def rule_fingerprint(rule):
    return hashlib.sha256(json.dumps({k:rule[k] for k in ['id','title','phaseId','expectation','evidence']},sort_keys=True).encode()).hexdigest()

def describe(rule,result):
    """One rule's state for the teacher: what was expected, what was recorded, and why it matters now."""
    seed=seed_for(rule) or {};observed=result.get('observed','');why=result.get('why','')
    out=dict(id=rule['id'],title=rule['title'],phaseId=rule['phaseId'],condition=rule['condition'],status=result['status'],detail=(observed+(' '+why if why else '')).strip(),people=list(result.get('people') or []),response=rule['response'],
             expected=result.get('expected') or rule['expectation'],observed=observed,why=why,key=result.get('key',''),records=result.get('records') or [],
             family=seed.get('family','custom'),short=seed.get('short') or rule['title'],scope=seed.get('scope','team'),pattern=seed.get('pattern',''),nextTime=rule.get('nextTime',''))
    for extra in ['groups','role','allYes']:
        if extra in result:out[extra]=result[extra]
    return out

def rule_signals(state,group,evidence,preview=False):
    from collab_signals import DETECTORS,CLASS_CONDITIONS,Team,finish_team
    plan=state['plan'];phases=plan['phases'];live=plan['live'];now=time.time();signals=[];view=None
    people=[p for p in state['people'] if p['active'] and p['group']==group]
    responses=state.get('previewResponses' if preview else 'responses',{})
    team=state.get('previewProgress' if preview else 'progressRecords',{}).get('teams',{}).get(str(group),{})
    for rule in effective_rules(plan,state):
        if not rule['enabled'] or rule['condition'] in CLASS_CONDITIONS:continue
        phase=next((p for p in phases if p['id']==rule['phaseId']),None)
        if not phase:continue
        if rule['condition'] in DETECTORS:
            view=view or Team(state,group,evidence,preview,now)
            result=DETECTORS[rule['condition']](view,rule)
        else:
            status='waiting';detail='Waiting for this stage.';people_ids=[]
            if rule['condition']=='private_check':
                people_ids=[r['person'] for r in evidence['rows'] if r['initial'] and not r['initial']['correct']]
                if people_ids:
                    status='addressed' if (evidence.get('support') or {}).get('resolved') else 'attention'
                    detail=f'{len(people_ids)} initial answer{"" if len(people_ids)==1 else "s"} need{"s" if len(people_ids)==1 else ""} review; {evidence["answered"]} / {evidence["total"]} saved.'
                elif evidence['answered']:
                    status='checked' if evidence['answered']==evidence['total'] else 'collecting'
                    detail=f'{evidence["answered"]} / {evidence["total"]} private answers saved; none flagged so far.'
            elif rule['condition']=='submission':
                people_ids=[p['id'] for p in people if not responses.get(p['id'],{}).get(phase['id']+':submitted')]
                done=len(people)-len(people_ids);detail=f'{done} / {len(people)} role submissions saved.'
                current=next((i for i,p in enumerate(phases) if p['id']==live.get('phaseId')),0);target=phases.index(phase)
                remaining=live.get('remaining') if live.get('paused') else phase['minutes']*60-(now-(live.get('startedAt') or now))
                due=bool(live.get('started')) and (current>target or current==target and remaining<=rule['remainingMinutes']*60)
                status='checked' if not people_ids else 'attention' if due and not preview else 'collecting'
                if status=='attention':detail+=' The configured reminder time has been reached.'
            elif rule['condition']=='support_request':
                from adaptive_backend import current_requests
                requests=[r for r in current_requests(state,group,preview) if r.get('requestKind') in ['difficulty','participation','unheard']]
                people_ids=list(dict.fromkeys(r['person'] for r in requests))
                status='attention' if requests else 'collecting'
                detail=f'{len(requests)} private support request{"" if len(requests)==1 else "s"}. Review what the learner asked for.' if requests else 'No open request. This does not establish participation.'
            elif rule['condition']=='answer_pattern':
                answers=[r['initial']['answer'] for r in evidence['rows'] if r['initial']]
                if len(answers)==len(people) and len(answers)>1:
                    if len(set(answers))==1:
                        from adaptive_backend import fingerprint
                        changes=state.get('previewAdaptive' if preview else 'adaptive',{}).get('teams',{}).get(str(group),{})
                        decision=any(d['evidenceKey']==fingerprint(state,group) for d in changes.get('decisions',[])) if not preview else False
                        reviewed=any(c['pattern']=='reason-check' and c.get('reviewed') and c.get('reviewEvidenceKey')==fingerprint(state,group) for c in changes.get('changes',[])) if not preview else False
                        status='checked' if decision or reviewed else 'attention'
                        detail=f'All {len(answers)} chose the same answer. Check reasons; agreement alone is not evidence of a problem.'
                        if decision:detail+=' Instructor chose to keep the current activity.'
                        if reviewed:detail+=' Instructor reviewed the added reasoning task.'
                    else:status='checked';detail='Different choices are available to discuss. The quality of discussion still needs review.'
                else:status='collecting';detail=f'{len(answers)} / {len(people)} initial choices saved.'
            else:
                review=team.get('ruleReviews',{}).get(rule['id'])
                if review and review.get('ruleFingerprint')==rule_fingerprint(rule):status=review['status'];detail=review['note']
                else:status='needs-review';detail='Not yet checked by the instructor.'
            result=dict(status=status,expected=rule['expectation'],observed=detail,why='',people=people_ids)
            if plan.get('progress',{}).get('collaborationChecks') and rule['id'] in evidence.get('collaboration',{}):
                c=evidence['collaboration'][rule['id']];result=dict(status=c['status'],expected=c['expected'],observed=c['observed'],why=c['why'],people=c.get('targets',[]))
        signal=describe(rule,result)
        if not signal['key']:signal['key']=rule['id']+':'+hashlib.sha256(json.dumps([sorted(signal['people']),signal['observed']]).encode()).hexdigest()[:10]
        signals.append(signal)
    return finish_team(state,group,signals,preview)
