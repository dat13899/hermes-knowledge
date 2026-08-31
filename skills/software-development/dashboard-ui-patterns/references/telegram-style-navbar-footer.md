# Telegram-Style Navbar + Footer Patterns (React 19)

Added July 2026 — React 19 inline-style patterns for btdat.io.vn based on Telegram app aesthetic.

## 1. Telegram-Style Navbar (Scroll Effect + Active Pill)

**Key features:**
- Transparent at top → blur+shadow+gradient border when scrolled
- `useScrollNav(threshold)` hook for scroll detection
- Animated logo: icon in gradient box with `logoPulse` keyframe
- Active pill indicator: gradient bar with `pillSlide` animation under nav links
- Icon scale-on-hover, text lift-up
- Hamburger: border accent khi mở, 3-line → X mượt
- Mobile menu: border-left accent cho item active

**useScrollNav hook:**
```js
import { useState, useEffect } from 'react';

export default function useScrollNav(threshold = 60) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > threshold);
    handler();
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, [threshold]);
  return scrolled;
}
```

**Dynamic navbar style pattern:**
```jsx
const scrolled = useScrollNav(60);
const navStyle = {
  background: scrolled ? 'var(--glass-bg)' : 'rgba(17,24,39,0.2)',
  backdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'blur(8px) saturate(100%)',
  WebkitBackdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'blur(8px) saturate(100%)',
  boxShadow: scrolled ? '0 4px 24px rgba(0,0,0,0.15)' : 'none',
  // Gradient border via background-clip trick:
  backgroundImage: scrolled ? `linear-gradient(var(--glass-bg), var(--glass-bg)), linear-gradient(90deg, transparent, var(--accent), ..., transparent)` : 'none',
  backgroundClip: scrolled ? 'padding-box, border-box' : 'padding-box',
  transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
};
```

**CSS keyframes needed:**
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

## 2. Telegram-Style Footer (Floating Pill)

**Desktop:** Floating pill ở góc phải dưới — status dot xanh + live clock + brand + Hermes link. Hover lift-up.

```jsx
<div style={{
  position: 'fixed', bottom: '1rem', right: '1rem',
  padding: '0.4rem 0.9rem', borderRadius: '999px',
  background: 'var(--glass-bg)',
  backdropFilter: 'blur(16px)',
  border: '1px solid var(--glass-border)',
  boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
  transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
}}
onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; }}
onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
>
  {/* Green status dot → live clock → divider → brand → Hermes link */}
</div>
```

Live clock via `useEffect` + `setInterval` every 30s:
```js
const [time, setTime] = useState('');
useEffect(() => {
  const tick = () => setTime(new Date().toLocaleTimeString('vi-VN', { hour:'2-digit', minute:'2-digit' }));
  tick();
  const id = setInterval(tick, 30000);
  return () => clearInterval(id);
}, []);
```

## 3. Telegram-Style Bottom Tab (Mobile)

**Pitfalls from experience:**
- Container: `borderRadius: '20px'`, `bottom: '0.5rem'`, `left/right: '0.5rem'` — floating with margin
- Badge notification dot: `position: 'absolute'`, `top: '2px'`, `right: '6px'`, 7px diameter, red with `badgePulse` animation
- Active = background tím nhạt + pill 2.5px dưới cùng + icon scale 1.1
- Must include `env(safe-area-inset-bottom, 0px)` in paddingBottom
- Main padding-bottom: 64px (giảm từ 72px vì tab floating có margin)
- Icon size: 1.25rem (to hơn trước)

```css
@keyframes badgePulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
```

## 4. DOCX → PDF conversion in DocReader (React)

When a document has `ext === 'docx'`, render via PDF iframe instead of marked.js:

```jsx
const isDocx = doc?.ext === 'docx' || (doc?.file || '').endsWith('.docx');
const pdfUrl = isDocx ? `/api/documents/${doc?.id}/pdf` : null;

// Trigger conversion on mount
useEffect(() => {
  if (isDocx) {
    setPdfLoading(true);
    fetch(pdfUrl).finally(() => setPdfLoading(false));
  }
}, [doc?.id, isDocx, pdfUrl]);

// Render PDF iframe or markdown HTML
{isDocx ? (
  <div style={s.pdfContainer}>
    {pdfLoading ? <Spinner /> : <iframe src={pdfUrl} style={s.pdfIframe} />}
  </div>
) : (
  <div dangerouslySetInnerHTML={{ __html: renderedHtml }} />
)}
```

Server endpoint: `GET /api/documents/:id/pdf` → LibreOffice convert docx → stream PDF.

## 5. React Prop Mismatch Debugging

**Pattern:** Component con được rewrite với API mới hoàn toàn, nhưng component cha vẫn truyền props cũ → `onSelectDoc = undefined` → click crash → ErrorBoundary.

**Debug flow:**
1. Compare component signature (props destructuring) vs call site
2. Check built bundle chunk for prop references
3. Fix: bridge old→new props in parent, or rewrite parent to match new API
4. Default values as band-aid (lazy), full integration as fix (proper)
