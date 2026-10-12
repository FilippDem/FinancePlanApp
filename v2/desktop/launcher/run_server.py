"""Runs the Financial Planner server in the background (started by start.ps1 with pythonw, so no window).

Everything the server prints goes to logs/server.log next to this folder.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'app')
LOGS = os.path.join(ROOT, 'logs')
os.makedirs(LOGS, exist_ok=True)

log = open(os.path.join(LOGS, 'server.log'), 'a', buffering=1, encoding='utf-8')
sys.stdout = sys.stderr = log          # pythonw has no console; keep the output somewhere readable

os.chdir(APP)
sys.path.insert(0, APP)
os.environ.setdefault('DATA_DIR', os.path.join(ROOT, 'data'))
os.environ.setdefault('ALLOW_DEV_LOGIN', '1')   # simple email sign-in on this computer
os.environ['PYTHONUNBUFFERED'] = '1'

with open(os.path.join(ROOT, '.server.pid'), 'w') as f:   # the real server process, for "Stop Financial Planner"
    f.write(str(os.getpid()))

import uvicorn  # noqa: E402

uvicorn.run('server.app:app', host='127.0.0.1', port=int(os.environ.get('FP_PORT', '8502')), log_level='info')
