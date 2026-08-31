# Ngày đầu tiên: 08082026 — "Cỗ Máy Ý Tưởng" (Idea Forge)

Build 08/08/2026, trang đầu tiên của daily.btdat.io.vn. Làm mẫu cho các ngày sau.

## Ý tưởng

Meta: 1 cỗ máy pixel-fantasy sinh ý tưởng ngẫu nhiên — chính nó "tự nói về" chức năng của cả site
(mỗi sáng một ý tưởng mới). Không cần hỏi anh, tự chọn vì vui + dễ verify.

## Cấu trúc

1 file `index.html` duy nhất (CSS + JS inline, không CDN nào ngoài Google Fonts):
- **3 bánh xe** (arrays): Đối tượng × Hành động × Công nghệ, mỗi bánh 20 lựa chọn
- **Seed theo ngày**: `xmur3(str) + mulberry32(seed)` → combo ổn định theo ngày (mở trang luôn có
  idea cố định cho hôm đó), dùng `'ideaf' + yyyy + mm + dd` làm seed string
- **Nút QUAY MÁY**: setInterval 55ms nháy giá trị ngẫu nhiên (hiệu ứng quay), sau 900ms chốt kết quả
- **Âm thanh retro**: WebAudio oscillator (square/triangle), sfxSpin = 220→330→440Hz, sfxDone = 523→659→784
- **Lịch sử**: localStorage key `'ideaforge-hist-08082026'`, chống trùng liên tiếp, tối đa 30 item
- **Sao chép**: navigator.clipboard + fallback textarea execCommand

## Giao diện

Theme tối retro terminal: bg `#0d0806`, panel `#1a130d`, text `#f5ead0`, dim `#b8a898`,
accent `#f0b36a`, scanline `rgba(0,0,0,.035)` lặp 1px/4px. Nút chính gradient cam có box-shadow
3D bấm lún (`transform: translateY(4px)`), min-height 54px. Mobile-first max-width 560px.

## Verdict sau khi verify

- Mobile 375×667 + desktop 1280×800 đều không vỡ, không scroll ngang, tap ≥44px
- JS boot chạy đúng (slot có giá trị seed theo ngày)
- **Lỗi font tiếng Việt trên Android** phát hiện SAU khi user báo → fix bằng Roboto Mono
  (xem SKILL.md phần FONT TIẾNG VIỆT — đây là pitfall quan trọng nhất, áp dụng MỌI ngày)

## Cảm hứng / nguồn

Không dùng nguồn cụ thể — tự nghĩ từ yêu cầu "mỗi ngày một ý tưởng". Có thể tham khảo
`web_search` với query: "web app ideas", "creative web experiments", "fun interactive website",
"generative art web", "useful micro tools".
