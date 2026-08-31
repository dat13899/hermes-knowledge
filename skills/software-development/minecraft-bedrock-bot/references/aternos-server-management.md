# Aternos Server Management (python-aternos)

Control Aternos Minecraft server (start/stop/status) via Python from Windows.

## Setup

```bash
uv pip install python-aternos
```

## API Pattern

```python
from python_aternos import Client

at = Client()
at.login('username', 'password')
# OR: at.login_hashed('username', 'md5hash')

# List servers
servers = at.account.list_servers()
s = servers[0]

# MUST call fetch() before accessing most properties
s.fetch()

# Status
print(s.status)          # 'online' | 'offline' | etc.
print(s.status_num)      # Status enum — works after fetch
print(s.players_count)   # current players
print(s.players_list)    # list of online player names
print(s.slots)           # max slots
print(s.software)        # e.g. 'Bedrock'
print(s.version)         # e.g. '1.26.30.5'
print(s.address)         # full address (may crash if domain fails)
print(s.motd)            # server MOTD
print(s.ram)             # allocated MB
print(s.servid)          # server ID (for API calls)

# Start/Stop
s.start()                # starts server (handles queue)
s.stop()                 # stops server
s.restart()              # restart
s.cancel()               # cancel pending start
s.confirm()              # confirm start from queue
```

## _info dict (raw response)

After `fetch()`, all data lives in `s._info`:

```python
for k, v in s._info.items():
    print(f'{k}: {v}')
```

Key fields:
| Key | Meaning |
|-----|---------|
| `status` | 1=online, 2=offline, 0=starting/loading |
| `players` | online count |
| `playerlist` | list of player names |
| `slots` | max players |
| `host` / `port` | connection address parts |
| `ip` | subdomain (e.g. `dat1389.aternos.me`) |
| `displayAddress` | user-facing address |
| `software` | e.g. `Bedrock` |
| `version` | MC version string |
| `ram` | current RAM MB |
| `maxram` | max RAM MB |
| `motd` | server description |
| `bedrock` | bool, is bedrock edition |
| `onlineMode` | bool |
| `region` | server region |
| `queue` | queue position (None if not queued) |
| `countdown` | countdown seconds (None if not counting) |

## Pitfalls

- **`domain` property crashes**: `s.domain` / `s.address` access `_info['ip']` which may not exist after `list_servers()`. Always call `s.fetch()` first.
- **`_info` empty before fetch**: After `list_servers()`, `_info` is `[]`. Properties like `status_num`, `domain`, `address` crash with `KeyError`. Call `fetch()` immediately.
- **Credentials in plaintext**: `Client.login()` takes plain password. For production, use `login_hashed(username, md5hash)`. Generate MD5 in Python:
  ```python
  import hashlib
  md5 = hashlib.md5(password.encode()).hexdigest()
  at.login_hashed('username', md5)
  ```
- **Cloudflare protection**: Aternos uses Cloudflare. `python-aternos` handles it internally via its own session management. If login fails with captcha/Cloudflare, try:
  ```python
  at = Client()
  at.login('username', 'password')
  at.save_session()  # saves session for reuse
  ```
  Then on next run:
  ```python
  at = Client()
  at.restore_session()  # uses saved session, avoids login
  ```
- **Start queue**: Aternos may queue server starts during high load. `s.start()` still works but will queue. Check `s._info.get('queue')` after start.
- **2FA**: If 2FA is enabled, use `at.login(username, password, code=123456)` with the 2FA code.

## Quick status check script

```python
from python_aternos import Client
import json

at = Client()
at.login('username', 'password')
servers = at.account.list_servers()
s = servers[0]
s.fetch()

print(json.dumps({
    'status': s.status,
    'players': s.players_count,
    'max_players': s.slots,
    'software': f'{s.software} {s.version}',
    'motd': s.motd,
    'ram_mb': s.ram,
}, indent=2))
```
