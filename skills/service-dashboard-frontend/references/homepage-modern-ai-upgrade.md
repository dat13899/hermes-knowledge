# Homepage Modern AI/Tech Upgrade Patterns (July 2026)

## Libraries used (installed for this upgrade)

```json
"motion": "^12.x",         // Framer Motion — animations, scroll reveal, 3D tilt
"canvas-confetti": "^1.x", // Confetti burst on CTA click
```

## Motion patterns

### LazyMotion (code splitting)
```jsx
import { LazyMotion, domAnimation } from 'motion/react';
// Wrap entire page:
<LazyMotion features={domAnimation}>
  {/* page content */}
</LazyMotion>
```

### Scroll parallax
```jsx
const { scrollY } = useScroll();
const sphereScale = useTransform(scrollY, [0, 400], [1, 0.3]);
const sphereOpacity = useTransform(scrollY, [0, 400], [1, 0]);
```

### Scroll reveal (useInView)
```jsx
const ref = useRef(null);
const inView = useInView(ref, { once: true, margin: '-100px' });
// Then use motion.div with:
animate={inView ? { opacity: 1, y: 0 } : {}}
```

### Staggered entry
```jsx
// Inside a map:
<motion.div
  key={item.id}
  initial={{ opacity: 0, y: 20 }}
  animate={inView ? { opacity: 1, y: 0 } : {}}
  transition={{ delay: 0.15 + index * 0.05, duration: 0.4 }}
>
```

### Hover/tap effects
```jsx
whileHover={{ scale: 1.06, boxShadow: '0 0 35px rgba(52,211,153,0.5)' }}
whileTap={{ scale: 0.96 }}
```

## GlitchText component

```
components/GlitchText.jsx
```
- Two `@aria-hidden` spans with `clipPath` masks: red (#ff006e) translated (-2,1) and cyan (#00f0ff) translated (2,-1)
- Base text below both with gradient + slight blur
- Triggers every 3-5s via setTimeout, lasts 200ms
- Must keep base text visible for readability — overlays are decorative only

## WireframeSphere component (canvas 2D)

```
components/WireframeSphere.jsx
```
- No Three.js — pure Canvas 2D, ~2KB
- Props: width, height, color, speed, opacity
- Nested loops: rings × pointsPerRing → 3D → Y rotation → perspective projection
- DPR scaling: `c.width = width * dpr; ctx.scale(dpr, dpr)`
- Perspective: `scale = 200 / (200 + rz)` — constant tunable for depth
- Multiple instances in HeroSection: main (right, opacity 0.5) + smaller (left, opacity 0.25)

## AIBadge component

```
components/AIBadge.jsx
```
- Green dot with `aiPulse` CSS animation (box-shadow pulse)
- Outer ripple ring with `aiRipple` animation (scale + fade)
- Glass-background pill: `rgba(34,197,94,0.08)` border with `rgba(34,197,94,0.2)`

## 3D tilt cards (ServiceSection)

```jsx
const [rotate, setRotate] = useState({ x: 0, y: 0 });
const handleMove = (e) => {
  const rect = ref.current.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width - 0.5;
  const y = (e.clientY - rect.top) / rect.height - 0.5;
  setRotate({ x: y * 8, y: x * 8 });
};
// Style: transform: `perspective(600px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`
// transition: 'transform 0.1s ease' for smooth return on mouse leave
// Combined with whileHover={{ y: -4 }} from motion
```

## Rotating conic-gradient border

CSS `@property --border-angle` with `conic-gradient` via `::before`:
```css
.rotating-border::before {
  content: ''; position: absolute; inset: -1px;
  border-radius: inherit;
  background: conic-gradient(from var(--border-angle), var(--accent), var(--green), var(--accent));
  opacity: 0; z-index: -1;
  animation: borderRotate 3s linear infinite;
}
.rotating-border:hover::before { opacity: 1; }
```

## CountUp animation

```
pages/home/AnimatedStatsBanner.jsx
```
- `useInView` trigger → `setInterval` step counter 16ms
- Step: `Math.ceil(end / (duration * 60))`
- Gradient text: `WebkitBackgroundClip: 'text'` + `WebkitTextFillColor: 'transparent'`
- 4 stat cards in auto-fit grid: Services Online, Uptime, AI Requests, Microservices

## AI Features Section

```
pages/home/AISection.jsx
```
- 3 cards in auto-fit grid: Hermes Agent, RAG Knowledge Base, AI Tools Suite
- Each card: icon, title, description, tags (small pills)
- WireframeSphere decoration background-right
- `rotating-border` class for hover border effect
- Tags: `rgba(52,211,153,0.1)` background, `var(--accent)` text

## canvas-confetti

```jsx
import confetti from 'canvas-confetti';
const fireConfetti = useCallback(() => {
  confetti({
    particleCount: 80, spread: 70,
    origin: { y: 0.6, x: 0.5 },
    colors: ['#34d399', '#10b981', '#fff', '#6ee7b7'],
  });
}, []);
// On CTA click: fireConfetti(); setTimeout(() => navigate, 300);
```

## Animated grid background

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

## Keyframe additions (mobile-ux.css)

```css
@keyframes aiPulse {
  0%, 100% { box-shadow: 0 0 4px var(--green); }
  50% { box-shadow: 0 0 12px var(--green), 0 0 24px rgba(34,197,94,0.4); }
}
@keyframes aiRipple {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(3); opacity: 0; }
}
```

## Section integration order (HomePage)

```jsx
<LazyMotion features={domAnimation}>
  <HeroSection displayedText={displayedText} scrollTo={scrollTo} />
  <AnimatedStatsBanner services={services} />
  <ServicesSection ... />
  <AISection />
  <TechStackSection />
  <ContactSection toast={toast} />
  <ConfirmModal ... />
</LazyMotion>
```

## Build impact

HomePage chunk: ~166KB (includes motion library). Worth it for the animation quality — motion uses spring physics, GPU-accelerated transforms, and proper RAF scheduling.

## User feedback pattern

User judged font/color-only changes as "vẫn thế, ko có gì đột phá." The pattern that satisfied was:
- Visible animation (glitch, sphere, confetti, count-up, scroll reveal)
- Interactive 3D (tilt cards, rotating borders)
- Touch feedback (ripple effects, hover states)
- "Wow" on first F5, not subtle improvements

Rule: when user wants "wow" or "đột phá" → add animation/motion, not just CSS polish.
