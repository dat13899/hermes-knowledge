# Apple Authentic Liquid Glass (WWDC25) — Research Notes 2026-08-26

> Trigger: user said "làm kiểu này không giống, phải nghiên cứu kỹ vào xem cách apple làm như nào" — blur-only glassmorphism ≠ Liquid Glass. Required deep research before re-implementing.

## Why blur-only is wrong
Apple: *"Liquid Glass isn't a blur filter with rounded corners. It's a 2D optical simulation that only looks like 3D."* (1ar.io). Previous demo used `backdrop-filter: blur(20px)` only = glassmorphism. Missing refraction.

## 6-layer stack (bottom → top)
1. **Refraction (displacement)** — 2D displacement map, R/G = refraction vector, `scale ~16, n=1.5`, `feDisplacementMap` in SVG filter. Core.
2. **Blur (variable)** — `backdrop-filter: blur(28px) saturate(160%) brightness(1.05)` — thicker glass = more blur/lensing.
3. **Tint** — `rgba(255,255,255,.07)` very faint glass color.
4. **Inner Fresnel rim** — `inset 0 1px 0 rgba(255,255,255,.35)` + `inset 0 -1px 0 rgba(255,255,255,.08)`.
5. **Top specular** — `linear-gradient(180deg, rgba(255,255,255,.32) 0%, rgba(255,255,255,.14) 14%, transparent 45%)` — shifts with gyroscope. Screenshots look flat because this is lost.
6. **Shadow** — `0 20px 60px rgba(0,0,0,.45)` — larger element = thicker material = deeper shadow + stronger lensing (Apple WWDC25: "When Liquid Glass morphs to larger sizes, it simulates thicker material").

## Surface shape — Squircle
```
y = (1 - (1-x)^4)^(1/4)   // Apple continuous corner
```
`border-radius` causes harsh refraction at corners when stretched to pill/rect. Squircle keeps gradient smooth even when stretched. Displacement map must use this formula.

## Physics
- Snell: `n₁·sinθ₁ = n₂·sinθ₂`, glass `n=1.5`, air `n=1`.
- Shrink 2% then stretch edges → lens thickness at bezel, flat in center. All 2D (planar map on flat bg) — works because viewing angle is narrow. Cheaper than real 3D.
- Derivative via finite diff `eps=0.001` to get normal vector, then encode as R/G.

## Implementation pattern
```html
<svg width="0" height="0"><filter id="liquid" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">
  <feImage href="DISPLACEMENT_MAP.png" result="map"/>
  <feDisplacementMap in="SourceGraphic" in2="map" scale="16" xChannelSelector="R" yChannelSelector="G"/>
</filter></svg>
<div style="filter: url(#liquid)"><div class="glass">content</div></div>
```
- Displacement map generated on canvas via squircle + Snell (see `buildDisplacementMap()` in `dist/documents/liquid-glass-apple.html` — copies full algorithm with 256x256 canvas, bezel 22px).
- Also need to update `feDisplacementMap scale` dynamically when user tweaks refraction.

## Browser support
- `filter: url(#liquid)` + `backdrop-filter` combo is **Chrome-only** for smooth refraction. Safari/Firefox: fallback to blur-only.
- Test on Chrome desktop; mobile gyro via `DeviceOrientationEvent` → `rotateY(gamma * 0.3deg)`.

## When to use which
- Dashboard cards/tabs/inputs → existing `.liquid-card` classes (blur-only, lightweight)
- Hero / marketing demo where "giống Apple thật" required → displacement map version

## References
- Apple WWDC25 session 219: Meet Liquid Glass — https://developer.apple.com/videos/play/wwdc2025/219/
- 1ar.io: How Liquid Glass works — https://1ar.io/updates/how-liquid-glass-works
- kube.io: Liquid Glass in the Browser (refraction with CSS+SVG, Snell math, 4 surface functions) — https://kube.io/blog/liquid-glass-css-svg/
- Demo: `dist/documents/liquid-glass-apple.html` served at `/liquid-glass`

## Pitfall added 2026-08-26
- Never ship blur-only as "Liquid Glass" — user will immediately notice missing edge refraction. Research first, verify viền có uốn cong lưới nền.
