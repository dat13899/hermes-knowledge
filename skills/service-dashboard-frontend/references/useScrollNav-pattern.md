# useScrollNav hook — reusable scroll-effect pattern

Hook theo dõi scroll position để trigger UI changes (navbar opacity, shadow, blur intensity).

## Code

```js
// frontend/src/hooks/useScrollNav.js
import { useState, useEffect } from 'react';

export default function useScrollNav(threshold = 60) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > threshold);
    handler(); // init
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, [threshold]);

  return scrolled;
}
```

## Usage in Navbar

```jsx
import useScrollNav from '../../hooks/useScrollNav';

const scrolled = useScrollNav(60);

const navStyle = {
  position: 'fixed', top: 0, left: 0, right: 0,
  zIndex: 500, height: '56px',
  background: scrolled ? 'var(--glass-bg)' : 'rgba(17,24,39,0.2)',
  backdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'blur(8px) saturate(100%)',
  boxShadow: scrolled ? '0 4px 24px rgba(0,0,0,0.15)' : 'none',
  // Gradient border via backgroundImage trick (inline style, no pseudo-element)
  backgroundImage: scrolled
    ? `linear-gradient(var(--glass-bg), var(--glass-bg)), 
       linear-gradient(90deg, transparent, var(--accent), #06b6d4, #a855f7, transparent)`
    : 'none',
  backgroundOrigin: 'border-box',
  backgroundClip: scrolled ? 'padding-box, border-box' : 'padding-box',
  transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
};
```

## Key CSS keyframes (go in components.css)

```css
@keyframes logoPulse {
  0%, 100% { box-shadow: 0 0 12px rgba(129,140,248,0.35); }
  50% { box-shadow: 0 0 24px rgba(129,140,248,0.55); }
}

@keyframes pillSlide {
  from { opacity: 0; transform: translateX(-50%) scaleX(0); }
  to { opacity: 1; transform: translateX(-50%) scaleX(1); }
}
```
