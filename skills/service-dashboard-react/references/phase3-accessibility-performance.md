# Phase 3: Accessibility + Performance + Real Data (July 2026)

## A1: Theme Auto-Detect System Preference

`useTheme.js` now auto-detects `prefers-color-scheme` on first visit (no localStorage key). Manual toggle overrides and persists. Listens for system theme changes via `matchMedia('change')` event.

Key: system preference is a fallback, not an override. Once user manually toggles, localStorage wins.

**File:** `hooks/useTheme.js`

## A2: Reduced Motion Respect

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Place in `mobile-ux.css`. `!important` intentional — must override inline styles + library animations.

## A3: Scroll Progress Bar

Fixed 2px gradient bar under navbar. `useState(scrollProgress)` + scroll listener in AppLayout.

```
position: fixed; top: calc(var(--navbar-height) - 2px); left: 0;
height: 2px; width: <scrollProgress>%;
background: linear-gradient(90deg, var(--accent), var(--green));
transition: width 0.1s linear;
```

## A4: Keyboard Shortcut Helper

New component: `ShortcutHelper.jsx`. Press `?` (no modifier, ignored in input/textarea) → glass overlay showing all shortcuts (Ctrl+K, ?, Esc, ↑↓/Enter).

Hook: `useShortcutHelper()` returns `{ open, close }`. Integrated in AppLayout.

## B1: Code Split Heavy 3D (React.lazy)

```
// BEFORE: import Scene3D from '../components/Scene3D';
const Scene3D = lazy(() => import('../components/Scene3D'));

// JSX:
<Suspense fallback={<Fallback />}>
  <Scene3D />
</Suspense>
```

**Result:** HomePage chunk: 922KB → 25KB (-97%). Three.js pulled into separate chunk.

## B2: Font Preload

In `index.html`, before Font Awesome CDN:
```html
<link rel="preload" href="/node_modules/@fontsource/geist-sans/files/geist-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/node_modules/@fontsource/geist-mono/files/geist-mono-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
```

## C1+C2: Real Stats Over Hardcoded Data

HomePage `StatsDashboard`:
- Services Online: live from `fetchServices()` count
- Uptime: oldest running service's `startedAt` timestamp
- Removed: "AI Models: 3" and "Requests/Day: 12K" (hardcoded, no API source)

## Back-to-Top Floating Button

AppLayout: round floating button (40px, `borderRadius: 50%`), appears after 400px scroll. Spring animated enter/exit. Position aware of mobile bottom-nav height.
