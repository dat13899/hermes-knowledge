# Retro Terminal CRT Theme (July 2026)

> Complete Retro Terminal CRT implementation for btdat.io.vn homepage.
> Replaced the Liquid Glass + 3D Scene homepage with a phosphor-green terminal aesthetic.

## Design Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Color palette | `#00ff41` phosphor green on `#050805` near-black | Most iconic terminal aesthetic |
| Font | Geist Mono 100% (both sans + mono vars) | Monospace everywhere = terminal feel |
| Border radius | `0px` everywhere | No rounding = CRT terminal authenticity |
| Shadows | Green glow (`0 0 Npx rgba(0,255,65,...)`) | Terminal phosphor glow replaces soft drop shadows |
| Corner rounding | Radical gradient vignette | Emulates CRT screen curvature |

## Architecture

### CSS Layer Structure

1. **`tokens.css`** — overrode all `[data-theme="dark"]` variables for CRT palette + flat radius + monospace font + glow shadows
2. **`components.css`** — added 6 new CRT effect classes (see below)
3. **`HomePage.jsx`** — completely rewritten with terminal components

### CRT Effect Classes (components.css)

| Class | What it does |
|-------|-------------|
| `.crt-overlay` | Fixed scanline pattern (`repeating-linear-gradient` 1px/3px, 3% opacity black) |
| `.crt-curve` | Radial gradient vignette (`transparent 60% → black 25%` at edges) |
| `.crt-flicker` | `animation: crtFlicker 8s infinite` — subtle opacity oscillation |
| `.terminal-glow` | `text-shadow: 0 0 4px rgba(0,255,65,0.5)` |
| `.terminal-glow-strong` | Triple text-shadow for heading glow |
| `.terminal-cursor` | Blinking green block cursor (`animation: cursorBlink 1s step-end`) |
| `.terminal-pulse` | Opacity pulse for running status dots |
| `.term-dot` / `.term-dot.on` / `.term-dot.off` / `.term-dot.err` | Square (not round!) status indicators |

**CRT flicker animation:**
```css
@keyframes crtFlicker {
  0% { opacity: 0.96; }   5% { opacity: 0.98; }
  10% { opacity: 0.95; }  15% { opacity: 0.97; }
  20% { opacity: 0.96; }  50% { opacity: 0.98; }
  80% { opacity: 0.96; }  90% { opacity: 0.95; }
  100% { opacity: 0.97; }
}
```

## HomePage Architecture

```jsx
export default function HomePage() {
  return (
    <>
      <CRT overlays />       {/* CRT effects — scanlines, curve, flicker */}
      <BootSequence />        {/* One-time boot animation */}
      <AsciiLogo />           {/* Block-letter ASCII art */}
      <TerminalPrompt />      {/* Interactive $ prompt with typed commands */}
      <TerminalServices />    {/* Service list from API */}
      <TerminalTechStack />   {/* Technology badges */}
      <TerminalContact />     {/* SSH simulator + links */}
      <NavLinks />            {/* [dashboard] [documents] etc */}
      <TerminalFooter />      {/* Green border + timestamp */}
    </>
  );
}
```

## Components Detail

### 1. BootSequence

- Plays once per session (stored in `sessionStorage.setItem('crts_boot', '1')`)
- Shows 11-step boot sequence with typed delays:
  - BIOS init → Kernel load → Memory check → Network init → Services start
- Uses `useTypewriter` hook for the final "All systems nominal" line
- Wrapped in `AnimatePresence` for fade-out exit transition
- ASCII art logo "btdat" in block letters renders above boot text

```jsx
const BOOT_LINES = [
  { msg: '▸ SYSTEM INITIALIZATION...', delay: 200 },
  { msg: '  ✓ BIOS v3.0 RETRO EDITION', delay: 300 },
  // ... 11 lines total
];
```

### 2. AsciiLogo

Block-letter ASCII art rendered in a `<pre>` tag:
```
╔══╗╔═══╗╔══╗╔═══╗╔═══╗╔══╗╔═══╗
║  ║║   ║║  ║║   ║║   ║║  ║║   ║
║  ║║   ║║  ║║   ║║   ║║  ║║   ║
║  ║║   ║║  ║║   ║║   ║║  ║║   ║
╚══╝╚═══╝╚══╝╚═══╝╚═══╝╚══╝╚═══╝
```

### 3. TerminalPrompt (Interactive)

Faux terminal with submit handler. Recognizes these commands:

| Command | Response |
|---------|----------|
| `whoami` | `dat — developer / homelab operator / AI enthusiast` |
| `uptime` | Static: `24/7 since 2023` |
| `services` | Not handled as command but auto-displayed below |
| `stack` | Not handled as command but auto-displayed below |
| `contact` | Not handled as command but auto-displayed below |
| `neofetch` | Multi-line system info |
| `date` | Dynamic `new Date().toLocaleString()` |
| `help` | Lists all commands |
| `clear` | Clears history |
| `<anything else>` | `bash: <input>: command not found` |

**Architecture:** Uses `<form onSubmit={handleSubmit}>` with controlled `<input>`. History stored as `{ input, response }[]` in state.

### 4. TerminalServices

Fetches from `/api/services` and renders a monospace list with status dots:
```
── SERVICES ──────────────────────────
  ● AFK Bot         [RUNNING]  2h 15m
  ○ Aternos         [STOPPED]
  ● Agentic RAG     [RUNNING]  5h 30m
```

Uses `.term-dot.on` (square green glow) for running, `.term-dot.off` (dim) for stopped, `.term-dot.err` (red) for error. Running dots get `.terminal-pulse` animation.

### 5. TerminalContact

SSH connection simulator. Two states:
1. **Idle:** Shows `$ ssh btdat@home-lab` as a clickable button + GitHub/Telegram/Email links
2. **Connecting:** Typewriter animates the SSH command, then shows "Connected to btdat.io.vn"

```jsx
// Triggered by button click — no actual SSH connection
const handleSsh = () => {
  // type out SSH_CMD character by character
  // after typing complete, wait 600ms, show "✓ Connected"
};
```

## CRT Effects — How They Stack

```
┌───────────────────────────────────────────┐
│  CRT Curvature (radial-gradient vignette)  │  ← .crt-curve (z-index: 9997)
│  ┌─────────────────────────────────────┐   │
│  │  CRT Scanlines (repeating-linear)   │   │  ← .crt-overlay (z-index: 9998)
│  │  ┌───────────────────────────────┐  │   │
│  │  │  Page Content (z-index: 1)    │  │   │
│  │  └───────────────────────────────┘  │   │
│  └─────────────────────────────────────┘   │
└───────────────────────────────────────────┘
```

CRT flicker animation is applied to `.crt-overlay`, not the content — keeps scanlines subtly alive while content stays crisp.

## Lighting Changes vs Liquid Glass

| Feature | Liquid Glass (previous) | CRT Terminal (this) |
|---------|----------------------|-------------------|
| Background | 3D Three.js torus knot + particles | Pure CSS scanlines + vignette |
| Hero title | Gradient cyan→emerald | Block-letter ASCII art |
| Cards | `.liquid-card` with prismatic overlay | No cards — terminal list style |
| Status | Green pulse dots (round) | Square `.term-dot` with glow |
| Animation | Framer-motion whileInView | Typewriter + CRT flicker |
| Font | Geist Sans (headings) + Mono (code) | Geist Mono 100% |
| Theme vars | Cyan accent, rounded corners | Green accent, 0px radius |

## Builder's Notes

- Scene3D (Three.js) was **removed** from this version — doesn't fit terminal aesthetic
- Boot sequence only plays once per browser session via `sessionStorage`
- Need to ensure `.crt-flicker` doesn't cause motion sickness — animation is very subtle (1-5% opacity delta)
- The `z-index` stack: CRT curvature (9997) < CR overlay (9998) < Boot sequence overlay (9999)
- No external terminal font needed — Geist Mono already imported in `main.jsx`
