---
name: btdat-frontend
description: "Frontend development workflow for btdat.io.vn — QA, pitfalls, browser visual verification, and design system reference"
triggers:
  - "any UI/UX change, component edit, or visual bug fix on btdat.io.vn"
  - "any file edit in C:/Users/datel/service-dashboard/frontend/src/"
  - "user reports visual misalignment, overlap, or layout bug on btdat.io.vn"
---

> **References:** `references/pixel-fantasy-design-system.md` — full pixel tokens, component API, page mapping, and pitfalls from the 2026-07-30 theme migration.
> **Palette v2:** `references/pixel-fantasy-palette-v2.md` — updated 2026-07-30 palette, font hierarchy, and key rules from UI/UX overhaul.
> **QA audit 2026-08-01:** `references/live-site-qa-audit-2026-08-01.md` — 5 live bugs FIXED (progress-bar bleed, diacritic filenames, ALL/ALL labels, dock overlap, hero whitespace) with exact fix + deploy recipe.
> **Mobile usability 2026-08-01:** `references/mobile-usability-2026-08-01.md` — CDP measurement technique + 44px tap-target/font-floor fixes for the "khó dùng trên mobile" report.
> **Mobile follow-ups (same day):** min-width pitfall + hamburger-right + icon-only bottom nav — see `references/mobile-usability-2026-08-01.md` §Fixes 5-7.

## Browser verification pitfalls (learned 2026-08-01)
- **CDP `Emulation.setDeviceMetricsOverride` targets a DIFFERENT tab** than the one browser_navigate uses — `Runtime.evaluate` via `browser_cdp` can land on `chrome://new-tab-page/` while browser_vision screenshots the real site. Always pass the correct `target_id` (from `Target.getTargets`) and check `location.href` before trusting a measurement.
- **Vision-model layout analysis is unreliable for pixel-perfect overlap bugs** — it reported ghosts at 0,0 due to off-screen elements. JS measurement (`getBoundingClientRect()`) is authoritative.

## Hosting standalone HTML demos on btdat.io.vn

Server (`server.js`) has two directories:
- **`DOCS_DIR`** = `C:\Users\datel\documents` — for API-backed upload/read via `/api/documents/...`
- **`PUBLIC_DIR`** = `C:\Users\datel\service-dashboard\public` — serve static files directly, NO SPA interception

Route logic: SPA routes (`/documents`, `/dashboard`, `/hermes`, etc.) → React build. Everything else → check `public/` first, then SPA fallback for extensionless paths.

### To host a standalone HTML file (no React wrapper):
```bash
cp your-file.html /c/Users/datel/service-dashboard/public/some-name.html
# Available at: https://btdat.io.vn/some-name.html
```

**DO NOT** put it under `dist/documents/` — those paths get served via React SPA, not as raw HTML.
**DO NOT** put it under `DOCS_DIR` (`~/documents/`) — those are only served via `/api/documents/` API, not direct URL.

## Mobile scroll fix for standalone HTML with flexbox layout

When a flex container child won't scroll on iOS/Android:

```css
@media (max-width: 600px) {
  body {
    padding: 0; margin: 0;
    position: fixed; inset: 0;   /* ← KEY: fixed fills physical screen, not vh */
    overflow: hidden;
  }
  .container {
    width: 100%; height: 100%;
    position: absolute; inset: 0; /* ← match body */
    display: flex; flex-direction: column;
    overflow: hidden;
  }
  .scrollable-content {
    flex: 1; min-height: 0;      /* ← min-height:0 REQUIRED for flex child scrolling */
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}
```

**Why vh/dvh fails:** iOS Safari address bar collapse changes viewport height dynamically. CSS `height: 100dvh` doesn't update fast enough → content area incorrectly sized. `position: fixed; inset: 0` uses the actual layout viewport (stable across address bar animation).

**Why `min-height: 0` matters:** Flexbox quirk — a flex child with `flex: 1` defaults to `min-height: auto` (content's intrinsic height). When content is taller than the container, the child overflows the parent instead of scrolling inside. `min-height: 0` forces the child to respect the parent's height so `overflow-y: auto` activates.
- **Native curl.exe on Windows writes 0 bytes to MSYS `/tmp/` paths** — `curl -o /tmp/x.js` gives `size_download: 0` while `-v` shows full body (looks like a broken server!). Use Windows paths (`C:/Users/.../Temp/...`) or `--output` to a real path. See `windows-cli` skill.
- **Slug Vietnamese text with Unicode properties, not `[a-z0-9]`**: `[^\p{L}\p{N}]+gu` keeps "Báo cáo" → `báo-cáo`; the old `[^a-z0-9]+` turned every accented char into `-`. Slugging lives server-side in `server.js` (upload/create/rename) — fix there, not in the UI.
- **`server.js` restart trap**: killing a bg-session node may not kill the listener PID. After restart, always `netstat -ano | grep ":3000"` and `taskkill /F /PID` the orphan before starting fresh — otherwise you test against stale code and "fixes" don't appear.

# btdat.io.vn Frontend Development

## Stack Fact: NO shadcn/ui, NO Tailwind
- btdat frontend is hand-written React 19 + Vite with **pure CSS + custom property tokens** (`tokens.css`, `pixel-tokens.css`, `utilities.css`, `components.css`). No `@radix-ui`, no `tailwind-merge`, no `clsx`, no `tailwind.config`.
- UI components are hand-rolled (CommandPalette, ConfirmModal, BottomSheet, TerminalContact...).
- **Consequence:** shadcn-specific tooling does NOT apply — e.g. shadscan (`npx @shadscan/cli`) audits only shadcn apps and will report "not applicable" here. Don't propose it for this codebase. The *concepts* it checks (a11y, focus-visible, loading/empty/error states, alt text, mobile overflow, metadata) are the right checklist — audit manually or via a custom script, not via shadscan.

## User Preferences (read before any pixel theme change)

- **Default to dark mode only.** Light mode is unpolished. `useTheme.js` defaults to `'dark'`, never auto-detect system. Theme toggle button is hidden (`display: none` in Navbar — keep it there).
- **Readability > pixel purism.** If a font is hard to read, swap it. Press Start 2P ≤ 0.5rem for nav/display only; VT323 for headings/section titles; Geist Sans for body paragraphs. Text-dim must be clearly readable against surface.
- **If user says "text khó nhìn"** → first fix: font stack (body → Geist Sans), second: bump contrast (text-dim lighter, bg darker), third: mobile media queries for brighter text-dim.
- **If user says "bottom nav khó nhìn"** → switch to VT323 at 0.6rem for labels, use glow-line active indicator (`::after` top bar) instead of border-based, increase icon to 1.1rem.

## Pitfalls (check ALL before commit)

### P0. Navbar: TWO files, the layout/ one is real
- `src/components/layout/Navbar.jsx` is the **real** navbar used by AppLayout. Edit THIS one.
- `src/components/Navbar.jsx` is orphaned dead code — NOT imported anywhere. Do NOT edit it.
- When adding new nav links, update the `NAV_LINKS` array in `layout/Navbar.jsx`.
- **Do NOT re-add `BottomTab`** — the Navbar component already has its own mobile bottom hotbar built in.

### P0a. AppLayout: strip dependencies before adding new ones
When cleaning up AppLayout for a theme migration:
- Import ONLY what the new layout needs (Navbar). Remove Footer, CommandPalette, ShortcutHelper, and any old glass/liquid components in ONE clean pass.
- These old components reference removed CSS classes (`glass-dock`, `liquid-skeleton`, `glass-panel`) and hooks (`useMediaQuery`, `useHaptic`, `useSwipeBack`, `useCommandPalette`) — keeping the imports causes ErrorBoundary crashes.
- Do NOT keep old imports "just in case" — they WILL crash because the CSS classes they depend on are gone.
- The error will show up as "Có lỗi xảy ra" / "Vui lòng thử tải lại trang" — this is the ErrorBoundary fallback from `src/components/shared/ErrorBoundary.jsx`.

### P0b. Restart flow after every build
After every `npm run build`, the server MUST be restarted:
```
cmd.exe /c "taskkill /F /PID <PORT_PID>"   # kill old server on :3000
netstat -ano | grep ":3000 " | grep LISTENING   # verify empty
cd /c/Users/datel/service-dashboard && node server.js &   # start new server
cloudflared tunnel run b3e9ea6a-9ed9-41fc-be71-66f52b31fef3 &  # restart tunnel
```
The tunnel MUST point to localhost:3000 — if the server restarts before the tunnel, cloudflared gets a stale connection error. Kill old tunnel AND restart it together.
- Tunnel health check: `curl -sL "https://btdat.io.vn/" --max-time 10 | wc -c` should return > 1000 bytes.
- If the site still shows ErrorBoundary after rebuild, the build probably has old imports or the server is serving stale dist.

### P1. PageHeader component — use it everywhere
`<PageHeader icon="" title="" subtitle="" glow="purple|gold|blue" />` from `../components/pixel`.
Do NOT write inline h1 headers. Every route has its own PageHeader (see references/pixel-fantasy-design-system.md).

### P2. Pixel palette: contrast & depth
- **Accent `#7c4dff` is too dark on dark bg** — fails WCAG AA. Use `#ad80ff` (50% lighter).
- **3 background layers**: `--bg: #0a0705` → `--surface: #18100a` → `--surface-alt: #22180e`. Without `--surface-alt`, cards blend into nav.
- **Two border levels**: `--border: #3a281a` (subtle) and `--border-lt: #5a3a2a` (strong). Use `--border-lt` for component borders.
- Magic blue: `#64d8ff`, ember gold: `#ffc400`, blood red: `#ff5252`, heal green: `#80d080`.

### P2a. Pixel font hierarchy
- **Press Start 2P**: ONLY for display (logo, nav labels, badges, stats). Max 3–4 words.
- **VT323** (`--font-heading`): Page headers, section titles. 0.85–1rem.
- **Geist Sans** (`--font-body`): All body text, paragraphs.
- Mobile: bump `--text-dim` to `#c8b090`.

### P2b. Scanlines start subtle
- Opacity `0.02–0.025`, 3px gap. NEVER 0.08 (causes moiré + user complaints).
- Let user ASK for stronger before increasing.

### P2c. JSX color replacement: NEVER use sed
- sed breaks template literals and style objects. Use Python `re.sub` with lookbehind assertions, or per-file `patch()` calls.
- Best: refactor to CSS classes so colors live in `.css` files.

### P2. Body font: Geist Sans, NOT Press Start 2P
- `--font-body: 'Geist Sans', sans-serif` — body text. Readable, clean.
- `--font-pixel: 'Press Start 2P'` — ONLY for short headings, nav labels, buttons. **Illegible below 0.7rem**.
- When user says "text khó nhìn quá": switch body to Geist Sans, bump font-size to 16px, increase text contrast (`--text-dim` should be #a09080 or brighter).

### P3. Scanlines cause moiré / "sọc ngang"
`.pixel-scanlines::after` at `opacity: 0.03` / 3px spacing. If user complains: reduce toward 0.01 or remove the class from AppLayout entirely.

### P4. Build + restart sequence (reliable)
1. Kill all node processes: `taskkill /F /PID <PID>` — find PID via `netstat -ano | grep LISTENING | grep ':3000 '`
2. Clean + build: delete `frontend/node_modules/.vite` and `dist/`, then `npm run build`
3. Start: `cd /c/Users/datel/service-dashboard && node server.js` (background)
4. If tunnel is down: `cloudflared tunnel run b3e9ea6a-9ed9-41fc-be71-66f52b31fef3` (background)
5. Wait 3s, verify: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/`
6. Tell user to hard refresh (Ctrl+F5). If tunnel is slow, DO NOT use browser_ tools — curl is faster and more reliable for verification.

### P5. DO NOT delete dist/ before build
Deleting `dist/` while the server is running causes 404 on next request. Either: (a) build first, THEN restart server; or (b) kill server, clean+build, then restart.
### 1. SVG gradient colors
NEVER use CSS vars (`var(--accent)`) inside `<stop stopColor="...">` — browsers don't resolve them. Hardcode hex: `#00d4ff`, `#34d399`.

### 2. Inline style beats CSS, always
`style={{}}` on a React element overrides ANY CSS rule on the same property — even `!important` media queries. Two critical cases:
- **Inline `transform` kills CSS `:hover`**: if `style={{ transform: 'translateX(-50%)' }}` exists, `.glass-dock:hover { transform: translateY(-2px) }` never fires. Move hover effects to JS `onMouseEnter`/`onMouseLeave`.
- **Inline `display` kills responsive CSS**: `style={{ display: 'none' }}` on hamburger beats `.hamburger-btn { display: flex !important }` media query. Elements needing responsive visibility MUST NOT have inline `display`. Let CSS media queries own it entirely.

### 2a. JSX comments must be in braces
`// comment` or `/* comment */` between JSX elements causes Vite build error (`SyntaxError: Unexpected token`). Always wrap: `{/* comment here */}`. This is NOT the same as JS inside `{ }` — multi-line comments still need `{/* */}` wrapper.

### 2b. React state + ref timing: element not rendered yet
When calling `setState(data)` then immediately accessing the same element via `ref.current`, the ref is `null` — React hasn't flushed the DOM update yet. **This is the #1 cause of silent failures in async flows** (audio/video/media elements, canvas, iframes).

**Wrong** — setting `audio.src` right after `setPlayer(d)` before DOM re-render:
```jsx
const loadYt = async () => {
  const d = await fetch(...);
  setPlayer(d);                    // schedules re-render
  const a = audioRef.current;      // null! element not yet mounted
  a.src = streamUrl;               // never runs
};
```
**Right** — split into 2 phases:
```jsx
const loadYt = async () => {
  const d = await fetch(...);
  setPlayer(d);                    // Phase 1: set state, let DOM catch up
};

useEffect(() => {
  if (!player) return;
  // Phase 2: DOM is ready, ref is valid
  const a = audioRef.current;
  if (a) {
    a.src = streamUrl;
    a.play();
  }
}, [player]);
```
**Double-check before every media/ref interaction:** is the target element conditionally rendered? If its JSX is inside `{cond ? <Thing/> : null}` and `cond` JUST changed, the ref is NOT yet available. Either:
- Use `useEffect` with the condition as dependency
- Keep the element always-mounted and toggle visibility with CSS (`display`/`opacity`) instead

**Race condition on rapid clicks:** add a request-id ref:
```jsx
const reqId = useRef(0);
const loadYt = async () => {
  const myReq = ++reqId.current;
  const d = await fetch(...);
  if (myReq !== reqId.current) return; // stale, drop
  setPlayer(d);
};
```

### 2c. Mobile safe-area bottom padding
Floating BottomTab (z-index 600, height ~64px) covers content on all pages. Every scrollable page's outer container needs `paddingBottom: '6rem'`. If a page has a fixed-position element after the main content (e.g. TerminalContact), use `'7rem'`. Applied to: DashboardPage, WidgetPage, UtilitiesPage, HomePage (Contact section gets 7rem).

### 3. Mobile screenshot QA uses CDP, not browser_vision
`browser_vision` routes through OmniRoute → MiniMax models return 401. `browser_navigate` times out on WebGL pages. Use Chrome CDP + WebSocket + Python JPEG capture (see `references/cdp-screenshot-workflow.md`).

### 4. TopBar / Header icon alignment
ThemeToggle (moon/sun) and hamburger buttons in Navbar MUST have identical `display: flex`, `alignItems: center`, `justifyContent: center` in their inline styles. ThemeToggle often misses these (has `width`, `height`, `borderRadius` but no flex), causing the icon to float off-center vs the hamburger beside it. Always add:
```jsx
style={{ width: '36px', height: '36px', borderRadius: '10px',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  padding: 0, minWidth: '36px' }}
```
Without explicit flex centering, `AnimatePresence` motion spans inside the button don't inherit button-level alignment.

### 5. Input field styling on mobile
Every `<input>` or text field on mobile MUST have visible borders — glass-panel backgrounds swallow the input boundary:
```jsx
<input style={{
  border: '1px solid var(--glass-border)',
  borderRadius: '8px',
  background: 'var(--glass-bg)',
  padding: '0 12px', color: 'var(--text-strong)',
}} />
```
If an input and button are side-by-side, they overlap on narrow viewport (<400px). Put the button on a SEPARATE row below with `marginBottom: '0.75rem'` gap.

### 6. Mobile bottom nav spacing
Every page MUST have `padding-bottom: 6rem` on its outermost container to prevent the floating BottomTab from covering content. Check this on all pages after any layout change.

### 7. JSX comments — use `{/* */}` not `//`
Inside JSX, `// comment` is invalid syntax that breaks Vite build. Always use `{/* comment */}` inside JSX blocks. Outside JSX (inside `{...}` expressions), `//` is fine.

### 8. Landing page design for mobile (replacing 3D hero)
Heavy 3D scenes (Three.js wireframe, particle systems) cause:
- `browser_navigate` / `browser_vision` timeouts during QA
- Slow initial paint on mobile devices
- Text overlap with the 3D mesh

Prefer **gradient mesh background** (multiple radial-gradient circles) + **gradient text hero** instead:
```jsx
{/* Background — three gradient circles, zero Three.js */}
<div style={{ position: 'fixed', inset: 0, zIndex: 0, overflow: 'hidden', pointerEvents: 'none' }}>
  <div style={{ position: 'absolute', width: '600px', height: '600px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)',
    top: '-10%', right: '-10%' }} />
  <div style={{ position: 'absolute', width: '400px', height: '400px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(139,92,246,0.03) 0%, transparent 70%)',
    bottom: '10%', left: '-5%' }} />
</div>

{/* Gradient text hero — no background mesh, no overlap */}
<h1 style={{
  background: 'linear-gradient(135deg, var(--accent) 0%, #8b5cf6 50%, #10b981 100%)',
  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
}}>btdat.io.vn</h1>
```

Feature cards grid: `grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))` with `motion.div` + `whileInView` stagger (delay `0.05 * index`). Each card: icon gradient bg + name + status dot + description.

### 5. Mass mobile fix workflow — delegate in parallel batches
When fixing the same class of issue across 5+ pages, fan out subagents like this:
- **Batch 1** (3 agents): complex pages — Homepage, Dashboard, Widgets
- **Batch 2** (3 agents): simpler pages + shared components

### P4. Palette migration: old-hex-to-CSS-var at scale
When bulk-replacing hex colors in JSX files with CSS variables:
- **DON'T use sed alone.** It strips quotes around `var(--x)` inside template literals. Use two-pass: (1) sed to replace hex strings, (2) Python regex to quote any `var(--X)` not inside quotes.
- **Fix pattern:** `color: var(--x)` → `color: 'var(--x)'` (JSX style objects need quotes). Template literal: `` `${focus ? 'var(--a)' : var(--b)}` `` → `` `${focus ? 'var(--a)' : 'var(--b)'}` ``.
- **Always grep for unquoted `var(--` before building:** `grep -rn "var(--" src/pages/ | grep -v "'var(--"` — if non-zero, build fails.
- **Two CSS files define `[data-theme="dark"]`** (`tokens.css` + `pixel-tokens.css`). Later import wins by cascade. This is expected.

### P5. Bottom nav mobile UX
- Active state: use glow bar `::after` above (`position: absolute; top: -3px`), NOT border around item.
- Font: `--font-heading` (VT323) at 0.55–0.6rem for labels, never Press Start 2P below 0.5rem.
- Icon: 1.1rem minimum. Background: gradient from `#120c08` to `var(--surface)`.

## Browser visual verification

### 2a. Comments between arrow `(` and opening JSX tag break esbuild
Arrow-function bodies returning JSX: `items.map(w => ( <div ... ))` — **ANY comment** between the opening `(` and the first JSX element causes esbuild `ERROR: Expected ")" but found...`. Both `{/* */}` AND `//` break in this position. The parser expects an expression after `(`, and a lone comment isn't one.

**Fix:** move the comment *inside* the JSX element:
```jsx
// WRONG — both styles break esbuild
filtered.map(w => (
  // this breaks
  <div key={w.id}>...
))
filtered.map(w => (
  {/* this also breaks */}
  <div key={w.id}>...
))

// RIGHT — comment inside the element or use /* */ outside
filtered.map(w => (
  <div key={w.id} /* comment here */>...
))
```

If you need a comment before the element, put it above the `.map()` call, not between `(` and the JSX tag.
Check ALL `position: fixed` elements. This JS expression dumps every fixed element:
```
document.querySelectorAll('*').forEach(function(el){var s=getComputedStyle(el);if(s.position==='fixed'&&el.offsetHeight>0)console.log({tag:el.tagName,cls:el.className.slice(0,40),text:el.textContent.slice(0,30),bottom:s.bottom,z:s.zIndex})})
```
Current z-index map (desktop):
- Navbar: z=500, height=

### 4. Mobile QA — CDP screenshot workflow
Headless Chrome CANNOT render WebGL/3D (Scene3D, particles, Three.js). For visual QA of 3D pages, use non-headless Chrome:
```
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:/Users/datel/chrome-debug --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1920,1080 "URL"
```
**NEVER use `browser_vision`** — it routes through OmniRoute vision model which fails on MiniMax-M3 (401). Use Python CDP directly:
```python
import json, base64, websocket, subprocess, time
tabs = json.loads(subprocess.run(['curl','-s','http://localhost:9222/json'], capture_output=True, text=True).stdout)
page = [t for t in tabs if 'btdat.io.vn' in t['url']][0]
ws = websocket.create_connection(page['webSocketDebuggerUrl'])
# Set mobile: ws.send(json.dumps({'id':1,'method':'Emulation.setDeviceMetricsOverride','params':{'width':390,'height':844,'deviceScaleFactor':3,'mobile':True}}))
# Screenshot: ws.send(json.dumps({'id':2,'method':'Page.captureScreenshot','params':{'format':'jpeg','quality':25}}))
```
Use JPEG quality=25-30 for small file size. PNG screenshots get truncated (base64 >1MB). Save to `C:/Users/datel/Downloads/` for MEDIA: sharing.
**Never use `browser_vision`** — fails with 401 on vision model, wastes 5+ minutes. Always use direct CDP.

### 5. Common mobile bugs — checklist
These recur on every btdat.io.vn page. Check ALL before claiming "done":

| Bug | Fix |
|-----|-----|
| **Bottom nav covers content** | Add `paddingBottom: '6rem'` to outermost page container |
| **Safe area (status bar overlap)** | Add `paddingTop: 'env(safe-area-inset-top, 0.5rem)'` to header |
| **Input fields no border** | Add `border: '1px solid var(--glass-border)', borderRadius: 8, background: 'var(--glass-bg)'` |
| **Badge overflow card** | Add `overflow: 'hidden'` to the parent card. Keep badge `position: 'absolute'; top: 6px; right: 6px` — `overflow: hidden` clips it. DO NOT change badge to `position: 'relative'` — that breaks the top-right corner placement |
| **Buttons overlap input** | Put button BELOW input in separate row, not inline. Add `marginTop: '0.75rem'` |
| **Hero text overlaps 3D** | Three layers: (1) dark radial-gradient overlay `position:'absolute'` between 3D canvas and text, `zIndex:0`; (2) `textShadow: '0 0 18px rgba(0,0,0,0.45)'` on hero chars; (3) lower 3D mesh `opacity` (torus 0.06→0.08, particles 0.3). See `references/hero-3d-overlay.md` |
| **Empty white space below content** | Check `minHeight:'100vh'` vs `100dvh` — mobile needs `100dvh`. But don't force if content is short — let it be natural + paddingBottom is enough |
| **Bottom nav labels missing** | All 5 items (4 tabs + More) show label text under icon always. Inactive labels: `opacity: 0.45`, `fontSize: '0.55rem'`. Active: full opacity, bold. All items share `flex: '1 1 0'` for equal width — see `references/bottom-tab-patterns.md` |
| **framer-motion whileInView never fires** | `viewport={{ once: true }}` alone is unreliable on mobile — elements enter viewport but animation never triggers. ALWAYS add `amount: 0.1` (or `amount: 'some'` for very tall screens): `viewport={{ once: true, amount: 0.1 }}`. Same fix for `useInView(ref, { once: true, amount: 0.1 })`. Do NOT use negative `margin` (e.g. `-80px`) — it delays trigger past user scroll. See `references/framer-motion-whileInView.md` |
- Footer glass-dock: z=350, bottom=1.5rem (24px)
- Back-to-top: z=2000, bottom=4rem (64px) — must clear dock
- Animated blobs: z=0
- Noise overlay: z=9999 (top layer, non-interactive)

### 3a. Browser console layout verification (no vision needed)
Key one-liners for checking layout health:
```
// SVG logo rendered?
document.querySelector('nav svg rect') ? getComputedStyle(document.querySelector('nav svg rect')).fill : 'MISSING'
// Hamburger display state (should be 'none' on desktop)
getComputedStyle(document.querySelector('.hamburger-btn')).display
// Footer vs back-to-top overlap check  
document.querySelector('.glass-dock') && document.querySelector('[aria-label="Back to top"]') ? 'both exist, dock='+getComputedStyle(document.querySelector('.glass-dock')).bottom+' bt='+getComputedStyle(document.querySelector('[aria-label="Back to top"]')).bottom : 'one missing'

### 4. Browser visual verification (live)
Requires Chrome running with remote debugging on port 9222. See `references/browser-setup.md` and the `hermes-browser-setup` skill for full instructions. Quick start:
```
# Kill all Chrome first (CRITICAL — existing Chrome ignores the debug flag)
taskkill /F /IM chrome.exe && sleep 2
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/Users/datel/chrome-debug" --no-first-run &
sleep 4

# Hermes config (once)
hermes config set browser.cdp_url "http://127.0.0.1:9222"
```

Once connected, verify every UI change:
```
browser_navigate("https://btdat.io.vn/")
browser_snapshot(full=true)         # full DOM tree
browser_console(expression="...")   # query computed styles, positions
browser_scroll(direction="down")    # check overlap at page bottom
```

### Vision analysis setup (Gemini auxiliary)

The main model (DeepSeek V4 Pro via 9Router) cannot see images. Two routes were tested:

**9Router multimodal** — FAILS. Although `POST /v1/chat/completions` with `image_url` content blocks returns 200 OK, images are stripped before reaching the upstream model. All tested models (Kimi K2.6, Qwen3.6-Plus, DeepSeek V4 Pro) respond "I don't see the image." Known bug: [decolua/9router#1078](https://github.com/decolua/9router/issues/1078).

**Google Gemini auxiliary vision** — WORKS. Config in `config.yaml`:
```yaml
auxiliary.vision:
  provider: google
  model: gemini-2.0-flash
```
Secrets in `~/.hermes/.env`: `GOOGLE_API_KEY=...` (also set `GEMINI_API_KEY` as alias). Free tier: 10-15 RPM, 250-1500 RPD. Key from https://aistudio.google.com/apikey — no credit card. Common error: 429 = quota exhausted, resets at midnight.

This setup keeps DeepSeek for chat but routes all `vision_analyze()` / `browser_vision()` calls to Gemini. Use `browser_snapshot` + `browser_console` for layout verification when vision is unavailable (rate limited).

## Build & Deploy
```bash
cd /c/Users/datel/service-dashboard/frontend && npm run build  # 0 errors required
bash /c/Users/datel/AppData/Local/hermes/scripts/kill-node.sh
cd /c/Users/datel/service-dashboard && node server.js &  # background
curl -s -o /dev/null -w "%{http_code}" https://btdat.io.vn/  # must return 200
```

**Reference:** `references/full-site-redesign-workflow.md` — step-by-step for site-wide themed redesign (audit → plan → tokens → components → build → verify)

## Design Tokens
- Accent: `#00d4ff` (cyan), `#34d399` (green), `#f59e0b` (amber)
- Glass: `var(--glass-bg)`, `var(--liquid-border)`, `var(--glass-border)`
- Font: Geist Sans (body), Geist Mono (code) — preloaded in index.html
- Components: `liquid-panel`, `liquid-btn`, `liquid-card`, `liquid-skeleton`, `glass-dock`
- Motion: framer-motion (`motion/react`), AnimatePresence with mode="wait"

## Responsive
- `.desktop-only` / `.mobile-only` CSS classes
- Footer: `isMobile` guard → null on mobile
- BottomTab: `mobile-only` class → hidden on desktop
- Hamburger: CSS media query `@media (max-width: 768px)` with `!important`

## Project Map
- Frontend: C:\Users\datel\service-dashboard\frontend\ (React 18, Vite 5)
- Server: C:\Users\datel\service-dashboard\server.js (Node, port 3000)
- Domain: btdat.io.vn → cloudflared tunnel `hermes-tunnel`
- Dev server: `npx vite --port 5173 --host` (HMR, use for rapid iteration)
