# Standalone Demo Pages at Custom Routes (service-dashboard)

> Pattern used 2026-08-26 to expose `/liquid-glass` at https://btdat.io.vn/liquid-glass

## Workflow: add a standalone HTML demo at any path (e.g. /liquid-glass, /lab/*)

1. **Create HTML** in `dist/documents/<name>.html` (or `public/<name>.html` if static asset). `dist/documents/` is auto-created and served under `/documents/<name>.html` but NOT under custom path.

2. **Patch `server.js` BEFORE SPA fallback** (insert between `/rune/` handler and `// Redirect — for SPA routes`):
```js
// ── <Name> demo at /<route> ──
if (u.pathname === '/liquid-glass' || u.pathname === '/liquid-glass/') {
  const lgPath = path.join(__dirname, 'dist', 'documents', 'liquid-glass-apple.html');
  if (fs.existsSync(lgPath)) {
    fs.readFile(lgPath, (err, data) => {
      if (err) { res.writeHead(500); res.end('read error'); return; }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store, must-revalidate' });
      res.end(data);
    });
    return;
  }
}
```
- Must be **before** `// Try Vite build assets` and SPA fallback, otherwise `!hasExt` fallback serves `dist/index.html`.
- Use `path.join(__dirname, 'dist', 'documents', ...)` — `__dirname` is `C:/Users/datel/service-dashboard`.

3. **Restart server** — `server.js` is not hot-reloaded:
```bash
taskkill /PID <pid> /F   # find pid via: netstat -ano | grep ":3000.*LISTEN"
# then background start (use terminal background=true, notify_on_complete=true):
node server.js   # in C:/Users/datel/service-dashboard
# verify:
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/<route>  # expect 200
curl -s http://localhost:3000/<route> | head -c 200  # check correct HTML, not SPA index.html
```

## Pitfalls
- `taskkill -f -im node.exe` kills ALL node including RAG 20128 — never use. Kill only PID on :3000.
- `fs.existsSync` check is sync but `fs.readFile` is async — must `return` immediately after calling it to avoid falling through to SPA handler.
- Cloudflare Tunnel forwards to `localhost:3000`, so local 200 = public 200 (no extra Cloudflare config).
- If deploying multiple routes, add each `if` block separately or use `startsWith('/lab/')` prefix match with `path.join` sanitization.
