---
name: service-dashboard-frontend
title: Service Dashboard Frontend (React + Vite)
description: >
  Code giao diện FE cho btdat.io.vn service-dashboard: React 19 + Vite + inline styles +
  CSS custom properties. Glass-morphism, mobile-first, Node.js + Cloudflare Tunnel.
category: software-development
trigger:
  - "sửa UI dashboard"
  - "sửa navbar"
  - "sửa header"
  - "responsive layout"
  - "nâng cấp giao diện"
  - "cải thiện UX"
  - "đổi style"
  - "làm giao diện"
  - "thêm animation"
  - "liquid glass"
  - "làm lại footer"
  - "footer menu"
  - "bottom tab"
  - "mobile nav"
version: "1.0"
---

## Stack

- **Framework**: React 19 (function components, hooks)
- **Build**: Vite (`npm run build` → `dist/`)
- **Styles**: Inline JS object styles + CSS custom properties (`tokens.css`)
- **CSS files**: `tokens.css` (design tokens dark/light), `components.css` (shared classes + keyframes + noise overlay), `reset.css`, `utilities.css`
- **Font**: Geist + Geist Mono (`@fontsource/geist-sans` 400/500/600/700, `@fontsource/geist-mono` 400/500) — self-hosted, no Google Fonts CDN
- **Icons**: Font Awesome 6 (via CDN in `index.html`). Không dùng Phosphor/Lucide — tất cả icons trong project là `fa-*` classes
- **Theme**: `data-theme="dark"/"light"` on `<html>`, `useTheme()` hook, localStorage persist
- **Accent**: Cyber Cyan `#00d4ff` / `#00a8e0` hover — **1 accent duy nhất** (chosen per user direction on 2026-07-26 for tech/AI vibe). Formerly Emerald. No AI purple, no multi-accent.
- **Shadows**: Tinted `rgba(10,14,23,0.x)` — never pure `rgba(0,0,0,...)`. `--glass-shadow` same tint.
- **Server**: Node.js `server.js` port 3000
- **Deploy**: Cloudflare Tunnel → `btdat.io.vn`

## Taste Skill integration

Project uses 2 Hermes skills from [Taste Skill](https://www.tasteskill.dev):

| Skill | When |
|-------|------|
| `taste-redesign` | Audit + redesign existing codebase → Scan → Diagnose → Fix |
| `taste-design` | Build new components → anti-slop rules, 3-dial tuning, pre-flight check |

**Workflow:** Before large UI feature → `skill_view("taste-redesign")` → audit checklist → fix by priority. New component → `skill_view("taste-design")` → check rules.

**Pre-Flight Check (before every deploy):**
- [ ] Font is Geist, not Inter
- [ ] 1 accent color only (Cyber Cyan), no AI purple
- [ ] `100dvh` not `100vh` for full-screen sections
- [ ] Shadows tinted to `rgba(10,14,23,...)`, not pure black
- [ ] All buttons have hover + active + focus-visible + transition
- [ ] Noise overlay active in AppLayout
- [ ] No AI buzzwords ("Elevate", "Seamless", "Unleash")
- [ ] `z-index` scale consistent (no `9999`)
- [ ] Scroll progress bar present (AppLayout)
- [ ] `@media (prefers-reduced-motion: reduce)` in mobile-ux.css
- [ ] Font preload links in index.html
- [ ] Design Audit Checklist passed (see section above)

**3-Dial Tuning for btdat.io.vn:**
- `VARIANCE: 7` — có asymmetry nhẹ, không centered hết
- `MOTION: 5` — có animation nhưng restrained
- `DENSITY: 4` — airy nhưng đủ data cho dashboard

## Premium Motion System

Project uses 3 libraries for cinematic motion. Full reference: `references/premium-motion-system.md`.

| Library | Size (gzip) | Purpose |
|---------|-------------|---------|
| `lenis` | ~5.6KB | Smooth scroll — Apple/Linear/Vercer standard |
| `motion` | ~30KB | Spring physics, stagger, scroll-linked, AnimatePresence |
| `canvas-confetti` | ~2KB | Confetti burst on CTA |

**Components for motion (3D rebuild replaces old):**
- `Scene3D.jsx` — React Three Fiber background: torus knots + icosahedron + 500 instanced particles (replaces old WireframeSphere, GlitchText, AIBadge)
- `NeuralNodes.jsx` — Service nodes as neural network visualization with SVG connection lines
- `TerminalContact.jsx` — Fake SSH terminal with sequential typing + contact actions
- `Cursor.jsx` — custom magnetic spring cursor (desktop only)

**Patterns:**
- Page transitions: `AnimatePresence mode="wait"` wrapping `<Outlet>`
- Scroll parallax: `useScroll()` + `useTransform()` from Motion
- 3D tilt cards: `onMouseMove` → `perspective() rotateX() rotateY()`
- Stagger reveal: Motion variants with `staggerChildren`
- CountUp: `useInView({ once: true })` → setInterval counter
- Rotating border: CSS `@property` + `conic-gradient` on `::before`

### Lenis gotchas
- Lazy-import in `useEffect` — never block initial render
- `lerp: 0.065` desktop, `0.1` mobile (higher to avoid lag on touch)
- `syncTouch: true` preserves native scroll accessibility
- Always `destroy()` on unmount

### Cursor gotchas
- Hide on touch: `window.matchMedia('(pointer: coarse)').matches`
- `z-index: 100000` — above everything including modals
- `pointer-events: none` — never blocks clicks
- Detect hover targets via `e.target.closest('a, button, .card, ...')`

## Project structure

```
frontend/src/
  components/layout/  ← Navbar, Footer, BottomTab, AppLayout
  components/shared/  ← BlobBackground, Toast, ConfirmModal
  hooks/              ← useTheme, useMediaQuery, useScrollNav, useDocuments
  pages/              ← HomePage, DashboardPage, DocumentsPage, UtilitiesPage, WidgetPage, HermesPage
    docs/             ← DocReader, DocEditor, DocSidebar, DocSearch, DocTags
  styles/             ← tokens.css, components.css, reset.css, utilities.css
  main.jsx            ← Entry, React Router
dist/                 ← Build output
server.js             ← Node HTTP server
```

## Style conventions

- **Glass-morphism** (base): `background: var(--glass-bg)`, `backdropFilter: blur(Npx)`, `border: 1px solid var(--glass-border)`, `borderRadius: var(--radius-lg)`
- **Liquid Glass** (preferred for cards/panels/inputs/buttons): Use CSS classes `.liquid-card`, `.liquid-panel`, `.liquid-input`, `.liquid-btn`, `.liquid-tabs/.liquid-tab`, `.liquid-stat` from `components.css`. These have depth layering (raise/float/modal), prismatic hover overlay, and mobile blur reduction. Full reference: `references/liquid-glass-system.md`. Migrate old `.card`/`.glass-panel`/`.btn-glass` to liquid equivalents.
- **Inline styles**: Object constants `const s = { ... }` ở đầu file component
- **Tokens**: Tất cả màu sắc/border-radius/shadow qua `var(--xxx)` từ `tokens.css`
- **Mobile-first**: `useMediaQuery()` hook → `isMobile`, flex-wrap, minWidth: 0
- **No**: Service Worker, manifest.json, skip-to-content, view-transition, full-screen overlay, native confirm()

## Build + Deploy workflow

Mỗi lần sửa FE:

1. **Build**: `cd ~/service-dashboard/frontend && npm run build`
2. **Kill server**: 
   ```bash
   for pid in $(netstat -ano | grep ":3000.*LISTEN" | awk '{print $NF}' | sort -u); do
     taskkill -f -pid $pid 2>/dev/null
   done
   ```
3. **Start**: `node server.js` (background) trong `/c/Users/datel/service-dashboard`
4. **Verify hash + 200**:
   ```bash
   curl -s http://localhost:3000/ | grep -oP 'index-[A-Za-z0-9]+\.'
   curl -s https://btdat.io.vn/ | grep -oP 'index-[A-Za-z0-9]+\.'
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
   curl -s -o /dev/null -w "%{http_code}" https://btdat.io.vn/
   ```
5. **Commit + push**: `git add -A && git commit -m "..." && git push origin master`

## Navbar — Liquid Glass Pattern

File: `components/layout/Navbar.jsx`. Uses SVG gradient logo + layoutId animated pill + animated ThemeToggle + liquid-btn class + AnimatePresence mobile menu.

### SVG Gradient Logo (Logomark component)
```jsx
function Logomark() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30">
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--accent)" />
          <stop offset="100%" stopColor="var(--green)" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="26" height="26" rx="7" fill="url(#logo-grad)" className="logo-rect" />
      <path d="M16 5 L9 15 H13 L11 25 L20 13 H15 L18 5 Z" fill="white" />
    </svg>
  );
}
```
- SVG inline để gradient dùng CSS variables (hoạt động light/dark)
- `className="logo-rect"` → `@keyframes logoPulse` glow filter
- Lightning bolt custom path — không dùng emoji thô
- **Pitfall:** `<linearGradient>` với `var(--accent)` cần verify trong light mode

### Animated Theme Toggle (ThemeToggle component)
```jsx
function ThemeToggle({ theme, toggle }) {
  return (
    <motion.button onClick={toggle} className="liquid-btn" whileTap={{ scale: 0.9 }}>
      <AnimatePresence mode="wait">
        <motion.span key={theme}
          initial={{ rotate: -90, opacity: 0, scale: 0.5 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 90, opacity: 0, scale: 0.5 }}>
          <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`} style={{ color: 'var(--amber)' }} />
        </motion.span>
      </AnimatePresence>
    </motion.button>
  );
}
```
- `key={theme}` để AnimatePresence morph giữa ☀↔☾
- Icon màu amber (vàng) — nhất quán semantic

### Active Pill (layoutId spring — preferred over CSS animation)
```jsx
{active && (
  <motion.span layoutId="nav-pill"
    style={{ position: 'absolute', bottom: '-2px', left: '50%', width: '55%', height: '2.5px',
      borderRadius: '999px', background: 'linear-gradient(90deg, var(--accent), var(--green))',
      boxShadow: '0 0 8px rgba(0,212,255,0.4)' }}
    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
  />
)}
```
- `layoutId="nav-pill"` → Framer Motion animates pill trượt mượt giữa các tab
- **Không dùng** `@keyframes pillSlide` cũ nữa

### Nav Links (liquid hover)
- `className="liquid-btn"` thay inline style thô
- `border: active ? '1px solid rgba(0,212,255,0.12)' : '1px solid transparent'`
- Hover: `rgba(0,212,255,0.03)` bg + `translateY(-1px)`
- Icon active → `color: var(--accent)` + `scale(1.15)`

### Mobile Menu
- `<AnimatePresence>` → backdrop fade + slide spring panel
- `<motion.div>` with `className="liquid-panel"` + `border: 1px solid var(--liquid-border)`
- Menu items: `borderLeft: active ? '3px solid var(--accent)' : ...`
- Theme toggle trong menu: `className="liquid-btn"` full width

### Navbar Scroll States
- `scrolled` boolean từ `useScrollNav(60)`:
  - `background: scrolled ? 'var(--glass-bg)' : 'rgba(17,24,39,0.15)'`
  - `backdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'blur(8px) saturate(100%)'`
  - `borderBottom: scrolled ? '1px solid var(--liquid-border)' : '1px solid rgba(255,255,255,0.03)'`
  - `boxShadow: scrolled ? '0 2px 20px rgba(0,0,0,0.12), inset 0 1px 0 rgba(0,212,255,0.04)' : 'none'`
- Không cần gradient border trick qua `backgroundImage` — liquid-border + inset glow đẹp hơn

## Footer — Glass Dock Pattern

File: `components/layout/Footer.jsx`. Centered floating dock bar (desktop only) — **không phải pill nhỏ góc phải**.

```jsx
<motion.div className="glass-dock"
  initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
  style={{ position: 'fixed', bottom: '1rem', left: '50%', transform: 'translateX(-50%)',
    display: 'flex', gap: '0.75rem', padding: '0.45rem 1rem', borderRadius: '999px',
    background: 'var(--glass-bg)', backdropFilter: 'blur(20px) saturate(180%)',
    border: '1px solid var(--liquid-border)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,212,255,0.04) inset' }}
>
  {/* Left→Right: green dot + live clock(seconds) + date + quick links + Ctrl+K hint */}
</motion.div>
```

**Contents (trái→phải):**
- **Pulsing dot**: `animation: pulse-dot 2s ease-in-out infinite` (CSS keyframe)
- **Live clock**: `setInterval(tick, 1000)` — hiển thị giây thật
- **Date**: `toLocaleDateString('vi-VN', { weekday: 'short', day: 'numeric', month: 'short' })`
- **Divider**: `var(--liquid-border)` style
- **Quick links**: Home / Dashboard / Hermes (`--accent` color)
- **Shortcut hint**: `<kbd>Ctrl+K</kbd>` badge

**CSS (components.css):**
```css
.glass-dock { transition: transform 0.2s, box-shadow 0.2s; }
.glass-dock:hover { transform: translateX(-50%) translateY(-2px); box-shadow: 0 6px 28px rgba(0,0,0,0.18), ...; }
@keyframes pulse-dot { 0%,100% { box-shadow: 0 0 6px var(--green); } 50% { box-shadow: 0 0 12px var(--green); } }
[data-theme="light"] .glass-dock { background: rgba(255,255,255,0.75); border: 1px solid rgba(0,0,0,0.06); box-shadow: ...; }
```

## Design Audit Checklist (MANDATORY trước khi claim "done")

Sau mỗi đợt UI/UX overhaul, chạy checklist này — **không chỉ check bug functional mà còn thẩm mỹ**:

- [ ] **Mọi component có dùng liquid class?** Nếu còn inline `background: rgba(...)` → migrate
- [ ] **Header/Footer có đồng bộ liquid glass?** Đây là 2 component dễ bị bỏ sót nhất
- [ ] **Logo có phải SVG?** Emoji thô (⚡) → SVG gradient + glow pulse
- [ ] **Nav link hover có liquid effect?** Không chỉ đổi màu
- [ ] **Active pill dùng layoutId?** Spring trượt thay CSS animation tĩnh
- [ ] **Theme toggle có animated icon?** Morph transition ☀↔☾
- [ ] **Footer có phải glass dock?** Centered dock, không pill lẻ loi
- [ ] **Scroll progress bar hoạt động?** 0→100% cyan line
- [ ] **`prefers-reduced-motion` có?** `@media (prefers-reduced-motion: reduce)`
- [ ] **Build 0 errors** + verify 200 local + public

## Scroll Progress Bar

Thêm vào AppLayout:
```jsx
const [scrollProgress, setScrollProgress] = useState(0);
useEffect(() => {
  const onScroll = () => {
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    setScrollProgress(docH > 0 ? (window.scrollY / docH) * 100 : 0);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  return () => window.removeEventListener('scroll', onScroll);
}, []);

// JSX (dưới Navbar):
<div style={{ position:'fixed', top:'calc(var(--navbar-height) - 2px)', left:0, zIndex:1099,
  height:'2px', width:scrollProgress+'%',
  background:'linear-gradient(90deg, var(--accent), var(--green))',
  boxShadow:'0 0 6px var(--accent)', transition:'width 0.1s linear' }} />
```

## Keyboard Shortcut Helper

File: `components/ShortcutHelper.jsx`. Nhấn `?` (không Ctrl) → overlay shortcut list.

- `useShortcutHelper()` hook: useState + keydown listener, bỏ qua khi focus input
- Component: AnimatePresence backdrop + liquid-panel spring modal
- Hiển thị dạng `<kbd>` rows, đóng bằng Escape

## Code Splitting Heavy Libraries

Lib nặng (Three.js ~900KB) chỉ dùng ở 1 page:
```jsx
const Scene3D = lazy(() => import('../components/Scene3D'));
// In JSX: <Suspense fallback={<Scene3DFallback />}><Scene3D /></Suspense>
```
→ HomePage chunk 922KB → 25KB (Scene3D tách riêng, load async).

## `useNavigation()` Crash Fix (BrowserRouter)

`useNavigation()` chỉ hoạt động với `createBrowserRouter`. App dùng `<BrowserRouter>` → crash.
**Fix:** Manual tracker:
```jsx
const [navigating, setNavigating] = useState(false);
useEffect(() => { setNavigating(true); requestAnimationFrame(() => setNavigating(false)); }, [location.pathname]);
```

## System Theme Auto-Detection

Hook `useTheme()` pattern:
```js
function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}
const [theme, setThemeState] = useState(() => localStorage.getItem(KEY) || getSystemTheme());

// Listen system changes (chỉ khi user chưa manual set):
useEffect(() => {
  const mq = window.matchMedia('(prefers-color-scheme: light)');
  const handler = (e) => { if (!localStorage.getItem(KEY)) setThemeState(e.matches ? 'light' : 'dark'); };
  mq.addEventListener('change', handler);
  return () => mq.removeEventListener('change', handler);
}, []);
```

## `prefers-reduced-motion` (Accessibility)

Trong `mobile-ux.css`:
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

## Font Preloading (FOUT fix)

Trong `index.html` `<head>`:
```html
<link rel="preload" href="/node_modules/@fontsource/geist-sans/files/geist-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/node_modules/@fontsource/geist-mono/files/geist-mono-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
```

## BottomTab floating pill pattern (mobile)

File: `components/layout/BottomTab.jsx`. iOS 18-style centered floating pill.

**Structure:**
- Floating `<nav>` centered horizontally: `position: fixed; bottom: calc(14px + var(--safe-bottom)); left: 50%; transform: translateX(-50%)`
- Pill shape: `borderRadius: 30px`, `padding: 4px`, dark glass bg
- 4 main tabs + "..." More button → opens BottomSheet

**Active tab behavior:**
- Width expands: `width: active ? '72px' : '56px'` with CSS transition
- `motion.div layoutId="btab-bg"` for smooth pill slide between tabs
- Icon glow: `drop-shadow(0 0 8px rgba(0,212,255,0.6))` + spring scale(1.15)
- Label appears only on active tab: `<AnimatePresence>` fade + slide up

**More button:**
- Opens `<BottomSheet mode="list">` with Utilities + Hermes links
- Uses `useNavigate()` in onClick handlers (not `<Link>`) for programmatic nav
- `fa-ellipsis` icon, 44px tap target

**Haptic integration:**
- `haptic.light()` on tab tap, `haptic.medium()` on More tap
- Import `useHaptic` from `../../hooks/useHaptic`

**Desktop:** BottomTab renders empty (`if (!isMobile) return null`) — Footer handles desktop.

**Pitfall:** Don't use `<Link>` inside BottomSheet actions — use `navigate()` in onClick. BottomSheet unmounts on close, breaking Link navigation.

## Parallel page refactoring with subagents

When refactoring 3+ pages to a new design system simultaneously:

1. **Batch 1 (max 3):** `delegate_task` with `tasks: [{goal, context, role:'leaf'}...]`
2. **Batch 2:** Remaining pages in second `delegate_task` call
3. **Context must include:** exact file paths, CSS class names to use, what to keep untouched
4. **Verify:** After all complete, `npm run build` — 0 errors is canonical verification
5. **Commit:** Single atomic commit covering all changed files

Never use delegate_task with >3 tasks (config.yaml `delegation.max_concurrent_children` default).

## DOCX → PDF conversion pattern

Khi `DocReader` gặp file `.docx`:

1. **Detect**: `const isDocx = doc?.ext === 'docx' || (doc?.file || '').endsWith('.docx');`
2. **Pre-fetch**: `useEffect(() => { if (isDocx) setPdfLoading(true); fetch(\`/api/documents/${doc.id}/pdf\`).finally(() => setPdfLoading(false)); }, [doc.id, isDocx]);`
3. **Display**: `<iframe src={pdfUrl} style={{flex:1, border:'none', minHeight:'400px'}} />` ← KHÔNG dùng `dangerouslySetInnerHTML`
4. **Loading**: Spinner "Đang chuyển đổi DOCX sang PDF..." + note "Quá trình này có thể mất vài giây"
5. **Hide controls**: Ẩn font-size, font-controls, TOC, edit button khi `isDocx` (dùng `!isDocx && (...)`)
6. **Download**: Tạo `<a>` element với `href=/api/documents/:id?dl=1` + `.docx` filename
7. **Badge**: `<span>` màu xanh dương `rgba(59,130,246,0.15)` + icon `fa-file-word`
8. Server side: `GET /api/documents/:id/pdf` → `convertDocxToPdf()` (LibreOffice) → `res.end(buf)`

## UI Polish Patterns (Taste Skill)

### Noise overlay (breaks digital flatness)
```css
.noise-overlay {
  position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='...'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
```
Add `<div className="noise-overlay" />` as first child of AppLayout's fragment.

### Focus ring (accessibility)
```css
.btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
```

### Button states
All buttons must have 4 state layers: hover → active → focus-visible → transition (200-300ms ease-out).
- Hover: `translateY(-2px)` or `scale(1.02)` or background shift
- Active: `scale(0.97)` or `translateY(1px)`
- Focus: visible ring via CSS, not inline
- Transition: applied on base class, not per-state

### Color consistency sweep
When changing accent color in `tokens.css`, also search & replace all hardcoded hex values across the codebase:
```bash
cd frontend/src && grep -rn '<old-hex>|<old-hex>' . --include='*.jsx' --include='*.css' | grep -v node_modules
```
Then bulk-replace with sed:
```bash
for f in $(grep -rl ...); do sed -i 's/#old/#new/g; ...' "$f"; done
```
Replace all with `var(--accent)` or `var(--green)` or `var(--amber)` — never embed raw hex in components.

**Current accent colors:** `#00d4ff` (primary), `#00a8e0` (hover), `#0080b0` (deep), `#66e0ff` (light). Search for any residual emerald (`#34d399`, `rgba(52,211,153` etc.) and replace.

Khi component con được viết lại API mới nhưng component cha truyền props cũ:

1. **Đọc cả 2 file**: Cha và con — `read_file` toàn bộ
2. **So sánh props**: Liệt kê destructuring/tham số của con vs JSX attributes cha truyền
3. **Không vá tạm**: Đừng chỉ thêm `= () => {}` default values nếu API thay đổi toàn diện — viết lại phần gọi trong cha
4. **Callback undefined → crash**: `onSelectDoc={undefined}` → click crash. Tất cả callback phải được truyền thật hoặc gọi `?.()`
5. **Build + verify**: Sau sửa, build lại, curl kiểm tra page 200, kiểm tra click hoạt động

## Pitfalls

- **Tuyệt đối không** `taskkill -f -im node.exe` — kill tất cả Node process bao gồm RAG port 20128. Chỉ kill PID cụ thể trên port 3000
- **Props lệch cha-con** → đọc cả 2 file, so sánh API, sửa triệt để. Default values chỉ là band-aid
- **Patch hỏng JSX** → >3 dòng thay đổi dùng `write_file` full file
- **Server die âm thầm** → sau restart luôn verify `curl -s -o /dev/null -w "%{http_code}"`
- **Cache** → hash mới tự cache-bust, nhưng báo user Ctrl+F5 nếu thấy version cũ
- **DOCX content** → server trả base64, KHÔNG parse qua `marked.js`. Phải convert PDF server-side
- **Inline styles + pseudo-elements** → không hỗ trợ `::after`/`::before`. Dùng border-box gradient trick hoặc thêm CSS class
- **Commit trước khi sửa** → `git add -A && git commit -m "snap: ..."` để có thể revert nếu lỗi
- **Mobile glass blur** → Desktop 24px blur gây GPU jank trên mobile. Giảm xuống 12px + saturate(140%) trong mobile-ux.css `@media (max-width:768px)`. Tắt prismatic `::before` overlay trên mobile (tiết kiệm GPU).
- **`liquid-tab` class name** → CSS defines `.liquid-tab.is-active` (not `.active`). JSX must use `className={`liquid-tab ${active ? 'is-active' : ''}`}`. Mismatch → tabs never highlight.
- **`.liquid-input` invisible on dark glass** → CSS class `.liquid-input` sets background + blur + focus ring nhưng KHÔNG có `border` property. Trên dark glass background, input trông như borderless, hòa lẫn vào nền. LUÔN thêm inline `border: '1px solid var(--glass-border)'`, `borderRadius: '8px'`, `background: 'var(--glass-bg)'`, `padding: '0.6rem 0.8rem'` khi dùng `.liquid-input`. Đặc biệt quan trọng với input có button Play/Submit bên cạnh — nếu không có border, user không thấy ranh giới input.
- **Play button đè input** → Khi để button cùng `display: flex` row với input, nội dung input bị che khuất trên mobile màn hình hẹp. Tách button xuống hàng riêng với `marginBottom: '0.75rem'` trên input + button ở `<div>` riêng bên dưới.
- **Bottom tab nav đè nội dung cuối trang** → Mobile bottom nav (`BottomTab`) là `position: fixed; bottom: 0` cao ~4rem. Các page có interactive content ở cuối scroll (form, player, button row) cần `paddingBottom: '6rem'` trên container chính để nội dung không bị nav che. Áp dụng cho mọi page có content sát đáy viewport.
- **Project-wide** → loads 6 skills for full coverage: `service-dashboard-react` (React patterns), `dashboard-ui-patterns` (UI components), `taste-design` (anti-slop), `taste-redesign` (audit+fix), `redesign-existing-projects` (premium upgrades), `plan` (implementation plans). Cross-reference these before large UI changes.
- **Aesthetic audit gap** → checking only functional bugs (tab class, modal, skeleton) leaves header/footer un-reviewed. Always run the Design Audit Checklist above — it catches the 2 most commonly missed components (Navbar, Footer) and ensures liquid class migration. The question is not just "does it work?" but "does it look professional + use liquid classes?"
