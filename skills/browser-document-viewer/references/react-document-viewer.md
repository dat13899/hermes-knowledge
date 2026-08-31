# React Document Viewer (Vite + React 19)

## Difference from vanilla-JS version

The `browser-document-viewer` skill covers a **vanilla JS single-HTML** doc viewer with Node.js server. This reference covers the **React variant** — same concept (sidebar + reader + editor, marked.js rendering, auto-save, TOC, reading progress) but as a **Vite + React 19 + React Router 7** SPA with JSX components and inline styles.

## Component Architecture

```
DocumentsPage (page-level orchestrator)
├── DocSidebar       ← search, tag chips, doc list, drag-drop upload
├── DocReader        ← header, meta, rendered markdown, TOC, reading progress bar
└── DocEditor        ← full-screen overlay: split-pane textarea + preview

useDocuments(toast)  ← custom hook encapsulating all API interactions
```

### Key patterns

1. **Orchestrator page** owns all state. Sub-components are presentational with callbacks.
2. **Custom hook** (`useDocuments`) encapsulates all fetch/CRUD/auto-save logic. Accepts `toast` for error feedback.
3. **All sub-components in `pages/docs/`** directory, not in `components/` — they are page-specific.
4. **Style objects** (`const s = {...}`) at top of each component — avoids CSS files, keeps styles co-located with markup. Mirrors the CSS variable system.

## useDocuments Hook Pattern

```javascript
import { useState, useCallback, useRef } from 'react';

export default function useDocuments(toast) {
  const [docs, setDocs] = useState([]);
  const [currentDoc, setCurrentDoc] = useState(null);
  const [saving, setSaving] = useState(false);
  const saveTimer = useRef(null);

  // Fetch all
  const fetchDocs = useCallback(async () => { ... }, [toast]);

  // Fetch single
  const fetchDoc = useCallback(async (id) => { ... }, [toast]);

  // Create
  const createDoc = useCallback(async (title) => { ... }, [toast]);

  // Update (immediate)
  const updateDoc = useCallback(async (id, data) => {
    setSaving(true);
    try {
      // ...fetch...
    } finally {
      setSaving(false);  // MUST use finally to handle both success/error
    }
  }, [toast]);

  // Debounced auto-save (2s)
  const scheduleSave = useCallback((id, data) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    setSaving(true);
    saveTimer.current = setTimeout(async () => {
      // ...PUT request...
      setSaving(false);
    }, 2000);
  }, [toast]);

  // Delete, rename, convert, upload — same pattern
  return { docs, setDocs, loading, currentDoc, setCurrentDoc, saving,
    fetchDocs, fetchDoc, createDoc, updateDoc, scheduleSave,
    deleteDoc, renameDoc, convertDoc, uploadDoc };
}
```

**Pitfalls:**
- `updateDoc` must use `try/finally` for `setSaving(false)` — `try/catch` with `return null` in the catch block creates dead code after.
- `scheduleSave` stores the timer ref — component unmount should NOT clear it (the save runs even if user navigates away, which is the desired behavior for auto-save).
- All callbacks are `useCallback`-wrapped to prevent infinite effect loops in the parent.

## Style Object Pattern

```javascript
const s = {
  container: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    background: 'var(--glass-bg)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',  // Firefox needs -webkit prefix
    border: '1px solid var(--glass-border)',
    borderRadius: 'var(--radius-lg)',
    overflow: 'hidden',
    position: 'relative',
    minWidth: 0,  // REQUIRED for flex children to shrink in nested flex
  },
  actionBtn: (color = 'var(--text-dim)') => ({
    // style factories for variants
    fontSize: '0.75rem',
    padding: '0.3rem 0.55rem',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--glass-border)',
    background: 'var(--surface-2)',
    color: color,
    cursor: 'pointer',
    // ...
  }),
};
```

**Pitfalls:**
- `backdrop-filter` MUST include `WebkitBackdropFilter` prefix for Firefox.
- Flex children with `overflow-y: auto` need `minHeight: 0` (or `min-width: 0` for horizontal) to actually scroll — without it the child assumes content intrinsic height.
- Style factories (functions returning objects) are OK for small variants but avoid deep nesting.

## Markdown Rendering (marked.js from CDN)

Inject the script tag once at page mount:

```javascript
// In DocumentsPage.jsx
const MARKED_CDN = 'https://cdn.jsdelivr.net/npm/marked@5/marked.min.js';

function loadMarked() {
  if (typeof window !== 'undefined' && !window.marked) {
    const script = document.createElement('script');
    script.src = MARKED_CDN;
    script.async = false;
    document.head.appendChild(script);
  }
}

// In component
const [markedLoaded, setMarkedLoaded] = useState(false);
useEffect(() => {
  if (!window.marked) {
    loadMarked();
    const check = setInterval(() => {
      if (window.marked) { setMarkedLoaded(true); clearInterval(check); }
    }, 100);
    setTimeout(() => clearInterval(check), 10000); // safety timeout
  } else { setMarkedLoaded(true); }
}, []);
```

Then render in sub-components:

```javascript
function renderMarkdown(content) {
  if (typeof window !== 'undefined' && window.marked) {
    return window.marked.parse(content || '', { breaks: true, gfm: true });
  }
  return '<p>Loading...</p>';
}
```

**Pitfall:** `window.marked.parse()` is synchronous in marked@5. Never use `await` — the CDN script blocks enough that the polling loop resolves before user interaction.

## Reading Progress Bar (React)

```javascript
const [readProgress, setReadProgress] = useState(0);
const contentRef = useRef(null);

const handleScroll = useCallback(() => {
  const el = contentRef.current;
  if (!el) return;
  const scrollTop = el.scrollTop;
  const scrollHeight = el.scrollHeight - el.clientHeight;
  if (scrollHeight > 0) {
    setReadProgress(Math.min((scrollTop / scrollHeight) * 100, 100));
  }
}, []);

// On the scrollable div:
<div ref={contentRef} onScroll={handleScroll}>
  {/* Progress bar positioned absolutely at top */}
  <div style={{ position: 'absolute', top: 0, left: 0, height: '3px',
    background: 'var(--accent)', transition: 'width .2s ease',
    width: `${readProgress}%`, zIndex: 2 }} />
  {/* content */}
</div>
```

## TOC from Rendered HTML

```javascript
function extractTOC(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  const headings = div.querySelectorAll('h1, h2, h3, h4');
  return Array.from(headings).map(h => ({
    id: h.id || h.textContent.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    text: h.textContent,
    depth: parseInt(h.tagName[1], 10),
  }));
}
```

- Store TOC in `useMemo` keyed on content.
- Dropdown positioned absolutely relative to the TOC button.
- Close on outside click with `useEffect` + document `mousedown` listener.
- Scroll to heading: `contentRef.current.querySelector(`#${CSS.escape(id)}`).scrollIntoView({ behavior: 'smooth' })`.

## Editor Overlay (Full-Screen)

Structure:
```
<div style={{ position: 'fixed', inset: 0, zIndex: 5000, background: 'rgba(0,0,0,0.6)',
  backdropFilter: 'blur(4px)', display: 'flex', flexDirection: 'column' }}>
  <Toolbar> ← close, title, save status, save button
  <SplitPane> ← left=textarea, right=preview, resizable divider
  <Footer> ← word/line/char count
</div>
```

### Resizable Split Pane

```javascript
const [splitRatio, setSplitRatio] = useState(50);
const [isDragging, setIsDragging] = useState(false);
const containerRef = useRef(null);

// On divider mousedown: setIsDragging(true)

useEffect(() => {
  if (!isDragging) return;
  const handleMouseMove = (e) => {
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = Math.max(20, Math.min(80, (x / rect.width) * 100));
    setSplitRatio(pct);
  };
  const handleMouseUp = () => setIsDragging(false);
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
  return () => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };
}, [isDragging]);
```

Panes use `flexBasis: ${splitRatio}%` with `maxWidth` constraint. The divider is 4px wide with cursor `col-resize` and changes color when dragging.

### Keyboard shortcuts

```javascript
const handleKeyDown = useCallback((e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    onSave?.(content);
  }
}, [content, onSave]);

// Escape to close
useEffect(() => {
  const handler = (e) => { if (e.key === 'Escape') onClose?.(); };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [onClose]);
```

## Mobile Responsive (State-Based)

Breakpoint at 720px. Uses `window.innerWidth` + `resize` listener (no CSS media queries for layout state):

```javascript
const [isMobile, setIsMobile] = useState(window.innerWidth < 720);
const [showSidebar, setShowSidebar] = useState(true);

useEffect(() => {
  const onResize = () => {
    const mob = window.innerWidth < 720;
    setIsMobile(mob);
    if (!mob) setShowSidebar(true); // restore sidebar on desktop
  };
  window.addEventListener('resize', onResize);
  return () => window.removeEventListener('resize', onResize);
}, []);
```

- **Mobile sidebar**: `width: 100%`, reader hidden.
- **Mobile reader**: Appears as overlay when user selects a doc from sidebar.
- **Toggle button** in top bar switches between sidebar view and reader view.

## API Proxy Pattern

In `vite.config.js`:
```javascript
server: { proxy: { '/api': 'http://localhost:3000' } }
```

All `fetch('/api/documents/...')` calls go through Vite's dev proxy — no base URL needed in production (same origin). The `useDocuments` hook uses a `BASE = ''` constant so it works both in dev (via proxy) and production (served from the same port as the Express backend).

## Project Structure for This Feature

```
frontend/src/
├── hooks/
│   ├── useDocuments.js        ← created for this feature
│   ├── useTheme.js            ← existing
│   └── useToast.jsx           ← existing (context provider)
├── pages/
│   ├── DocumentsPage.jsx      ← main page (BlobBackground, Navbar, Docs)
│   └── docs/
│       ├── DocSidebar.jsx     ← search, tags, doc list, drag-drop
│       ├── DocReader.jsx      ← rendered markdown, TOC, progress
│       └── DocEditor.jsx      ← full-screen split-pane editor
└── services/
    └── api.js                 ← existing (fetch wrappers for other pages)
```

## API Endpoints Used

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/documents | List all docs |
| GET | /api/documents/:id | Get single doc with content |
| PUT | /api/documents/:id | Update content/title/tags |
| POST | /api/documents | Create new doc |
| DELETE | /api/documents/:id | Delete doc |
| POST | /api/documents/upload | File upload (multipart form-data) |
| POST | /api/documents/:id/rename | Rename doc |
| POST | /api/documents/:id/convert | Convert to PDF |
