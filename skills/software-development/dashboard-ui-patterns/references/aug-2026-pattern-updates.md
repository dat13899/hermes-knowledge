# UI Pattern Updates — Aug 2026

## No Auto-Poll / Manual Refresh

User hates flicker from setInterval polling. Pattern:

```javascript
let _firstLoad = true;
async function loadData(){
  if(_firstLoad) { showSkeleton(); _firstLoad = false; }
  try { const r = await fetch('/api/...'); render(await r.json()); hideSkeleton(); }
  catch(e) { hideSkeleton(); }
}
loadData(); // once on init
// Refresh button: <button onclick="loadData();">↻</button>
```

No `setInterval(fn, N)`. Skeleton only shows first load — subsequent refreshes render inline, no flicker.

## Container Spacing

Layout sát viền → thêm padding:

```css
.main-wrap{max-width:1200px;margin:0 auto;padding:0 .75rem}
```

Hoặc trên layout container:
```css
.dash-layout{height:calc(100vh - 100px);padding:0 .5rem}
.dash-stats{padding:0 .5rem}
```

## Detail View Transition

```css
.detail-view-wrap{display:none;animation:fadeUp .3s ease}
.detail-view-wrap.active{display:block}
@keyframes fadeUp{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}
```

JS: `classList.add/remove('active')` thay `style.display='block'`.

## Widget Grid Improvements

```css
.widget-grid{grid-template-columns:repeat(5,1fr);gap:.75rem}
@media(max-width:768px){.widget-grid{grid-template-columns:repeat(2,1fr);gap:.5rem}}
.widget-card{border-radius:14px;padding:1.25rem .6rem;transition:transform .2s,box-shadow .2s,border-color .2s}
.widget-card:hover{transform:translateY(-4px) scale(1.015);border-color:var(--accent)}
```

- Smaller padding (1.25rem .6rem vs 1.5rem .8rem)
- Border accent on hover (not just shadow)
- Smaller gap (1rem → .75rem)
- Gradient title: `background:linear-gradient(135deg,var(--text-strong),var(--accent));-webkit-background-clip:text`

## Empty State Pattern

Dùng `.svc-card` wrapper, ko dùng `.card.glass-card` riêng:

```html
<div class="svc-card"><div class="svc-top" style="justify-content:center;padding:2rem">
  <span class="has-text-grey-light"><small>Chưa có gì. Bấm + để thêm.</small></span>
</div></div>
```

## Stats Bar (4 glass cards)

```css
.dash-stats{display:flex;gap:.6rem;margin-bottom:.8rem;flex-wrap:wrap;padding:0 .5rem}
.dash-stat{flex:1;min-width:100px;text-align:center;border-radius:12px;padding:.5rem 1rem;box-shadow:0 4px 16px var(--glass-shadow);transition:.2s}
.dash-stat:hover{transform:translateY(-2px)}
.dash-stat .stat-num{font-size:1.25rem;font-weight:700}
.dash-stat .stat-label{font-size:.65rem;text-transform:uppercase;color:var(--text-dim)}
.stat-green .stat-num{color:var(--green)}
.stat-gray .stat-num{color:var(--text-dim)}
.stat-red .stat-num{color:var(--red)}
.stat-blue .stat-num{color:var(--accent)}
```

JS: `$('stat-running').textContent=run` (textContent, ko innerHTML).

## Log Panel Architecture

```html
<div class="log-panel">
  <div class="log-header">
    <span class="log-title">📋 Logs</span>
    <select id="log-select"></select>
    <div class="log-actions">
      <button onclick="clearLogs()" title="Clear">🧹</button>
      <button onclick="toggleAutoScroll()">⬇</button>
    </div>
    <span class="log-status" id="log-status"></span>
  </div>
  <div id="log-box"></div>
</div>
```

```css
.log-panel{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
.log-header{display:flex;align-items:center;gap:.4rem;padding:.5rem .75rem;border-bottom:1px solid var(--glass-border)}
```

## Service Card Compact (.svc-card)

```css
.svc-card{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:12px;overflow:hidden;margin-bottom:.5rem;transition:.2s}
.svc-card:hover{border-color:var(--accent)}
.svc-card .svc-top{display:flex;align-items:center;gap:.5rem;padding:.65rem .75rem;cursor:pointer}
.svc-card .svc-name{flex:1;font-size:.85rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.svc-card .svc-port{font-size:.65rem;padding:.15rem .5rem;border-radius:6px;background:var(--surface-2);border:1px solid var(--glass-border);color:var(--text-dim);text-decoration:none}
.svc-card .svc-meta{font-size:.7rem;color:var(--text-dim);display:flex;gap:.3rem}
.svc-card .svc-actions{display:flex;gap:2px;padding:.35rem .75rem;border-top:1px solid var(--glass-border)}
.svc-card .svc-actions button{background:none;border:none;color:var(--text-dim);font-size:.7rem;padding:.2rem .5rem;border-radius:6px;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:3px}
.svc-card .svc-actions button:disabled{opacity:.3;cursor:not-allowed}
.svc-card .svc-actions .act-start:hover{color:var(--green)}
.svc-card .svc-actions .act-stop:hover{color:var(--red)}
.svc-card .svc-actions .act-restart:hover{color:var(--accent)}
.svc-card .svc-actions .act-logs{color:var(--accent)}
.svc-card .svc-actions .act-del:hover{color:var(--red)}
.svc-card .svc-bar{height:3px;background:var(--border);overflow:hidden}
.svc-card .svc-bar .fill{height:100%;background:var(--green);transition:width 1s}
.svc-card .svc-details{display:none;padding:.4rem .75rem .6rem;border-top:1px solid var(--glass-border);font-size:.7rem;gap:.5rem;flex-wrap:wrap}
.svc-card.expanded .svc-details{display:flex}
.svc-card .svc-chart{height:18px;background:var(--surface-2);border-radius:3px;overflow:hidden;display:flex;gap:1px;padding:1px;margin:.3rem .75rem .5rem}
```

## Auto-restart badge

```css
.svc-card .auto-restart-badge{font-size:.6rem;padding:.1rem .4rem;border-radius:4px;background:rgba(245,158,11,.15);color:var(--amber)}
```

## Mobile col-header — single row

KHÔNG tách running/stopped counters thành row riêng. Gộp với Services title:

```html
<div class="level col-header">
  <div class="level-left">
    <h2 class="title is-5">📦 Services</h2>
    <span id="running-count" class="tag is-success is-light">...</span>
    <span id="stopped-count" class="tag">...</span>
  </div>
  <div class="level-right"><button onclick="toggleLayout()">⊞</button></div>
</div>
```

CSS:
```css
.col-header{flex-wrap:wrap;gap:.4rem}
@media(max-width:768px){.col-header{display:flex!important;flex-direction:row!important;justify-content:flex-start!important;flex-wrap:wrap}}
```
