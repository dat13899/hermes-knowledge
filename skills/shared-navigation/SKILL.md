---
name: "shared-navigation"
title: "Shared Navigation (Client-Side Fetch)"
description: "Dùng chung navbar cho toàn bộ site multi-page bằng client-side fetch — tránh duplicate HTML, per-page config qua data attributes."
category: "software-development"
triggers:
  - "navbar dùng chung"
  - "shared navbar"
  - "navigation bar across pages"
  - "client-side navbar"
  - "multi-page nav"
  - "tránh duplicate navbar"
  - "nav-target"
version: "1.3"
---

## Mô tả

Site multi-page với Bulma CSS + vanilla JS, không server-side template engine → navbar duplicate ở mỗi file HTML. Giải pháp: 1 file `navbar.html` template + inline fetch script ở mỗi trang.

## Cấu trúc

```
public/
├── navbar.html          # Template chung (placeholders)
├── index.html           # <div id="nav-target" data-active="home">
├── dashboard.html       # <div id="nav-target" data-active="dashboard">
└── ...                  # same pattern
```

## Template file (navbar.html)

```html
<nav class="navbar is-glass" role="navigation" aria-label="Main navigation">
  <div class="navbar-brand">
    <a class="navbar-item has-text-weight-bold" href="/">btdat.io.vn{BREADCRUMB}</a>
    <a role="button" class="navbar-burger" onclick="document.querySelector('.navbar-menu').classList.toggle('is-active')" aria-label="Menu"><span></span><span></span><span></span></a>
  </div>
  <div class="navbar-menu">
    <div class="navbar-end">
      <div class="navbar-item"><button class="button is-small" onclick="toggleTheme()" aria-label="Toggle theme"><span class="theme-btn-icon">{THEME_ICON}</span></button></div>
      <a class="navbar-item{HOME}" href="/">Home</a>
      <a class="navbar-item{DASH}" href="/dashboard">Dashboard</a>
      <a class="navbar-item{DOCS}" href="/documents">Docs</a>
      <a class="navbar-item{UTIL}" href="/utilities">Tiện ích</a>
      <a class="navbar-item{WIDGET}" href="/random-widget">🎲 Widget</a>
    </div>
  </div>
</nav>
```

Placeholders:
- `{BREADCRUMB}` — breadcrumb span HTML (vd: `' <span class="...">/ widget</span>'`), empty string nếu ko có
- `{THEME_ICON}` — `🌙` (dark) hoặc `☀️` (light)
- `{HOME}` — ` has-text-link` nếu active, chuỗi rỗng nếu ko

## Per-page loader (current — refactored)

```html
<div id="nav-target" data-active="widget" data-bc=" / widget"></div>
<script>initNavbar()</script>
```

`initNavbar()` defined in `/assets/theme.js`. Does the fetch + placeholder replacement + theme icon auto-set + scroll listener re-attach. No-op if navbar already injected.

## Per-page loader (legacy — extracted to theme.js)

Mỗi trang HTML trước đây có inline fetch script ~10 dòng, đã được extract vào `initNavbar()` trong theme.js:

```html
<div id="nav-target" data-active="widget" data-bc=" / widget"></div>
<script>
fetch('/navbar.html').then(r=>r.text()).then(t=>{
  const el=document.getElementById('nav-target'),a=el.dataset.active,
    bc=el.dataset.bc?' <span class="has-text-grey-light" style="font-weight:400;margin-left:4px">'+el.dataset.bc+'</span>':'';
  const i=localStorage.getItem('btdat-theme')==='light'?'🌙':'☀️';
  el.outerHTML=t.replace(/{BREADCRUMB}/g,bc).replace(/{THEME_ICON}/g,i)
    .replace(/{HOME}/g,a==='home'?' has-text-link':'')
    .replace(/{DASH}/g,a==='dashboard'?' has-text-link':'')
    .replace(/{DOCS}/g,a==='docs'?' has-text-link':'')
    .replace(/{UTIL}/g,a==='utilities'?' has-text-link':'')
    .replace(/{WIDGET}/g,a==='widget'?' has-text-link':'');
  const n=document.querySelector('.navbar.is-glass');
  if(n){const o=()=>n.classList.toggle('scrolled',window.scrollY>20);window.addEventListener('scroll',o,{passive:true});o()}
});
</script>
```

## Quy tắc

1. **Navbar đồng nhất** — tất cả trang dùng 1 navbar.html, chỉ khác active link + breadcrumb
2. **Page-specific items** — ko đặt trong navbar. Để ở trang đó (vd: running/stopped counts trên dashboard, Services/Stack/Contact anchors trên index, doc toolbar trên documents)
3. **Style consistency** — mọi element thêm vào trang PHẢI dùng CSS class + design variables, ko inline styles. Dùng `var(--glass-bg)` + `var(--glass-border)` cho glass elements. `var(--border)` chỉ khi ko phải glass surface (progress bars, skeleton gradients). Tham khảo `references/style-consistency.md`.
4. **Navbar-spacer** — mỗi trang cần `<div class="navbar-spacer"></div>` sau navbar (height 52px, CSS trong global.css)
5. **Layout height** — nếu trang có toolbar phụ (documents layout), cập nhật: `calc(100vh - 96px)` cho 2 bars (52px navbar-spacer + ~44px toolbar). Nếu chỉ có navbar → `calc(100vh - 52px)`.
6. **initNavbar()** — phải gọi SAU khi `div#nav-target` đã trong DOM VÀ `theme.js` đã load. Thường đặt ngay sau div đó.
7. **Script order (MANDATORY)** — `theme.js` (hoặc file chứa `initNavbar`) phải load TRƯỚC inline `<script>initNavbar()</script>`. Pattern: `<body> <script src="/assets/theme.js"> <div id="nav-target"> <script>initNavbar()</script>`. Không đặt theme.js ở cuối body sau initNavbar call.

## Comprehensive site-wide refactoring

Khi cần đồng bộ code/style trên tất cả trang cùng lúc (CSS variables, navbar, inline styles), dùng 6-phase approach:

1. **CSS variable sweep** — `var(--border)` → `var(--glass-border)` in ALL border properties across ALL pages (keep `background:var(--border)` for progress bars, skeleton shimmer). Python regex: `re.sub(r'([a-zA-Z-]+\s*:\s*[^;}]*?)var\(--border\)', ...)` with capture group 1 to detect background context. Verify: `grep -nP 'border[^:]*:\s*[^;]*var\(--border\)' *.html` → empty.
2. **CSS dedup** — xoá inline CSS trùng global.css
3. **Glass card sweep** — border-radius + box-shadow cho tất cả panel chính
4. **JS extraction** — inline fetch script → shared function in theme.js. Move theme.js to `<body>` top. Verify: `grep -c 'theme.js' *.html` → each page has exactly 1.
5. **Inline style → CSS class** — scan `grep -oP 'style="[^"]{8,80}"' file.html | sort | uniq -c | sort -rn`. Group patterns, create utility classes. Batch-replace via python `str.replace()`. Skip JS template literals. Target <15 per small page, <30 per large page. See `references/style-consistency.md` for reusable class list.
6. **Commit + push all**

**Safety:** commit after EACH phase. Verify live server with curl. Phases non-overlapping.

## Pitfalls

- **Script loading order (CRITICAL)** — khi extract inline fetch script vào `initNavbar()` trong theme.js, phải đảm bảo theme.js load TRƯỚC khi gọi `initNavbar()`. Sai: theme.js ở cuối body (`</body>`) còn inline script ở đầu body. Đúng: `<script src="/assets/theme.js">` ở ngay sau `<body>`, SAU ĐÓ mới `<script>initNavbar()</script>`. Verify bằng curl trước khi git push.
- **Multiple theme.js includes** — khi move script tag, check ko còn dư bản cũ. Dùng `grep -c 'theme.js' *.html` để verify mỗi page chỉ 1x.
- **theme.js timing** — theme.js chạy trước khi fetch resolve. Không tìm thấy `.theme-btn-icon` → ko set icon. **Resolved**: `initNavbar()` tự set icon sau fetch.
- **Scroll listener miss** — theme.js gắn scroll listener lúc DOMContentLoaded. Navbar chưa inject → listener miss. **Resolved**: `initNavbar()` re-attach listener.
- **initNavbar() undefined** — nếu page chưa cập nhật theme.js (cache cũ), `initNavbar()` ko tồn tại. Hard refresh hoặc giữ inline fallback trong transition.
- **Duplicate navbar-spacer** — nếu navbar.html có spacer và trang cũng có → double spacer. Giải pháp: navbar.html chỉ chứa `<nav>`, mỗi trang tự có spacer riêng.
- **Browser caching (critical)** — navbar.html được cache mạnh ở cả browser và Cloudflare. Sau khi sửa navbar, nếu user vẫn thấy navbar cũ/mất navbar, trình tự debug:
  1. `curl -sI https://domain.com/navbar.html | grep -i 'cf-cache-status'` — kiểm tra DYNAMIC hay HIT
  2. `curl -sL https://domain.com/ | grep 'theme.js' | head -1` — kiểm tra cache-bust version `?v=N`
  3. Nếu CF cache cũ: bump `?v=N` trên tất cả CSS/JS links. Dùng batch command:
     ```bash
     for f in *.html; do sed -i 's/\?v=[0-9]/?v='$((N+1))'/g' "$f"; done
     ```
  4. Restart Node server để serve code mới
  5. Force production lấy code mới: `curl -sL https://domain.com/ | grep 'v='` verify
  6. Báo user Ctrl+F5 hard refresh
- **Cache-bust cascade** — khi navbar lỗi (mất, theme icon ko đổi), thường do `theme.js` hoặc `global.css` cũ ở CF cache. Bump version trên ALL pages đồng loạt — không chỉ 1 page.
- **Nhiều theme button** — nếu trang có theme button riêng (documents cũ), xoá khỏi toolbar vì navbar đã có.
- **Inline styles bị user từ chối** — user bắt lỗi "để ý style ý" nếu dùng inline styles. Luôn dùng CSS class + design variables. Copy pattern từ element cùng page.
- **Liquid glass escalation** — nếu user nói "chưa giống style liquid glass" hoặc "khác hẳn style trang chủ", đây không phải vấn đề 1 element. PHẢI làm comprehensive sweep: thay ALL `var(--border)` = `var(--glass-border)`, thêm border-radius + box-shadow + glass-bg + backdrop-filter vào tất cả panel chính. Xem `references/style-consistency.md` → "Comprehensive glass sweep approach".
- **Inline utility class overkill** — 1-2 elements dùng `margin-right:8px` thì inline style OK, ko cần `.icon-spacer` class. User sẽ yêu cầu bỏ. Chỉ tạo utility class khi ≥3 occurrences.
- **Mobile col-header stacking** — dashboard có running/stopped counters + Services title → KHÔNG tách 2 rows riêng (`<div class="level col-header">` × 2). Gộp 1 row: title + counters ở level-left, toggle ở level-right.

## Migrating existing pages

### 1. Xác định page-specific items

| Trang | Items cần giữ lại ở page | Items xoá (đã có trong navbar) |
|---|---|---|
| index.html | Services, Stack, Contact section anchors → sub-nav dưới hero | nav links |
| dashboard.html | running-count, stopped-count → stats bar | nav links |
| documents.html | sidebar toggle, New/Upload → sidebar-header; font controls → reader-header | brand, theme btn, 🧰 link |
| random-widget.html | (none) | — |
| utilities.html | (none) | — |

### 2. Steps

1. Tạo `navbar.html` với placeholders
2. Mỗi trang: thay `<nav>` bằng `<div id="nav-target" data-active="..." data-bc="...">` + `<script>initNavbar()</script>`
3. Page-specific items: move ra khỏi navbar template, đặt vào HTML body của trang đó
4. Nếu trang có layout đặc biệt (documents): cập nhật CSS height constraints
5. Thêm `sidebar-header`, `font-controls` vào print media query nếu cần

## Common patterns

### App-style pages (documents)

Trang có sidebar + reader layout riêng thay vì content-flow:

- **Navbar**: shared, đồng nhất (Home | Dashboard | Docs | Tiện ích | 🎲 Widget)
- **Toolbar items**: dồn vào sidebar header (☰, New, Upload) và reader header (A− A+, TOC, actions)
- **Layout height**: `calc(100vh - 52px)` (chỉ navbar-spacer), hoặc `calc(100vh - 96px)` nếu có doc-toolbar
- **Sidebar header**: dùng `.sidebar-header` class với `.s-btn` glass ghost buttons
- **Font controls**: dùng `.font-controls` class, glass ghost button pattern
- **App → homepage conversion**: xem `references/style-consistency.md` → "App-style page → homepage glass card layout"

### Landing page section anchors (index)

```html
<div class="container has-text-centered" style="margin-bottom:0;margin-top:-1.5rem">
  <a class="button is-small is-ghost" href="#services">Services</a>
  <a class="button is-small is-ghost" href="#stack">Stack</a>
  <a class="button is-small is-ghost" href="#contact">Contact</a>
</div>
```

### Dashboard stats bar

```html
<div class="level col-header">
  <div class="level-left">
    <h2 class="title is-5">📦 Services</h2>
    <span id="running-count" class="tag is-success is-light"><span class="sc-dot running m-0"></span> 0</span>
    <span id="stopped-count" class="tag"><span class="sc-dot stopped m-0"></span> 0</span>
  </div>
  <div class="level-right"><button class="button is-small" onclick="toggleLayout()">⊞</button></div>
</div>
```

**Merged single row** (mobile-friendly) — counters inline with title, layout toggle on right. Avoid stacking 2 level rows on mobile.
