---
name: bhxe-diagnose
description: "Sửa bhxe (btdat.io.vn/bhxe): AI chẩn đoán đèn taplo."
version: 1.0.0
author: Cu em
category: frontend
platforms: [windows]
triggers:
  - sửa / phát triển trang bhxe
  - chẩn đoán đèn taplo bằng AI vision
  - crop đèn cảnh báo từ ảnh taplo
tags: [bhxe, vision, ai, rag, dashboard, taplo, crop, bbox, vinfast]
related_skills: [web-ui-standards]
---

# BHXe — Chẩn đoán đèn taplo bằng AI

## Kiến trúc
- Trang: `C:/Users/datel/service-dashboard/public/bhxe.html` (dark premium, gradient #7c6cf0→#5b8def, Inter)
- **SERVE BỞI `C:/Users/datel/astryx-demo/server.js`** (từ 08/2026 — server mới thay service-dashboard chiếm port 3000):
  - Route `/bhxe` → `bhxe.html`, `/bhxe/data` → `bhxe-data.html`, `/bhxe/damage-data` → `bhxe-damage-data.html`, `/bhxe-data.json`, `/bhxe-damage-data.json`, `/bhxe-icons/*`
  - API `/api/bhxe/diagnose` + `/api/bhxe/detail` + `/api/bhxe/damage` port nguyên vẹn từ server cũ
  - Helper: `SERVICE_PUBLIC = C:/Users/datel/service-dashboard/public`, `DETECT_SCRIPT = .../detect_lights.py`, `bhxe-match.js` require qua `createRequire` (ESM)
- **2 TAB trong bhxe.html** (từ 08/2026):
  1. 💡 **Đèn taplo** (tab cũ): `/api/bhxe/diagnose` — vision + matchLights + detect_lights.py
  2. 💥 **Va chạm & hư hỏng** (tab mới): `/api/bhxe/damage` — upload ảnh hiện trường → AI vision quét thiệt hại → match `bhxe-damage-data.json` (24 loại: bumper, hood, headlight, door, chassis_frame...) → tổng hợp count theo severity + ước tính chi phí (cost range)
  - Tab switching: `.tab-btn[data-tab]` + `.tab-panel` (CSS `display:none/.active`)
  - Damage API trả: `{damages[], total, cost_estimate{low,high}, sevCount{minor,moderate,severe}}`
  - AI prompt damage: liệt kê damageNames từ data, yêu cầu bbox 0-1000 + damage_id; fallback keyword match nếu AI đoán sai id
- Data icon: `public/bhxe-data.json` — node cha = hãng xe (9 hãng), node con = đèn lỗi
  - Mỗi đèn: `{id, name, color, severity, shape: [keywords VN], description, advice, icon: SVG}`
- API: `server.js` → `/api/bhxe/diagnose` (POST brand+image+imgW+imgH) + `/api/bhxe/detail`
- Route: `/bhxe` → `bhxe.html`
- Route: `/bhxe/data` → `bhxe-data.html` (xem dữ liệu đã lưu — data viewer, fetch `/bhxe-data.json`)
- Route: `/bhxe/damage-data` → `bhxe-damage-data.html` (data viewer thiệt hại va chạm — stats severity, filter tab, search keywords, modal chi tiết, fetch `/bhxe-damage-data.json`)
- **RULE MÔ TẢ (08/2026):** mô tả ngắn gọn ≤25 từ; mọi text mô tả clamp 2 dòng bằng `.clamp2` (line-clamp) + nút **Xem thêm/Thu gọn** (`.clamp-toggle` với `data-clamp`, event delegation qua `document.addEventListener('click')` — KHÔNG dùng inline onclick vì bị chặn). Phát hiện overflow bằng probe span (line-clamp làm scrollHeight==clientHeight nên không dò được)
- **UI DAMAGE LIST (08/2026):** danh sách thiệt hại = **list dọc compact** (không card grid dàn trải). Mỗi dòng: icon nhỏ + tên + vị trí 📍 + badge severity + giá, click → modal chi tiết (`#dmodal`, `openDamageModal(i)` với `lastDamageData`). KHÔNG dùng icon 🛠️ trong damage list

## Layout bhxe.html (desktop 2 cột, mobile 1 cột)
- **Desktop (≥900px)**: `.main` = `grid-template-columns: 360px 1fr`. Cột trái = form (chọn hãng + upload + nút), cột phải = kết quả. `.wrap` = `height:100vh; flex-direction:column` → gọn 1 màn hình không cuộn.
- **Kết quả nhiều đèn**: `.lights` = `grid repeat(auto-fill, minmax(300px,1fr))` (nhiều cột thay vì dọc dài).
- **Placeholder state**: `#placeholder` hiển thị khi chưa phân tích, ẩn khi `renderResult`/error.
- **Summary bar**: đếm đèn theo severity (x nguy hiểm · y nghiêm trọng · z cảnh báo...).
- **Mobile (<900px)**: xếp dọc 1 cột, crop 72px, nút đủ 44px+ tap target. `<560px`: card padding 15px, gap 10px.
- Verify desktop bằng `cdp('Emulation.setDeviceMetricsOverride', width=1440, height=900, ...)` qua browser_exec.

## Icon ảnh (icon_img)
- 171/171 đèn có `icon_img` (ảnh PNG). 2 loại:
  - **Generic chuẩn ISO** (`/bhxe-icons/*.png`): 50 icon PNG từ warninglightfinder.com (1254×1254 neon glow), map theo tên/keyword cho 7 hãng còn lại.
  - **Chính hãng** (`/bhxe-icons/hyundai_*.png`, `kia_*.png`): 35 Hyundai + 35 Kia crop trực tiếp từ infographic OBD Advisor bằng vision bbox (MiniMax M3 trả bbox từng icon, bỏ text nhãn).
- Hiển thị: `addEmoji()` trong server.js ưu tiên `icon_img` (thẻ `<img>`) trước `icon` (SVG).
- Trang data viewer fetch `/bhxe-data.json?t=Date.now()` để chống cache browser.

## Luồng xử lý
1. Browser nén ảnh ≤1280px, gửi base64 + `imgW/imgH` (kích thước ảnh nén)
2. Server gọi vision model → prompt yêu cầu trả JSON:
   `{"lights": [{shape, text, color, position, bbox:[x1,y1,x2,y2]}]}`
3. Server fuzzy match `shape` với keywords trong DB theo hãng → `lights` (match ≥2) + `uncertain` (gợi ý fallback)
4. Server trả kèm `imgW/imgH` (kích thước ảnh model nhìn) — **BẮT BUỘC** để frontend crop đúng tỉ lệ
5. Frontend crop ảnh gốc theo bbox (scale `ow/baseW`, `oh/baseH`), padding 45%, 120×120px

## Nguồn dữ liệu đèn taplo (theo hãng)
- **Hyundai + Kia**: có data thật từ infographic chính hãng OBD Advisor (ảnh 1200x~2800, tải bằng curl `obdadvisor.com/dash-lights/wp-content/uploads/2023/01/<BRAND>-WARNING-LIGHTS-AND-INDICATORS.jpg`). Trích bằng vision MiniMax M3 (split ảnh 2 nửa rồi đọc tên+màu). Đã merge vào `bhxe-data.json` (hyundai 35 đèn, kia 39 đèn).
- **50 đèn phổ thông chuẩn**: scrape `warninglightfinder.com` — mỗi `symbol-card` có `symbol-name` + `symbol-shape-hint` + `symbol-meaning` + `.pill` (color+system) + icon PNG tại `/generated/symbols/<slug>.png`. Lưu ở `$LOCALAPPDATA/Temp/wlf_lights_full.json`.
- **VinFast VF9**: PDF manual `vinfastowners.org/manuals/VF9_2023-2024-2025_Owners_Manual_Condensed.pdf` (466 trang) — KHÔNG có bảng tổng hợp đèn, chỉ bảng Auto Hold (trang 212, "CONDITION/LAMP/SYMBOL/DESCRIPTION"). VinFast dùng màn hình Infotainment, đèn theo chuẩn EV chung. Data hiện tại (23 đèn) đã đủ.
- **Toyota/Honda/Mazda/Ford/Chevy**: chưa có data thật riêng, đang dùng đèn phổ thông viết tay (12-14 đèn mỗi hãng). Muốn bổ sung: scrape OBD Advisor infographic từng hãng (browser lấy URL chính xác — curl đoán pattern chỉ trúng Hyundai/Kia).

## Logic match (bhxe-match.js)
Tách riêng module `bhxe-match.js` (require từ server.js). Pipeline rule-based có trọng số:
1. **normalizeVN**: bỏ dấu TV (NFD), `đ`→`d`, lowercase, bỏ ký tự đặc biệt
2. **SYNONYMS**: bảng từ đồng nghĩa (lốp=tire, ắc quy=battery, nhiệt kế=nhiệt độ...) → `hasSynonymMatch`
3. **scoreLight** (0-11): text match=5 → color=3 → shape=2 → position=1
4. **Ngưỡng**: `>=5` matched · `3-4` uncertain (gợi ý top 5) · `<3` unknown
5. **Dedupe** theo id (giữ score cao nhất / bbox lớn nhất), **clampBbox** (swap + clamp + bỏ bbox <2px)

⚠️ Ngưỡng matched phải `>=5` (không phải 6) vì shape+color đúng = 5 điểm max khi không có `text`.
- Test: `node bhxe-match.test.js` (14 ca). Response có `confidence` (0-100), bỏ `rawVision`.
- `matchLights(visionLights, dbLights, imgW, imgH)` → `{matched, uncertain}`.
- server.js cache `BHXE_DB`/`BHXE_MTIME` (reload khi file mtime đổi).

## Semantic match (RAG embedding)
- Precompute embedding (MiniLM 384-dim) cho mỗi đèn → field `embedding` trong `bhxe-data.json` (script `precompute_embedding.py`)
- `rag_server.py` (port 3001) thêm endpoint `POST /embed` `{text}` → `{embedding, dim}`
- `bhxe-match.js` có `semanticMatch(queryText, dbLights, topK)` — cosine similarity, ngưỡng sim > 0.3
- server.js gọi semanticMatch CHỈ khi rule-based trả "unknown" (đèn không xác định) — bổ sung gợi ý gần nhất
- ⚠️ MiniLM kém tiếng Việt (query VN → similarity thấp, nhiễu). Chỉ dùng làm fallback bổ trợ, rule-based vẫn là chính.
- uncertain chỉ giữ đèn score >= 3, top 3 (tránh nhiễu 27%)

## Model vision
- **`cmd/MiniMaxAI/MiniMax-M3`** — model vision DUY NHẤT chạy được qua OmniRoute (127.0.0.1:20128)
- Các model khác: `aug/*` trả SSE rỗng (tokens-in=0, provider chết), `command-code/*` + `Gemini` bị `MODEL_NOT_IN_PLAN`
- Gọi `stream: true` (aug/* cũng stream nhưng rỗng)
- Prompt phải nhấn: **đọc chữ trên màn hình trước** (vd "Kiểm tra lốp bên phải phía trước") — manh mối quan trọng nhất

## Pitfall: crop lệch / sai vị trí
1. **MiniMax M3 bbox KHÔNG ổn định** — mỗi lần gọi trả bbox khác nhau (lệch lên, lệch ngang, hoặc trống). `temperature` thấp (0) → ổn định nhưng sót đèn; cao → bắt nhiều đèn nhưng bbox lung tung. Đừng kỳ vọng bbox chuẩn từ model.
2. **Giải pháp: dùng xử lý ảnh (màu HSV) để tìm vị trí đèn** — `detect_lights.py` (OpenCV) phát hiện vùng sáng đỏ/vàng/xanh/lam trên nền tối, trả bbox pixel CHÍNH XÁC. Server gọi script này và GHI ĐÈ bbox model bằng vùng detect gần nhất (match theo màu + khoảng cách tâm).
3. **Prompt vẫn dùng bbox tỉ lệ 0-1000** làm gợi ý thô, nhưng bbox cuối lấy từ detect_lights.py.
4. **Crop frontend giữ tỉ lệ (contain)** — không kéo méo. Padding 8% (vì server đã mở rộng bbox rồi).
5. **Lọc nhiễu vùng sáng**: bỏ vùng quá lớn (LCD/text >5% ảnh), giữ icon nhỏ gọn.

## Deploy
- Sửa file trong `public/` (serve trực tiếp, không cần build)
- Restart server: tìm PID port 3000 (`netstat -ano | grep ":3000 .*LISTENING"`), `taskkill /PID <pid> /F`, rồi `node server.js` (background)
- Test nhanh API: gửi base64 + brand qua curl/python tới `http://localhost:3000/api/bhxe/diagnose`

## Test
- Ảnh test thật: `$LOCALAPPDATA/Temp/dash_real.jpg` (cụm đèn BRAKE/ABS từ Wikimedia), `vinfast-lux.jpg` (taplo Ford hiển thị "Kiểm tra lốp bên phải phía trước" từ thegioiphuongtien.vn)
- Verify crop bằng browser (CDP setFileInputFiles → click → chờ loading ẩn → scroll + screenshot) rồi vision_analyze kiểm tra ô crop có đúng không
