---
name: react-vite-migration
title: React + Vite Migration (from vanilla HTML/Bulma)
description: >-
  Migrate multi-page vanilla HTML+Bulma+JS sites to React 19 + Vite 6 + React Router 7.
  Incremental phase-based strategy, keep existing Node.js server, deploy after each phase.
  Covers scaffold, API client, SSE hooks, SPA fallback, canvas wrapper, widget lazy-loading.
category: software-development
trigger:
  - "chuyển qua react"
  - "migrate sang react"
  - "react hóa"
  - "vite migration"
  - "rewrite frontend react"
  - "từ html sang react"
  - "chuyển toàn bộ code qua react"
  - "vibe coding react"
version: "1.1"
---

## Strategy: Incremental Phase-Based Migration

**Golden rule:** Do NOT touch the backend (`server.js` logic). Keep API endpoints unchanged. Only add a SPA fallback at the static-serving layer.

**Phase cadence:** Each phase = deployable. Old HTML pages remain accessible during migration. New React pages serve when built `dist/` exists.

**Testing:** Vite dev (`npm run dev` on :5173) proxies `/api` → existing backend on :3000. Production: `npm run build` → `node server.js` serves both old `public/` and new `dist/`.

---

## Phase 0: Codebase Inspection

Before writing any code:

1. **Inventory all HTML pages** — count files, lines, structure
2. **Map ALL API endpoints** — list every route, method, purpose
3. **Identify no-touch zones** — Canvas/WebGL code (keep as-is, wrap via iframe)
4. **Map CSS variables** — `global.css` variables are reused via CDN import
5. **Identify shared UI patterns** — navbar, toast, modal, blob bg, confirm dialog

### API endpoint mapping template

| Endpoint | Method | Purpose | Page |
|---|---|---|---|
| `/api/services` | GET | List services | Dashboard |
| `/api/services/:id/logs?lines=N` | GET | Fetch logs | Dashboard |
| `/api/logs/stream` | GET | SSE log stream | Dashboard |
| `/api/documents` | GET | List documents | Documents |
| `/api/documents/:id` | PUT | Update document | Documents |
| `/api/utilities/youtube-audio?url=X` | GET | YouTube metadata | Utilities |
| ... | ... | ... | ... |

---

## Phase 1: Scaffold + Core

### 1.1 Create Vite + React project

Run in project root:

```bash
mkdir -p frontend/src/{pages,components,hooks,services}
```

**package.json:**
```json
{
  "name": "frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^6.0.0"
  }
}
```

**vite.config.js:**
```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: { outDir: '../dist', emptyOutDir: true },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:3000',
      '/assets': 'http://localhost:3000',
      '/proxy': 'http://localhost:3000',
    },
  },
});
```

**frontend/index.html:** CDN links for Bulma, Font Awesome, Inter font, global.css — same as old HTML pages. Entry: `<script type="module" src="/src/main.jsx"></script>`.

### 1.2 Create shared component library

**Navbar.jsx** — glassmorphism with theme toggle, nav links, active state via `useLocation()`:
```jsx
import { Link, useLocation } from 'react-router-dom';
import useTheme from '../hooks/useTheme';
export default function Navbar({ active: forcedActive }) { ... }
```

**BlobBackground.jsx** — 4 animated blobs matching the existing `blob-container` CSS.

**ConfirmModal.jsx** — glass Bulma modal with confirm/cancel callbacks.

**useTheme.js** — reads/writes `data-theme` on `<html>`, `localStorage` persistence.

**useToast.jsx** — ToastProvider context + useToast hook. Stacks toasts in bottom-right.

### 1.3 API client

Single `services/api.js` with typed fetch functions for every endpoint:

```js
const BASE = '';
async function request(path, options = {}) { ... }
export function fetchServices() { return request('/api/services'); }
export function startService(id) { return request(`/api/services/${id}/start`, { method: 'POST' }); }
export function stopService(id) { ... }
// ... one function per API endpoint
```

### 1.4 Server.js SPA fallback

**Key:** `serveStatic` checks `isSafePath(PUBLIC_DIR, ...)` which rejects paths outside `public/`. Do NOT pass `dist/` paths through `serveStatic` — read the file directly:

```js
// In the route handler, BEFORE the static file handler:
if (u.pathname === '/' || u.pathname === '/dashboard' || /* ...other SPA routes... */) {
  const spaPath = path.join(__dirname, 'dist', 'index.html');
  if (fs.existsSync(spaPath)) {
    fs.readFile(spaPath, (err, data) => {
      if (!err) {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store, must-revalidate' });
        res.end(data);
      }
    });
    return;
  }
}

// Also serve Vite build assets from dist/assets/:
if (u.pathname.startsWith('/assets/') && u.pathname.endsWith('.js')) {
  const distAsset = path.join(__dirname, 'dist', u.pathname);
  if (fs.existsSync(distAsset)) {
    fs.readFile(distAsset, (err, data) => {
      if (!err) {
        res.writeHead(200, { 'Content-Type': 'text/javascript; charset=utf-8', 'Cache-Control': 'public, max-age=31536000, immutable' });
        res.end(data);
      }
    });
    return;
  }
}

// Then fall through to old static handler for backward compat:
if (fs.existsSync(filePath)) { serveStatic(res, filePath); return; }
```

---

## Phase 2-3: Build page components

## Critical: Feature Parity Audit

**The #1 pitfall when delegating page migration to subagents is `missing-feature-drift`** — vanilla HTML pages have hundreds of lines of interactive features (search history, bulk delete, sort controls, export buttons, font size, reading progress, markdown toolbars, keyboard shortcuts, etc.) that subagents don't see because you only give them the API spec and component spec, not the full original HTML.

### Required workflow for page migration

1. **Read the ENTIRE original HTML file** — every `<style>`, `<script>`, and `<body>` section. Categorize features into:
   - **Core/API features** — data fetching, CRUD (must replicate)
   - **UI/UX features** — modals, toasts, animations, responsive behavior (must replicate)
   - **Utility features** — font size controls, search history, reading progress, keyboard shortcuts, markdown toolbar, print/export buttons, bulk delete (EASY TO FORGET — must explicitly list)
   - **Decoration** — blob backgrounds, splash screens, skeleton loaders (nice-to-have)

2. **Build a feature checklist** before writing any code. Use this format:

```markdown
## Feature Parity Checklist for [PageName]

- [ ] Core CRUD (list, get, create, update, delete)
- [ ] Search with debounce + history dropdown (localStorage)
- [ ] Sort controls (newest/oldest/A→Z)
- [ ] Filter (by tags, status/draft)
- [ ] Bulk select + bulk delete
- [ ] Reading progress bar (fixed top, 3px gradient)
- [ ] Font size controls (A+/A-)
- [ ] Markdown toolbar in editor (Bold, Italic, Heading, Link, Code, List)
- [ ] Print button
- [ ] Download as file
- [ ] Export PDF (POST to export endpoint)
- [ ] Inline rename (double-click title)
- [ ] New doc modal with templates
- [ ] Drag-and-drop upload
- [ ] Word count display
- [ ] Cache clear button
- [ ] Keyboard shortcuts
- [ ] Toast notifications
- [ ] Confirm dialog for destructive actions
- [ ] Empty state / loading skeleton
- [ ] Mobile responsive (sidebar/reader overlay toggle)
- [ ] Auto-save with debounce
```

3. **Include the full original HTML in subagent context** — when using `delegate_task` to build a page component, include the original `.html` file content in the `context` field (not just the goal). The subagent needs to see the original CSS selectors, class names, JS function names, and HTML structure to replicate features faithfully.

4. **Verify feature parity after build** — run a manual diff against the original HTML. Common misses:
   - Search history (localStorage)
   - Full-text search dropdown with results
   - Sort bar with multiple criteria
   - Draft/status filter checkbox
   - Bulk delete with checkboxes
   - Font size controls (A+/A-)
   - Reading progress bar (top of reader)
   - Markdown toolbar buttons (Bold/Italic/Heading/Link/Code/List)
   - Print/Download/Export PDF buttons
   - Cache clear button
   - Word count at bottom of reader
   - Keyboard shortcut hints
   - Drag-and-drop upload
   - Template selector for new documents

### Pattern: Lazy-loaded pages with React.lazy + Suspense

```jsx
// App.jsx
const WidgetPage = lazy(() => import('./pages/WidgetPage'));

// Wrapping in Suspense:
<Suspense fallback={<div style={loadingStyle}>Loading...</div>}>
  <WidgetPage />
</Suspense>
```

### Pattern: Document viewer with marked.js

`marked` is loaded from CDN (`https://cdn.jsdelivr.net/npm/marked@5/marked.min.js`). Reference via `window.marked`:

```jsx
function loadMarked() {
  if (typeof window !== 'undefined' && !window.marked) {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/marked@5/marked.min.js';
    document.head.appendChild(s);
    return new Promise(res => { s.onload = () => res(window.marked); });
  }
  return Promise.resolve(window.marked);
}
```

### Pattern: SSE (EventSource) hook

```jsx
export default function useSSE(url, options = {}) {
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef(null);

  useEffect(() => {
    const es = new EventSource(url);
    es.onopen = () => setConnected(true);
    es.onmessage = (e) => {
      try { setLogs(prev => [...prev, JSON.parse(e.data)]); } catch {}
    };
    es.onerror = () => setConnected(false);
    esRef.current = es;
    return () => es.close();
  }, [url]);

  return { logs, connected };
}
```

### Pattern: Canvas/Three.js visualizer wrapper (iframe)

Keep existing canvas code untouched in `public/hermes-standalone.html`. Create a React wrapper:

```jsx
export default function HermesPage() {
  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column' }}>
      <Navbar active="/hermes" />
      <iframe
        src="/hermes-standalone.html"
        style={{ flex: 1, border: 'none', width: '100%', background: '#05060f' }}
      />
    </div>
  );
}
```

The standalone HTML is a copy of the original page with ALL its CSS+HTML+JS intact, minus the React-managed navbar.

### Pattern: Widget grid → detail with lazy loading

```jsx
const widgetComponents = {
  random: lazy(() => import('./widgets/RandomDiscovery')),
  dice: lazy(() => import('./widgets/DiceRoller')),
  // ...
};
```

Grid view shows all widgets as clickable cards. Detail view renders the selected widget component inside a `<Suspense>` boundary. Back button returns to grid.

---

## Hooks reference

| Hook | Purpose | Dependencies |
|---|---|---|
| `useTheme` | Dark/light theme, `localStorage`, `data-theme` attribute | none |
| `useToast` | Stacked toast notifications, auto-dismiss | none (uses context) |
| `useServices` | Fetch + cache services from API | `fetchServices()` |
| `useDocuments` | CRUD for documents, search, tags | API client |
| `useSSE` | EventSource connection, auto-reconnect | EventSource URL |

---

## Build caches

`.gitignore` should include:
```
dist/
frontend/node_modules/
frontend/dist/
```

Vite outputs to `../dist/` (relative to `frontend/`) — `dist/` at project root. This is where `server.js` serves from.

---

## .gitignore pattern

```
# Build output
dist/
frontend/dist/

# Dependencies
node_modules/
frontend/node_modules/

# Data files (root level only)
/services.json
/*.json
/*.txt

# Plans
DESIGN.md
PLAN.md
```

---

## Pitfalls

- **API data shape mismatch between single-doc and list-doc endpoints** — Many backends return DIFFERENT fields for `/api/documents/:id` vs `/api/documents`. The single-doc endpoint often returns only `{id, content, ext}` (no `title`, `tags`, `created`), while the list endpoint has full metadata. **Workaround**: Merge the single-doc response with the list entry:
  ```js
  const fetchDoc = useCallback(async (id) => {
    const data = await request(`/api/documents/${id}`);
    const listDoc = docs.find(d => d.id === id);
    const merged = { ...(listDoc || {}), ...data };
    setCurrentDoc(merged);
  }, [docs]); // depends on docs for merge
  ```
- **Tags field normalization** — Backend may return tags as comma-separated string `"hướng dẫn"` instead of array `["hướng dẫn"]`. Always normalize:
  ```js
  const tags = d.tags
    ? (Array.isArray(d.tags) ? d.tags : String(d.tags).split(',').map(t => t.trim()).filter(Boolean))
    : [];
  ```
  Apply in ALL places: tag filter, tag display (sidebar, reader), dynamic tag extraction, sort-by-date (use `d.created || d.meta?.createdAt`).
- **NEVER assume subagent will replicate all features** — A subagent given an API spec + design spec will build a functioning component, but it WILL miss 30-50% of the UX features from the original HTML (search history, sort controls, bulk delete, reading progress, font controls, keyboard shortcuts, markdown toolbar, etc.). Always include the FULL original HTML file in the subagent context and add a feature parity checklist to the goal. After the subagent finishes, run a manual diff: compare rendered React page against original HTML's interactive features — not just build output.
- **Mobile hamburger menu is REQUIRED from day one** — Navbar with 6+ links will overflow on mobile. Must implement responsive hamburger with animated X icon (3 lines rotate on toggle), full-height overlay backdrop filter, slide-down panel, body scroll lock, touch-friendly padding (0.65rem 0.85rem), and active indicator dot. Reference pattern: `useState(menuOpen)` → hamburger button with 3 `<span>` lines that rotate on `menuOpen` → fixed overlay div with backdrop blur → panel with animation `slideDown .25s cubic-bezier(.4,0,.2,1)`. Use `useEffect` to toggle `body.menu-open` class for scroll lock.
- **Navbar link completeness** — Start with ALL nav links (Home, Dashboard, Documents, Utilities, Widget, Hermes) from day one. NEVER deploy with just Home + Dashboard. Users will immediately notice missing navigation links. Build the full `NAV_LINKS` array immediately:
  ```js
  const NAV_LINKS = [
    { to: '/', label: 'Home', icon: 'fa-house' },
    { to: '/dashboard', label: 'Dashboard', icon: 'fa-gauge-high' },
    { to: '/documents', label: 'Documents', icon: 'fa-file-lines' },
    { to: '/utilities', label: 'Utilities', icon: 'fa-wrench' },
    { to: '/random-widget', label: 'Widget', icon: 'fa-cubes' },
    { to: '/hermes', label: 'Hermes', icon: 'fa-cube' },
  ];
  ```
  Also add responsive hamburger menu for mobile (< 820px) — 6 links won't fit on a small navbar without it. Use `navbar-burger` with 3 spans + `useState` toggle + slideDown dropdown.
- **Subagent overwrites parent-modified files** — After `delegate_task` subagent finishes, the files it modified (DocumentsPage.jsx, WidgetPage.jsx, hook files, widget files) may differ from what the parent read earlier. Always RE-READ modified files after subagent completion before doing further edits — the subagent's version may have different structure, different imports, or different variable names than what the parent expected.
- **`serveStatic` checks `isSafePath(PUBLIC_DIR, ...)`** — `dist/` lives OUTSIDE `public/`, so it gets 403'd. Do NOT pass `dist/` paths through `serveStatic`. Read them directly with `fs.readFile`.
- **`data-theme` on `<html>`** — The theme system uses `data-theme` attribute. `useTheme` hook must set it on `document.documentElement` on every toggle.
- **Vite build places JS in `dist/assets/`** — These paths start with `/assets/` but are in `dist/assets/`, not `public/assets/`. The server.js must route them separately.
- **Old `.html` redirect in server.js** — The original server likely has a line like:
  ```js
  if (u.pathname === '/dashboard') u.pathname = '/dashboard.html';
  ```
  Intercept BEFORE this redirect when `dist/index.html` exists.
- **SSE and Vite dev proxy** — EventSource works fine through Vite's `/api` proxy. No special config needed.
- **marked.js loading race** — If marked.js is loaded asynchronously, DocReader may render before it loads. Use a `loaded` state + loading indicator.
- **Don't delete old HTML files** — They serve as fallback if `dist/` doesn't exist. Remove them only after full migration confirmed.
- **Navbar active state** — Use `useLocation()` from react-router-dom, not `window.location.pathname`.
- **Widget lazy loading** — Each widget file must have a `default` export. Code-split at the widget level using `React.lazy`.
- **Canvas iframe keyboard events** — Keyboard shortcuts won't reach the iframe. Either forward them via `postMessage` or accept that iframe keyboard shortcuts work within the iframe only.
- **Bulma CSS still imported** — Bulma is loaded from CDN in `frontend/index.html`. React components use Bulma classes via `className`.
- **`z-index` stacking** — Canvas visualizer uses z-index up to 500. React Navbar needs `z-index: 500+`. Hermes standalone iframe handles its own z-index internally.
- **CSS `composes:` in Vite** — Vite's LightningCSS pipeline does NOT support `composes:` from CSS Modules when the CSS file is imported via JS/CSS import (not as a `.module.css`). Rules using `composes: card` silently fail with no properties. Always expand composed rules inline — copy all properties from the source class into the target class.
- **`await` in `setInterval` callbacks** — esbuild may reject `setInterval(async () => { await ... })` in some configs. Use `.then()/.catch()` pattern instead for setInterval callbacks.
- **AppLayout deduplication** — After creating `<AppLayout>` as the single source of truth for Navbar + BlobBackground + Footer, go through EVERY page and remove all 3 patterns: `import Navbar`, `import BlobBackground`, `<BlobBackground />`, `<Navbar active="..." />`. All pages switch from `useToast()` to `useToastContext()`.
- **Navbar file move breaks imports** — When Navbar moves from `components/Navbar.jsx` to `components/layout/Navbar.jsx`, internal imports like `useTheme` change from `../hooks/` to `../../hooks/`.
- **ToastProvider after useToast hook refactor** — If `useToast.js` changes from `export default function` to `export function useToast` (named export), the `ToastProvider` import must change from `import useToast from` to `import { useToast } from`. The provider should manage toast state internally with `useState` + `useRef` timers, not via the hook's own state.
- **BottomTab route paths must match App routes exactly** — If App.jsx defines `<Route path="widgets">` but BottomTab links to `/random-widget`, the tab never highlights active. Always verify the `TABS` array routes match `<Route path="...">` exactly, including the `/` prefix. Common mismatch: BottomTab links to `/random-widget` but App.jsx route is `/widgets`.
- **Page CSS file import location matters** — Page-specific CSS files (e.g. `pages/home/home.css`) must be imported ONLY in the main page component, NEVER in sub-components inside the same directory. Sub-components importing the same CSS cause duplicate style injection. The import path from the main page is `'./home/home.css'`; from a sibling sub-component it would be `'./home.css'` — two different resolved paths = duplicate CSS in Vite.
- **lazy(() => import(...)) with dynamic template literals FAILS in Vite** — Vite's Rollup build uses static analysis for code splitting. ``import(`./widgets/${widget.component}.jsx`)`` with template literals is not resolved — produces a runtime error or empty chunk. Always pre-declare every import as a static string literal in a lookup object.

- **Duplicate .js/.jsx files → silent ErrorBoundary crash** — If `hooks/useToast.js` and `hooks/useToast.jsx` coexist, Vite may resolve the wrong module. The old `.jsx` exports default `ToastProvider`, new `.js` exports named `useToast`. Pages importing `{ useToast }` get wrong module → runtime crash → ErrorBoundary "Có lỗi xảy ra / Vui lòng thử lại trang". **Fix**: `ls -la hooks/` after every refactor, delete stale duplicates.

- **Parent doesn't pass props child destructures (prop contract mismatch)** — During migration, parent components get rebuilt with different prop contracts. A parent renders `<Child docs={data} />` but the child destructures `{ docs, searchQuery, sortBy }`. Since `searchQuery` wasn't passed, it's `undefined` → `searchQuery.trim()` crashes. **Symptoms**: child renders fine in isolation, ErrorBoundary shows "Có lỗi xảy ra", `grep` for the prop name in the child shows it's USED but not PASSED. **Fix**: (1) Add defensive defaults to ALL child props (`searchQuery = ''`, `sortBy = 'newest'`, `setSearchQuery = () => {}`, `selectedIds = []`), AND (2) wire the prop from parent's state. The defensive defaults prevent future crashes when other parents also forget props. **Verify**: cross-reference parent JSX props vs child's destructured params — every child param without a default must appear in the parent's JSX.

- **Prop NAME mismatch — parent + child have different API versions** — WORSE than missing props. Child was rewritten with new prop names (e.g. `onSelectDoc`, `currentDoc`, `searchQuery`) but parent STILL passes OLD names (`onSelect`, `activeId`, no search state at all). `grep` shows MANY props being passed → looks correct superficially. Cross-reference by NAME reveals: `onSelect` ≠ `onSelectDoc`, `activeId` ≠ `currentDoc`. Every mismatched prop → `undefined.method()` → TypeError → ErrorBoundary. **Diagnostic**: cross-reference EVERY prop name between parent's `<ChildName propName={...}>` and child's `{ propName }` destructuring — count means nothing, names are everything. **Fix**: rewrite parent JSX to match child's CURRENT prop contract. Lift shared state (`searchQuery`, `sortBy`, `draftOnly`, `selectedIds`) up to parent, wire through correct names. Then add defensive defaults to child anyway.

- **DOCX binary file viewer — must not pass to marked.js** — Server returns docx content as base64 string in JSON. DocReader MUST detect `doc.ext === 'docx'` and switch to PDF rendering via existing LibreOffice endpoint `/api/documents/:id/pdf`. Display PDF in iframe with loading spinner. Hide edit/font/TOC controls for docx. Download button streams original file via `?dl=1`. First conversion is slow (LibreOffice cold start ~2-5s) — loading state is mandatory.

- **ErrorBoundary fallback IS a frontend crash, not server down** — "Có lỗi xảy ra / Vui lòng thử lại trang" means a React component threw during render. Triple-check: (1) duplicate module files in hooks/, (2) `//` comments in imported CSS, (3) import path mismatches after file moves, (4) missing SPA route in server.js (old HTML loads → references non-existent JS).

- **server.js SPA routes must stay in sync with App.jsx <Route> paths** — Adding `<Route path="widgets">` means adding `'/widgets'` to the server's SPA intercept list. Also verify BottomTab + Navbar links use matching paths.

- **Production server restart required after `npm run build`** — chunk hashes change every build: `fuser -k 3000/tcp && node server.js` then `curl localhost:3000/ | grep "script src"` to verify the new bundle loaded.

---

## References

- `dashboard-ui-patterns` skill — SSE logs, toast, health ping, expandable cards, glassmorphism
- `subagent-driven-development` skill — parallel page building via delegate_task
- `plan` skill — migration plan template
- `references/agent-friendly-react-refactor.md` — full 5-phase refactoring plan: mobile-first architecture, component-driven design, 150-line file limit, auto-discovery widget pattern, agent-friendly folder conventions
- `references/phase1-design-system-foundation.md` — Phase 1 implementation guide: AppLayout, ToastProvider migration, CSS utility classes, BottomTab, ErrorBoundary, pitfalls (composes, setInterval await, named exports)
- `references/phases-2-5-mobile-first-refactor.md` — Phases 2-5 implementation guide: mobile-first responsive grid patterns, page component splits (HomePage→4 sections, DocumentsPage→DocSearch+DocTags), route-based lazy loading (6 lazy routes → 45 chunks), barrel exports (ui/layout/shared/index.js), WidgetPage static widgetMap pattern, section markers, build verification checklist
- `references/july-2026-navbar-fix.md` — past navbar fix session notes
- `references/session-aug-2026-migration.md` — past migration session notes