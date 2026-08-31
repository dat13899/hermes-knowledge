---
name: daily-ideas-site
description: "Build daily.btdat.io.vn: mỗi ngày 1 web mới trong D:/daily/."
category: software-development
---

# Daily Ideas Site (daily.btdat.io.vn)

Trang "mỗi ngày một ý tưởng" của anh Đạt. Mỗi sáng 6h cron tự tìm ý tưởng → build → verify → gửi link. Anh Đạt đã duyệt: **TỰ DO sáng tạo, KHÔNG hỏi, KHÔNG giới hạn công nghệ/giao diện** — chỉ cần mobile-first, UI/UX tốt cả điện thoại lẫn máy tính, không lỗi khi xong, gửi link + tóm tắt.

## Kiến trúc

```
D:\daily\
├── server.js          # Node static server ZERO dependency, port 3050
└── <DDMMYYYY>\        # mỗi ngày 1 thư mục — NGÀY trước THÁNG sau (10/08/2026 = 10082026)
    ├── index.html     # <title> mô tả ý tưởng (dùng cho card listing)
    └── assets...
```

- Server: `GET /` = listing (scan thư mục `\d{8}` có index.html, sort DESC), `GET /<DDMMYYYY>/` = index.html, `GET /<DDMMYYYY>/<file>` = assets (MIME map đầy đủ). 404 đẹp cho ngày không tồn tại / sai format. Path traversal protected.
- Chạy tay: `cd /d/daily && node server.js` — KHÔNG `node /d/daily/server.js` (MSYS biến dạng → MODULE_NOT_FOUND).
- Server tự chạy qua startup bat (`btdat-startup.bat`).
- Ingress: `daily.btdat.io.vn → http://localhost:3050` trong `~/.cloudflared/config.yml` (đặt trước catch-all 404).

## 🔥 Pitfalls 18/08 — canvas nền không chạy + touch target bị clear

Build "Neon Vortex" (bullet-hell game). Hai bug dễ mắc:

1. **Canvas nền không vẽ**: BG object có `running: true` mặc định → hàm `resume()` thấy `running` đã true nên KHÔNG gọi `loop()` → canvas nền trống (screenshot toàn đen). Fix: `running: false` mặc định, `resume()` mới bắt đầu loop.
2. **Touch target bị clear mỗi frame**: `if (!kbd && p.target) p.target = null;` xóa target ngay lập tức → tap 1 lần trên mobile chỉ nhúc nhích 1 frame rồi đứng. Fix: chỉ clear khi `kbd` dùng, hoặc khi ship tới gần (<8px).
3. **`const` Game không expose ra window** → test Playwright không đọc được state. Fix: `window.Game = Game;` cuối file.

Pattern test: expose game object → Playwright `page.evaluate` chèn enemy/đạn vào array, ép wave, set energy=100 → nhấn Space → assert state. Nhanh hơn nhiều so với chờ game tự chơi (deep test 11.5s không kill được enemy vì ship đứng yên).

## 🔥 Pitfalls 17/08 — rAF vô hạn cạn tài nguyên headless verify

Build "Chart Lab" (data-viz tool). Hai vòng `requestAnimationFrame` chạy vô hạn (background particles + hero demo animation) khiến Playwright headless báo `ERR_INSUFFICIENT_RESOURCES` + `Page.captureScreenshot: Unable to capture screenshot` (fonts chờ mãi). Fix: mỗi loop có cờ `running` + `visibilitychange` listener — pause khi `document.hidden`, resume khi visible:

```js
let running = true, rafId = 0;
document.addEventListener('visibilitychange', () => {
  running = !document.hidden;
  if (running) rafId = requestAnimationFrame(loop); else cancelAnimationFrame(rafId);
});
(function loop() { if (!running) return; /*...*/ rafId = requestAnimationFrame(loop); })();
```

- Lỗi `b is not defined` trong `renderScatter` — hàm con dùng biến `b` tính trong `render()` nhưng không được truyền vào (signature thiếu param). Khi render 0 pixel + console error → mở devtools check.
- Export PNG vẽ title TRƯỚC khi `render()` → bị `clearRect` xóa sạch. Vẽ title SAU render, và dùng padding lớn `{t:96,...}` cho chart export để chừa vùng title.
- `render()` export: nhớ restore `{W,H,ctx,chartCanvas,padding}` sau khi vẽ.
- Header sticky đè nội dung trên mobile editor → `@media (max-width:900px) { #screen-editor .nav { position: static; } }`.
- Scatter cần ≥2 chuỗi dữ liệu — guard trong `setType`: nếu 1 chuỗi → toast + return.
- Test canvas render: đọc pixel vùng GIỮA (bỏ padding), không đọc góc (luôn trong suốt).
- Tooltip test: đọc `hitMap` trực tiếp rồi dispatch `PointerEvent('pointermove')` tại tọa độ hit — chuẩn hơn mouse.move mò.

## 🔥 Pitfalls 14/08 — particle/glow: Canvas 2D additive (KHÔNG WebGL)

Ngày này build "Tinh Vân Số Hóa" (particle nebula). WebGL thuần đốt ~1h debug vẫn đen màn hình trong headless verify — **quyết định Technical Artist: pivot sang Canvas 2D additive, render ngay lần đầu, đẹp tương đương**. Đây là mặc định cho mọi hiệu ứng particle/glow/stars:

- **Canvas 2D additive**: `ctx.globalCompositeOperation = 'lighter'` + `createRadialGradient` (stop 0 → màu alpha ~0.2-0.5, stop 1 → alpha 0) = phát sáng cộng dồn y hệt additive blending. Vẽ nền trước với `'source-over'`, đổi `'lighter'` cho glow/particle. Budget: 700 hạt mobile / 1500 desktop chạy mượt.
- **Verify render = đọc PIXEL, không tin screenshot bytes**: Canvas 2D → `ctx.getImageData(0,0,w,h).data` đếm pixel sáng (r+g+b > 30); WebGL → `gl.readPixels`. Screenshot 500KB chỉ chứng minh có gì đó, không chứng minh render đúng.
- Script tái dùng: `scripts/verify-render.js` (playwright-core, đếm pixel sáng + bắt lỗi JS).

**Nếu buộc dùng WebGL — các bẫy đã gặp (tất cả "im lặng": không error, không crash, chỉ đen):**
1. Headless verify cần `--enable-unsafe-swiftshader` (Chrome mới chặn software WebGL fallback; headless shell cần thêm `--use-angle=swiftshader`).
2. `gl.uniform1f`/`uniformMatrix4fv` gọi TRƯỚC `useProgram` → bị bỏ qua im lặng → uniform = 0 → `gl_PointSize = 0` → không vẽ gì. Set lại uniform mỗi frame (không phụ thuộc resize/init).
3. `bufferSubData` vào buffer CHƯA `bufferData` alloc → fail im lặng. Phải `bufferData(size)` trước.
4. Nhân matrix đúng: `proj[i] = P[r4]*m[c4] + P[r4+4]*m[4+c4] + P[r4+8]*m[8+c4] + P[r4+12]*m[12+c4]` với `r4 = i>>2, c4 = i&3`. Viết nhầm `P[r+4]` (r = index 0..15 thay vì row) → matrix garbage → mọi điểm ra ngoài clip space.
5. Đừng `const m = proj` — matrix đầu ra và rotation phải 2 mảng riêng (alias → ghi đè trong lúc đọc).
6. Camera: hạt có z dương = SAU camera khi nhìn -z → clip hết, màn hình đen dù mọi thứ "đúng". Camera phải nằm ngoài đám mây: eye=(0,0,+26) nhìn gốc → `p' = p - eye` → translation T[14] = -26.
7. Thiếu `attribute vec3 position;` trong vertex shader → compile fail chỉ hiện ở console INFO (không phải pageerror).
8. JS naming collision: `const sy` (sin yaw) + `const sy = H/2 - yr*f` (toạ độ màn hình) cùng scope → "Identifier 'sy' has already been declared". Trong render loop, toạ độ màn hình đặt tên khác (sy2/syp).

**Verify cache-bust**: server có `Cache-Control: no-store` nhưng Chrome headless vẫn có thể serve file cũ → load bằng `?v=<Date.now()>` khi nghi ngờ code cũ vẫn chạy.

## 🧪 Verify workflow thực chiến (playwright-core — đã dùng 12/08)

Chrome full: `C:/Users/datel/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe` (playwright-core trong `~/daily-test/node_modules`). Template script tham số hoá (day code): `templates/verify-daily.js` — copy sang `~/daily-test/`, chạy `node verify-daily.js <DDMMYYYY>`.

**Pitfalls đã học (13/08 — pixel editor):**
- **Canvas overlay nuốt pointer events**: canvas overlay (preview/ghost layer) đè lên canvas chính → vẽ không ra gì. Fix: `#overlayCanvas { pointer-events: none; }`. Triệu chứng: desktop click vẽ được, mobile thì không (hit-test khác) — luôn check `document.elementsFromPoint(x,y)` khi nghi vấn.
- **playwright `touchscreen.tap()` KHÔNG dùng toạ độ truyền vào trong headless** — luôn tap lại vị trí tap trước đó. Chỉ kiểm tra "tap vẽ được" (1 tap), không assert 2 tap ở 2 điểm khác nhau ra 2 pixel.
- **CDP `Input.dispatchTouchEvent` "Invalid parameters"** khi dùng layout px trong mobile context — cần device px (×dpr) hoặc bỏ qua, dùng `touchscreen.tap` thay.
- **Undo/redo 1-stack sai**: lưu snapshot trước khi vẽ → redo trả về trạng thái cũ. Fix: 2-stack chuẩn (undos/redos), push snapshot trước stroke, redo push ngược lại.
- **Draft debounce mất data**: nút "Lưu" ghi draft qua debounce → user rời editor liền sau save mất bản thảo. Fix: ghi localStorage đồng bộ ngay trong handler save.
- AutoZoom desktop ≠ zoom mặc định: test không hardcode kích thước canvas, đọc `zoomSlider.value` rồi tính.

**Checklist verify** (chạy inline `node -e` để khỏi để lại file):
- console error + pageerror + response 404 → 0 lỗi (favicon! Chrome tự gọi `/favicon.ico` → 404 trong console nếu thiếu — thêm `<link rel="icon" href="data:image/svg+xml,...">` inline từ đầu)
- h-scroll mobile: `document.documentElement.scrollWidth - clientWidth === 0`
- tap targets: button hiển thị (height>0) đều ≥44px — chips/seg cần `min-height:44px`
- layout nhiều lane: đo `getBoundingClientRect().y` → `new Set(ys).size` = số hàng (không đo bằng mắt)
- race/đa-lane chạy hết: `statDone === '4/4'`, podium hiện, HOF có card
- phím tắt: `page.keyboard.press('Space')` → nút đổi thành "Tiếp tục" (pause) rồi chạy tiếp

**Pitfalls Windows/MSYS (đã dính):**
- `curl -o /dev/null -w '%{http_code} %{size_download}B'` → exit 23 + **luôn báo 0B** (gây hiểu lầm file 0 byte). Dùng `curl -s URL | wc -c` để đếm byte thật.
- `grep -c` đếm **dòng** không đếm **occurrence** — HTML render 1 dòng thì `grep -c` sai; dùng `grep -o ... | wc -l`.
- write_file vào `C:\Users\...` báo lint "Cannot find module C:\c\Users\..." — **false positive** (file vẫn ghi đúng). Verify bằng `node --check app.js` sau đó, đừng tin message lỗi.
- Screenshot `fullPage: true` với sticky topbar → header bị "nhân bản" giữa trang trong ảnh, trông như đè lên content — **không phải bug thật**. Đánh giá layout bằng screenshot viewport-height + đo geometry qua JS, không bằng fullPage.
- CSS grid đa-lane: flex-wrap cho 3+1 lệch. `display:grid; grid-template-columns:repeat(auto-fit, minmax(420px,1fr))` → 2x2 chuẩn trên desktop (container ~1104px), `minmax(560px,1fr)` quá lớn → sập về 1 cột. Mobile override `grid-template-columns:1fr`.
- **TZ pitfall**: `TZ='Asia/Ho_Chi_Minh' date` trên host này trả SAI giờ (23:01 thay vì 06:01 — zoneinfo MSYS thiếu). Máy đã đặt giờ VN sẵn → dùng `date` thuần (local = VN time) để lấy mã ngày.

**Verify thuật toán không cần DOM**: trích generator function bằng brace-counting từ `app.js` (`src.indexOf('function* NAME')` → đếm `{}`), `eval` vào node, chạy 200 case random (size 5-50, Fisher-Yates shuffle, assert sorted + `done` flag + guard 200k steps chống infinite loop). 8 thuật toán × 25 case pass=200/fail=0.

## ⚠️ Font tiếng Việt — Press Start 2P KHÔNG có glyph VN (đã dính)

- **Press Start 2P, Pixelify Sans, Silkscreen, Tiny5, Micro 5, DotGothic16, Jacquard, Handjet KHÔNG có subset vietnamese** trong Google Fonts → chữ "NHỮNG Ý TƯỞNG" bị fallback font mặc định → **heading lệch, khác kiểu** (anh Đạt phàn nàn "lệch quá + sai font chữ").
- **CÓ glyph VN**: VT323, Space Mono, Roboto Mono, Be Vietnam Pro, Inter (verify bằng `curl -s -A "<UA Chrome đầy đủ>" "https://fonts.googleapis.com/css2?family=<Tên+Font>&display=swap" | grep 'vietnamese'`).
- **Pitfall khi verify**: curl KHÔNG gửi User-Agent → Google Fonts trả CSS rỗng/không đủ subset → grep 'vietnamese' báo sai "không có". LUÔN thêm `-A "Mozilla/5.0 ... Chrome/120..."`.
- Giải pháp heading pixel + VN: dùng **VT323** (pixel vibe, đủ dấu) nhưng font-size phải tăng ~2.5x so với PS2P (VT323 rất nhỏ: h1 34-56px, kicker 16px, stat 28px).

## ⚠️ Game canvas — bug "vệt lưu lại" khi di chuyển

- **Triệu chứng**: sprite di chuyển để lại vệt mờ (ghost trail) — anh Đạt báo "di chuyển cứ bị vệt lưu lại".
- **Nguyên nhân**: `render()` thiếu `ctx.clearRect(0, 0, W, H)` ở đầu — canvas không được xoá giữa các frame.
- **Fix**: thêm `ctx.clearRect(0, 0, W, H)` ngay đầu `render()` trước `ctx.save()`/`translate`.
- **Kiểm tra nhanh**: `grep -c 'clearRect' <file>.html` — 0 = bug chắc chắn.

## 🧪 Verify game bằng playwright-core + QA hook (đã dùng, hiệu quả)

- Browser tool chặn localhost → dùng `playwright-core` (cài ở `~/daily-test`, executable `C:\Users\datel\AppData\Local\ms-playwright\chromium_headless_shell-1228\chrome-headless-shell-win64\chrome-headless-shell.exe`).
- **QA hook pattern**: `page.addInitScript(() => { window.__QA__ = {}; })` + trong game `if (window.__QA__) window.__QA__.S = S;` (expose state) → test teleport player lên quái/exit để trigger game over / floor advance nhanh chóng. **NHỚ XOÁ hook trước khi ship** (`grep -c '__QA__'` = 0).
- Không di chuyển player khi test = bắn 1 cột hẹp không trúng quái → tưởng bug mà thực ra test chơi kém. Test phải sweep ngang.
- Chrome headless screenshot: dùng **Windows path** (`D:/daily/verify-shots/...`), MSYS path `/d/...` fail ("cannot find path").

## 🗂️ Listing page (server.js) — parse ngày DDMMYYYY + timezone

- Thư mục ngày format **DDMMYYYY** (ngày trước tháng sau): `10082026` = 10/08/2026, `08082026` = 08/08/2026. `listDays()` sort string tăng dần = ngày cũ → mới (last = mới nhất).
- **Pitfall timezone**: `new Date("2026-08-10T12:00:00")` parse theo UTC nhưng `getMonth()/getDate()` theo local (+7) → ngày lệch 1. **LUÔN dùng constructor số**: `new Date(Number(yyyy), Number(mm)-1, Number(dd), 12)`.
- **Pitfall format**: nếu parse nhầm MMDDYYYY, `10082026` (10/08) thành 08/10 → ngày hiển thị sai + streak sai. Verify bằng `fmtDate('10082026')` phải ra "Thứ Hai, 10/08/2026".
- Streak: key so sánh phải cùng format DDMMYYYY: `String(getDate()).padStart(2,'0') + String(getMonth()+1).padStart(2,'0') + getFullYear()`.
- Grid: 3 cards ở 1280px → media query 4 cột chỉ từ **1300px** (1200px áp repeat(4) với 3 cards → lệch 1 cột trống). Card lệch trái = do media query cột nhiều hơn số card.
- **Restart server sau khi sửa server.js**: tìm PID qua `netstat -ano | grep ':3050' | grep LISTENING` → `taskkill /PID <pid> /F` (chú ý: trong git-bash dùng `/PID` KHÔNG `//PID`) → start lại `cd /d/daily && node server.js` (background).

## 🌐 Cloudflared chết → Error 1033 (đã dính, đã fix)

- **Triệu chứng**: truy cập daily.btdat.io.vn → "Error 1033 Cloudflare Tunnel error".
- **Nguyên nhân**: process `cloudflared` không chạy (server local vẫn OK, chỉ tunnel chết).
- **Kiểm tra**: `tasklist //FI "IMAGENAME eq cloudflared.exe"` trống = chết. `curl -s -o /dev/null -w '%{http_code}' http://localhost:3050/` vẫn 200 = server OK.
- **Fix**: chạy `cd ~/bin && ./cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run` (background). Chờ log "Registered tunnel connection" → verify `https://daily.btdat.io.vn/` HTTP 200.
- **Pitfall**: startup bat `btdat-startup.bat` gọi `cloudflared.exe` nhưng file thật là `cloudflared` (KHÔNG đuôi .exe) → bat fail khi logon. Đã sửa bat bỏ `.exe`.
- **Pitfall**: binary ở `~/bin/cloudflared` KHÔNG phải `cloudflared.exe`. Dùng absolute path `/c/Users/datel/bin/cloudflared`.

## ⚠️ Ngày tháng — lỗi đã dính phải (ghi đè nhầm ngày)

- **LUÔN tính mã ngày bằng giờ VN, KHÔNG dùng giờ máy/conversation date**: `TZ='Asia/Ho_Chi_Minh' date '+%m%d%Y'`. Máy có thể đang ở múi giờ khác — lúc 07:29 máy (giờ khác) thì VN đã là 00:29 hôm sau → tưởng còn hôm cũ mà thực ra ngày mới đã bắt đầu.
- **KHÔNG BAO GIỜ ghi đè thư mục ngày đã tồn tại**. Khi anh Đạt bảo "làm lại/ghi đè hôm nay": kiểm tra `D:\daily\<mã>` trước. Nếu mã = hôm nay đã có → tạo THƯ MỤC MỚI (ngày mới), đừng đè. Nếu vô tình đã đè → khôi phục bản gốc từ backup rồi tạo ngày đúng.

## 🐛 Pitfalls build game canvas (kinh nghiệm 10/08/2026 — Đảo Trọng Lực)

- **Verify gameplay bằng playwright-core**: xem `references/playwright-game-verify.md` — recipe 11 bước (start→jump→flip→move→die→retry→gem→clear→next) với `window.__` debug hooks, script test mẫu, screenshot script, và pixel-sampling để chứng minh chi tiết nhỏ (outline 1-2px) khi vision model không thấy.
- **Hitstop tự khoá game**: nếu đặt `hitstop` decay bên trong `update()` mà update bị skip khi `hitstop>0` → hitstop không bao giờ giảm → game đóng băng vĩnh viễn sau chết/retry. **Decay hitstop ở `loop()` (ngoài update)**: `hitstop=Math.max(0,hitstop-dt); if(hitstop<=0) update(dt);`
- **Spawn player phải chạm đất**: `py=(R-1)*TILE-PH` (hàng đất cuối trừ chiều cao player). Nếu spawn lơ lửng → không grounded → KHÔNG nhảy được (bug khó thấy). Tương tự nhảy ngược dấu: flip=true (trọng lực hướng lên) thì nhảy phải `+JUMPV`, bình thường `-JUMPV`.
- **Không dùng `player.h` khi khởi tạo player**: `py=(R-1)*TILE-player.h` chết vì player chưa tồn tại → dùng hằng `PH=30`.
- **Verify gameplay bằng playwright-core** (thư mục `~/daily-test`, có node_modules/playwright-core): click BẮT ĐẦU → keyboard Space/Shift → check `window.__` debug hooks → teleport tới gem/goal → verify clear/next level. Expose `window.__p/__gems/__goal/__state/__lvl` để test dễ.
- **Màn hẹp hơn viewport**: camera phải giữa màn (`(bounds.w-W)/2`) chứ không clamp 0 → tránh trống 1 bên. Vẽ viền glow quanh bounds.
- Chromium headless shell: dùng `--dump-dom --enable-logging=stderr` để bắt JS errors; `--screenshot` chụp 2 viewport 375x667 + 1280x800; xem bằng vision_analyze.
- Màn 1 = tutorial: dạy nhảy → flip → thu gem → chạm cổng; các màn sau tăng dần: spike (3-4), platform động (5-6), kết hợp (7-8), challenge (9-10). Đảm bảo critical path legible (chuẩn Level Designer).
- Luôn `cp` backup (`<mã>-bak/`) TRƯỚC khi sửa/đè, và sau khi xong kiểm tra `ls /d/daily/` thấy đủ các ngày.
- Title trong `<title>` phải khớp mã ngày thư mục (09/08/2026 ↔ 09082026), không sót sau khi copy.

## Verify — headless chrome + Playwright (Windows/MSYS)

- `--screenshot` path PHẢI là Windows path (`D:\\daily\\verify-shots\\x.png`), MSYS path (`/d/daily/...`) bị Chrome từ chối ("cannot find the path specified").
- `--dump-dom` + `--enable-logging=stderr` + `--virtual-time-budget=8000` → grep `uncaught|exception|TypeError` → 0 = sạch.
- Có `~/daily-test` với playwright-core + chromium-1228 (`chrome-win64/chrome.exe`) sẵn — dùng cho E2E: click start, plant, toggle night/rain, mở stats, check console/pageerror/requestfailed.
- Playwright: `executablePath: 'C:\\Users\\datel\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe'` — trong JS string phải escape `\\`, viết file rồi chạy (inline `node -e` bị nuốt backslash).
- Test script viết vào `~/daily-test/test-*.js` (node_modules playwright-core ở đó), KHÔNG để trong `D:\\daily\\<mã>\\` (bẩn thư mục build).
- `page.on('response')` bắt được 404 — favicon.ico thiếu gây "Failed to load resource 404" ×2, thêm `<link rel="icon" href="data:image/svg+xml,...">` để sạch console.
- Browser tool (`browser_navigate`) chặn localhost/private — dùng playwright script thay thế.
- App có AudioContext: test cần `args: ['--autoplay-policy=no-user-gesture-required']` để audio init không bị chặn.
- Modal mở chặn click nút sau nó — test phải đóng modal (`[data-close="..."]`) trước khi click tiếp.

## Pitfall: save/resume + AudioContext

Nếu app có start screen ẩn khi có save cũ (localStorage) → AudioContext không có user gesture → suspended → app "chết âm thanh". Giải pháp: LUÔN giữ start screen làm "resume gate" (đổi nút thành "Tiếp tục"), click mới khởi tạo audio. Đây là lỗi đã gặp ở Khu Vườn Âm Thanh 11/08.

## Pitfall: JS lint qua write_file/patch

`write_file`/`patch` lint node `--check` trên Windows/MSYS báo `Cannot find module 'D:\d\daily\...'` — path bị biến dạng, LÀ LỖI GIẢ (file vẫn ghi đúng). Verify thật: `cd /d/daily/<mã> && node --check app.js`.

## Verify & QA thực chiến (pitfalls đã đúc kết)

- **Canvas game — `ctx.clearRect(0,0,W,H)` ĐẦU `render()` là BẮT BUỘC** (dùng `ctx.save()` + `translate(shakeX,shakeY)` bên dưới). Thiếu clearRect = **vệt mờ (ghost trail)** khi sprite di chuyển — lỗi kinh điển, dễ bỏ sót vì menu tĩnh vẫn đẹp, chỉ thấy khi gameplay di chuyển. Nhớ kiểm tra cả file cũ copy từ template cũ (bản "Hầm Ngục" cũng dính).
- **Playwright test "game kẹt" thường là TEST chơi kém, không phải bug game**: player đứng yên (test không di chuyển) → auto-fire bắn 1 cột hẹp, enemies spawn random x → không trúng → tưởng collision bug. Test phải di chuyển ngang liên tục (sweep a/d trong vùng an toàn, tránh kẹt mép tường). Muốn chắc chắn → dùng QA hook + god mode `S.maxHp=999` để chạy tới boss nhanh, hoặc teleport lên enemy.
- **QA hook cho game canvas (state trong IIFE closure)**: playwright không đọc được state vì bị ẩn trong closure. Thêm `if (window.__QA__) window.__QA__.S = S;` cuối script + `await page.addInitScript(() => { window.__QA__ = {}; })` (chạy TRƯỚC page scripts) → đọc/teleport state trực tiếp: `S.player.px = m.x*32+8` lên quái, force `S.hp=1` để test game over, teleport lên exit để test xuống tầng, set `S.maxHp=999` để chạy tới boss nhanh. **PHẢI xoá hook trước khi ship** (`grep -c '__QA__' index.html` = 0).
- **Đừng kết luận "game bug" khi test chỉ di chuyển ngẫu nhiên**: game bắn 1 cột hẹp, player đứng yên/kẹt tường = không trúng enemy = score "kẹt" nhưng là gameplay hợp lệ (chết vì đứng im là đúng). Verify cơ chế bằng QA hook (teleport/force state) chứ không đoán từ HUD.
- **Thư mục test**: `~/daily-test` (npm i playwright-core; chạy `cd /c/Users/datel/daily-test && node test-*.js`). Lưu ý: write_file lint báo `Cannot find module C:\c\Users\...` là **lỗi lint giả** do MSYS path — file vẫn ghi đúng, cứ chạy node bình thường.
- **Test gameplay bằng playwright-core*
- **Canvas cần CSS constrain**: `width: min(94vw, 640px); height: min(94vw, 640px)` — nếu không, canvas nội tại 640px render nguyên cỡ trên màn 375px → menu text bị cắt 2 bên (vision_analyze bắt được, dump-dom không thấy).
- **Test gameplay bằng playwright-core**: cài ở `~/daily-test` (`npm i playwright-core`, dùng chromium_headless_shell path `C:/Users/datel/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe`). Mô phỏng phím (Enter start, WASD di chuyển, R restart), đọc HUD DOM để xác nhận score/HP/floor đổi. Browser tool Hermes chặn localhost → bắt buộc playwright-core.
- **QA hook cho game IIFE-encapsulated**: state game nằm trong closure → playwright không đọc được trực tiếp. Thêm tạm `if (window.__QA__) window.__QA__.S = S;` sau khi khởi tạo + `if (window.__QA__) window.__QA__.gameOver = true;` trong gameOver(). Inject `page.addInitScript(() => { window.__QA__ = {}; })` TRƯỚC page.goto → teleport player lên quái (set `S.player.px/py = m.x*32`), force HP thấp, đứng lên exit để test game over / floor advance / restart deterministically. XÓA hooks trước khi giao (grep `__QA__` = 0).
- **Bug class game canvas thường gặp**: (1) spawn `px = tileIndex` thay vì `tileIndex * TILE` → player sai vị trí; (2) không reset `S.exit` khi newGame → dính exit cũ nhảy tầng ngay; (3) monster so sánh int vs float (`m.x === S.player.x` khi player.x là float) → xuyên player; (4) monster collision dùng `m.px` (tile int) → `Math.floor((m.px+16)/32)` luôn = 0 → không bao giờ damage. (browser tool chặn localhost): `~/daily-test/` đã cài playwright-core, executablePath = `C:/Users/datel/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe`. Pattern: `page.keyboard.press('Enter')` start → `keyboard.down/up` di chuyển → đọc HUD DOM (`document.getElementById('scoreHud').textContent`) → assert score tăng.
- **QA hooks để test vòng đời deterministic**: di chuyển ngẫu nhiên không chắc trúng quái. Thêm tạm `window.__QA__` (qua `page.addInitScript(() => { window.__QA__ = {}; })`) + expose state `if (window.__QA__) window.__QA__.S = S;` → teleport player lên quái/exit, force HP thấp để trigger game over, test R restart, test xuống tầng. **Xoá hooks sau khi test** (`grep -c '__QA__'` = 0).
- **Bug patterns canvas game hay gặp**: (1) spawn set `px = start.x` (tile index) thay vì `start.x * TILE`; (2) monster AI so sánh `m.x === S.player.x` (int vs float) → dùng `Math.floor(player.x)`; (3) monster damage dùng `m.px` (tile int) → `Math.floor((m.px+16)/32)` luôn = 0 → damage không bao giờ chạy, phải dùng `m.x`/`m.y` trực tiếp; (4) `newGame()` quên reset `S.exit = null` → dính exit tầng cũ.
- **Luôn backup trước khi ghi đè ngày đã tồn tại**: `mkdir -p <mã>-bak && cp <mã>/index.html <mã>-bak/` (skill này đã làm khi anh Đạt cho phép ghi đè).

## Cron "Daily Idea 6h sáng" (job 62c3fee9aaf7)

- Schedule `0 6 * * *`, deliver origin (Telegram). Skills đính kèm: web-research, verification-before-completion.
- **QUY TẮC ĐA DẠNG (10/08/2026 — anh Đạt phàn nàn "toàn làm game"):** CẤM game 2 ngày liên tiếp. Trước khi chọn thể loại phải đọc `<title>` của `D:\daily\<mã hôm trước>\index.html` để xác định hôm trước làm gì; nếu hôm trước là game → hôm nay BẮT BUỘC non-game. Ưu tiên luân phiên, tránh lặp thể loại trong 4 ngày gần nhất. Thể loại: app phức tạp / 3D-visual-generative / tool hữu ích / data-viz-interactive / creative-experiment / game (chỉ khi hôm trước không phải game). Search query ưu tiên non-game trước. Tóm tắt cuối phải ghi "hôm trước: X → hôm nay chọn: Y".
- Luồng: mã ngày **DDMMYYYY** (giờ VN — ví dụ 10/08/2026 = `10082026`, KHÔNG phải MMDDYYYY; 08082026 = 08/08/2026) → **skip nếu `D:\daily\<mã>\index.html` đã tồn tại** (chống ghi đè — chỉ gửi lại link + tóm tắt) → tìm idea bằng web_search đa dạng → **THUÊ CHUYÊN GIA AGENCY** (bước 4): dùng `agency_agents_search` tìm agent phù hợp (game-design, ui-designer, creative-coding...) + `agency_agents_load` nạp full instructions → áp dụng standards vào build → verify → gửi link + tóm tắt 2-3 câu kèm emoji.
- Plugin Agency Agents: `agency-agents-router` (4 tools `agency_agents_*`) đã cài ở `~/AppData/Local/hermes/plugins/`, enabled trong config. Cron session load plugin tools vì `enabled_toolsets = null` (không giới hạn). Nếu tool không khả dụng trong cron → bỏ qua bước thuê, build bình thường (KHÔNG chặn).
- Rule an toàn: chỉ làm việc trong `D:\daily\`. KHÔNG chạm service-dashboard/voice-lab/omniroute, không kill process, không restart tunnel, không sửa config.
- Fail 3 lần liên tiếp → trang fallback đẹp (thông báo "máy quá tải" + nút thử lại) + báo rõ lỗi. KHÔNG bỏ trống ngày.

## Verify — headless chrome + Playwright (Windows/MSYS)

- `--screenshot` path PHẢI là Windows path (`D:\\daily\\verify-shots\\x.png`), MSYS path (`/d/daily/...`) bị Chrome từ chối ("cannot find the path specified").
- `--dump-dom` + `--enable-logging=stderr` + `--virtual-time-budget=8000` → grep `uncaught|exception|TypeError` → 0 = sạch.
- Có `~/daily-test` với playwright-core + chromium-1228 (`chrome-win64/chrome.exe`) sẵn — dùng cho E2E: click start, plant, toggle night/rain, mở stats, check console/pageerror/requestfailed.
- Playwright: `executablePath: 'C:\\Users\\datel\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe'` — trong JS string phải escape `\\`, viết file rồi chạy (inline `node -e` bị nuốt backslash).
- Test script viết vào `~/daily-test/test-*.js` (node_modules playwright-core ở đó), KHÔNG để trong `D:\\daily\\<mã>\\` (bẩn thư mục build).
- `page.on('response')` bắt được 404 — favicon.ico thiếu gây "Failed to load resource 404" ×2, thêm `<link rel="icon" href="data:image/svg+xml,...">` để sạch console.
- Browser tool (`browser_navigate`) chặn localhost/private — dùng playwright script thay thế.
- App có AudioContext: test cần `args: ['--autoplay-policy=no-user-gesture-required']` để audio init không bị chặn.
- Modal mở chặn click nút sau nó — test phải đóng modal (`[data-close="..."]`) trước khi click tiếp.

## Pitfall: save/resume + AudioContext

Nếu app có start screen ẩn khi có save cũ (localStorage) → AudioContext không có user gesture → suspended → app "chết âm thanh". Giải pháp: LUÔN giữ start screen làm "resume gate" (đổi nút thành "Tiếp tục"), click mới khởi tạo audio. Đây là lỗi đã gặp ở Khu Vườn Âm Thanh 11/08.

## Pitfall: JS lint qua write_file/patch

`write_file`/`patch` lint node `--check` trên Windows/MSYS báo `Cannot find module 'D:\d\daily\...'` — path bị biến dạng, LÀ LỖI GIẢ (file vẫn ghi đúng). Verify thật: `cd /d/daily/<mã> && node --check app.js`.

## Verify trước khi báo xong (bắt buộc mỗi ngày)

Chạy `scripts/verify-day.sh <MMDDYYYY>` rồi xem kết quả. Script nằm trong **skill dir**, không có trong `D:\daily` — gọi bằng path đầy đủ:

```bash
bash "C:/Users/datel/AppData/Local/hermes/skills/software-development/daily-ideas-site/scripts/verify-day.sh" <MMDDYYYY>
```

1. `curl http://localhost:3050/<mã>/` → HTTP 200
2. Chromium headless shell `--dump-dom` → DOM render đúng (check giá trị động như slot/state) + scan 0 lỗi JS (`Uncaught|TypeError|ReferenceError|SyntaxError|CONSOLE.*error`)
3. Screenshot 375×667 (mobile) + 1280×800 (desktop) → xem bằng mắt (vision_analyze): không scroll ngang, tap ≥44px, contrast tốt, không vỡ layout

⚠️ **Server 3050 có thể chết giữa ngày** (startup bat chỉ chạy lúc boot). Nếu `curl localhost:3050` → 000, kickstart lại: `cd /d/daily && node server.js` (background). Đây là thao tác hợp lệ trong phạm vi `D:\daily` — không phải đụng tunnel/config.

⚠️ **Browser tool (browser_navigate / browser_cdp) chặn URL private (localhost/127.0.0.1)** — chặn bảo mật cố ý, không phải lỗi cấu hình. Với trang local dùng chromium headless shell (script trên). Với trang public chưa có DNS: `curl --resolve daily.btdat.io.vn:443:<CF-IP>` (xem skill `tunnel`).

## Pitfalls

- **`--screenshot` với MSYS path fail im lặng**: `--screenshot=/d/daily/x.png` (MSYS style) chết không báo lỗi, không tạo file. Luôn dùng Windows path: `--screenshot="D:\\daily\\verify-shots\\08082026-mobile.png"`. Thành công sẽ in `NNNN bytes written to file`.
- **`verify-day.sh` chạy từ D:\daily thất bại**: script nằm trong skill dir, không có trong `D:\daily` → luôn gọi bằng path đầy đủ (xem Verify section). DOM dump `0 bytes` thường là do redirect stdout/stderr lệch, không phải trang hỏng — chạy shell trực tiếp để debug.
- **`--enable-logging=stderr` nuốt stdout khi redirect**: khi dùng `--dump-dom ... 2>&1` để bắt JS errors, DOM có thể rơi vào nhầm stream → `0 bytes`. Tách 2 stream: `--dump-dom URL > dom.txt 2> jslog.txt`.

- Chromium headless shell path có version dir (vd `chromium_headless_shell-1228`) — đổi khi Playwright update → script tự glob version mới nhất (`ls -d .../chromium_headless_shell-* | sort -V | tail -1`).
- `--window-size` + `--screenshot` cho screenshot đúng kích thước; `--hide-scrollbars` tránh scrollbar lệch layout; `--virtual-time-budget=2000` cho JS kịp chạy.
- Trang listing sort DESC → ngày mới nhất lên đầu.
- Pattern tốt từ ngày đầu (08082026 "Cỗ Máy Ý Tưởng"): seeded random theo ngày (xmur3 + mulberry32) cho nội dung ổn định mỗi ngày, WebAudio SFX retro, localStorage lịch sử — tái dùng cho các ngày sau.

## Tham khảo

- `scripts/verify-day.sh` — script verify chuẩn (curl 200 + DOM render + JS errors + 2 screenshot).
