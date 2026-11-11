#!/usr/bin/env python3
"""Local classroom prototype. No cloud service or model API is used."""
import argparse, base64, html, io, json, mimetypes, os, secrets, socket, subprocess, sys, threading, time, webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
from model import MATERIALS, ROLEPLAY, default_plan, validate_plan
from studio_backend import host_studio, learner_artifacts, save_artifact, import_slides, seed_rehearsal, propose_edit, offline_workspace
from collab_workflow import group_records, save_group, roles_ready, start_test, test_run, test_request, finish_test
from tutorial_backend import launch_tutorial, practice_action
from progress_rules import suggested_rules, effective_rules
from rule_library import archive_run, carry_stored, remember_custom, match_text
from collab_signals import learner_action, host_action, rule_preview, touch, record_submit
from build_info import BUILD
from adaptive_backend import preview_change, apply_change, save_response as save_adaptive_response, review_change, review_signal, preview_session
from progress_backend import supported as supports_progress, learner_progress, host_progress, save_answer, intervene, create_draft, draft_session, support_comparison, config as progress_config
from knowledge_backend import report as knowledge_report, review as review_knowledge, save_snapshot as save_knowledge_snapshot
import qrcode
import qrcode.image.svg

LOCK=threading.RLock()
STATE=None; DATA=None; BASE=''; PORT=8931

def save():
    DATA.parent.mkdir(parents=True,exist_ok=True)
    tmp=DATA.with_suffix('.tmp'); tmp.write_text(json.dumps(STATE,ensure_ascii=False),encoding='utf8'); tmp.replace(DATA)

def reconcile():
    p=STATE['plan']
    for person in STATE['people']: person['active']=False
    for g in range(p['groupCount']):
        for s in range(p['groupSize']):
            person=next((x for x in STATE['people'] if x['group']==g and x['slot']==s),None)
            if person: person['active']=True
            else: STATE['people'].append(dict(id=secrets.token_hex(5),token=secrets.token_urlsafe(18),name='',group=g,slot=s,active=True,claimed=False))

def initialize(path):
    global DATA,STATE
    DATA=Path(path)
    if DATA.exists(): STATE=json.loads(DATA.read_text())
    else:
        seed=ROOT/'runtime'/'public-seed.json'
        if os.environ.get('COLLABCANVAS_PUBLIC','').lower() in ('1','true','yes') and seed.exists():
            STATE=json.loads(seed.read_text(encoding='utf8'))
            STATE['admin']=os.environ.get('COLLABCANVAS_DEMO_ADMIN') or STATE.get('admin') or secrets.token_urlsafe(24)
            STATE['code']=os.environ.get('COLLABCANVAS_DEMO_CODE') or STATE.get('code') or secrets.token_hex(3)
        else:
            admin=os.environ.get('COLLABCANVAS_DEMO_ADMIN') or secrets.token_urlsafe(24)
            STATE=dict(admin=admin,code=secrets.token_hex(3),plan=default_plan(),people=[],responses={},previewResponses={},posts={},previewPosts={},groupAnswers={},previewGroupAnswers={},feedback={},requests=[],rev=1,planRev=1,customMaterials=[])
            reconcile()
    STATE.setdefault('deployment',dict(active=False,deployedAt=None))
    save()

def deployment_issues():
    p=STATE['plan'];issues=[]
    if not p.get('planned'):issues.append('Generate the activity pages first.')
    if sum(s['minutes'] for s in p['phases'])>p['budget']:issues.append('The stages exceed your time budget.')
    for slot in range(p['groupSize']):
        if not any(slot in t['assignees'] and t['prompt'].strip() for t in p['tasks']):
            issues.append('Assign a question to Learner '+chr(65+slot)+'.')
    return issues

def person_by_id(pid): return next((p for p in STATE['people'] if p['id']==pid and p['active']),None)
def own_responses(pid,preview=False,state=None):
    state=STATE if state is None else state
    return (state['previewResponses' if preview else 'responses']).get(pid,{})
def submitted(pid,preview=False,state=None):
    state=STATE if state is None else state
    stages=[s['id'] for s in state['plan']['phases'] if s['kind']=='individual']
    return bool(stages) and all(own_responses(pid,preview,state).get(s+':submitted') for s in stages)

def learner_view(person,preview=False,phase_id=None,state=None):
    state=STATE if state is None else state
    p=state['plan']; peers=[x for x in state['people'] if x['active'] and x['group']==person['group']]
    if p['interaction']['regroup']=='cross' and p['groupCount']>1:
        peers=[x for x in state['people'] if x['active'] and x['slot']==person['slot']]
    peers=sorted(peers,key=lambda x:(x['group'],x['slot']))
    visible=p['interaction']['visibility']=='always' or (p['interaction']['visibility']=='after_own' and submitted(person['id'],preview,state)) or (p['interaction']['visibility']=='after_group' and all(submitted(x['id'],preview,state) for x in peers))
    board_key=('cross-'+str(person['slot'])) if p['interaction']['regroup']=='cross' and p['groupCount']>1 else str(person['group'])
    ga=state['previewGroupAnswers' if preview else 'groupAnswers'].get(board_key,dict(text='',version=0))
    ref=p['interaction']['feedback']=='teacher' and p['live'].get('reveal') or p['interaction']['feedback']=='after_group' and bool(ga['text']) or p['interaction']['feedback']=='request' and person['id'] in state.get('referenceRequests',[])
    plan=json.loads(json.dumps(p)); plan['interaction']['reference']=p['interaction']['reference'] if ref else ''
    response_map=state['previewResponses' if preview else 'responses']
    index=next((i for i,x in enumerate(peers) if x['id']==person['id']),0)
    review_to=peers[(index+1)%len(peers)]['id']
    if p['structure']=='Role Play':
        own_role=next((t.get('roleId') for t in p['tasks'] if person['slot'] in t['assignees']),None)
        target=next((r['target'] for r in ROLEPLAY['roles'] if r['id']==own_role),None)
        match=next((x for x in peers if x['id']!=person['id'] and any(t.get('roleId')==target and x['slot'] in t['assignees'] for t in p['tasks'])),None)
        if match:review_to=match['id']
    visible_responses={}
    prep_phases=[s['id'] for s in p['phases'] if s['kind']=='individual']
    for x in peers:
        if not (visible or x['id']==person['id']):continue
        records=response_map.get(x['id'],{})
        visible_responses[x['id']]=records if x['id']==person['id'] else {k:v for k,v in records.items() if any(k.startswith(phase+':') for phase in prep_phases)}
    studio_artifacts=learner_artifacts(state,person,peers,visible,preview)
    if p.get('studio',{}).get('exchange')=='questions' and visible:
        own_ready=bool(studio_artifacts.get(person['id'],{}).get('questionSent'))
        if not own_ready:
            visible_responses={person['id']:response_map.get(person['id'],{})}
            studio_artifacts={pid:(r if pid==person['id'] else {k:v for k,v in r.items() if k in ['question','questionSent']}) for pid,r in studio_artifacts.items()}
    shared=group_records(state,person,preview)
    ready=roles_ready(state,person['group'],preview)
    if not ready:shared['critique']={'message':'','misreading':'','change':'','version':0}
    progress=learner_progress(state,person,preview)
    if progress and progress['config'].get('beforeDiscussion') and not progress['answers'].get('initial'):
        shared['opening']={'text':'','version':0}
    return dict(progress=progress,studioGroup=shared,groupRolesReady=ready,studioArtifacts=studio_artifacts,plan=plan,person={k:v for k,v in person.items() if k!='token'},peers=[{k:v for k,v in x.items() if k!='token'} for x in peers],responses=visible_responses,peerVisible=visible,groupAnswer=ga if visible else dict(text='',version=ga['version']),posts=state['previewPosts' if preview else 'posts'].get(board_key,[]) if visible else [],feedback=state['feedback'].get(str(person['group']),''),materials=MATERIALS+state['customMaterials'],rev=state['rev'],planRev=state['planRev'],preview=preview,boardKey=board_key,reviewTo=review_to)

def snapshot_export(view):
    if view['plan'].get('materialId')=='81' and view['plan'].get('structure')=='Role Play':return offline_workspace(ROOT,view)
    p=view['plan']; person=view['person']; mats={m['id']:m for m in view['materials']}
    m=mats.get(p['materialId'],MATERIALS[0]); src=m['image']; fp=ROOT/src.lstrip('/')
    if fp.exists(): src='data:'+mimetypes.guess_type(fp)[0]+';base64,'+base64.b64encode(fp.read_bytes()).decode()
    esc=lambda x:html.escape(str(x),quote=True)
    role=' · '.join(t['title'] for t in p['tasks'] if person['slot'] in t['assignees'])
    visual=('<p>'+esc(m.get('frameLabels',[''])[0])+'</p>' if m.get('frameLabels') else '')+'<img src="'+esc(src)+'" alt="'+esc(m['title'])+'">'
    if len(m.get('images',[]))>1:
        remaining=[]
        for i,path in enumerate(m['images'][1:],2):
            image_file=ROOT/path.lstrip('/')
            image_src='data:'+mimetypes.guess_type(image_file)[0]+';base64,'+base64.b64encode(image_file.read_bytes()).decode() if image_file.exists() else path
            remaining.append(('<p>'+esc(m['frameLabels'][i-1])+'</p>' if m.get('frameLabels') else '')+'<img src="'+esc(image_src)+'" alt="Story frame '+str(i)+'">')
        visual+='<details><summary>Open the remaining story frames</summary>'+''.join(remaining)+'</details>'
    cards=[]
    for phase in p['phases']:
        prompts=p['tasks'] if phase['kind']=='individual' else [dict(id=phase['id'],title=phase['title'],prompt=phase['instruction'],assignees=[person['slot']])]
        fields=[]
        for t in prompts:
            if person['slot'] not in t['assignees']:continue
            if phase['kind']=='discussion' and p['structure']=='Role Play':
                personal=next((x for x in p['tasks'] if person['slot'] in x['assignees']),{})
                peer=next((x for x in view['peers'] if x['id']==view['reviewTo']),{})
                peer_name=peer.get('name') or 'Learner '+chr(65+peer.get('slot',0))
                t={**t,'prompt':personal.get('handoff',phase['instruction']).replace('{peer}',peer_name)+' After the exchange, record one point you checked or changed.'}
            key=phase['id']+':'+t['id']; answer=view['responses'].get(person['id'],{}).get(key,'')
            fields.append('<label>'+esc(t['prompt'])+'<textarea data-key="'+esc(key)+'">'+esc(answer)+'</textarea></label>')
        cards.append('<section><h2>'+esc(phase['title'])+' <small>'+str(phase['minutes'])+' min</small></h2>'+''.join(fields)+'</section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My InfoVis worksheet</title><style>body{font:16px/1.6 system-ui;color:#1d1d1f;background:#f5f5f7;margin:0}main{max-width:1050px;margin:auto;padding:24px}h1{font-size:27px}small,p{color:#86868b}img{width:100%;background:white}section{padding:24px 0;border-bottom:1px solid #e5e5ea}label{display:block;margin:18px 0}textarea{display:block;width:100%;box-sizing:border-box;min-height:150px;margin-top:10px;padding:14px;font:inherit;border:1px solid #dedee3;border-radius:10px}button{padding:10px 18px;font:inherit}</style><main><p>Offline worksheet · '''+esc(person['name'] or 'Learner '+chr(65+person['slot']))+'''</p><h1>'''+esc(p['title'])+'''</h1><p>'''+esc(role)+''' · Group '''+str(person['group']+1)+'''</p><p>Saved snapshot. Edits on this page stay on this device and do not sync with the class.</p><p>'''+esc(m.get('context',''))+'''</p>'''+visual+'''<p>'''+esc(m['author'])+'''</p>'''+''.join(cards)+'''<button onclick="print()">Print / Save PDF</button></main><script>const key='worksheet-'''+person['id']+'''-';document.querySelectorAll('textarea').forEach(e=>{const s=localStorage.getItem(key+e.dataset.key);if(s!==null)e.value=s;e.oninput=()=>localStorage.setItem(key+e.dataset.key,e.value)});</script></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,body,status=200,kind='application/json',extra=None):
        if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode()
        elif isinstance(body,str):body=body.encode()
        self.send_response(status);self.send_header('Content-Type',kind+('; charset=utf-8' if kind.startswith('text/') else ''));self.send_header('Cache-Control','no-store' if kind=='application/json' else 'no-cache');self.send_header('X-Content-Type-Options','nosniff')
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def send_video(self,path):
        size=path.stat().st_size;range_header=self.headers.get('Range');headers={'Accept-Ranges':'bytes'}
        if not range_header:return self.send(path.read_bytes(),kind='video/mp4',extra=headers)
        try:
            unit,value=range_header.split('=',1)
            if unit!='bytes' or ',' in value:raise ValueError()
            left,sep,right=value.partition('-')
            if not sep:raise ValueError()
            if left:
                start=int(left);end=min(size-1,int(right)) if right else size-1
            else:
                suffix=int(right)
                if suffix<=0:raise ValueError()
                start=max(0,size-suffix);end=size-1
            if start<0 or start>=size or end<start:raise ValueError()
        except ValueError:
            return self.send(b'',416,'video/mp4',extra={**headers,'Content-Range':'bytes */'+str(size)})
        with path.open('rb') as stream:stream.seek(start);chunk=stream.read(end-start+1)
        return self.send(chunk,206,'video/mp4',extra={**headers,'Content-Range':f'bytes {start}-{end}/{size}'})
    def args(self):
        u=urlparse(self.path);return u.path,{k:v[0] for k,v in parse_qs(u.query).items()}
    def admin(self,q):return secrets.compare_digest(self.headers.get('X-Admin-Token',q.get('admin','')),STATE['admin'])
    def person(self,q):
        if q.get('preview')=='1' and self.admin(q):return person_by_id(q.get('person')),q.get('inspect')!='1'
        return next((p for p in STATE['people'] if p['active'] and secrets.compare_digest(p['token'],q.get('token',''))),None),False
    def do_HEAD(self):
        """Cloud health checks often use HEAD. Only /api/health is supported."""
        path=urlparse(self.path).path
        if path=='/api/health':
            body=json.dumps(dict(ok=True,service='CollabCanvas',base=BASE,build=BUILD)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        path,q=self.args()
        try:
            with LOCK:
                if path.startswith('/api/test/'):
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    run=test_run(path.rsplit('/',1)[1])
                    return self.send(test_request(run,q.get('person'),q.get('action'),{},learner_view,save_artifact))
                if path=='/api/host/knowledge-report':
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    return self.send(knowledge_report(STATE,q.get('snapshot')))
                if path=='/api/health':return self.send(dict(ok=True,service='CollabCanvas',base=BASE,build=BUILD))
                if path=='/api/host':
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    return self.send(dict(build=BUILD,tutorialSession=bool(STATE.get('tutorialSession')),tutorialReturn=STATE.get('tutorialReturn',''),tutorialPeerExamples=bool(STATE.get('tutorialPeerExamples')),tutorialFollowupExamples=bool(STATE.get('tutorialFollowupExamples')),progress=host_progress(STATE),previewProgress=host_progress(STATE,True),studio=host_studio(STATE),**{k:STATE[k] for k in ['plan','people','requests','feedback','rev','planRev','deployment']},previousActivity=bool(STATE.get('previousActivity')),deploymentIssues=deployment_issues(),materials=MATERIALS+STATE['customMaterials'],roleplay=ROLEPLAY,sampleLoaded=STATE.get('sampleLoaded',False),base=BASE,joinUrl=BASE+'/join?code='+STATE['code'],code=STATE['code']))
                if path=='/api/state' or path=='/api/export':
                    p,preview=self.person(q)
                    if not p:return self.send(dict(error='This learner link is unavailable.'),403)
                    if not preview and not STATE['deployment']['active']:return self.send(dict(error='This activity has not been deployed yet.'),403)
                    view=learner_view(p,preview)
                    view['instructorReadOnly']=q.get('inspect')=='1' and self.admin(q)
                    if path=='/api/export':return self.send(snapshot_export(view),kind='text/html',extra={'Content-Disposition':'attachment; filename="InfoVis-'+chr(65+p['slot'])+'.html"'})
                    return self.send(view)
                if path=='/api/join':
                    if q.get('code')!=STATE['code']:return self.send(dict(error='Unknown class code.'),404)
                    if not STATE['deployment']['active']:return self.send(dict(error='Your teacher has not deployed this activity yet.'),403)
                    places=[]
                    for person in STATE['people']:
                        if not person['active']:continue
                        tasks=[{k:t.get(k,'') for k in ['id','title','prompt','roleId']} for t in STATE['plan']['tasks'] if person['slot'] in t['assignees']]
                        places.append(dict(**{k:person[k] for k in ['id','name','group','slot','claimed']},tasks=tasks))
                    return self.send(dict(title=STATE['plan']['title'],people=places))
                if path=='/api/qr':
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    if not STATE['deployment']['active']:return self.send(dict(error='Deploy the activity before sharing a QR.'),409)
                    target=q.get('target','')
                    if not target.startswith(BASE+'/'):return self.send(dict(error='Use a class link.'),400)
                    qr=qrcode.make(target,image_factory=qrcode.image.svg.SvgPathFillImage,border=4)
                    return self.send(qr.to_string(),kind='image/svg+xml')
            target='host.html' if path=='/' else 'student.html' if path.startswith('/s/') else 'join.html' if path=='/join' else path.lstrip('/')
            fp=(ROOT/target).resolve()
            if ROOT not in fp.parents or not fp.is_file() or not (fp.suffix in ['.html','.css','.js','.png','.jpg','.mp4','.pdf','.svg','.txt']):return self.send('Not found',404,'text/plain')
            if any(x in fp.parts for x in ['vendor','runtime']):return self.send('Not found',404,'text/plain')
            if fp.suffix=='.mp4':return self.send_video(fp)
            self.send(fp.read_bytes(),kind=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
        except (ValueError,KeyError,TypeError) as e:self.send(dict(error=str(e)),400)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):
        path,q=self.args()
        if q.get('inspect')=='1':return self.send(dict(error='Instructor inspection is read-only.'),403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size>20_000_000:return self.send(dict(error='Use a file under 14 MB.'),413)
            body=json.loads(self.rfile.read(size) or b'{}')
            with LOCK:
                if path.startswith('/api/test/'):
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    run=test_run(path.rsplit('/',1)[1])
                    return self.send(test_request(run,q.get('person'),q.get('action'),body,learner_view,save_artifact))
                if path=='/api/join':
                    if body.get('code')!=STATE['code']:return self.send(dict(error='Unknown class code.'),403)
                    if not STATE['deployment']['active']:return self.send(dict(error='Your teacher has not deployed this activity yet.'),403)
                    p=person_by_id(body.get('person'))
                    if not p or p['claimed']:return self.send(dict(error='That place was just claimed. Choose another.'),409)
                    p['name']=str(body.get('name',''))[:60].strip()
                    if not p['name']:return self.send(dict(error='Enter a name.'),400)
                    p['claimed']=True;STATE['rev']+=1;save();return self.send(dict(url='/s/'+p['token']))
                if path.startswith('/api/host/'):
                    if not self.admin(q):return self.send(dict(error='Host access required.'),403)
                    action=path.rsplit('/',1)[1]
                    if action=='tutorial-start':
                        origin=STATE.get('tutorialReturn') if STATE.get('tutorialSession') else (BASE+'/?admin='+STATE['admin']+'&view=flow')
                        result=launch_tutorial(ROOT,origin,bool(body.get('reset')))
                        # Public hosts reload the practice state in this process instead of opening another port.
                        if result.pop('inplace',False):
                            initialize(result['state']);return self.send(result)
                        # A practice classroom that started its own replacement closes once the browser has moved on.
                        if result.pop('retire',False) and STATE.get('tutorialSession'):threading.Timer(12,lambda:os._exit(0)).start()
                        return self.send(result)
                    elif action=='tutorial-examples':
                        result=practice_action(STATE,body);STATE['rev']+=1;save();return self.send(result)
                    elif action=='knowledge-review':
                        result=review_knowledge(STATE,body);STATE['rev']+=1;save();return self.send(dict(ok=True,review=result))
                    elif action=='knowledge-snapshot':
                        result=save_knowledge_snapshot(STATE);STATE['rev']+=1;save();return self.send(dict(ok=True,snapshot=result))
                    elif action=='progress-analyze':
                        if not STATE['plan'].get('planned'):raise ValueError('Generate the activity before suggesting progress rules.')
                        if not supports_progress(STATE['plan']):raise ValueError('Suggestions in this pilot support the voting-story role play.')
                        return self.send(dict(rules=suggested_rules(STATE['plan'],STATE),planRev=STATE['planRev'],source='Seed dictionary; no model call.'))
                    elif action=='rule-action':
                        result,changed=host_action(STATE,body)
                        if changed:STATE['rev']+=1;save()
                        return self.send(result)
                    elif action=='rule-preview':
                        return self.send(rule_preview(STATE,body))
                    elif action=='rule-compile':
                        return self.send(dict(matches=match_text(body.get('text','')),source='Keyword matching against the rule library; no model call.'))
                    elif action=='support-comparison':
                        return self.send(support_comparison(STATE,body))
                    elif action=='progress-support':
                        result=intervene(STATE,body);STATE['rev']+=1;save();return self.send(dict(ok=True,evidence=result))
                    elif action=='adaptive-preview':
                        return self.send(preview_change(STATE,body))
                    elif action=='adaptive-preview-session':
                        return self.send(preview_session(STATE,body))
                    elif action=='adaptive-apply':
                        result=apply_change(STATE,body);STATE['rev']+=1;save();return self.send(dict(ok=True,change=result))
                    elif action=='adaptive-review':
                        result=review_change(STATE,body);STATE['rev']+=1;save();return self.send(dict(ok=True,change=result))
                    elif action=='adaptive-keep':
                        result=review_signal(STATE,body);STATE['rev']+=1;save();return self.send(result)
                    elif action=='progress-draft':
                        draft=create_draft(STATE,body);STATE['rev']+=1;save();return self.send(dict(ok=True,draft=draft))
                    elif action=='progress-draft-preview':
                        return self.send(draft_session(STATE,body.get('id')))
                    elif action=='progress-draft-start':
                        if STATE['plan']['live']['started']:raise ValueError('End the live session before starting a saved draft.')
                        draft=next((d for d in STATE.get('progressDrafts',[]) if d['id']==body.get('id')),None)
                        if not draft:raise ValueError('This draft is unavailable.')
                        archive=DATA.parent/'archives'/(str(time.time_ns())+'.json');archive.parent.mkdir(parents=True,exist_ok=True);archive.write_text(json.dumps(STATE,ensure_ascii=False),encoding='utf8')
                        plan=json.loads(json.dumps(draft['plan']));old_admin,old_rev,old_plan_rev=STATE['admin'],STATE['rev'],STATE['planRev']
                        practice_meta={k:STATE[k] for k in ['tutorialSession','tutorialReturn'] if k in STATE};library=archive_run(STATE,effective_rules(STATE['plan'],STATE))
                        if library:practice_meta.update(ruleLibrary=library)
                        practice_meta['runId']=secrets.token_hex(4);carry_stored(plan,practice_meta);STATE.clear();STATE.update(practice_meta);STATE.update(admin=old_admin,code=secrets.token_hex(3),plan=plan,people=[],responses={},previewResponses={},posts={},previewPosts={},groupAnswers={},previewGroupAnswers={},feedback={},requests=[],rev=old_rev,planRev=old_plan_rev+1,customMaterials=[],deployment=dict(active=False,deployedAt=None),previousActivity=str(archive));reconcile()
                    elif action=='test-start':
                        if not STATE['plan'].get('planned'):raise ValueError('Generate the student interfaces before testing.')
                        return self.send(start_test(STATE))
                    elif action=='test-report':
                        result=finish_test(STATE,body.get('id'),body.get('checks'));STATE['rev']+=1;save();return self.send(dict(ok=True,report=result))
                    elif action=='new':
                        if STATE['plan']['live']['started']:raise ValueError('End the live session before creating a new activity.')
                        archive=DATA.parent/'archives'/(str(time.time_ns())+'.json');archive.parent.mkdir(parents=True,exist_ok=True)
                        archive.write_text(json.dumps(STATE,ensure_ascii=False),encoding='utf8')
                        old_admin,old_rev,old_plan_rev=STATE['admin'],STATE['rev'],STATE['planRev']
                        practice_meta={k:STATE[k] for k in ['tutorialSession','tutorialReturn'] if k in STATE};library=archive_run(STATE,effective_rules(STATE['plan'],STATE))
                        if library:practice_meta.update(ruleLibrary=library)
                        practice_meta['runId']=secrets.token_hex(4);STATE.clear();STATE.update(practice_meta);STATE.update(admin=old_admin,code=secrets.token_hex(3),plan=default_plan(),people=[],responses={},previewResponses={},posts={},previewPosts={},groupAnswers={},previewGroupAnswers={},feedback={},requests=[],rev=old_rev,planRev=old_plan_rev+1,customMaterials=[],deployment=dict(active=False,deployedAt=None),previousActivity=str(archive))
                        reconcile()
                    elif action=='restore':
                        archive=STATE.get('previousActivity')
                        if not archive or STATE['plan'].get('planned'):raise ValueError('Restore is available from an empty canvas.')
                        restored=json.loads(Path(archive).read_text(encoding='utf8'));rev=STATE['rev'];plan_rev=STATE['planRev']
                        restored['admin']=STATE['admin'];restored['rev']=rev;restored['planRev']=plan_rev+1
                        if STATE.get('ruleLibrary'):restored['ruleLibrary']=STATE['ruleLibrary']
                        STATE.clear();STATE.update(restored);STATE.setdefault('deployment',dict(active=False,deployedAt=None))
                    elif action=='deploy':
                        if body.get('planRev')!=STATE['planRev']:return self.send(dict(error='The plan changed. Review it before deploying.'),409)
                        issues=deployment_issues()
                        if issues:return self.send(dict(error=' '.join(issues)),400)
                        STATE['deployment']=dict(active=True,deployedAt=time.time())
                    elif action=='plan':
                        if body.get('planRev')!=STATE['planRev']:return self.send(dict(error='The plan changed in another window. Reload before saving.'),409)
                        p=validate_plan(body['plan']);p['live']=STATE['plan']['live']
                        if p['live']['phaseId'] not in [s['id'] for s in p['phases']]:p['live'].update(phaseId=p['phases'][0]['id'],startedAt=time.time(),remaining=None)
                        STATE['plan']=p;reconcile();STATE['planRev']+=1;remember_custom(STATE,p)
                    elif action=='live':
                        live=STATE['plan']['live'];cmd=body.get('command')
                        if cmd=='start' and not STATE['deployment']['active']:raise ValueError('Deploy the activity before starting the class.')
                        if cmd=='start':live.update(started=True,paused=False,startedAt=time.time(),remaining=None,clock=time.time())
                        elif cmd=='pause':
                            phase=next(x for x in STATE['plan']['phases'] if x['id']==live['phaseId']);live.update(paused=True,remaining=max(0,phase['minutes']*60-(time.time()-(live.get('startedAt') or time.time()))))
                        elif cmd=='resume':
                            phase=next(x for x in STATE['plan']['phases'] if x['id']==live['phaseId']);live.update(paused=False,startedAt=time.time()-(phase['minutes']*60-(live.get('remaining') or 0)),clock=time.time())
                        elif cmd=='stage':
                            if body['phaseId'] not in [x['id'] for x in STATE['plan']['phases']]:raise ValueError('Unknown stage.')
                            live.update(phaseId=body['phaseId'],startedAt=time.time(),remaining=None,clock=time.time())
                        elif cmd=='extend':
                            minutes=float(body.get('minutes',1))
                            if not live.get('started') or not 0<minutes<=15:raise ValueError('Add up to 15 minutes to a stage that is live.')
                            if live.get('paused'):live['remaining']=(live.get('remaining') or 0)+minutes*60
                            else:live['startedAt']=(live.get('startedAt') or time.time())+minutes*60
                        elif cmd=='reveal':live['reveal']=not live.get('reveal')
                        elif cmd=='stop':live.update(started=False,paused=False,startedAt=None)
                        STATE['planRev']+=1
                    elif action=='feedback':STATE['feedback'][str(int(body['group']))]=str(body['text'])[:3000]
                    elif action=='sample':
                        STATE['sampleLoaded']=True
                        seed_rehearsal(STATE)
                        examples={
                            '83':['Red shows a women-dominated occupation. It does not show growth.','A falling line shows a smaller share of middle-class jobs, not necessarily fewer jobs in total.','The groups run from the largest increase to the largest decline.'],
                            '81':['Area shows population rather than geographic size.','Each step removes people outside a smaller voting group.','The outlines help compare the small final electorate with the earlier population.'],
                            '82':['The long time scale puts recent warming beside a much longer history.','Historical notes give reference points while I scroll.','Future scenarios are distinct from the past temperature record.'],
                            '84':['Dot color shows vaccination or infection status in the legend.','The captured panels show fewer infections at higher vaccination rates.','One captured outcome cannot establish how much results vary between repeated runs.'],
                            '85':['Growth pauses at a concentration boundary and later advances.','The labels and time-lapse make the advance visible.','The video shows growth into stronger concentrations, but it does not directly show mutations.']
                        }.get(STATE['plan']['materialId'],['This is an example interpretation of the supplied material.']*3)
                        for p in STATE['people']:
                            if not p['active']:continue
                            d={}
                            for phase in STATE['plan']['phases']:
                                if phase['kind']=='individual':
                                    for t in STATE['plan']['tasks']:
                                        if p['slot'] in t['assignees']:
                                            role_index=next((i for i,r in enumerate(ROLEPLAY['roles']) if r['id']==t.get('roleId')),0)
                                            answer=ROLEPLAY['samples'].get(STATE['plan']['materialId'],examples)[role_index] if STATE['plan']['structure']=='Role Play' and STATE['plan']['materialId'] in ROLEPLAY['samples'] else examples[p['slot']%len(examples)]
                                            d[phase['id']+':'+t['id']]=answer
                                    d[phase['id']+':submitted']=True
                            STATE['previewResponses'][p['id']]=d
                    elif action=='clear-sample':STATE['previewResponses']={};STATE['previewPosts']={};STATE['previewGroupAnswers']={};STATE['sampleLoaded']=False;STATE['previewArtifacts']={};STATE['previewStudioGroups']={}
                    elif action=='studio-propose':
                        return self.send(propose_edit(STATE['plan'],body.get('instruction',''),body.get('target','editor'),body.get('alternative')))
                    elif action=='slides':
                        content=base64.b64decode(body['data'],validate=True)
                        try:lecture=import_slides(ROOT,STATE,content,body.get('name','slides.pdf'))
                        except Exception as error:raise ValueError('Could not read the uploaded PDF. Please choose a valid PDF.') from error
                        STATE['rev']+=1;save();return self.send(dict(ok=True,lecture=lecture))
                    elif action=='upload':
                        content=base64.b64decode(body['data'],validate=True);ext=body['ext'].lower()
                        if ext not in ['png','jpg','jpeg','pdf']:raise ValueError('Upload PNG, JPG or PDF.')
                        fid=secrets.token_hex(6);dest=ROOT/'assets'/('upload-'+fid+'.'+ext);dest.write_bytes(content)
                        m=dict(id=fid,slide='Upload',title=str(body.get('name','My material'))[:120],author='Instructor material',image='/assets/'+dest.name,source='',context='Use the material supplied by your instructor.',kind='pdf' if ext=='pdf' else 'image')
                        STATE['customMaterials'].append(m)
                    elif action=='swap':
                        a=person_by_id(body.get('a'));b=person_by_id(body.get('b'))
                        if not a or not b:raise ValueError('Choose two active learners.')
                        a['group'],b['group']=b['group'],a['group'];a['slot'],b['slot']=b['slot'],a['slot'];STATE['planRev']+=1
                    else:return self.send(dict(error='Unknown action.'),404)
                    STATE['rev']+=1;save();return self.send(dict(ok=True,rev=STATE['rev'],planRev=STATE['planRev']))
                person,preview=self.person(q)
                if not person:return self.send(dict(error='Learner access required.'),403)
                if not preview and not STATE['deployment']['active']:return self.send(dict(error='This activity has not been deployed yet.'),403)
                view=learner_view(person,preview);p=STATE['plan'];phase=next((x for x in p['phases'] if x['id']==body.get('phaseId')),None)
                if path=='/api/adaptive/response':
                    result=save_adaptive_response(STATE,person,body,preview);touch(STATE,person,'shared' if body.get('shared') else 'own',preview);STATE['rev']+=1;save();return self.send(dict(ok=True,response=result))
                elif path=='/api/progress/answer':
                    if not phase:raise ValueError('Choose a stage from this activity.')
                    if not preview and p['interaction']['mode']=='sync' and phase['id']!=p['live']['phaseId']:return self.send(dict(error='The class has moved to another stage.'),409)
                    answer=save_answer(STATE,person,body,preview);touch(STATE,person,'own',preview);STATE['rev']+=1;save();return self.send(dict(ok=True,answer=answer))
                elif path=='/api/studio/group':
                    if not phase:raise ValueError('Choose a stage from this activity.')
                    if not preview and p['interaction']['mode']=='sync' and phase['id']!=p['live']['phaseId']:return self.send(dict(error='The class has moved to another stage.'),409)
                    record=save_group(STATE,person,body,preview);STATE['rev']+=1;save();return self.send(dict(ok=True,record=record))
                elif path=='/api/studio/save':
                    if not phase:raise ValueError('Choose a stage from this activity.')
                    if not preview and p['interaction']['mode']=='sync' and phase['id']!=p['live']['phaseId']:return self.send(dict(error='The class has moved to another stage.'),409)
                    record=save_artifact(STATE,person,body,preview);touch(STATE,person,'own',preview)
                    STATE['rev']+=1;save();return self.send(dict(ok=True,artifact=record))
                elif path=='/api/response':
                    if not phase:raise ValueError('That stage was removed. Your previous answers are retained.')
                    if not preview and p['interaction']['mode']=='sync' and phase['id']!=p['live']['phaseId']:return self.send(dict(error='The class has moved to another stage.'),409)
                    d=STATE['previewResponses' if preview else 'responses'].setdefault(person['id'],{})
                    for key,value in body.get('answers',{}).items():
                        allowed=[t['id'] for t in p['tasks'] if person['slot'] in t['assignees']] if phase['kind']=='individual' else [phase['id']]
                        if key not in allowed:raise ValueError('This question is not assigned to you.')
                        d[phase['id']+':'+key]=str(value)[:8000]
                    touch(STATE,person,'own',preview)
                    if body.get('submitted'):record_submit(STATE,person,phase['id'],preview);d[phase['id']+':submitted']=True
                elif path=='/api/collab':
                    result=learner_action(STATE,person,body,preview)
                    if result.pop('quiet',False):return self.send(result)
                    STATE['rev']+=1;save();return self.send(result)
                elif path=='/api/discussion':
                    if not view['peerVisible']:return self.send(dict(error='Complete the sharing condition first.'),403)
                    if not preview and p['interaction']['mode']=='sync' and next(x for x in p['phases'] if x['id']==p['live']['phaseId'])['kind']!='discussion':return self.send(dict(error='Discussion is not open yet.'),403)
                    key=view['boardKey'];text=str(body.get('text','')).strip()[:8000]
                    if body.get('kind')=='post':
                        if text:STATE['previewPosts' if preview else 'posts'].setdefault(key,[]).append(dict(id=secrets.token_hex(5),person=person['id'],to=view['reviewTo'] if p['structure'] in ['Peer Editing','Role Play'] else None,text=text,time=time.time()))
                    else:
                        store=STATE['previewGroupAnswers' if preview else 'groupAnswers'];old=store.get(key,dict(text='',version=0))
                        if body.get('version')!=old['version']:return self.send(dict(error='A teammate saved a newer response. Copy your draft, then reload the shared response.'),409)
                        store[key]=dict(text=text,version=old['version']+1,person=person['id'])
                elif path=='/api/help':
                    request_kind=body.get('requestKind','visit')
                    if request_kind not in ['visit','difficulty','participation','unheard']:raise ValueError('Choose an available support request.')
                    STATE['requests'].append(dict(id=secrets.token_hex(4),person=person['id'],group=person['group'],requestKind=request_kind,text=str(body.get('text','Please join our discussion.'))[:500],time=time.time(),preview=preview))
                elif path=='/api/reference':
                    if p['interaction']['feedback']!='request':return self.send(dict(error='The instructor controls this reference.'),403)
                    STATE.setdefault('referenceRequests',[]).append(person['id'])
                else:return self.send(dict(error='Unknown action.'),404)
                STATE['rev']+=1;save();return self.send(dict(ok=True,rev=STATE['rev']))
        except (ValueError,KeyError,TypeError,StopIteration) as e:self.send(dict(error=str(e) or 'Invalid request.'),400)
        except (BrokenPipeError,ConnectionResetError):pass

def lan_ip():
    if sys.platform=='darwin':
        for interface in ['en0','en1','en2']:
            try:
                ip=subprocess.check_output(['/usr/sbin/ipconfig','getifaddr',interface],stderr=subprocess.DEVNULL,text=True,timeout=2).strip()
                if ip and not ip.startswith('169.254.'):return ip
            except (OSError,subprocess.SubprocessError):pass
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:s.connect(('8.8.8.8',80));return s.getsockname()[0]
    except OSError:return '127.0.0.1'
    finally:s.close()

def public_base(port):
    """Cloud hosts set PUBLIC_BASE / RENDER_EXTERNAL_URL. Local runs keep the LAN address for QR join."""
    for key in ('PUBLIC_BASE','RENDER_EXTERNAL_URL','COLLABCANVAS_BASE'):
        value=os.environ.get(key,'').strip().rstrip('/')
        if value:return value
    return 'http://'+lan_ip()+':'+str(port)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=int(os.environ.get('PORT',8931)));ap.add_argument('--state',default=str(ROOT/'runtime'/'state.json'));ap.add_argument('--open',action='store_true');args=ap.parse_args();PORT=args.port
    initialize(args.state);BASE=public_base(PORT)
    server=ThreadingHTTPServer(('0.0.0.0',PORT),Handler);host=BASE+'/?admin='+STATE['admin']
    if os.environ.get('COLLABCANVAS_START_VIEW')=='progress':host+='&view=flow&demo=progress'
    if DATA.resolve()==(ROOT/'runtime'/'state.json').resolve():
        (ROOT/'runtime').mkdir(exist_ok=True);(ROOT/'runtime'/'launch.json').write_text(json.dumps(dict(host=host,join=BASE+'/join?code='+STATE['code'],base=BASE)))
    print(json.dumps(dict(host=host,join=BASE+'/join?code='+STATE['code'],base=BASE)),flush=True)
    if args.open:webbrowser.open(host)
    server.serve_forever()
