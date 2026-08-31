---
name: dashboard-ui-patterns
title: Dashboard UI Patterns (Bulma + vanilla JS)
description: Reusable UI patterns for single-page dashboards — SSE logs, health ping, expandable cards, toast system, responsive layout, reading progress, full-text search, drag-drop upload, font controls, keyboard help, PWA, view transitions, a11y
category: software-development
triggers:
  - "ui/ux nâng cấp dashboard"
  - "Bulma dashboard UI"
  - "SSE real-time logs"
  - "health check dashboard"
  - "toast notification system"
  - "reading progress bar"
  - "full-text search document viewer"
  - "drag and drop upload"
  - "PWA service worker"
  - "view transitions"
  - "responsive dashboard layout"
  - "keyboard shortcuts overlay"
  - "font size controls"
  - "expandable cards"
  - "confirm modal"
  - "tab-based panel"
  - "crash alerts SSE"
  - "service search filter"
  - "bulk start/stop"
  - "scheduled restart"
version: "1.4"
---

## Mô tả

Patterns cho single-page dashboard UI với Bulma + vanilla JS (không framework). Mỗi pattern là copy-paste block.

---

## 1. Toast system (stacked + undo)

### CSS (global.css)

```css
.toast-container{position:fixed;top:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem;pointer-events:none}
.toast{pointer-events:auto;padding:.6rem 1rem;border-radius:8px;font-size:.85rem;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,.35);display:flex;align-items:center;gap:.5rem;animation:slideIn .25s ease;max-width:360px;color:#fff}
.toast.success{background:var(--green,#22c55e)}
.toast.error{background:var(--red,#ef4444)}
.toast.info{background:var(--accent,#818cf8)}
.toast.removing{animation:slideOut .2s forwards}
.toast .toast-undo{background:rgba(255,255,255,.2);border:none;color:#fff;padding:2px 8px;border-radius:4px;font-size:.75rem;cursor:pointer;margin-left:.5rem;font-weight:600}
@keyframes slideIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}
@keyframes slideOut{from{opacity:1;transform:translateX(0)}to{opacity:0;transform:translateX(30px)}}
```

### JS

```javascript
function toast(msg,type,undoCb){
  const c=document.getElementById('toast-container')||(t=>{t.id='toast-container';document.body.appendChild(t);return t})(document.createElement('div'));
  c.className='toast-container';
  const el=document.createElement('div');el.className='toast '+type;el.innerHTML=msg;
  if(undoCb){const u=document.createElement('button');u.className='toast-undo';u.textContent='Undo';u.onclick=()=>{undoCb();el.classList.add('removing');setTimeout(()=>el.remove(),200)};el.appendChild(u)}
  c.appendChild(el);setTimeout(()=>{el.classList.add('removing');setTimeout(()=>el.remove(),200)},4000);
}
```

---

## 2. SSE real-time log stream

### Server (Node.js)

Routes: `GET /api/logs/stream` với header `Content-Type: text/event-stream`. Mỗi log entry gửi dạng `event: log\ndata: {...}\n\n`. Support `?serviceId=` filter.

### Client

```javascript
let logEventSource=null;
function connectSSE(filterId){
  if(logEventSource)logEventSource.close();
  const url=filterId?`/api/logs/stream?serviceId=${filterId}`:'/api/logs/stream';
  logEventSource=new EventSource(url);
  logEventSource.onmessage=function(e){
    try{const d=JSON.parse(e.data);appendLog(d.line,false)}catch(_){}
  };
}
function appendLog(line,prepend){
  const box=$('log-box');
  const cls=line.startsWith('[E]')||line.startsWith('[ERROR]')?'error':line.includes('warn')?'warn':'';
  const el=document.createElement('div');el.className='log-line'+(cls?' '+cls:'');
  el.textContent=line;
  if(prepend)box.prepend(el);else box.appendChild(el);
  if(autoScroll)box.scrollTop=box.scrollHeight;
}
```

Log toolbar: select dropdown (service filter), clear, autoscroll toggle, line count.

---

## 3. Health ping inline

Mỗi service card có dot ping:

```javascript
async function pingHealth(id,port,el){
  if(!port){el.className='health-dot offline';return}
  try{
    const r=await fetch(`/api/services/${id}/health`,{signal:AbortSignal.timeout(4000)});
    const d=await r.json();el.className='health-dot '+(d.ok?'online':'offline')+(d.ok?' pulse':'');
  }catch(e){el.className='health-dot offline'}
}
```

CSS: `.health-dot.online{background:var(--green);box-shadow:0 0 6px var(--green);animation:pulse 2s infinite}`

Gọi sau khi render với stagger delay: `svcs.indexOf(s)*300`.

---

## 4. Expandable card

```html
<div class="card card-hover card-expandable" data-svc-id="${id}">
  <div class="card-content" onclick="toggleExpand('${id}')">...</div>
  <div class="card-expanded-body" id="exp-${id}">(detail: status, port, PID, uptime, link)</div>
  <div class="card-footer">(action buttons)</div>
</div>
```

```javascript
function toggleExpand(id){document.querySelector(`[data-svc-id="${id}"]`)?.classList.toggle('expanded')}
```

CSS: `.card-expanded-body{display:none;padding:.5rem .75rem;border-top:1px solid var(--border)}`
`.card-expandable.expanded .card-expanded-body{display:block}`

---

## 5. Document Reader Typography (marked.js rendering)

Full reader typography for rendered Markdown:

```css
.reader-content .article{line-height:1.8;font-size:var(--font-size);padding:2rem 1.5rem;max-width:900px;margin:0 auto;background:rgba(255,255,255,.03);border-radius:var(--radius-md);animation:fadeIn .25s ease}
.reader-content .article h1{font-size:1.5rem;margin:1.2rem 0 .5rem;border-bottom:1px solid var(--glass-border);padding-bottom:.3rem}
.reader-content .article h2{font-size:1.2rem;margin:1rem 0 .4rem}
.reader-content .article h3{font-size:1.05rem;margin:.8rem 0 .3rem}
.reader-content .article p{margin:.5rem 0}
.reader-content .article blockquote{border-left:3px solid var(--accent);padding:.3rem .8rem;margin:.6rem 0;background:rgba(99,102,241,.04);border-radius:0 var(--radius-sm) var(--radius-sm) 0}
.reader-content .article img{max-width:100%;border-radius:var(--radius-sm);margin:.5rem 0}
.reader-content .article table{max-width:100%;border-collapse:collapse;margin:.5rem 0;font-size:.8rem}
.reader-content .article th,.reader-content .article td{border:1px solid var(--glass-border);padding:.3rem .6rem}
.reader-content .article th{background:var(--surface-2);font-weight:600}
.reader-content .article pre{background:var(--surface-2);border:1px solid var(--glass-border);border-radius:var(--radius-sm);padding:.7rem .9rem;overflow-x:auto;font-size:.78rem}
.reader-content .article code{background:var(--surface-2);padding:1px 4px;border-radius:3px;font-size:.85em}
.reader-content .article pre code{background:none;padding:0}
.reader-content .article .word-count{font-size:.6rem;text-align:right;padding:.4rem 0;border-top:1px solid var(--glass-border);margin-top:1rem}
```

Key: `fadeIn` on article load, `--radius-*` tokens, blockquote accent-border, table collapse borders.

## 6. Reading progress bar

```html
<div class="reading-progress" id="reading-progress"></div>
```

```css
.reading-progress{position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,var(--accent),#06b6d4);z-index:9998;transition:width .1s linear;width:0}
```

```javascript
readerContent.addEventListener('scroll',function(){
  const h=this.scrollHeight-this.clientHeight;
  if(h<=0)return;
  progressBar.style.width=Math.min(100,Math.round(this.scrollTop/h*100))+'%';
});
```

Reset về 0 khi load doc mới.

---

## 6. Full-text search (server-side)

```javascript
// GET /api/documents/search?q=
// Iterate .md files, indexOf content, return {id, match:snippet±40chars}
```

Client: debounced input (300ms) → fetch results → dropdown `<div class="search-results">` → click loads doc.

Highlight in rendered Markdown:

```javascript
renderArticle(md){
  const html=marked.parse(md);
  const q=searchInput.value.trim();
  art.innerHTML=q?html.replace(new RegExp('('+escapedQ+')','gi'),'<mark>$1</mark>'):html;
}
```

---

## 7. Font size controls

```css
:root{--font-size:.95rem}
.reader-content .article{font-size:var(--font-size)}
```

```javascript
function fontSize(delta){
  const r=document.querySelector(':root');
  let cur=parseFloat(getComputedStyle(r).getPropertyValue('--font-size'))||.95;
  cur=Math.max(.7,Math.min(1.5,cur+delta*.05));
  r.style.setProperty('--font-size',cur+'rem');
}
```

---

## 8. Drag-and-drop upload

```javascript
const dz=document.getElementById('drop-zone');
document.addEventListener('dragenter',e=>{e.preventDefault();dz.style.display='block';dz.classList.add('dragover')});
document.addEventListener('dragover',e=>e.preventDefault());
document.addEventListener('dragleave',e=>{if(e.target===document||e.relatedTarget===null){dz.style.display='none';dz.classList.remove('dragover')}});
dz.addEventListener('drop',async e=>{
  e.preventDefault();dz.style.display='none';
  const f=e.dataTransfer.files[0];if(!f||!f.name.endsWith('.docx'))return;
  // FileReader → base64 → fetch POST
});
```

---

## 9. Keyboard help tooltip (compact)

Full-screen overlay bị user phàn nàn "vỡ giao diện". Dùng tooltip nhỏ góc dưới phải.

### CSS

```css
.kb-hint{position:fixed;bottom:1rem;right:1rem;z-index:9997;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:.6rem .9rem;font-size:.75rem;box-shadow:0 4px 20px rgba(0,0,0,.3);display:none;min-width:200px}
.kb-hint.show{display:block}
.kb-hint h3{font-size:.8rem;color:var(--text-strong);margin:0 0 .4rem;font-weight:600}
.kb-hint .kb-row{display:flex;justify-content:space-between;padding:.15rem 0;font-size:.7rem;color:var(--text-dim)}
.kb-hint .kb-row kbd{background:var(--surface-2);border:1px solid var(--border);border-radius:3px;padding:0 5px;font-size:.65rem;font-family:monospace}
```

### HTML

```html
<div class="kb-hint" id="kb-hint" onclick="this.classList.remove('show')">
  <h3>⌨</h3>
  <div class="kb-row"><span>Help</span><kbd>?</kbd></div>
  <div class="kb-row"><span>Dashboard</span><kbd>g d</kbd></div>
  <div class="kb-row"><span>Docs</span><kbd>g o</kbd></div>
  <div class="kb-row"><span>Home</span><kbd>g h</kbd></div>
</div>
```

### JS

```javascript
document.addEventListener('keydown',e=>{
  if(e.key==='?'&&!(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')){
    e.preventDefault();document.getElementById('kb-hint')?.classList.toggle('show')
  }
});
```

Click tooltip hides it. Không backdrop, không focus trap, không phá layout.

---

## 10. PWA Service Worker

```javascript
const CACHE='btdat-v1';
const ASSETS=['/','/dashboard','/documents','/assets/global.css','/assets/theme.js','/assets/favicon.svg','/assets/manifest.json'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(clients.claim());e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.origin===location.origin&&(u.pathname.startsWith('/assets/')||['/','/dashboard','/documents'].includes(u.pathname))){
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(r=>{const c=caches.open(CACHE);c.then(cache=>cache.put(e.request,r.clone()));return r})));
  }
});
```

Register: `if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}`

---

## 11. View Transitions (crossfade)

```css
@view-transition{navigation:auto}
::view-transition-old(root){animation:0.3s ease fadeOut}
::view-transition-new(root){animation:0.3s ease fadeIn}
@keyframes fadeOut{to{opacity:0}}
@keyframes fadeIn{from{opacity:0}}
```

---

## 12. Responsive layout with container padding

Main container cần `padding` để spacing từ edge:

```css
.dash-stats{padding:0 .5rem}
.dash-layout{padding:0 .5rem}
```

Ko dùng `margin` trên layout container — overflow-x hidden ở page level. Dùng `padding` trên stats + layout.

Button toggle log panel width (380px / 480px / full).

---

## 13. Skeleton loader

```css
.skeleton{background:linear-gradient(90deg,var(--surface-2) 25%,var(--border) 50%,var(--surface-2) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:6px}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.skel-d1{animation-delay:.1s}.skel-d2{animation-delay:.2s}.skel-d3{animation-delay:.3s}.skel-d4{animation-delay:.4s}
```

---

## 14. Reduced motion & light a11y

Tránh skip-link — user thấy xấu, làm vỡ layout. Chỉ giữ reduced motion + `aria-label`, `role`, `aria-live`.

```css
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:0.01ms!important;animation-iteration-count:1!important;transition-duration:0.01ms!important}}
```

Use `aria-label` on nav, `role="navigation"`, `aria-live="polite"` on status areas.

---

## 15. Inline service actions (landing page)

Cho phép Start/Stop/Restart trực tiếp trên landing service card, không cần vào dashboard:

```javascript
async function actLand(id,a){
  if(a==='stop'||a==='restart'){/* confirm dialog */return}
  const r=await fetch(`/api/services/${id}/${a}`,{method:'POST'});
  if((await r.json()).error)return toast('❌ Failed','error');
  toast('▶ Started','success');setTimeout(loadSvcs,500);
}
```

## 16. Confirm modal (replaces browser confirm())

Shared Bulma modal across all pages. See `references/ux-fixes-july-2026.md` for full HTML+JS.

Tránh `confirm()` — browser native dialog inconsistent với dark theme. Luôn dùng Bulma `.modal` wrapper.

---

## 17. SSE crash alerts (dashboard v3.1+)

Log EventSource listens for `alert` event type. Red badge top-right shows count. Click opens dropdown.

Server-side: exit handler gửi alert event khi process crash (code ≠ 0, sig ≠ SIGTERM):
```javascript
child.on('exit', (code, sig) => {
  if (wasRunning && code !== 0 && sig !== 'SIGTERM') {
    for (const cb of st.sseClients) cb(alert.msg, id, 'alert');
  }
});
```

SSE client handler:
```javascript
logEventSource.addEventListener('alert', function(e){
  const d=JSON.parse(e.data); addAlert(d.msg);
});
```

---

## 18. Tab-based panel

Service list, Resource monitor, Port scanner, File browser — each as `.panel` with tab switch:

```html
<div class="tab-bar">
  <button class="active" data-tab="svc">Services</button>
  <button data-tab="res">⚡ Resources</button>
  <button data-tab="ports">🔌 Ports</button>
  <button data-tab="files">📁 Files</button>
</div>
<div id="tab-svc" class="panel active">...</div>
<div id="tab-res" class="panel">...</div>
```

```javascript
function switchTab(name){
  document.querySelectorAll('.tab-bar button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+name));
}
```

Lazy load tab content on first switch (resources, ports, files fetch on click).

---

## 19. Service search/filter

Client-side filter by name/description. Input filters `.card-expandable` visibility:

```javascript
function filterSvcs(){
  const q=$('svc-search').value.toLowerCase();
  document.querySelectorAll('.card-expandable').forEach(c=>{
    c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
  });
}
```

No server round-trip. Works on rendered cards only.

---

## 20. React Migration: Feature Parity Checklist

When porting a vanilla JS dashboard page to React, complete this checklist to avoid missing-feature-drift:

### Documents Page checklist
```
[ ] Full-text search with dropdown results
[ ] Search history (localStorage, last 5 queries)
[ ] Sort bar (newest, oldest, A→Z, Z→A)
[ ] Draft/status filter checkbox
[ ] Bulk select checkboxes + "Delete selected" button
[ ] Font size controls (A+/A- adjust CSS var --font-size)
[ ] Markdown toolbar (B, I, H, Link, Code, List buttons with cursor wrapping)
[ ] Print button → window.print()
[ ] Download button → download as .md file
[ ] Export PDF → POST /api/documents/:id/export-pdf → blob download
[ ] Reading progress bar (fixed top, 3px gradient, z-index 999)
[ ] Word count at bottom of reader
[ ] Inline rename (double-click title → input → Enter/Blur saves)
[ ] New doc modal (title, tags, template selector: Blank/Article/Report/Note, content)
[ ] Drag-and-drop upload (.docx via FileReader → base64 → POST)
[ ] Cache clear button (caches.delete + reload)
[ ] Dynamic tag filter (extract tags from all docs, not hardcoded)
[ ] Ctrl+S save shortcut + Escape to close editor
```

### Dashboard Page checklist
```
[ ] Stats bar (running/stopped/error count cards)
[ ] Auto-restart badge in service card header
[ ] Clickable port links (open localhost:N in new tab)
[ ] 24h timeline chart (colored bars from service event history)
[ ] SSE log stream with service filter
[ ] Confirm modals for stop/restart/delete
[ ] Skeleton loading cards on first load
```

### Home Page checklist
```
[ ] Status bar (running count + stopped count + uptime/dot)
[ ] Tech stack badges (clickable links + hover effects)
[ ] Contact section with social links
[ ] Anchor nav links (#services, #stack, #contact)
[ ] Confirm modal for stop/restart actions
[ ] Typing effect (cycle through taglines)
[ ] Health ping dots next to each service
[ ] Cache clear button in footer
```

## 21. Liquid Glass UI system

Full glassmorphism theme with floating blobs, reveal animations, fixed glass navbar. Zero deps.

### Glass classes

```css
.glass{background:var(--glass-bg);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);border:1px solid var(--glass-border);box-shadow:0 8px 32px var(--glass-shadow)}
.glass-card,.card.glass-card{border-radius:16px;background:var(--glass-bg);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);border:1px solid var(--glass-border);box-shadow:0 8px 32px var(--glass-shadow);transition:transform .3s cubic-bezier(.25,.46,.45,.94),box-shadow .3s}
.glass-card:hover{transform:translateY(-4px) scale(1.01);box-shadow:0 12px 48px var(--glass-shadow)}
.glass-card:active{transform:scale(.98)}
```

### Glass navbar (fixed + scroll blur)

```css
.navbar.is-glass{position:fixed;top:0;left:0;right:0;z-index:500;background:transparent;transition:background .3s,border .3s,box-shadow .3s}
.navbar.is-glass.scrolled{background:var(--glass-bg);-webkit-backdrop-filter:blur(30px);backdrop-filter:blur(30px);border-bottom:1px solid var(--glass-border);box-shadow:0 4px 24px var(--glass-shadow)}
.navbar-spacer{height:52px}
```

HTML: `<nav class="navbar is-glass">` then `<div class="navbar-spacer"></div>`. JS: scroll listener toggles `scrolled` class.

### CSS vars for glass

Add to dark/light theme blocks:
```
--glass-bg:rgba(17,24,39,.55); --glass-border:rgba(255,255,255,.08); --glass-shadow:rgba(0,0,0,.3)
--blob-1:#818cf8; --blob-2:#06b6d4; --blob-3:#a855f7; --blob-4:#f59e0b
```

### Radius tokens (global.css)

```css
:root{--radius-sm:6px;--radius-md:12px;--radius-lg:16px;--radius-xl:20px}
```

Use everywhere — `.glass-card`, `.widget-card`, `.svc-card`, `.player-area`, `inputs`, `buttons`. Replaces hardcoded `8px`, `12px`, `14px`, `16px` across all pages. Bump margin/padding/vars simultaneously to avoid visual regressions.

### Unified button classes (global.css)

```css
.btn-ghost{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:var(--radius-sm);color:var(--text-dim);padding:.3rem .65rem;font-size:.77rem;cursor:pointer;transition:all .12s;display:inline-flex;align-items:center;gap:.3rem}
.btn-ghost:hover{background:var(--surface-2);color:var(--text);border-color:var(--accent);transform:translateY(-1px)}
.btn-primary{background:var(--accent);border:none;border-radius:var(--radius-sm);color:#fff;padding:.3rem .7rem;font-size:.78rem;cursor:pointer;font-weight:600;transition:opacity .15s,transform .15s;display:inline-flex;align-items:center;gap:.3rem}
.btn-primary:hover{opacity:.9;transform:translateY(-1px)}
.btn-danger{border-color:var(--red);color:var(--red)}
.btn-danger:hover{background:rgba(239,68,68,.1);border-color:var(--red);color:var(--red)}
.btn-sm{font-size:.7rem;padding:.2rem .5rem}
.btn-icon{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:5px;color:var(--text-dim);padding:.2rem .45rem;font-size:.7rem;cursor:pointer;transition:all .12s;line-height:1.4}
.btn-icon:hover{background:var(--surface-2);color:var(--text);border-color:var(--accent);transform:translateY(-1px)}
```

Target replacement for disparate button styles across pages (`.btn`, `.wid-btn`, `.back-btn`, `.font-controls button`, `.timer-bar button`, `.svc-inline-actions button`). Start migration from most-used page, not all at once.

### Unified section headings (global.css)

```css
.section-title{font-size:1.15rem;font-weight:700;color:var(--text-strong);display:flex;align-items:center;gap:.4rem;margin-bottom:.6rem}
.section-sub{font-size:.82rem;color:var(--text-dim);margin-bottom:.8rem}
.section-icon{flex-shrink:0;line-height:1}
```

### @keyframes fadeIn (global.css)

```css
@keyframes fadeIn{0%{opacity:0;transform:translateY(6px)}100%{opacity:1;transform:translateY(0)}}
```

Used for `.player-area`, `.detail-view-wrap`, `.reader-content .article`. Single shared keyframe instead of per-page duplicates.

### Comprehensive UI consistency sweep pattern

When user says "nâng cấp lại ui/ux toàn diện đi" — do NOT touch JS logic. Scope:

1. **global.css** — add missing tokens (radius vars, button classes, section headings, keyframes)
2. **Per-page radius pass** — replace hardcoded `border-radius: Xpx` with `var(--radius-*)` across all pages. Use grep: `grep -n 'border-radius' *.html`
3. **Per-page padding pass** — `.section{padding:2.5rem 1.25rem}` replaces `0` horizontal to fix edge-hugging
4. **Cross-page typography** — font-size, line-height, heading hierarchy consistent
5. **Cross-page button styles** — migrate toward `.btn-ghost`/`.btn-primary`/`.btn-icon` classes
6. **Animation consistency** — all fade/slide animations reference global keyframes, no inline `@keyframes` per page
7. **Commit per page group** — not one monolithic commit. Commit order: global.css first (foundation), then each page.

### Landing page hero section

Khi user nói "trang chủ bị sát viền" — fix nhanh:
```css
.section{padding:2.5rem 1.25rem}  /* replaces padding:2.5rem 0 */
.hero-section{padding:5rem 1.75rem 3.5rem}
```
Không dùng `margin` trên container — Bulma `.container` có sẵn margin auto. Dùng padding trên section/hero.
Kiểm tra: Bulma `.section` mặc định `padding:3rem 1.5rem`, nhưng `padding:2.5rem 0` ghi đè mất padding trái phải. Fix bằng đặt `padding:2.5rem 1.25rem`.

### Cache-bust pattern for CSS/JS

```bash
# Bump version across all pages
for f in *.html; do sed -i 's/\?v=[0-9]/?v='"$(( $(grep -oP 'v=\K[0-9]' index.html) + 1 ))"'/g' "$f"; done
```
Luôn migrate lên version kế tiếp, ko skip. Verify bằng curl trước khi git push.

### Liquid blobs (floating background)

```html
<div class="blob-container"><div class="blob"></div><div class="blob"></div><div class="blob"></div><div class="blob"></div></div>
```

```css
.blob-container{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:-1}
.blob{position:absolute;border-radius:50%;filter:blur(80px);opacity:.25;will-change:transform;animation:blobFloat 25s ease-in-out infinite}
```

4 blobs — diff sizes/positions/delays. `blur(80px)` + `opacity:.25` + border-radius morph creates organic fluid. Use 2 animation keyframes (`blobFloat`, `blobFloat2`) assigned to `.blob:nth-child(2)` so blobs don't synchronize visually.

### Blob vars in theme.js

Blob color must change per theme (dark=indigo/cyan/purple/amber, light=pink/orange/purple/green). Inject via CSS custom properties on `<html>`:

```javascript
function setBlobVars(theme){
  const dark={blob1:'#818cf8',blob2:'#06b6d4',blob3:'#a855f7',blob4:'#f59e0b'};
  const light={blob1:'#f472b6',blob2:'#fb923c',blob3:'#a78bfa',blob4:'#34d399'};
  const b=theme==='light'?light:dark;
  document.documentElement.style.setProperty('--blob-1',b.blob1);
  // ... etc
}
```

Full theme.js init sequence:
1. Read `localStorage` (or `prefers-color-scheme` fallback)
2. Set `data-theme` attribute on `<html>`
3. Call `setBlobVars(theme)` for blob colors
4. Set `.theme-btn-icon` text
5. After DOM ready: init IntersectionObserver for `.reveal` elements
6. Init glass navbar scroll listener (`.is-glass`)

### IntersectionObserver for scroll reveal

```javascript
(function(){
  let ro=null;
  function initReveal(){
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.reveal-scale').forEach(el=>{
      if(el.getBoundingClientRect().top<window.innerHeight-60)el.classList.add('visible');
    });
    if(ro)ro.disconnect();
    ro=new IntersectionObserver(ents=>{ents.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')})},{rootMargin:'0px 0px -60px 0px'});
    document.querySelectorAll('.reveal, etc').forEach(el=>ro.observe(el));
  }
  // Run on DOMContentLoaded, load, and watch DOM mutations
})();
```

### Scroll reveal animations

`.reveal` (translateY 30px), `.reveal-left`, `.reveal-right`, `.reveal-scale`. IntersectionObserver toggles `.visible`. Stagger delays `.sd-1`–`.sd-7`.

### Hero glow

```css
.hero-glow{background:linear-gradient(135deg,var(--accent),var(--blob-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;filter:drop-shadow(0 0 30px rgba(129,140,248,.3))}
```

### Pitfalls

- `backdrop-filter`: always include `-webkit-backdrop-filter` prefix for Firefox.
- Blob container `position:fixed` (not relative) so it sits under everything including fixed navbar.
- `prefers-reduced-motion` must kill blob animation (opacity .08 + animation:none).
- **Cloudflare cache CSS** — CF caches CSS aggressively. After changes, add `?v=N` query param to CSS link. Hard reload not enough.
- **Navbar fixed needs spacer** — `<div class="navbar-spacer">` (52px) after nav. Don't use body padding-top.
- Glass hover + `will-change` — test on low-end GPUs. `backdrop-filter` is expensive.
- **Comprehensive sweep, not incremental** — when converting a page to liquid glass, replace ALL `var(--border)` with `var(--glass-border)` in ONE pass. Incremental 3+ patches get rejected by user with escalating frustration. Full protocol in `shared-navigation/references/style-consistency.md`.
- **Audit before touch** — count `--border`/`--glass-border`/`glass-card`/inline-CSS-size across all pages FIRST using `references/css-consistency-audit.md`. One quantify-all step saves 5 back-and-forth rounds with user.
- **Don't touch inline styles on glass panels** — buttons, toolbars, headers on glass surfaces use outline/ghost variant (`background:var(--glass-bg); border:1px solid var(--glass-border)`) not solid fill (`background:var(--accent); color:#fff`). Solid accent buttons clash with frosted glass aesthetic.
- **Don't use solid-fill accent buttons on glass toolbars** — outline glass buttons (`background:var(--glass-bg); border:1px solid var(--accent); color:var(--accent)`) look consistent with frosted UI. Solid-fill buttons (`background:var(--accent); color:#fff`) clash with glass aesthetic. Exception: primary CTAs on landing page.
- **Don't hover-lift structural panels** — sidebar, reader, layout containers get `border-radius` + `box-shadow` but NOT `hover{transform:translateY()}`. Only `.glass-card` (individual cards) gets hover lift.

---

## 21. Random Discovery Widget

3-source random content fetcher: Wikipedia article, static fact pool, or YouTube search result.

### Server: Wikipedia (handles 303 redirect)

Wikipedia `/api/rest_v1/page/random/summary` returns **303 redirect** (not direct JSON). Must follow manually:

```javascript
const https = require('https');
const r = await new Promise((resolve, reject) => {
  https.get('https://en.wikipedia.org/api/rest_v1/page/random/summary',
    { headers: { 'User-Agent': 'MyApp/1.0' }, timeout: 8000 }, res => {
    if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
      https.get(res.headers.location, { headers: { 'User-Agent': 'MyApp/1.0' }, timeout: 8000 }, res2 => {
        let d = ''; res2.on('data', c => d += c);
        res2.on('end', () => { try { resolve(JSON.parse(d)); } catch(_) { reject(); } });
      }).on('error', reject);
      return;
    }
    let d = ''; res.on('data', c => d += c);
    res.on('end', () => { try { resolve(JSON.parse(d)); } catch(_) { reject(); } });
  }).on('error', reject);
});
```

Return fields: `r.title`, `r.extract`, `r.content_urls.desktop.page`, `r.thumbnail?.source`.

### Server: Random YouTube via yt-dlp search (with fallback)

```javascript
const keywords = ['beautiful scenery', 'strange things', 'unexplained', 'rare skills'];
let video = null;
try {
  const q = keywords[Math.floor(Math.random() * keywords.length)];
  const out = execSync(`yt-dlp --dump-json --no-warnings --default-search "ytsearch" "${q}"`,
    { timeout: 15000, maxBuffer: 1024 * 512, encoding: 'utf8', windowsHide: true });
  const v = JSON.parse(out.split('\\n').filter(Boolean)[0]);
  if (v && v.id) { video = {...}; CACHE.push(video); }
} catch (_) { /* yt-dlp failed — fall through */ }
if (!video) {
  const pool = CACHE.length ? CACHE : FALLBACK_POOL;
  const f = pool[Math.floor(Math.random() * pool.length)];
  video = { title: f.title, id: f.id, ... };
}
```

See `video-downloader` skill for full fallback pool + cache pattern. Key: `timeout: 15000`, `--default-search "ytsearch"`, fallback pool of ~16 known video IDs.

### Server: Fact pool (static JSON)

`facts.json` as array of `{text, source?}` objects. ~40 facts, read fresh each request (or cache in memory).

### Server route must be async

`http.createServer((req, res) =>` → `http.createServer(async (req, res) =>` for `await` to work inside route handlers.

### Client: skeleton pattern

```css
.rand-skel .skel-line{height:.8rem;background:linear-gradient(90deg,var(--surface-2) 25%,var(--border) 50%,var(--surface-2) 75%);background-size:200%;animation:shimmer 1.5s infinite;border-radius:4px;margin-bottom:.5rem}
.rand-skel .skel-line:nth-child(1){width:60%}.rand-skel .skel-line:nth-child(2){width:90%}
```

### Client: fetch and render

```javascript
async function discover(type){
  empty.style.display='none'; res.style.display='none'; skel.style.display='block';
  try{
    const r = await fetch('/api/utilities/random' + (type ? '?type='+type : ''));
    const d = await r.json();
    // d.type: 'wiki'|'fact'|'youtube'
    if(d.type==='wiki'){ /* title + img + extract + link */ }
    else if(d.type==='fact'){ /* text only + optional source */ }
    else{ /* title + channel + duration + link */ }
    res.style.display='block';
  } catch(e) {
    empty.innerHTML = '<div class="icon">😵</div><p>Lỗi, thử lại</p>'; empty.style.display='block';
  }
  skel.style.display='none';
}
```

Filter buttons: "Khám phá" (any), "Wikipedia", "Fact", "YouTube". Each calls `discover(type)`.

---

## 22. Brain Dump Canvas

Click-to-add note on infinite canvas. Drag to move. Persist to localStorage. Export as Markdown/JSON.

### HTML

```html
<div class="brain-bar">
  <span>Click để thêm note, kéo để di chuyển</span>
  <button onclick="brainExport('md')">Markdown</button>
  <button onclick="brainExport('json')">JSON</button>
  <button onclick="brainClear()" style="color:var(--red)">Clear</button>
  <span class="status" id="brain-status">0 notes</span>
</div>
<div class="brain-workspace" id="brain-ws" onclick="brainAdd(event)">
  <div class="brain-hint" id="brain-hint">Bấm vào khoảng trống để thêm note</div>
</div>
```

### CSS

```css
.brain-workspace{position:relative;width:100%;height:70vh;overflow:hidden;cursor:crosshair;background:var(--glass-bg);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);border:1px solid var(--glass-border);border-radius:12px}
.brain-note{position:absolute;min-width:140px;max-width:260px;padding:.5rem .7rem;background:rgba(79,70,229,.1);border:1px solid var(--glass-border);border-radius:8px;cursor:grab;z-index:10;font-size:.8rem}
.brain-note .brain-note-text{outline:none;min-height:1.2em;width:100%;background:transparent;border:none;color:var(--text);font-size:.8rem;font-family:inherit;resize:vertical}
.brain-note .brain-del{position:absolute;top:-6px;right:-6px;width:16px;height:16px;border-radius:50%;background:var(--red);color:#fff;border:none;font-size:.5rem;cursor:pointer;opacity:0;transition:.15s}
.brain-note:hover .brain-del{opacity:1}
.brain-hint{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--text-dim);pointer-events:none;z-index:0}
```

### JS: click to add note

```javascript
function brainAdd(e){
  if(e.target !== document.getElementById('brain-ws') && !e.target.closest('.brain-hint')) return;
  const ws = document.getElementById('brain-ws');
  const rect = ws.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width * 100) + '%';
  const y = ((e.clientY - rect.top) / rect.height * 100) + '%';
  const div = document.createElement('div');
  div.className = 'brain-note';
  div.style.left = x; div.style.top = y;
  div.innerHTML = '<textarea class="brain-note-text" rows="2" placeholder="Ghi gì đó..." oninput="brainSave()"></textarea>' +
    '<button class="brain-del" onclick="this.parentElement.remove();brainSave()">✕</button>';
  ws.appendChild(div);
  div.querySelector('.brain-note-text').focus();
  brainSave();
}
```

### JS: drag to move

```javascript
function makeDraggable(el){
  el.addEventListener('mousedown', e => {
    if(e.target.tagName === 'TEXTAREA' || e.target.tagName === 'BUTTON') return;
    e.preventDefault();
    const r = el.getBoundingClientRect(), ws = document.getElementById('brain-ws').getBoundingClientRect();
    const offX = e.clientX - r.left, offY = e.clientY - r.top;
    const mousemove = ev => {
      let pctX = ((ev.clientX - ws.left - offX) / ws.width) * 100;
      let pctY = ((ev.clientY - ws.top - offY) / ws.height) * 100;
      el.style.left = Math.max(0, Math.min(90, pctX)) + '%';
      el.style.top = Math.max(0, Math.min(90, pctY)) + '%';
    };
    const mouseup = () => { document.removeEventListener('mousemove', mousemove); brainSave(); };
    document.addEventListener('mousemove', mousemove);
    document.addEventListener('mouseup', mouseup, {once: true});
  });
}
```

### JS: localStorage persistence

```javascript
function brainSave(){
  const notes = [];
  document.querySelectorAll('.brain-note').forEach(n => {
    const text = n.querySelector('.brain-note-text').value;
    if(text.trim()) notes.push({text, left: n.style.left, top: n.style.top});
  });
  localStorage.setItem('brain-dump', JSON.stringify(notes));
  document.getElementById('brain-status').textContent = notes.length + ' notes';
}

function brainLoad(){
  try {
    const data = JSON.parse(localStorage.getItem('brain-dump')) || [];
    data.forEach(n => {
      const div = document.createElement('div');
      div.className = 'brain-note'; div.style.left = n.left; div.style.top = n.top;
      div.innerHTML = '<textarea class="brain-note-text" rows="2">'+n.text.replace(/</g,'&lt;')+'</textarea>' +
        '<button class="brain-del" onclick="this.parentElement.remove();brainSave()">✕</button>';
      document.getElementById('brain-ws').appendChild(div);
      makeDraggable(div);
    });
    brainSave();
  } catch(_) {}
}
```

### JS: export / clear

```javascript
function brainExport(fmt){
  const notes = JSON.parse(localStorage.getItem('brain-dump')) || [];
  if(!notes.length) return toast('Không có note','info');
  let out = fmt==='md' ? '# Brain Dump\n\n'+notes.map((n,i)=>(i+1)+'. '+n.text).join('\n')
                       : JSON.stringify(notes, null, 2);
  const a = document.createElement('a');
  a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(out);
  a.download = 'brain-dump.' + (fmt==='md'?'md':'json');
  a.click();
}

function brainClear(){
  if(!confirm('Xoá tất cả notes?')) return;
  document.querySelectorAll('.brain-note').forEach(n => n.remove());
  brainSave();
}
```

### Pitfalls

- **`e.target` check** — verify user clicked on workspace background, not on existing note. Use `!e.target.closest('.brain-hint')` to allow clicks on the hint text.
- **Drag percentage clamp** — 0-90% so notes don't disappear off-edge. `90%` leaves room for delete button.
- **Textarea resize** — `resize: vertical` so user can expand height without breaking width.
- **Export HTML escaping** — note text can contain `<`. In localStorage save it raw (safe in JSON); in HTML insert use `.replace(/</g,'&lt;')`.
- **Call `makeDraggable(div)` after every create and after `brainLoad()`**.

---

## 23. Multi-Widget Tab Page (Bulma tabs)

Pattern trang có 5+ widget độc lập, mỗi widget 1 tab riêng. Dùng Bulma `.tabs` với data attributes.

### HTML

```html
<div class="tabs-container">
  <div class="tabs is-small">
    <ul>
      <li class="is-active" data-tab="widget1"><a onclick="switchTab('widget1')">🎲 Tab 1</a></li>
      <li data-tab="widget2"><a onclick="switchTab('widget2')">🎨 Tab 2</a></li>
      <li data-tab="widget3"><a onclick="switchTab('widget3')">🍜 Tab 3</a></li>
    </ul>
  </div>
</div>

<div class="tab-panel active" id="tab-widget1"><!-- widget 1 --></div>
<div class="tab-panel" id="tab-widget2"><!-- widget 2 --></div>
<div class="tab-panel" id="tab-widget3"><!-- widget 3 --></div>
```

### JS

```javascript
function switchTab(id){
  document.querySelectorAll('.tabs li').forEach(l=>l.classList.toggle('is-active',l.dataset.tab===id));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+id));
}
```

### CSS

```css
.tab-panel{display:none}.tab-panel.active{display:block}
```

### When to use `is-small`

- 2-4 tabs → `is-medium` or omit (default)
- 5+ tabs → `is-small` để không tràn trên desktop. Tự động wrap trên mobile.

### Widget card container

```css
.wid-card{background:var(--glass-bg);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:12px;padding:2rem;min-height:200px;text-align:center}
```

---

## 24. Client-Side Random Picker (embedded data)

Pattern: data array nhúng trong JS, random pick mỗi lần bấm nút. Không cần API.

### Data pattern

```javascript
const items = [
  {name:'Phở bò', emoji:'🍜', cat:'Món mặn', desc:'Nước dùng xương bò...'},
  {name:'Bún chả', emoji:'🍖', cat:'Món mặn', desc:'Thịt heo nướng...'},
  // 30+ items
];
```

### Pick with dedup guard

Tránh trùng item liên tiếp khi bấm "Gợi ý khác":

```javascript
let _lastIdx = -1;
function pickOne(){
  let i;
  do { i = Math.floor(Math.random() * items.length); } while(i === _lastIdx && items.length > 1);
  _lastIdx = i;
  const item = items[i];
  // render item.name, item.emoji, item.cat, item.desc
}
```

### Render pattern

```javascript
function renderItem(item){
  document.getElementById('result-emoji').textContent = item.emoji;
  document.getElementById('result-name').textContent = item.name;
  document.getElementById('result-cat').textContent = item.cat;
  document.getElementById('result-desc').textContent = item.desc;
}
```

Dùng `.textContent` thay `.innerHTML` khi không cần markup — an toàn hơn, nhanh hơn.

---

## 25. Color Palette Generator (HSL Golden Ratio)

Sinh bảng màu hài hòa dùng golden angle (≈222.5°) trong không gian HSL. 100% client-side, không API.

### Core: HSL to Hex

```javascript
function hslToHex(h, s, l){
  h /= 360; s /= 100; l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = n => { const k = (n + h * 12) % 12; return l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1); };
  const t = x => Math.round(255 * f(x / 3)).toString(16).padStart(2, '0');
  return '#' + t(0) + t(8) + t(4);
}
```

### Palette generation

```javascript
function genPalette(count = 5){
  const golden = 0.618033988749895; // 1/φ
  let hue = Math.random() * 360;
  const sBase = 45 + Math.random() * 20;
  const lBase = 40 + Math.random() * 15;
  const colors = Array.from({length: count}, (_, i) => {
    const h = (hue + golden * i * 360) % 360;
    const s = Math.min(95, Math.max(15, sBase + Math.random() * 20 - 10));
    const l = Math.min(80, Math.max(20, lBase + Math.random() * 20 - 10));
    return hslToHex(h, s, l);
  });
  return colors;
}
```

### UI: swatch grid

```html
<div class="palette-grid" id="palette-grid"></div>
```

```css
.palette-grid{display:flex;gap:8px;flex-wrap:wrap}
.palette-swatch{flex:1;min-width:100px;height:120px;border-radius:10px;cursor:pointer;position:relative;transition:transform .2s}
.palette-swatch:hover{transform:scale(1.06);z-index:2}
.palette-hex{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.55);color:#fff;padding:3px 10px;border-radius:6px;font-size:.75rem;font-family:monospace;backdrop-filter:blur(4px)}
```

```javascript
function renderPalette(colors){
  document.getElementById('palette-grid').innerHTML = colors.map(c =>
    `<div class="palette-swatch" style="background:${c}" onclick="copyText('${c}')"><span class="palette-hex">${c}</span></div>`
  ).join('');
}
```

---

## 26. Password Generator with Strength Meter

Options (upper/lower/number/symbol toggles), length slider, real-time strength indicator.

### HTML structure

```html
<div class="pw-display" id="pw-output">D3f@ult_P@ss1</div>
<div class="pw-options">
  <label class="pw-opt"><input type="checkbox" id="pw-upper" checked onchange="genPassword()"> A-Z</label>
  <label class="pw-opt"><input type="checkbox" id="pw-lower" checked onchange="genPassword()"> a-z</label>
  <label class="pw-opt"><input type="checkbox" id="pw-nums" checked onchange="genPassword()"> 0-9</label>
  <label class="pw-opt"><input type="checkbox" id="pw-syms" onchange="genPassword()"> !@#$%</label>
</div>
<div class="pw-length">
  <label>Độ dài: <span id="pw-len-label">16</span></label>
  <input type="range" id="pw-len" min="6" max="64" value="16" oninput="updateLen()">
</div>
<div class="pw-strength-bar"><div id="pw-bar"></div></div>
```

### Generation + scoring

```javascript
function genPassword(){
  const len = parseInt(document.getElementById('pw-len').value);
  const sets = {
    upper:'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    lower:'abcdefghijklmnopqrstuvwxyz',
    nums:'0123456789',
    syms:'!@#$%^&*()_+-=[]{}|;:,.<>?'
  };
  let chars = '';
  if(document.getElementById('pw-upper').checked) chars += sets.upper;
  if(document.getElementById('pw-lower').checked) chars += sets.lower;
  if(document.getElementById('pw-nums').checked) chars += sets.nums;
  if(document.getElementById('pw-syms').checked) chars += sets.syms;
  if(!chars) chars = sets.lower;

  let pw = '';
  for(let i = 0; i < len; i++) pw += chars[Math.floor(Math.random() * chars.length)];
  document.getElementById('pw-output').textContent = pw;

  // Strength scoring
  let score = 0;
  if(len >= 10) score++; if(len >= 14) score++; if(len >= 20) score++;
  if(upper && lower) score++;
  if(nums) score++; if(syms) score++;
  const pct = [0, 20, 35, 55, 75, 100][Math.min(score, 5)];
  bar.style.width = pct + '%';
  bar.style.background = ['#ef4444','#ef4444','#f59e0b','#22c55e','#22c55e','#22c55e'][Math.min(score, 5)];
}
```

### CSS

```css
.pw-display{font-family:monospace;font-size:1.2rem;padding:.8rem;background:var(--surface-2);border-radius:8px;border:1px solid var(--border);text-align:center;word-break:break-all;user-select:all}
.pw-opt{display:flex;align-items:center;gap:.4rem;font-size:.85rem;cursor:pointer}
.pw-opt input{accent-color:var(--accent);width:16px;height:16px}
.pw-length input[type=range]{accent-color:var(--accent);height:4px}
.pw-strength-bar{height:6px;background:var(--surface-2);border-radius:3px;overflow:hidden}
.pw-strength-bar div{height:100%;border-radius:3px;transition:width .3s,background .3s;width:0}
```

---

## 27. Mini-Game CSS Animations (Dice / Coin)

CSS keyframe animation + class-swap technique với DOM reflow để restart animation.

### Dice shake

```css
.game-roll{animation:diceShake .3s ease}
@keyframes diceShake{
  0%{transform:rotate(0) scale(1)}
  25%{transform:rotate(90deg) scale(1.3)}
  50%{transform:rotate(180deg) scale(.9)}
  75%{transform:rotate(270deg) scale(1.2)}
  100%{transform:rotate(360deg) scale(1)}
}
```

### Coin flip

```css
.coin-flip{animation:coinFlip .4s ease}
@keyframes coinFlip{
  0%{transform:rotateY(0)}
  50%{transform:rotateY(720deg)}
  100%{transform:rotateY(0)}
}
```

### JS: restart animation via reflow

```javascript
function rollDice(){
  const r = Math.floor(Math.random() * 6) + 1;
  const dice = ['⚀','⚁','⚂','⚃','⚄','⚅'];
  const el = document.getElementById('dice-result');
  el.className = 'game-result';                              // reset
  void el.offsetWidth;                                       // force reflow
  el.className = 'game-result game-roll';                    // start animation
  setTimeout(() => {
    el.className = 'game-result';
    el.textContent = dice[r - 1];                            // set result after anim
  }, 300);
}
```

`void el.offsetWidth` triggers DOM reflow — required to restart CSS animation on the same element. Without it, adding the same class again does nothing.

### Unicode dice faces

```
⚀ ⚁ ⚂ ⚃ ⚄ ⚅
```

---

## 28. Gradient Generator (Random CSS)

Sinh linear/radial gradient ngẫu nhiên, hiển thị preview + CSS code copy.

### JS

```javascript
function randColor(){
  return '#' + Math.floor(Math.random() * 0xFFFFFF).toString(16).padStart(6, '0');
}

function genGradient(){
  const type = document.getElementById('grad-type').value;
  const c1 = randColor(), c2 = randColor();
  let css;
  if(type === 'linear'){
    const angle = Math.floor(Math.random() * 360);
    css = 'linear-gradient(' + angle + 'deg, ' + c1 + ', ' + c2 + ')';
  } else {
    css = 'radial-gradient(circle, ' + c1 + ', ' + c2 + ')';
  }
  document.getElementById('grad-preview').style.background = css;
  document.getElementById('grad-code').textContent = 'background: ' + css + ';';
}
```

### UI

```html
<div class="grad-preview" id="grad-preview"></div>
<div class="grad-code" id="grad-code">background: linear-gradient(135deg, #667eea, #764ba2);</div>
<select id="grad-type"><option value="linear">Linear</option><option value="radial">Radial</option></select>
```

```css
.grad-preview{height:200px;border-radius:12px;border:1px solid var(--glass-border);transition:background .3s}
.grad-code{background:var(--surface-2);padding:.8rem;border-radius:8px;font-family:monospace;font-size:.8rem;border:1px solid var(--border);word-break:break-all;user-select:all}
```

---

## 29. Copy-to-Clipboard + Toast Feedback

### copyText helper

```javascript
function copyText(text, msg){
  navigator.clipboard.writeText(text)
    .then(() => toast(msg || 'Đã copy!'))
    .catch(() => toast('Không thể copy', 'error'));
}
```

Dùng trong onclick inline: `onclick="copyText('#ff00ff', 'Đã copy màu')"` hoặc `onclick="copyText(document.getElementById('pw-output').textContent)"`.

### Toast (minimal, no undo)

```javascript
function toast(msg, type = 'success'){
  const c = document.getElementById('toast-container');
  const t = document.createElement('div'); t.className = 'toast ' + type;
  t.innerHTML = msg;
  c.appendChild(t);
  setTimeout(() => t.classList.add('removing'), 1500);
  setTimeout(() => t.remove(), 1700);
}
```

HTML: `<div id="toast-container" class="toast-container"></div>` before `</body>`.

Toast CSS defined in `global.css` and also in section 1 above.

### Pitfall

- `navigator.clipboard.writeText()` requires HTTPS (or localhost). Trên HTTP plain sẽ fail. Fallback: `document.execCommand('copy')` hoặc toast báo lỗi.
- Copy từ `.grad-code` và `.pw-display` — thêm `user-select:all` để user vẫn có thể copy thủ công nếu clipboard API fail.

---

## 30. Hash-Based Widget Grid → Detail Navigation

Thay thế tab-based navigation bằng grid view → detail view dùng hash routing. Phù hợp khi có 8+ widgets (tabs không scale).

### HTML structure

```html
<!-- Grid view (default) -->
<div id="grid-view">
  <div class="widget-grid" id="widget-grid"></div>
</div>

<!-- Detail view -->
<div id="detail-view">
  <div class="detail-header">
    <button class="back-btn" onclick="closeWidget()"><i class="fas fa-arrow-left"></i> Widgets</button>
    <span class="detail-title" id="detail-title"></span>
  </div>
  <div class="widget-panel" id="panel-8ball"><!-- widget content --></div>
  <div class="widget-panel" id="panel-cards"><!-- widget content --></div>
### Grid responsive

Desktop: `grid-template-columns:repeat(5,1fr)`. Mobile: `repeat(2,1fr)` (luôn 2 cột).

```css
.widget-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:1rem}
@media(max-width:768px){.widget-grid{grid-template-columns:repeat(2,1fr)}}
```

### Card badge absolute (không chiếm diện tích)

```css
.widget-card{position:relative}
.widget-card .card-title{padding-right:.5rem}
.widget-card .card-badge{position:absolute;top:8px;right:8px;font-size:.5rem;padding:.1rem .45rem;border-radius:10px;pointer-events:none}
```

### Card desc line-clamp (2 dòng)

```css
.widget-card .card-desc{font-size:.75rem;color:var(--text-dim);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
```

#grid-view,#detail-view{display:none}
#grid-view.active,#detail-view.active{display:block}
.detail-header{display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem;flex-wrap:wrap}
.back-btn{background:none;border:1px solid var(--glass-border);color:var(--text-dim);padding:.4rem .8rem;border-radius:8px;cursor:pointer;font-size:.8rem;display:flex;align-items:center;gap:.3rem}
.back-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.widget-panel{display:none}
```

### JS: widget registry + auto-grid

```javascript
const WIDGETS = [
  { id:'random', icon:'🎲', title:'Khám phá', desc:'...', cat:'Ngẫu nhiên', color:'#818cf8' },
  // add widgets here — grid auto-builds from this array
];

// Auto-generate grid
(function buildGrid(){
  document.getElementById('widget-grid').innerHTML = WIDGETS.map(w =>
    `<div class="widget-card" onclick="openWidget('${w.id}')">
      <div class="card-icon">${w.icon}</div>
      <div class="card-title">${w.title}</div>
      <div class="card-desc">${w.desc}</div>
      <span class="card-badge" style="background:${w.color}">${w.cat}</span>
    </div>`
  ).join('');
})();
```

### JS: navigation

```javascript
function initPage(){
  const hash = window.location.hash.slice(1);
  if(hash && WIDGETS.find(w => w.id === hash)) showDetail(hash);
  else showGrid();
}

function showGrid(){
  document.getElementById('grid-view').classList.add('active');
  document.getElementById('detail-view').classList.remove('active');
  window.location.hash = '';
}

function showDetail(id){
  document.getElementById('grid-view').classList.remove('active');
  document.getElementById('detail-view').classList.add('active');
  document.querySelectorAll('.widget-panel').forEach(p => p.style.display = 'none');
  const panel = document.getElementById('panel-'+id);
  if(panel) panel.style.display = 'block';
  const w = WIDGETS.find(x => x.id === id);
  if(w) document.getElementById('detail-title').textContent = w.icon+' '+w.title;
  // init widget
  if(id === 'colors') genPalette();
  if(id === 'password') genPassword();
  // ...
}

function openWidget(id){ window.location.hash = id; showDetail(id); }
function closeWidget(){ showGrid(); }

window.addEventListener('hashchange', () => {
  const hash = window.location.hash.slice(1);
  if(hash && WIDGETS.find(w => w.id === hash)) showDetail(hash);
  else showGrid();
});
```

### Pitfalls

- **Hash init must handle missing hash** — `showGrid()` fallback khi hash không match hoặc rỗng.
- **Panel show/hide** — dùng `.widget-panel{display:none}` + `style.display='block'`, không toggle class.
- **Widget init on every show** — gọi init function mỗi khi open widget. OK vì init function idempotent.
- **Memorize `_lastIdx` for pickers** — module-level var tránh trùng item liên tiếp.

---

## 31. Magic 8-Ball Widget

CSS 8-ball shape + triangle window + shake animation + 20 classic answers + Vietnamese translation below.

### HTML

```html
<div class="ball-shape" id="ball-shape" onclick="shakeBall()">
  <div class="ball-window">
    <div class="ball-triangle" id="ball-triangle"></div>
    <div class="ball-answer-text" id="ball-answer">YES</div>
  </div>
</div>
<div class="ball-answer-label" id="ball-answer-label"></div>
```

### CSS

```css
.ball-shape{position:relative;width:260px;height:260px;margin:.5rem auto;cursor:pointer;border-radius:50%;background:radial-gradient(circle at 35% 35%,#444,#111);box-shadow:0 8px 32px rgba(0,0,0,.5),inset 0 -6px 16px rgba(0,0,0,.4);user-select:none}
.ball-shape:active{transform:scale(.95)}
.ball-shake{animation:ballShake .45s ease}
@keyframes ballShake{0%{transform:rotate(0) scale(1)}20%{transform:rotate(-15deg) scale(1.04)}40%{transform:rotate(15deg) scale(1.01)}60%{transform:rotate(-10deg) scale(1.05)}80%{transform:rotate(10deg) scale(1.02)}100%{transform:rotate(0) scale(1)}}
.ball-window{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:100px;height:100px;border-radius:50%;background:radial-gradient(circle at 40% 30%,#1a237e,#0d1448);border:3px solid #999;display:flex;align-items:center;justify-content:center;overflow:hidden}
.ball-triangle{width:0;height:0;border-left:32px solid transparent;border-right:32px solid transparent;border-bottom:48px solid #e3f2fd;opacity:.9;transition:opacity .2s}
.ball-answer-text{position:absolute;font-size:.55rem;color:#e3f2fd;text-align:center;padding:4px 6px;line-height:1.3;opacity:0;transition:opacity .3s;font-weight:600}
.ball-answer-text.show{opacity:1}
.ball-answer-label{font-size:1.1rem;font-weight:600;text-align:center;min-height:2rem;margin:.5rem 0;color:var(--accent)}
```

### JS with Vietnamese translation

```javascript
const BALL_ANSWERS = [
  {t:'It is certain', v:'Chắc chắn rồi'},{t:'It is decidedly so', v:'Rõ ràng là vậy'},
  // ... 20 answers with vi translation
];
let _balling = false;
function shakeBall(){
  if(_balling) return;
  _balling = true;
  const shape = document.getElementById('ball-shape');
  const tri = document.getElementById('ball-triangle');
  const ans = document.getElementById('ball-answer');
  const label = document.getElementById('ball-answer-label');
  shape.className = 'ball-shape ball-shake';
  tri.style.opacity = '0';
  ans.className = 'ball-answer-text';
  label.textContent = '';
  setTimeout(() => {
    const a = BALL_ANSWERS[Math.floor(Math.random() * BALL_ANSWERS.length)];
    ans.textContent = a.t;
    ans.className = 'ball-answer-text show';
    label.innerHTML = '✨ '+a.t+'<br><span style="font-size:.85rem;opacity:.7">→ '+a.v+'</span>';
    shape.className = 'ball-shape';
    _balling = false;
  }, 450);
}
```

Answer text tiny (.42rem) → complaints from user. Fix: bigger ball 260px, bigger window 100px, font .55rem. Still hard to read in-ball → add `.ball-answer-label` below (1.1rem) with Vietnamese translation line.

---

## 32. Card Draw (52-card deck)

Fisher-Yates shuffle, staggered deal animation, mode toggle 1/5 cards.

```javascript
const SUITS = [{s:'♠',c:'black'},{s:'♥',c:'red'},{s:'♦',c:'red'},{s:'♣',c:'black'}];
const RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];

function drawCards(count = 1){
  const deck = [];
  SUITS.forEach(s => RANKS.forEach(r => deck.push({rank:r, suit:s.s, color:s.c})));
  for(let i = deck.length-1; i > 0; i--){
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  const cards = deck.slice(0, count);
  document.getElementById('card-area').innerHTML = cards.map(c =>
    `<div class="card ${c.color}" style="animation-delay:${Math.random() * 0.2}s">
      <div class="card-rank">${c.rank}</div><div class="card-suit">${c.suit}</div>
    </div>`
  ).join('');
}
```

CSS: `.card{animation:cardDeal .3s ease forwards;opacity:0}` with translateY(-50px) → translateY(0). Stagger via `animation-delay:${Math.random()*0.2}s`.

---

## 33. Pomodoro Timer

setInterval-based countdown with pause/resume, 3 modes (25/5/15 min), progress bar.

### Core: absolute end time

```javascript
let _pomoMinutes = 25, _pomoRemaining = 1500, _pomoRunning = false, _pomoInterval = null, _pomoEnd = null;

function pomoStart(){
  if(_pomoRunning){
    _pomoRunning = false; clearInterval(_pomoInterval); _pomoInterval = null;
    btn.innerHTML = '<i class="fas fa-play"></i> Tiếp tục';
    return;
  }
  _pomoRunning = true;
  _pomoEnd = Date.now() + _pomoRemaining * 1000;
  btn.innerHTML = '<i class="fas fa-pause"></i> Tạm dừng';
  _pomoInterval = setInterval(() => {
    const left = Math.max(0, Math.floor((_pomoEnd - Date.now()) / 1000));
    _pomoRemaining = left;
    display.textContent = padTime(Math.floor(left/60)) + ':' + padTime(left%60);
    bar.style.width = ((1 - left / (_pomoMinutes * 60)) * 100) + '%';
    if(left <= 0){ clearInterval(_pomoInterval); _pomoRunning = false;
      _pomoToday++; localStorage.setItem('pomo-sessions', _pomoToday);
      toast('🍅 Hết giờ!');
      try{ new AudioContext().createOscillator().connect(new AudioContext().destination).start() } catch(_){} }
  }, 200);
}
```

**Key:** `_pomoEnd = Date.now() + remaining * 1000` survives tab switches. **Beep** via Web Audio API oscillator. **Session count** saved to localStorage every 5s via separate interval.

---

## 34. Countdown Date Calculator

Input date picker → compute days/hours/min/sec → tabular-nums display.

```javascript
function calcCountdown(){
  const val = document.getElementById('cd-date').value;
  if(!val) return toast('Chọn ngày mục tiêu', 'error');
  const target = new Date(val + 'T23:59:59');
  const now = Date.now();
  if(target <= now) return toast('Ngày mục tiêu phải ở tương lai', 'error');
  const diff = target - now;
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  // render 4 boxes: Ngày / Giờ / Phút / Giây
}
```

No live tick (intentional — low CPU). User re-clicks to refresh.

---

## 35. Random List Tool

Textarea (one per line) → 3 modes: random pick, shuffle all, pick N.

```javascript
const items = textarea.value.trim().split('\n').map(s => s.trim()).filter(Boolean);
if(mode === 'random') result = items[Math.floor(Math.random() * items.length)];
else if(mode === 'shuffle'){
  // Fisher-Yates → join('\n')
} else { // pick N
  // shuffle → slice(0, N)
}
```

---

## 36. Embedded History Events (Today in History)

Array `{m, d, y, e}` events → filter by month+date for "today" or random pick.

```javascript
const EVENTS = [
  {m:1, d:1, y:1959, e:'Cách mạng Cuba thành công'},
  {m:4, d:30, y:1975, e:'Giải phóng miền Nam'},
  // 50+ events
];

function showHistory(mode){
  if(mode === 'today'){
    const now = new Date();
    const todayEvents = EVENTS.filter(x => x.m === now.getMonth()+1 && x.d === now.getDate());
    if(!todayEvents.length) return; // empty state
    e = todayEvents[Math.floor(Math.random() * todayEvents.length)];
  } else {
    e = EVENTS[Math.floor(Math.random() * EVENTS.length)];
  }
}
```

Date filter: `getMonth()+1` (1-indexed) matches embedded `m` field.

---

## 37. Emoji Mix

40 emojis, random pair, pop animation, avoid same pair consecutively.

```javascript
const EMOJIS = ['🦊','🔥','🌊','🌙','⭐','💀','👻','🤖','👽','🦄','🐉','🍕','🎸','🚀','🌈','💎','🧊','🍑','❤️','✨','🎯','🌀','🧩','🎲','🎪','🎭','🎤','🎧','🥁','🎮','🎰','🍄','🌵','🦋','🐙','🦩','🦦','🫶','🥷','🧙'];

function mixEmoji(){
  let e1, e2;
  do { e1 = EMOJIS[rand]; e2 = EMOJIS[rand]; } while(e1 === e2);
  display.innerHTML = `<span class="em-part">${e1}</span><span class="emoji-plus">+</span><span class="em-part">${e2}</span>`;
}
```

CSS: `.em-part{animation:emojiPop .35s ease}` pop-in scale from 0.

---

## 38. Random Challenge with Category Filters

24 challenges in 5 categories (thể-chất, kỹ-năng, sáng-tạo, xã-hội, tư-duy). Filter buttons generated from JS array.

```javascript
const CHALLENGES = [
  {t:'Hít đất 15 cái 💪', e:'🏋️', c:'thể-chất', bg:'#ef4444'},
  {t:'Nói 1 câu TA trong 30s 🗣️', e:'🗣️', c:'kỹ-năng', bg:'#f59e0b'},
  // ...
];
const CATS = ['tất-cả','thể-chất','kỹ-năng','sáng-tạo','xã-hội','tư-duy'];

// Generate filter buttons dynamically
(function initFilters(){
  document.getElementById('challenge-filters').innerHTML = CATS.map(c =>
    `<button class="${c==='tất-cả'?'active':''}" onclick="filterChallenge('${c}')">${LABELS[c]}</button>`
  ).join('');
})();
```

Filter: pool = active filter === 'tất-cả' ? all : CHALLENGES.filter(c => c.c === filter).

---

## 39. Text Generator (Lorem / Names / Words)

4 types: Lorem Ipsum (EN words shuffled), Vietnamese words, Vietnamese names, Lorem Ipsum VI (lorem-ified Vietnamese sentences). Quantity slider 1-50.

```javascript
function genText(){
  const type = document.getElementById('tgen-type').value;
  const amt = parseInt(document.getElementById('tgen-amount').value) || 3;
  if(type === 'lorem'){
    // shuffle LOREM_WORDS, pick amt*30, join
  } else if(type === 'words'){
    // pick from WORDS_VI array
  } else if(type === 'names'){
    // shuffle NAMES_VI, slice(0, amt)
  } else if(type === 'ipsum-vi'){
    // pick from LOREM_VI sentences
  }
  output.textContent = result;
}
```

Data arrays: `LOREM_WORDS` (split from classic lorem), `WORDS_VI` (~20 Vietnamese words), `NAMES_VI` (20 Vietnamese full names), `LOREM_VI` (custom VI sentences).

---

## 40. Workout Random

18 exercises with name, emoji, detail (sets×reps), target muscle group, color badge.

```javascript
const WORKOUTS = [
  {n:'Hít đất', e:'💪', d:'4 × 12 reps', t:'Ngực, tay sau', bg:'#ef4444'},
  {n:'Plank', e:'🧘', d:'3 × 30 giây', t:'Core', bg:'#f59e0b'},
  // ...
];

function randomWorkout(){
  const w = WORKOUTS[Math.floor(Math.random() * WORKOUTS.length)];
  // render emoji, name, detail, target with styled badge
}
```

## 41. Global Category Filter Bar on Grid Hub

Auto-generated from WIDGETS array categories. Shows "📦 Tất cả" as default active. Each button filters grid cards by `data-cat` attribute.

### CSS

```css
.filter-bar{display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:1rem;justify-content:center}
.filter-btn{font-size:.7rem;padding:.25rem .65rem;border-radius:20px;border:1px solid var(--glass-border);background:var(--glass-bg);color:var(--text-dim);cursor:pointer;transition:.15s;font-weight:500;white-space:nowrap}
.filter-btn:hover{background:rgba(255,255,255,.08);color:var(--text)}
.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
```

### HTML

```html
<div class="filter-bar" id="filter-bar"></div>
<div class="widget-grid" id="widget-grid"></div>
```

### JS: filter generation + auto-grid with data-cat

```javascript
(function buildGrid(){
  const grid=document.getElementById('widget-grid');
  grid.innerHTML=WIDGETS.map(w=>
    '<div class="widget-card" data-cat="'+w.cat+'" onclick="openWidget(\''+w.id+'\')">'+
      '<div class="card-icon">'+w.icon+'</div>'+
      '<div class="card-title">'+w.title+'</div>'+
      '<div class="card-desc">'+w.desc+'</div>'+
      '<span class="card-badge" style="background:'+w.color+'">'+w.cat+'</span>'+
    '</div>'
  ).join('');
  const cats=[...new Set(WIDGETS.map(w=>w.cat))].sort();
  document.getElementById('filter-bar').innerHTML='<button class="filter-btn active" data-cat="all" onclick="filterGrid(\'all\')">📦 Tất cả</button>'+
    cats.map(c=>'<button class="filter-btn" data-cat="'+c+'" onclick="filterGrid(\''+c+'\')">'+c+'</button>').join('');
})();

function filterGrid(cat){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===cat));
  document.querySelectorAll('.widget-card').forEach(c=>c.style.display=(cat==='all'||c.dataset.cat===cat)?'':'none');
}
```

Key: `data-cat` on cards + buttons, `filterGrid('all')` shows everything, buttons styled as pill shapes.

---

## 42. Tarot Card 3D Flip (CSS perspective + rotateY)

3D card flip with backface-visibility. Two faces: back (repeating-diamond pattern + star) and front (gradient + card data).

### CSS

```css
.tarot-card{width:150px;height:220px;margin:.5rem auto;border-radius:10px;position:relative;cursor:pointer;perspective:600px}
.tarot-inner{width:100%;height:100%;border-radius:10px;transition:transform .35s;transform-style:preserve-3d;position:relative}
.tarot-card.flip .tarot-inner{transform:rotateY(180deg)}
.tarot-back,.tarot-front{position:absolute;inset:0;border-radius:10px;backface-visibility:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center}
.tarot-back{background:repeating-linear-gradient(45deg,#4a1942,#4a1942 10px,#381430 10px,#381430 20px);border:2px solid #c9a84c}
.tarot-front{background:linear-gradient(135deg,#1a1a2e,#16213e);transform:rotateY(180deg);border:2px solid #c9a84c;padding:.4rem}
```

### JS: toggle flip and reset

```javascript
const TAROT = [
  {n:'The Fool',e:'🤡',v:'Kẻ Ngốc',m:'Khởi đầu mới, cơ hội, hãy mạo hiểm!'},
  // 22 major arcana...
];
let _tarotI=-1;

function tarotNew(){
  _tarotI=Math.floor(Math.random()*TAROT.length);
  const c=TAROT[_tarotI];
  document.getElementById('tarot-card').className='tarot-card';     // force flip back
  document.getElementById('tf-emoji').textContent=c.e;
  document.getElementById('tf-name').textContent=c.n;
  document.getElementById('tf-vi').textContent=c.v;
  document.getElementById('tarot-meaning').textContent='☝️ Bấm lật bài!';
}

function tarotFlip(){
  const card=document.getElementById('tarot-card');
  card.classList.toggle('flip');
  document.getElementById('tarot-meaning').textContent=card.classList.contains('flip')
    ? TAROT[_tarotI].m : '☝️ Bấm lật bài!';
}
```

Key: `.tarot-card.flip .tarot-inner{transform:rotateY(180deg)}` — toggle class on container, inner element rotates. Both `.tarot-back` and `.tarot-front` have `backface-visibility:hidden`. Front is pre-rotated `rotateY(180deg)` so flip reveals it.

---

## 43. Mood Tracker (daily localStorage + 7-day history)

6 emoji mood options. Save by date (ISO key). Render last 7 days as colored dots. Data persists across sessions.

### Data

```javascript
const MOODS = [
  {e:'😊', l:'Vui', c:'#22c55e'},
  {e:'😐', l:'B/thường', c:'#f59e0b'},
  {e:'😢', l:'Buồn', c:'#818cf8'},
  {e:'😡', l:'Giận', c:'#ef4444'},
  {e:'😴', l:'Mệt', c:'#a855f7'},
  {e:'🥰', l:'Yêu', c:'#f472b6'},
];
```

### JS: save + render

```javascript
function moodSet(i){
  MOODS.forEach((_,j)=>document.getElementById('mb-'+j).classList.toggle('on',j===i));
  const t=new Date().toISOString().split('T')[0];
  localStorage.setItem('md', JSON.stringify({...JSON.parse(localStorage.getItem('md')||'{}'), [t]: i}));
  moodRender();
}

function moodRender(){
  let data = JSON.parse(localStorage.getItem('md') || '{}');
  const today = new Date();
  let html = '';
  for(let i=6;i>=0;i--){
    const d = new Date(today); d.setDate(d.getDate()-i);
    const key = d.toISOString().split('T')[0];
    const idx = data[key];
    html += '<div class="mood-hd"><div class="mh-lb">'+(i===0?'⭐':['CN','T2','T3','T4','T5','T6','T7'][d.getDay()])+'</div>'+
      (idx!==undefined ? '<div class="mh-dot" style="background:'+MOODS[idx].c+'">'+MOODS[idx].e+'</div>' : '<div class="mh-non"></div>')+
    '</div>';
  }
  document.getElementById('mood-hist').innerHTML = html;
}
```

Key: ISO date `split('T')[0]` as localStorage key. 7-day history iterates from 6 days ago to today. `mh-non` = no data dot. Auto-restore today's selection on render.

---

## 44. Calendar Month Grid (Date API)

Generate month calendar with proper padding for prev/next month days. Highlight today.

### JS

```javascript
const CAL_H=['T2','T3','T4','T5','T6','T7','CN'];
let _calD=new Date();

function calRender(){
  const y=_calD.getFullYear(), m=_calD.getMonth();
  const fd=(new Date(y,m,1).getDay()+6)%7;  // Mon=0
  const days=new Date(y,m+1,0).getDate();
  const prevDays=new Date(y,m,0).getDate();
  const today=new Date();
  let h=CAL_H.map(d=>'<div class="cal-cell hd">'+d+'</div>').join('');
  for(let i=fd-1;i>=0;i--) h+='<div class="cal-cell om">'+(prevDays-i)+'</div>';
  for(let d=1;d<=days;d++){
    const isT=d===today.getDate()&&m===today.getMonth()&&y===today.getFullYear();
    h+='<div class="cal-cell'+(isT?' today':'')+'">'+d+'</div>';
  }
  const rem=7-((fd+days)%7); if(rem<7) for(let d=1;d<=rem;d++) h+='<div class="cal-cell om">'+d+'</div>';
  document.getElementById('cal-grid').innerHTML = h;
}
function calMove(n){_calD.setMonth(_calD.getMonth()+n);calRender()}
```

Key: `(getDay()+6)%7` converts JS Sunday=0 → Monday=0. `.cal-cell.today` gets accent background + 50% circle. Prev/next cells get `.om` (opacity .35). Left/right arrows call `calMove(±1)`.

---

## 45. Unit Converter (conversion factors map)

Central conversion factor map relative to SI base unit. Build unit selectors dynamically per category.

### Data structure

```javascript
const UC = {
  temp:{
    u:[{i:'c',n:'°C'},{i:'f',n:'°F'},{i:'k',n:'K'}],
    c:(v,f,t)=>{let c; if(f==='c')c=v; else if(f==='f')c=(v-32)*5/9; else c=v-273.15;
      if(t==='c')return c; if(t==='f')return c*9/5+32; return c+273.15}
  },
  length:{
    u:[{i:'mm',n:'mm'},{i:'cm',n:'cm'},{i:'m',n:'m'},{i:'km',n:'km'},{i:'in',n:'inch'},{i:'ft',n:'ft'}],
    c:(v,f,t)=>{const m={mm:.001,cm:.01,m:1,km:1e3,in:.0254,ft:.3048}; return v*m[f]/m[t]}
  },
  weight:{
    u:[{i:'g',n:'g'},{i:'kg',n:'kg'},{i:'t',n:'tấn'},{i:'lb',n:'lbs'}],
    c:(v,f,t)=>{const m={g:1,kg:1e3,t:1e6,lb:453.592}; return v*m[f]/m[t]}
  },
};
```

### JS: conversion + dynamic unit selectors

```javascript
function ucConvert(){
  const t=document.getElementById('uc-type').value, d=UC[t];
  const fs=document.getElementById('uc-from'), ts=document.getElementById('uc-to');
  if(!fs.options[0]||fs.options[0].value!==d.u[0].i){
    const b=(s,di)=>{ s.innerHTML = d.u.map((u,i)=>'<option value="'+u.i+'"'+(i===di?' selected':'')+'>'+u.n+'</option>').join(''); };
    b(fs,0); b(ts,Math.min(1,d.u.length-1));
  }
  const v=parseFloat(document.getElementById('uc-in').value)||0;
  document.getElementById('uc-res').textContent = d.c(v,fs.value,ts.value).toFixed(4).replace(/\.?0+$/,'')||'0';
}
```

Key: Category change rebuilds both unit `<select>` (source=first unit, target=second). Conversion factor map = `value * m[from] / m[to]` — no per-pair formulas. Temperature uses branch logic since °C/°F/K is non-linear.

---

## 46. Shared Component via Fetch + Template

Share navbar/footer across multi-page vanilla JS app — no build step, no server template. See `references/shared-navbar-pattern.md` for full code.

### Principle
1. `navbar.html` — single file with `{BREADCRUMB}`, `{EXTRA}`, `{THEME_ICON}` placeholders
2. Each page has `<template id="nav-extra" data-bc="/ widget">` with per-page nav links + breadcrumb config
3. Inline `<script>` fetches navbar.html, replaces placeholders from template, injects into `<div id="nav-target">`

### Key rules
- **Spacer stays in page HTML**, not in component file (prevents layout flash before fetch resolves)
- **Re-attach scroll listener** after DOM injection (theme.js runs before fetch completes)
- **Theme icon** calculated from localStorage at injection time, not from theme.js init
- Active link marked with `has-text-link` class in per-page template
- Dashboard-style pages with extra items (running/stopped counts, button links) put those in `{EXTRA}`

---

## 47. Fullscreen Canvas Visualizer UI

Full-screen Canvas-based interactive visualizer integrated with Bulma glass navbar — auto-hide navbar, mode panel bottom sheet, touch interaction guards, consistent theme.

### Navbar: auto-hide (scroll-independent)

Fullscreen canvas pages have no scrolling. Navbar auto-hide must be timer-based, not scroll-based:

```css
.navbar.is-glass.hidden{transform:translateY(-100%)}
```

```javascript
// Desktop: show near top edge, auto-hide after idle
let navVisible=true, navHideTimer;
function showNavbar(){nav.classList.remove('hidden');navVisible=true;clearTimeout(navHideTimer);navHideTimer=setTimeout(()=>{nav.classList.add('hidden');navVisible=false},5000)}
document.addEventListener('mousemove',e=>{if(e.clientY<60&&!navVisible)showNavbar()},{passive:true});
document.addEventListener('touchstart',e=>{if(e.touches[0].clientY<80)showNavbar()},{passive:true});
showNavbar(); // start visible, auto-hide after 5s
```

### Canvas layer z-index protocol

| Layer | z-index | Element | Pointer |
|-------|---------|---------|---------|
| Trail | 1 | #trailCanvas | none |
| Main canvas | 2 | #c | crosshair |
| Bloom | 3 | #bloom | none |
| Storm overlay | 4 | #storm-overlay | none |
| Storm flash | 5 | #storm-flash | none |
| Scene transition | 6 | #trans-overlay | none |
| Hint / Constellation | 5 | #hint, #constellation | none |
| Mode badge / Gravity | 5 | #mode-badge, #gravity-indicator | none |
| HUD | 10 | #hud | auto |
| Palette / Vol toggle | 10 | #palette-indicator, #vol-toggle | auto |
| Paint controls | 15 | #paint-controls | auto |
| Mode config | 19 | #mode-config | auto |
| Mode panel | 20 | #mode-panel | auto |
| Panel toggle | 21 | #mode-panel-toggle | auto |
| Config button | 22 | #cfg-btn | auto |
| Snapshot toast | 30 | #snapshot-toast | none |
| Help overlay | 50 | #help-overlay | auto |
| Word modal | 60 | #word-modal | auto |
| Splash | 100 | #splash | auto |
| Navbar | 500 | .navbar | auto |

### Touch interaction guards

Prevent canvas visualizer effects (explosion, gravity well, paint) when user touches UI elements:

```javascript
addEventListener('touchstart', e => {
  const target = e.target;
  if(target.closest('#mode-panel') || target.closest('#mode-config') ||
     target.closest('#paint-controls') || target.closest('#help-overlay') ||
     target.closest('#word-modal') || target.closest('#vol-toggle') ||
     target.closest('#cfg-btn') || target.closest('#hud') ||
     target.closest('#palette-indicator') || target.closest('#back-site') ||
     target.closest('.navbar') || target.closest('#mode-panel-toggle') ||
     target.closest('#snapshot-toast')) return;
  // proceed with canvas interaction
}, {passive:true});
```

Also guard the `click` handler with `document.activeElement.closest(...)` check.

### Mode panel: Mobile bottom sheet

Desktop = sidebar left. Mobile (<768px) = bottom sheet with drag handle:

```css
#mode-panel{position:fixed;left:16px;top:50%;transform:translateY(-50%);flex-direction:column;gap:4px}
@media(max-width:768px){
  #mode-panel{left:0;right:0;bottom:0;top:auto;
    transform:translateY(calc(100% - 38px));
    flex-direction:row;flex-wrap:wrap;gap:2px;padding:8px 6px calc(env(safe-area-inset-bottom,0)+6px);
    border-radius:16px 16px 0 0;max-height:55vh;overflow-y:auto;
    transition:transform .35s cubic-bezier(.4,0,.2,1)}
  #mode-panel .panel-handle{display:block;width:32px;height:4px;border-radius:2px;background:rgba(200,220,255,.15);margin:0 auto 6px}
  #mode-panel.visible{transform:translateY(0)}
  .mode-btn{flex:1 1 31%;min-width:68px;padding:5px 4px;font-size:10px;justify-content:center}
}
```

### HUD: Fixed bottom bar

```css
#hud{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:var(--glass-bg);border:1px solid var(--glass-border);
  border-radius:12px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
  padding:7px 14px;font-size:11px;white-space:nowrap}
#hud.hidden{opacity:0;transform:translateX(-50%) translateY(16px);pointer-events:none}
@media(max-width:480px){
  #hud{bottom:8px;font-size:10px;padding:5px 10px;max-width:96vw;overflow-x:auto}
  .hud-div,#scene-name,#palette-name{display:none}
}
```

### Paint controls: Responsive

```css
@media(max-width:480px){
  #paint-controls{bottom:68px;padding:8px 12px;gap:6px;width:94%;flex-wrap:wrap;justify-content:center}
  #paint-controls input[type=range]{width:55px}
}
```

### Config panel: Mobile bottom sheet

```css
@media(max-width:768px){
  #mode-config{left:8px;right:8px;top:auto;bottom:60px;transform:translateY(120%);
    flex-direction:row;flex-wrap:wrap;padding:10px 14px;min-width:auto;
    border-radius:14px;max-height:45vh}
  #mode-config.open{transform:translateY(0)}
  #cfg-btn{left:12px;bottom:62px}
}
```

### Theme integration

```html
<script src="/assets/theme.js"></script>
```
Navbar uses `{THEME_ICON}` placeholder. Toggle button inline: `onclick="toggleTheme()"`.

### Splash screen

```html
<div id="splash">
  <svg><!-- rotating circles --></svg>
  <div class="splash-sub">hermes</div>
</div>
```
```javascript
setTimeout(()=>document.getElementById('splash').classList.add('fade'),600);
```
CSS: `#splash{position:fixed;inset:0;z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#05060f;transition:opacity 1.2s ease}`

### Back to site button (mobile)

```html
<a id="back-site" href="/" title="Back to site"><i class="fas fa-arrow-left"></i></a>
```
```css
#back-site{position:fixed;top:8px;left:8px;z-index:501;display:none;
  width:32px;height:32px;border-radius:8px;background:var(--glass-bg);border:1px solid var(--glass-border)}
@media(max-width:768px){#back-site{display:flex;top:50px;width:30px;height:30px;font-size:12px}}
```

### Safe area for modern mobile

```css
padding:8px 6px calc(env(safe-area-inset-bottom,0)+6px);
```

### Pitfalls

- **No scroll-based nav hiding** — canvas fullscreen pages have no scroll. Use timer-based auto-hide triggered by mouse near top edge.
- **Touch enter events fire explosions on UI** — ALL canvas touch handlers must guard against UI elements using `e.target.closest('#ui-element')` check.
- **`backdrop-filter` must include `-webkit-backdrop-filter`** — Firefox and older Chrome need both prefixes.
- **`env(safe-area-inset-bottom)`** — always include fallback via `calc(env(safe-area-inset-bottom,0)+Xpx)`.
- **HUD mobile width** — cap at `max-width:96vw` + `overflow-x:auto`.
- **Splash z-index** — must be higher than all other layers (100+). `.fade` adds `pointer-events:none`.
- **Config panel text input** — keyboard pushes bottom-fixed elements. Config panel uses `bottom:60px` + `max-height:45vh`.

---

## React Multi-Page UI Consistency Audit

When user says "giao diện xấu với loạn" across multiple React pages, run `references/react-ui-consistency-audit.md` first — a 5-minute automated audit that quantifies glass-token usage, inline-style count, CSS isolation, and duplicate rendering. Produces a fix order: (1) remove duplicates (2) drop per-page CSS files (3) split monoliths (4) unify spacing.

## Session History

- `references/taste-skill-integration.md` — Taste Skill (tasteskill.dev) integration guide: audit checklist, 8-group diagnosis, font/color/layout rules, Glassmorphism done right, z-index scale, fix priority order (July 2026)
- `references/react-ui-consistency-audit.md` — 5-minute audit: CSS variable counts, double-rendering detection, HomePage→glass migration pattern (July 2026)
- `references/react-mobile-ux-patterns.md` — Touch ripple, skeleton loading, pull-to-refresh, swipe-to-dismiss hooks for React. **Font/color changes invisible; touch interactions create real difference.** (July 2026)
- `references/random-widget-july-2026.md` — 28-widget page architecture, hash-based grid→detail navigation, category filter bar, all widget patterns (v2+v3+v4)
- `references/react-widget-architecture.md` — React 19/Vite 6 port of the widget page: inline-style glassmorphism components, dynamic component registry, 11 widget patterns (DiceRoller, CoinFlip, NumberGen, PasswordGen, ColorPalette, GradientGen, RandomDiscovery, ActivitySuggester, Magic8Ball, BrainDump, MiniGames), build verification checklist
- `references/ux-fixes-july-2026.md` — full pattern code from this session (confirm modal, SSE reconnect, empty state, loading spinner, theme icon init, layout utilities)
- `references/shared-navbar-pattern.md` — fetch-based shared navbar across 4 pages, per-page config via `<template>` tags
- `references/react-mobile-navbar.md` — React hamburger navbar pattern: animated X icon, overlay, slide-down panel, body scroll lock, active dot indicator, responsive breakpoints
- `references/july-2026-dashboard-redesign.md` — full dashboard v2 CSS+HTML+JS (stats bar, .svc-card, glass log panel, skeleton loader, inline actions)
- `references/july-2026-hermes-visualizer.md` — fullscreen canvas visualizer page structure, CSS architecture, touch guards, mode panel bottom sheet
- `references/react-prop-mismatch-debugging.md` — React component prop mismatch silent crash: component con được rewrite nhưng cha vẫn truyền props cũ → ErrorBoundary. Debug bằng so sánh signature vs call site, build bundle check. Checklist deploy sau fix.

## Pitfalls

- **Skeleton chỉ lần đầu** — auto-refresh setInterval, show skeleton mỗi lần → flicker. Dùng `_firstLoad` flag. Lần đầu skeleton, các lần sau render inline.
- **Duplicate component rendering** — when `AppLayout` renders `<Footer />` but `HomePage` also has `<footer className="home-footer">` inline, two footers overlap. Always check: does the shared layout already provide this component? Grep the layout + every page before adding shared chrome.
- **Per-page CSS files break consistency** — `import './home/home.css'` in one page creates an isolated visual language. The other pages use inline `style={{}}` + shared `components.css`. Result: each page looks like a different site. Migrate per-page CSS to inline styles + shared class names (`card`, `btn`, `glass-panel`).
- **Manual refresh > auto-poll** — bỏ setInterval. Thêm nút ↻ stats bar. User thích kiểm soát.
- **Dashboard stats/layout padding** — `padding:0 .5rem` trên `.dash-stats` và `.dash-layout`. Ko dùng margin.
- **Detail view animation** — `.detail-view-wrap{animation:fadeUp .3s ease}` thay `display:none` trần. Widget panel dùng `.classList.add('active')` với `display:block` trên `.widget-panel.active`.
- **Full-screen overlays** — user complaint ngay. Content page + full-screen overlay = broken UX. Luôn dùng tooltip/compact widget (section 9).
- **Skip-to-content link** — user thấy xấu, skip nó. Chỉ dùng cho form-heavy pages.
- **View Transitions snapshot ghost** — `@view-transition{navigation:auto}` snapshot DOM cũ → crossfade. Nếu xoá element giữa trang, element cũ vẫn hiện. Xoá view-transition CSS.
- **Keyboard help trigger `?`** — check `e.target.tagName` để ko intercept khi gõ trong input.
- **Toast auto-dismiss** — 4s sweet spot. Kèm undo button cho destructive actions.
- **Reading progress bar** — reset về 0 khi load doc mới, transition width `.1s linear`.
- **Search debounce** — 300ms, cache query.
- **Server restart** — verify port free + curl health check sau restart.
- **CSS class rename** — search cả `@media print{}` blocks, inline HTML, global.css.
- **SW anti-pattern** — project ko cần PWA. Xoá `sw.js`, manifest, SW registration.
