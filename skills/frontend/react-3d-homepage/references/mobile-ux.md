# Mobile UX Reference — Components & Hooks

> Concrete code from the "nâng cấp trải nghiệm ui/ux mobile" session on btdat.io.vn.
> Copy-paste ready. Lib: `@use-gesture/react`, `motion`.

---

## 1. useHaptic.js

```js
export function useHaptic() {
  const canVibrate = typeof navigator !== 'undefined' && 'vibrate' in navigator;
  const vibrate = (pattern) => { if (canVibrate) try { navigator.vibrate(pattern); } catch {} };
  return {
    light: () => vibrate(10),
    medium: () => vibrate(20),
    heavy: () => vibrate(40),
    success: () => vibrate([10, 50, 20]),
    error: () => vibrate([30, 50, 30, 50, 50]),
    warning: () => vibrate([20, 80, 40]),
    selection: () => vibrate(15),
  };
}
```

---

## 2. useSwipeBack.js

Edge-swipe right → go back. Only from left 30px, not on homepage.

```js
import { useCallback, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export function useSwipeBack({ enabled = true, threshold = 80, edgeWidth = 30 } = {}) {
  const navigate = useNavigate();
  const location = useLocation();
  const startX = useRef(0), startY = useRef(0), currentX = useRef(0);
  const swiping = useRef(false);
  const indicatorRef = useRef(null);

  const handleTouchStart = useCallback((e) => {
    const touch = e.touches[0];
    if (touch.clientX > edgeWidth || location.pathname === '/') return;
    startX.current = touch.clientX; startY.current = touch.clientY;
    swiping.current = true;
  }, [edgeWidth, location.pathname]);

  const handleTouchMove = useCallback((e) => {
    if (!swiping.current) return;
    const touch = e.touches[0];
    currentX.current = touch.clientX - startX.current;
    if (Math.abs(touch.clientY - startY.current) > Math.abs(currentX.current) * 1.5) {
      swiping.current = false; return;
    }
    if (currentX.current > 0 && indicatorRef.current) {
      const p = Math.min(currentX.current / threshold, 1);
      indicatorRef.current.style.opacity = p;
      indicatorRef.current.style.transform = `translateY(-50%) translateX(${Math.min(currentX.current - 16, 40)}px)`;
    }
  }, [threshold]);

  const handleTouchEnd = useCallback(() => {
    if (!swiping.current) return; swiping.current = false;
    if (currentX.current > threshold) navigate(-1);
    if (indicatorRef.current) {
      indicatorRef.current.style.opacity = '0';
      indicatorRef.current.style.transform = 'translateY(-50%) translateX(-16px)';
    }
    currentX.current = 0;
  }, [navigate, threshold]);

  useEffect(() => {
    if (!enabled || location.pathname === '/') return;
    const el = document.createElement('div');
    el.style.cssText = `position:fixed;left:0;top:50%;transform:translateY(-50%) translateX(-16px);width:36px;height:36px;border-radius:50%;background:var(--glass-bg);backdrop-filter:blur(8px);border:1px solid var(--glass-border);display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:1rem;opacity:0;z-index:600;pointer-events:none;transition:opacity .15s`;
    el.textContent = '←';
    document.body.appendChild(el);
    indicatorRef.current = el;
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('touchend', handleTouchEnd);
    return () => { el.remove(); document.removeEventListener('touchstart', handleTouchStart); document.removeEventListener('touchmove', handleTouchMove); document.removeEventListener('touchend', handleTouchEnd); };
  }, [enabled, location.pathname]);
  return { isSupported: true };
}
```

---

## 3. BottomSheet.jsx

Two modes: `list` (action sheet with cancel) and `content` (custom children).

```jsx
import { useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';

export default function BottomSheet({ open, onClose, title, children, mode = 'list', actions = [], cancelLabel = 'Cancel' }) {
  const sheetRef = useRef(null);
  const startY = useRef(0), currentY = useRef(0), dragging = useRef(false);

  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const handleTouchStart = useCallback((e) => { dragging.current = true; startY.current = e.touches[0].clientY; }, []);
  const handleTouchMove = useCallback((e) => {
    if (!dragging.current) return;
    currentY.current = e.touches[0].clientY - startY.current;
    if (currentY.current > 0 && sheetRef.current)
      sheetRef.current.style.transform = `translateY(${currentY.current}px)`;
  }, []);
  const handleTouchEnd = useCallback(() => {
    dragging.current = false;
    if (currentY.current > 100) onClose();
    if (sheetRef.current) sheetRef.current.style.transform = '';
    currentY.current = 0;
  }, [onClose]);

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div variants={{ initial:{opacity:0}, animate:{opacity:1}, exit:{opacity:0} }}
        initial="initial" animate="animate" exit="exit" onClick={onClose}
        style={{ position:'fixed',inset:0,zIndex:2000,background:'rgba(0,0,0,0.5)',backdropFilter:'blur(4px)',display:'flex',alignItems:'flex-end',justifyContent:'center' }}>
        <motion.div ref={sheetRef}
          variants={{ initial:{y:'100%'}, animate:{y:0,transition:{type:'spring',damping:28,stiffness:360}}, exit:{y:'100%',transition:{duration:.2,ease:'easeIn'}} }}
          initial="initial" animate="animate" exit="exit" onClick={e => e.stopPropagation()}
          style={{ width:'100%',maxWidth:500,background:'var(--surface)',borderRadius:'20px 20px 0 0',paddingBottom:'env(safe-area-inset-bottom,0px)',maxHeight:'80vh',overflowY:'auto',boxShadow:'0 -4px 30px rgba(0,0,0,0.3)' }}>
          {/* Drag handle */}
          <div style={{ padding:'.75rem',display:'flex',justifyContent:'center',touchAction:'none' }}
            onTouchStart={handleTouchStart} onTouchMove={handleTouchMove} onTouchEnd={handleTouchEnd}>
            <div style={{ width:36,height:4,background:'var(--text-dim)',opacity:.4,borderRadius:'999px' }} />
          </div>
          {title && <h3 style={{ textAlign:'center',fontSize:'.95rem',fontWeight:700,color:'var(--text-strong)',padding:'0 1rem .5rem' }}>{title}</h3>}
          {mode === 'list' ? (
            <div style={{ padding:'.5rem 1rem' }}>
              <div style={{ display:'flex',flexDirection:'column',gap:'.5rem' }}>
                {actions.map((a,i) => (
                  <button key={i} onClick={() => { a.onClick?.(); if(a.close!==false) onClose(); }}
                    style={{ display:'flex',alignItems:'center',gap:'.75rem',padding:'.85rem 1rem',background:'var(--surface-2)',border:'none',borderRadius:'14px',color:a.danger?'var(--red)':'var(--text)',fontSize:'.95rem',fontWeight:500,cursor:'pointer',textAlign:'left',width:'100%',minHeight:48 }}>
                    {a.icon && <i className={a.icon} style={{ fontSize:'1.1rem',width:24,textAlign:'center',color:a.danger?'var(--red)':'var(--text-dim)' }} />}
                    <span>{a.label}</span>
                  </button>
                ))}
              </div>
              <button onClick={onClose} style={{ width:'100%',marginTop:'.75rem',marginBottom:'1rem',padding:'.85rem',background:'var(--surface-2)',border:'none',borderRadius:'14px',color:'var(--text-dim)',fontSize:'.95rem',fontWeight:600,cursor:'pointer',minHeight:48 }}>{cancelLabel}</button>
            </div>
          ) : <div style={{ padding:'1rem' }}>{children}</div>}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

---

## 4. BottomTab.jsx (upgraded)

Pill animation + haptic + spring icons.

```jsx
import { useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'motion/react';
import { useHaptic } from '../../hooks/useHaptic';

const TABS = [
  { to: '/', icon: 'fa-house', label: 'Home' },
  { to: '/dashboard', icon: 'fa-gauge-high', label: 'Dashboard' },
  { to: '/documents', icon: 'fa-file-lines', label: 'Docs' },
  { to: '/widgets', icon: 'fa-cubes', label: 'Widget' },
  { to: '/utilities', icon: 'fa-toolbox', label: 'Tools' },
];

export default function BottomTab() {
  const location = useLocation();
  const haptic = useHaptic();
  const handleTap = useCallback(() => haptic.light(), [haptic]);
  const activeIndex = TABS.findIndex(t => t.to === location.pathname);

  return (
    <nav style={{ position:'fixed',bottom:0,left:0,right:0,zIndex:'var(--z-bottom-nav)',background:'var(--glass-bg)',backdropFilter:'blur(28px) saturate(200%)',borderTop:'1px solid var(--glass-border)',display:'flex',justifyContent:'space-around',alignItems:'center',padding:'.3rem .25rem',paddingBottom:'var(--safe-bottom)',boxShadow:'0 -1px 20px rgba(0,0,0,0.15)' }}>
      {/* Animated pill background */}
      <div style={{ position:'absolute',top:4,height:'calc(100% - 8px - var(--safe-bottom))',width:`${100/TABS.length}%`,transform:`translateX(${activeIndex*100}%)`,transition:'transform .3s cubic-bezier(.4,0,.2,1)',display:'flex',justifyContent:'center',alignItems:'center',pointerEvents:'none' }}>
        <div style={{ width:'calc(100% - 16px)',height:'100%',background:'rgba(0,212,255,0.08)',borderRadius:'16px' }} />
      </div>
      {TABS.map((tab,i) => {
        const active = i === activeIndex;
        return (
          <Link key={tab.to} to={tab.to} onClick={handleTap}
            style={{ display:'flex',flexDirection:'column',alignItems:'center',gap:'2px',padding:'.3rem .4rem',minWidth:56,minHeight:48,justifyContent:'center',color:active?'var(--accent)':'var(--text-dim)',textDecoration:'none',position:'relative',zIndex:1,WebkitTapHighlightColor:'transparent',transition:'color .2s' }}>
            <motion.i className={`fas ${tab.icon}`} animate={{ scale: active?1.15:1 }} transition={{ type:'spring',stiffness:400,damping:18 }} style={{ fontSize:'1.35rem',lineHeight:1 }} />
            <motion.span animate={{ opacity: active?1:.65, fontWeight: active?600:400 }} style={{ fontSize:'.58rem',letterSpacing:'.02em',lineHeight:1 }}>{tab.label}</motion.span>
            {active && <motion.div layoutId="bottom-tab-dot" style={{ width:4,height:4,borderRadius:'50%',background:'var(--accent)',position:'absolute',bottom:'-2px' }} transition={{ type:'spring',stiffness:500,damping:30 }} />}
          </Link>
        );
      })}
    </nav>
  );
}
```

---

## 5. AppLayout.jsx (mobile integration)

Key changes from desktop-only: conditional rendering of Navbar/Footer/Blob/Cursor, swipe-back hook, mobile Lenis settings.

```jsx
import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'motion/react';
import Navbar from './Navbar';
import Footer from './Footer';
import BottomTab from './BottomTab';
import BlobBackground from '../shared/BlobBackground';
import Cursor from '../Cursor';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useSwipeBack } from '../../hooks/useSwipeBack';

export default function AppLayout() {
  const { isMobile } = useMediaQuery();
  const location = useLocation();
  useSwipeBack({ enabled: isMobile });

  useEffect(() => {
    let lenis;
    import('lenis').then(mod => {
      lenis = new mod.default({
        lerp: isMobile ? 0.08 : 0.065,
        wheelMultiplier: 1,
        smoothWheel: !isMobile,
        syncTouch: true,
        gestureOrientation: 'vertical',
      });
      const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
    });
    return () => lenis?.destroy();
  }, [isMobile]);

  return (
    <>
      {!isMobile && <Cursor />}
      <div className="noise-overlay" />
      {!isMobile && <BlobBackground />}
      {!isMobile && <Navbar />}
      <main style={{ paddingTop: isMobile?0:'56px', paddingBottom: isMobile?'var(--bottom-nav-height)':0, minHeight:'100dvh', display:'flex',flexDirection:'column' }}>
        <AnimatePresence mode="wait">
          <motion.div key={location.pathname}
            variants={{ initial:{opacity:0,y:isMobile?20:12}, animate:{opacity:1,y:0,transition:{duration:.3,ease:[.25,.46,.45,.94]}}, exit:{opacity:0,y:isMobile?-10:-8,transition:{duration:.15,ease:'easeIn'}} }}
            initial="initial" animate="animate" exit="exit" style={{ flex:1 }}>
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
      {isMobile && <BottomTab />}
      {!isMobile && <Footer />}
    </>
  );
}
```

---

## 6. CSS Tokens (mobile additions)

```css
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --safe-left: env(safe-area-inset-left, 0px);
  --safe-right: env(safe-area-inset-right, 0px);
  --bottom-nav-height: calc(60px + var(--safe-bottom));
  --navbar-height: 56px;
  --tap-target-min: 44px;
  --z-bottom-nav: 800;
}
```

```css
.pb-safe { padding-bottom: var(--bottom-nav-height); }
.tap-target { min-height: var(--tap-target-min); min-width: var(--tap-target-min); }

@media (max-width: 767px) {
  input, textarea, select { font-size: 16px !important; } /* prevent iOS zoom */
}
```

---

## 7. PWA manifest.json

```json
{
  "name": "btdat.io.vn",
  "short_name": "btdat",
  "description": "Home lab dashboard — AI agent, Minecraft, service monitoring",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0e17",
  "theme_color": "#00d4ff",
  "icons": [
    { "src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

HTML additions:
```html
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0e17">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="btdat">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
<link rel="manifest" href="/manifest.json">
```

---

## 8. Install

```bash
npm install @use-gesture/react
```

Library list for mobile UX: `@use-gesture/react`, `motion` (already in stack), `lenis` (already in stack).
