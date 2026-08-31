# Pixel Fantasy Design System — btdat.io.vn

> Complete design reference for the 16-bit RPG pixel fantasy theme.
> Added 2026-07-30 in a full-site theme migration from Retro Terminal CRT.

## Readability Lessons (learned 2026-07-30)

**Press Start 2P is ONLY for short headings and nav labels.** Never use it for body text, paragraphs, or descriptions — it is unreadable below 0.7rem and fatiguing even at larger sizes.

**Font hierarchy (applied after user complaint):**
- Display / short headings → `Press Start 2P`
- Body / descriptions → `Geist Sans` (via `--font-body`)
- Decorative / retro flair → `VT323` (fallback, not primary body)
- Code / logs → `JetBrains Mono`

**Contrast fix:** `--text-dim` was `#8a7a6a` → bumped to `#a09080`. `--text` was `#f4e8c1` → bumped to `#f0dec0`. Light mode `--text-dim` from `#6b4e3a` → `#8a7050`.

**Scanlines:** `opacity: 0.08` at 2px caused moiré patterns. Reduced to `opacity: 0.03` at 3px spacing. If still distracting, remove entirely.

## PageHeader Component

Created 2026-07-30. Lives at `src/components/pixel/PageHeader.jsx`. Exported from `src/components/pixel/index.js`.

```jsx
<PageHeader
  icon="📊"
  title="Quest Log"
  subtitle="Monitor your domain services"
  glow="purple"   // "purple" | "gold" | "blue"
/>
```

**Always use PageHeader instead of inline h1 headers.** Every route has one:
- `/` → emoji in hero (not PageHeader, unique)
- `/dashboard` → Quest Log (purple)
- `/documents` → Scroll Library (gold)
- `/widgets` → Alchemy Lab (blue)
- `/stream` → Crystal Ball Scrying (blue)
- `/utilities` → Enchanting Table (gold)
- `/hermes` → Arcane Focus (purple)
- `/*` → 404 Lost in the Dungeon (gold, custom)

## Tokens (in `pixel-tokens.css`)

| Token | Dark | Light |
|-------|------|-------|
| `--bg` | `#1a0e0a` | `#f4e8c1` |
| `--surface` | `#2a1a0e` | `#e8d8a8` |
| `--surface-2` | `#3a2a1a` | `#dcc88e` |
| `--border` | `#5a3a2a` | `#c4a86a` |
| `--text` | `#f0dec0` | `#2a1a0e` |
| `--text-strong` | `#fff8e8` | `#1a0e0a` |
| `--text-dim` | `#a09080` | `#8a7050` |
| `--accent` | `#7c4dff` | `#7c4dff` |
| `--magic-blue` | `#4fc3f7` |
| `--ember-gold` | `#ffb300` |
| `--healing-green` | `#66bb6a` |
| `--blood-red` | `#e53935` |
| `--font-pixel` | `Press Start 2P` |
| `--font-body` | `Geist Sans` |
| `--font-sans` | `Geist Sans, VT323` |

## Navbar — RPG HUD Bar

`src/components/layout/Navbar.jsx`. The ONLY navbar.

**Structure:**
- Fixed top bar with ⚔️ level badge (BT DAT · LV.30 ENGINEER, gold border)
- Desktop: horizontal spell-slot links — active item has purple border + glow
- Mobile: bottom hotbar (game inventory style) — activated via `.is-hidden-tablet` / `.is-hidden-desktop`
- Theme toggle: moon/sun seal button
- Mobile dropdown: hamburger → expanded link list

**Edge cases:**
- Nav links use emoji icons + short label (Log, Scrolls, Items, Alchemy...)
- BottomTab is REMOVED — the Navbar component IS the bottom nav on mobile
- Wrapping `/components/Navbar.jsx` is orphaned dead code, never edit it

## Pixel Components

| Component | File | API |
|-----------|------|-----|
| PixelButton | `components/pixel/PixelButton.jsx` | `variant="primary|secondary|gold|danger|ghost"`, `size="sm|md|lg"`, `glow` |
| PixelCard | `components/pixel/PixelCard.jsx` | `variant="dark|parchment|stone|magic"`, `glow="purple|blue|gold"`, `padding` |
| PixelProgress | `components/pixel/PixelProgress.jsx` | `value`, `max?`, `color?`, `label?`, `height?` |
| PageHeader | `components/pixel/PageHeader.jsx` | `icon`, `title`, `subtitle?`, `glow?` |

## Pixel CSS Classes (in `pixel-tokens.css`)

- `.pixel-border` — 2px hard border + shadow
- `.pixel-border-thick` — 3px hard border
- `.pixel-btn-3d` — chiseled 3D button look
- `.pixel-bar` — pixelated progress bar
- `.pixel-scanlines` — CRT monitor lines (via `::after`)
- `.pixel-bg-dungeon` — repeating cobblestone pattern
- `.pixel-parchment` — warm scroll/paper background
- `.pixel-divider` — pixel dashed/checkered horizontal rule
- `.pixel-glow-purple/.pixel-glow-gold/.pixel-glow-blue` — text glow

## Post-Mortem: Common Crash Causes During Theme Migration

### ErrorBoundary "Có lỗi xảy ra"
This text comes from `src/components/shared/ErrorBoundary.jsx`. When you see it:
1. Check `AppLayout.jsx` — did you leave any imports from the old theme? Footer (uses `useMediaQuery` + `glass-dock`), CommandPalette (uses `useHaptic`), BlobBackground, or `useSwipeBack` hook.
2. These old components depend on CSS classes (`glass-dock`, `liquid-skeleton`, `glass-panel`, `animated-blobs`) and hooks that don't exist after theme migration.
3. Fix: nuke ALL old theme imports in AppLayout. Import only Navbar. Keep no "maybe needed" leftovers.

### Port clash on restart
After killing node processes, a stale PID can still hold port 3000. Use:
```
netstat -ano | grep LISTENING | grep ":3000 "
taskkill /F /PID <PID>
```
Then verify empty before starting new server.

### Tunnel stale connection
If cloudflared shows "dial tcp [::1]:3000: connectex: actively refused it", the old tunnel is pointing to a dead server. Kill the old tunnel process and restart both server and tunnel together.
