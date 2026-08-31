# btdat.io.vn server.js deploy routing

Server tại `C:\Users\datel\service-dashboard\server.js` (port 3000, fronted by Cloudflare Tunnel).

## Two file-serving directories

| Directory | Path | Purpose |
|---|---|---|
| `DOCS_DIR` | `C:\Users\datel\documents` | API-driven document upload/read (`/api/documents/...`) |
| `PUBLIC_DIR` | `C:\Users\datel\service-dashboard\public` | Direct static file serving |

## Key routing order (handler chain near end of server.js)

1. **API routes** (`/api/...`) — handled first
2. **SPA routes** (line 731) — if pathname matches `/documents`, `/dashboard`, `/utilities`, etc → serve `dist/index.html` (React SPA)
3. **Static files** (line 882) — `PUBLIC_DIR + pathname`, 403 if escapes `PUBLIC_DIR`
4. **SPA fallback** (line 891) — any route without `.ext` and not `/api/` → serve `dist/index.html`

## Why `/documents/vtts/` doesn't work for HTML files

Path `/documents/vtts/` matches step 2 (SPA route `/documents/` prefix) → React `index.html` is served instead of the actual file. HTML files hosted under `/documents/` are consumed by SPA.

## Right way: `public/` directory

- Put HTML file in `C:\Users\datel\service-dashboard\public\<name>.html`
- Access via `https://btdat.io.vn/<name>.html`
- For clean URLs like `/vtts`, add a redirect in the `// Static` block:

```js
// Static
let filePath = u.pathname === '/' ? '/index.html' : u.pathname;
if (u.pathname === '/vtts') filePath = '/vtts-drive.html';  // clean URL → real file
filePath = path.join(PUBLIC_DIR, filePath);
```

## Restart after editing server.js

```bash
# Find PID
netstat -ano | grep ":3000.*LISTENING"
# Kill
taskkill /F /PID <pid>
# Restart (auto by cloudflared tunnel monitor, or manual)
cd /c/Users/datel/service-dashboard && node server.js
```

Server PID is also written to `C:\Users\datel\AppData\Local\hermes\scripts\.server-pid`.
