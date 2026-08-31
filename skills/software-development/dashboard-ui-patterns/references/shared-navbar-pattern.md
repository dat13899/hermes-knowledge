# Shared Navbar Pattern (Fetch + Template)

## Problem
Multi-page vanilla JS app (no framework, no build step) — navbar duplicated across 4+ HTML files. Each edit requires patching all files.

## Solution
Single `navbar.html` template fetched by each page, with per-page overrides via `<template>` tag.

## Architecture
```
public/
├── navbar.html          # Shared template with {PLACEHOLDERS}
├── index.html           # Has <template id="nav-extra">
├── dashboard.html       # Has <template id="nav-extra">
├── random-widget.html   # Has <template id="nav-extra">
└── utilities.html       # Has <template id="nav-extra">
```

## navbar.html template
```html
<nav class="navbar is-glass" role="navigation" aria-label="Main navigation">
  <div class="navbar-brand">
    <a class="navbar-item has-text-weight-bold" href="/">btdat.io.vn{BREADCRUMB}</a>
    <a role="button" class="navbar-burger" onclick="document.querySelector('.navbar-menu').classList.toggle('is-active')" aria-label="Menu"><span></span><span></span><span></span></a>
  </div>
  <div class="navbar-menu">
    <div class="navbar-end">
      <div class="navbar-item"><button class="button is-small" onclick="toggleTheme()" aria-label="Toggle theme"><span class="theme-btn-icon">{THEME_ICON}</span></button></div>
      {EXTRA}
    </div>
  </div>
</nav>
```

## Per-page setup
### Template element
```html
<!-- Breadcrumb via data-bc, links go inside template -->
<template id="nav-extra" data-bc=" / widget">
  <a class="navbar-item" href="/">Home</a>
  <a class="navbar-item" href="/dashboard">Dashboard</a>
  <a class="navbar-item" href="/documents">Docs</a>
  <a class="navbar-item" href="/utilities">Tiện ích</a>
  <a class="navbar-item has-text-link" href="/random-widget">🎲 Widget</a>
</template>
```
- `data-bc` = breadcrumb text (e.g. ` / widget`, ` / dashboard`, empty for landing page)
- Inside template = EXTRA links (each page's specific nav items)
- Active link gets `has-text-link` class

### Placeholder + fetch script
```html
<div id="nav-target"></div>
<script>
fetch('/navbar.html').then(r=>r.text()).then(t=>{
  const tmpl=document.getElementById('nav-extra');
  document.getElementById('nav-target').outerHTML=t
    .replace(/{BREADCRUMB}/g,tmpl.dataset.bc||'')
    .replace(/{EXTRA}/g,tmpl.innerHTML)
    .replace(/{THEME_ICON}/g,localStorage.getItem('btdat-theme')==='light'?'🌙':'☀️');
  // Re-attach scroll listener (theme.js already ran before nav loaded)
  const n=document.querySelector('.navbar.is-glass');
  if(n){const o=()=>n.classList.toggle('scrolled',window.scrollY>20);
    window.addEventListener('scroll',o,{passive:true});o()}
});
</script>
```

## Spacer: keep in page HTML, NOT in navbar.html
```html
<div class="navbar-spacer"></div>
```
Prevents layout shift when fetch hasn't resolved yet. navbar.html should NOT include the spacer.

## Pitfalls
- **theme.js timing** — theme.js runs on DOMContentLoaded. If navbar hasn't been injected yet, the scroll listener misses. Always re-attach in fetch callback.
- **Theme icon** — theme.js sets `.theme-btn-icon` textContent on init. If navbar isn't in DOM yet, icon stays wrong. Calculate from localStorage in fetch callback.
- **Server restart** — navbar.html is served by same Node server. If server is restarted while page is open, fetch resolves fine on next page load. No special handling needed.
