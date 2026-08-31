# Making a Full-Screen Canvas App Mobile-Responsive

Specific to generative-art/canvas-heavy pages with HUD overlays, mode panels, and touch gestures.

## Key CSS Patterns

### HUD → bottom bar on mobile
Desktop: centered floating bar. Mobile: full-width strip at the very bottom.

```css
#hud{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);...}

@media(max-width:480px){
  #hud{position:fixed;bottom:0;left:0;right:0;transform:none;
    border-radius:0;border-width:1px 0 0;font-size:11px;
    justify-content:center;flex-wrap:wrap}
  #hud.hidden{transform:translateY(100%)}
  .hud-div{display:none}
}
```

### Mode panel → bottom sheet with peek bar
Desktop: sidebar with toggle button. Mobile: sheet that slides up from bottom, showing a thin peek bar by default.

```css
/* Desktop */
#mode-panel-toggle{display:block}
#mode-panel{position:fixed;left:16px;top:50%;...flex-direction:column;...}

/* Mobile */
@media(max-width:768px){
  #mode-panel-toggle{display:none}
  #mode-panel{position:fixed;left:0;right:0;bottom:0;top:auto;
    transform:translateY(calc(100% - 36px));   /* peek bar: 36px visible */
    flex-direction:row;flex-wrap:wrap;gap:2px;padding:8px 6px 40px;
    border-radius:16px 16px 0 0;z-index:20;
    transition:transform .35s cubic-bezier(.4,0,.2,1)}
  #mode-panel::before{content:'☰';display:block;width:100%;text-align:center;
    color:rgba(200,220,255,.3);padding-bottom:4px;cursor:pointer}
  #mode-panel.visible{transform:translateY(0)}    /* fully open */
  .mode-btn{flex:1 1 28%;min-width:70px;padding:5px 4px;font-size:10px}
  .mode-btn .mode-check{display:none}
}
```

### Config panel → bottom sheet
Desktop: sidebar (left side). Mobile: slides up from bottom over the mode panel.

```css
@media(max-width:480px){
  #mode-config{left:8px;right:8px;top:auto;bottom:52px;
    transform:translateY(100%);
    flex-direction:row;flex-wrap:wrap;padding:10px 14px;
    max-height:50vh;overflow-y:auto}
  #mode-config.open{transform:translateY(0)}
  #cfg-btn{left:8px;bottom:50px}
}
```

### Hiding sidebar toggle, palette name, scene name on mobile
```css
@media(max-width:480px){
  #palette-name{display:none}
  #scene-name{display:none}
  #vol-toggle{bottom:48px;right:12px;width:32px;height:32px;font-size:14px}
}
```

### Help overlay → single column
```css
@media(max-width:768px){
  .help-row,#help-overlay .help-row{flex-direction:column}
  .help-desc{font-size:12px}
}
```

## JS Changes Needed

### Auto-open/close panel on mobile
```javascript
function isMobilePanel(){return window.innerWidth<=768}

// Tap the peek bar to open/close
panel.addEventListener('click',e=>{
  if(!isMobilePanel())return;
  if(e.target===panel||e.target===panel.firstChild){
    panelOpen=!panelOpen;
    panel.classList.toggle('visible',panelOpen);
  }
});

// Auto-close after selecting a mode
document.querySelectorAll('.mode-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    setSceneMode(btn.dataset.mode);
    if(isMobilePanel()&&panelOpen){
      panelOpen=false;
      panel.classList.remove('visible');
    }
  });
});
```

### Two-finger touch gestures

```javascript
let touchPinchDist=0;
let touchModeCycle=false;
let touchStartAvgX=0;

addEventListener('touchstart',e=>{
  if(e.touches.length===2&&!wordModalActive){
    const t1=e.touches[0],t2=e.touches[1];
    touchPinchDist=Math.hypot(t1.clientX-t2.clientX,t1.clientY-t2.clientY);
    touchStartAvgX=(t1.clientX+t2.clientX)/2;
    touchModeCycle=true;
    e.preventDefault();
  }
},{passive:false});

addEventListener('touchmove',e=>{
  if(e.touches.length===2&&touchModeCycle){
    e.preventDefault();
    const t1=e.touches[0],t2=e.touches[1];
    const dist=Math.hypot(t1.clientX-t2.clientX,t1.clientY-t2.clientY);
    const delta=touchPinchDist-dist;

    // Pinch in/out → toggle config panel
    if(Math.abs(delta)>80){
      toggleConfigPanel(delta>0);
      touchModeCycle=false;
    }

    // Horizontal 2-finger swipe → cycle scene modes
    const avgX=(t1.clientX+t2.clientX)/2;
    const swipeX=avgX-touchStartAvgX;
    if(Math.abs(swipeX)>120){
      const idx=SCENE_MODES.findIndex(m=>m.id===currentMode);
      if(swipeX>0) setSceneMode(SCENE_MODES[(idx+1)%n].id);
      else setSceneMode(SCENE_MODES[(idx-1+n)%n].id);
      touchModeCycle=false;
    }
  }
},{passive:false});
```

### iOS AudioContext resume
```javascript
function initAudio(){
  // ...
  audioCtx=new(window.AudioContext||window.webkitAudioContext)();
  if(audioCtx.state==='suspended') audioCtx.resume();
  // ...
}

// Must be called from a user gesture (click/touchstart)
document.addEventListener('click', ()=>{ if(!window.audioInitialized) initAudio(); }, {once:true});
document.addEventListener('touchstart', ()=>{ if(!window.audioInitialized) initAudio(); }, {once:true});
```

## Critical: Window-width-based vs Media-query-based checks
When JS needs to detect mobile mode, `window.innerWidth <= 768` is sufficient. Do NOT use `matchMedia` for UI-toggle logic — it fires callbacks on resize and can cause toggles to fight each other. Simple imperative checks at interaction time are more reliable.
