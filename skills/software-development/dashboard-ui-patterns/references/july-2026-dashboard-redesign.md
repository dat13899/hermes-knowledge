# Dashboard Redesign (July 2026)

## Stats Bar (replaces .level col-header)

```html
<div class="dash-stats">
  <div class="dash-stat stat-green"><div class="stat-num" id="stat-running">0</div><div class="stat-label">Running</div></div>
  <div class="dash-stat stat-gray"><div class="stat-num" id="stat-stopped">0</div><div class="stat-label">Stopped</div></div>
  <div class="dash-stat stat-red"><div class="stat-num" id="stat-error">0</div><div class="stat-label">Errors</div></div>
  <div class="dash-stat stat-blue"><div class="stat-num" id="stat-total">0</div><div class="stat-label">Total</div></div>
</div>
```

```css
.dash-stats{display:flex;gap:.6rem;margin-bottom:.8rem;flex-wrap:wrap}
.dash-stat{background:var(--glass-bg);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:12px;padding:.5rem 1rem;flex:1;min-width:100px;text-align:center;box-shadow:0 4px 16px var(--glass-shadow);transition:.2s}
.dash-stat:hover{transform:translateY(-2px);box-shadow:0 8px 24px var(--glass-shadow)}
.dash-stat .stat-num{font-size:1.25rem;font-weight:700;line-height:1.3}
.dash-stat .stat-label{font-size:.65rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:.5px}
.dash-stat.stat-green .stat-num{color:var(--green)}
.dash-stat.stat-gray .stat-num{color:var(--text-dim)}
.dash-stat.stat-red .stat-num{color:var(--red)}
.dash-stat.stat-blue .stat-num{color:var(--accent)}
```

## .svc-card (replaces .card-expandable)

Compact glass card with inline action pills, no card-footer.

```css
.svc-card{background:var(--glass-bg);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:12px;padding:0;margin-bottom:.5rem;box-shadow:0 4px 16px var(--glass-shadow);transition:.2s;overflow:hidden}
.svc-card:hover{border-color:var(--accent);box-shadow:0 6px 24px var(--glass-shadow)}
.svc-card .svc-top{padding:.65rem .75rem;cursor:pointer;display:flex;align-items:center;gap:.5rem}
.svc-card .svc-top:hover{background:var(--surface-2)}
.svc-card .svc-dot{flex-shrink:0}
.svc-card .svc-name{flex:1;font-size:.85rem;font-weight:600;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.svc-card .svc-port{font-size:.65rem;padding:.15rem .5rem;border-radius:6px;background:var(--surface-2);border:1px solid var(--glass-border);color:var(--text-dim);flex-shrink:0;text-decoration:none}
.svc-card .svc-port:hover{border-color:var(--accent);color:var(--accent)}
.svc-card .svc-meta{font-size:.7rem;color:var(--text-dim);display:flex;gap:.3rem;align-items:center;flex-shrink:0}
.svc-card .svc-actions{display:flex;gap:2px;padding:.35rem .75rem;border-top:1px solid var(--glass-border);flex-wrap:wrap}
.svc-card .svc-actions button{background:none;border:none;color:var(--text-dim);font-size:.7rem;padding:.2rem .5rem;border-radius:6px;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:3px}
.svc-card .svc-actions button:hover{background:var(--surface-2);color:var(--text)}
.svc-card .svc-actions button:disabled{opacity:.3;cursor:not-allowed}
.svc-card .svc-actions .act-start:hover{color:var(--green)}
.svc-card .svc-actions .act-stop:hover{color:var(--red)}
.svc-card .svc-actions .act-restart:hover{color:var(--accent)}
.svc-card .svc-actions .act-logs{color:var(--accent)}
.svc-card .svc-actions .act-del:hover{color:var(--red)}
.svc-card .svc-bar{height:3px;background:var(--border);overflow:hidden}
.svc-card .svc-bar .fill{height:100%;background:var(--green);transition:width 1s}
.svc-card .svc-desc{padding:0 .75rem .35rem;font-size:.7rem;color:var(--text-dim);line-height:1.4}
.svc-card .svc-details{display:none;padding:.4rem .75rem .6rem;border-top:1px solid var(--glass-border);font-size:.7rem;gap:.5rem;flex-wrap:wrap}
.svc-card.expanded .svc-details{display:flex}
.svc-card .svc-details span{color:var(--text-dim)}
.svc-card .svc-details strong{color:var(--text)}
.svc-card .svc-chart{height:18px;background:var(--surface-2);border-radius:3px;overflow:hidden;display:flex;gap:1px;padding:1px;margin:.3rem .75rem .5rem}
.svc-card .svc-chart .seg{flex:1;border-radius:1px;transition:background .5s}
.svc-card .svc-chart .seg.running{background:var(--green)}
.svc-card .svc-chart .seg.stopped{background:var(--border)}
.svc-card .svc-chart .seg.error{background:var(--red)}
.svc-card .auto-restart-badge{font-size:.6rem;padding:.1rem .4rem;border-radius:4px;background:rgba(245,158,11,.15);color:var(--amber);flex-shrink:0}
```

### JS render template

```javascript
function render(svcs){
  const list=$('svc-list');
  if(!svcs||!svcs.length){list.innerHTML='<div class="svc-card"><div class="svc-top" style="justify-content:center;padding:2rem"><span class="has-text-grey-light"><small>Empty</small></span></div></div>';return}
  let run=0,stop=0,err=0;
  list.innerHTML=svcs.map((s,i)=>{
    if(s.status==='running')run++;else if(s.status==='error')err++;else stop++;
    const up=s.uptime>0?fmt(s.uptime):'', lnk=s.port>0?` href="/proxy/${s.port}/" target="_blank"`:'';
    const upPct=s.uptime>0?Math.min(100,Math.round(s.uptime/86400*100)):0;
    const arlbl=s.autoRestart?`<span class="auto-restart-badge" title="Auto-restart every ${fmt(s.autoRestart)}">↻ ${fmt(s.autoRestart)}</span>`:'';
    const desc=s.description?`<div class="svc-desc">${esc(s.description)}</div>`:'';
    const meta=s.pid||up?`<div class="svc-meta">${s.pid?'PID '+s.pid+' ':''}${up?'⏱ '+up:''}</div>`:'';
    return `<div class="svc-card" data-svc-id="${s.id}">
      <div class="svc-top" onclick="toggleExpand('${s.id}')">
        <span class="sc-dot ${s.status} svc-dot"></span>
        <span class="svc-name">${esc(s.name||s.id)}</span>
        ${arlbl}
        ${s.port>0?`<a class="svc-port"${lnk}>:${s.port}</a>`:''}
        ${meta}
      </div>
      ${desc}
      ${s.uptime>0?`<div class="svc-bar"><div class="fill" style="width:${upPct}%"></div></div>`:''}
      <div class="svc-actions">
        <button class="act-start" onclick="act('${s.id}','start')" ${s.status==='running'?'disabled':''}>▶ Start</button>
        <button class="act-stop" onclick="act('${s.id}','stop')" ${s.status!=='running'?'disabled':''}>■ Stop</button>
        <button class="act-restart" onclick="act('${s.id}','restart')" ${s.status!=='running'?'disabled':''}>↻ Restart</button>
        <button class="act-logs" onclick="selLog('${s.id}')">📋 Logs</button>
        <button class="act-del" onclick="deleteSvc('${s.id}')" style="margin-left:auto">🗑</button>
      </div>
      <div class="svc-details" id="exp-${s.id}">
        <span>Status: <strong>${s.status}</strong></span>
        ${s.port?`<span>Port: <strong>${s.port}</strong></span>`:''}
        ${s.pid?`<span>PID: <strong>${s.pid}</strong></span>`:''}
        ${s.uptime>0?`<span>Uptime: <strong>${fmt(s.uptime)}</strong></span>`:''}
        ${s.port?`<span><a href="/proxy/${s.port}/" target="_blank" rel="noopener">🔗 Open</a></span>`:''}
        <span style="margin-left:auto"><button class="button is-small" style="font-size:.65rem;padding:.1rem .5rem" onclick="editSvc('${s.id}')">⚙️</button></span>
      </div>
      <div class="svc-chart" id="chart-${s.id}"></div>
    </div>`;
  }).join('');
  $('stat-running').textContent=run;
  $('stat-stopped').textContent=stop;
  $('stat-error').textContent=err;
  $('stat-total').textContent=svcs.length;
}
```

## Glass Log Panel

Replaces the old log-toolbar + loose log box. Wraps everything in a glass card.

```html
<div class="log-panel">
  <div class="log-header">
    <span class="log-title">📋 Logs</span>
    <select id="log-select"></select>
    <div class="log-actions">
      <button onclick="clearLogs()" title="Clear">🧹</button>
      <button onclick="toggleAutoScroll()" id="auto-scroll-btn" title="Auto-scroll">⬇</button>
    </div>
    <span class="log-status" id="log-status"></span>
  </div>
  <div id="log-box">...</div>
</div>
```

```css
.log-panel{background:var(--glass-bg);backdrop-filter:blur(16px);border:1px solid var(--glass-border);border-radius:12px;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 4px 16px var(--glass-shadow)}
.log-header{display:flex;align-items:center;gap:.4rem;padding:.5rem .75rem;border-bottom:1px solid var(--glass-border);flex-shrink:0}
.log-header .log-title{font-size:.8rem;font-weight:600;flex-shrink:0}
.log-header select{flex:1;background:var(--surface-2);border:1px solid var(--glass-border);border-radius:6px;color:var(--text);font-size:.7rem;padding:.2rem .4rem;outline:none;max-width:180px}
.log-header .log-actions{display:flex;gap:3px}
.log-header .log-actions button{background:none;border:1px solid transparent;border-radius:5px;color:var(--text-dim);padding:.2rem .45rem;font-size:.7rem;cursor:pointer;transition:.15s;line-height:1}
.log-header .log-actions button:hover{border-color:var(--glass-border);background:var(--surface-2)}
.log-header .log-status{font-size:.65rem;color:var(--text-dim);margin-left:auto}
#log-box{flex:1;padding:.5rem .75rem;font-family:monospace;font-size:.7rem;min-height:180px;max-height:calc(60vh - 100px);overflow-y:auto;white-space:pre-wrap;color:var(--text);line-height:1.6;background:transparent}
```

## Search filter uses .svc-card selector

```javascript
function filterSvcs(){
  const q=$('svc-search').value.toLowerCase();
  document.querySelectorAll('.svc-card').forEach(c=>{
    c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
  });
}
```

## Skeleton loader for services

```html
<div id="svc-skel" style="display:none">
  <div class="svc-card"><div class="svc-top"><div class="svc-name" style="height:1rem;width:60%;background:var(--border);border-radius:4px"></div></div></div>
  <div class="svc-card"><div class="svc-top"><div class="svc-name" style="height:1rem;width:50%;background:var(--border);border-radius:4px"></div></div></div>
  <div class="svc-card"><div class="svc-top"><div class="svc-name" style="height:1rem;width:70%;background:var(--border);border-radius:4px"></div></div></div>
</div>
```

```javascript
async function loadSvcs(){
  $('svc-skel').style.display='block';
  $('svc-list').innerHTML='';
  try{const r=await fetch('/api/services');render(await r.json());$('svc-skel').style.display='none'}catch(e){$('svc-skel').style.display='none'}
}
```

## Migration notes

- Old `.card-expandable` + `.card-footer` → `.svc-card` with `.svc-actions` pills
- Old `.level.col-header` with running/stopped counts → `.dash-stats` with 4 cards
- Old `.log-toolbar` + loose `#log-box` → `.log-panel` (glass wrapper)
- Old `.dash-layout height:calc(100vh - 52px)` → `calc(100vh - 100px)` (room for stats bar)
- Remove `layoutCol` and `toggleLayout()` — no longer needed
