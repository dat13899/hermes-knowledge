---
name: minecraft-bedrock-bot
description: "Build autonomous Minecraft Bedrock Edition bots using the bedrock-protocol library. Covers setup, packet-level movement/interaction/inventory, version monkey-patching, and connection lifecycle."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
---

# Minecraft Bedrock Bot

Build bots for Minecraft Bedrock Edition using [bedrock-protocol](https://github.com/PrismarineJS/bedrock-protocol) — a low-level Node.js library that speaks the MC Bedrock protocol directly (no Java edition, no bot API layer).

## When to Use

- **AFK keep-alive bots** — stay connected, swing arm periodically
- **Autonomous player bots** — walk, jump, break/place blocks, interact
- **Chat bots** — read chat, respond, run commands
- **Farm bots** — harvest, replant, collect drops (needs inventory handling)
- **PvP bots** — target entities, attack, dodge (needs movement + entity tracking)
- **Server management** — automated moderation, world backup triggers

## Project Setup

```bash
mkdir my-bot && cd my-bot
npm init -y
npm install bedrock-protocol minecraft-data tsx
```

### package.json

```json
{
  "private": true,
  "type": "module",
  "scripts": { "start": "tsx ./src/index.ts" },
  "dependencies": {
    "bedrock-protocol": "^3.57.0",
    "minecraft-data": "^3.111.0",
    "tsx": "^4.7.1"
  },
  "devDependencies": {
    "@types/node": "^25.5.0"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "strict": false,
    "target": "ESNext",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "noEmit": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "types": []
  },
  "include": ["src/**/*.ts"]
}
```

## config.json

```json
{
  "client": {
    "host": "your-server.com",
    "port": 19132,
    "username": "MyBot",
    "version": "1.21.50"
  },
  "bot": {
    "offline": true
  }
}
```

Set `offline: true` for servers that don't require Xbox Live auth (most Aternos / LAN servers with `online-mode=false`).

## Version Monkey-Patching

Bedrock-protocol ships with support for official MC versions only. Unofficial/patch versions (e.g., `1.26.30.5`) require runtime monkey-patching:

```ts
import { Versions } from 'bedrock-protocol/src/options.js'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)

// Patch minecraft-data: alias custom version to closest supported version
const mcData = require('minecraft-data/data.js')
mcData.bedrock['1.26.30.5'] = mcData.bedrock['1.26.30']

const mcIndex = require('minecraft-data')
mcIndex.versions.bedrock.unshift({
  version: 1001,
  minecraftVersion: '1.26.30.5',
  majorVersion: '1.26.30',
  releaseType: 'release',
})
mcIndex.versionsByMinecraftVersion.bedrock['1.26.30.5'] = {
  version: 1001, minecraftVersion: '1.26.30.5',
  majorVersion: '1.26.30', releaseType: 'release',
  dataVersion: 0,
}

// Patch bedrock-protocol options
Versions['1.26.30.5'] = 1001
```

Find the version number (1001 here) and the base version (`1.26.30`) from the server's ping response or protocol docs.

## Ping Server to Verify Version

Before connecting, ping the server to check its real version and protocol:

```ts
import { ping } from 'bedrock-protocol'

ping({ host, port })
  .then(r => console.log({ version: r.version, protocol: r.protocol }))
  .catch(e => console.error('Ping failed:', e.message))
```

Compare the returned `version` (e.g. `1.26.30`) against your config. If they differ, adjust the monkey-patch to alias your config version to the server's real version.

## Connection Lifecycle

```ts
import { createClient } from 'bedrock-protocol'

const client = createClient({
  host, port, username,
  offline: true,
  version: '1.26.30.5',
  skipPing: true,  // connect with fixed version, skip auto-detect
})

client.on('join',  () => console.log('Joined server'))
client.on('spawn', () => console.log('Spawned — ready to act'))
client.on('error', (e) => console.error('Error:', e.message))
client.on('close', () => console.log('Connection closed'))
```

**Event order:** `join` → `spawn` → (player is in world). Act only after `spawn`.

**skipPing strategy:** Use `skipPing: true` + monkey-patched version for reliability with patch versions (e.g. `1.26.30.5`). Without `skipPing`, the library pings the server and auto-selects the version — this also works but can expose serialization ordering issues. Prefer `skipPing: true` when you control the version alias.

## Available Packets (1.26.30)

### Movement

| Packet | Purpose | Key Fields |
|--------|---------|------------|
| `move_player` | Update position/rotation | `runtime_entity_id`, `position: vec3f`, `pitch`, `yaw`, `head_yaw`, `mode`, `on_ground` |
| `player_input` | Movement input flags | `motion_x`, `motion_z`, `jumping`, `sneaking` |
| `player_auth_input` | Server-authoritative movement (1.19.30+) | `position`, `pitch`, `yaw`, `head_yaw`, `move_vector`, `input_data`, `input_mode`, `play_mode`, `tick` |

### Actions

| Packet | Purpose | Key Fields |
|--------|---------|------------|
| `animate` | Swing arm, critical hit | `action_id` (1=swing), `runtime_entity_id` |
| `player_action` | Break block, drop, jump, sprint, sneak | `runtime_entity_id`, `action` (enum), `position`, `face` |
| `interact` | Leave vehicle, mouse-over entity, open inventory | `action_id` (3=leave_vehicle, 4=mouse_over, 6=open_inventory), `target_entity_id` |

### Chat & Commands

**Sending chat — use `command_request`, NOT `text` packet**

The `text` packet with `type: 'chat'` causes most Bedrock servers (Aternos, dedicated) to kick the bot immediately. Always use `command_request` with `/say`:

```ts
// ✅ WORKS everywhere
client.write('command_request', {
  command: '/say Hello from bot!',
  origin: { type: 'player', uuid: '', request_id: '' },
  internal: false,
})
```

```ts
// ❌ KICKS on most servers — do not use
client.write('text', {
  type: 'chat', needs_translation: false,
  source_name: client.username, xuid: '', platform_chat_id: '',
  filtered_message: '', message: 'Hello!',
})
```

The bot sends `/say` as if the player typed a command — the server broadcasts it as normal chat.

**Running other commands:**
```ts
client.write('command_request', {
  command: '/kill @e[type=!player]',
  origin: { type: 'player', uuid: '', request_id: '' },
  internal: false,
})
```

**Reading chat:**
```ts
client.on('text', (p) => {
  if (p.source_name && p.source_name !== client.username) {
    console.log(`${p.source_name}: ${p.message}`)
  }
})
```

### Inventory

```ts
// Change hotbar slot
client.write('player_hotbar', { selected_slot: 0, window_id: 0, select_slot: true })

// Inventory transactions (move items, drop, equip)
client.write('inventory_transaction', { transaction: { ... } })

// Listen for inventory updates
client.on('inventory_content', (p) => console.log(p))
```

### Block Interaction

```ts
// Start breaking block
client.write('player_action', {
  runtime_entity_id: entityId,
  action: 'start_break',   // 0
  position: { x: 10, y: 64, z: 20 },
  result_position: { x: 10, y: 64, z: 20 },
  face: 0,
})
// Stop breaking (complete the break)
client.write('player_action', {
  runtime_entity_id: entityId,
  action: 'stop_break',    // 2
  position: { x: 10, y: 64, z: 20 },
  result_position: { x: 10, y: 64, z: 20 },
  face: 0,
})
```

## Movement Implementation

Two approaches:

### 1. Direct position updates (simplest)

```ts
function walkDirection(dir: string, blocks: number, pos, yaw, entityId) {
  const speed = 0.3, steps = Math.round(blocks / speed)
  const { sin, cos } = Math, yawRad = yaw * Math.PI / 180
  let dx = 0, dz = 0
  if (dir === 'forward') { dx = -sin(yawRad) * speed; dz = cos(yawRad) * speed }
  else if (dir === 'back')  { dx = sin(yawRad) * speed; dz = -cos(yawRad) * speed }
  else if (dir === 'left')  { dx = cos(yawRad) * speed; dz = sin(yawRad) * speed }
  else if (dir === 'right') { dx = -cos(yawRad) * speed; dz = -sin(yawRad) * speed }

  for (let i = 0; i < steps; i++) {
    if (!client || !entityId) return
    pos.x += dx; pos.z += dz
    client.write('move_player', {
      runtime_entity_id: entityId,
      position: { x: pos.x, y: pos.y, z: pos.z },
      pitch, yaw, head_yaw: yaw,
      mode: 'normal', on_ground: true,
      riding_runtime_entity_id: 0n,
      tick: 0n as any,  // 'as any' avoids BigInt TS errors
    })
    sleep(50)
  }
}
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))
```

Use `tick: 0n as any` to avoid TS errors when `target` < ES2020. The original `moveTo(targetX, targetZ)` approach is in `references/` — prefer directional walking for simpler control.

### 2. Queue-based sequenced movement

```ts
const moveQueue: { dir: string; dist: number }[] = []
let moving = false

async function processQueue() {
  if (moving || moveQueue.length === 0) return
  moving = true
  while (moveQueue.length > 0) {
    const cmd = moveQueue.shift()!
    await walkDirection(cmd.dir, cmd.dist, pos, yaw, entityId)
  }
  moving = false
}
function enqueue(dir: string, dist: number) {
  moveQueue.push({ dir, dist })
  processQueue()
}
```

For server-authoritative servers (1.19.30+) that require `player_auth_input` — test first: if the bot disconnects right after spawn without sending own movement, try adding auth input. Most Aternos servers work without it.

## Chat Command Pattern (Controlling Bot In-Game)

```ts
client.on('text', (p) => {
  if (p.type !== 'chat' || p.source_name === botUsername) return
  if (!p.message.startsWith('!')) return  // prefix commands

  const cmd = p.message.trim().toLowerCase()
  if (cmd === '!swing') swing()
  else if (cmd === '!jump') jump()
  else if (cmd.startsWith('!f ')) enqueue('forward', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!b ')) enqueue('back', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!l ')) enqueue('left', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!r ')) enqueue('right', parseInt(cmd.slice(3)) || 1)
  else if (cmd === '!pos') chat(`(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`)
  else if (cmd.startsWith('!say ')) chat(cmd.slice(5))
}
```

Common prefix: `!f N` (forward N blocks), `!b N` (back), `!l N` (left), `!r N` (right), `!jump`, `!swing`, `!pos` (coordinates), `!say <text>`.

## Reconnect with Exponential Backoff

```ts
let retryDelay = 5000
let reconnectTimer: any = null

function connect() {
  client = createClient({ ... })
  client.on('disconnect', (p) => {
    const reason = p?.reason ?? 'unknown'
    if (reason === 'server_id_conflict') {
      // ghost session — wait fixed 20s for ghost to clear
      cleanup()
      setTimeout(connect, 20000)
      return
    }
    if (reason === 'server_full') {
      // server at capacity — let backoff retry naturally
      scheduleReconnect()
      return
    }
    scheduleReconnect()
  })
  client.on('close', () => scheduleReconnect())
}

function cleanup() {
  if (swingTimer) clearInterval(swingTimer)
  if (reconnectTimer) clearTimeout(reconnectTimer)
  entityId = null; client = null
}

function scheduleReconnect() {
  cleanup()
  if (reconnectTimer) return  // already scheduled
  retryDelay = Math.min(retryDelay * 1.5, 60000)  // 5s → 7.5s → 11.25s → ... → 60s
  setTimeout(connect, retryDelay)
}

// Reset retry delay on successful spawn:
client.on('spawn', () => { retryDelay = 5000 })
```

### Reconnect reasons

| `reason` | Cause | Strategy |
|----------|-------|----------|
| `server_id_conflict` | Ghost session — another connection with same username still active on server | Wait fixed 20s (ghost clears ~30-60s) |
| `server_full` | Server at max player capacity | Let exponential backoff retry (5s → 7.5s → ... → 60s) |
| `(any other)` | Server kicked, banned, wrong version, etc. | Let backoff retry |
| `server_full` | Max player capacity reached | Let exponential backoff retry (5s → 7.5s → ... → 60s). Ping `playersOnline == playersMax` to confirm. |
| `close` (no reason) | Connection dropped (server restart, network) | Let backoff retry |

### Server capacity & ghost session detection

Ghost sessions persist for ~30-60s after the original client disconnects. In severe cases a "ghost storm" (from rapid reconnect loops across many bot processes) can pin the server at `playersOnline == playersMax` for minutes, blocking new connections entirely.

Use `ping()` before every reconnect attempt as a guard:

```ts
import { ping } from 'bedrock-protocol'

let serverDown = false  // state flag

async function tryConnect(host, port) {
  try {
    const info = await ping({ host, port, timeout: 5000 })
    if (info.playersOnline >= info.playersMax) {
      log(`Server full (${info.playersOnline}/${info.playersMax}), deferring`)
      serverDown = false
      return false
    }
    serverDown = false
    return true
  } catch {
    log('Ping timed out — server unreachable')
    serverDown = true
    return false
  }
}
```

**flow:**
1. Call `ping()` before `createClient()` — this is cheap (~2s) vs `createClient` timeout (~10s)
2. If `playersOnline >= playersMax` → skip `createClient`, let backoff fire next cycle
3. If ping times out → server down, skip `createClient`, set `serverDown` flag  
4. If ping returns a high count consistently (3+ minutes) with no active process → likely ghost storm. Only fix: Aternos restart or `/deop`/`/kick` in-game
5. Otherwise → room exists, call `createClient()`

Ghost session strategies:
- Use a **different username** and reconnect immediately
- **Wait** for the ghost to clear (backoff handles this)
- **Kill all bot processes**, wait 60s for ghosts to age out, then start fresh
- If `playersOnline` stays high (e.g. 4/4 for 3+ minutes) after killing ALL local processes → ghost storm. The server still has session entries for those clients. Run a single new bot — it'll enter the reconnect loop (`server_full`) with backoff, and eventually a slot frees. **However** this loop also generates new ghosts if the bot connects briefly, gets `server_id_conflict`, and disconnects — creating a cycle. Better approach: use a **unique username** on the first attempt to guarantee no conflict.

## Entity & World Events

| Event | When | Data |
|-------|------|------|
| `move_player` | Any player/entity moves | `runtime_entity_id`, `position`, rotation |
| `add_player` | Player joins | `username`, `entity_id`, position |
| `remove_entity` | Entity despawns | `entity_id` |
| `update_block` | Block changes | position, new block type |
| `level_chunk` | Chunk data | chunk coordinates, sub-chunk data |
| `text` | Chat message | `source_name`, `message`, `type` |

## Pitfalls

- **BigInt literals** (`0n`, `1n`) cause TS errors when `target` < ES2020. Two fixes: use `tick: 0n as any` in packet writes, or set `target: "ESNext"` + `skipLibCheck: true` in tsconfig.
- **`disconnect` + `close` duplicate reconnect** — Both events fire on the same disconnection. If both handlers call `scheduleReconnect()`, 2 timers run concurrently, doubling the backoff. Fix: only `close` triggers reconnect; `disconnect` just logs the reason:
  ```ts
  client.on('disconnect', (p) => {
    if (p?.reason === 'server_id_conflict') {
      cleanup()
      setTimeout(connect, 20000)
      return
    }
    log('Kick:', p?.reason)  // log only
  })
  client.on('close', () => scheduleReconnect())  // only close triggers reconnect
  ```
- **`@types/node` version mismatch** — `@types/node@25+` requires TS 5.7+ and `esnext.disposable` lib. This is a compile-time only issue — runtime via `tsx` is unaffected. Fix: `skipLibCheck: true`, `types: []` in tsconfig.
- **`server_id_conflict` / ghost sessions** — two clients with the same username get kicked immediately. The ghost persists on the server for ~30-60s after the original client disconnects, showing `playersOnline: 1` in the ping response. Fix: wait 20s and reconnect, or use a different username. The server may appear offline during the ghost window — check with `ping()` before connecting.
- **`player_auth_input` SizeOf errors** — Sending `player_auth_input` with wrong/omitted fields causes `SizeOf error for undefined : Cannot read properties of undefined (reading 'type')` crashes. The protocol serialiser expects exact field types for each version. If you need auth input (1.19.30+ servers), copy field structure exactly from the protocol docs. For most Aternos-type servers, skip auth input entirely — the bot works with just `move_player` + `animate`.
- **`disconnect` + `close` duplicate reconnect** — Both events fire on the same disconnection. If both handlers call `scheduleReconnect()`, 2 timers run concurrently, doubling the backoff. Fix: only `close` triggers reconnect; `disconnect` just logs the reason:
  ```ts
  client.on('disconnect', (p) => {
    if (p?.reason === 'server_id_conflict') {
      cleanup()
      setTimeout(connect, 20000)
      return
    }
    log('Kick:', p?.reason)  // log only
  })
  client.on('close', () => scheduleReconnect())  // only close triggers reconnect
  ```
- **Incremental testing methodology** — When debugging connection issues, strip the bot to minimum (just `createClient` + `spawn` + `animate` swing). Verify stability for 30-60s. Add one feature at a time. This isolates whether a disconnect is a protocol issue vs a server condition (ghost session, full server, version mismatch).
- **`server_full` ping check** — When ping shows `playersOnline == playersMax` consistently even after killing all bot processes, suspect **ghost storm** (rapid reconnect loops created many stale sessions). Ping before EACH reconnect attempt: if `playersOnline >= playersMax`, skip `createClient` to avoid rate-limit timeouts. Use a `tryConnect()` guard that returns false early. Ghost storms take 60-90s to clear — during that time ALL bots get `server_full`. Strategy: wait 90s, kill all processes, then start one fresh bot with a unique username.
- **`connect timed out`** — Occurs when the server is unreachable, saturated, or in a ghost session storm. The ping response + `playersOnline` check helps distinguish: if ping succeeds but `playersOnline >= playersMax`, the server is full. If ping times out, the server is down or port changed (Aternos ports change on restart).
- **Newer protocol (1.19.30+)** — some servers require `player_auth_input` for movement. If the bot disconnects right after spawn without sending movement, try adding auth input packets. Most Aternos servers work without it.
- **Method `on` type errors** — `Client` extends `EventEmitter` via JS prototype chain. Use `as any` or `skipLibCheck`. Runtime works fine.
- **Connection to own server** — use LAN IP, not `localhost`, to avoid port conflicts when MC server runs on the same machine as the bot.
- **Packet sending before ready** — sending packets before `spawn` event can cause `SizeOf` errors ("SizeOf error for undefined"). Always guard writes with `if (!client || !entityId) return`.
- **Multiple bots, one server** — Each bot needs a unique username. Even after killing a bot process, the server keeps a ghost session for ~30-60s. Trying to reconnect with the same name causes `server_id_conflict`. Workaround: wait 20-30s, or use a different name. When running an AFK bot + a player bot, give them distinct usernames in separate config files. — `skipPing: true` + monkey-patched version avoids auto-detection. If the version in config doesn't match the server's reported version, the connection may succeed at login but fail after spawn. Always ping first to verify.
- **Reconnect backoff reset placement** — Reset `retryDelay = 5000` inside the `spawn` handler (not in `scheduleReconnect()`) so exponential backoff actually grows on consecutive failures. If reset inside `scheduleReconnect()`, every retry starts at 5s and backoff never kicks in. Critical for `server_full` scenarios — without it the bot spams connection attempts.
- **Unique username for ghost storms** — When the server has ghost sessions stuck (showing 4/4 for 3+ minutes after killing all local processes), connect with a **different username** to bypass `server_id_conflict`. The new name has no ghost to conflict with. Once connected, the old ghosts eventually time out and slots free up. This breaks the reconnect-loop cycle.
- **`!say` via command_request** — In `handleChat`, when the bot needs to say something (e.g. `!hello` or `!pos` response), use `client.write('command_request', { command: '/say ...', ... })` NOT `client.write('text', { type: 'chat', ... })`. The text packet causes immediate kick on most servers.
- **HTTP port conflict** — When running both an AFK bot and a player bot on the same machine, give them different HTTP ports. Default: AFK bot uses 5500, player bot uses 5501. Starting a second process on the same port fails with `EADDRINUSE`.

## HTTP Control Server (Telegram Bridge)

For remote control of a running bot from Telegram/Discord, add a built-in HTTP server using Node.js stdlib `http`. The agent relays user commands via curl:

```ts
import { createServer } from 'node:http'
import { URL } from 'node:url'

const HTTP_PORT = 5501
createServer((req, res) => {
  const u = new URL(req.url!, `http://localhost:${HTTP_PORT}`)
  const p = u.pathname
  const n = parseInt(u.searchParams.get('n') || '1')
  const msg = u.searchParams.get('msg') || ''
  let body = ''
  if (p === '/swing') { swing(); body = 'ok' }
  else if (p === '/jump') { jump(); body = 'ok' }
  else if (p === '/f') { enqueueMove('forward', n); body = 'ok' }
  else if (p === '/b') { enqueueMove('back', n); body = 'ok' }
  else if (p === '/l') { enqueueMove('left', n); body = 'ok' }
  else if (p === '/r') { enqueueMove('right', n); body = 'ok' }
  else if (p === '/say' && msg) { chat(msg); body = 'ok' }
  else if (p === '/pos') body = JSON.stringify(pos)
  else if (p === '/status') body = JSON.stringify({ connected: !!client && !!entityId, pos })
  else { res.writeHead(404); res.end('unknown'); return }
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.end(body)
}).listen(HTTP_PORT, () => log(`HTTP control on :${HTTP_PORT}`))
```

Agent-to-bot command relay: `curl -s http://localhost:5501/f?n=5`. Available endpoints:
- `GET /f?n=N` — forward N blocks
- `GET /b?n=N` — back N blocks
- `GET /l?n=N` — left N blocks
- `GET /r?n=N` — right N blocks
- `GET /jump` — jump
- `GET /swing` — swing arm
- `GET /say?msg=text` — say text via command_request
- `GET /pos` — return current position JSON
- `GET /status` — return connection state + position JSON

## Running

```bash
# Foreground
cd my-bot && npm start

# Background (long-running bot)
cd /c/Users/datel/my-bot
# In Hermes, use terminal(background=true, notify_on_complete=true)
# then process(action='poll') to check status
```

## References

- `references/aterbot-player-full-bot.md` — fully working bot source with movement, chat commands, auto-swing, reconnect, ghost handling
- `references/aternos-server-management.md` — start/stop/check-status Aternos server via python-aternos Python library
- [bedrock-protocol GitHub](https://github.com/PrismarineJS/bedrock-protocol)
- [Protocol docs (prismarinejs.github.io)](https://prismarinejs.github.io/minecraft-data/?v=bedrock_1.26.30&d=protocol)
- [minecraft-data](https://github.com/PrismarineJS/minecraft-data)
