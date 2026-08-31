---
name: frontend-ui-workflow
description: Checklist and workflow for frontend UI changes — visual verification, CSS best practices, overlap/responsive/theme checks, dev server usage.
---

# Frontend UI Development Workflow

## Checklist before committing any UI change

- **Mobile scroll failure — flexbox `min-height: 0` trap**: When a flex child has `flex: 1` + `overflow-y: auto` and its parent uses `height: 100vh`/`100dvh`, the child won't scroll if `min-height` defaults to `auto` (flexbox quirk). Fix: add `min-height: 0` to the flex child. Better: avoid `vh`/`dvh` entirely on mobile — use `position: fixed; inset: 0` on body + `position: absolute; inset: 0; width: 100%; height: 100%` on the container. This survives iOS address bar collapse without viewport unit volatility.
- **Pixel sampling for canvas/sprite detail**: `vision_analyze` cannot see
  1-2px details (sprite outlines, small crops <80px). Before "fixing" based on
  vision output, sample actual pixels via playwright `page.evaluate`:
  `ctx2.getImageData(Math.round(x*dpr), Math.round(y*dpr), 1, 1).data` and
  compare (body vs edge vs background). If contrast is objectively proven
  (e.g. [236,225,199] outline vs [146,102,231] body vs [12,12,17] bg), the
  detail IS present — vision just can't resolve it at small scale. Decide on
  measured data, not model description.
- **Narrow game levels (bounds < viewport)**: camera should center the level
  `(bounds.w-W)/2` when `bounds.w < W`, never clamp to 0 (leaves one side
  empty). Draw a dashed glow border around bounds instead of a dark overlay —
  a dark overlay hides the star/parallax background and unbalances desktop.
  Dark player sprites on dark bg → add light outline (cream/white stroke 2px +
  small shadowBlur).
- No reusability, hard to debug
- **JSX comment trap**: `// comment` or `/* comment */` between JSX elements causes Vite build error. Always use `{/* comment */}` wrapper.
3. **Overlap check**: verify no `position: fixed` elements overlap (e.g. footer dock vs back-to-top button). Use JS snippet in `btdat-frontend` skill for fixed-el dump.
4. **Responsive check**: mobile (390×844 iPhone 12) + desktop viewport. **CRITICAL: framer-motion `whileInView`** — `viewport={{ once: true }}` alone is unreliable on mobile. Always add `amount: 0.1`: `viewport={{ once: true, amount: 0.1 }}`. Same for `useInView(ref, { once: true, amount: 0.1 })`. Never use negative `margin` (e.g. `margin: '-80px'`) on mobile — it delays trigger past user scroll causing blank spaces.
5. **Readability audit**: after any theme/token update, verify contrast on mobile specifically:
- `--text-dim` must be ≥ #a09080 on dark, ≥ #c8b8a8 on mobile
- Pixel fonts (Press Start 2P) are UNREADABLE below 10px — use them for headings/short labels only
- Body font should be Geist Sans or similar readable sans-serif, never pixel font
- Active nav contrast: use bright accent (#ad80ff minimum, never #7c4dff on dark bg) + visible border, not just color change
- Min touch target: 44px for mobile nav/buttons
- **min-height 44px, NOT min-width**: forcing `min-width:44px` on every button breaks card action rows (▶✎✕ overflow viewport edge). Height alone is the safe floor.
- **Inline styles beat CSS**: mobile override rules need `!important` (e.g. `main button { min-height:44px !important }`).
- **Font floors via `max()` are a trap**: with inline `fontSize`, CSS only wins via `!important`, and `max(a, inherit)`/`1em*0.001` either nukes heading hierarchy or does nothing. Fix tiny fonts by editing inline `fontSize` values (0.4-0.55rem → 0.6-0.75rem): `grep "fontSize: '0\\.\\(4\\|45\\|5\\|55\\)rem'" -r src`.
- **Bottom nav <400px = icon-only**: 6 items × (icon+label) at 375px truncates labels ("ltems", "Alchewy"). Hide labels under 399px, keep icons ~1.5rem.
- **MEASURE mobile usability via CDP, don't trust screenshots**: after `Emulation.setDeviceMetricsOverride {width:375,height:667,mobile:true}` (re-apply AFTER browser_navigate — navigation resets emulation; see hermes-browser-setup cdp-multitab-pitfalls for target_id rules), run a JS tree-walker counting buttons < 40px and text < 10px. Targets: near-zero smallCount, tinyCount trending down.
- Bottom nav height ~48px + main `padding-bottom` ≥ 96px keeps content clear of fixed dock — verify by scrolling to bottom, measuring nav.top vs last content bottom.
- When user reports "khó nhìn", fix contrast FIRST (bg darker, text brighter, dim brighter) before layout
- Depth layers: need 3+ levels (bg → surface → surface-alt) to avoid flat look

6. **CRITICAL: Hex-to-CSS-var mass replacement pitfalls**
   - `sed`-based bulk replacement in JSX is dangerous: `var(--x)` inside `{{ }}` style objects needs quotes: `'var(--x)'`, not `var(--x)`.
   - Template literals (`` ` ``) create another quoting level: inside `${}` the CSS var must be a string: `` `${focus ? 'var(--x)' : 'var(--y)'}` ``
   - `color: var(--x)` in JSX is INVALID — JSX treats `:` after a prop name as separator, then the unquoted `var()` is parsed as JS expression → build error.
   - **Safer approach:** replace ONE FILE AT A TIME then build. Never mass-replace across many files then build — the error cascade is hard to isolate.
   - Best practice for color migration: write the new file fresh rather than sed-replacing the old one. When that's not possible, use Python with precise regex, build after each file.

7. **ErrorBoundary crash debugging**
   - "Có lỗi xảy ra" / "Vui lòng thử tải lại trang" = ErrorBoundary caught a render crash.
   - Common cause: removed imports (useMediaQuery, useHaptic, useCommandPalette) from AppLayout but kept rendering components that depend on them.
   - Fix: remove ALL component usage when removing its imports. Don't leave zombie components in the render tree.
   - Pattern: when refactoring AppLayout, strip it to bare minimum (Navbar + <Outlet /> + background), then re-add components one by one.

8. **Bottom nav mobile UX for pixel themes**
   - Font: use VT323 (--font-heading) NOT Press Start 2P — readable at small sizes
   - Active indicator: subtle glow line at top of item (::after 2px bar, 25%-75% width, accent color with box-shadow glow)
   - Never use chiseled border around bottom nav items — takes too much space
   - Icon minimum: 1.1rem, Label minimum: 0.55rem
   - Background: slightly darker gradient than top nav to create depth (e.g. #120c08 → surface)
   - No borders on individual items — separation via spacing + active indicator only
   - 44px min touch target per Apple HIG

9. **Scanner/fix-it-yourself-first escalation** for contrast complaints:
   - User says "khó nhìn" → immediately darken bg, brighten text, brighten text-dim, then check mobile
   - User says "vẫn khó" → switch body font to readable sans-serif, increase font-size
   - User says "vẫn thế" → check color contrast ratios, increase accent brightness
   - Only after 3 rounds consider layout changes
- `--accent` on dark bg: minimum `#ad80ff` (WCAG AA contrast); `#7c4dff` is too dark

6. **Theme redesign pitfall — stale components crash**: When swapping theme tokens globally, components using old CSS classes/hooks will crash silently (ErrorBoundary catches "Có lỗi xảy ra"). Before deploying a new theme: (a) check all children of AppLayout for deprecated imports (useMediaQuery, useHaptic, useSwipeBack, old class names like glass-dock, liquid-skeleton), (b) strip AppLayout to minimal (only Navbar) to isolate crashes, (c) remove or update stale components in the same pass.

7. **Bulk hex-to-CSS-var replacement in JSX**: When replacing old hex colors with `var(--x)` in JSX files, ALL CSS var references in inline style objects must be single-quoted: `'var(--x)'`. Bare `var(--x)` causes esbuild `Unexpected "var"` syntax errors. After bulk replace via sed/regex: (a) run `npm run build` immediately, (b) fix `color: var(--x),` → `color: 'var(--x)',`, (c) fix double-quote traps like `'2px dashed 'var(--border)''` → `'2px dashed var(--border)'`, (d) fix template literal missing quotes: `` `2px solid ${x ? 'var(--a)' : 'var(--b)'}` ``

8. **ErrorBoundary debug procedure**: "Có lỗi xảy ra / Vui lòng thử tải lại trang" = React ErrorBoundary. Strip AppLayout to bare minimum (Navbar only), rebuild. Common causes: Footer using old useMediaQuery, CommandPalette using old useHaptic, stale glass/liquid CSS classes missing.

9. **Mobile readability specificity for pixel themes**: Use `@media (max-width: 768px)` override blocks. `--text-dim` on mobile dark: `#c8b8a0` minimum. Pixel nav links: 0.4rem minimum with 44px touch targets. Bottom hotbar: icon 0.85rem, label 0.35rem, active MUST have visible border.
6. **Theme redesign pitfall — stale components crash**: When swapping theme tokens globally, components using old CSS classes (`glass-dock`, `liquid-skeleton`, `noise-overlay`, `animated-blobs`, `useMediaQuery`, `useHaptic`, `useCommandPalette`) WILL crash. Strip them from AppLayout or they trigger ErrorBoundary fallback "Có lỗi xảy ra".
7. **Post-build deployment**: 
- `rm -rf dist` then rebuild (Vite cache doesn't auto-invalidate)
- Kill ALL node processes (`taskkill /F /PID <pid>` — check `netstat -ano | find ":3000"`)
- Restart server AND Cloudflare tunnel
- Verify with `curl -sL https://site.com/ | wc -c` (should be 1500+ for SPA shell)
5. **Light theme check**: `[data-theme="light"]` overrides for every new component
6. **SVG in React**: CSS variables (`var(--accent)`) do NOT work in SVG `<stop>` / gradient attributes. Use hardcoded hex or pass as props.
7. **Animation:** use `layoutId` for shared element transitions, `AnimatePresence` for mount/unmount

## Dev server workflow
When making UI changes, use `vite dev` for HMR instead of full `npm run build` each iteration. Only build at the end.
## Audit flow

When asked to review code: check not just for bugs, but also:
- Are liquid-* classes used consistently?
- Are animations smooth?
- Does it look professional (not placeholder-ish)?

## Structural verification for creative/visual UI rewrites

When performing a large creative UI rewrite (re-theming, re-layout, or component overhaul) where no formal test suite exists, use ad-hoc structural verification:

1. **JSX syntax** — run esbuild `.transform(jsx, { loader: 'jsx' })` to catch syntax errors.
2. **Component tag balance** — regex-count non-self-closing opens vs closes. `<Component` matches must equal `</Component>` matches. Self-closing (`/>`) are exempt.
3. **Brace/bracket balance** — character-count `{}`, `()`, `[]` for mismatches. Angle `<>` may false-positive on fragments — cross-check against tag balance.
4. **Import sweep** — every imported symbol present. Remove unused imports from old code.
5. **Component definitions** — every function used in JSX is defined/imported.
6. **CSS class verification** — extract all `className="..."` values, check each `.*-.*` class exists in a CSS source file.
7. **Design token consistency** — extract `var(--...)` from JSX, verify each is defined in CSS.
8. **Old-theme artifact sweep** — list known old names (e.g. `BootSequence`, `TerminalPrompt`) and verify none survive except as substrings of new names.
9. **Section content checklist** — define keywords per expected section and sweep.

**Bundle into a standalone script** (`.cjs` using only `fs`) that reports `Errors: N / Warnings: M / Pass: YES|NO` with a single exit code.
