# Liquid Glass Design System

> Full reference for the Liquid Glass design layer built on 2026-07-26.
> Adds depth-aware, prismatic glass on top of the base glass-morphism tokens.

## Design Tokens (`tokens.css`)

| Token | Value | Purpose |
|-------|-------|---------|
| `--liquid-bg` | `rgba(10,14,23,0.65)` | Deeper background for cards/panels |
| `--liquid-border` | `rgba(255,255,255,0.07)` | Softer, more transparent border |
| `--liquid-glow` | `rgba(0,212,255,0.08)` | Accent glow for active states |
| `--prismatic` | `linear-gradient(135deg, rgba(0,212,255,0.12), rgba(0,168,224,0.06), rgba(102,224,255,0.04))` | Chromatic aberration overlay on hover |
| `--depth-raise` | `0 4px 24px rgba(0,0,0,0.3) + inset 1px rgba(255,255,255,0.04)` | Base card elevation |
| `--depth-float` | `0 8px 40px rgba(0,0,0,0.4) + inset 1px rgba(0,212,255,0.08)` | Hover/popover elevation |
| `--depth-modal` | `0 16px 60px rgba(0,0,0,0.5) + inset 1px rgba(0,212,255,0.12)` | Modal/max elevation |

**Light theme** uses same token names with lighter values (`rgba(255,255,255,0.55)` backgrounds etc).

## CSS Classes (`components.css`)

### `.liquid-card`
Full card with prismatic hover effect.
```html
<div class="liquid-card" style="padding: 1rem; cursor: pointer;">
  Content
</div>
```
- `backdrop-filter: blur(24px) saturate(180%)`
- `::before` pseudo-element with `--prismatic` gradient, fades in on hover
- `border-radius: var(--radius-lg)`

### `.liquid-panel`
Section container with top accent line.
```html
<div class="liquid-panel" style="padding: 1.25rem;">
  Section content
</div>
```
- `backdrop-filter: blur(20px) saturate(160%)`
- `::after` pseudo-element: 1px `linear-gradient(90deg, transparent, var(--accent), transparent)` top edge
- Slightly less blur than card (distinguishes container from content)

### `.liquid-input`
Glass text input.
```html
<input class="liquid-input" placeholder="Search..." />
```
- `background: rgba(255,255,255,0.04)`, `backdrop-filter: blur(8px)`
- Focus: `border-color: var(--accent)` + `box-shadow: 0 0 0 3px var(--liquid-glow)`
- `min-height: 44px` (tap target)

### `.liquid-btn`
Glass action button with variants.
```html
<button class="liquid-btn">Default</button>
<button class="liquid-btn primary">Primary</button>
<button class="liquid-btn danger">Danger</button>
<button class="liquid-btn sm">Small</button>
```
- `background: rgba(255,255,255,0.04)`, `backdrop-filter: blur(12px)`
- Hover: `translateY(-1px)`, border → accent, bg brightens
- Active: `scale(0.97)`
- `.primary`: accent bg + glow shadow
- `.danger`: red-tinted bg
- `.sm`: compact (32px min-height)

### `.liquid-tabs` / `.liquid-tab`
iOS-style segmented tab bar.
```html
<div class="liquid-tabs">
  <button class="liquid-tab active">Tab 1</button>
  <button class="liquid-tab">Tab 2</button>
</div>
```
- Container: `padding: 4px`, rounded `var(--radius-lg)`
- Active tab: `background: var(--liquid-glow)`, `color: var(--accent)`, glow shadow
- Hover inactive: subtle bg brighten

### `.liquid-stat`
Stat/metric card with hover float.
```html
<div class="liquid-stat">
  <div class="liquid-stat-value">47.2<span style="font-size:0.5em">%</span></div>
  <div class="liquid-stat-label">Uptime</div>
</div>
```
- Hover: `translateY(-2px)`, border glows accent, shadow deepens
- Value: mono font, accent color, `letter-spacing: -0.02em`
- Label: uppercase, `letter-spacing: 0.06em`

## Mobile Performance (`mobile-ux.css`)

On mobile (≤768px), blur is reduced to prevent GPU jank:

| Desktop | Mobile | Element |
|---------|--------|---------|
| `blur(24px) saturate(180%)` | `blur(12px) saturate(140%)` | `.liquid-card`, `.liquid-panel`, `.liquid-stat` |
| `blur(8px)` | `blur(6px)` | `.liquid-input` |
| Prismatic overlay active | **disabled** (`display: none`) | `.liquid-card::before` |

Also added `.liquid-panel-scroll` for iOS momentum scrolling on glass panels.

## Migration from old classes

| Old class/style | Liquid equivalent |
|-----------------|-------------------|
| `className="card"` + inline glass | `className="liquid-card"` |
| `className="glass-panel"` | `className="liquid-panel"` |
| `className="input"` | `className="liquid-input"` |
| `className="btn btn-glass"` | `className="liquid-btn"` |
| `className="btn btn-primary"` | `className="liquid-btn primary"` |
| `className="btn btn-danger"` | `className="liquid-btn danger"` |
| Inline stat card with `background: rgba(...)` | `className="liquid-stat"` + `liquid-stat-value` + `liquid-stat-label` |

## Depth Layering

```
Background (--bg) < Surface (--surface) < Liquid Card < Liquid Panel < Bottom Sheet < Modal
```

Each layer has progressively stronger blur + darker/lighter background + deeper shadow.
