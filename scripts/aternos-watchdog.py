#!/usr/bin/env python3
"""Aternos watchdog — silent when online, auto-start + confirm if offline."""
import sys, json, os, subprocess

DIR = os.path.dirname(__file__)
PY = os.path.join(DIR, 'aternos.py')

def run(action):
    r = subprocess.run(['python', PY, action], capture_output=True, text=True, timeout=120)
    return json.loads(r.stdout)

try:
    data = run('status')
except Exception as e:
    print(f'⚠️ Aternos watchdog error: {e}')
    sys.exit(0)

if not data.get('ok'):
    print(f'⚠️ Aternos status check failed: {data.get("error")}')
    sys.exit(0)

status = data['status']
queue = data.get('queue', False)

# If online or starting/loading — silent
if status == 'online':
    sys.exit(0)
if status in ('starting', 'loading') and not queue:
    sys.exit(0)

# If in queue (waiting/preparing) — confirm
if queue or status in ('waiting', 'preparing'):
    result = run('confirm')
    if result.get('ok'):
        print(f'⛏️ Aternos in queue — confirmed ✓')
    else:
        print(f'❌ Confirm failed: {result.get("error")}')
    sys.exit(0)

# Offline — start (start handles auto-confirm internally)
print(f'⛏️ Aternos {status}. Starting...')
result = run('start')
if result.get('ok'):
    msg = result.get('message', '')
    if result.get('confirmed'):
        print(f'✅ Server started + queue confirmed ✓')
    else:
        print(f'✅ {msg}')
else:
    print(f'❌ Start failed: {result.get("error")}')
