# Mobile Usability Fixes — btdat.io.vn (2026-08-01)

Trigger: user reported "khó dùng trên mobile" / "vẫn thấy hơi khó dùng trên mobile"
after deploy. Root causes were NOT layout overflow — they were **tap targets
< 44px and pixel-font text < 12px**.

## Measurement (do this FIRST, don't trust vision/screenshots)

Set mobile viewport via CDP, then run a JS audit on the REAL tab:

```js
// 1) Emulation.setDeviceMetricsOverride {width:375, height:667, mobile:true, deviceScaleFactor:2}
//    ⚠️ browser_navigate RESETS emulation — re-apply AFTER every navigate.
//    Always pass target_id from Target.getTargets (see cdp-multitab-pitfalls.md).
// 2) Runtime.evaluate (returnByValue:true, target_id=<site tab>):
(function(){
  var small=[], tiny=[];
  document.querySelectorAll('button,a,input,[role=button]').forEach(function(el){
    var r=el.getBoundingClientRect(), st=getComputedStyle(el);
    if(r.width>0&&r.height>0&&(r.width<40||r.height<40)&&st.display!=='none'&&st.visibility!=='hidden')
      small.push({txt:(el.innerText||el.placeholder||'').slice(0,18),w:Math.round(r.width),h:Math.round(r.height)});
  });
  document.querySelectorAll('span,div,p,a,button').forEach(function(el){
    var st=getComputedStyle(el), fs=parseFloat(st.fontSize), r=el.getBoundingClientRect();
    if(fs>0&&fs<10&&el.innerText&&el.innerText.trim()&&r.width>0&&st.display!=='none')
      tiny.push({txt:el.innerText.trim().slice(0,16),fs:fs});
  });
  return {smallCount:small.length,small:small.slice(0,8),tinyCount:tiny.length,tiny:tiny.slice(0,8)};
})()
```

Baseline found: **29 tap targets < 40px**, **54 texts < 12px** (logo "BT DAT" at
7.68px, "LV.30 ENGINEER" at 4.8px, bottom-nav labels 8.8px). After fixes:
**1 small target** (logo link only), **9 tiny texts** (mostly emoji icons ~9.6px).

## Fixes applied

### 1. Tap targets (in mobile-ux.css, `@media (max-width: 768px)`)

```css
main button, main a, main [role="button"], main input {
  min-height: 44px !important;   /* DO NOT also set min-width — see Fix 5 */
}
```
- PixelButton `sm` size padding bumped 0.3rem→0.55rem vertical (inline style in
  PixelButton.jsx — CSS can't override inline reliably).
- Bottom nav links: `min-width:52px; min-height:48px; gap:0.2rem`.

### 2. Pixel-font text floor

Pixel font (Press Start 2P) is WIDE — 0.4-0.55rem renders 6-9px, unreadable on
mobile. Bumped inline `fontSize` across 12 files (0.4→0.6, 0.45→0.65, 0.5→0.7,
0.55→0.75rem) with a Python batch replace. Navbar uses a `<style>` block —
its sizes are edited inside the JSX `<style>`, NOT external CSS, and it's
OUTSIDE `<main>` so `main *` overrides never reach it.

### 3. Navbar logo readability
- `.pixel-nav-logo-title` 0.48→0.62rem (base), mobile override 0.7rem
- `.pixel-nav-logo-sub` 0.3→0.45rem (base), mobile override 0.6rem
- ⚠️ A `!important` mobile override that's SMALLER than intended (0.5rem) will
  silently shrink the logo — always verify computed size after.

### 4. Bottom nav icon-only on narrow screens
6+ items with labels clip at ≤375px ("ltems"/"Alchewy"). Fix:
```css
@media (max-width: 399px) {
  .pixel-nav-bottom-label { display: none !important; }
  .pixel-nav-bottom-link { min-height: 50px; }
  .pixel-nav-bottom-icon { font-size: 1.5rem !important; }
}
```
Verified: labels `display:none`, icons 24px at 375px.

### 5. ⚠️ min-width: 44px BREAKS card action rows (do NOT do this)
Adding `min-width: 44px !important` to `main button` forces icon-only action
buttons (▶ ✎ ✕ ⏹ ⟳) to 44px wide — 4 buttons + name + badge overflow the
card edge on 375px and the ✕ button gets clipped. **Fix: min-height only.**
Icon buttons stay ~35-37px wide (acceptable; height 44px is what matters).

### 6. Hamburger to the right on mobile
Hamburger sits left (right after logo) because `.pixel-nav-links-desktop` is
hidden. Fix in Navbar.jsx `<style>` media query:
```css
@media (max-width: 768px) {
  .pixel-nav-hamburger { display: block; margin-left: auto; }
}
```
`.pixel-nav-inner` is already `display:flex` so `margin-left:auto` pushes it to
the right edge. Verify: hamburger `right == inner.right` (gap 0).

### 7. Dead code: BottomTab.jsx
BottomTab.jsx is exported but NEVER rendered — Navbar.jsx has its own bottom
bar (`.pixel-nav-bottom`). Don't waste time fixing BottomTab thinking it's the
live component.

## Deploy + verify loop (each change)
```bash
cd ~/service-dashboard/frontend && npm run build   # expect 0 errors
# kill node on :3000, restart `node server.js` (background), then:
curl -s -o /dev/null -w "%{http_code}" https://btdat.io.vn/   # 200
```
Remember Cloudflare caches JS/CSS assets up to 4h (`cf-cache-status: HIT`) —
after a deploy, the user's browser may still show old bundle; tell them to
hard-refresh / incognito, and verify the new hashed bundle URL returns 200.
