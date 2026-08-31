---
name: astryx
description: "Astryx UI: install, CSS imports, API quirks, deploy, verify."
---

# Astryx — Meta's design system (React 19+)

Astryx = Meta's 8-year internal design system, open-sourced July 2026 (MIT, `@astryxdesign/core`). 150+ components, 7 themes (neutral, butter, chocolate, matcha, stone, gothic, y2k), StyleX-based but zero lock-in. "Agent-ready": `npx @astryxdesign/cli init` writes the component index into AGENTS.md so AI agents stop guessing.

## Install (Vite)
```bash
npm create vite@latest app -- --template react-ts
npm install @astryxdesign/core @astryxdesign/theme-neutral @stylexjs/stylex
```
Requires React 19+ (peer dependency).

## CSS imports — USE PACKAGE EXPORT PATHS, not dist/...
In main.tsx, order matters (reset → astryx → theme):
```tsx
import '@astryxdesign/core/reset.css'
import '@astryxdesign/core/astryx.css'
import '@astryxdesign/theme-neutral/theme.css'
```
`@astryxdesign/core/dist/astryx.css` FAILS at build ("not exported under the conditions") — package.json `exports` maps the bare paths only.

## Provider
```tsx
import {Theme} from '@astryxdesign/core/theme'
import {neutralTheme} from '@astryxdesign/theme-neutral/built'
<Theme theme={neutralTheme}><App/></Theme>
```

## Component API quirks (v0.4.1, learned from tsc errors)
| Thing | Reality |
|---|---|
| Button variant | ONLY `primary | secondary | ghost | destructive` |
| Badge variant | color names: neutral, info, success, warning, error, blue, cyan, green, orange, pink, purple, red, teal, yellow — NOT 'primary'/'subtle' |
| HStack/VStack gap, padding | SpacingStep = `0|0.5|1|1.5|2|3|4|5|6|8|10` (~4px/step). No paddingX/paddingY — only `padding` |
| Spacer | DOES NOT EXIST — push with `style={{marginLeft:'auto'}}` |
| Grid responsive | `columns={{minWidth: 260, max: 3}}` (auto-columns); plain number = fixed columns |
| Button | `label` prop is REQUIRED |

## Theming / branding
- Themes are CSS custom properties. neutral's accent is blue `#0074e2`.
- For branded dark UI: define own vars in `:root` (`--bg-body:#0a0a0f; --accent:#7c6cf0; --text-secondary:#a1a1b5; --border: rgba(255,255,255,0.08)`) and style via className + own CSS — Astryx components coexist fine.
- Tailwind bridge: import `@astryxdesign/core/tailwind-theme.css` → utilities like `bg-surface`, `text-primary`.

## Deploy pitfall — vite preview 403 on real domain
`vite preview` returns 403 "Blocked request. This host is not allowed" for any non-localhost Host header. Fix in vite.config.ts:
```ts
preview: { allowedHosts: ['btdat.io.vn', 'www.btdat.io.vn'] }
```
Test origin BEFORE blaming Cloudflare: `curl -s -H "Host: btdat.io.vn" http://localhost:3000`.

## Custom Node server for btdat.io.vn (port 3000)
`~/astryx-demo/server.js` (ESM, `node server.js`, package.json has `"type":"module"` so no require()):
- `/` → Astryx landing from dist/ (SPA fallback to index.html)
- `/vtts`, `/vtts-drive.html` → exception serving old `service-dashboard/dist/vtts-drive.html` (byte-identical, MD5-verified)
- `/yt` → `public/yt.html` (YouTube audio player)
- `/api/utilities/youtube-audio*` → yt-dlp/ffmpeg pipeline (see video-downloader skill → references/audio-streaming.md)
- Static assets: long cache except html (no-cache); `safeResolve()` guards path traversal.

## QA workflow (Đạt demands visual quality)
- Verify with playwright-core headless chromium (path: `C:/Users/datel/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe`) + full-page screenshot → vision_analyze. Check `body.scrollWidth <= innerWidth` (mobile overflow), 0 console errors.
- Overflow traps seen: hero `::before` glow (absolute, wide) → add `overflow:hidden` on hero + `width: min(480px, 120%)`; native `<audio>` controls can widen body.
- "Xấu" verdict → rebuild, don't patch: modern premium (Linear/Stripe-style), NOT pixel. Press Start 2P / scanlines / #0d0806 retro palette are FORBIDDEN on btdat.io.vn (see memory).
