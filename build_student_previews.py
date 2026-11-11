"""Build self-contained four-role previews; all sample work is explicitly offline."""
from pathlib import Path
from copy import deepcopy
import json,tempfile
import server
from model import tasks_for,default_plan
from collab_workflow import group_first_plan
from studio_backend import seed_rehearsal,offline_workspace
ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as temp:
    server.initialize(Path(temp)/'state.json')
    p=default_plan();p.update(planned=True,materialId='81',structure='Role Play',groupSize=4,groupCount=1,budget=18,title='Who gets a vote? · Editorial meeting')
    p['tasks']=tasks_for('81','Role Play',4);p=group_first_plan(p)
    server.STATE['plan']=p;server.reconcile();seed_rehearsal(server.STATE)
    pages=[]
    for person in server.STATE['people']:
        if not person['active']:continue
        server.STATE['previewResponses'][person['id']]={'discuss:submitted':True}
    for person in sorted([p for p in server.STATE['people'] if p['active']],key=lambda p:p['slot']):
        role=next(t for t in p['tasks'] if person['slot'] in t['assignees'])
        view=server.learner_view(person,True);view['preview']=False
        document=offline_workspace(ROOT,view)
        (ROOT/f"Example_Learner_{chr(65+person['slot'])}.html").write_text(document)
        pages.append(dict(title=role['title'],html=document))
    encoded=json.dumps(pages,ensure_ascii=False).replace('<','\\u003c')
    shell='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CollabCanvas · Four student interfaces</title><style>html,body{margin:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f6f9;color:#2d3441}header{min-height:74px;display:flex;align-items:center;gap:20px;padding:12px 24px;background:white;border-bottom:1px solid #e2e6ed;box-sizing:border-box}h1{font-size:17px;letter-spacing:-.4px;margin:0}small{display:block;font-size:11px;color:#7d8797;margin-top:5px}nav{display:flex;gap:5px;margin-left:auto;flex-wrap:wrap}button{font:12px system-ui;border:0;border-radius:7px;background:transparent;color:#657184;padding:10px 16px;cursor:pointer}button.on{background:#eaf1fc;color:#416ba9}iframe{border:0;width:100%;height:calc(100% - 76px)}@media(max-width:800px){header{display:block;padding:10px}nav{margin:8px 0 0}button{padding:8px}iframe{height:calc(100% - 112px)}}</style><header><div><h1>CollabCanvas · Student interfaces</h1><small>Offline sample work · discuss together → work by role → write together</small></div><nav id="roles"></nav></header><iframe id="workspace" title="Selected student interface"></iframe><script>const pages=PAYLOAD;function openRole(i){document.querySelector('#workspace').srcdoc=pages[i].html;document.querySelectorAll('nav button').forEach((b,n)=>b.classList.toggle('on',n===i))}document.querySelector('#roles').innerHTML=pages.map((p,i)=>'<button data-role="'+i+'">'+p.title+'</button>').join('');document.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>openRole(+b.dataset.role));openRole(0);</script></html>'''.replace('PAYLOAD',encoded)
    (ROOT/'Student_Versions.html').write_text(shell)
    print('Built',len(pages),'offline role interfaces')
