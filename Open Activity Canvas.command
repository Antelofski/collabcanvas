#!/bin/zsh
cd "$(dirname "$0")"
python3 - <<'PY'
import json, urllib.request, webbrowser, subprocess, os, signal, time
from pathlib import Path
from build_info import BUILD
p=Path('runtime/launch.json')
try:
    data=json.loads(p.read_text())
    base=data['host'].split('/?')[0]
    with urllib.request.urlopen(base+'/api/health',timeout=1) as r:
        health=json.load(r)
    if health.get('service') not in ['CollabCanvas','Activity Canvas']:
        raise ValueError('other service')
    if health.get('build') and health.get('build')!=BUILD:
        # Stale local process: stop it and start this copy.
        try:
            with urllib.request.urlopen(base+'/api/host',timeout=1) as r: pass
        except Exception:
            pass
        for line in subprocess.check_output(['lsof','-nP','-iTCP','-sTCP:LISTEN'],text=True,stderr=subprocess.DEVNULL).splitlines():
            if f":{base.rsplit(':',1)[-1]} " in line or line.endswith(':'+base.rsplit(':',1)[-1]):
                pid=int(line.split()[1]); os.kill(pid, signal.SIGTERM); time.sleep(0.4); break
        raise SystemExit(3)
    webbrowser.open(data['host']); raise SystemExit(0)
except (OSError,ValueError,KeyError,subprocess.SubprocessError):
    raise SystemExit(3)
PY
if [[ $? -eq 0 ]]; then
  exit 0
fi
python3 server.py --open
