---
name: daily-idea-site
description: 'Use for daily.btdat.io.vn. Build one web idea daily.'
version: 1.0.0
author: Cu em
category: software-development
metadata:
  hermes:
    tags: [daily, cron, static-server, mobile-first, vietnamese-font, btdat]
    related_skills: [cloudflare-tunnel, verification-before-completion, web-research, windows-cli, fe-qa-checklist]
---

# Daily Ideas Site (daily.btdat.io.vn)

Anh Đạt duyệt (08/08/2026): mỗi sáng 6h, Hermes **tự tìm 1 ý tưởng web mới**, build thành
trang hoàn chỉnh, verify không lỗi, gửi link + tóm tắt vào Telegram. **KHÔNG hỏi anh, không giới hạn
công nghệ/giao diện.** Yêu cầu duy nhất: mobile-first, UI/UX tốt cả điện thoại lẫn máy tính.

## Kiến trúc

```
D:\daily\
├── server.js          # Node static server ZERO dependency, port 3050
└── <MMDDYYYY>\        # mỗi ngày 1 thư mục con
    ├── index.html     # bắt buộc (dùng cho listing + serve)
    ├── style.css      # tùy chọn
    └── app.js         # tùy chọn
```

- `GET /` → trang listing (card grid) tự scan `D:\daily\`, đọc `<title>` mỗi index.html
- `GET /<MMDDYYYY>` → serve index.html; `GET /<MMDDYYYY>/<asset>` → static file
- Chống path traversal; 404 đẹp cho ngày chưa tồn tại; ngày phải khớp regex `^\d{8}$`
- Server khởi động qua `btdat-startup.bat` (Startup folder); cron check server còn sống trước khi build

## Cron job "Daily Idea 6h sáng" (job 62c3fee9aaf7)

Schedule `0 6 * * *`, skills gắn: `web-research`, `verification-before-completion`.
Prompt đầy đủ nhắc: xác định ngày (giờ VN, mã MMDDYYYY), **chống ghi đè** (index.html đã tồn tại → chỉ gửi lại link + tóm tắt, KHÔNG build lại), tự tìm ý tưởng bằng web_search đa dạng, build, verify, gửi Telegram. Rule an toàn: fail 3 lần → trang fallback đẹp + báo lỗi, không bỏ trống ngày. KHÔNG chạm thư mục khác (service-dashboard, voice-lab, omniroute), không kill process/restart tunnel.

## Verify trang mới (bắt buộc trước khi báo xong)

Browser tools (`browser_navigate`, `browser_cdp`) **CHẶN private/internal address** (localhost, 127.0.0.1)
với thông báo "Blocked: URL targets a private or internal address". Không phải lỗi setup — là guard cố định.
Verify bằng **chromium headless shell** qua terminal:

```bash
SHELL="$LOCALAPPDATA/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe"

# 1. DOM render + JS boot chạy không lỗi
"$SHELL" --headless --disable-gpu --no-sandbox --dump-dom --virtual-time-budget=2000 http://localhost:3050/08082026/
# check: title đúng, giá trị slot/DOM render đúng (chứng minh JS chạy), không 'Uncaught'

# 2. Console errors
"$SHELL" --headless --disable-gpu --no-sandbox --virtual-time-budget=2500 --enable-logging=stderr --v=0 http://localhost:3050/08082026/ 2>&1 | grep -iE 'Uncaught|TypeError|ReferenceError|SyntaxError'

# 3. Screenshot 2 viewport (chụp rồi xem bằng mắt qua vision_analyze)
"$SHELL" --headless --disable-gpu --no-sandbox --window-size=375,667 --hide-scrollbars --screenshot=shot.png --virtual-time-budget=2000 http://localhost:3050/08082026/
# Desktop: --window-size=1280,800
```

⚠️ Viết script check vào `C:\Users\datel\` rồi chạy `cd /c/Users/datel && node check.js` — nếu cwd là `/d/daily`, MSYS biến path thành `C:\d\...` → "Cannot find module". Xem `windows-cli` skill.

## ⚠️ FONT TIẾNG VIỆT — pitfall quan trọng nhất

Trang dùng font mono hệ thống (Consolas/Courier New) → trên **Android** fallback (Droid Sans Mono)
**KHÔNG có glyph tiếng Việt** → chữ mất dấu/vỡ. User sẽ báo "lỗi font chữ tiếng việt".

**Đã test (08/08/2026):** các Google Fonts mono SAU ĐÂY KHÔNG có subset `vietnamese`:
Space Mono, VT323, JetBrains Mono, Azeret Mono, IBM Plex Mono, Share Tech Mono.
**Roboto Mono CÓ subset tiếng Việt** (kiểm tra: response css2 có `/* vietnamese */` block).

**Rule:** mọi trang daily phải dùng **Roboto Mono** (hoặc font có subset vietnamese) cho chữ tiếng Việt:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```
```css
body { font-family: 'Roboto Mono', ui-monospace, Consolas, monospace; }
```

Verify font bằng cách chụp mobile + `vision_analyze` hỏi "chữ có dấu đầy đủ không, có tofu/ô vuông không".

## Conventions giao diện (theo gu Đạt — xem user profile)

- Mobile-first: 375px không scroll ngang, tap target ≥44px, chữ ≥14px, contrast tốt
- Desktop 1280px: layout cân đối
- Đẹp nhất khi dùng theme tối retro: bg `#0d0806`, text `#f5ead0`, dim `#b8a898`, accent `#f0b36a`, scanline nhẹ
- `prefers-reduced-motion: reduce` tắt animation
- Sau khi fix font → **hard-refresh mới thấy** (CF cache asset 1h) — nhắc user Ctrl+F5

## Pitfall: entity game không có radius default → NaN → không bao giờ trúng

```js
function spawnAsteroid(x, y, r, vx, vy) {
  if (r == null) r = 20 + Math.random() * 14; // LUÔN có default!
  ...
}
```
Triệu chứng: `hits:0` mãi dù đạn bay sát (debug khoảng cách 16px < rr nhưng không nổ).
`r: undefined` → NaN → `dx*dx+dy*dy < NaN` luôn FALSE. Luôn check `r` khi spawn entity có collision.
Debug: thêm `window.__dbg = {hits, near:[]}` đẩy khoảng cách <60px — thấy đạn tới 16px mà không nổ = NaN.

## References

- `references/idea-machine-day1.md` — chi tiết build ngày đầu (08082026 "Cỗ Máy Ý Tưởng") làm mẫu
