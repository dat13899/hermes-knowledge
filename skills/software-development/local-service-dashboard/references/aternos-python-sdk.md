# python-aternos SDK reference

## Install
```bash
uv pip install python-aternos --no-deps
uv pip install requests cloudscraper  # deps nó cần
```

## Auth + fetch
```python
from python_aternos import Client

at = Client()
at.login('username', 'password')
servers = at.account.list_servers()
s = servers[0]
s.fetch()  # required before accessing most fields
```

## Status enum
```python
from python_aternos import Status
# Status.off = 0, .on = 1, .starting = 2, .shutdown = 3
# .loading = 6, .error = 7, .preparing = 10
```
`waiting` / `preparing` = in queue, needs confirm.

## Properties (after fetch)

| Property | Type | Notes |
|---|---|---|
| `s.status` | str | `'online'`, `'offline'`, `'starting'`, `'loading'`, `'waiting'`, `'preparing'`, `'stopped'` |
| `s.status_num` | Status | enum `.value` → int |
| `s.players_count` | int | Players online |
| `s.players_list` | list[str] | Player names |
| `s.slots` | int | Max players |
| `s.software` | str | Server type (`Bedrock`, `Vanilla`, `Paper`...) |
| `s.version` | str | Version string |
| `s.motd` | str | MOTD (§ color codes) |
| `s.ram` | int | RAM in MB |
| `s.address` | str | `ip:port` |
| `s.domain` | str | Hostname |
| `s.port` | int | Port number |
| `s.servid` | str | Unique server ID |
| `s.subdomain` | str | Subdomain part |
| `s.is_bedrock` | bool | Bedrock vs Java |
| `s.is_java` | bool | |
| `s.edition` | int | 1=Bedrock, 0=Java |
| `s.countdown` | int | -1 if no countdown |
| `s.css_class` | str | CSS class hint |
| `s._info` | dict | Raw response — keys: `ip`, `port`, `slots`, `software`, `version`, `ram`, `label`, `inQueue`, `countdown` |

## Actions

```python
s.start()        # Start server (async)
s.stop()         # Stop server (async)
s.restart()      # Restart server
s.confirm()      # Confirm when in queue (waiting/preparing)
s.cancel()       # Cancel pending operation
s.fetch()        # Refresh status from Aternos
```

## Auto-confirm queue flow

```python
s.start()
# After start, server may enter queue (status 'waiting'/'preparing')
for _ in range(6):
    time.sleep(5)
    s.fetch()
    if s.status in ('waiting', 'preparing') or s._info.get('inQueue'):
        s.confirm()
        break
    if s.status == 'online':
        break
```

## Properties (no fetch needed — from list_servers)

```python
s.servid          # Always available
s.domain          # After login
s.port            # After login
s.status_num      # After login (may be stale)
```

## Set MOTD / Subdomain

```python
s.set_motd("§aWelcome §6to §bmy §dserver!")
s.set_subdomain("mysubdomain")
```

## Players method

```python
s.players(["player1", "player2"])  # returns player info dict
```

## File Manager

```python
fm = s.files()
fm.list_dir('/')            # list files at path
fm.list_dir('world')        # list world files
fm.get_file('world/level.dat')  # file metadata
fm.dl_file('world/level.dat')   # download as bytes
fm.dl_world('world')            # download world as zip bytes
```

## Config

```python
cfg = s.config()
# Available methods:
cfg.get_java()            # Java settings (not for bedrock)
cfg.get_server_props()    # server.properties
cfg.get_world_props()     # world properties
cfg.get_timezone()
cfg.set_server_prop(key, val)
cfg.set_server_props({key: val, ...})
cfg.set_world_prop(key, val)
cfg.set_world_props({key: val, ...})
cfg.set_java(flags)
cfg.set_timezone(tz)
```

## WebSocket (real-time console)

```python
s.wss  # WebSocket connection for live log output
```

## Notes / Pitfalls

- **Address from _info**: `s.address` works after `fetch()`, falls back to `s._info['ip']` + `s._info['port']`
- **Async**: start/stop/restart are signals — server takes 1-2 min to actually respond
- **Queue**: free Aternos servers may queue (status `waiting`/`preparing`) — need `s.confirm()`
- **lxml bug**: uv install may fail on lxml — use `--no-deps` + install requests/cloudscraper separate
- **players()**: requires a list arg (even empty) — weird API design
- **get_server_props() returns {} for Bedrock**: Bedrock edition uses different config system. `set_server_prop()` returns 400 on Bedrock. Java-only feature.
- **Servers turn off automatically**: Aternos free turns off after ~1h no players. Restart needed.
- **GeyserMC bridge**: only option to join Bedrock players to a Java server. Requires plugins — not available on Aternos free tier.
- **Java vs Bedrock separate games**: Java edition cannot run on mobile (no app). Bedrock = phone, tablet, console, Win10/11. Cannot cross-play without GeyserMC bridge.
