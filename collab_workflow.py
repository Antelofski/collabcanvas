"""Shared phase artifacts and isolated, real browser-journey test sessions."""
from copy import deepcopy
import json, secrets, time

TEST_RUNS={}

def group_first_plan(plan):
    p=deepcopy(plan);p.setdefault('studio',{})['flow']='group-first'
    minutes=max(3,int(p['budget']));opening=max(1,round(minutes*2/9));work=max(1,round(minutes*4/9));final=max(1,minutes-opening-work)
    p['phases']=[dict(id='read',title='Discuss together',kind='discussion',purpose='opening',minutes=opening,instruction='Compare the first and last frames. Record one initial group reading.',deliverable='One initial group reading'),dict(id='discuss',title='Work by role',kind='individual',purpose='rolework',minutes=work,instruction='Use the group’s initial reading. Complete your role task before opening peer work.',deliverable=str(p['groupSize'])+' role contributions'),dict(id='revise',title='Write together',kind='revision',purpose='critique',minutes=final,instruction='Bring all role findings together. Write one shared critique.',deliverable='One shared critique')]
    p['interaction']['visibility']='after_group';p['interaction']['regroup']='home'
    for task in p['tasks']:task['handoff']='Use the group’s initial reading in your role task. Bring your findings back to the shared critique.'
    if not p['live']['started']:p['live']['phaseId']='read'
    return p

def group_store(state,preview=False):return state.setdefault('previewStudioGroups' if preview else 'studioGroups',{})
def group_records(state,person,preview=False):
    return deepcopy(group_store(state,preview).get(str(person['group']),{'opening':{'text':'','version':0},'critique':{'message':'','misreading':'','change':'','version':0}}))
def roles_ready(state,group,preview=False):
    phases=[x['id'] for x in state['plan']['phases'] if x['kind']=='individual']
    responses=state.get('previewResponses' if preview else 'responses',{})
    people=[x for x in state['people'] if x['active'] and x['group']==group]
    return bool(phases) and bool(people) and all(all(responses.get(p['id'],{}).get(s+':submitted') for s in phases) for p in people)
def save_group(state,person,body,preview=False):
    section=body.get('section');phase=next((p for p in state['plan']['phases'] if p['id']==body.get('phaseId')),None)
    if state['plan'].get('studio',{}).get('flow')!='group-first':raise ValueError('This activity does not use a shared starting discussion.')
    if section not in ['opening','critique'] or not phase or phase.get('purpose')!=section:raise ValueError('Use the matching shared activity stage.')
    if section=='opening' and state['plan'].get('progress',{}).get('beforeDiscussion'):
        from progress_backend import records
        if not records(state,preview)['answers'].get(person['id'],{}).get('initial'):raise ValueError('Save your own reading check before joining the group response.')
    if section=='critique' and not roles_ready(state,person['group'],preview):raise ValueError('Everyone must share their role work before the shared critique opens.')
    record=body.get('record',{})
    if not isinstance(record,dict):raise ValueError('Invalid group response.')
    fields=['text'] if section=='opening' else ['message','misreading','change']
    clean={k:str(record.get(k,'')).strip()[:8000] for k in fields}
    if not all(clean.values()):raise ValueError('Complete each shared response before saving.')
    records=group_store(state,preview).setdefault(str(person['group']),{})
    old=records.get(section,{'version':0})
    if body.get('version',0)!=old.get('version',0):raise ValueError('A teammate saved a newer version. Reload the shared response before continuing.')
    clean.update(version=old.get('version',0)+1,updated=time.time(),person=person['id']);records[section]=clean
    from collab_signals import group_saved
    group_saved(state,person,section,old,clean,preview)
    return deepcopy(clean)

def start_test(state):
    now=time.time()
    for key in list(TEST_RUNS):
        if now-TEST_RUNS[key]['created']>3600:del TEST_RUNS[key]
    clone=deepcopy(state)
    for key in ['artifacts','previewArtifacts','responses','previewResponses','studioGroups','previewStudioGroups','posts','previewPosts','groupAnswers','previewGroupAnswers','feedback']:clone[key]={}
    for key in ['progressRecords','previewProgress','adaptive','previewAdaptive','signals','previewSignals','ruleLog']:clone.pop(key,None)
    clone['progressDrafts']=[]
    clone['requests']=[];clone['deployment']={'active':True,'deployedAt':now};clone['plan']['interaction']['mode']='async'
    for p in clone['people']:p['name']='Test '+chr(65+p['slot']);p['claimed']=False
    token=secrets.token_urlsafe(18);TEST_RUNS[token]={'state':clone,'created':now,'planRev':state['planRev'],'report':None}
    return {'id':token,'people':[{k:v for k,v in p.items() if k!='token'} for p in clone['people'] if p['active']],'plan':deepcopy(clone['plan']),'planRev':state['planRev']}

def test_run(token):
    run=TEST_RUNS.get(token)
    if not run or time.time()-run['created']>3600:raise ValueError('This test session has expired. Run the test again.')
    return run

def test_request(run,person_id,action,body,view_function,save_artifact):
    state=run['state'];person=next((p for p in state['people'] if p['active'] and p['id']==person_id),None)
    if not person:raise ValueError('Choose an active test learner.')
    if action=='/api/state':
        view=view_function(person,False,state=state);view.update(preview=True,testMode=True,instructorReadOnly=bool(run.get('readOnly')));return view
    if run.get('readOnly'):raise ValueError('Comparison previews are read-only.')
    if action=='/api/progress/answer':
        from progress_backend import save_answer
        answer=save_answer(state,person,body,False);state['rev']+=1;return {'ok':True,'answer':answer}
    if action=='/api/adaptive/response':
        from adaptive_backend import save_response
        response=save_response(state,person,body);state['rev']+=1;return {'ok':True,'response':response}
    if action=='/api/studio/save':
        result=save_artifact(state,person,body,False);state['rev']+=1;return {'ok':True,'artifact':result}
    if action=='/api/studio/group':
        record=save_group(state,person,body,False);state['rev']+=1;return {'ok':True,'record':record}
    if action=='/api/response':
        phase=next((x for x in state['plan']['phases'] if x['id']==body.get('phaseId')),None)
        if not phase:raise ValueError('Unknown test stage.')
        allowed=[t['id'] for t in state['plan']['tasks'] if person['slot'] in t['assignees']] if phase['kind']=='individual' else [phase['id']]
        record=state['responses'].setdefault(person['id'],{})
        for key,value in body.get('answers',{}).items():
            if key not in allowed:raise ValueError('This task is not assigned to this test learner.')
            record[phase['id']+':'+key]=str(value)[:8000]
        from collab_signals import touch,record_submit
        touch(state,person)
        if body.get('submitted'):record_submit(state,person,phase['id']);record[phase['id']+':submitted']=True
        state['rev']+=1;return {'ok':True,'rev':state['rev']}
    if action=='/api/collab':
        from collab_signals import learner_action
        result=learner_action(state,person,body,False)
        if not result.pop('quiet',False):state['rev']+=1
        return result
    if action=='/api/help':state['requests'].append({'person':person_id,'group':person['group'],'text':str(body.get('text','Help'))});return {'ok':True}
    raise ValueError('This operation is not part of the isolated UI test.')

def finish_test(state,run_id,checks):
    run=test_run(run_id)
    if run['planRev']!=state['planRev']:raise ValueError('The activity changed during testing. Test the new version.')
    if not isinstance(checks,list) or not checks or any(c.get('status') not in ['passed','failed','skipped'] for c in checks):raise ValueError('No valid test results were recorded.')
    result={'id':run_id,'planRev':state['planRev'],'time':time.time(),'checks':deepcopy(checks),'passed':sum(c['status']=='passed' for c in checks),'failed':sum(c['status']=='failed' for c in checks),'skipped':sum(c['status']=='skipped' for c in checks),'engine':'scripted-browser-journeys'}
    state['activityTest']=result;run['report']=result;return result
