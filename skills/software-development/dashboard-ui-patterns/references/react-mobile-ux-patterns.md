# React Mobile UX Patterns — btdat.io.vn

> Touch-first interactions for React 19 + Vite. CSS + lightweight hooks.  
> No heavy libraries. Proven effective: user F5 on mobile → immediate difference.

## Lesson: font/color changes are invisible; touch interactions create real impact.

---

## 1. Touch Ripple (global)

CSS in `mobile-ux.css`, global handler in `AppLayout.jsx`:

```jsx
// In AppLayout — renders once, covers all .btn, .card, [role="button"], a[href]
useEffect(() => {
  const handler = (e) => {
    const el = e.target.closest('.btn, .card, [role="button"], a[href]');
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = (e.touches?.[0]?.clientX ?? e.clientX) - rect.left - size / 2;
    const y = (e.touches?.[0]?.clientY ?? e.clientY) - rect.top - size / 2;
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`; ripple.style.top = `${y}px`;
    el.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  };
  document.addEventListener('click', handler);
  document.addEventListener('touchstart', handler, { passive: true });
  return () => { /* cleanup both listeners */ };
}, []);
```

**Requirements:**
- All `.btn` CSS must have `overflow: hidden; position: relative; -webkit-tap-highlight-color: transparent;`
- `@keyframes rippleAnim { to { transform: scale(4); opacity: 0; } }`
- Ripple color: `rgba(255,255,255,0.3)` for dark theme

---

## 2. Skeleton Loading (Telegram-style shimmer)

```css
.skeleton {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface) 50%, var(--surface-2) 75%);
  background-size: 200% 100%;
  animation: skeletonShimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}
@keyframes skeletonShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

Usage:
```jsx
{loading ? (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
    {['60%','80%','40%'].map((w,i) => (
      <div key={i} className="skeleton skeleton-card" style={{ width: w }} />
    ))}
  </div>
) : (
  /* actual content */
)}
```

---

## 3. Pull-to-Refresh Hook

```js
import { useState, useRef, useCallback } from 'react';

export function usePullToRefresh(onRefresh) {
  const [refreshing, setRefreshing] = useState(false);
  const [pullState, setPullState] = useState('idle');
  const startY = useRef(0);

  const handleTouchStart = (e) => {
    if (el.scrollTop <= 0) startY.current = e.touches[0].clientY;
  };
  const handleTouchMove = (e) => {
    const delta = e.touches[0].clientY - startY.current;
    setPullState(delta > 50 ? 'ready' : delta > 10 ? 'pulling' : 'idle');
  };
  const handleTouchEnd = async () => {
    startY.current = 0;
    if (pullState === 'ready' && !refreshing) {
      setRefreshing(true); setPullState('refreshing');
      await onRefresh();
      setRefreshing(false); setPullState('idle');
    } else { setPullState('idle'); }
  };

  return {
    refreshing,
    indicatorStyle: { pulling: 'pulling', ready: 'pulling', refreshing: 'refreshing', idle: '' }[pullState],
    listeners: { onTouchStart, onTouchMove, onTouchEnd },
  };
}
```

---

## 4. Swipe-to-Dismiss Hook

```js
export function useSwipe({ onSwipeLeft, onSwipeRight, threshold = 80 }) {
  const startX = useRef(0); const currentX = useRef(0);
  const [swiping, setSwiping] = useState(false);
  const [swipeDir, setSwipeDir] = useState(null);

  const handleTouchStart = (e) => { startX.current = e.touches[0].clientX; setSwiping(true); };
  const handleTouchMove = (e) => {
    currentX.current = e.touches[0].clientX - startX.current;
    if (Math.abs(currentX.current) > 10)
      setSwipeDir(currentX.current > 0 ? 'right' : 'left');
  };
  const handleTouchEnd = () => {
    if (Math.abs(currentX.current) > threshold)
      currentX.current > 0 ? onSwipeRight?.() : onSwipeLeft?.();
    setSwiping(false); setSwipeDir(null); currentX.current = 0;
  };

  return {
    handlers: { onTouchStart, onTouchMove, onTouchEnd },
    style: swiping ? { transform: `translateX(${currentX.current}px) rotate(${currentX.current * 0.03}deg)` } : {},
    activeAction: swipeDir === 'left' ? 'right' : swipeDir === 'right' ? 'left' : null,
  };
}
```

---

## File locations in project

```
frontend/src/
  hooks/
    useRipple.js          — per-component ripple (if needed; global handler usually enough)
    usePullToRefresh.js   — pull-to-refresh
    useSwipe.js           — swipe-to-dismiss
  styles/
    mobile-ux.css         — ripple, skeleton, ptr, swipe CSS
  components/layout/
    AppLayout.jsx         — global ripple handler (useEffect)
```

---

## Anti-patterns

- ❌ Installing Framer Motion or react-spring for touch effects
- ❌ Pure CSS `:active` pseudo for touch (no visual feedback)
- ❌ Forgetting `touch-action: pan-y` on swipe containers
- ❌ Skeleton without `overflow: hidden` (shimmer bleeds)
- ❌ Not clearing touch listeners in useEffect cleanup
