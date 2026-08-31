---
name: fe-qa-checklist
description: "Frontend QA checklist for every UI change on btdat.io.vn — prevents invisible bugs from inline styles"
triggers:
  - "any UI/UX change to btdat.io.vn frontend"
  - "any file edit in /c/Users/datel/service-dashboard/frontend/src/components/"
---

# Frontend QA Checklist

Before committing ANY UI change, run this checklist:

## 1. Browser Cross-Compat
- SVG `<stop>` elements: NEVER use CSS vars like `var(--accent)` — they don't work in most browsers. Use HARDCODED hex: `#00d4ff`, `#34d399`
- Test `backdrop-filter` with `-webkit-backdrop-filter` fallback

## 2. Specificity Conflicts
- If a component uses `style={{}}` with `transform`, any CSS `:hover { transform: ... }` will be overridden by inline style.
  → Move hover effects to JS `onMouseEnter`/`onMouseLeave` OR use CSS class instead of inline style.

## 3. Overlap Check (position:fixed)
- Check all `position: fixed` elements for z-index conflicts
- Check bottom-positioned elements: footer (bottom: 1.5rem), back-to-top (bottom: 4rem), mobile bottom nav
- Desktop: footer z-index=350, back-to-top z-index=2000

## 4. Build Verification
```bash
cd /c/Users/datel/service-dashboard/frontend && npm run build
```
Must produce 0 errors. Warnings about chunk size are OK.

## 5. Deploy
```bash
bash /c/Users/datel/AppData/Local/hermes/scripts/kill-node.sh
cd /c/Users/datel/service-dashboard && node server.js &
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
# Must return 200
```

## 6. Responsive
- Classes `.desktop-only` and `.mobile-only` properly applied
- Footer renders only on desktop (`isMobile` guard)
- BottomTab renders only on mobile

## 7. Cloudflare Cache Pitfall (CRITICAL)
- Static files served with `Cache-Control: public, max-age=14400` (4h) via Cloudflare
- After editing `public/*.js` or `public/*.html`, Cloudflare may serve STALE version (`cf-cache-status: HIT`, `Age: N`)
- Fix: RENAME the file (e.g. `hermes-visuals.js` → `hermes-visuals-v2.js`) and update references
- Verify: `curl -sI URL | grep -i "cf-cache-status"` — should be MISS/EXPIRED, not HIT
- When bulk-replacing script tags in HTML, check for duplicate/mangled lines after — use unique context!

## Project Context
- Frontend: React 18 + Vite 5, `/c/Users/datel/service-dashboard/frontend/`
- Server: Node.js, `/c/Users/datel/service-dashboard/server.js`, port 3000
- Domain: btdat.io.vn via cloudflared tunnel `hermes-tunnel`
- Key accent colors: `#00d4ff` (cyan), `#34d399` (green), `#f59e0b` (amber)
- Glass design: `--glass-bg`, `--glass-border`, `--liquid-border` CSS vars
- Motion library: framer-motion (`motion/react`)
