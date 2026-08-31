---
name: react-3d-homepage
description: "Xây dựng homepage React 19 + Vite với 3D background (@react-three/fiber), cinematic scroll (lenis), motion animations, và terminal contact. Dùng khi user muốn đập đi xây lại trang chủ theo hướng hiện đại, công nghệ, AI."
trigger:
  - "đập đi xây lại trang chủ"
  - "làm lại homepage cho xịn"
  - "3D homepage"
  - "cinematic landing page"
  - "command center"
version: "1.0"
---

# React 3D Homepage — "Command Center" Pattern

> Triển khai trang chủ single-page narrative scroll với Three.js background, smooth scroll, và staggered animations.

## Khi nào dùng

User nói: "đập đi xây lại", "xịn xò", "hiện đại", "công nghệ AI", "đủ wow", "nhìn choáng", "ko cần giữ logic cũ". Họ muốn bỏ code cũ hoàn toàn, build từ đầu.

## Stack

| Package | Role | Size |
|---------|------|------|
| `three` + `@react-three/fiber` + `@react-three/drei` | WebGL 3D background | ~190KB |
| `motion` (Framer Motion) | Stagger, page transitions, scroll-linked | ~30KB |
| `lenis` | Smooth scroll lerp | ~3KB |
| `canvas-confetti` | Pháo giấy CTA | ~2KB |

Không ngại bundle size — user đã yêu cầu xịn.

## Kiến trúc

### 5 Sections Narrative Scroll

1. **Cinematic Hero** — Title stagger từng chữ + shimmer gradient + 3D torus/particle background + scroll indicator
2. **Stats Dashboard** — 4 metric cards glassmorphism, số real-time từ API
3. **Neural Nodes** — Services hiển thị như nodes mạng AI, pulse ring cho running, SVG connection lines
4. **AI Features** — Card grid với gradient accent line + tag pills
5. **Terminal Contact** — Fake SSH terminal, gõ từng lệnh sequential, output tương tác

### Scene3D Component

```jsx
// Fixed background canvas — không block click
<div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 0, pointerEvents: 'none' }}>
  <Canvas camera={{ position: [0, 0, 5], fov: 60 }} dpr={[1, 1.5]}>
    <ambientLight intensity={0.3} />
    <FloatingTorus /> {/* torusKnotGeometry + MeshDistortMaterial wireframe */}
    <Icosahedron />   {/* wireframe + emissive glow */}
    <ParticleField count={500} /> {/* instanced Float32Array positions */}
  </Canvas>
</div>
```

**Performance:**
- `dpr={[1, 1.5]}` — tránh retina 2x render
- Particle count ≤ 500, instanced (không individual meshes)
- `Float` wrapper từ drei cho animation mượt (GPU accelerated)
- `pointer-events: none` — tất cả click xuyên qua, không block UI

### Staggered Title Pattern

```jsx
'BT DAT'.split('').map((ch, i) => (
  <motion.span
    initial={{ opacity: 0, y: 60, rotateX: 90 }}
    animate={{ opacity: 1, y: 0, rotateX: 0 }}
    transition={{ delay: 0.2 + i * 0.06, duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
    style={{
      background: 'linear-gradient(135deg, #fff 20%, var(--accent) 50%, #fff 80%)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      backgroundSize: '200% auto',
      animation: 'shimmer 3s ease-in-out infinite',
    }}
  >{ch === ' ' ? '\u00A0' : ch}</motion.span>
))
```

CSS:
```css
@keyframes shimmer {
  0% { background-position: 200% center; }
  100% { background-position: -200% center; }
}
```

### Terminal Contact Pattern

State machine sequential: `COMMANDS[n]` → type từng char setTimeout → pause 300ms → hiện output → pause 500ms → advance. Khi xong hết command → render contact buttons (GitHub, Email, Telegram). Dùng `font-family: var(--font-mono)`, title bar macOS buttons (đỏ/vàng/xanh), `backdrop-filter: blur(12px)`.

### Neural Nodes Pattern

- Grid `repeat(auto-fit, minmax(200px, 1fr))`
- Running services: `background: rgba(34,197,94,0.08)` + pulse ring CSS animation `aiPulse`
- Stopped: `rgba(107,114,128,0.06)`
- SVG overlay với `<line>` elements tạo connection network (opacity 0.08)
- Health bar: CPU % với width transition 0.5s

## Quy trình

**Theme:** Current accent is Cyber Cyan: `#00d4ff` (primary), `#00a8e0` (hover), `#0080b0` (deep), `#66e0ff` (light). User chose over Emerald and Violet for tech/AI vibe. Theme swap: sed replace all hex codes across 9 files → build → deploy.

1. Cài packages: `npm install three @react-three/fiber @react-three/drei`
2. Lenis đã có sẵn — dùng `useEffect` + dynamic `import('lenis')`
3. Tạo `Scene3D.jsx` + `NeuralNodes.jsx` + `TerminalContact.jsx`
4. Viết lại `HomePage.jsx` từ đầu — tất cả sections inline, không import file section riêng
5. **Xóa file cũ:** `rm -f pages/home/*.jsx` + xóa components không dùng (GlitchText, WireframeSphere, AIBadge, Magnetic)
6. Build → kill old server → restart → curl verify local + CDN → commit + push

## Mobile UX — bottom tab bar + gestures

> Xem `references/mobile-ux.md` để copy-paste các component đầy đủ.

### Kiến trúc mobile

Trên mobile (`< 768px`), layout lật ngược:
- **Ẩn** Navbar top desktop, BlobBackground, Cursor, Footer
- **Hiện** BottomTab fixed bottom, swipe-back gesture, touch ripple
- **3D Scene giảm mạnh**: `dpr={[1,1]}`, 120 particles (↓70% so với 400), single torus

Dùng `useMediaQuery` hook có sẵn: `{ isMobile, isTablet, isDesktop }`.

```jsx
const { isMobile } = useMediaQuery();
```

### BottomTab — iOS-style pill bar

```jsx
// Active pill trượt CSS translateX theo activeIndex
// Haptic feedback mỗi lần tap: haptic.light()
// Spring bounce icon khi active
// Fixed bottom, safe-area-aware: paddingBottom: 'var(--safe-bottom)'
```

### Swipe-back

Hook `useSwipeBack` trong `AppLayout`:
- Chỉ kích hoạt từ left edge 30px
- Không swipe trên homepage (pathname === '/')
- Threshold 80px → `navigate(-1)`
- Visual indicator (← icon) fade-in theo progress

### BottomSheet

Component `BottomSheet.jsx`:
- `mode='list'`: action sheet với cancel button
- `mode='content'`: custom children
- Drag-to-dismiss: touchstart/move/end handlers, dismiss if deltaY > 100px
- Motion spring animation slide-up
- `backdrop-filter: blur(4px)` overlay, tap outside = close

### Haptic feedback

Hook `useHaptic` — wrapper `navigator.vibrate`:
- `light()` = 10ms, `medium()` = 20ms, `heavy()` = 40ms
- `success()` = [10, 50, 20], `error()` = [30, 50, 30, 50, 50]
- Safe fallback nếu browser không hỗ trợ

### CSS safe-area + mobile tokens

Thêm vào `tokens.css`:
```css
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --bottom-nav-height: calc(60px + var(--safe-bottom));
  --tap-target-min: 44px;
}
```

Thêm vào `utilities.css`:
```css
.pb-safe { padding-bottom: var(--bottom-nav-height); }
.tap-target { min-height: var(--tap-target-min); min-width: var(--tap-target-min); }

@media (max-width: 767px) {
  input, textarea, select { font-size: 16px !important; } /* ngăn iOS zoom */
}
```

### PWA setup

- `public/manifest.json` với `display: standalone`, theme-color `#00d4ff`
- Tạo icon 192×192 + 512×512 PNG (diamond đơn giản)
- Meta tags: `apple-mobile-web-app-capable`, `viewport-fit=cover`
- `<link rel="manifest" href="/manifest.json">`

### Scene3D mobile

```jsx
export default function Scene3D() {
  const { isMobile } = useMediaQuery();
  if (isMobile) {
    return (
      <Canvas dpr={[1, 1]} performance={{ min: 0.3 }}>
        <FloatingTorus opacity={0.06} scale={0.7} />
        <ParticleField count={120} />
      </Canvas>
    );
  }
  // Desktop: full scene
}
```

## Pitfalls

- **Lenis + React 19:** dùng `useEffect` với dynamic `import('lenis')`, KHÔNG dùng `<ReactLenis>` wrapper (conflict strict mode)
- **Canvas positioning:** `position: fixed` (không absolute) để 3D background theo scroll
- **`pointer-events: none`** trên Canvas — bắt buộc, nếu không tất cả click bị hứng
- **Delete old files:** khi user nói "ko giữ logic cũ", xóa sạch file cũ. Không keep "just in case"
- **Build warning:** HomePage chunk ~900KB (Three.js engine ~700KB) — bình thường, không cần fix
- **Không dùng `useInView` cho elements trong 3D canvas** — dùng `useFrame` hoặc `whileInView` trên wrapper
- **Mobile Lenis:** set `lerp: 0.08` trên mobile (desktop 0.065), `smoothWheel: false`, `gestureOrientation: 'vertical'` để tránh conflict với swipe-back
- **BottomTab z-index:** dùng `--z-bottom-nav: 800` (giữa nav và overlay), không dùng `--z-nav: 500` của top navbar
- **iOS input zoom:** bắt buộc set `font-size: 16px` trên tất cả input/textarea/select ở mobile — iOS tự zoom nếu font < 16px
- **Pull-to-refresh:** hook `usePullToRefresh` đã có sẵn trong codebase, dùng touch events thuần, không cần thư viện ngoài

## Tier 1 UX Enhancements (proven patterns)

After building the base homepage + dashboard, these upgrades deliver maximum visual impact for minimal effort. See `references/liquid-glass.md` for full CSS token reference.

### Command Palette (`Ctrl+K`)

Component at `components/CommandPalette.jsx` + hook `useCommandPalette()`. Liquid-glass overlay, fuzzy search across all routes, arrow-key nav, haptic feedback on selection. Integrate in `AppLayout` for global access.

### Toast Redesign

Replace solid-color toasts with `liquid-panel` + `AnimatePresence`. Each toast gets a color-coded icon circle + spring enter/exit. See current `Toast.jsx` in `components/shared/` for reference implementation.

### Animated Blob Background

3 drifting gradient blobs at `position: fixed; z-index: 0; pointer-events: none`. Desktop only. CSS: `filter: blur(80px); opacity: 0.12; animation: blobDrift 18-25s infinite`. See `mobile-ux.css` for full keyframes.

### Liquid Skeleton Loader

`.liquid-skeleton` class: `linear-gradient(110deg, ...)` shimmer animation 1.8s, `border: 1px solid var(--liquid-border)`. Shown during `navigation.state === 'loading'` in AppLayout.

### 404 Page

Liquid-card wrapper + SVG gradient `<text>` + spring scale animation + Ctrl+K hint.

### Pitfalls

- Blob backgrounds on mobile → disable entirely. Even with reduced opacity they eat GPU
- CommandPalette must close on `location.pathname` change (useEffect dependency)
- Toast must use `AnimatePresence` + `exit` animation; old pattern used CSS reverse animation which leaves ghost elements
- Skeleton loader must always have `border-radius: var(--radius-lg)` for consistency

## So sánh trước/sau rebuild

| Khía cạnh | Trước | Sau |
|-----------|-------|-----|
| Background | Grid CSS tĩnh | Three.js torus knots + 500 particles |
| Hero | Gradient text + typing | Stagger char với shimmer + 3D background |
| Services | Card grid phẳng | Neural nodes + pulse ring + connection lines |
| Contact | Form tĩnh | Fake SSH terminal typing |
| Scroll | Native | Lenis smooth (lerp 0.065) |
