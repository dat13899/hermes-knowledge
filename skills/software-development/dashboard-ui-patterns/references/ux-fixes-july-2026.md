# This session's UX fixes (July 2026)

Patterns added during this session. All live at btdat.io.vn.

## Layout utilities (global.css)
```css
.max-w-article{max-width:min(90vw,900px);margin:0 auto}
.max-w-hero{max-width:min(90vw,650px);margin:0 auto}
.gap-sm{gap:.3rem}.gap-md{gap:.5rem}.gap-lg{gap:1rem}
.text-center{text-align:center}
```

## Theme button (global.css)
```css
.theme-btn{position:fixed;bottom:1rem;left:1rem;z-index:9997;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:1rem;padding:.25rem .35rem;line-height:1;box-shadow:0 2px 8px rgba(0,0,0,.2)}
```

## Theme icon init (theme.js)
Dark → ☀️, Light → 🌙. Must call after setting `data-theme`:
```javascript
function init(){
  const h=document.documentElement;
  let s=localStorage.getItem(KEY);
  if(!s){s=window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark';localStorage.setItem(KEY,s)}
  h.setAttribute('data-theme',s);
  updateIcons(s);
}
function updateIcons(s){const n=s||document.documentElement.getAttribute('data-theme');document.querySelectorAll('.theme-btn-icon').forEach(e=>{e.textContent=n==='light'?'🌙':'☀️'})}
```

## Confirm modal (shared 3 pages)

Replace browser `confirm()` with Bulma modal:

```
HTML: modal#confirm-modal with .modal-card, .modal-background, #confirm-msg, #confirm-btn
```

```javascript
function showConfirm(msg,onConfirm){
  $('confirm-msg').innerHTML=msg;$('confirm-btn').onclick=()=>{closeConfirm();if(onConfirm)onConfirm()};
  $('confirm-modal').classList.add('is-active');
}
function closeConfirm(){$('confirm-modal').classList.remove('is-active')}
```

## SSE with crash alerts (dashboard v3.1)
Log EventSource listens for `alert` event type too:
```javascript
logEventSource.addEventListener('alert', function(e){
  try{const d=JSON.parse(e.data); addAlert(d.msg||'Service crashed')}catch(_){}
});
```
Alert badge: fixed top-right red bubble. On click, show dropdown with alert list.

## SSE reconnect handler
```javascript
logEventSource.onerror=function(){
  logEventSource.close();sseRetries++;
  if(sseRetries<5)setTimeout(()=>connectSSE(logSvcId),3000*Math.min(sseRetries,3));
  else $('log-status').textContent='⚠️ disconnected';
};
```

## Tab-based panel UI
Horizontal tab bar with `.panel / .active` toggle:
```javascript
function switchTab(name){
  document.querySelectorAll('.tab-bar button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+name));
}
```
Panels: Services, Resources (CPU/RAM), Ports (unknown listening), Files (browser).

## Empty state
Show message, not skeleton, when fetch returns empty list.

## Loading spinner on submit
```javascript
btn.disabled=true; btn.innerHTML='<span class="spinner"></span>';
// await...
finally{btn.disabled=false; btn.innerHTML='Original text'}
```

## Service search/filter
```javascript
function filterSvcs(){
  const q=searchInput.value.toLowerCase();
  document.querySelectorAll('.card-expandable').forEach(c=>{
    c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
  });
}
```

## Hardcoded px → responsive
- Landing max-widths: `max-w-hero` = `min(90vw, 650px)`, `max-w-article` = `min(90vw, 900px)`
- Dashboard log panel: `width:clamp(280px,30vw,480px)` (was 380px fixed)
- Dashboard media query: 960px breakpoint (kept — breakpoint, not layout px)
