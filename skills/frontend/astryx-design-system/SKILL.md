---
name: astryx-design-system
description: "Build React 19 UI with Meta's Astryx design system."
---

# Astryx Design System (Meta)

Astryx = Meta's design system (open-sourced, MIT, v0.4.x beta). React 19+ required,
styling via StyleX (invisible to consumers). 150+ components, 7 themes, CLI that
writes a component index into AGENTS.md ("agent-ready").

**Project state:** `~/astryx-demo` is the new main-site project replacing
service-dashboard (dev server port 4000). Demo landing page lives there.

## Quick start (Vite + TS)

```bash
npm create vite@latest <name> -- --template react-ts
npm install
npm install @astryxdesign/core @astryxdesign/theme-neutral @stylexjs/stylex
```

**main.tsx — CSS import paths MUST use the package exports map** (NOT `dist/...`):

```tsx
import '@astryxdesign/core/reset.css'
import '@astryxdesign/core/astryx.css'
import '@astryxdesign/theme-neutral/theme.css'
import './index.css'
```

Wrong (`dist/astryx.css`, `dist/theme.css`) → Vite build fails with
`"X is not exported under the conditions [...] from package ..."`.

**Theme provider** (wraps whole app):

```tsx
import {Theme} from '@astryxdesign/core/theme'
import {neutralTheme} from '@astryxdesign/theme-neutral/built'
<Theme theme={neutralTheme}>...</Theme>
```

## API quirks (learned the hard way — see references/api-quirks.md for full detail)

- **SpacingStep**: `gap`/`padding` props only accept
  `0 | 0.5 | 1 | 1.5 | 2 | 3 | 4 | 5 | 6 | 8 | 10` (≈4px/step). Passing `24`/`14`
  etc. is a TS error. Map values to the step scale.
- **No `Spacer` component** — use `style={{marginLeft: 'auto'}}` on a child.
- **No `paddingX`/`paddingY`** on HStack/VStack — only `padding` (SpacingStep).
- **Button**: `label` is REQUIRED (not children); variant ∈
  `primary | secondary | ghost | destructive`; size `sm | md | lg`.
- **Badge**: variant ∈ `neutral | info | success | warning | error | blue | cyan |
  green | orange | pink | purple | red | teal | yellow` — NO `primary`, NO `subtle`.
- **Grid**: `columns={3}` fixed, or responsive `columns={{minWidth: 260, max: 3}}`
  (auto 1-col on mobile — fixes horizontal overflow). `gap` is SpacingStep.
- **HStack/VStack**: support `as`, `wrap`, `className`, `style`. Inline `style`
  does NOT support nested `@media` — use CSS classes + media queries instead.
- Component subpath exports exist (`@astryxdesign/core/Button`), full barrel from
  `@astryxdesign/core`.

## CLI (agent-ready)

```bash
npx @astryxdesign/cli init            # writes component index into AGENTS.md/CLAUDE.md
npx @astryxdesign/cli component Button # full docs for a component
npx @astryxdesign/cli template dashboard # emit full page source
```

## Pitfalls

- **`npx vite build` in foreground** → Hermes terminal misdetects it as a
  long-lived server and refuses ("appears to start a long-lived server/watch
  process"). Run with `background=true` + `process(wait)`.
- **Verifying localhost**: `browser_exec` blocks private/internal addresses →
  use playwright-core headless (see below).
- **npm postinstall warning** for `@astryxdesign/core` (allowScripts) is harmless —
  CSS is pre-built, no plugin needed.

## Verify (playwright-core headless, reuse ~/daily-test)

Browser helper lives in `~/daily-test/node_modules`; script must be run from there
(node resolves deps by script location, not cwd).

```cjs
const {chromium} = require('playwright-core');
chromium.launch({executablePath:
  'C:/Users/datel/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe',
  headless: true});
```

- **Chrome path is `chrome-win64/chrome.exe`** — `chrome-win/` does NOT exist.
- Check overflow: `document.body.scrollWidth > innerWidth` → find offenders via
  `getBoundingClientRect()` (right > viewport or left < 0).
- Screenshot fullPage to project dir, then `vision_analyze` for visual QA.
- `viewport: {width: 390}` works; `isMobile: true` can override width oddly.

## User design preference (for THIS user's main site / landing pages)

- **NO pixel/RPG style on the main site** — user explicitly rejected it
  ("quên pixel đi, tư duy mới"). Pixel fantasy style is only for game/demo
  projects (rune-fate, web games).
- Direction: **modern premium, Linear/Stripe style** — near-black bg `#0a0a0f`,
  Inter font, gradient text (violet→blue `#7c6cf0`→`#5b8def`), glassmorphism nav
  (backdrop blur), subtle radial glow background, and a **dashboard/product mockup
  right under the hero** as the visual anchor (this was the single biggest
  premium upgrade per vision QA).
- Contrast-first still applies: bright text `#f5f5f7`/`#fff` on dark, accent
  `#7c6cf0`, muted `#a1a1b5`.
