#!/usr/bin/env python3
"""Aternos CLI — called by dashboard server.js or cron"""
import sys, json, os, time

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'aternos_config.json')

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

from python_aternos import Client, Status

def _get():
    at = Client()
    at.login(cfg['user'], cfg['pass'])
    servers = at.account.list_servers()
    return at, servers[0]

def _build_info(s):
    info = s._info
    return {
        'ok': True,
        'status': s.status,
        'status_num': s.status_num.value if hasattr(s.status_num, 'value') else int(getattr(s.status_num, 'value', -1)),
        'players': s.players_count,
        'players_list': s.players_list,
        'slots': info.get('slots', 0),
        'software': f'{info.get("software","?")} {info.get("version","")}'.strip(),
        'address': f'{info.get("ip","?")}:{info.get("port","?")}',
        'motd': s.motd,
        'ram': info.get('ram', 0),
        'label': info.get('label', s.status),
        'queue': info.get('inQueue', False) or s.status in ('waiting', 'preparing'),
        'countdown': info.get('countdown', -1),
    }

def cmd_status():
    try:
        at, s = _get()
        s.fetch()
        return _build_info(s)
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def cmd_start():
    try:
        at, s = _get()
        s.fetch()
        cur = s.status
        if cur == 'online':
            return {'ok': True, 'message': 'already online'}
        s.start()
        # Poll briefly to catch queue state and auto-confirm
        for _ in range(6):  # ~30s
            time.sleep(5)
            try:
                s.fetch()
                if s.status == 'online':
                    return _build_info(s) | {'message': 'online'}
                # Queue — needs confirm
                wait_states = ('waiting', 'preparing')
                if s.status in wait_states or s._info.get('inQueue'):
                    s.confirm()
                    return _build_info(s) | {'message': 'started + confirmed', 'confirmed': True}
            except:
                pass
        # After poll — return current state
        s.fetch()
        return _build_info(s) | {'message': f'start signal sent (current: {s.status})'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def cmd_confirm():
    try:
        at, s = _get()
        s.fetch()
        before = s.status
        if s.status not in ('waiting', 'preparing') and not s._info.get('inQueue'):
            return {'ok': True, 'message': f'no queue needed (status: {before})'}
        s.confirm()
        return {'ok': True, 'message': 'confirmed', 'before': before}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def cmd_stop():
    try:
        at, s = _get()
        s.stop()
        return {'ok': True, 'message': 'stop signal sent'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def cmd_restart():
    try:
        at, s = _get()
        s.restart()
        return {'ok': True, 'message': 'restart signal sent'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

CMDS = {'status': cmd_status, 'start': cmd_start, 'confirm': cmd_confirm, 'stop': cmd_stop, 'restart': cmd_restart}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(json.dumps({'ok': False, 'error': 'Usage: aternos.py status|start|confirm|stop|restart'}))
        sys.exit(1)
    print(json.dumps(CMDS[sys.argv[1]]()))
