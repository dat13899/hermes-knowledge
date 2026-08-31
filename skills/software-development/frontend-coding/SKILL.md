---
name: frontend-coding
title: Frontend Coding (Bulma + vanilla JS)
description: >
  Code giao diện FE với Bulma CSS + vanilla JS — responsive, dark/light theme,
  interactive components. Zero framework, zero build step.
category: software-development
trigger:
  - "làm giao diện FE"
  - "sửa UI"
  - "thêm component"
  - "responsive layout"
  - "cải thiện UX"
version: "1.0"
---

## Stack

- **CSS**: Bulma 1.x + custom `global.css` (CSS custom properties)
- **JS**: Vanilla (không jQuery, không framework)
- **Icons**: Font Awesome 6
- **Font**: Inter (Google Fonts CDN)
- **Theme**: CSS vars, `data-theme="dark"` / `"light"`, localStorage toggle
- **Deploy**: Single-page MPA (multi-page app), Node.js server, Cloudflare Tunnel

## HTML Template

```html
<!DOCTYPE html>
<html lang="vi" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page — btdat.io.vn</title>
<meta name="description" content="...">
<meta property="og:title" content="...">
<meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="manifest" href="/assets/manifest.json">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1/css/bulma.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap">
<link rel="stylesheet" href="/assets/global.css">
</head>
<body>
  <!-- content -->
<script src="/assets/theme.js"></script>
<script>
// JS here
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(()=>{})}
</script>
</body>
</html>
```

## CSS: global.css structure

```css
/* 1. Theme vars (dark/light) */
[data-theme="dark"]{--bg:#0a0e17;--surface:#111827;--surface-2:#1e293b;--border:#2d3a5c;--text:#f1f5f9;--text-strong:#fff;--text-dim:#94a3b8;--accent:#818cf8;--accent-hover:#6366f1;--green:#22c55e;--red:#ef4444;--amber:#f59e0b}
[data-theme="light"]{--bg:#f8fafc;--surface:#fff;--surface-2:#f1f5f9;--border:#e2e8f0;--text:#1e293b;--text-strong:#0f172a;--text-dim:#64748b;--accent:#6366f1;--accent-hover:#4f46e5;--green:#16a34a;--red:#dc2626;--amber:#d97706}

/* 2. Inter font */
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}

/* 3. Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}

/* 4. Reduced motion */
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:0.01ms!important;animation-iteration-count:1!important;transition-duration:0.01ms!important}}
```

## Responsive Rules

| Layout | Breakpoint | Behavior |
|--------|-----------|----------|
| Dashboard | max-width:960px | 2-column → stack |
| Documents | max-width:720px | sidebar full-width, reader là layer riêng |
| Editor | max-width:720px | split → tab (textarea top, preview bottom) |
| Nav | mobile | burger menu `.navbar-burger` |

Không dùng hardcoded pixel widths cho layout chính. Dùng flex/grid + min-width/max-width.

## JS Patterns

### Lightweight $ helper
```javascript
const $=id=>document.getElementById(id)
```

### Toast
```javascript
function toast(msg,type,undoCb){...} // copy from dashboard-ui-patterns
```

### Keyboard help
Tooltip nhỏ bottom-right, bấm `?` show/hide. Không dùng full-screen overlay.

### Resize observer / throttle
Không dùng — Bulma flexbox tự responsive. Chỉ cần CSS media query.

## Workflow Rules

1. **Before edit** — `git add -A && git commit -m "snap: ..."`
2. **After edit** — `python ~/AppData/Local/hermes/scripts/review.py`
3. **After review OK** — `git add -A && git commit -m "..." && git push`
4. **Restart server** — kill node (process kill + verify port free) → start → curl health check → verify live 3 pages

## Pitfalls (từ kinh nghiệm)

- **Skip-to-content link** — user thấy xấu, KHÔNG thêm. Chỉ dùng cho form-heavy pages.
- **Full-screen overlay** — user phàn nàn "vỡ giao diện". Dùng tooltip compact thay modal.
- **View Transitions** — `@view-transition{navigation:auto}` snapshot DOM cũ → ghost element cũ hiện khi chuyển trang. KHÔNG dùng cho multi-page SPA.
- **Server restart** — background process die âm thầm. Luôn verify health check sau restart.
- **Patch nhỏ** — dễ hỏng HTML (mất thẻ, dư thẻ). >3 dòng thay đổi → dùng write_file full file.
- **CSS class rename** — search cả @media print{} blocks và inline HTML khi đổi tên class.
- **Cloudflare cache** — CF cache HTML dynamic, nhưng browser cache mạnh hơn. Báo user Ctrl+F5.
