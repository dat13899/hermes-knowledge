# Hero text over 3D wireframe — fix recipe

Problem: Hero text (e.g. "BT DAT") rendered over Three.js 3D wireframe/particle background gets drowned out — poor contrast, text unreadable, wireframe lines cut through characters.

## Three-layer fix

### 1. Dark radial-gradient overlay
Place a `div` between the 3D canvas and the text content, same stacking context:
```jsx
{/* Dark overlay — right after <Scene3D /> */}
<div style={{
  position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none',
  background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.25) 60%, transparent 100%)',
}} />
```
Key: `pointerEvents: 'none'` so clicks pass through to CTA button. `zIndex: 0` sits below text (`zIndex: 1`) but above 3D canvas.

### 2. textShadow on hero chars
Even with gradient text (`background-clip: text`), a subtle shadow helps glyph edges:
```jsx
textShadow: '0 0 18px rgba(0,0,0,0.45)'
```
Don't use `textShadow` in the gradient style object if using `WebkitBackgroundClip: 'text'` — apply it separately in the same `style={{}}` object. It works because `textShadow` renders behind the clipped gradient text.

### 3. Reduce 3D mesh opacity on mobile
In Scene3D mobile branch:
- Torus opacity: 0.06 → 0.08 (subtle but visible, not overpowering)
- Particle opacity: already 0.3, keep
- Wireframe opacity: already low (0.08 in default props)

## What NOT to do
- Don't increase torus opacity past 0.10 on mobile — it becomes a visual distraction
- Don't add a solid-color overlay — kills the cinematic feel
- Don't hide 3D on mobile — it's the page's signature element
