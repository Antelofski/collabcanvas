"""Structured learner work and local, inspectable teaching edits for the pilot."""
from copy import deepcopy
from pathlib import Path
import json, re, time, secrets
from collab_workflow import group_first_plan, group_records

def stores(state, preview=False):
    return state.setdefault('previewArtifacts' if preview else 'artifacts', {})

def learner_artifacts(state, person, peers, visible, preview=False):
    records = stores(state, preview)
    fields = ['reflection', 'checks', 'beats', 'observations', 'criteria', 'reviews', 'revision', 'decision', 'question', 'questionSent', 'returned', 'submitted', 'updated', 'version']
    result = {person['id']: deepcopy(records.get(person['id'], {}))}
    for peer in peers:
        if peer['id'] == person['id'] or not visible:
            continue
        record = records.get(peer['id'], {})
        result[peer['id']] = {k: deepcopy(record[k]) for k in fields if k in record}
    return result

def host_studio(state):
    return dict(artifacts=deepcopy(stores(state)), previewArtifacts=deepcopy(stores(state, True)),
                responses=deepcopy(state['responses']), previewResponses=deepcopy(state['previewResponses']),
                lectures=deepcopy(state.get('lectures', [])), edits=deepcopy(state.get('studioEdits', [])), groups=deepcopy(state.get('studioGroups',{})), previewGroups=deepcopy(state.get('previewStudioGroups',{})), activityTest=deepcopy(state.get('activityTest')))

def save_artifact(state, person, body, preview=False):
    store = stores(state, preview)
    old = store.get(person['id'], {'version': 0})
    if body.get('version', 0) != old.get('version', 0):
        raise ValueError('A newer copy was saved. Reload this page before continuing.')
    record = body.get('artifact', {})
    if not isinstance(record, dict) or len(json.dumps(record)) > 65000:
        raise ValueError('Keep this workspace under 65 KB.')
    allowed = {'checks','beats','observations','criteria','reviews','revision','decision','question','questionSent','returned','submitted','reflection'}
    result = {k: deepcopy(v) for k,v in record.items() if k in allowed}
    for key in ['beats','observations','checks']:
        if key in result:
            if not isinstance(result[key],list) or len(result[key])>12:raise ValueError('Keep a focused list of up to 12 items.')
            ids=[]
            for item in result[key]:
                if not isinstance(item,dict) or not isinstance(item.get('id'),str):raise ValueError('Every item needs an identifier.')
                ids.append(item['id'])
                if not isinstance(item.get('frame'),int) or not 0<=item['frame']<=6:raise ValueError('Choose a valid story frame.')
                if not isinstance(item.get('text',''),str) or len(item.get('text',''))>5000:raise ValueError('Keep each item under 5,000 characters.')
            if len(ids)!=len(set(ids)):raise ValueError('Item identifiers must be unique.')
    if 'checks' in result:
        for check in result['checks']:
            if check.get('status') not in ['supported','correct','notshown']:raise ValueError('Choose a valid evidence status.')
            if not all(isinstance(check.get(k,''),str) and len(check.get(k,''))<=5000 for k in ['statement','reason']):raise ValueError('Keep evidence checks under 5,000 characters.')
    if state['plan'].get('studio',{}).get('flow')=='group-first':
        role_phase=next((s['id'] for s in state['plan']['phases'] if s['kind']=='individual'),None)
        if result.get('submitted',{}).get(role_phase) and not group_records(state,person,preview).get('opening',{}).get('text'):raise ValueError('Save the group’s starting reading before sharing role work.')
    if 'reviews' in result:
        if not isinstance(result['reviews'],dict):raise ValueError('Invalid claim checks.')
        for review in result['reviews'].values():
            if not isinstance(review,dict) or review.get('status') not in [None,'supported','clarify','beyond']:raise ValueError('Choose a valid claim-check status.')
    if 'submitted' in result and (not isinstance(result['submitted'],dict) or any(type(v) is not bool for v in result['submitted'].values())):raise ValueError('Invalid completion state.')
    result.update(version=old.get('version',0)+1, updated=time.time())
    store[person['id']] = result
    return result

def seed_rehearsal(state):
    for p in state['people']:
        if not p['active']: continue
        g,s=p['group'],p['slot']
        role=next((t.get('roleId') for t in state['plan']['tasks'] if s in t['assignees']),['author','reader','editor'][s%3])
        work_phase=next((x['id'] for x in state['plan']['phases'] if x['kind']=='individual'),'read')
        record={'version':stores(state,True).get(p['id'],{}).get('version',0)+1,'updated':time.time(),'submitted':{work_phase:True}}
        if role=='author':
            record['beats']=[dict(id='beat-1',frame=0,text='Area shows population rather than land.',reason='Every square represents one million people.'),dict(id='beat-2',frame=4,text='Each filter leaves a smaller electorate.',reason='Only competitive Senate states remain.'),dict(id='beat-3',frame=6,text='The final comparison makes the small electorate tangible.',reason='The remaining voters are placed beside Florida.')]
        elif role=='reader':
            record['observations']=[dict(id='note-1',frame=3,kind='Needs context',text='Does this step remove people or resize the same states?'),dict(id='note-2',frame=6,kind='Easy to misread',text='Is Florida a comparison of population size or political power?')]
            record['question']='What exactly is being compared with Florida?'
        elif role=='checker':
            record['checks']=[dict(id='check-1',frame=0,statement='Map area represents land area.',status='correct',reason='The legend says one square represents one million people.'),dict(id='check-2',frame=4,statement='The maps show population declining over time.',status='correct',reason='The labels filter who is included; they do not show a time series.')]
        else:
            record['reflection']='The story communicates a narrowing electorate. Population size and political influence need separate claims.'
            record['criteria']=['Encoding','Scope of the claim','Reader clarity']
            if g==0:
                record['reviews']={'beat-1':dict(status='supported',frame=0,reason='The unit is people, not land.'),'beat-2':dict(status='clarify',frame=4,reason='Name the population retained at this filter.'),'beat-3':dict(status='clarify',frame=6,reason='Clarify population size; avoid inferring political influence.')}
                record['returned']=True
                record['submitted']['discuss']=True
        if g==1 and s==1:
            record['submitted'][work_phase]=False
        if g==0 and s==0:
            record['revision']='The story shows a narrowing population. Label the retained population at each transition; the Florida comparison is about size.'
        stores(state, True)[p['id']]=record
        if state['plan'].get('studio',{}).get('flow')=='group-first':
            state.setdefault('previewStudioGroups',{}).setdefault(str(g),{})['opening']={'text':'The remaining map is smaller because each step filters people. Area counts people, not land.','version':1,'updated':time.time(),'person':p['id']}

def import_slides(root, state, content, name):
    import fitz
    fid=secrets.token_hex(6)
    dest=Path(root)/'assets'/('lecture-'+fid+'.pdf');dest.write_bytes(content)
    doc=fitz.open(dest)
    if not len(doc):raise ValueError('The PDF has no pages.')
    # The supplied lecture is a two-up handout: slide labels are not PDF page numbers.
    handout=len(doc)==42 and 'Communicative Visualization' in doc[0].get_text()
    slides=[]
    if handout:
        for label,page_index,half in [(81,39,1),(82,40,0),(83,40,1),(84,41,0),(85,41,1)]:
            page=doc[page_index];r=page.rect
            clip=fitz.Rect(r.x0,r.y0+r.height*half/2,r.x1,r.y0+r.height*(half+1)/2)
            out=Path(root)/'assets'/('lecture-'+fid+'-'+str(label)+'.png')
            page.get_pixmap(matrix=fitz.Matrix(1.8,1.8),clip=clip).save(out)
            slides.append(dict(label=str(label),page=page_index+1,image='/assets/'+out.name,materialId=str(label)))
    else:
        for i in range(min(6,len(doc))):
            out=Path(root)/'assets'/('lecture-'+fid+'-'+str(i+1)+'.png')
            doc[i].get_pixmap(matrix=fitz.Matrix(1.15,1.15)).save(out)
            mid=fid+'-'+str(i+1)
            state['customMaterials'].append(dict(id=mid,slide='Page '+str(i+1),title=Path(name).stem+' · page '+str(i+1),author='Instructor upload',image='/assets/'+out.name,source='/assets/'+dest.name,context=doc[i].get_text()[:1000],kind='image'))
            slides.append(dict(label=str(i+1),page=i+1,image='/assets/'+out.name,materialId=mid))
    lecture=dict(id=fid,name=Path(name).name,pages=len(doc),file='/assets/'+dest.name,slides=slides,matched=handout)
    state.setdefault('lectures',[]).append(lecture)
    doc.close()
    return lecture

def propose_edit(plan, text, target, alternative=None):
    text=text.strip()
    if not text:raise ValueError('Describe the change you want.')
    p=deepcopy(plan);config=p.setdefault('studio',{})
    if alternative:
        if alternative not in ['compare','questions']:raise ValueError('Choose one of the two exchange arrangements.')
        config['exchange']=alternative
        title='Compare independent readings' if alternative=='compare' else 'Exchange questions before explanations'
        changes=['Author: keep an independent story draft.','Reader: '+('compare the two accounts side by side.' if alternative=='compare' else 'send a question before opening peer explanations.'),'Editor: retain the shared review and revision workspace.']
    elif re.search(r'(start|begin).*group discussion|shared discussion|initial (reading|interpretation)|先.*讨论|共同讨论',text,re.I):
        p=group_first_plan(p);config=p['studio'];config['editInstruction']=text[:3000]
        title='Discuss together → work by role → write together'
        changes=['Start: compare the first and last frames and save one group reading.','Role work: each learner uses that reading in their own tools; peer answers stay hidden until everyone submits.','Shared critique: bring the author’s claims, reader’s questions, evidence checks, and editor’s assessment into one writing space.','All four interfaces keep their role tools and update the stage order, source context, and handoffs together.']
    elif re.search(r'claim|逐条|主张|editor|编辑|review|检查|交回|澄清',text,re.I):
        config['review']='claims'
        config['editInstruction']=text[:3000]
        title='Review claims, then return for revision'
        changes=['Author: turn story beats into individually reviewable claims.','Editor: check each claim against a selected frame and return specific feedback.','Reader: contribute frame-linked questions to the review.','Author: revise using the returned checks; Editor can retain unresolved points.']
        for t in p['tasks']:
            if t.get('roleId')=='author':t['handoff']='Send your claims to the editor. Respond to each returned check before revising.'
            elif t.get('roleId')=='editor':t['handoff']='Check each claim against the source. Return specific changes to the author before forming a decision.'
        p['interaction']['visibility']='after_group'
    elif re.search(r'hide|independent|独立|隐藏',text,re.I):
        p['interaction']['visibility']='after_group';title='Protect independent preparation'
        changes=['All learners: peer work opens after the group finishes independent preparation.','Existing drafts and role-specific tools remain available.']
    else:
        raise ValueError('This local pilot supports group-first activity flow, claim review, independent preparation, and the two exchange alternatives. Your instruction has not been applied.')
    return dict(plan=p,title=title,changes=changes,target=target,instruction=text,engine='local-pilot')

def offline_workspace(root,view):
    """Keep the real role tools in an independent, self-contained HTML snapshot."""
    import base64, mimetypes
    root=Path(root);v=deepcopy(view)
    used={v['plan']['materialId']}|{t['materialId'] for t in v['plan']['tasks']}
    v['materials']=[m for m in v['materials'] if m['id'] in used]
    for m in v['materials']:
        if m.get('images'):m['image']=''
        for key in ['image']:
            source=root/m.get(key,'').lstrip('/')
            if source.is_file():m[key]='data:'+(mimetypes.guess_type(source)[0] or 'image/png')+';base64,'+base64.b64encode(source.read_bytes()).decode()
        if 'images' in m:
            m['images']=['data:'+(mimetypes.guess_type(path)[0] or 'image/jpeg')+';base64,'+base64.b64encode((root/path.lstrip('/')).read_bytes()).decode() if (root/path.lstrip('/')).is_file() else path for path in m['images']]
    v['plan']['interaction']['mode']='async';v['plan']['live']['started']=False
    payload=json.dumps(v,ensure_ascii=False).replace('</','<\\/')
    css='\n'.join((root/x).read_text() for x in ['student.css','apple-student.css','studio-student.css','progress-student.css'])
    base=(root/'student.js').read_text().replace('},1000);refresh();','},1000);')
    studio=(root/'studio-student.js').read_text()+'\n'+(root/'workflow-student.js').read_text()+'\n'+(root/'progress-student.js').read_text()
    driver='''const offlineSeed=SEED;
let offlineState=offlineSeed;try{offlineState=JSON.parse(localStorage.getItem('offline-state-'+offlineSeed.person.id)||'null')||offlineSeed}catch{}
function offlineRemember(){try{localStorage.setItem('offline-state-'+offlineSeed.person.id,JSON.stringify(offlineState))}catch{}}
async function api(path,body){
 if(body){
  if(path==='/api/progress/answer'){const answer={answer:body.answer,reason:body.reason,time:Date.now()/1000};offlineState.progress.answers[body.kind]=answer;offlineRemember();return {ok:true,answer}}
  if(path==='/api/studio/save'){const record={...body.artifact,version:(body.version||0)+1,updated:Date.now()/1000};offlineState.studioArtifacts[offlineState.person.id]=record;offlineRemember();return {ok:true,artifact:record}}
  if(path==='/api/studio/group'){const record={...body.record,version:(body.version||0)+1,updated:Date.now()/1000};offlineState.studioGroup??={};offlineState.studioGroup[body.section]=record;offlineRemember();return {ok:true,record}}
  if(path==='/api/response'){const r=offlineState.responses[offlineState.person.id]||={};for(const [k,val]of Object.entries(body.answers||{}))r[body.phaseId+':'+k]=val;if(body.submitted)r[body.phaseId+':submitted']=true}
  if(path==='/api/help')notice('Offline snapshot: this request is not sent to the teacher.');
  offlineRemember();return {ok:true};
 }
 return structuredClone(offlineState);
}
refresh();
'''.replace('SEED',payload)
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My editorial workspace</title><style>'+css+'.export{display:none!important}.offline-banner{font:11px/1.5 system-ui;text-align:center;padding:8px;background:#fff2dd;color:#8b6a39}</style><div class="offline-banner">Independent HTML snapshot · edits stay on this device · teammates and teacher do not receive updates</div><div id="app"></div><div id="notice" class="notice" role="status"></div><div id="mediaOverlay" class="media-overlay" hidden></div><script>'+base+'</script><script>'+studio+'</script><script>'+driver+'</script></html>'
