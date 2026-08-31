# v2.0 — Port Scan & Tab System (session 2026-07-11)

## Context

Anh Đạt's dashboard project at `C:\Users\datel\service-dashboard\` manages:
- AFK Bot (aterbot, port 5500)
- Player Bot (aterbot-player, port 5501)

Session added: tab system, port scanning, service CRUD via UI.

## services.json (unchanged schema)

```json
[
  {
    "id": "aterbot",
    "name": "AFK Bot",
    "description": "Minecraft AFK bot — tự động reconnect, tránh idle kick",
    "dir": "C:\\Users\\datel\\aterbot",
    "command": "cmd.exe /c npm start",
    "port": 5500
  }
]
```

## Tab Implementation

Frontend uses `display: none` / `display: block` tab switching:

```js
// Tab click handler
$$('.tab').forEach(tab => tab.addEventListener('click', () => {
  $$('.tab').forEach(t => t.classList.remove('active'));
  $$('.tab-content').forEach(tc => tc.classList.remove('active'));
  tab.classList.add('active');
  $(`#tab-${tab.dataset.tab}`).classList.add('active');
  if (tab.dataset.tab === 'scan') runScan();  // auto-trigger scan
}));
```

- Priority tab: renders cards from `/api/services` (polled every 3s)
- Scan tab: calls `/api/scan` on activation, shows discovered ports in same card grid CSS

## Scan API Detail

**`GET /api/scan`** returns:

```json
[
  {"port": 9119, "pid": 10940, "name": "python.exe"},
  {"port": 63119, "pid": 10940, "name": "python.exe"}
]
```

Known ports excluded from output:
- Ports from `services.json` (e.g. 5500, 5501)
- Dashboard port (3000)
- System ports < 1024
- Known Windows system ports: 135, 445, 3389, 5040, 5357, 7680, 8644, 20128, 49664–49675

## Add/Delete Service

**Add modal** (frontend):

```
Form fields:
  - Tên service *      (string, required)
  - Port *              (number, required)
  - Thư mục làm việc   (string, optional)
  - Câu lệnh chạy       (string, optional)
  - Mô tả               (string, optional)
```

**Validation** (backend):
- `id` auto-generated from name (lowercased, non-alphanum → hyphens)
- Rejects if id or port already exists
- Empty dir + command allowed (monitor-only service)

**Delete**: calls `confirm()` first, then `DELETE /api/services/:id`.

## State Persistence Rules

- `saveServices()` rewrites `services.json` to disk on every add/delete
- `reloadServices()` re-reads disk but preserves running processes that still exist
- Memory state (`S` Map) is the source of truth for process lifecycle

## Frontend Pattern: API Helper

```js
async function api(path, opts = {}) {
  try {
    const r = await fetch(path, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...opts.headers }
    });
    if (!r.ok) return { error: `HTTP ${r.status}` };
    return r.json();
  } catch (e) {
    return { error: e.message };
  }
}
```

**Key**: always returns `{error}` on failure, never throws. Callers check `res?.error`.

## Bug Fixed: GET vs POST

Original `act()` called `api()` without method → defaulted to GET. Server checked `method === 'POST'` → fell through to static file handler → 404 HTML → silent failure.

Fix: explicit `{ method: 'POST' }` on every start/stop/restart call.

```js
// Before (broken):
res = await api(`/api/services/${id}/start`);

// After (fixed):
res = await api(`/api/services/${id}/start`, { method: 'POST' });
```

## CORS

Server sets `Access-Control-Allow-Origin: *` and allows `GET, POST, DELETE, OPTIONS`. DELETE needed explicit addition to the allowed methods list.
