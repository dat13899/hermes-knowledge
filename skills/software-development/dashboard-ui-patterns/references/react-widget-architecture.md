# React Widget Page Architecture — July 2026

Port of the 28-widget vanilla-JS page (`random-widget.html`) to React 19 + Vite 6 + React Router 7 with lazy-loaded components.

## Architecture

```
frontend/src/pages/WidgetPage.jsx     ← Grid + detail modal
frontend/src/pages/widgets/
├── widgetData.js                     ← Metadata array (id, name, icon, desc, badge)
├── RandomDiscovery.jsx               ← fetch /api/utilities/random?type=any
├── DiceRoller.jsx                    ← d4/d6/d8/d10/d12/d20/d100 with animation
├── CoinFlip.jsx                      ← Heads/tails with running counter
├── NumberGen.jsx                     ← min-max range, count, stats
├── PasswordGen.jsx                   ← Options, strength meter, copy
├── ColorPalette.jsx                  ← HSL golden ratio, harmony modes
├── GradientGen.jsx                   ← Direction picker, copy CSS
├── ActivitySuggester.jsx             ← 35 activities, dedup-guard
├── Magic8Ball.jsx                    ← 20 answers, question history
├── BrainDump.jsx                     ← Sticky notes, drag, localStorage
└── MiniGames.jsx                     ← Dice + coin + number combined
```

## Widget Registry Pattern (React)

Instead of the vanilla-JS hash-based routing + WIDGETS array + manual init calls in `showDetail()`, React uses:

### 1. Import registry

```jsx
import RandomDiscovery from './widgets/RandomDiscovery';
import DiceRoller from './widgets/DiceRoller';
// ... all 11 widgets

const WIDGET_COMPONENTS = {
  random: RandomDiscovery,
  dice: DiceRoller,
  coin: CoinFlip,
  number: NumberGen,
  password: PasswordGen,
  palette: ColorPalette,
  gradient: GradientGen,
  activity: ActivitySuggester,
  '8ball': Magic8Ball,
  braindump: BrainDump,
  games: MiniGames,
};
```

### 2. Dynamic rendering

```jsx
const SelectedComponent = selectedId ? WIDGET_COMPONENTS[selectedId] : null;

// In JSX:
{selectedWidget && SelectedComponent && (
  <div className="modal-overlay" onClick={handleOverlayClick}>
    <div className="detail-card">
      <div className="detail-header">
        <button onClick={() => setSelectedId(null)}>←</button>
        <span>{selectedWidget.icon}</span>
        <div className="detail-title">{selectedWidget.name}</div>
      </div>
      <div className="detail-body">
        <SelectedComponent />
      </div>
    </div>
  </div>
)}
```

### 3. Filtering

```jsx
const filtered = useMemo(() => {
  if (!search.trim()) return widgets;
  const q = search.toLowerCase();
  return widgets.filter(w =>
    w.name.toLowerCase().includes(q) ||
    w.desc.toLowerCase().includes(q)
  );
}, [search]);
```

## Glassmorphism with Inline Styles (no CSS modules)

Each widget uses a local `S` style object with CSS custom properties:

```jsx
const S = {
  container: { textAlign: 'center', padding: '1.5rem 1rem' },
  genBtn: {
    padding: '0.6rem 2rem', borderRadius: 'var(--radius-sm)', border: 'none',
    background: 'var(--accent)', color: '#fff', fontSize: '0.9rem',
    fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s',
  },
};
```

CSS vars used consistently: `--glass-bg`, `--glass-border`, `--surface-2`, `--text`, `--text-dim`, `--text-strong`, `--accent`, `--radius-sm`, `--radius-md`, `--radius-lg`.

Colors: `#ef4444` (red), `#22c55e` (green), `#f59e0b` (yellow), `#818cf8` (purple).

## Card Colors (per-widget tint)

```jsx
const cardColors = [
  { bg: 'rgba(99,102,241,0.08)', border: 'rgba(99,102,241,0.2)', accent: '#818cf8' },
  { bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)', accent: '#22c55e' },
  { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)', accent: '#ef4444' },
  { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', accent: '#f59e0b' },
  { bg: 'rgba(168,85,247,0.08)', border: 'rgba(168,85,247,0.2)', accent: '#a855f7' },
  { bg: 'rgba(14,165,233,0.08)', border: 'rgba(14,165,233,0.2)', accent: '#0ea5e9' },
  { bg: 'rgba(236,72,153,0.08)', border: 'rgba(236,72,153,0.2)', accent: '#ec4899' },
  { bg: 'rgba(20,184,166,0.08)', border: 'rgba(20,184,166,0.2)', accent: '#14b8a6' },
];
```

Cycled by index: `const selectedIdx = widgets.findIndex(w => w.id === selectedWidget.id) % cardColors.length`.

## Toast Hook Usage

All widgets import and use the shared toast context:

```jsx
import { useToast } from '../../hooks/useToast';

export default function PasswordGen() {
  const toast = useToast();
  // ...
  toast('Đã copy mật khẩu', 'success');
}
```

## Key Component Patterns

### RandomDiscovery (API fetch)
- `fetch('/api/utilities/random?type=any')`
- Loading state via `setLoading(true)` / `setLoading(false)`
- Error state via `setError(message)`
- Renders thumbnail, title, source, extract, link

### DiceRoller (rolling animation)
- Interval-based animation: rapid random values for 10 ticks
- History stored in state, sliced to last 20 entries
- Dice faces represented as pure numbers (no Unicode faces)

### CoinFlip (rotating animation)
- `transform: 'rotateY(720deg)'` via state for visual flip
- Tracks heads/tails count as counters
- History shown as colored H/T beads in a row

### NumberGen (range + count)
- Input fields for min, max, count
- Multiple results shown with aggregate stats (min, max, sum, avg)
- Count capped at 100 with safety clamp

### PasswordGen (options + strength)
- Four toggle buttons for character types (upper/lower/digits/symbols)
- Ambiguous character exclusion toggle (O0Il1)
- Strength scoring function with color-coded bar
- Copy-to-clipboard with toast feedback

### ColorPalette (HSL harmony)
- Three harmony modes: random, mono (luminance-based), complement (invert RGB)
- Slider for palette size (3-10)
- Click-to-copy hex values via clipboard API

### GradientGen (CSS generator)
- Direction buttons as visual arrow indicators
- Random HSL color generation for vibrant gradients
- Preview pane + CSS code block with copy button

### ActivitySuggester (35-item pool)
- Large embedded array of activities with emoji + description
- Dedup guard via direct random (no consecutive-pick guard needed since pool is large enough)
- Tag display showing pool size

### Magic8Ball (question input + shake)
- Text input + Enter key handler
- Animated ball rotation on shake (800ms)
- 20 classic answers in Vietnamese
- History log of recent questions + answers (last 10)

### BrainDump (canvas + drag)
- Click on canvas background (guard against clicks on notes) to add
- Drag via mousedown/mousemove/mouseup with offset tracking
- Position clamped to canvas bounds (0 to width-200px, 0 to height-120px)
- Textarea inside each note for content
- Persist to localStorage as JSON array
- Clear all button with toast confirmation

### MiniGames (combined tab)
- Three sub-widgets in one component: dice (selectable sides), coin (heads/tails counter), number (range)
- Each has its own state, independent history
- Compact layout inside a single glass panel section

## Build Verification

```bash
cd frontend && npx vite build
```

Expected output: each widget as a separate chunk in `dist/assets/`:

```
dist/assets/DiceRoller-*.js       2.5 kB
dist/assets/RandomDiscovery-*.js  2.5 kB
dist/assets/CoinFlip-*.js         3.1 kB
dist/assets/ColorPalette-*.js     3.2 kB
dist/assets/GradientGen-*.js      3.3 kB
dist/assets/NumberGen-*.js        3.4 kB
dist/assets/Magic8Ball-*.js       3.5 kB
dist/assets/MiniGames-*.js        4.0 kB
dist/assets/ActivitySuggester-*.js 4.1 kB
dist/assets/PasswordGen-*.js      4.2 kB
dist/assets/BrainDump-*.js        4.6 kB
```

## Pitfalls

- **Don't use CSS modules** — all inline styles. The existing project has no CSS module setup and uses CSS custom properties via `style={{}}`.
- **Modal overlay click-away** — check `e.target === e.currentTarget` to close detail view only when clicking the backdrop, not the card.
- **`e.stopPropagation()` on inputs** — textareas and inputs inside draggable/detail cards must stop propagation so clicks don't bubble to drag/modal-close handlers.
- **React reflow for CSS animation restart** — vanilla JS uses `void el.offsetWidth` to force reflow. In React, toggle a key or use `requestAnimationFrame` + state reset instead.
- **BrainDump drag ref** — use `useRef` for the drag state object, not useState (frequent position updates during drag shouldn't cause re-renders of sibling components).
- **`localStorage` in useEffect** — load on mount (`useEffect(() => setNotes(loadNotes()), [])`), save on change (`useEffect(() => saveNotes(notes), [notes])`).
- **Build fails silently in git-bash** — `npx vite build` in foreground may be detected as a long-running process. Use `background=true` + `notify_on_complete=true` or pipe to a file.
- **Export `widgetData` as default** — not named export. Import: `import widgets from './widgets/widgetData'`.
