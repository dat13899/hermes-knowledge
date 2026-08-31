# React Mobile Hamburger Navbar Pattern

Reusable glassmorphism navbar for React apps with responsive hamburger menu on mobile.

## Key features

- 6+ nav links with Font Awesome icons
- Desktop: horizontal bar, icons + labels
- Mobile (< 820px): hamburger button with animated X icon
- Overlay backdrop with slide-down panel
- Body scroll lock when menu open
- Touch-friendly padding (0.65rem 0.85rem)
- Active link indicator (● dot)
- Theme toggle button (dark/light)

## Component structure

```
Navbar.jsx
├── useState(menuOpen)
├── useEffect to toggle body.menu-open class
├── Desktop navbar
│   ├── Brand link (btdat.io.vn)
│   ├── .desktop-nav with NAV_LINKS (display:flex)
│   └── Theme toggle button
├── Mobile hamburger button (3 × span.ham-line)
│   └── Animated: top/bottom rotate 45°/-45°, middle fades out
└── Mobile menu (menuOpen && ...)
    ├── Full-screen overlay (z-index 9998, backdrop-filter blur)
    └── Slide-down panel
        ├── NAV_LINKS with larger padding
        ├── Active dot indicator
        └── Theme toggle button
```

## Nav links array

```js
const NAV_LINKS = [
  { to: '/', label: 'Home', icon: 'fa-house' },
  { to: '/dashboard', label: 'Dashboard', icon: 'fa-gauge-high' },
  { to: '/documents', label: 'Documents', icon: 'fa-file-lines' },
  { to: '/utilities', label: 'Utilities', icon: 'fa-wrench' },
  { to: '/random-widget', label: 'Widget', icon: 'fa-cubes' },
  { to: '/hermes', label: 'Hermes', icon: 'fa-cube' },
];
```

## CSS (global.css)

```css
/* Hide desktop nav on mobile */
@media (max-width: 820px) {
  .desktop-nav { display: none !important; }
  .hamburger-btn { display: flex !important; }
}
@media (min-width: 821px) {
  .hamburger-btn { display: none !important; }
}
@media (max-width: 640px) {
  .nav-label { display: none; }
}

/* Ham button */
.hamburger-btn { background: none; border: none; cursor: pointer; }
.hamburger-btn:hover { background: var(--surface-2); }

/* Ham lines */
.ham-line {
  display: block; width: 22px; height: 2.5px;
  background: var(--text); border-radius: 3px;
  transition: all .25s cubic-bezier(.4,0,.2,1);
}

/* Menu animations */
.mobile-menu-overlay { animation: fadeIn .15s ease; }
.mobile-menu-panel { animation: slideDown .25s cubic-bezier(.4,0,.2,1); }

/* Scroll lock */
body.menu-open { overflow: hidden; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## Hamburger button JSX (animated X)

```jsx
<button className="hamburger-btn" onClick={() => setMenuOpen(p => !p)}>
  <span className="ham-line" style={{
    transform: menuOpen ? 'rotate(45deg) translate(5.5px, 5.5px)' : 'none',
  }} />
  <span className="ham-line" style={{
    opacity: menuOpen ? 0 : 1,
  }} />
  <span className="ham-line" style={{
    transform: menuOpen ? 'rotate(-45deg) translate(5.5px, -5.5px)' : 'none',
  }} />
</button>
```

## Body scroll lock

```jsx
useEffect(() => {
  if (menuOpen) document.body.classList.add('menu-open');
  else document.body.classList.remove('menu-open');
  return () => document.body.classList.remove('menu-open');
}, [menuOpen]);
```

## Mobile panel JSX

```jsx
{menuOpen && (
  <div className="mobile-menu-overlay" onClick={() => setMenuOpen(false)}>
    <div className="mobile-menu-panel" onClick={e => e.stopPropagation()}>
      {NAV_LINKS.map(link => (
        <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)}
          className={`navbar-item ${active === link.to ? 'is-active' : ''}`}
          style={{
            padding: '0.65rem 0.85rem', fontSize: '0.95rem',
            display: 'flex', alignItems: 'center', gap: '0.65rem',
            borderRadius: '12px',
            ...(active === link.to ? activeLinkStyle : linkStyle),
          }}
        >
          <i className={`fas ${link.icon}`} style={{ fontSize: '0.95rem', width: '24px' }} />
          <span>{link.label}</span>
          {active === link.to && <span style={{ marginLeft: 'auto', color: 'var(--accent)' }}>●</span>}
        </Link>
      ))}
    </div>
  </div>
)}
```
