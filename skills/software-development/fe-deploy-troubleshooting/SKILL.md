---
name: fe-deploy-troubleshooting
title: FE deploy troubleshooting — cache, SW, theme, responsive
description: >
  Fix recurring FE deploy issues: SW caching stale HTML, ERR_HTTP_HEADERS_SENT
  proxy crash, theme button double-toggle, Bulma class conflicts, kb-hint/skip-link
  residual, server restart verification.
category: software-development
trigger:
  - site cũ sau deploy
  - theme nút không đổi
  - bấm theme bounce lại
  - SW cache
  - layout hỏng do class button
  - 502 ERR_HTTP_HEADERS_SENT
  - React SPA serve 403 Forbidden
  - Vite build không load trên server
  - SPA fallback
  - migration vanilla → React
  - CSS 404 (endsWith .js filter)
  - ErrorBoundary Có lỗi xảy ra
  - static asset handler not serving CSS
  - server.js filter blocking assets
  - DNS_PROBE_FINISHED_NXDOMAIN
  - .io.vn không vào được
  - ISP VN chặn domain
  - Cloudflare cache 404 poisoning
  - Vite hash mới bị CF cache 404 cũ
  - hook return value undefined
  - docsCtrl.allTags undefined
  - useMemo missing from hook return
  - DocSidebar crash
  - searchQuery undefined
  - props không khớp
  - props not passed to child
  - child component renders but crashes
  - default props missing
  - prop name mismatch
  - parent passes onSelect but child expects onSelectDoc
  - Child/ChildName API mismatch
  - docx hiển thị lỗi
  - file .docx không xem được
  - convert docx sang pdf
  - SPA nuốt file HTML trong /documents/
  - public folder serve file tĩnh
  - btdat.io.vn server routing
  - server.js restart deploy
  - LibreOffice soffice convert
  - binary format viewer
  - ReferenceError: time is not defined
  - Runtime Error Uncaught ReferenceError
  - hermes visualizer crash
  - updateStardust drawStardust time not defined
  - canvas page white / error overlay after deploy
version: "2.1"
---

# FE Deploy Troubleshooting

## Hermes visualizer crash — `ReferenceError: time is not defined`

Symptom: `/hermes` page shows an iframe error overlay: `Uncaught ReferenceError:
time is not defined at updateStardust (hermes-visuals.js:2129) at loop
(hermes-main.js:48)`.

Root cause: `loop(time)` in hermes-main.js passes `time` to every draw fn, but
`updateStardust(dt)` and `drawStardust()` reference `time` WITHOUT declaring it
as a parameter — so inside their scope `time` is undefined. Same class of bug:
any helper that uses a value from the caller's scope but doesn't receive it.

Fix:
```js
// hermes-main.js
updateStardust(dt, time);
drawStardust(time);
// hermes-visuals.js
function updateStardust(dt, time){...}
function drawStardust(time){...}
```
Verify with `node --check` on both files, then deploy.

### ⚠️ Cloudflare serves stale JS even after fixing the file
`public/*.js` gets `Cache-Control: public, max-age=14400` (4h) and Cloudflare
caches it (`cf-cache-status: HIT`, `Age: N`). Editing the file in place does
NOT reach users — even curl through the tunnel may return the OLD bytes while
`curl ?v=999` (cache-busted) returns NEW bytes. **Fix: rename the file**
(`hermes-visuals.js` → `hermes-visuals-v2.js`) and update all HTML references
(`hermes.html` + `hermes-standalone.html`).

### ⚠️ Bulk-replacing script tags can mangle HTML
`replace_all` on a multi-line `<script>` block in an HTML file can duplicate/
corrupt adjacent lines (seen: `</script>` fragments multiplied). After any
bulk script-tag replace, re-read the block and confirm the full sequence
(core → visuals → theme → main) is intact, no stray fragments.


**Cause A**: Service Worker cache HTML pages (MOST COMMON)
- SW intercept `/dashboard` → server redirect 302 → SW cache redirect response
- Every subsequent navigation serves STALE redirect → never sees new code
- **Fix A1 (FINAL STATE)**: Xoá SW hoàn toàn. Delete `sw.js`, remove `<link rel="manifest">`, remove ALL `navigator.serviceWorker.register()`. Final codebase has zero SW trace. Verify: `grep -rn "serviceWorker\|sw\.js" public/ --include="*.html" --include="*.js"` → 0 matches.
  - Also remove special-case `path.basename(filePath) === 'sw.js'` from server.js static handler.
  - Delete manifest.json if exists.
- **Fix A2 (MIGRATION ONLY)**: SW self-destruct pattern — deploy `sw.js` that clears ALL caches then unregisters itself. Only use when existing SW is already deployed and users need 1 F5 to clear it. After migration completes, apply Fix A1.
  ```js
  self.addEventListener('install',function(e){self.skipWaiting()});
  self.addEventListener('activate',function(e){
    e.waitUntil(
      caches.keys().then(function(ks){return Promise.all(ks.map(function(k){return caches.delete(k)}))}).then(function(){
        return self.registration.unregister();
      })
    );
  });
  self.addEventListener('fetch',function(e){e.respondWith(fetch(e.request))});
  ```
  Deploy + re-register on pages (`navigator.serviceWorker.register('/sw.js')`). User 1 F5 triggers update. SW nukes itself.
  - **Server Cache-Control for sw.js**: `no-store, must-revalidate`, check `path.basename(filePath) === 'sw.js'`.
- **Clear cache button**: Add `clearCacheAndSW()` function to all pages. Gives users manual way to nuke browser cache on any device:
  ```js
  function clearCacheAndSW(){
    if('caches' in window){caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k)))).then(()=>{toast('Cache cleared','success')})}
    setTimeout(()=>location.reload(),500);
  }
  ```
  Place button in footer or navbar: clear cache icon
- Verify: `Cache-Control: no-store, must-revalidate` trên HTML

**Cause B**: Browser cache
- Fix: `Ctrl+F5` (hard reload)
- Server: set `Cache-Control` header phù hợp

**Cause C**: Cloudflare cache
- Cloudflare Tunnel serve page cũ nếu server restart không kèm tunnel restart
- Fix: Kill + restart cả node lẫn cloudflared

**Cause D (COMMON)**: Cloudflare edge cache CSS + JS
- CF caches static assets aggressively at edge. Hard reload (Ctrl+F5) still loads stale content.
- **Fix**: Add `?v=N` query param to EVERY asset `<link>` and `<script>` tag (both `/assets/global.css?v=2` and `/assets/theme.js?v=2`). Bump N on each deploy. Patch all pages.
- **`?v=N` still not enough** — CF can cache `theme.js?v=2` at edge from a previous deploy. User gets stale JS even after bumping to `?v=3`. **Must purge CF cache**: Cloudflare Dashboard → Caching → Configuration → Purge Everything. Without CF API token, manual purge via dashboard is the only option.
- **Symptoms of stale JS at CF edge**:
  - Page content renders fine in `curl` but browser shows **blank or no navbar** → `initNavbar()` in cached `theme.js` is old version or never loaded. User says "navbar mất rồi".
  - `.reveal` elements stuck at `opacity:0` because IntersectionObserver code in old `theme.js` never loaded.
  - **Hard refresh (Ctrl+F5) doesn't fix it** — CF edge cache bypasses browser cache entirely for subsequent hits.
  - **Differentiation from other navbar issues**: If `curl -s https://domain.com/navbar.html` shows correct template AND `curl -s https://domain.com/assets/theme.js?v=N | grep initNavbar` returns >0 matches, problem is CF edge serving stale `theme.js`. Purge CF cache.
- **Verify**:
  ```bash
  curl -s https://domain.com/ | grep "global.css"       # must show ?v=N
  curl -s https://domain.com/ | grep "theme.js"         # must show ?v=N
  curl -s https://domain.com/assets/theme.js?v=N | grep "initNavbar\|IntersectionObserver"  # must match latest code
  ```

## 2. Theme button không đổi / bounce dark→light→dark

**Root cause**: Multiple click handlers.
- `.addEventListener('click', toggle)` + delegation `e.target.closest('.theme-btn')` + MutationObserver
- 1 click → toggle runs 2+ times → `light→dark→light`

**Fix**: Chỉ dùng `onclick="toggleTheme()"` attribute. theme.js không có .addEventListener.

**Verify**: Mở DevTools → Elements → click button → check `data-theme` attribute on `<html>`. Phải flip mỗi lần click.

## 3. Layout hỏng do Bulma class xung đột

**Symptom**: Button không đúng vị trí, style sai.

**Cause**: Element có cả class custom (`.theme-btn`) lẫn Bulma class (`.button`). Bulma `.button` đặt position, padding, font riêng.

**Fix**: Dùng 1 class thôi. Trong navbar dùng `<button class="button is-small" onclick="...">`, không thêm `.theme-btn`.

## 4. Residual kb-hint / skip-link

Các pattern đã xoá khỏi codebase. Grep `kb-hint\|skip-link` trên cả 3 pages. Nếu >0 → fail.

## 5. ERR_HTTP_HEADERS_SENT — Server crash

**Symptom**: Node process die, `ERR_HTTP_HEADERS_SENT` stack trace, site 502.

**Root cause**: Proxy handlers call `res.writeHead()` / `json(res)` multiple times. Common pattern:

```js
// BUG: r.destroy() triggers 'error' event → both handlers call json()
r.on('error', () => json(res, { ok: false }));
r.on('timeout', () => { r.destroy(); json(res, { ok: false }); });
```

**Fix**: `timedOut` flag + `try/catch` + `headersSent` guard — apply all 3.

```js
// Fix A — timedOut flag (prevents race between timeout & error)
let timedOut = false;
r.on('error', () => { if (!timedOut) json(res, { ok: false }); });
r.on('timeout', () => { timedOut = true; r.destroy(); json(res, { ok: false }); });

// Fix B — try/catch for direct res.writeHead
r.on('error', () => { try { res.writeHead(502); res.end('Proxy error'); } catch (_) {} });

// Fix C — guard in json() itself
function json(res, data, code = 200) {
  if (res.headersSent) return;
  ...
}
```

After: `timedOut` prevents error handler after timeout. `try/catch` catches races. `headersSent` is last resort.

## 6. Server restart sequence

1. `process(action='kill', session_id=...)` kill current
2. `terminal(cmd='cd ~/service-dashboard && node server.js', background=true)`
3. `sleep 2 && curl -s http://localhost:3000/api/version` verify
4. For each page: `curl -s -o /dev/null -w '%{size_download}' http://localhost:3000/PATH`
5. Check `Cache-Control` header: `curl -sI http://localhost:3000/ | grep -i cache-control`

## 7. SPA Fallback — React + Vite on Vanilla Node.js HTTP

**Symptom:** `/` and `/dashboard` serve old `.html` files instead of the React SPA, or return 403 "Forbidden".

**Root cause:** The server's `serveStatic()` checks `isSafePath(PUBLIC_DIR, ...)` and rejects `dist/index.html` since it's outside `public/`.

**Full reference:** `fe-deploy-troubleshooting/references/spa-fallback-pattern.md`

**Quick checklist:**
1. SPA route intercept must come BEFORE old `.html` redirect
2. Must use `fs.readFile`, not `serveStatic()`, for `dist/` files
3. Vite assets at `/assets/*` need their own handler — serve ALL types (`.js`, `.css`, `.svg`, `.png`, `.jpg`, `.woff2`, `.woff`), NOT just `.js`. 🚨 Missing CSS → site renders without styles → React may crash into ErrorBoundary → user sees "Có lỗi xảy ra" even though JS loads fine. See MIME map pattern below.
4. Old `.html` files must still be accessible directly (`.html` suffix)
5. Vite proxy config: API → localhost:3000, assets → localhost:3000, hermes → localhost:3000

**Config pattern:**
```js
// frontend/vite.config.js
build: { outDir: '../dist', emptyOutDir: true }
server: { proxy: { '/api': 'http://localhost:3000' } }
```

**Server SPA intercept pattern:**
```js
const SPA_ROUTES = new Set(['/', '/dashboard', '/documents', ...]);
if (SPA_ROUTES.has(u.pathname)) {
  const spaPath = path.join(__dirname, 'dist', 'index.html');
  if (fs.existsSync(spaPath)) {
    fs.readFile(spaPath, (err, data) => {
      if (!err) { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(data); }
    });
    return; // CRITICAL: return to prevent old .html redirect
  }
}
```

**🚨 PITFALL: `.endsWith('.js')` filter on asset handler**
The most common Vite migration mistake: the static asset handler has `u.pathname.endsWith('.js')`, blocking `.css`, `.svg`, fonts. This produces a deceptive failure: JS loads fine, page renders, but without CSS → React crashes into ErrorBoundary → user sees "Có lỗi xảy ra" even though:
- `curl https://btdat.io.vn/` → 200 OK with correct HTML
- `curl https://btdat.io.vn/assets/index-*.js` → 200 OK  
- `curl https://btdat.io.vn/assets/index-*.css` → **404** ← CSS blocked!

**Correct pattern (serve ALL asset types with MIME):**
```js
if (u.pathname.startsWith('/assets/')) {
  const distAsset = path.join(__dirname, 'dist', u.pathname);
  if (fs.existsSync(distAsset)) {
    const ext = path.extname(distAsset).toLowerCase();
    const mime = ext === '.js' ? 'text/javascript; charset=utf-8'
      : ext === '.css' ? 'text/css; charset=utf-8'
      : ext === '.svg' ? 'image/svg+xml'
      : ext === '.png' ? 'image/png'
      : ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg'
      : ext === '.woff2' ? 'font/woff2'
      : ext === '.woff' ? 'font/woff'
      : 'application/octet-stream';
    fs.readFile(distAsset, (err, data) => {
      if (!err) {
        res.writeHead(200, { 'Content-Type': mime, 'Cache-Control': 'public, max-age=31536000, immutable' });
        res.end(data);
      }
    });
    return;
  }
}
```

**Diagnostic: verify ALL assets from index.html are reachable:**
```bash
for path in $(grep -oP '(?:src|href)="(/assets/[^"]+)"' dist/index.html | cut -d'"' -f2 | sort -u); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$path")
  echo "$code $path"
done
# ALL must be 200. Any 404 = asset handler filters that file type.
```

## 8. Bump static asset version across all pages

When deploying CSS/JS changes that Cloudflare caches at edge:

```bash
# Bump ?v=N on all pages atomically
cd public/
for f in index.html dashboard.html documents.html utilities.html random-widget.html; do
  sed -i 's/theme.js?v=2/theme.js?v=3/g; s/global.css?v=2/global.css?v=3/g' "$f"
  echo "Fixed $f"
done
```

- Use `?v=3` (or next number), never same version twice
- After bump: `git add -A && git commit -m "fix: bump cache-bust to vN" && git push`
- Restart Node server after push
- If navbar still missing after all steps: **purge CF cache manually** — Cloudflare Dashboard → Caching → Configuration → Purge Everything
- No CF API key available in this setup → skip automated purge

## 9. ErrorBoundary "Có lỗi xảy ra" — React Runtime Crash (NOT server error)

**Symptom**: Page shows "Có lỗi xảy ra / Vui lòng thử tải lại trang" with a retry button. The page loaded (server is fine) but a React component crashed during render.

**Diagnostic checklist** (in order of likelihood after a refactor):
1. **server.js asset handler filters `.js` only** — `grep 'endsWith' server.js` — if `u.pathname.endsWith('.js')` is present, `.css`, `.svg`, fonts are 404. Index page loads, JS runs, but no CSS → React may crash. See Section 7 pitfall for fix.
2. **Duplicate module files** — `ls -la hooks/` — if `useToast.js` AND `useToast.jsx` both exist, Vite resolves the wrong export. Delete the stale file.
3. **`//` comments in imported CSS** — `grep -rn '//' src/pages/**/*.css` — CSS files imported via `import './foo.css'` cannot contain `//` comments. Replace with `/* */`.
4. **Import path mismatches after file moves** — `grep -rn "from '" src/ | sort` — after moving files between directories, relative imports break.
5. **Missing SPA route in server.js** — server.js SPA route list must include EVERY `<Route path="...">` from App.jsx. Missing route → server serves old `.html` → old HTML references non-existent JS.
6. **BottomTab / Navbar link paths mismatch** — verify ALL nav link arrays match App.jsx routes exactly.

**Fix**: `npm run build` → `fuser -k 3000/tcp` → `node server.js` → `curl localhost:3000/ | grep "script src"`.

## 10. server.js SPA route list is a MANUAL sync point

Every new React `<Route path="foo">` requires adding `'/foo'` to server.js, `BottomTab` TABS, and `Navbar` NAV_LINKS. Three places to keep in sync. Verify: `grep -n 'path=' src/App.jsx`.

## 11. DNS_PROBE_FINISHED_NXDOMAIN — Vietnamese ISP blocks `.io.vn`

**.io.vn là domain miễn phí → các ISP lớn tại VN CHẶN DNS resolution.**

| DNS Server | `.io.vn` result |
|---|---|
| Cloudflare (1.1.1.1) | ✅ Resolves OK |
| Google (8.8.8.8) | ✅ Resolves OK |
| **VNPT (203.162.4.1)** | ❌ Query refused |
| **Viettel (203.113.131.1)** | ❌ Query refused |
| **FPT (210.245.24.20)** | ❌ Timeout |

**Symptoms:** User reports DNS_PROBE_FINISHED_NXDOMAIN on ALL devices (PC + phone) despite site being fully operational from foreign IPs. `curl` from server returns 200. `nslookup` from 8.8.8.8 resolves correctly. Cloudflare tunnel healthy. Everything works — EXCEPT user's ISP DNS refuses `.io.vn`.

**Quick fix (user side):** Change DNS to 1.1.1.1 / 8.8.8.8 on device.
**Permanent fix:** Buy a paid domain (`.com`, `.net`, `.dev`, `.me`, `.site` — $5-15/year on Cloudflare Registrar). Paid TLDs are NOT blocked by Vietnamese ISPs.

**Verify ISP blocking:**
```bash
nslookup btdat.io.vn 203.162.4.1   # VNPT
nslookup btdat.io.vn 203.113.131.1  # Viettel
nslookup btdat.io.vn 210.245.24.20  # FPT
# Any response containing "Query refused" or timeout = ISP blocks this TLD
```

## 12. Cloudflare Edge Cache 404 Poisoning (Renamed Vite Assets)

**Symptom:** After fixing a build issue, new asset hashes are generated. Old hashes return 404 from Cloudflare. Browser requesting old `index.html` (CF-cached) references old hashes → 404 cascade.

**Root cause:** Cloudflare caches HTTP 404 at the edge. Even after the server is fixed and serves the file correctly, CF returns the cached 404.

**Diagnostic:**
```bash
# File exists on local server
curl -s http://localhost:3000/assets/index-CJpm7VkC.css  # → 200
# Same file from CF
curl -s https://btdat.io.vn/assets/index-CJpm7VkC.css    # → 404 (CF cached!)
# But with cache-bust query param → 200
curl -s "https://btdat.io.vn/assets/index-CJpm7VkC.css?v=$(date +%s)"  # → 200
```

**Fix A — rebuild with content change (no CF API token needed):** Add a real CSS rule (not just a comment — Vite hashes on content, not comments), rebuild → new hash → CF has no cached 404 for the new hash. Example: add `.rebuild-marker{display:none}` to any CSS file, build, deploy. ⚠️ Must be a real CSS rule — comments don't change Vite content hash.

**Fix B — purge CF cache (requires API token):**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"files":["https://btdat.io.vn/assets/index-CJpm7VkC.css"]}'
```

## 13. ErrorBoundary — Hook Return Value Mismatch

**Pattern:** Component accesses `hookReturnValue.property` but the hook's interface doesn't include `property`. `undefined.length` / `undefined.map()` → TypeError → ErrorBoundary "Có lỗi xảy ra".

```jsx
// ❌ useDocuments doesn't return `allTags`
{docsCtrl.allTags.length > 0 && <DocTags allTags={docsCtrl.allTags} />}
// TypeError: Cannot read properties of undefined (reading 'length')
```

**Diagnostic:** Check every `.` access on hook return values against the hook's actual `return {}` block. The hook itself loads fine, the component loads fine — the crash is at access time.

**Fix:** If the property is derivable from existing return values, compute it with `useMemo` in the component:
```jsx
const allTags = useMemo(() => {
  const tags = new Set();
  for (const d of docsCtrl.docs) {
    if (d.tags) {
      const list = Array.isArray(d.tags) ? d.tags : d.tags.split(',').map(t => t.trim()).filter(Boolean);
      list.forEach(t => tags.add(t));
    }
  }
  return Array.from(tags).sort();
}, [docsCtrl.docs]);
// Then use `allTags` instead of `docsCtrl.allTags`
```

### 13a. Props Not Passed To Child Component

**Pattern:** Parent renders a child but DOES NOT pass a prop the child destructures and accesses → `undefined.trim()` / `undefined.map()` or other method call → TypeError → ErrorBoundary "Có lỗi xảy ra".

```jsx
// ❌ Parent (DocumentsPage) renders DocSidebar but NEVER passes `searchQuery`:
<DocSidebar
  docs={docsCtrl.docs}
  activeId={docsCtrl.currentDoc?.id}
  onSelect={handleSelect}
  // ❌ searchQuery MISSING — no prop passed
/>

// Child (DocSidebar) accesses the prop:
export default function DocSidebar({ docs, searchQuery, ... }) {
  // `searchQuery` is undefined because parent never passed it
  const q = searchQuery.trim(); // 💥 TypeError: Cannot read properties of undefined (reading 'trim')
```

**Why this is harder to find than hook mismatch:**
- The child component's own `useState` or variable declarations look correct
- The parent passes SOME props (so the child renders), but not ALL required props
- The crash happens deep inside the child's render logic, not at the import/module level
- ErrorBoundary only shows the generic error message — the stack trace is buried
- `grep -rn "allTags\|searchQuery" src/` shows the CHILD uses it, but doesn't reveal the PARENT never passes it

**Diagnostic workflow (4 steps):**
1. List every prop passed in the parent's JSX: `grep -A 20 "<ChildComponent" parent.jsx`
2. List every destructured parameter in the child: `grep "^export default function" child.jsx`
3. Cross-reference: find props present in child's signature but ABSENT from parent's JSX
4. Those are the crash candidates — any prop accessed via `.method()` or `.property` on `undefined` will crash

**Fix A — defensive defaults (quick, prevents all future crashes):**
```jsx
export default function DocSidebar({
  docs, loading,
  searchQuery = '',           // default → no crash on .trim()
  setSearchQuery = () => {},  // default → no crash on call
  sortBy = 'newest',          // default → valid initial sort
  setSortBy = () => {},
  setSelectedTags = () => {},
  selectedIds = [],            // default → no crash on .includes()
  setSelectedIds = () => {},
  ...other props
}) { ... }
```

**Fix B — pass the prop from parent (structural correctness):**
```jsx
// In parent, add state + pass to child via JSX props:
const [searchQuery, setSearchQuery] = useState('');
<DocSidebar searchQuery={searchQuery} setSearchQuery={setSearchQuery} ... />
```

**Best practice:** Apply BOTH. Fix A prevents ALL current and future missing-prop crashes. Fix B wires the structural data flow correctly.

**Verification after fix:**
```bash
# Verify the built chunk contains the fix
python -c "
js=open('dist/assets/DocumentsPage-*.js').read()
print('Has defaults:', 'searchQuery' in js, 'sortBy' in js)
print('Has useMemo allTags:', 'Array.from' in js and 'new Set' in js)
"
# Also verify the parent JSX passes the props now:
grep -A 15 '<DocSidebar' frontend/src/pages/DocumentsPage.jsx | grep searchQuery
```

**Related patterns (same vulnerability class):**
- `useToastContext` imported but `useToast` is the actual export → `import { useToast }`
- Hook returns `{fetchDocs, createDoc}` but component calls `docsCtrl.fetchAll()` → function not found
- Hook's return shape changed during refactor, caller still references old property names
- **Props passed to child but child destructures wrong field names** — `{ onSelect }` when parent passes `onSelectDoc`
- **Parent passes `docs={docsCtrl}` but child destructures `{ docs, loading }` expecting an object with both`

### 13b. Prop Name Mismatch — Parent and Child Have Different API Versions

**Pattern:** Parent and child were written at different times with DIFFERENT prop contracts — parent passes OLD prop names but child destructures NEW prop names. This is WORSE than 13a because `grep` shows the parent IS passing props — they're just the WRONG NAMES. Every prop accessible via `.method()` on `undefined` will crash.

```jsx
// ❌ Parent (DocumentsPage) uses OLD prop names from previous DocSidebar version:
<DocSidebar
  docs={docsCtrl.docs}
  activeId={docsCtrl.currentDoc?.id}    // child expects: currentDoc
  onSelect={handleSelect}                // child expects: onSelectDoc
  onDelete={(doc) => setDeleteTarget(doc)} // child expects: (nothing — removed)
  onUpload={docsCtrl.uploadDoc}          // child expects: onUploadDoc
  // ❌ searchQuery, sortBy, draftOnly, setSearchQuery, setSortBy ALL MISSING
/>

// ❌ Child (DocSidebar) uses NEW prop names from newer rewrite:
export default function DocSidebar({
  docs,
  currentDoc,           // parent passed: activeId   → undefined
  onSelectDoc,          // parent passed: onSelect    → undefined → click crash
  onUploadDoc,          // parent passed: onUpload    → undefined
  searchQuery,          // parent NEVER passed        → undefined → .trim() crash
  setSearchQuery,       // parent NEVER passed        → undefined
  sortBy,               // parent NEVER passed        → undefined
  setSortBy,            // parent NEVER passed        → undefined
  ...
}) { }
```

**How this happens:** During migration/refactor, child is rewritten with a richer API (integrated search, sort, filter). Parent is NOT updated. The two files hold different prop contract versions.

**Why this is hard to find:**
- `grep -A 20 "<DocSidebar" DocumentsPage.jsx` shows MANY props — looks complete
- `grep "onSelectDoc\|searchQuery" DocSidebar.jsx` shows child uses them — looks wired
- But cross-reference reveals the PARENT uses `onSelect=` not `onSelectDoc=`
- The two prop "dialects" pass each other silently — child receives `undefined` for everything

**Diagnostic (mandatory 3-step cross-reference):**
1. Read child's destructured params: `grep -A 30 "export default function ChildName" child.jsx`
2. Read parent's JSX for that child: `grep -A 25 "<ChildName" parent.jsx`
3. Cross-reference by NAME — not just count. `onSelect` ≠ `onSelectDoc`. `activeId` ≠ `currentDoc`.

**Fix — apply BOTH structurally:**
1. **Fix A (parent):** Rewrite parent JSX to pass correct prop names with shared state lifted up
2. **Fix B (child):** Add defensive defaults to ALL props the child accesses via method calls:
```jsx
searchQuery = '', setSearchQuery = () => {}, sortBy = 'newest',
setSortBy = () => {}, setSelectedTags = () => {}, selectedIds = [],
setSelectedIds = () => {},
```

**Verification:** After fix, `curl localhost:3000/PATH` must return 200 with full page content (not just ErrorBoundary fallback text). For production: `curl -s https://domain/PATH | grep -c "Có lỗi xảy ra"` must be 0.

## 14. Binary Format Viewer — DOCX/DOC to PDF via LibreOffice

**Symptom:** File `.docx` shows garbled text or crashes. DocReader parses `doc.content` (base64 binary) through `marked.js` markdown parser → garbage output.

**Root cause:** Server returns docx content as base64 string in JSON. Frontend blindly passes it to markdown renderer. Binary data is not markdown.

**Server already has LibreOffice conversion endpoint:**
```js
// GET /api/documents/:id/pdf — converts .docx → PDF via soffice.exe
convertDocxToPdf(docxPath, pdfPath, (err) => {
  const buf = fs.readFileSync(pdfPath);
  res.writeHead(200, { 'Content-Type': 'application/pdf', 'Content-Length': buf.length });
  res.end(buf);
});
```

**Fix — detect format + display PDF in iframe:**
```jsx
const isDocx = doc?.ext === 'docx' || (doc?.file || '').endsWith('.docx');
const pdfUrl = isDocx ? `/api/documents/${doc?.id}/pdf` : null;

// Pre-fetch to trigger server-side LibreOffice conversion
useEffect(() => {
  if (isDocx) {
    setPdfLoading(true);
    fetch(pdfUrl).finally(() => setPdfLoading(false));
  }
}, [doc?.id, isDocx, pdfUrl]);

// Render: PDF iframe for DOCX, HTML for markdown
{isDocx ? (
  <div style={s.pdfContainer}>
    {pdfLoading ? (
      <div style={s.pdfLoading}>
        <i className="fas fa-spinner fa-spin" />
        <span>Đang chuyển đổi DOCX sang PDF...</span>
      </div>
    ) : (
      <iframe style={s.pdfIframe} src={pdfUrl} title={doc.title} />
    )}
  </div>
) : (
  <div ref={contentRef} dangerouslySetInnerHTML={{ __html: renderedHtml }} />
)}
```

**DOCX-specific UI adjustments:**
- Add badge: `<span className="docx-badge"><i className="fas fa-file-word" /> DOCX</span>` in metadata row
- Hide edit button (binary can't be edited in markdown editor)
- Hide font controls, TOC, reading progress (irrelevant for PDF)
- Download button downloads `.docx` file directly: `window.open(\`/api/documents/${doc.id}?dl=1\`)`
- First load is slow (LibreOffice cold start ~2-5s). Subsequent loads use cached PDF

**Pitfalls:**
- Server uses `spawn(SOFFICE, ['--headless', '--convert-to', 'pdf', ...])` — first call cold-starts LibreOffice. UI must show loading spinner to avoid blank screen
- `doc.ext` comes from API (`/api/documents` list) as `'docx'`. Also check `doc.file.endsWith('.docx')` as fallback
- `s.pdfIframe` needs `minHeight: '400px'` and `flex: 1` to fill the reader panel
- Disable `dangerouslySetInnerHTML` path entirely for docx — don't try to render base64 as HTML
