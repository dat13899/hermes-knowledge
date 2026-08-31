# SPA Fallback Pattern — React + Vite on Vanilla Node.js HTTP Server

**When:** Migrating from vanilla HTML files to a React + Vite SPA, where the backend is a pure `http` module server (no Express).

**Problem:** The server's `serveStatic()` checks `isSafePath(PUBLIC_DIR, ...)` which rejects paths outside `public/`. Vite build outputs to `dist/` (sibling of `public/`), so you can't use the existing `serveStatic()` for the SPA.

**Key constraints:**
- Old `.html` files must keep working (backward compat)
- New SPA routes (`/`, `/dashboard`, `/documents`, etc.) serve React
- API endpoints (`/api/...`) and proxy routes (`/proxy/...`) must work unchanged
- Vite's JS bundle at `/assets/index-*.js` needs proper Content-Type and caching

## Solution Architecture

```
server.js (http module)
├── Route handlers (API, documents, etc.) — unchanged
├── .html redirect block — intercept BEFORE old redirect logic
├── Vite asset handler — serve dist/assets/*.js with immutable cache
└── Static handler — serve old public/ files unchanged
```

## Exact Implementation

### 1. Route intercept BEFORE old .html redirect

The original server had a redirect block like:
```js
if (u.pathname === '/dashboard' || ...) {
  u.pathname = u.pathname + '.html';
}
```

Replace with SPA-aware intercept:
```js
// SPA routes — serve React build if available
const SPA_ROUTES = new Set(['/', '/dashboard', '/documents', '/utilities', '/random-widget', '/hermes']);
if (SPA_ROUTES.has(u.pathname) || SPA_ROUTES.has(u.pathname.replace(/\/$/, ''))) {
  const spaPath = path.join(__dirname, 'dist', 'index.html');
  if (fs.existsSync(spaPath)) {
    fs.readFile(spaPath, (err, data) => {
      if (!err) {
        res.writeHead(200, {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-store, must-revalidate',
        });
        res.end(data);
      }
    });
    return; // ← MUST return to prevent falling through to old handler
  }
}
```

**Important:** Use `fs.readFile` directly, NOT `serveStatic()`, because `serveStatic()` calls `isSafePath(PUBLIC_DIR, ...)` which rejects `dist/`.

### 2. Vite JS asset handler

Add BEFORE the main static handler:
```js
// Vite build assets from dist/ (immutable cache)
if (u.pathname.startsWith('/assets/') && u.pathname.endsWith('.js')) {
  const distAsset = path.join(__dirname, 'dist', u.pathname);
  if (fs.existsSync(distAsset)) {
    fs.readFile(distAsset, (err, data) => {
      if (!err) {
        res.writeHead(200, {
          'Content-Type': 'text/javascript; charset=utf-8',
          'Cache-Control': 'public, max-age=31536000, immutable',
        });
        res.end(data);
      }
    });
    return;
  }
}
```

### 3. Final fallback (old HTML or 404)
```js
// Static file from public/
let filePath = u.pathname === '/' ? '/index.html' : u.pathname;
filePath = path.join(PUBLIC_DIR, filePath);
if (isSafePath(PUBLIC_DIR, filePath) && fs.existsSync(filePath)) {
  serveStatic(res, filePath);
  return;
}

// SPA fallback for unrecognized paths (if not API and no extension)
if (!u.pathname.startsWith('/api/') && !path.extname(u.pathname)) {
  const spaPath = path.join(__dirname, 'dist', 'index.html');
  if (fs.existsSync(spaPath)) {
    fs.readFile(spaPath, (err, data) => {
      if (!err) { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(data); }
    });
    return;
  }
}
```

## Vite Config

```js
// frontend/vite.config.js
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: '../dist',      // output to project root/dist/
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:3000',    // proxy to real backend
      '/assets': 'http://localhost:3000', // global.css, theme.js, favicon
      '/hermes': 'http://localhost:3000', // canvas visualizer scripts
      '/proxy': 'http://localhost:3000',  // service proxy routes
    },
  },
});
```

## Build & Deploy Cycle

```bash
cd frontend
npm run build         # outputs to ../dist/
# Restart node server to pick up new dist/
```

## Verification

```bash
# React SPA routes
curl -s http://localhost:3000/ | grep -c 'id="root"'   # → 1
curl -s http://localhost:3000/dashboard | grep -c 'id="root"'  # → 1

# Vite JS bundle accessible
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/assets/index-*.js  # → 200

# Old HTML still works
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/hermes.html  # → 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/dashboard.html  # → 200

# API routes work
curl -s http://localhost:3000/api/services | head -c 100  # → [{...\n

# Cache headers correct
curl -sI http://localhost:3000/ | grep -i cache-control  # → no-store
curl -sI http://localhost:3000/assets/index-*.js | grep -i cache-control  # → max-age=31536000
```

## Windows Pitfalls

### `path.resolve` vs `path.join` for SPA route paths

On Windows (Node.js), `path.resolve(base, target)` treats a `target` argument starting with `/` as an **absolute path**, replacing the base entirely:

```js
// WRONG — returns C:\stream (treats /stream as absolute)
path.resolve('C:\\Users\\...\\public', '/stream')
// → 'C:\\stream'

// RIGHT — returns C:\Users\...\public\stream (joins correctly)
path.join('C:\\Users\\...\\public', '/stream')
// → 'C:\\Users\\...\\public\\stream'
```

**Impact:** The SPA fallback check `!isSafePath(PUBLIC_DIR, filePath)` uses `path.resolve` internally. When requesting a path like `/stream`, `path.resolve(PUBLIC_DIR, '/stream')` resolves to `C:\stream` which does NOT start with `PUBLIC_DIR` → 403 Forbidden.

**Fix — use `filePath.startsWith()` instead of `path.resolve`-based `isSafePath`:**
```js
// ❌ Broken on Windows for SPA routes
if (!isSafePath(PUBLIC_DIR, filePath)) { res.writeHead(403); ... }

// ✅ Safe — path.join already normalizes correctly
filePath = path.join(PUBLIC_DIR, u.pathname);
if (!filePath.startsWith(PUBLIC_DIR)) { res.writeHead(403); ... }
```

**Same issue in `serveStatic()`:** When the SPA fallback calls `serveStatic(res, spaPath)` where `spaPath = path.join(__dirname, 'dist', 'index.html')`, the same `isSafePath(PUBLIC_DIR, spaPath)` check rejects it because `dist/` is not under `public/`.

**Fix — allow `index.html` paths outside PUBLIC_DIR:**
```js
function serveStatic(res, filePath) {
  if (!filePath.startsWith(PUBLIC_DIR) && !filePath.endsWith(path.sep + 'index.html'))
    { res.writeHead(403); res.end('Forbidden'); return; }
  …
}
```

**Prevention:** Never use `path.resolve` for security checks on Windows when the second argument could start with `/`. Prefer `path.join` + `String.prototype.startsWith()` — `path.join` strips leading slashes from non-first arguments, so the path stays under the intended base directory.
