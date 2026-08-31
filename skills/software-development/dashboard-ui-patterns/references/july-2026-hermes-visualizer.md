# Hermes Fullscreen Canvas Visualizer — July 2026

## Page servit

`/hermes` → `public/hermes.html` (full HTML page, not a subdirectory).
Server at line 594 of `server.js` maps `/hermes` → `/hermes.html`.

## File structure

```
public/
  hermes.html            — HTML + CSS (rewritten for responsive)
  hermes/
    hermes-core.js       — globals, utils, PALETTES, SCENE_MODES, canvas refs, gradient strip
    hermes-visuals.js    — ALL drawing modes, audio, UI, controls, touch/click handlers
    hermes-main.js       — Main loop (loop function), init sequence
```

## What was fixed (responsive UI/UX)

### 1. Glass navbar (Bulma) with auto-hide
- Desktop: glass navbar with `backdrop-filter:blur(30px)`, auto-hides after 5s idle
- Mobile: hidden, replaced by small `←` back button at top-left
- Theme toggle works via `theme.js` (same as other pages)

### 2. HUD — responsive bottom bar
- `max-width:96vw` + `overflow-x:auto` on mobile
- Hides dividers and less-important labels on small screens

### 3. Mode panel — bottom sheet on mobile
- Desktop: sidebar left (column)
- Mobile (<768px): bottom sheet with `panel-handle` drag indicator
- `env(safe-area-inset-bottom)` for iPhone notch
- Auto-closes after mode selection on mobile

### 4. Config panel — bottom sheet on mobile
- Slides up from below, doesn't overlap HUD
- `max-height:45vh` to stay above keyboard

### 5. Touch interaction guards
- Touch events on UI panels no longer trigger explosions/gravity wells
- Both `touchstart` and `click` handlers guard via `e.target.closest()`

### 6. Splash + theme
- Loading splash, theme.js integration, pulse keyframe added at runtime

## Canvas z-index protocol

| Layer | z-index | Notes |
|-------|---------|-------|
| Trail | 1 | pointer-events:none |
| Main canvas | 2 | cursor:crosshair |
| Bloom | 3 | pointer-events:none |
| Storm overlay/flash | 4-5 | |
| Scene transition | 6 | |
| Hint/Constellation/Gravity | 5 | pointer-events:none |
| HUD | 10 | user-select:none |
| Paint controls | 15 | |
| Mode config | 19 | |
| Mode panel | 20 | |
| Splash | 100 | |
| Navbar | 500 | |
