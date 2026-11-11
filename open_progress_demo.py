#!/usr/bin/env python3
"""An independent, simulated classroom. Never reads or replaces the main class."""
from pathlib import Path
import argparse,json,os,secrets,socket,sys,urllib.request,webbrowser
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8942);ap.add_argument('--no-open',action='store_true');args=ap.parse_args()
state_path=ROOT/'runtime'/'progress-demo-state.json';state_path.parent.mkdir(exist_ok=True)
if not state_path.exists():
 seed=json.loads((ROOT/'progress_demo_seed.json').read_text());seed.update(admin=secrets.token_urlsafe(24),code=secrets.token_hex(3),deployment=dict(active=True,deployedAt=None),customMaterials=[],lectures=[],previewResponses={},previewArtifacts={},previewPosts={},previewGroupAnswers={},previewStudioGroups={})
 for person in seed['people']:person['token']=secrets.token_urlsafe(18)
 state_path.write_text(json.dumps(seed,ensure_ascii=False),encoding='utf8')
else:seed=json.loads(state_path.read_text())
for port in range(args.port,args.port+10):
 host=f'http://127.0.0.1:{port}/?admin='+seed['admin']+'&view=flow&demo=progress'
 try:
  request=urllib.request.Request(f'http://127.0.0.1:{port}/api/host',headers={'X-Admin-Token':seed['admin']})
  with urllib.request.urlopen(request,timeout=.6) as r:found=json.load(r)
  if found.get('plan'):
   if not args.no_open:webbrowser.open(host)
   print(host,flush=True);raise SystemExit(0)
 except (OSError,ValueError):pass
 sock=socket.socket()
 try:sock.bind(('127.0.0.1',port))
 except OSError:sock.close();continue
 sock.close()
 if not args.no_open:
  # server.py opens the actual host URL after binding.
  extra=['--open']
 else:extra=[]
 os.environ['COLLABCANVAS_START_VIEW']='progress'
 os.execv(sys.executable,[sys.executable,str(ROOT/'server.py'),'--port',str(port),'--state',str(state_path),*extra])
raise SystemExit('No free demo port. Close an older progress demo and try again.')
