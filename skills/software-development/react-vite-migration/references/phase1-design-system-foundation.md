# Phase 1 Design System Foundation — Implementation Notes (July 2026)

Patterns and pitfalls from implementing Phase 1 of the agent-friendly refactoring plan.

## What Phase 1 Delivers

1. **CSS design system** — `src/styles/tokens.css` + `reset.css` + `utilities.css` + `components.css`, imported via `main.jsx`, through Vite pipeline
2. **8 UI components** — Button (primary|glass|danger|icon, sm|md|lg), Card (with hover), Badge (accent|green|red|amber), Input, GlassPanel, Skeleton, Spinner, EmptyState
3. **AppLayout wrapper** — single source of truth: `<AppLayout><Page /></AppLayout>` handles BlobBackground + Navbar + main padding + Footer (desktop) or BottomTab (mobile)
4. **BottomTab.jsx** — iOS-style fixed bottom nav for mobile with safe-area inset, active indicator dot
5. **ErrorBoundary** — catches render crashes, shows fallback UI with retry button
6. **ToastProvider** — global context (`useToastContext()`), animated stack
7. **useMediaQuery()** — `{ isMobile, isTablet, isDesktop, isWide }` with requestAnimationFrame throttle
8. **404 page** — custom glass card with animation

## Key Implementation Patterns

### AppLayout wraps everything
```jsx
// App.jsx — one level
<AppLayout>
  <Routes>
    <Route path="/" element={<ErrorBoundary><HomePage /></ErrorBoundary>} />
  </Routes>
</AppLayout>

// AppLayout.jsx
<BlobBackground />
<Navbar />
<main style={{ paddingTop: '56px', paddingBottom: isMobile ? '72px' : 0 }}>
  <div className="page-enter">{children || <Outlet />}</div>
</main>
{isMobile && <BottomTab />}
<Footer />  {/* desktop only */}
```

### Removing duplicate Navbar/BlobBackground from all pages
Every page had these 3 lines at the top of render:
```jsx
<BlobBackground />
<Navbar active="/" />
```
Remove ALL of them. AppLayout handles it. Also remove the imports.

### Toast migration pattern
Old: `import { useToast } from '../hooks/useToast'` → `const toast = useToast();`
New: `import { useToastContext } from '../components/shared/Toast'` → `const toast = useToastContext();`

`useToast.js` becomes a standalone named export (not default), used by `ToastProvider` internally.

### CSS utility class system
Replace inline styles with composable utility classes:
- `.flex`, `.flex-col`, `.items-center`, `.justify-between`, `.gap-sm`, `.gap-md`
- `.btn`, `.btn-primary`, `.btn-glass`, `.btn-danger`, `.btn-sm`
- `.card`, `.card-hover`
- `.badge`, `.badge-accent`, `.badge-green`, `.badge-red`
- `.text-xs`, `.text-sm`, `.text-dim`, `.text-strong`
- `.glass-panel`, `.p-sm`, `.p-md`, `.p-lg`

### Navbar import path fix
When Navbar moves from `components/Navbar.jsx` to `components/layout/Navbar.jsx`, the `useTheme` import changes:
- Old: `import useTheme from '../hooks/useTheme'`
- New: `import useTheme from '../../hooks/useTheme'`

## Pitfalls Specific to Phase 1

### 1. `composes:` not supported in Vite's CSS pipeline
Vite uses LightningCSS which supports `composes:` from CSS Modules, but when the CSS file is imported via a regular `<link>` or JS `import`, `composes:` silently fails — no error, but the rule has no effect. **Always expand composed rules inline**:
```css
/* BROKEN */
.card-hover { composes: card; transition: ... }
/* WORKING */
.card-hover {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  /* ... all card properties expanded ... */
  transition: transform var(--transition-slow), box-shadow var(--transition-slow);
}
```

### 2. `await` in `setInterval` callbacks
`setInterval(async () => {...})` is technically valid `async` — the callback itself IS async. But esbuild may reject it in some configs. Safer pattern: use `.then()/.catch()` instead of `async/await` in setInterval callbacks.

### 3. DashboardPage DOM structure after patching
When removing `<section>` wrappers with patch, the closing `</section>` at bottom of file becomes orphaned. Always verify the full DOM structure after removing a section tag. Better: rewrite the entire page component if it has a history of DOM structure issues.

### 4. Named vs default export in useToast
If `useToast.js` changes from `export default function` to `export function useToast`, all consumers need updating. Widget pages that import `import { useToast } from '../../hooks/useToast'` already use named import — but `Toast.jsx` which did `import useToast from '../../hooks/useToast'` must change to `import { useToast } from '../../hooks/useToast'`.

### 5. Multiple CSS `composes:` errors
Error messages say "Could not resolve" but the real issue is CSS `composes:` found in `.card-hover` and `.glass-card` classes. Must expand ALL composed rules throughout `components.css`.

### 6. File import path in new folder structure
When creating new folders (`components/layout/`, `components/shared/`), all relative imports from within those folders need to go up one extra `../`:
- `components/layout/Navbar.jsx` → `../../hooks/useTheme` (not `../hooks/useTheme`)
- `components/shared/Toast.jsx` → `../../hooks/useToast` (not `./useToast`)

### 7. ToastProvider no longer depends on useToast hook for actual toast state
The original pattern had ToastProvider using `useToast()` to get `{ toasts, toast, dismiss }`. After refactoring `useToast.js` to return just `toast`, the provider must manage its own state with `useState` + `useRef` timers. Keep ToastProvider self-contained.

## Build Verification
After Phase 1, expect **99 modules** (up from 89), 0 build errors. The CSS is now tree-shaken and optimized through Vite, output as `assets/index-*.css` (~10KB gzipped to ~3KB).
