# aterbot-player — Fully Working Bot

Complete bot `C:\Users\datel\aterbot-player\src\index.ts` for Minecraft Bedrock (Aternos server, version 1.26.30).

## Architecture

- **config.json** — host, port, username (no version string; monkey-patch hardcoded)
- **index.ts** — ESM TypeScript ~200 lines, runs via `tsx`
- **start.bat** — `cd /d %~dp0 && npm start && pause`

## Key Patterns

### Version patch (must run before createClient)

```ts
import { Versions } from 'bedrock-protocol/src/options.js'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
;(() => {
  const d = require('minecraft-data/data.js')
  if (d.bedrock?.['1.26.30']) d.bedrock['1.26.30.5'] = d.bedrock['1.26.30']
  const idx = require('minecraft-data')
  if (!idx.versions.bedrock.find((v: any) => v.minecraftVersion === '1.26.30.5'))
    idx.versions.bedrock.unshift({ version: 1001, minecraftVersion: '1.26.30.5', majorVersion: '1.26.30', releaseType: 'release' })
  const v30 = idx.versionsByMinecraftVersion.bedrock['1.26.30']
  idx.versionsByMinecraftVersion.bedrock['1.26.30.5'] = { version: 1001, minecraftVersion: '1.26.30.5', majorVersion: '1.26.30', releaseType: 'release', dataVersion: v30?.dataVersion ?? 0 }
})()
Versions['1.26.30.5'] = 1001
Versions['1.26.0'] = 944
```

### createClient (skipPing + fixed version)

```ts
client = createClient({
  host, port: +port, username,
  offline: true,
  version: '1.26.30.5',
  skipPing: true,
})
```

### Movement via move_player (directional)

Direct `move_player` writes with 50ms interval. No `player_auth_input`.

```ts
function walk(dir, blocks) {
  const speed = 0.3, steps = Math.round(blocks / speed)
  const { sin, cos } = Math, yawRad = yaw * Math.PI / 180
  let dx = 0, dz = 0
  switch (dir) {
    case 'forward': dx = -sin(yawRad) * speed; dz = cos(yawRad) * speed; break
    case 'back':    dx = sin(yawRad) * speed; dz = -cos(yawRad) * speed; break
    case 'left':    dx = cos(yawRad) * speed; dz = sin(yawRad) * speed; break
    case 'right':   dx = -cos(yawRad) * speed; dz = -sin(yawRad) * speed; break
  }
  for (let i = 0; i < steps; i++) {
    pos.x += dx; pos.z += dz
    client.write('move_player', {
      runtime_entity_id: entityId,
      position: { x: pos.x, y: pos.y, z: pos.z },
      pitch, yaw, head_yaw: yaw,
      mode: 'normal', on_ground: true,
      riding_runtime_entity_id: 0n, tick: 0n as any,
    })
    sleep(50)
  }
}
```

### Reconnect with exponential backoff + server_full guard

```ts
let retryDelay = 5000
let reconnectTimer: any = null

function connect() { /* ... createClient(...) ... */ }

function scheduleReconnect() {
  cleanup()
  if (reconnectTimer) return
  log(`Reconnect in ${retryDelay / 1000}s`)
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    retryDelay = Math.min(retryDelay * 1.5, 60000)
    connect()
  }, retryDelay)
}

// On spawn, reset:
client.on('spawn', () => { retryDelay = 5000 })

// On disconnect:
client.on('disconnect', (packet) => {
  if (packet?.reason === 'server_id_conflict') {
    cleanup()
    reconnectTimer = setTimeout(connect, 20000)  // fixed 20s for ghost
    return
  }
  scheduleReconnect()
})

client.on('close', () => scheduleReconnect())
```

### Chat command handler

```ts
client.on('text', (p) => {
  if (p.type !== 'chat' || p.source_name === botUsername) return
  const cmd = p.message.trim().toLowerCase()
  if (cmd === '!swing') swing()
  else if (cmd === '!jump') jump()
  else if (cmd.startsWith('!f ')) enqueue('forward', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!b ')) enqueue('back', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!l ')) enqueue('left', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!r ')) enqueue('right', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!say ')) chat(cmd.slice(5))
  else if (cmd === '!pos') chat(`(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`)
})

// NOTE: bot's chat() function must use command_request, NOT text packet:
function chat(msg: string) {
  if (!client) return
  // ✅ Use /say command — text packet kicks
  client.write('command_request', {
    command: `/say ${msg}`,
    origin: { type: 'player', uuid: '', request_id: '' },
    internal: false,
  })
}
```

### Jump

```ts
function jump() {
  if (!client || !entityId) return
  pos.y += 0.5
  client.write('move_player', { ..., position: { x: pos.x, y: pos.y, z: pos.z }, mode: 'normal', on_ground: false })
  setTimeout(() => { pos.y -= 0.5 }, 500)
}
```

## Full Source

See `C:\Users\datel\aterbot-player\src\index.ts` on the Windows host.