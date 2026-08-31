# Error Patterns (từ thực tế)

## Double-toggle theme

**WRONG** — 3 handlers fire:
```js
// theme.js — BUGGY
T.querySelectorAll('.theme-btn').forEach(b=>b.addEventListener('click',toggle)); // 1
T.addEventListener('click',e=>{const b=e.target.closest('.theme-btn');if(b)return toggle()}); // 2
const obs=new MutationObserver(()=>T.querySelectorAll('.theme-btn:not([data-bound])').forEach(b=>{b.dataset.bound='1';b.addEventListener('click',toggle)})); // 3
obs.observe(T.body,{childList:true,subtree:true});
```

**FIX**:
```js
window.toggleTheme=function(){
  const h=document.documentElement;
  const n=h.getAttribute('data-theme')==='light'?'dark':'light';
  localStorage.setItem('btdat-theme',n);
  h.setAttribute('data-theme',n);
  updateIcons(n);
};
// No event listeners. Button uses onclick attribute.
```

## SW Cache HTML pages

**WRONG** — intercepts all same-origin requests:
```js
if(u.origin===location.origin&&(u.pathname.startsWith('/assets/')||u.pathname==='/'||u.pathname==='/dashboard'||u.pathname==='/documents')){
  e.respondWith(caches.match(e.request)...);
}
```
Problem: `/dashboard` gets 302 → `/dashboard.html`. SW caches 302 response. Every subsequent navigation sees redirect → browser follows redirect → SW intercepts `/dashboard.html` → same redirect forever.

**FIX** — remove SW entirely (preferred) or only intercept /assets/:
```js
if(!u.pathname.startsWith('/assets/'))return;
e.respondWith(caches.match(e.request));
```

## Server missing Cache-Control

Before:
```js
res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
```
After:
```js
res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store, must-revalidate' });
```

## Bulma class conflict

```html
<!-- BUG -->
<button class="theme-btn button">☀️</button>
```
`.button` from Bulma has its own padding, margin, font-size. `.theme-btn` CSS is overridden.

```html
<!-- FIX -->
<button class="button is-small" onclick="toggleTheme()">☀️</button>
```

## ERR_HTTP_HEADERS_SENT — Proxy crash

**WRONG** — timeout + error handlers both call `json(res)`:
```js
// r.destroy() fires 'error' event → both handlers run
r.on('error', () => json(res, { ok: false }));
r.on('timeout', () => { r.destroy(); json(res, { ok: false }); });
```

**FIX** — 3-layer defense:
```js
// 1. timedOut flag
let timedOut = false;
r.on('error', () => { if (!timedOut) json(res, { ok: false }); });
r.on('timeout', () => { timedOut = true; r.destroy(); json(res, { ok: false }); });

// 2. try/catch on direct writeHead
r.on('error', () => { try { res.writeHead(502); res.end('Proxy error'); } catch (_) {} });

// 3. headersSent guard in json()
function json(res, data, code = 200) {
  if (res.headersSent) return;
  // ... writeHead + end
}
```
