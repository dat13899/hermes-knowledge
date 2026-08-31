# Navbar Fix (July 2026) — Missing navigation links

## Problem

After React migration, Navbar only had Home + Dashboard links. User immediately complained: "cái header sao mất hết link điều hướng tới các chức năng rồi"

## Root cause

The original `NAV_LINKS` array in `Navbar.jsx` only contained 2 links. The other 4 pages (Documents, Utilities, Widget, Hermes) were accessible via direct URL but had no navigation entry.

## Fix

Added 4 missing links and made the navbar responsive with a hamburger menu:

```jsx
const NAV_LINKS = [
  { to: '/', label: 'Home', icon: 'fa-house' },
  { to: '/dashboard', label: 'Dashboard', icon: 'fa-gauge-high' },
  { to: '/documents', label: 'Documents', icon: 'fa-file-lines' },
  { to: '/utilities', label: 'Utilities', icon: 'fa-wrench' },
  { to: '/random-widget', label: 'Widget', icon: 'fa-cubes' },
  { to: '/hermes', label: 'Hermes', icon: 'fa-cube' },
];
```

## Responsive behavior

- **Desktop (≥ 821px)**: All 6 links inline, hamburger hidden
- **Mobile (< 820px)**: Desktop links hidden (`.navbar-menu { display: none !important; }`), hamburger visible
- **Very narrow (< 640px)**: Link labels hidden (`.nav-label { display: none; }`), only icons shown
- **Mobile dropdown**: Fixed position below navbar (top: 52px), glass background, slideDown animation

## Hamburger implementation pattern

```jsx
const [menuOpen, setMenuOpen] = useState(false);

// In JSX:
<button className={`navbar-burger ${menuOpen ? 'is-active' : ''}`}
  onClick={() => setMenuOpen(p => !p)}
  aria-label="menu" aria-expanded={menuOpen}>
  <span></span><span></span><span></span>
</button>

{menuOpen && (
  <div style={{
    position: 'fixed', top: '52px', left: 0, right: 0,
    background: 'var(--glass-bg)', backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    borderBottom: '1px solid var(--glass-border)',
    padding: '0.5rem 0.75rem', zIndex: 9999,
    display: 'flex', flexDirection: 'column', gap: '0.25rem',
    animation: 'slideDown .15s ease',
  }}>
    {NAV_LINKS.map(link => (
      <Link key={link.to} to={link.to}
        onClick={() => setMenuOpen(false)}
        style={{ padding: '0.5rem 0.75rem', fontSize: '0.9rem' }}>
        <i className={`fas ${link.icon}`} style={{ marginRight: '0.5rem' }}></i>
        {link.label}
      </Link>
    ))}
  </div>
)}
```

## CSS needed

```css
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 820px) {
  .navbar-menu { display: none !important; }
  .navbar-burger { display: flex !important; }
}
@media (min-width: 821px) {
  .navbar-burger { display: none !important; }
}
@media (max-width: 640px) {
  .nav-label { display: none; }
}
```

## Lesson

**ALWAYS** build the full `NAV_LINKS` array from the beginning of a migration. Don't start with a subset. Users navigate via the navbar, and missing links are the #1 immediately visible regression after any UI change.
