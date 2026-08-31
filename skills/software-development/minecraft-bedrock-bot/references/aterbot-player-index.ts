// === Fully working bedrock-protocol bot example ===
// See minecraft-bedrock-bot skill for full context.
// Copy this, change config.json, run with `npx tsx ./src/index.ts`

import { createClient } from 'bedrock-protocol'
// @ts-ignore
import { Versions } from 'bedrock-protocol/src/options.js'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const CONFIG: any = JSON.parse(readFileSync(new URL('../config.json', import.meta.url), 'utf-8'))

// ---------- version monkey-patch ----------
;(() => {
  try {
    const d = require('minecraft-data/data.js')
    if (d.bedrock?.['1.26.30']) d.bedrock['1.26.30.5'] = d.bedrock['1.26.30']
    const idx = require('minecraft-data')
    if (!idx.versions.bedrock.find((v: any) => v.minecraftVersion === '1.26.30.5'))
      idx.versions.bedrock.unshift({ version: 1001, minecraftVersion: '1.26.30.5', majorVersion: '1.26.30', releaseType: 'release' })
    const v30 = idx.versionsByMinecraftVersion.bedrock['1.26.30']
    idx.versionsByMinecraftVersion.bedrock['1.26.30.5'] = { version: 1001, minecraftVersion: '1.26.30.5', majorVersion: '1.26.30', releaseType: 'release', dataVersion: v30?.dataVersion ?? 0 }
  } catch (_) {}
  Versions['1.26.30.5'] = 1001
  Versions['1.26.0'] = 944
})()

// ---------- helpers ----------
const now = () => new Date().toLocaleTimeString('en-GB', { hour12: false })
const log = (...a: any[]) => console.log(`[${now()}]`, ...a)
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

// ---------- state ----------
let client: any = null
let entityId: any = null
let pos = { x: 0, y: 0, z: 0 }
let yaw = 0, pitch = 0
let swingTimer: any = null

// ---------- movement queue ----------
type Dir = 'forward' | 'back' | 'left' | 'right'
let moveQueue: { dir: Dir; dist: number }[] = []
let moving = false

async function processQueue() {
  if (moving || moveQueue.length === 0) return
  moving = true
  while (moveQueue.length > 0) {
    const cmd = moveQueue.shift()!
    await walk(cmd.dir, cmd.dist)
  }
  moving = false
}

function enqueue(dir: Dir, dist: number) {
  moveQueue.push({ dir, dist })
  processQueue()
}

async function walk(dir: Dir, blocks: number) {
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
    try {
      client.write('move_player', {
        runtime_entity_id: entityId,
        position: { x: pos.x, y: pos.y, z: pos.z },
        pitch, yaw, head_yaw: yaw,
        mode: 'normal', on_ground: true,
        riding_runtime_entity_id: 0n, tick: 0n as any,
      })
    } catch (_) {}
    await sleep(50)
  }
}

// ---------- actions ----------
function swing() {
  if (!client || !entityId) return
  try { client.write('animate', { action_id: 1, runtime_entity_id: entityId }) } catch (_) {}
}
function jump() {
  if (!client || !entityId) return
  pos.y += 0.5
  try {
    client.write('move_player', {
      runtime_entity_id: entityId,
      position: { x: pos.x, y: pos.y, z: pos.z },
      pitch, yaw, head_yaw: yaw,
      mode: 'normal', on_ground: false,
      riding_runtime_entity_id: 0n, tick: 0n as any,
    })
  } catch (_) {}
  setTimeout(() => { pos.y -= 0.5 }, 500)
}
function chat(msg: string) {
  if (!client) return
  try {
    client.write('text', {
      type: 'chat', needs_translation: false,
      source_name: CONFIG.client.username || 'Bot', xuid: '', platform_chat_id: '',
      message: msg,
    })
  } catch (_) {}
}

// ---------- connect + reconnect ----------
let reconnectTimer: any = null
let retryDelay = 5000

function connect() {
  if (client) return
  log('Connecting to', `${CONFIG.client.host}:${CONFIG.client.port}`)
  client = createClient({
    host: CONFIG.client.host, port: +CONFIG.client.port,
    username: CONFIG.client.username, offline: true,
    version: '1.26.30.5', skipPing: true,
  })
  client.on('join', () => log('Joined'))
  client.on('spawn', () => {
    entityId = client.entityId
    retryDelay = 5000
    log(`Spawned | entityId=${entityId}`)
    if (swingTimer) clearInterval(swingTimer)
    swingTimer = setInterval(() => swing(), 3000)
    log('Bot ready — auto-swing every 3s')
  })
  client.on('move_player', (p: any) => {
    if (p.runtime_entity_id === entityId) {
      pos = { x: p.position.x, y: p.position.y, z: p.position.z }
      yaw = p.yaw ?? yaw; pitch = p.pitch ?? pitch
    }
  })
  client.on('text', (p: any) => {
    if (p.type === 'chat' && p.source_name !== CONFIG.client.username) {
      log(`[Chat] <${p.source_name}> ${p.message}`)
      handleChat(p.source_name, p.message)
    }
  })
  client.on('disconnect', (p: any) => {
    const reason = p?.reason ?? 'unknown'
    if (reason === 'server_id_conflict') {
      log('server_id_conflict — waiting 20s')
      cleanup(); reconnectTimer = setTimeout(connect, 20000)
      return
    }
    log('Kick:', reason)
    scheduleReconnect()
  })
  client.on('close', () => { log('Disconnected'); scheduleReconnect() })
  client.on('error', (e: Error) => log('Error:', e.message))
}

function cleanup() {
  if (swingTimer) { clearInterval(swingTimer); swingTimer = null }
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  entityId = null; client = null
}

function scheduleReconnect() {
  cleanup()
  if (reconnectTimer) return
  log(`Reconnect in ${retryDelay / 1000}s`)
  retryDelay = Math.min(retryDelay * 1.5, 60000)
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, retryDelay)
}

function handleChat(_sender: string, msg: string) {
  const cmd = msg.toLowerCase().trim()
  if (cmd === '!swing') swing()
  else if (cmd === '!jump') jump()
  else if (cmd.startsWith('!f ')) enqueue('forward', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!b ')) enqueue('back', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!l ')) enqueue('left', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!r ')) enqueue('right', parseInt(cmd.slice(3)) || 1)
  else if (cmd.startsWith('!say ')) chat(cmd.slice(5))
  else if (cmd === '!pos') chat(`(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`)
}

connect()
process.on('SIGINT', () => { cleanup(); process.exit() })
process.on('SIGTERM', () => { cleanup(); process.exit() })
