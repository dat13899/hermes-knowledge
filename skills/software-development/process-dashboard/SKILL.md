---
name: process-dashboard
title: Process Dashboard
description: Build zero-dependency local web dashboards to manage Windows services/processes — start, stop, restart, view live logs via browser
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [windows, nodejs]
---

# Process Dashboard

Build a local web dashboard to manage Windows services/processes without any npm dependencies.

## When to Use

- User runs multiple long-lived services/bots on Windows and needs a browser UI to manage them
- Lightweight requirement — adding Express or a framework is overkill
- User wants to see service status at a glance + one-click start/stop + log viewer
- Pattern also works on Linux/macOS (just skip taskkill workaround)

## Architecture

```
[Browser] ← HTTP → [Node.js server (zero dep)]
                       │
              child_process.spawn + taskkill
                       │
            [managed processes: bots, servers, etc]
```

**Backend**: single `server.js`, zero dependencies — uses only `http`, `fs`, `path`, `child_process`.

**Frontend**: single `public/index.html` — embedded CSS + vanilla JS. No build step, no framework.

**Config**: `services.json` — array of service definitions (id, name, dir, command, port).

## Step-by-Step

### 1. Create services.json

Each service entry:

```json
{
  "id": "my-bot",
  "name": "My Bot",
  "description": "What it does, shown as card subtitle",
  "dir": "C:\\path\\to\\project",
  "command": "cmd.exe /c npm start",
  "port": 5500
}
```

`command` field: on Windows, prefix with `cmd.exe /c` for npm/npx scripts. This runs through cmd.exe properly.

### 2. Build the backend (server.js)

Core components:

**Process state map:**
```js
const S = new Map(); // id → { proc, pid, status, logs[], sseClients[] }
```

**Start service** — spawn with `windowsHide: true`, capture stdout/stderr into a ring buffer:
```js
const child = spawn(cmd, args, {
  cwd: svc.dir,
  windowsHide: true,
  stdio: ['ignore', 'pipe', 'pipe'],
});
```

**Stop service** — on Windows, taskkill `/t` kills the full process tree:
```js
spawn('taskkill', ['/pid', String(pid), '/t', '/f'], { windowsHide: true, stdio: 'ignore' }).unref();
```

**Log ring buffer** — keep last 2000-3000 lines per service. Trim from front on overflow.

**SSE endpoint** — `/api/logs/stream?serviceId=X`. Each new log line broadcasts to all connected SSE clients for that service.

### 3. Build the frontend (public/index.html)

Single HTML file with embedded CSS + JS:

- **Cards grid** — responsive grid of service cards, each showing: status dot (●green/●gray), name, port badge, description, PID, action buttons (Start/Stop/Restart/Log)
- **Log panel** — bottom panel with service selector dropdown, auto-scroll toggle, auto-refresh via SSE
- **Status polling** — every 3s poll `/api/services` to update cards
- **SSE** — connect to `/api/logs/stream`, receive `event: log` messages with `{serviceId, line, ts}`, append to selected service's log panel

### 4. Run

```bash
node server.js
# → http://localhost:3000
```

### 5. Tab System (v2.0)

The dashboard has two tabs:

**Tab 1 — "Ưu tiên" (Priority):** Shows services from `services.json` only. Each card has Start/Stop/Restart/Log buttons + a ✕ delete button. An **"+ Thêm service"** button opens a modal to add a new entry (name, port, dir, command, description). Modal POSTs to `/api/services` which writes to `services.json` and updates runtime state.

**Tab 2 — "Quét port" (Scan):** Discovers unknown listening ports via netstat. Each scanned port gets a card showing port number, PID, and process name. A **"+ Thêm vào ưu tiên"** button pre-fills the add-service modal with the port number and process name for one-click promotion.

```html
<!-- Tab bar structure -->
<div class="tabs">
  <button class="tab active" data-tab="priority">★ Ưu tiên</button>
  <button class="tab" data-tab="scan">🔍 Quét port</button>
</div>
<div class="tab-content active" id="tab-priority">...</div>
<div class="tab-content" id="tab-scan">...</div>
```

Switching to the Scan tab auto-triggers a scan. Switching back to Priority fetches fresh `/api/services`.

### 6. Port Scanning (v2.0)

**Endpoint:** `GET /api/scan`

Backend runs `netstat -ano`, parses TCP LISTENING lines, resolves process names via `tasklist /fi "pid eq X" /nh /fo csv`:

```js
function scanPorts() {
  const known = new Set(services.map(s => s.port));
  known.add(PORT); // dashboard itself (3000)

  const portMap = new Map();
  const out = execSync('netstat -ano', { encoding: 'utf8', timeout: 5000 });

  for (const line of out.split('\n')) {
    const m = line.match(/^\s*TCP\s+\S+:(\d+)\s+\S+:\d+\s+LISTENING\s+(\d+)/);
    if (m) {
      const port = parseInt(m[1]), pid = parseInt(m[2]);
      if (!portMap.has(port)) portMap.set(port, { port, pid, name: '' });
    }
  }

  // Resolve names and filter
  for (const [port, info] of portMap) {
    const out = execSync(`tasklist /fi "pid eq ${info.pid}" /nh /fo csv`, { encoding: 'utf8', timeout: 3000 });
    const m = out.match(/"([^"]+)"/);
    if (m) info.name = m[1];
    info.known = known.has(port) || SYSTEM_PORTS.has(port) || port < 1024;
  }
  // Return only unknown ports, sorted
  return [...portMap.values()].filter(p => !p.known).sort((a, b) => a.port - b.port);
}
```

**System ports excluded from scan** (beyond <1024 and known services):
```
135, 445, 3389, 5040, 5357, 7680, 8644, 20128, 49664-49675
```

### 7. Service CRUD (v2.0)

**Add service** — `POST /api/services` with JSON body `{name, description, dir, command, port}`:
- Auto-generates `id` from name (lowercased, non-alphanum → hyphens)
- Rejects if `id` or `port` already exists
- Writes updated `services.json` to disk
- Creates fresh runtime state entry

**Remove service** — `DELETE /api/services/:id`:
- Stops the service if running (via `stopService`)
- Removes from both `services[]` array and `S` state map
- Writes updated `services.json`

```js
function saveServices() {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(services, null, 2), 'utf-8');
}
```

Both operations preserve existing runtime state for services that aren't being modified.

## REST API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/services` | List all services + running status + PID |
| POST | `/api/services` | Add new service (body: `{name, port, dir?, command?, description?}`) |
| DELETE | `/api/services/:id` | Remove service + stop if running |
| POST | `/api/services/:id/start` | Start service (spawn child process) |
| POST | `/api/services/:id/stop` | Stop service (taskkill /t /f) |
| GET | `/api/services/:id/logs?lines=200` | Get recent log entries from ring buffer |
| GET | `/api/scan` | Scan listening ports via netstat, return unknown ones |
| GET | `/api/logs/stream?serviceId=X` | SSE — real-time log stream (omit serviceId for all) |

## Windows Process Management

### Spawn on Windows

```js
// npm scripts need cmd.exe context
spawn('cmd.exe', ['/c', 'npm', 'start'], { cwd: dir, windowsHide: true, stdio: [...] });
// OR with shell: true
spawn('npm start', [], { cwd: dir, shell: true, windowsHide: true, stdio: [...] });
```

### Kill on Windows

`child.kill()` sends SIGTERM which TerminateProcess only the immediate child. Use `taskkill` for tree kill:

```js
spawn('taskkill', ['/pid', String(pid), '/t', '/f'], { windowsHide: true, stdio: 'ignore' }).unref();
```

`/t` = kill process tree, `/f` = force.

### Detecting port-in-use

If the service starts its own HTTP server and the port is taken, the process will exit with EADDRINUSE. This is captured in logs and shown as status `error`.

## SSE (Server-Sent Events)

```js
res.writeHead(200, {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
});
res.write(`event: connected\ndata: {}\n\n`);

// On each log line:
res.write(`id: ${ts}\nevent: log\ndata: ${JSON.stringify({serviceId, line, ts})}\n\n`);
```

Keep a Set of callback functions per service. When a log line arrives, iterate and call each. Clean up on `res.on('close')`.

## UI/UX Components (v3.0)

### Toast system (stacked + undo)

```javascript
function toast(msg, type, undoCb){
  const c = document.getElementById('toast-container') || (t=>{t.id='toast-container';document.body.appendChild(t);return t})(document.createElement('div'));
  c.className = 'toast-container';
  const el = document.createElement('div'); el.className = 'toast ' + type; el.innerHTML = msg;
  if(undoCb){
    const u = document.createElement('button'); u.className = 'toast-undo'; u.textContent = 'Undo';
    u.onclick = ()=>{ undoCb(); el.classList.add('removing'); setTimeout(()=>el.remove(),200); };
    el.appendChild(u);
  }
  c.appendChild(el);
  setTimeout(()=>{ el.classList.add('removing'); setTimeout(()=>el.remove(),200); }, 4000);
}
```

### Keyboard shortcuts overlay

Press `?` to show overlay. Use on all 3 pages:

```html
<div class="kb-overlay" id="kb-overlay" onclick="if(event.target===this)this.classList.toggle('show')">
  <div class="kb-panel">
    <h3>⌨ Keyboard Shortcuts</h3>
    <div class="kb-row"><span>Show help</span><kbd>?</kbd></div>
    <div class="kb-row"><span>Go to Dashboard</span><kbd>g</kbd> then <kbd>d</kbd></div>
    <div class="kb-row"><span>Go to Documents</span><kbd>g</kbd> then <kbd>o</kbd></div>
  </div>
</div>
```

JS: `document.addEventListener('keydown', e => { if(e.key==='?' && !(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')){ e.preventDefault(); document.getElementById('kb-overlay')?.classList.toggle('show'); } });`

### SSE real-time logs (EventSource thay polling)

```javascript
let logEventSource = null;
function connectSSE(filterId){
  if(logEventSource) logEventSource.close();
  const url = filterId ? `/api/logs/stream?serviceId=${filterId}` : '/api/logs/stream';
  logEventSource = new EventSource(url);
  logEventSource.onmessage = function(e){
    try {
      const d = JSON.parse(e.data);
      if(filterId && d.serviceId !== filterId) return;
      appendLog(d.line, false);
    } catch(_){}
  };
  // Browser auto-reconnects on error
}
```

### Expandable service cards

```javascript
function toggleExpand(id){
  document.querySelector(`[data-svc-id="${id}"]`)?.classList.toggle('expanded');
}
```

CSS: `.card-expanded-body{display:none;padding:.5rem .75rem;border-top:1px solid var(--border);font-size:.75rem}` + `.card-expandable.expanded .card-expanded-body{display:block}`

### Health ping inline

```javascript
async function pingHealth(id, port, el){
  if(!port) return;
  try {
    const r = await fetch(`/api/services/${id}/health`, { signal: AbortSignal.timeout(4000) });
    const d = await r.json();
    el.className = 'health-dot ' + (d.ok ? 'online pulse' : 'offline');
  } catch(e){ el.className = 'health-dot offline'; }
}
```

### Reading progress bar (documents page)

```javascript
readerContent.addEventListener('scroll', function(){
  const h = this.scrollHeight - this.clientHeight;
  if(h <= 0) return;
  document.getElementById('reading-progress').style.width = Math.min(100, Math.round(this.scrollTop/h*100)) + '%';
});
```

HTML: `<div class="reading-progress" id="reading-progress"></div>` fixed position top, 3px gradient height.

### Font size controls (documents page)

CSS var `--font-size` controls `.reader-content .article{font-size:var(--font-size)}`. Buttons call `fontSize(delta)` which adjusts `--font-size` between 0.7rem and 1.5rem.

### Typing hero effect (landing page)

Cycle through 4 taglines with typewriter effect: `lines=['Chạy home lab 24/7','Tự động hóa với AI',...]`. Forward 80ms/char, back 40ms/char, 2s pause at end.

### Skeleton shimmer with stagger

```css
.skel-d1{animation-delay:.1s}.skel-d2{animation-delay:.2s}.skel-d3{animation-delay:.3s}
```

### Preconnect CDN

```html
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
```

### Git workflow trước mỗi edit

```bash
# Before edit
git add -A && git commit -m "snapshot: <state>"
# After edit + test OK
git add -A && git commit -m "<action>: <summary>"
git push origin master
# Rollback
git reset --hard HEAD~1
```

## Pitfalls

- **GET vs POST mismatch**: Frontend `fetch()` defaults to GET. API endpoints for start/stop/restart check for POST. Must pass `{ method: 'POST' }` explicitly. Without it, request hits static file handler → 404 HTML → `r.json()` throws. Always wrap API calls with explicit method.
- **api() error handling**: Always wrap fetch in `try/catch` and check `r.ok` before calling `.json()`. Without this, network errors or non-JSON responses (HTML 404) silently fail and the button appears to do nothing.
- **EADDRINUSE**: If managed service port is occupied, process crashes immediately. Log shows the error clearly.
- **cmd.exe wrapper**: Without `cmd.exe /c` on Windows, npm/npx scripts may fail because `.cmd` files need cmd.exe context (even with `shell: true`).
- **taskkill /t required**: Without tree kill, `npm start` → `tsx` child process survives.
- **Log buffer size**: 2000-3000 lines prevents OOM for long-running services.
- **SSE client cleanup**: Always delete callback from Set on connection close, else memory leak.
- **Port conflict**: Dashboard itself uses port 3000 — make sure it's free or change the constant.

## Extending

- Add auto-start on dashboard boot (iterate services, start if flag in config)
- Health check by pinging service port with `http.get`
- Protected mode with simple password / basic auth
- More service metadata: version, uptime, restart count

### Theme toggle (dark/light)

Add dark/light switch to dashboard pages:

**1. CSS custom properties** — light theme overrides `:root`:
```css
[data-theme="light"]{
  --bg:#f8fafc;
  --surface:#ffffff;
  --surface-2:#e2e8f0;
  --border:#cbd5e1;
  --accent:#6366f1;
  --accent-2:#0891b2;
  --text:#0f172a;
  --text-dim:#64748b;
  --green:#16a34a;
  --red:#dc2626;
  --orange:#d97706;
}
```

**2. Toggle button** — add to nav/top bar:
```html
<button id="theme-toggle" class="theme-btn" aria-label="Toggle theme">🌙</button>
```
Style: `background:none; border:1px solid var(--border); border-radius:6px; cursor:pointer; padding:4px 8px; font-size:16px;`

**3. JavaScript** — toggle `data-theme` on `<html>`, save to localStorage:
```javascript
(function(){
  const btn = document.getElementById('theme-toggle');
  const html = document.documentElement;
  const key = 'theme-landing'; // unique per page
  if (localStorage.getItem(key) === 'light') html.setAttribute('data-theme', 'light');
  if (localStorage.getItem(key) === 'light') btn.textContent = '☀️';
  btn.addEventListener('click', () => {
    const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    btn.textContent = next === 'light' ? '☀️' : '🌙';
    localStorage.setItem(key, next);
  });
})();
```

Use unique `key` per page (`theme-landing`, `theme-dash`) so each page remembers its own setting.

### CSS framework: Bulma (preferred) / Pico CSS (alternative)

User btdat prefers **Bulma** over Pico CSS (chê Pico "xấu quá"). Mặc định dùng Bulma cho dashboard + landing page. Pico CSS vẫn là alternative nếu user yêu cầu nhẹ/classless.

#### Bulma

**CDN:**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1/css/bulma.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
```

**Components thường dùng cho dashboard/landing:**
- `<nav class="navbar">` — top bar với brand + links + burger menu mobile
- `<div class="columns">` — split layout (services + logs)
- `<div class="card">` → `.card-content` + `.card-footer` — service cards với action buttons
- `<div class="level">` — horizontal alignment (status dot + name + port badge)
- `<span class="tag">` — port badge, status counters
- `<button class="button is-small is-link">` — action buttons
- `<div class="modal">` → `.modal-card` — create/edit modals
- `<div class="select">` + `<select>` — log service selector
- `<section class="section">` + `<div class="container">` — page layout

**Dark theme với CSS vars override:**
```css
[data-theme="dark"]{
  --bulma-scheme-main:#0a0e17;
  --bulma-scheme-main-bis:#111827;
  --bulma-scheme-main-ter:#1e293b;
  --bulma-background:#111827;
  --bulma-border:#2d3a5c;
  --bulma-text:#f1f5f9;
  --bulma-text-strong:#ffffff;
  --bulma-text-light:#94a3b8;
  --bulma-link:#818cf8;
  --bulma-link-hover:#6366f1;
  --bulma-body-background-color:#0a0e17;
  --bulma-card-background-color:#111827;
  --bulma-card-shadow:none;
  --bulma-navbar-background-color:#111827;
}
[data-theme="light"]{
  --bulma-link:#6366f1;
  --bulma-link-hover:#4f46e5;
}
```

**Landing page structure với Bulma:**
```html
<nav class="navbar" role="navigation">
  <div class="navbar-brand">
    <a class="navbar-item has-text-weight-bold" href="/">Site</a>
    <a role="button" class="navbar-burger" onclick="..."><span></span><span></span><span></span></a>
  </div>
  <div class="navbar-menu"><div class="navbar-end"><a class="navbar-item" href="/dashboard">Dashboard</a></div></div>
</nav>
<section class="section">
  <div class="container has-text-centered" style="max-width:600px">
    <h1 class="title is-1">👋 Hello</h1>
    <h2 class="subtitle is-5 has-text-grey-light">Tagline</h2>
    <a class="button is-link is-medium" href="/dashboard">Dashboard →</a>
  </div>
</section>
```

**Dashboard layout với columns:**
```html
<section class="section" style="padding:1rem 1.5rem">
  <div class="columns">
    <div class="column">
      <h2 class="title is-5">📦 Services</h2>
      <div id="svc-list"><!-- cards --></div>
    </div>
    <div class="column is-one-third">
      <h2 class="title is-5">📋 Logs</h2>
      <div class="select is-fullwidth"><select id="log-select"></select></div>
      <div id="log-box"><!-- log output --></div>
    </div>
  </div>
</section>
```

**Service card với Bulma:**
```html
<div class="card">
  <div class="card-content" style="padding:.75rem">
    <div class="level is-mobile">
      <div class="level-left">
        <div class="level-item"><span class="sc-dot running"></span><strong>Service name</strong></div>
      </div>
      <div class="level-right"><a class="tag is-info is-light" href="/proxy/5500/">:5500 🔗</a></div>
    </div>
    <p class="is-size-7 has-text-grey-light">Description</p>
    <p class="is-size-7 has-text-grey" style="font-family:monospace">PID 1234 🟢 Running</p>
  </div>
  <div class="card-footer">
    <button class="card-footer-item button is-small">▶ Start</button>
    <button class="card-footer-item button is-small">■ Stop</button>
    <button class="card-footer-item button is-small">↻ Restart</button>
    <button class="card-footer-item button is-small">📋 Logs</button>
  </div>
</div>
```

**Điểm lưu ý Bulma:**
- `.card-footer` buttons cần set `border-radius:0` và chia đều bằng flex
- Navbar burger cần JS toggle: `element.classList.toggle('is-active')` trên cả burger + menu
- Modal Bulma: `.modal.is-active` để hiện, `.modal-background` click để đóng
- Theme toggle button fixed góc phải dưới, z-index 999, border-radius 999px

#### Pico CSS (alternative)

Nếu user từ chối Bulma — dùng **Pico CSS** (`@picocss/pico@2`). Classless, responsive sẵn, dark/light built-in.

**CDN:** `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">`

**Cấu trúc HTML:**
```html
<html data-theme="dark">
<body>
<nav class="container">
  <ul><li><strong><a href="/">Site</a></strong></li></ul>
  <ul><li><a href="/dashboard">Dashboard</a></li></ul>
</nav>
<main class="container">
  <article>
    <header>Title</header>
    <p>Content</p>
    <footer>Meta</footer>
  </article>
</main>
</body>
</html>
```

**Override:**
```css
:root{--spacing:.75rem;font-size:15px}
@media(max-width:768px){:root{--spacing:.5rem;font-size:14px}}
```
Pico biến: `--pico-primary`, `--pico-muted-color`, `--pico-card-background-color`, `--pico-border-radius`, v.v.

**Lưu ý:** Pico bị chê "xấu quá" vì quá minimal. Chỉ dùng khi user đồng ý hoặc yêu cầu nhẹ.

### Landing page pattern

Serve 2 pages from same Node server: landing page (/) + dashboard (/dashboard).

```
public/
├── index.html           # Landing (served at /)
└── dashboard.html       # Dashboard (served at /dashboard)
```

Server routing:
```javascript
if (u.pathname === '/dashboard') {
  u.pathname = '/dashboard.html';
}
// Static files
let filePath = u.pathname === '/' ? '/index.html' : u.pathname;
filePath = path.join(__dirname, 'public', filePath);
```

Landing page: hero + about + services live-fetch (`/api/services`), dark theme, responsive, semantic HTML for AI readability.

### Reverse proxy endpoint

Proxy tới service web UI khác trên localhost:
```javascript
const mProxy = u.pathname.match(/^\/proxy\/(\d+)(\/.*)?$/);
if (mProxy && method === 'GET') {
  const targetPort = parseInt(mProxy[1], 10);
  const targetPath = mProxy[2] || '/';
  const opts = { hostname: 'localhost', port: targetPort, path: targetPath, method: 'GET', timeout: 10000 };
  const r = http.request(opts, (r2) => { res.writeHead(r2.statusCode, { ... }); r2.pipe(res); });
  r.on('error', () => { res.writeHead(502); res.end('Proxy error'); });
  r.end();
  return;
}
```

Card link 🔗 tới proxy:
```javascript
const link = s.port > 0 ? ` href="/proxy/${s.port}/" target="_blank"` : '';
${s.port > 0 ? `<a class="card-port"${link}>:${s.port} 🔗</a>` : '<span class="card-port">—</span>'}
```

### Auto-start on Windows boot (no admin needed)

Dùng User Startup folder thay vì Task Scheduler (schtasks yêu cầu admin):
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\startup.bat
```
Content: start dashboard + tunnel, chạy mỗi user login.

### Backup config

Python backup script (cron job với `no_agent=true`):
- Copy server.js, services.json, public/*.html, tunnel configs → `~/.btdat-backup/YYYYMMDD_HHMM/`
- Giữ 30 bản gần nhất
- Schedule: daily 3AM

## Reference Files

- `references/session-detail.md` — SSE implementation, ring buffer, testing commands (v1.0)
- `references/v2-scan-and-tabs.md` — Port scanning, tab system, CRUD, GET vs POST fix (v2.0)

## Document management system

Trang `/documents` + API `/api/documents/*` — quản lý tài liệu markdown (.md) và Word (.docx), lưu file trong `~/documents/`. AI assistant có thể đọc/ghi file trực tiếp bằng tool file — mỗi lần session mới có thể đọc lại, tiếp tục, chỉnh sửa document cũ.

**Workflow:**
1. User yêu cầu AI viết tài liệu → AI tạo file .md (qua API POST) hoặc .docx (qua python-docx, viết vào `~/documents/`)
2. User mở `btdat.io.vn/documents` trên browser → thấy file trong danh sách (hiển thị badge MD hoặc DOCX)
3. Tap để đọc:
   - .md → marked@5 render markdown → HTML article view
   - .docx → mammoth@1 convert .docx → HTML (client-side, arrayBuffer từ base64 API)
4. ✏️ Edit (chỉ .md) → full-screen split editor với live preview, save lưu lại `~/documents/`
5. ⬇ Download → tải file gốc (.md hoặc .docx) về máy
6. Session sau AI có thể đọc lại file bằng tool file để tiếp tục

### File format

**.md files** — YAML frontmatter:
```markdown
---
title: Tiêu đề
date: 2026-07-23
tags: tag1, tag2
---

Nội dung markdown...
```

**.docx files** — Word document, tạo bằng python-docx (`from docx import Document`), lưu trực tiếp vào `~/documents/`. Title lấy từ filename (bỏ .docx). Tag mặc định "docx".

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/documents` | List all .md + .docx files with metadata + `ext` field |
| GET | `/api/documents/:id` | Get content (.md → raw text; .docx → base64) + `ext` |
| GET | `/api/documents/:id?dl=1` | Download raw file (Content-Disposition attachment) |
| POST | `/api/documents` | Create new .md (title, content, tags) |
| PUT | `/api/documents/:id` | Update .md content (preserves existing frontmatter) |
| DELETE | `/api/documents/:id` | Delete file (.md or .docx) |

### Backend: listing both formats

```javascript
const files = fs.readdirSync(DOCS_DIR).filter(f => f.endsWith('.md') || f.endsWith('.docx')).sort().reverse();
const list = files.map(f => {
  const ext = path.extname(f).toLowerCase();
  const stat = fs.statSync(path.join(DOCS_DIR, f));
  if (ext === '.docx') {
    return { id: f.replace(/\.docx$/, ''), file: f, title: f.replace(/\.docx$/, ''), created: stat.birthtime.toISOString(), tags: 'docx', size: stat.size, ext: 'docx' };
  }
  // .md: parse frontmatter...
  return { id, title, created, tags, size, ext: 'md' };
});
```

### Backend: serving .docx (base64) + download (`?dl=1`)

```javascript
// Serve .docx as base64 for mammoth.js client-side rendering
if (isDocx) {
  const buf = fs.readFileSync(filePath);
  return json(res, { id: baseName, content: buf.toString('base64'), ext: 'docx', size: buf.length });
}
// Download handler — trước content handler
if (isDl) {
  const buf = fs.readFileSync(filePath);
  const mime = ext === '.docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : 'text/markdown';
  res.writeHead(200, { 'Content-Type': mime, 'Content-Disposition': 'attachment; filename="' + path.basename(filePath) + '"', 'Content-Length': buf.length });
  return res.end(buf);
}
```

### Frontend: CDN dependencies

```html
<script src="https://cdn.jsdelivr.net/npm/marked@5/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mammoth@1/mammoth.browser.min.js"></script>
```

`marked@5` sync (tránh async bug từ marked@12+). `mammoth@1` — .docx → HTML client-side.

### Frontend: render logic (dispatch by ext)

```javascript
if (currentExt === 'docx') {
  $('article').innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Đang tải...</p>';
  const result = await mammoth.convertToHtml({
    arrayBuffer: Uint8Array.from(atob(d.content), c => c.charCodeAt(0)).buffer
  });
  $('article').innerHTML = result.value;
} else {
  renderArticle(d.content || ''); // marked.parse
}
```

Base64 → ArrayBuffer: `Uint8Array.from(atob(str), c => c.charCodeAt(0)).buffer`

### Frontend: full architecture (`public/documents.html`)

- **Sidebar:** search input (oninput → filterList) + doc list render + count footer
- **Reader:** article layout max-width 680px, clean blog/Medium style
- **Reader header:** title + meta (date, tags) + actions (Download, Edit, Delete)
- **Full-screen editor overlay** (chỉ .md files):
  - Trái textarea 50% width, phải live preview 50%
  - Mobile: xếp dọc (textarea trên 50% height, preview dưới 50%)
  - Live preview update qua `input` event listener
  - Ctrl+S lưu + đóng editor
  - Tags input lưu metadata tự động
- **Mobile:** sidebar 100% khi chưa chọn; tap doc → sidebar ẩn, reader full màn + ← back
- **Unsaved changes warning:** `confirmUnsaved()` trước khi chuyển doc khi editing
- **Search** real-time lọc list theo title + tags
- **Badge** hiển thị DOCX / MD bên cạnh title trong list

### Mobile layout (sidebar toggle) — CSS + JS

```css
@media(max-width:720px){
  .sidebar{width:100%;height:100%;border-right:none}
  .main{position:fixed;inset:52px 0 0;z-index:100;background:var(--bg);display:none;flex-direction:column}
  .main.show{display:flex}
  .sidebar.hide{display:none}
}
```

```javascript
if(window.innerWidth <= 720){
  $('#sidebar').classList.add('hide');
  $('#reader').classList.add('show');
  $('#back-btn').style.display = '';
}
function showList(){
  $('#sidebar').classList.remove('hide');
  $('#reader').classList.remove('show');
  $('#back-btn').style.display = 'none';
}
```

### Frontmatter parsing (server-side)

```javascript
const m = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
const meta = {};
if (m) {
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.+)/);
    if (kv) meta[kv[1]] = kv[2].replace(/^['"]|['"]$/g, '');
  }
}
```

### Path safety

Always check `filePath.startsWith(DOCS_DIR)` to prevent path traversal. Apply for both .md and .docx paths.

## Cloudflare Web Analytics

Free, privacy-first analytics integration (no cookie banner needed).

**Add to `<head>` of every page:**
```html
<!-- Cloudflare Web Analytics -->
<script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "<your-token>"}'></script>
<!-- End Cloudflare Web Analytics -->
```

Enable via Cloudflare Dashboard → domain → Analytics → Web Analytics → Add site.
