---
name: webgl-scrollytelling
description: "Web kể chuyện theo cuộn, 3D scroll-driven vanilla Three.js."
---

# WebGL Scrollytelling — 3D Scroll-Driven Storytelling

> Vanilla Three.js (không React, không build): camera bay xuyên các "chương" theo scroll,
> mỗi chương 1 cảnh 3D riêng + text reveal + progress/rail/counter UI.
> Demo chuẩn: https://btdat.io.vn/3d (COSMOS — 6 kỷ nguyên vũ trụ, đã live).

## Khi nào dùng
- User hỏi "scrollytelling", "3D scroll-driven animation", "web kể chuyện theo cuộn", "scroll storytelling".
- User cho tự do chọn chủ đề, "sáng tạo ko cần dựa theo các dự án cũ" → **chọn 1 theme gốc mới** (vd: hành trình vũ trụ 6 chương), KHÔNG reuse nội dung dự án cũ.

## Stack & kiến trúc
- 1 file standalone `public/<name>.html`, Three.js qua importmap CDN (không cần build):
  ```html
  <script type="importmap">{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"}}</script>
  ```
- `canvas#c` fixed full-screen; các `<section class="chapter">` min-height 100vh là scroll driver.
- Camera fly-through: `camera.z = 6 - progress * ((N-1)*ZSTEP + 16)` với ZSTEP=26; mỗi group chương đặt tại `z = -i*ZSTEP`.
- `chapterProgressFor(i)`: start = top - vh*0.65, end = top + vh*0.65, smoothstep → drive text reveal + scene update.
- UI (rail dots, counter, progress bar, hint) chạy riêng `animateUI()` — **phải chạy cả khi không có WebGL**.
- Hiệu năng: pixelRatio ≤ 1.75; giảm particle count khi mobile (`isMobile`); glow = SpriteMaterial + AdditiveBlending + depthWrite:false; fog FogExp2.

## Bắt buộc: WebGL detection + fallback
```js
const webglOK = (() => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch { return false; } })();
if (!webglOK) document.body.classList.add('no-webgl'); // CSS: ẩn canvas, hiện note
```
Lý do: (1) browser headless verify KHÔNG có WebGL → không test được nhánh 3D; (2) user không GPU vẫn đọc được story. Fallback giữ nguyên text + scroll animation + toàn bộ UI.

## Pitfalls (đã dính thật)
1. **Hoisting bug trong ES module (bug chí mạng)**: khai báo `function animate3D(){}` BÊN TRONG `if (webglOK) {...}` KHÔNG được hoisted lên module scope (strict mode). Gọi `if (webglOK) animate3D()` ở top-level → `ReferenceError: animate3D is not defined` → crash NGAY trên Chrome thật có WebGL (headless không bắt được vì không vào nhánh 3D). Fix: `let animate3D = null;` ngoài block, gán `animate3D = function(){...}` trong block.
2. **Active chapter**: đừng chọn theo `max(cp)` — nhiều chapter cùng đạt progress 1.0 → luôn ra chapter 0. Chọn chapter có `offsetTop` gần viewport midpoint nhất.
3. **Headless browser không có WebGL**: dấu hiệu module script chết = rail có 0 dots (UI init nằm sau code 3D). Kiểm tra fallback bằng browser, kiểm tra logic 3D bằng node harness (bên dưới).
4. **browser_exec chặn private IP**: "Blocked: URL targets a private or internal address" → verify bằng URL public (https://btdat.io.vn/...), không dùng 127.0.0.1.
5. **curl -o /dev/null báo 0 bytes giả** (exit 23) → dùng `curl -s URL | wc -c` để so file size.
6. **taskkill //PID fails trong git-bash** (MSYS nuốt //) → `powershell -Command "Stop-Process -Id <pid> -Force"` (chi tiết thêm trong skill windows-cli).
7. `new Function()` không validate được module (import statement) → extract `<script type="module">` ra file .mjs tạm rồi `node --check`.

## Verify workflow (không GPU)
1. Syntax: extract inline module → `node --check file.mjs`.
2. Browser (headless): mở public URL, check 6 rail dots + counter đổi 01→06 khi scroll + không lỗi console (đây là fallback UI).
3. **Logic 3D thật**: `npm install --no-save three@0.160.0` rồi chạy `node scripts/verify-webgl-module.cjs public/3d.html node_modules/three/build/three.module.js` — mock DOM + WebGL context, chạy module thật, bắt runtime error (harness này đã bắt được hoisting bug). Xong có thể `npm uninstall --no-save three` (trang dùng CDN, không cần giữ).

## Deploy lên btdat.io.vn (server.js pattern /yt)
```js
const THREED_PAGE = 'C:/Users/datel/astryx-demo/public/3d.html';
// trong http.createServer, TRƯỚC static assets:
if (pathname === '/3d' || pathname === '/3d.html') {
  fs.readFile(THREED_PAGE, (err, data) => {
    if (err) { res.writeHead(404, {'Content-Type': 'text/plain'}); return res.end('not found'); }
    res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache'});
    res.end(data);
  });
  return;
}
```
Restart server: PID từ `netstat -ano | grep ":3000.*LISTENING"` → `powershell -Command "Stop-Process -Id <pid> -Force"` → `cd ~/astryx-demo && (node server.js > server.log 2>&1 &)`.
Verify: `curl -s http://127.0.0.1:3000/3d | wc -c` VÀ `curl -s https://btdat.io.vn/3d | wc -c` đều khớp file size.

## Gu thẩm mỹ của Đạt (đã áp dụng, anh thích)
- Dark #0a0a0f, gradient violet→blue (#7c6cf0 → #5b8def), Inter + JetBrains Mono (UI/data), radial glow nền.
- Glass/blur, border rgba(255,255,255,.07–.14), radius 16px, tag pill mono (font-size 11px, letter-spacing .08em).
- Title clamp(38–84px) weight 800 letter-spacing -.02em, gradient text trên từ khóa chính.
- Các chương xen kẽ left/center/right cho nhịp kể chuyện; era label mono uppercase + line gradient.

## Scripts
- `scripts/verify-webgl-module.cjs` — node harness: chạy inline ES module + Three.js với WebGL mock, bắt lỗi runtime không cần GPU (xem Verify workflow ở trên).
