# Liquid Glass Design System

Proven, repeatable premium glassmorphism pattern deployed across btdat.io.vn.

## CSS Custom Properties

Add to tokens.css under `[data-theme="dark"]`:
```css
--liquid-bg: rgba(10, 14, 23, 0.65);
--liquid-border: rgba(255, 255, 255, 0.07);
--liquid-glow: rgba(0, 212, 255, 0.08);
--prismatic: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(0, 168, 224, 0.06), rgba(102, 224, 255, 0.04));
--depth-raise: 0 4px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
--depth-float: 0 8px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 212, 255, 0.08) inset;
--depth-modal: 0 16px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 212, 255, 0.12) inset;
```

## CSS Classes (components.css)

| Class | Blur | Purpose |
|-------|------|---------|
| `.liquid-card` | 24px saturate(180%) | Cards, grid items. Prismatic `::before` hover overlay |
| `.liquid-panel` | 20px saturate(160%) | Section containers. Accent top-line `::after` |
| `.liquid-input` | 8px | Form inputs. Focus glow ring |
| `.liquid-btn` | 12px | Buttons. `.primary` (accent glow), `.danger`, `.sm` |
| `.liquid-tabs/.liquid-tab` | 12px | Tab bar. `.active` glow background |
| `.liquid-stat` | 20px saturate(180%) | Metric cards. Hover float + border accent |
| `.liquid-skeleton` | none | Shimmer loader, 1.8s animation |

## Mobile Performance Safety

```css
@media (max-width: 768px) {
  .liquid-card, .liquid-panel, .liquid-stat {
    backdrop-filter: blur(12px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(12px) saturate(140%) !important;
  }
  .liquid-input {
    backdrop-filter: blur(6px) !important;
    -webkit-backdrop-filter: blur(6px) !important;
  }
  .liquid-card::before { display: none; } /* disable prismatic GPU overhead */
}
```

## Animated Blob Background

3 drifting gradient blobs, desktop only. Each:
```css
.animated-blob {
  position: absolute; border-radius: 50%;
  filter: blur(80px); opacity: 0.12;
  animation: blobDrift 18-25s ease-in-out infinite;
  /* Size: 300-400px each, positioned off-edge */
}
```
Disable on mobile entirely — too GPU-heavy.

## Page Transitions (AppLayout)

```jsx
<AnimatePresence mode="wait">
  <motion.div key={location.pathname}
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.2, ease: 'easeOut' }}
  >
    <Outlet />
  </motion.div>
</AnimatePresence>
```

## Command Palette

`Ctrl+K` / `Cmd+K` global. Component: `CommandPalette.jsx` + `useCommandPalette()` hook. Glass overlay, fuzzy search, arrow-key nav, haptic feedback on selection. Integrate in AppLayout for site-wide access.

## Toast Redesign

Replace solid-color toasts with `liquid-panel` containers + `AnimatePresence`. Color-coded icon circles + spring enter/exit animation. Each toast has `boxShadow` with a tinted inset border matching its type color.

## 404 Page

Liquid-card wrapper + SVG gradient `<text>` element + spring scale animation + hint "Ctrl+K to search".

## Pitfalls

- `backdrop-filter` needs `-webkit-backdrop-filter` fallback ALWAYS
- Blur > 24px on mobile → scroll jank. Use `@media` override
- Prismatic `::before` must be `pointer-events: none`
- Animated blobs must be `position: fixed`, `z-index: 0`, `pointer-events: none`
- When converting inline styles to liquid-* classes, batch search patterns like `style={{...backdropFilter...border...boxShadow` across all pages
