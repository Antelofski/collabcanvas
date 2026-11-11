#!/usr/bin/env python3
"""Launch or resume an independent hands-on practice session."""
import argparse,json,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path
from tutorial_backend import launch_tutorial
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--no-open',action='store_true');ap.add_argument('--new',action='store_true');ap.add_argument('--resume',action='store_true');args=ap.parse_args()
main=ROOT/'runtime'/'state.json'
if not main.exists():
 import server
 server.initialize(main)
state=json.loads(main.read_text());host='http://127.0.0.1:8931/?admin='+state['admin']+'&view=flow'
def main_ready():
 try:
  request=urllib.request.Request('http://127.0.0.1:8931/api/host',headers={'X-Admin-Token':state['admin']})
  with urllib.request.urlopen(request,timeout=.5) as response:return bool(json.load(response).get('plan'))
 except (OSError,ValueError):return False
if not main_ready():
 log=(ROOT/'runtime'/'tutorial-main.log').open('ab');subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port','8931','--state',str(main)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close()
 for _ in range(60):
  if main_ready():break
  time.sleep(.05)
 else:raise SystemExit('Open the main CollabCanvas launcher first, then try Tutorial.')
result=launch_tutorial(ROOT,host,reset=args.new or not args.resume)
print(result['url'],flush=True)
if not args.no_open:webbrowser.open(result['url'])
