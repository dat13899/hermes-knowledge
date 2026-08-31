# HomePage Patterns (July 2026)

> Homepage redesign patterns used in the btdat.io.vn React frontend.

## Architecture

The HomePage is assembled from self-contained sections, each a named function component. Sections are stacked vertically in the main export. No shared state between sections — each fetches its own data or receives none.

```jsx
export default function HomePage() {
  return (
    <>
      <HeroSection />
      <LiveStatsBar />
      <FeaturesGrid />
      <TechStackSection />
      <LiveServicesSection />
      <AISection />
      <TerminalContact />
    </>
  );
}
```

## Section Patterns

### 1. HeroSection — 3D Background + Rotating Taglines

- **Background:** `Scene3D` component (lazy-loaded Three.js torus knot + particle field) rendered as fixed background layer
- **Title:** Gradient text using `background: linear-gradient(...)`, `WebkitBackgroundClip: 'text'`, `WebkitTextFillColor: 'transparent'`
- **Taglines array:** Rotates every 3.5s using `AnimatePresence mode="wait"` with fade-up/fade-down
- **Scroll indicator:** Bouncing chevron at bottom, click scrolls to `#features`

```jsx
const HERO_LINES = [
  '⚡ Home Lab chạy 24/7',
  '🤖 Tự động hóa với AI',
  '🎮 Minecraft server luôn online',
];

// Rotating tagline via setInterval + AnimatePresence
const [lineIdx, setLineIdx] = useState(0);
useEffect(() => {
  const interval = setInterval(() => {
    setLineIdx(prev => (prev + 1) % HERO_LINES.length);
  }, 3500);
  return () => clearInterval(interval);
}, []);
```

### 2. AnimatedCounter — IntersectionObserver Scroll Trigger

Counts from `from` → `to` when scrolled into view. Uses `IntersectionObserver` + `requestAnimationFrame` + easeOutCubic.

```jsx
function AnimatedCounter({ from = 0, to, suffix = '', duration = 2, decimals = 0 }) {
  const [value, setValue] = useState(from);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const startTime = performance.now();
          const step = (now) => {
            const elapsed = Math.min((now - startTime) / (duration * 1000), 1);
            const eased = 1 - Math.pow(1 - elapsed, 3); // easeOutCubic
            setValue(from + (to - from) * eased);
            if (elapsed < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [from, to, duration]);

  return <span ref={ref}>{value.toFixed(decimals)}{suffix}</span>;
}
```

**Usage:** `<AnimatedCounter from={0} to={running} duration={1.5} />`

### 3. LiveStatsBar — API + Glass Pill

Fetches services via `fetchServices()` on mount, displays running/total count in a glass pill (`borderRadius: 999px`, glass backdrop-filter). Uses `AnimatedCounter` for the running count.

```jsx
function LiveStatsBar() {
  const [services, setServices] = useState([]);
  useEffect(() => {
    fetchServices().then(d => setServices(d || [])).catch(() => {});
  }, []);
  // ...
}
```

### 4. FeaturesGrid — Stagger Scroll Reveal

6 feature cards using `motion.div` with `whileInView` + staggered `transition.delay`. Each card: icon in gradient box, name, description, chevron. Click navigates via `useNavigate()`.

```jsx
<FEATURES.map((feat, i) => (
  <motion.div
    key={feat.name}
    initial={{ opacity: 0, y: 25 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, amount: 0.2 }}
    transition={{ duration: 0.4, delay: 0.05 * i }}
    className="liquid-card card-hover"
    onClick={() => navigate(feat.to)}
  >
    {/* icon + title + description */}
  </motion.div>
))}
```

### 5. TechStackSection — Categorized Badges

Tech stack grouped by category (`Backend`, `Frontend`, `DevOps`, `AI`). Each badge uses inline style with hover event handlers (no CSS class) to change bg/accent on hover. This avoids CSS specificity issues when toggling background between glass and accent.

```jsx
<span style={{ background: 'var(--glass-bg)', ... }}
  onMouseEnter={e => {
    e.currentTarget.style.background = 'var(--accent)';
    e.currentTarget.style.color = '#fff';
  }}
  onMouseLeave={e => {
    e.currentTarget.style.background = 'var(--glass-bg)';
    e.currentTarget.style.color = 'var(--text)';
  }}
>
  {tech.label}
</span>
```

Alternative: use CSS classes with `:hover` for cleaner code.

### 6. LiveServicesSection — Real-Time Service Cards

Fetches service list from API, renders as cards with status indicators. Running services get green border + pulse dot. Uses grid layout `repeat(auto-fill, minmax(220px, 1fr))`.

Status mapping:
- `running` → 🟢 green pulse dot, green tinted bg
- `error` → 🔴
- `stopped` → ⚪ dim

### 7. Scene3D — Lazy-Loaded Three.js Background

The Three.js scene (floating torus knot + particle field) is lazy-imported:

```jsx
const Scene3D = lazy(() => import('../components/Scene3D'));

// In JSX:
<Suspense fallback={null}>
  <Scene3D />
</Suspense>
```

Build output: `Scene3D-Cj4d7a4P.js` (~897KB, gzip 242KB) — separate chunk.

## Common Animation Patterns

| Effect | Implementation |
|--------|---------------|
| **Fade-up on scroll** | `motion.div` with `initial={{ opacity: 0, y: 20 }}`, `whileInView={{ opacity: 1, y: 0 }}`, `viewport={{ once: true }}` |
| **Stagger delay** | `transition={{ delay: 0.05 * index }}` — use array index multiplier |
| **Card hover lift** | `className="liquid-card card-hover"` — CSS handles hover translateY + shadow |
| **Scale on tap** | `whileTap={{ scale: 0.98 }}` on cards, `whileTap={{ scale: 0.97 }}` on buttons |
| **Rotating text** | `useState(index)` + `setInterval` + `AnimatePresence mode="wait"` |
| **Counter animation** | `AnimatedCounter` component with IntersectionObserver trigger |
| **Scroll indicator** | `motion.div` with `animate={{ y: [0, 6, 0] }}`, `transition={{ duration: 2, repeat: Infinity }}` |
| **hover accent toggle (inline)** | `onMouseEnter`/`onMouseLeave` handlers on `e.currentTarget.style` |

## CSS Dependencies

- `pulse-dot` keyframe in `components.css` (line 192)
- `.liquid-card`, `.liquid-btn`, `.liquid-stat` classes for glassmorphism
- `--accent`, `--text-dim`, `--glass-bg`, `--glass-border`, `--liquid-bg` CSS vars from `tokens.css`
- `--font-mono` for monospace text (Geist Mono)

## Build Notes

- Scene3D is 897KB minified (Three.js) — lazy-load to avoid blocking initial render
- Clean `frontend/index.html`: only Font Awesome CDN + `main.jsx` entry. No Bulma CDN, no `global.css` reference (React app imports its own styles in `main.jsx`)
- The `crossorigin` attribute on font preload links must be bare (`crossorigin` not `crossorigin=""`) or Vite build fails with HTML parse error
