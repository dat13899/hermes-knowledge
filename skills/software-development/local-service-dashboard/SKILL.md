---
name: "local-service-dashboard"
title: "Local Service Dashboard"
description: "Zero-dep Node.js web dashboard quản lý local services — 2-column layout, special/regular card tiers, log panel, RAG + Aternos + netstat cache + process mgmt"
category: "software-development"
triggers: ["dashboard", "service dashboard", "local services", "quản lý port", "process manager", "port scan", "aternos", "rag", "2 column layout", "special card", "regular card"]
version: "3.0"
---

## Mô tả

Dashboard web local (`http://localhost:3000`) — 2 column layout. Trái: đặc biệt (Aternos, RAG) trên + service thường dưới. Phải: Log panel. Backend Node.js thuần (zero dep), frontend single HTML dark theme.

**Bố cục:**

```
┌──────────────────────────────┬───────────────────┐
│  🖥 Dashboard ▲ filter [R]  │                   │
│  ● N running ⊡ N total      │                   │
├──────────────────────────────┼───────────────────┤
│  ★ Đặc biệt (#N)            │  📋 Logs           │
│  ┌────────┐ ┌────────┐      │  ┌───────────────┐ │
│  │Aternos │ │RAG     │      │  │[dropdown] ✕   │ │
│  │▶■↻  ⏳ │ │🔍  ⟳  │      │  │⬇  count       │ │
│  └────────┘ └────────┘      │  │ log output…   │ │
│                              │  │               │ │
│  ⊞ Services (#N)            │  │               │ │
│  ┌─────┐ ┌──────┐ ┌────┐   │  └───────────────┘ │
│  │AFK  │ │Cuem  │ │Bdrk│   │                    │
│  │▶■↻📋✕│ │▶■↻📋✕│ │…  │   │                    │
│  └─────┘ └──────┘ └────┘   │                    │
│  [＋ Thêm service]          │                    │
└──────────────────────────────┴───────────────────┘
```

## Tính năng chính

- 2 cột: left (flex:1) + right (380px fixed), responsive → stack mobile (<900px)
- **Special cards** (Aternos + RAG): 2-column grid, gradient themed
- **Regular cards** (còn lại): compact 240px grid, action buttons (▶ ■ ↻ 📋 ✕)
- Log panel right, auto-scroll real-time qua SSE
- Port scan: netstat cache 5s TTL → detect port lạ + process name
- **Add/delete service** từ UI (modal form)
- **Confirm dialog** trước stop/restart/delete
- **Search/filter** services
- **Uptime display** (⏱ 5m23s / 2h15m)
- **Health check** — ping service port
- **Keyboard shortcuts**: `R` refresh, `F` focus search, `N` add service, `Esc` close modal/confirm
- Auto-detect port LISTENING ở startup
- Graceful shutdown (SIGINT/SIGTERM → kill child processes)
- Zero dep — chỉ Node.js + Python
- Aternos: cron watchdog + auto-confirm queue + start/stop/restart

## Card system

3 loại card, phân loại theo id:

### Special cards (★ Đặc biệt)
`.special-row` (2-column grid). Điều kiện: `s.id === 'aternos' || s.id === 'rag'`

**Aternos card** (`id: aternos`):
- Gradient xanh đậm (#1a2332→#162032), border #3b4a5e
- Hiển thị: status dot, address, player count, RAM
- Nút: Start / Stop / Restart / Queue (ẩn, hiện khi waiting)
- Poll 10s: `aternosFetch()`

**RAG card** (`id: rag`):
- Gradient tím (#1a1f2e→#161b28), border #4a3f6e
- Status dot, chunk count, inline search (input + 🔍 + ⟳)
- Kết quả trong `.rag-result` (hidden default, max-height 120px)
- API proxy qua dashboard: `/api/rag/status`, `/api/rag/query`, `/api/rag/reindex`

### Regular cards (⊞ Services)
`.service-grid` (auto-fill minmax(240px,1fr)). Action buttons: ▶ ■ ↻ 📋 ✕ (delete, with confirm dialog). ✕

### Add card button
Button `＋ Thêm service` ở cuối grid → mở modal form. Form: Tên, Mô tả, Dir, Command, Port.

## API endpoints

### Dashboard API (port 3000)

| Method | Path | Chức năng |
|---|---|---|
| GET | `/api/services` | Danh sách + trạng thái + uptime |
| POST | `/api/services` | Thêm service mới |
| DELETE | `/api/services/:id` | Xoá service |
| POST | `/api/services/:id/start` | Start (spawn) |
| POST | `/api/services/:id/stop` | Stop (taskkill /t /f) |
| GET | `/api/services/:id/logs?lines=200` | Log gần nhất |
| GET | `/api/services/:id/health` | Ping port health check |
| GET | `/api/scan` | Quét netstat port lạ |
| GET | `/api/aternos` | Aternos status |
| POST | `/api/aternos/start\|confirm\|stop\|restart` | Aternos actions |
| GET | `/api/rag/status` | RAG status proxy |
| POST | `/api/rag/query` | RAG query proxy |
| POST | `/api/rag/reindex` | RAG reindex proxy |
| GET | `/api/logs/stream` | SSE log real-time (`?serviceId=` lọc) |

### RAG server (port 3001)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/status` | — | `{ok, chunks, model}` |
| POST | `/query` | `{query, top_k}` | `{answer, sources}` |
| POST | `/reindex` | — | `{ok, chunks}` |

## Cấu trúc thư mục

```
C:\Users\datel\service-dashboard\
├── server.js                    # Backend (http, child_process, fs)
├── services.json                # Danh sách service
├── aternos.py                   # CLI: status|start|confirm|stop|restart
├── aternos_config.json          # Aternos credentials
├── aternos-watchdog.py          # Cron watchdog
├── public/
│   └── index.html               # Frontend single-page v3
├── rag_server.py                # FastAPI RAG (port 3001)
├── rag_chroma/                  # ChromaDB persistent
└── start.bat                    # Click chạy
```

## Auto-start services

Thêm `"autoStart": true` vào services.json entry. Server gọi `autoStartServices()` sau `server.listen()`:
```javascript
function autoStartServices() {
  for (const s of services) {
    if (s.autoStart && s.command) {
      const st = S.get(s.id);
      if (st && st.status !== 'running') startService(s.id);
    }
  }
}
```
Bỏ qua nếu port đã LISTENING (detect qua netstat cache). Thường dùng cho RAG server cần start cùng dashboard.

## Tối ưu backend (server.js)

### netstat cache
```javascript
let _netstatCache = { ts: 0, data: null };
function getNetstat() {
  if (_netstatCache.data && Date.now() - _netstatCache.ts < 5000) return _netstatCache.data;
  // parse netstat -ano → Map<port, pid>
}
```
Dùng ở 3 chỗ: initState, addService, scanPorts. Cache 5s tránh gọi netstat nhiều lần mỗi poll.

### Graceful shutdown
```javascript
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
```
Kill tất cả child processes (taskkill /t /f) trước khi exit.

### RAG proxy (thay execSync)
Tránh shell quoting security issue — proxy HTTP tới localhost:3001:
```javascript
const r = http.request({ hostname:'localhost', port:3001, path:'/query', method:'POST', headers:{'Content-Type':'application/json'} }, ...)
```

### Uptime tracking
Mỗi service state có `startedAt: Date.now()`. Backend trả `uptime` (seconds) trong getStatus().

### Health check
```javascript
// GET /api/services/:id/health → HEAD request tới service port
const r = http.request({ hostname:'localhost', port:svc.port, path:'/', method:'HEAD', timeout:3000 }, ...)
```

## Tối ưu frontend

### Add service modal
Modal overlay + form (Tên, Mô tả, Dir, Command, Port). `openModal()` / `closeModal()`. Gọi `POST /api/services`.

### Confirm dialog
```javascript
confirmAct(id, action) // action: 'stop' | 'restart' | 'delete'
```
Overlay confirm trước khi thực hiện destructive action.

### Search/filter
Input filter → ẩn/hiện card dựa trên name + description match.

### Render-once pattern (special cards)
Special cards (Aternos, RAG) có async fetch (`aternosFetch`, `ragFetch`) chạy interval riêng. `render()` chạy mỗi 3s từ `refresh()` sẽ destroy dot state nếu recreate HTML.
```javascript
let renderedInitial = false;
function render() {
  if (!renderedInitial) {
    specialEl.innerHTML = specials.map(...).join('');
    renderedInitial = true;
  }
  // Regular cards vẫn update bình thường
  svcEl.innerHTML = regular.map(normalCard).join('');
}
```
Reset `renderedInitial = false` nếu cần re-render special cards (thêm/xóa service special).

### Dot class initialization
Card function phải set dot class từ service status, ko để empty:
```javascript
function ragCard() {
  const svc = services.find(s => s.id === 'rag');
  const dotClass = svc?.status === 'running' ? 'dot running' : 'dot stopped';
  return `<span class="${dotClass}" id="rdot"></span>`;
}
```
Như vậy dù render có chạy giữa các poll, dot vẫn đúng class. `ragFetch`/`aternosFetch` chỉ refine thêm.

### Uptime display
```javascript
fmtUptime(sec) // 5s → "5s", 130s → "2m10s", 7200s → "2h0m"
```
Hiển thị ⏱ badge trên card đang running.

### Keyboard shortcuts
```javascript
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'r' || e.key === 'R') refresh()
  if (e.key === 'f' || e.key === 'F') $('#search-input').focus()
  if (e.key === 'n' || e.key === 'N') openModal()
  if (e.key === 'Escape') closeModal(); closeConfirm()
})
```

### SSE exponential backoff
```javascript
let sseRetry = 1000;
evtSrc.onerror = () => {
  sseRetry = Math.min(sseRetry * 1.5, 30000);
  setTimeout(connectSSE, sseRetry);
}
```
Reset 1000ms khi kết nối thành công, backoff tối đa 30s.

## Pitfalls

- **RAG card ragFetch()** → dùng `http://localhost:3001/status` cũ. Frontend v3 dùng `/api/rag/status` (proxy). Nếu port 3001 ko chạy, proxy trả `{ok: false}`.
- **RAG query execSync cũ** → server.js cũ dùng execSync RAG = security risk. Server v3 proxy HTTP thay thế.
- **selLog active state**: dùng class `active` trên button 📋 khi service đang được chọn trong log panel.
- **Aternos port=0**: services.json entry port=0 vì Aternos ko có port cố định. Dashboard skip health check cho port=0.
- **CORS**: ko cần CORS nữa vì frontend dùng proxy qua dashboard (cùng origin).
- **ChromaDB race**: 1 RAG instance — conflict nếu chạy 2 process cùng DB.
- **Special cards blink khi poll**: `render()` chạy mỗi 3s recreate toàn bộ HTML — xóa dot class vừa set bởi `ragFetch()`/`aternosFetch()` (chạy 10s). Fix: dùng flag `renderedInitial` để chỉ render special cards 1 lần. Đồng thời khởi tạo dot class từ `svc.status` trong `ragCard()`/`aternosCard()` thay vì empty.
- **`taskkill /f /im node.exe` kill cả service ko liên quan**: Trên máy Anh Đạt có 9router (port 20128) chạy node — lệnh này tắt luôn, gây lỗi. Luôn dùng `taskkill /pid <PID>` hoặc filter port: `taskkill /fi "tcp eq 5500" /f`. NOT `/im node.exe`.
- **RAG dot class empty trên card mới render**: `ragCard()` để `class="dot"` (ko class). Sau đó `ragFetch()` set thành `dot running` hoặc `dot stopped`. Nhưng `render()` tạo lại card mới → dot lại empty → blink. Fix: trong `ragCard()`, đọc `svc.status` và set dot class từ đầu: `const dotClass = svc?.status === 'running' ? 'dot running' : 'dot stopped';`.
- **Aternos dot có 4 trạng thái**: running (green), stopped (gray), waiting/preparing (yellow), loading/starting (orange). `aternosFetch()` set dot.style trực tiếp, ko dùng className cho yellow/orange. `render()` ko nên touch Aternos dot.

## Cách thêm service

Modal từ UI hoặc thêm vào services.json trực tiếp:
```json
{"id": "my-svc", "name": "My Service", "description": "...", "dir": "C:\\path", "command": "node app.js", "port": 3002}
```
Dashboard auto-detect port LISTENING sau khi reload.
