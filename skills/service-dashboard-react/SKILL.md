---
name: service-dashboard-react
title: Service Dashboard React Patterns
description: >
  React 19 + Vite patterns for btdat.io.vn service-dashboard — props sync debugging,
  DOCX-to-PDF rendering in DocReader, inline style gotchas, build/deploy checklist.
  Full error map for the pages/ tsx migration: references/tsx-migration-error-map.md.
category: software-development
trigger:
  - "DocReader"
  - "Documents page"
  - "props không khớp"
  - "DocSidebar"
  - "navbar upgrade"
  - "convert docx"
  - "service-dashboard React"
  - "inline style React"
  - "TS2322"
  - "CSSProperties"
  - "tsc --noEmit"
  - "widgets/*.tsx"
  - "jsx to tsx migration"
  - "Record<string, CSSProperties>"
  - "liquid-*"
  - "refactor to liquid"
  - "command palette"
  - "Ctrl+K"
  - "toast redesign"
  - "skeleton loader"
  - "blob background"
  - "page transition"
  - "useNavigation"
  - "BrowserRouter"
  - "404 page"
  - "liquid glass UI"
  - "progressive enhancement"
  - "accessibility"
  - "reduced motion"
  - "scroll progress"
  - "keyboard shortcut"
  - "code split"
  - "font preload"
  - "real stats"
  - "auto theme"
  - "back to top"
  - "ShortcutHelper"
  - "useShortcutHelper"
  - "AnimatedCounter"
  - "counter animation"
  - "rotating tagline"
  - "hero 3D"
  - "Scene3D"
  - "LiveStatsBar"
  - "homepage redesign"
  - "TechStackSection"
  - "LiveServicesSection"
  - "stagger animation"
  - "CRT terminal"
  - "retro terminal"
  - "scanlines"
  - "crt overlay"
  - "crt flicker"
  - "boot sequence"
  - "terminal prompt"
  - "ASCII logo"
  - "phosphor green"
  - "homepage terminal"
  - "dark design"
  - "bình thường quá"
  - "đập đi xây lại"
version: "1.8"

---

## TypeScript: widgets style-map errors (TS2322)

All 13 `src/pages/widgets/*.tsx` files hit TS2322 at `style={...}` usage sites because their
`const S = {...}` style maps are unannotated → string literals widen to `string`, which is not
assignable to CSSProperties union types (`TextAlign`, `FlexDirection`, `FlexWrap`, ...).

Fix: `const S: Record<string, CSSProperties> = {...}` for plain maps;
`Record<string, any>` for maps containing functions (`diceBtn: (active) => ...`) — NEVER
`Record<string, CSSProperties | fn>` (union breaks narrowing: TS2349 at call sites).

Full recipe, the 3 non-TS2322 errors (Date.getTime, e.currentTarget), and verification:
`references/typescript-widget-fixes.md`.

## CRT Retro Terminal Theme (July 2026 — Major redesign)

Full reference at `references/retro-terminal-crt.md`. Triggers: user says "chán", "bình thường quá", "đập đi xây lại", or explicitly chooses Retro Terminal / CRT style.

The homepage was completely rewritten from Liquid Glass (3D scene + glassmorphism) to a **Retro CRT Terminal** aesthetic. This is a complete theme swap, not incremental.

**Key architectural changes:**
- `tokens.css` `[data-theme="dark"]` overridden: `radius:0px`, `accent:#00ff41`, shadows→green glow, font→Geist Mono everywhere
- `components.css` gets CRT effect classes: `.crt-overlay` (scanlines), `.crt-curve` (vignette), `.crt-flicker` (subtle opacity), `.terminal-cursor` (blink block), `.term-dot`/`.on`/`.off`/`.err` (square status indicators)
- `HomePage.jsx` rewritten with: boot sequence (sessionStorage single-play), ASCII art logo, interactive \$ prompt with typed commands, monospace service list, SSH simulator
- Scene3D component removed (doesn't fit terminal aesthetic)
- Taste Design rules intentionally broken (radius, saturation, font lock) — user explicitly chose this direction

**CRT gotcha — `content` property in CSS:** When building the `.terminal-frame::before` pseudo-element with mixed strings and `attr()`:
```css
/* BROKEN — Vite build fails with "Unclosed string" */
content: '┌── ' attr(data-title) ' ' ──┐';
/* FIXED */
content: '┌── ' attr(data-title);
```

## Phase 3: Accessibility, Performance, Real Data

Full patterns at `references/phase3-accessibility-performance.md`. Summary:

- **Auto theme:** `useTheme.js` detects `prefers-color-scheme` on first visit, listens for OS changes, manual toggle overrides
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` kills all animations — in `mobile-ux.css`
- **Scroll progress bar:** 2px cyan gradient under navbar, `useState(scrollProgress)` + scroll listener
- **ShortcutHelper (`?` key):** New component `ShortcutHelper.jsx`, hook `useShortcutHelper()`, shows all keyboard shortcuts
- **Code split 3D:** `lazy(() => import('../components/Scene3D'))` + `Suspense` — HomePage 922KB → 25KB
- **Font preload:** `<link rel="preload">` in `index.html` for Geist Sans/Mono woff2 files
- **Real stats:** StatsDashboard reads live `fetchServices()` count + uptime from oldest `startedAt`, removed hardcoded numbers
- **Back-to-top:** Floating round button (40px circle), appears after 400px scroll, spring animated

---

## HomePage Patterns

See `references/homepage-patterns.md` for the Liquid Glass (3D + glassmorphism) version.

See `references/retro-terminal-crt.md` for the CRT Retro Terminal version.

The CRT variant was created when user rejected the Liquid Glass design as "bình thường quá" — demonstrating that the user prefers bold, unique directions over conventional polished designs. When choosing terminal-style design:
- All radius → 0px (no rounding)
- Single phosphor green accent (#00ff41) on near-black (#050805)
- 100% monospace font
- CRT scanline overlay + vignette + flicker animation
- Boot sequence with sessionStorage skip
- Interactive $ prompt with typed commands
- ASCII art logo in `<pre>` tags
- Square status indicators (`.term-dot`) not round dots

Seven-section architecture:

1. **HeroSection** — Scene3D background + gradient title + rotating taglines (AnimatePresence, 3.5s interval)
2. **LiveStatsBar** — Glass pill with API-driven counters using AnimatedCounter (IntersectionObserver + requestAnimationFrame)
3. **FeaturesGrid** — 6 glass cards with stagger scroll-reveal (motion whileInView + delay multiplier)
4. **TechStackSection** — Categorized pill badges with inline hover handlers
5. **LiveServicesSection** — Real-time service cards from API with pulse-dot status
6. **AISection** — Hermes feature card with CTA
7. **TerminalContact** — Fake SSH terminal typing effect

Key patterns: AnimatedCounter component, rotating tagline via setInterval + AnimatePresence, stagger animation via index multiplier, inline hover handlers for badge color swap.

---

## Props Mismatch: The Silent Killer

When a child component gets rewritten but the parent still passes old prop names, React doesn't throw — it just passes `undefined` for the missing props. User clicks → crash in ErrorBoundary with no clear error.

**Example (this session):** `DocSidebar` was rewritten with props `currentDoc`, `onSelectDoc`, `searchQuery`, `setSelectedTags` etc. But `DocumentsPage` still passed `activeId`, `onSelect`, `onDelete` etc. `onSelectDoc` = undefined → click → crash.

**Detection workflow:**
1. Read BOTH files side-by-side (`read_file` parent + child)
2. Compare prop destructuring in child vs prop passing in parent
3. Any mismatch → full rewrite of parent's section that renders the child
4. Use `write_file`, not incremental `patch` — too many changes

**Prevention:** When rewriting a child's props API, always open the parent at the same time and update both. Never assume "the parent will pass the right things."

## DocReader: DOCX → PDF via LibreOffice

See `references/docx-to-pdf.md` for the full implementation reference.

**Server endpoint:** `GET /api/documents/:id/pdf`
- Converts `.docx` to PDF using `convertDocxToPdf()` (LibreOffice headless)
- Caches PDF output, serves with `application/pdf` + `Cache-Control: public, max-age=3600`

**Client implementation pattern:**

```jsx
const isDocx = doc?.ext === 'docx' || (doc?.file || '').endsWith('.docx');
const pdfUrl = isDocx ? `/api/documents/${doc?.id}/pdf` : null;

// Pre-fetch to trigger server-side conversion
useEffect(() => {
  if (isDocx) {
    setPdfLoading(true);
    fetch(pdfUrl).finally(() => setPdfLoading(false));
  }
}, [doc?.id, isDocx, pdfUrl]);

// Conditional rendering
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
  <div dangerouslySetInnerHTML={{ __html: renderedHtml }} />
)}
```

**Key details:**
- Hide inapplicable controls for docx: font size, TOC button, edit button
- Download raw .docx via `GET /api/documents/:id?dl=1` (creates `<a>` element with download attr)
- Show DOCX badge in meta section (blue pill with `fa-file-word` icon)
- Loading state matters: LibreOffice conversion takes 2-5 seconds first time

## React Inline Style Gotchas

### No pseudo-elements in inline styles
You can't use `::after` or `::before` in React inline style objects. Workarounds:

1. **Gradient borders via `backgroundImage` trick:**
```jsx
borderBottom: '2px solid transparent',
backgroundImage: `linear-gradient(var(--glass-bg), var(--glass-bg)), 
                   linear-gradient(90deg, transparent, var(--accent), var(--green), transparent)`,
backgroundOrigin: 'border-box',
backgroundClip: 'padding-box, border-box',
```

2. **Actual DOM elements** — add a `<span>` or `<div>` as a pseudo-element substitute
3. **CSS classes** — define the pseudo-element in `components.css` and add the class to the JSX element

### Always include both `backdropFilter` + `WebkitBackdropFilter`
Chrome needs `WebkitBackdropFilter`, Firefox uses `backdropFilter`. Always write both:

```jsx
backdropFilter: 'blur(16px)',
WebkitBackdropFilter: 'blur(16px)',
```

### Animation keyframes must live in CSS files
React inline styles can't define `@keyframes`. Add them to `components.css` and reference by name.

### Prefer liquid-* CSS classes over raw inline styles

The project has a Liquid Glass Design System defined in `components.css`. When building cards, stat displays, buttons, inputs, or panels, **prefer these CSS classes** instead of writing inline style objects. This keeps the design consistent and reduces JSX bloat.

**Class → use case mapping:**

| Class | Use for |
|-------|---------|
| `liquid-card` | Service/feature cards, any interactive card with backdrop blur + hover prismatic effect |
| `liquid-stat` | Stat dashboard cards with value + label (hover lift, accent border on hover) |
| `liquid-stat-value` | Large stat number inside `.liquid-stat` |
| `liquid-stat-label` | Uppercase label text inside `.liquid-stat` |
| `liquid-panel` | Section containers, non-interactive panels with top accent line |
| `liquid-btn` | Buttons. Modifiers: `.primary` (accent fill), `.danger` (red tint), `.sm` (small) |
| `liquid-input` | Form inputs with glass blur styling |
| `liquid-tabs` / `liquid-tab` | Tab bar + individual tabs |

See the "Inline style → liquid-* migration" and "Mixing liquid-* classes with existing inline style objects" sections below for detailed migration patterns.

### Legacy class → liquid-* migration (btn-*, card, glass-panel, input)

When refactoring an existing component that uses the old Bulma-derived utility classes, replace them with the liquid-* design system. This is a direct class-name swap — not a full inline-style rewrite.

**Class mapping table:**

| Old class | New class | Notes |
|-----------|-----------|-------|
| `btn btn-primary btn-sm` | `liquid-btn primary` | Drop `btn-sm` — liquid-btn handles sizing |
| `btn btn-danger btn-sm` | `liquid-btn danger` | |
| `btn btn-glass btn-sm` | `liquid-btn` | Default variant, no modifier needed |
| `btn btn-glass` | `liquid-btn` | |
| `btn btn-primary` | `liquid-btn primary` | |
| `glass-panel` | `liquid-stat` or `liquid-panel` | `liquid-stat` for stat cards; `liquid-panel` for containers/log viewers |
| `card` | `liquid-card` | Interactive cards (services, features) |
| `card` | `liquid-panel` | Non-interactive panels (tables, log containers) |
| `input` | `liquid-input` | |
| `btn btn-primary btn-sm` (tab) | `liquid-tab is-active` | Tab-specific; wrapper div gets `liquid-tabs` |
| `btn btn-glass btn-sm` (tab) | `liquid-tab` | Inactive tab; wrapper div gets `liquid-tabs` |

**What NOT to touch:**
- **Modals** — `ServiceModal`, `ConfirmModal` keep their existing `btn`/`glass-panel` classes. These are isolated overlay components with their own z-index layer and distinct styling needs.
- **Skeleton loaders** — `skeleton skeleton-card` stays as-is.
- **Empty states** — `empty-state` stays as-is.
- **Files in other pages** — only refactor the page/component that was asked for; don't cascade to unrelated pages like `DocumentsPage.jsx`.

**Touch all affected sub-files:** When the target component imports child components (e.g. `ServiceCard`, `LogMonitor`), migrate those too — the refactor isn't done until every class in the component tree is updated. `replace_all=true` is useful for repeated patterns like Refresh buttons.

**Verification step:** After migration, grep the affected files for residual `btn-primary|btn-glass|btn-danger|btn-sm|glass-panel` and confirm only modal code has them.

### Mixing liquid-* classes with existing inline style objects

When a component already uses inline style objects for layout (`s.container`, `s.header`, etc.) but you want the liquid glass aesthetic handled by CSS classes, use the **class + style override** pattern:

```jsx
// BEFORE: pure inline style object
<div style={s.container}>

// AFTER: liquid-* class handles glassmorphism; style overrides the bits the class would duplicate
<div className="liquid-panel" style={{
  ...s.container,
  background: 'none',
  backdropFilter: 'none',
  WebkitBackdropFilter: 'none',
  border: 'none',
  borderRadius: 0,
}}>
```

**Why `background: 'none'` etc:** The `liquid-panel` class sets `background: var(--liquid-bg)`, `backdropFilter: blur(20px)`, etc. If the existing `s.container` style object also sets these, you get double-backdrop-filter artifacts. Nullify the duplicated properties in the style object, let the class handle them, but keep the layout properties (flex, display, overflow, gap) from the style object.

**This pattern is the correct approach for DocReader, DocSidebar, and any component that predates the liquid-* system and already has inline style objects.** Don't rewrite the entire component to use only classes — the style objects contain layout logic that works; the class overlay just upgrades the visual skin.

### Inline style → liquid-* migration (new components)

**Migration pattern (inline → class):**

```jsx
// BEFORE: inline style blob
<motion.div style={{
  background: 'rgba(10,14,23,0.6)', borderRadius: 'var(--radius-md)',
  padding: '1.2rem', textAlign: 'center',
  border: '1px solid rgba(52,211,153,0.1)',
  backdropFilter: 'blur(8px)',
}} whileHover={{ borderColor: '...', scale: 1.02 }}>

// AFTER: liquid-* class
<motion.div className="liquid-stat">
```

**Important:** When switching to `liquid-card`/`liquid-stat` classes, **remove** `whileHover` border-color/scale overrides — the CSS `:hover` pseudo-class handles these effects. Only keep motion library props that don't conflict (`initial`, `animate`, `whileTap` for press feedback, `transition` for stagger delays).

**Card with status-specific overrides:** Use `className="liquid-card"` for the base, then override only the status-dependent properties via inline `style`:
```jsx
<motion.div
  className="liquid-card"
  style={{
    background: svc.status === 'running' ? 'rgba(34,197,94,0.08)' : undefined,
    border: svc.status === 'running' ? '1px solid rgba(34,197,94,0.2)' : undefined,
  }}
>
```

**Toggle buttons on cards:** When migrating card `onClick` to a button, use:
```jsx
<button
  className={`liquid-btn sm ${isRunning ? 'danger' : 'primary'}`}
  onClick={(e) => { e.stopPropagation(); onToggle(item, isRunning ? 'stop' : 'start'); }}
  style={{ marginTop: '0.6rem', width: '100%' }}
>
  {isRunning ? 'Stop' : 'Start'}
</button>
```

## Build & Deploy Checklist

After every source change:

```bash
# 1. Build
cd ~/service-dashboard/frontend && npm run build

# 2. Kill server (TARGETED — never taskkill -f -im node.exe)
for pid in $(netstat -ano | grep ":3000.*LISTEN" | awk '{print $NF}' | sort -u); do
  taskkill -f -pid $pid 2>/dev/null
done

# 3. Start server (background=true)
cd /c/Users/datel/service-dashboard && node server.js 2>&1

# 4. Verify BOTH local + CDN
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/documents
curl -s -o /dev/null -w "%{http_code}" https://btdat.io.vn/documents

# 5. Verify hash match (ensures CDN isn't serving stale build)
curl -s http://localhost:3000/ | grep -oP 'index-[A-Za-z0-9]+\.'
curl -s https://btdat.io.vn/ | grep -oP 'index-[A-Za-z0-9]+\.'

# 6. Commit + push
cd ~/service-dashboard && git add -A && git commit -m "type: description" && git push origin master
```

## Glassmorphism Standard

Every card/container follows this pattern:
```jsx
background: 'var(--glass-bg)',
backdropFilter: 'blur(16px)',
WebkitBackdropFilter: 'blur(16px)',
border: '1px solid var(--glass-border)',
borderRadius: 'var(--radius-lg)',
boxShadow: 'var(--shadow-sm)',
```

Hover elevation:
```jsx
boxShadow: 'var(--shadow-md)',
transform: 'translateY(-2px)',
transition: 'all var(--transition-slow)',
```

## BrowserRouter vs DataRouter: `useNavigation()` Gotcha

**CRITICAL:** `useNavigation()` chỉ hoạt động với data routers (`createBrowserRouter`). App btdat.io.vn dùng `<BrowserRouter>` (component router). Gọi `useNavigation()` từ component router context → silent runtime crash:

```
useNavigation() may be used only in the context of a <DataRouter>
```

**Fix — manual pathname tracker:**
```jsx
const location = useLocation();
const [navigating, setNavigating] = useState(false);
useEffect(() => {
  setNavigating(true);
  requestAnimationFrame(() => setNavigating(false));
}, [location.pathname]);
```

Dùng `requestAnimationFrame` để skeleton render ít nhất 1 frame trước khi tắt. Nếu set `false` ngay trong cùng tick, skeleton không bao giờ hiển thị.

**Also unavailable với BrowserRouter:** `useLoaderData()`, `useActionData()`, mọi data-router-only hook.

## Animated Blob Backgrounds

3 gradient blobs drifting chậm phía sau toàn site. CSS-only, no JS loop.

**CSS:** `mobile-ux.css` hoặc `components.css`:
```css
.animated-blobs { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.animated-blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.12; animation: blobDrift 20s ease-in-out infinite; }
/* 3 blobs: cyan top-left 22s, lighter-cyan right 25s, deep-cyan bottom-left 18s, staggered delays */
@keyframes blobDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(40px, -30px) scale(1.15); }
  50% { transform: translate(-20px, 20px) scale(0.9); }
  75% { transform: translate(30px, 10px) scale(1.1); }
}
```

**Mobile:** Disable (`isMobile` check) + `@media` giảm opacity 0.06, blur 60px. Blur GPU-heavy trên mobile.

## Liquid Skeleton Loaders

Shimmer placeholder thay spinner cũ khi navigation loading.

**CSS:**
```css
.liquid-skeleton {
  background: linear-gradient(110deg, rgba(255,255,255,0.03) 8%, rgba(255,255,255,0.08) 18%, rgba(255,255,255,0.03) 33%);
  background-size: 200% 100%;
  animation: liquidShimmer 1.8s ease-in-out infinite;
  border-radius: var(--radius-lg); border: 1px solid var(--liquid-border);
}
@keyframes liquidShimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

**Usage:** `<div className="liquid-skeleton" style={{ height: '200px' }} />` — match content shape.

## Toast: Liquid Glass Redesign

`motion/react` + `AnimatePresence` + `liquid-panel`. Key changes from old:
- Spring physics: stiffness 400, damping 28
- Color-coded icon circles (24px, tinted bg)
- Colored inset border: `boxShadow: inset 0 0 0 1px <color>20`
- Position: `top: calc(var(--navbar-height) + 0.5rem)`
- 4 types: success (green), error (red), info (cyan), warning (amber)

## Command Palette (Ctrl+K)

Glass overlay search. Architecture:
- `CommandPalette.jsx` — component in AppLayout, open/onClose props
- `useCommandPalette()` hook — listens Ctrl+K/Cmd+K, returns `{ open, close, toggle }`
- 6 routes với icon, label, Vietnamese keywords
- Arrow keys navigate, Enter select, Escape close
- `useHaptic().light()` cho mobile tap feedback
- Auto-closes on route change

## Page Transitions in AppLayout

```jsx
<AnimatePresence mode="wait">
  <motion.div key={location.pathname}
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.2, ease: 'easeOut' }}>
    {navigating ? <SkeletonFallback /> : <Outlet />}
  </motion.div>
</AnimatePresence>
```

`mode="wait"` → exit animation xong mới enter. `key={location.pathname}` → trigger trên mọi route change.

## 404 Page: Liquid Glass

SVG gradient text + `liquid-panel` + spring animation (`stiffness: 200, damping: 15`). CTA button + Ctrl+K hint.

## Parallel Subagent Dispatch for Multi-Page Refactors

When refactoring 5+ pages to liquid-* classes, dispatch one subagent per page in parallel batches of 3 (max concurrent limit). Each subagent gets:
- Full file path + context about which classes to use
- Self-contained instructions (no shared state between agents)
- Verification step: build or grep check

**Effective batch pattern:**
```
Batch 1: HomePage, DashboardPage, WidgetPage (3 agents)
Batch 2: UtilitiesPage, DocumentsPage (2 agents)
```

Each agent works in isolation on one file. No cross-agent dependencies. Results consolidate after all finish.

**Verify after all agents return:** `npm run build` — catches import errors, syntax issues, missing classes across all pages at once.

## Mobile Responsive Pattern

```jsx
import { useMediaQuery } from '../../hooks/useMediaQuery';

const { isMobile } = useMediaQuery();

// Then inline:
style={{ flexDirection: isMobile ? 'column' : 'row' }}
// Or className:
className={isMobile ? 'mobile-stack' : 'desktop-row'}
```

Mobile breakpoint: 768px. Use `isMobile` from hook, or CSS media queries in `components.css`.
