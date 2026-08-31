---
name: mobile-ui-usability
description: "Khó dùng mobile. Measure tap targets & fonts via CDP."
triggers:
  - "giao diện khó dùng trên mobile"
  - "mobile UI quá nhỏ / chữ nhỏ không đọc được"
  - "nút bấm khó chạm trên điện thoại"
  - "bottom nav bị cắt chữ"
  - "hamburger vị trí sai trên mobile"
  - "tap target nhỏ hơn 44px"
---

# Mobile UI Usability — measure, then fix

When the user reports "khó dùng trên mobile" (hard to use on phone), MEASURE first — don't guess. The most common root causes are tap targets < 44px (Apple HIG) and text < 10-12px.

## 1. Measure (CDP Runtime.evaluate on the REAL tab)

```js
// Tap targets < 40px
(function(){
  var small=[];
  document.querySelectorAll('button,a,input,[role=button]').forEach(function(el){
    var r=el.getBoundingClientRect(); var st=getComputedStyle(el);
    if(r.width>0&&r.height>0&&(r.width<40||r.height<40)&&st.display!=='none'&&st.visibility!=='hidden'){
      small.push({tag:el.tagName,txt:(el.innerText||el.placeholder||'').slice(0,18),w:Math.round(r.width),h:Math.round(r.height)});
    }
  });
  return {count:small.length,small:small.slice(0,14)};
})()
```

```js
// Fonts < 10px
(function(){
  var tiny=[];
  document.querySelectorAll('span,div,p,a,button').forEach(function(el){
    var st=getComputedStyle(el); var fs=parseFloat(st.fontSize); var r=el.getBoundingClientRect();
    if(fs>0&&fs<10&&el.innerText&&el.innerText.trim().length>0&&r.width>0&&st.display!=='none'){
      tiny.push({txt:el.innerText.trim().slice(0,16),fs:fs});
    }
  });
  return {count:tiny.length,tiny:tiny.slice(0,10)};
})()
```

Record BEFORE/AFTER counts to prove the fix (e.g. small targets 29→1, tiny fonts 54→9).

## 2a. PITFALL: blanket `min-width: 44px !important` on ALL buttons breaks card rows

`main button { min-height: 44px !important; min-width: 44px !important }` was a MISTAKE this session — it forced every icon button (▶ ✎ ✕ ⏹ ⟳ in dashboard service rows) to ≥44px wide, which **overflowed the card's right edge** (delete buttons clipped). The correct scope:
- **min-height: 44px globally** — safe, never breaks rows (only makes them taller).
- **min-width: only where layout has room** (hamburger, primary CTA, tabs). Never force min-width on compact icon-button rows — 35-37px wide × 44px tall is acceptable.
- Verified fix: bump `PixelButton` sm padding `0.3rem 0.6rem` → `0.55rem 0.7rem` for height; leave widths alone.

## 2b. Trust DOM bounding-rect math over vision-model clipping claims

After a fix, verify with `getBoundingClientRect()` per element: every bottom-nav link's `right` must be `<= innerWidth`. This session vision repeatedly claimed "7th icon clipped" while the math showed Voice link right=368 < 375 (viewport) — fully visible. Vision models over-report emoji clipping at edges; the numbers are the source of truth.

## 2c. 7 bottom-nav items on 375px: icon-only mode is the fix

When adding a 7th nav item, `slice(0,6)` silently drops it. Use `filter(l => l.to !== '/hermes').slice(0,7)` to swap rather than crowd. On `<400px` screens hide labels (`display:none`) and keep icons ≥1.4rem — 7 icons × ~53px fit 375px. `justify-content: space-around` + measured gaps confirm fit.

## 2d. Hamburger to the right: `margin-left: auto` in the flex container

User: "pixel-nav-hamburger để ra bên phải" → add `margin-left: auto` to the hamburger inside its flex `nav-inner` (desktop links hidden on mobile). Verified: left=317, right=361 in 375px viewport, gap-to-right=0. No JS needed.

## 2. The core pitfall: inline style BEATS CSS

React components use `style={{ fontSize: '0.4rem' }}` inline styles. **An inline style cannot be overridden by a CSS media query**, even with `!important`. So:

- ❌ DON'T add `main * { font-size: ... !important }` to mobile-ux.css — it won't touch inline-styled elements and can wreck heading hierarchy.
- ✅ DO edit the JSX `fontSize` values directly. Bump map for pixel fonts: `0.4rem→0.6rem`, `0.45→0.65`, `0.5→0.7`, `0.55→0.75`. Batch with a python loop over the files (grep first to find them).

## 3. Tap targets

- `main button, main a, main [role="button"], main input { min-height: 44px !important }` — safe, works.
- ⚠️ Do NOT force `min-width: 44px` globally: it overflows card action-button rows on 375px (▶✎✕ icons get clipped at the right edge). Icon buttons 36-37px wide × 44px tall are acceptable.
- Bottom nav with 6 items on <400px: labels truncate ("ltems", "Alchewy"). Fix = icon-only nav: `.pixel-nav-bottom-label { display: none !important }`, icon ~1.5rem, link min-height 50px. Keep labels ≥400px.
- Hamburger ☰ on mobile right-aligned (user preference): `margin-left: auto` on `.pixel-nav-hamburger` inside the flex `.pixel-nav-inner`, in the `@media (max-width:768px)` block.

## 4. CDP testing pitfalls (Windows headless Chrome)

- `browser_navigate` RESETS device metrics → **re-apply `Emulation.setDeviceMetricsOverride` AFTER every navigate**, or the viewport silently returns to desktop width and media queries misbehave. Verify with `innerWidth` before trusting a screenshot.
- Multiple tabs: `browser_console`/evaluate may hit a `chrome://new-tab-page` tab instead of the app. Check `Target.getTargets`, use `browser_cdp` with explicit `target_id`, and verify `location.href` first.
- Chrome headless can serve stale JS even after edits: verify with `curl` on the public URL (`grep` for the new function signature), check `cf-cache-status: HIT` = Cloudflare serving old file → rename the file to bust cache (see fe-deploy-troubleshooting).

## 5. Verify loop

1. Edit JSX/CSS → `npm run build` → restart `node server.js` (kill port-3000 PID first)
2. `curl` public URL 200 + new bundle hash in HTML
3. Re-set mobile viewport → navigate → re-measure with scripts above
4. Report BEFORE/AFTER numbers to the user

## Related
- `fe-qa-checklist` (user-owned) has the browser cross-compat + deploy checklist for btdat.io.vn
- `fe-deploy-troubleshooting` (user-owned) covers Cloudflare cache 404 poisoning + SW stale HTML
