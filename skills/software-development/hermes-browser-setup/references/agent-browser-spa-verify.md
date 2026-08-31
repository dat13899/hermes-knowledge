# agent-browser: Verify SPA React nhanh (btdat.io.vn, daily ideas...)

Recipe đã test OK 10/08/2026 trên btdat.io.vn (React SPA pixel-RPG) và daily ideas. Dùng khi cần verify nhanh một trang JS-heavy mà web_extract fail hoặc Hermes browser nặng nề.

## Luồng verify nhanh (copy-paste được)

```bash
# 1. Mở trang — KHÔNG tin timeout (xem Pitfalls SKILL.md): open có thể timeout 60s dù đã navigate xong
agent-browser open "https://btdat.io.vn" &

# 2. Verify navigation THỰC SỰ thành công — đừng dựa vào exit code
agent-browser get url        # → https://btdat.io.vn/
agent-browser get title      # → title trang

# 3. Console check JS errors — quan trọng nhất (browser_console của Hermes cũng làm được, nhưng nhanh hơn)
agent-browser console        # sạch = 0 lỗi JS

# 4. Snapshot accessibility tree + refs
agent-browser snapshot       # → @e1... thấy nav/heading/buttons

# 5. Read rendered DOM (chính là thứ web_extract fail) — đọc được cả ASCII art
agent-browser read           # không URL = đọc active tab

# 6. Click test
agent-browser click @e12     # click theo ref

# 7. Screenshot desktop + mobile
agent-browser screenshot "C:\Users\datel\tmp\desktop.png"        # path WINDOWS bắt buộc
agent-browser set viewport 375 667                                # ⚠️ lệnh này, KHÔNG phải `viewport`
agent-browser screenshot "C:\Users\datel\tmp\mobile.png"
```

## Kết quả đo (btdat.io.vn, 10/08/2026)

- open + snapshot: ~0.5s (Hermes browser ~2-5s)
- `read` URL không cần Chrome: 1.4s (HN)
- Console: 0 lỗi JS
- Viewport mobile 375px: hamburger menu xuất hiện đúng (responsive OK)

## Phát hiện thật từ test (value)

- btdat.io.vn mobile: quick links `[dashboard] [documents] [widgets]` + dock icons ~28-32px < 44px chuẩn tap target → bug UX thật
- Desktop: "LV.30" lặp 2 lần (logo + status bar), dashed line lạ giữa trang → cosmetic

## Lưu ý

- `agent-browser read <url>` KHÔNG launch Chrome (fetch thẳng) — nhanh nhất, tiết kiệm tài nguyên
- `agent-browser read` (không URL) đọc rendered DOM active tab — dùng cho SPA đã mở
- `--json` cho mọi lệnh khi cần parse
- Chrome for Testing 151 tự tải (192MB, tại ~/.agent-browser/browsers/) — không ảnh hưởng Chrome chính
