# Phases 2-5: Mobile-First Refactor + Component Splits + Lazy Routes + Barrel Exports

## Phase 2: Mobile-First Responsive CSS

All CSS files use **mobile-first** media queries: base styles = mobile, `@media (min-width:)` = desktop overrides.

### Key patterns

```css
/* Base: mobile (1 column) */
.services-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }

/* Tablet: 2 columns */
@media (min-width: 640px) { .services-grid { grid-template-columns: repeat(2, 1fr); } }

/* Desktop: 3 columns */
@media (min-width: 900px) { .services-grid { grid-template-columns: repeat(3, 1fr); } }
```

### Widget grid responsive

```css
.widget-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
@media (min-width: 480px) { .widget-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 720px) { .widget-grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); } }
```

### BottomTab safe area

```css
nav {
  padding-bottom: env(safe-area-inset-bottom, 0.3rem);
}
```

### BottomTab route correctness

```js
const TABS = [
  { to: '/', icon: 'fa-house', label: 'Home' },
  { to: '/dashboard', icon: 'fa-gauge-high', label: 'Dashboard' },
  { to: '/documents', icon: 'fa-file-lines', label: 'Docs' },
  { to: '/widgets', icon: 'fa-cubes', label: 'Widget' },     // NOT '/random-widget'
  { to: '/utilities', icon: 'fa-toolbox', label: 'Tools' },
];
```

Must match actual route paths exactly. Wrong route → tab never shows active state.

### DocumentsPage mobile pattern

Desktop: sidebar (280px fixed) + reader (flex:1) side-by-side.
Mobile: toggle between sidebar list and reader view with button in topbar.

Use `useMediaQuery()` hook instead of `window.innerWidth` directly:

```js
import { useMediaQuery } from '../hooks/useMediaQuery';
const { isMobile } = useMediaQuery();
// isMobile triggers sidebar/reader overlay toggle
```

---

## Phase 3: Page Refactoring (Component Splits)

### Pattern: Split a monolithic page into components + CSS

**HomePage.jsx (472 lines → 118 lines + 4 components + 1 CSS file)**

```
src/pages/home/
├── HeroSection.jsx        (47 lines) — typing tagline, CTA, anchor nav
├── ServicesSection.jsx     (93 lines) — status bar + service cards + ServiceCard sub-component
├── TechStackSection.jsx    (31 lines) — badge grid with hover effects
├── ContactSection.jsx      (31 lines) — social link icons
└── home.css               (100 lines) — all HomePage styles, mobile-first
```

HomePage.jsx now only contains state + event handlers. Rendering delegated to section components.

**DocumentsPage.jsx (679 lines → 360 lines + 2 new components + 1 CSS file)**

```
src/pages/docs/
├── DocSearch.jsx           (80 lines) — search input + dropdown + history
├── DocTags.jsx             (25 lines) — tag filter buttons
└── docs.css               (120 lines) — all doc styles, mobile-first
```

### CSS file placement rule

Page-specific CSS lives in the page's subdirectory (e.g. `pages/home/home.css`).
Import once in the main page component: `import './home/home.css'`.
Sub-components inside the same directory do NOT re-import it — prevents duplicate CSS.

---

## Phase 4: Route-Based Code Splitting

### App.jsx with lazy routes

```jsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout';
import { ErrorBoundary } from './components/shared';

const HomePage = lazy(() => import('./pages/HomePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'));
const UtilitiesPage = lazy(() => import('./pages/UtilitiesPage'));
const WidgetPage = lazy(() => import('./pages/WidgetPage'));
const HermesPage = lazy(() => import('./pages/HermesPage'));

function PageFallback() {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
    <div className="spinner" style={{ width: '32px', height: '32px' }} />
  </div>;
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Suspense fallback={<PageFallback />}><HomePage /></Suspense>} />
          <Route path="dashboard" element={<Suspense fallback={<PageFallback />}><DashboardPage /></Suspense>} />
          {/* ... other routes ... */}
          <Route path="*" element={<div>404</div>} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
```

### Build output (45 chunks)

Each page gets its own chunk. CSS files are also split per page:
- `HomePage-CtR_ATRq.js` (8.46 KB) + `HomePage-TS8SmxRq.css` (4.27 KB)
- `DashboardPage-T81gEc93.js` (16.80 KB)
- `DocumentsPage-NHnhP2qP.js` (43.50 KB) + `DocumentsPage-D78JkFT8.css` (3.89 KB)
- `UtilitiesPage-Dt6UrzJ7.js` (6.52 KB)
- `WidgetPage-D7hdcSnT.js` (9.11 KB)
- `HermesPage-o0AmBehk.js` (0.61 KB)

---

## Phase 5: Agent-Friendly Architecture

### Barrel exports

```
src/components/
├── ui/index.js          — exports Button, Card, Badge, Input, GlassPanel, Skeleton, Spinner, EmptyState
├── layout/index.js      — exports AppLayout, Navbar, Footer, BottomTab
├── shared/index.js      — exports ToastProvider, useToastContext, ErrorBoundary, BlobBackground
└── index.js             — umbrella: exports commonly used components
```

Usage: `import { AppLayout } from './components/layout';` instead of deep paths.

### Section markers

Every file uses `// ── SECTION ──` comments to separate logical blocks:

```jsx
// ── State ──
const [foo, setFoo] = useState();

// ── Effects ──
useEffect(() => { ... });

// ── Handlers ──
const handleClick = () => { ... };

// ── Render ──
return ( ... );
```

### Max file size

Soft limit: ~400 lines. DashboardPage (369 lines) and DocumentsPage (360 lines with sub-components) stay under this. If a file approaches 400 lines, split it into sub-components.

### Consistent naming

- Components: PascalCase (`HeroSection`, `DocSearch`)
- Hooks: camelCase (`useMediaQuery`, `useToast`)
- CSS files: kebab-case (`home.css`, `docs.css`)
- Sub-directories: kebab-case (`home/`, `docs/`)

---

## WidgetPage: Auto-Register Pattern (Vite-Safe)

### Problem

Dynamic `lazy(() => import(./widgets/${widget.component}.jsx))` with template literals fails in Vite because Vite's static analysis can't resolve dynamic import paths.

### Solution: Static widget map

```jsx
// WidgetPage.jsx
import { lazy } from 'react';

const widgetMap = {
  random: lazy(() => import('./widgets/RandomDiscovery.jsx')),
  dice: lazy(() => import('./widgets/DiceRoller.jsx')),
  coin: lazy(() => import('./widgets/CoinFlip.jsx')),
  // ... one line per widget
};

// Usage:
const ActiveWidget = selected ? widgetMap[selected] : null;
```

Each widget needs exactly 1 line in `widgetMap`. The `widgetData.js` file defines metadata (icon, name, description, badges). Adding a new widget requires:
1. Create `WidgetName.jsx` with `export default function`
2. Add entry to `widgetData.js`
3. Add 1 line to `widgetMap` in `WidgetPage.jsx`

---

## New Pitfalls

### `lazy(() => import(...))` only works with static string literals

Vite's Rollup-based build uses static analysis for code splitting. Template literals like ``import(`./widgets/${id}.jsx`)`` are not resolved — they produce a runtime error or empty chunk.

**Fix**: Pre-declare every widget import as a static object key (see WidgetPage pattern above).

### CSS `composes:` is NOT supported in non-module CSS imports

When importing CSS via `import './foo.css'` (not `import styles from './foo.module.css'`), Vite's LightningCSS pipeline silently drops `composes: someClass` rules. The composed class gets zero properties.

**Fix**: Always expand composed rules inline — copy all properties from the source class.

### `await` inside `setInterval` callbacks

```js
// BROKEN — esbuild rejects this
setInterval(async () => { const result = await fetch(...); }, 30000);

// FIXED — use .then() instead
setInterval(() => { fetch(...).then(result => { ... }).catch(() => {}); }, 30000);
```

### Navbar/BottomTab route paths must match

If `App.jsx` defines route as `/widgets` but `BottomTab` links to `/random-widget`, the tab never highlights active. Always verify tab array routes match exactly what's in `<Route path="...">`.

### BottomTab on HermesPage

HermesPage uses `position: fixed; inset: 0` for fullscreen iframe. BottomTab (`position: fixed; bottom: 0; z-index: 500`) sits ABOVE the iframe on mobile. This is correct — the tab bar should always be reachable. The iframe fills the space between navbar and tab bar.

### AppLayout padding for bottom tab

```jsx
<main style={{
  paddingTop: '56px',                    // navbar height
  paddingBottom: isMobile ? '72px' : 0,  // bottom tab space on mobile
  minHeight: '100dvh',
}}>
```

### ToastProvider refactor: named export

If `useToast.js` changes from `export default function useToast()` to `export function useToast()`, the `ToastProvider` import must also change:

```js
// OLD
import useToast from '../../hooks/useToast';

// NEW
import { useToast } from '../../hooks/useToast';
```

### Page CSS import paths

When CSS file lives in a sub-directory (`pages/home/home.css`), import from main page: `import './home/home.css'`.
When a component inside that sub-directory (`pages/home/HeroSection.jsx`) tries to import, it uses `import './home.css'` (relative to its own location). Better: import CSS ONLY in the main page component, never in sub-components.

---

## Build verification checklist

After each phase, run `npm run build` and verify:
- [ ] 0 errors
- [ ] 0 warnings (CSS comment format hints are benign)
- [ ] Every page produces its own chunk (code-splitting working)
- [ ] CSS files are included for pages that need them (HomePage, DocumentsPage)
- [ ] Shared vendor (`index-*.js`) includes react, react-dom, react-router-dom
