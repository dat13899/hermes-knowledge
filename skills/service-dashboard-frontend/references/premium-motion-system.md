# Premium Motion System — Full Reference

**Date:** July 2026  
**Libraries:** `lenis` (5.6KB gzip), `motion` (already present), `canvas-confetti` (2KB gzip)

---

## Lenis Smooth Scroll (AppLayout.jsx)

Lazy-imported in `useEffect` to avoid blocking initial render:

```jsx
useEffect(() => {
  let lenis;
  import('lenis').then(mod => {
    const Lenis = mod.default;
    lenis = new Lenis({
      lerp: isMobile ? 0.1 : 0.065,
      wheelMultiplier: 1,
      smoothWheel: true,
      syncTouch: true,
    });
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  });
  return () => lenis?.destroy();
}, [isMobile]);
```

**Key params:** `lerp` controls inertia (0.065 = smooth desktop, 0.1+ = mobile to avoid lag). `syncTouch: true` keeps native scroll accessibility.

---

## Custom Cursor (Cursor.jsx)

Spring-follow dot using `useMotionValue` + `useSpring` from Motion:

```jsx
const mouseX = useMotionValue(-100);
const mouseY = useMotionValue(-100);
const springX = useSpring(mouseX, { damping: 25, stiffness: 250, mass: 0.5 });
const springY = useSpring(mouseY, { damping: 25, stiffness: 250, mass: 0.5 });
const size = useMotionValue(12);
const springSize = useSpring(size, { damping: 15, stiffness: 200 });
```

**States:**
- Default: 12px translucent emerald `rgba(52,211,153,0.5)` dot
- Hover interactive (a, button, .card, [role="button"], input, textarea, select): grows to 32px, semi-transparent `rgba(52,211,153,0.15)` with glow shadow
- Touch device: hidden entirely via `window.matchMedia('(pointer: coarse)').matches`
- `z-index: 100000`, `pointer-events: none`, `mixBlendMode: 'normal'`
- Hides on `mouseleave` document event

**Detection:** `mouseover` event with `e.target.closest('a, button, .card, [role="button"], input, textarea, select')`

---

## Magnetic Wrapper (Magnetic.jsx)

Child element follows cursor when hovered. Reusable across any element:

```jsx
<Magnetic strength={0.3}>
  <button>Click me</button>
</Magnetic>
```

**Mechanics:**
- `onMouseMove`: calculate distance from cursor to element center
- Pull factor: `(1 - distance/150) * strength * 1.5` (150px influence radius)
- Spring physics: `damping: 15, stiffness: 200, mass: 0.1`
- `onMouseLeave`: animate back to `{x: 0, y: 0}`
- `display: 'inline-block'` on wrapper to preserve layout

---

## Page Transitions (AppLayout.jsx)

`AnimatePresence mode="wait"` wrapping `<Outlet />` with `key={location.pathname}`:

```jsx
const pageVariants = {
  initial: { opacity: 0, y: 12, scale: 0.985 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] } },
  exit: { opacity: 0, y: -8, scale: 0.99, transition: { duration: 0.2, ease: 'easeIn' } },
};

<AnimatePresence mode="wait">
  <motion.div key={location.pathname} variants={pageVariants}
    initial="initial" animate="animate" exit="exit" style={{ flex: 1 }}>
    <Outlet />
  </motion.div>
</AnimatePresence>
```

**CRITICAL:** AnimatePresence wraps `<Outlet />`, NOT the `<main>` element. The `<main>` stays static; only the page content inside transitions.

---

## GlitchText (GlitchText.jsx)

Cyberpunk RGB channel split + skew jitter. Props: `text`, `className`, `as` (tag), `active` (default true), `style`.

```jsx
<GlitchText text="BT DAT" style={{ fontSize: 'clamp(2.5rem, 7vw, 4.5rem)' }} />
```

**Mechanism:**
- Timer loop: triggers glitch every 3-7s (random), lasts 200ms
- Two pseudo-layers: pink `#ff006e` (top 45% clipPath, `translate(-2px, 1px)`) and cyan `#00f0ff` (bottom 55% clipPath, `translate(2px, -1px)`)
- Active text: gradient `var(--text-strong) → var(--accent)` with 0.3px blur
- When not glitching: renders single `<Tag>` with gradient text only
- `aria-hidden="true"` on pseudo-layers for accessibility

---

## WireframeSphere (WireframeSphere.jsx)

3D rotating wireframe sphere via Canvas 2D — no Three.js. Props: `width`, `height`, `color`, `speed` (default 0.005), `opacity` (default 0.6).

```jsx
<WireframeSphere width={240} height={240} color="rgba(52,211,153,0.35)" opacity={0.5} />
```

**Math:**
- 14 rings × 32 points per ring
- Y-axis rotation: `rx = x3*cos(angle) - z3*sin(angle)`, `rz = x3*sin(angle) + z3*cos(angle)`
- Perspective projection: `scale = 200/(200+rz)`, `px = cx + rx*scale`, `py = cy + y3*scale`
- `requestAnimationFrame` loop, auto-cleanup on unmount
- Device pixel ratio capped at 2 (`Math.min(dpr, 2)`)
- `pointer-events: none` so it doesn't block clicks

---

## Scroll Parallax (HeroSection.jsx)

`useScroll()` + `useTransform()` from Motion for multi-layer parallax:

```jsx
const { scrollY } = useScroll();
const sphereScale = useTransform(scrollY, [0, 400], [1, 0.3]);
const sphereOpacity = useTransform(scrollY, [0, 400], [1, 0]);
const heroOpacity = useTransform(scrollY, [0, 300], [1, 0]);
```

Wireframe spheres shrink+hide as user scrolls. Hero content fades. All GPU-accelerated.

---

## 3D Tilt Cards (ServicesSection.jsx)

`onMouseMove` calculates rotation from cursor position relative to card center:

```jsx
const handleMove = (e) => {
  const rect = ref.current.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width - 0.5;
  const y = (e.clientY - rect.top) / rect.height - 0.5;
  setRotate({ x: y * 8, y: x * 8 });
};

// Applied inline:
transform: `perspective(600px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`
```

`transition: 'transform 0.1s ease'` for smooth following. `will-change: transform` from `.tilt-card` CSS class.

---

## Rotating Gradient Border (mobile-ux.css)

CSS `@property` + `conic-gradient` animation on `::before` pseudo-element:

```css
@property --border-angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}
@keyframes borderRotate {
  0% { --border-angle: 0deg; }
  100% { --border-angle: 360deg; }
}
.rotating-border::before {
  content: '';
  position: absolute; inset: -1px; border-radius: inherit;
  background: conic-gradient(from var(--border-angle), var(--accent), var(--green), var(--accent));
  opacity: 0; transition: opacity 0.3s; z-index: -1;
  animation: borderRotate 3s linear infinite;
}
.rotating-border:hover::before { opacity: 1; }
```

Add `className="card rotating-border"` to any glass card.

---

## Animated Counter (CountUp in AnimatedStatsBanner.jsx)

`useInView({ once: true })` triggers count-up from 0 to target:

```jsx
function CountUp({ end, duration = 2, suffix = '', prefix = '' }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = Math.ceil(end / (duration * 60));
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setCount(end); clearInterval(timer); }
      else setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [inView, end, duration]);

  return <span ref={ref}>{prefix}{count.toLocaleString()}{suffix}</span>;
}
```

---

## Stagger Scroll Reveal (all sections)

Motion variants for list items:

```jsx
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.15 } }
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};
```

Used across: ServiceCards grid (stagger 0.05s), TechStack badges (stagger 0.04s), AI feature cards (stagger 0.1s).

---

## Confetti on CTA (HeroSection.jsx)

```jsx
import confetti from 'canvas-confetti';

const fireConfetti = useCallback(() => {
  confetti({
    particleCount: 80, spread: 70, origin: { y: 0.6, x: 0.5 },
    colors: ['#34d399', '#10b981', '#fff', '#6ee7b7']
  });
}, []);

// On CTA click: fireConfetti() → setTimeout(navigate, 300)
```

---

## AI Badge (AIBadge.jsx)

Pulsing green dot with ripple animation + "AI Active" label:

```jsx
<AIBadge pulse={true} size="md" />
```

CSS keyframes: `aiPulse` (box-shadow pulse 2s) + `aiRipple` (scale 1→3 opacity 0.5→0 2s).

---

## Animated Grid Background

```css
.grid-bg {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(52,211,153,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(52,211,153,0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: gridMove 20s linear infinite;
  pointer-events: none; z-index: 0;
}
@keyframes gridMove {
  0% { background-position: 0 0; }
  100% { background-position: 40px 40px; }
}
```

Add `<div className="grid-bg" />` inside hero section.

---

## Bundle Size Impact

| Library | Size (gzip) |
|---------|-------------|
| `lenis` | ~5.6KB |
| `motion` | ~30KB (shared across chunks) |
| `canvas-confetti` | ~2KB |
| **Total added** | **~8KB** (plus Motion shared) |

Index.html bundle: ~385KB total (was ~251KB before motion system).
