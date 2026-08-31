---
name: web-ui-standards
description: "Chuẩn UI/UX web — contrast, tap target, breakpoint."
version: 1.0.0
author: Cu em
category: frontend
platforms: [linux, macos, windows]
triggers:
  - làm web mới / redesign
  - UI nhìn xấu / vỡ layout
  - không biết chọn màu / font / khoảng cách nào
  - kiểm tra web có chuẩn không
  - responsive mobile xấu
  - chữ khó đọc / nút khó bấm
tags: [ui, ux, web, standards, wcag, responsive, accessibility, css, mobile]
related_skills: [taste-skill, mobile-ui-usability, frontend-ui-workflow, fe-qa-checklist, popular-web-designs]
---

# Web UI Standards — Tiêu chuẩn web dễ nhìn, không vỡ, thân thiện

Áp dụng cho MỌI web (landing, dashboard, game, tool, app). Nguồn: WCAG 2.2 (W3C), Apple HIG, Material Design 3, 4pt grid. Đây là **minimum chuẩn** — phải đạt trước khi bàn tới đẹp/xấu.

## 1. MÀU & CONTRAST (WCAG 2.2)

| Loại | Tỷ lệ tối thiểu | Tiêu chuẩn |
|---|---|---|
| Text thường | **4.5:1** | WCAG 1.4.3 (AA) |
| Text lớn (≥18pt / ≥14pt bold) | **3:1** | WCAG 1.4.3 |
| UI components, borders, icons, graphs | **3:1** so với màu kề | WCAG 1.4.11 Non-text |
| AAA (khuyến khích) | 7:1 text thường, 4.5:1 text lớn | WCAG 1.4.6 |

- **Chuẩn đo nhanh:** dùng webaim.org/resources/contrastchecker/ hoặc tool check contrast.
- **Quy tắc thực dụng (đã đúc kết):** nền tối #0d0806 → text #f5ead0 (cao), dim #b8a898 (vừa). Accent phải ≥#ad80ff để đủ contrast trên nền tối. Chữ "khó nhìn" → **fix contrast trước**, rồi mới bàn layout.
- Màu xám mờ trên nền xám = fail ngay.

## 2. TAP TARGET (nút bấm)

| Tiêu chuẩn | Kích thước | Nguồn |
|---|---|---|
| **Khuyến nghị** | **44×44px** | Apple HIG, WCAG 2.5.5 (AAA) |
| Material Design 3 | 48×48dp | Google |
| **Tối thiểu** | **24×24px** (và phải có spacing ≥24px giữa các target) | WCAG 2.5.8 (AA) |
| Khoảng cách giữa 2 target | ≥8px | UX patterns |

- Trên mobile luôn target ≥44px. Desktop có thể 32-40px nhưng nên 44px.
- Nút nhỏ chỉ icon → tăng hit area bằng padding/pseudo-element, không nhất thiết to hình ảnh.

## 3. BREAKPOINTS (responsive)

**Mobile-first**, tối thiểu 3 breakpoint (Hoverify 2026):
- Mobile: **≤576px** (kiểm tra thực tế 375×667 — iPhone SE, và 390×844 — iPhone 12/14)
- Tablet: **577–1024px** (kiểm tra 768px, 1024px)
- Desktop: **≥1025px** (kiểm tra 1280×800)
- Large desktop: 1441px+

**Quy tắc:**
- Content quyết định breakpoint, không phải device cụ thể.
- Container max-width: **~1100-1200px** desktop, centered.
- Dùng `clamp()` cho font fluid: `font-size: clamp(16px, 1rem + 0.5vw, 24px)` — ít nhất 16px mobile.
- Base font ≥16px (browser default), line-height 1.5.

## 4. KHÔNG VỠ LAYOUT (overflow/reflow)

**WCAG 1.4.10 Reflow (AA):** content phải hiển thị **không scroll ngang ở 320px** width (tương đương 1280px @ 400% zoom).

Checklist chống vỡ:
- [ ] `overflow-x: hidden` trên body (fallback), nhưng **tìm root cause** — không che bằng overflow:hidden khi content bị cắt
- [ ] Không fixed width cứng trên element (`width: 400px` → vỡ mobile). Dùng `max-width: 100%`, `width: 100%`, flex/grid với `min-width: 0`
- [ ] Images: `max-width: 100%; height: auto`
- [ ] Flexbox: child dùng `flex-wrap: wrap` khi cần; text dài → `min-width: 0` + `word-break: break-word` / `overflow-wrap: anywhere`
- [ ] Grid: `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))` thay vì cột cố định
- [ ] Table: `overflow-x: auto` trên wrapper (data table được phép 2D scroll theo WCAG)
- [ ] `100vw` → dùng `100%` (100vw gây horizontal scroll do scrollbar)
- [ ] Test zoom 400% (Ctrl + +): không mất content/function

## 5. TYPOGRAPHY (WCAG 1.4.12 Text Spacing + readability)

- Base: **16px**, line-height ≥**1.5**
- Paragraph spacing: ≥2× font size
- Letter-spacing ≥0.12em, word-spacing ≥0.16em khi user override — không mất content
- Hệ thống scale: dùng 4pt/8pt grid — 16/20/24/32/40/48px (hoặc rem: 1/1.25/1.5/2/2.5/3rem)
- Font tối đa 2-3 family: 1 display + 1 body (+1 mono cho code)
- Font tiếng Việt: **PHẢI có glyph VN** (subset vietnamese). Font pixel (Press Start 2P, Pixelify...) KHÔNG có glyph VN → fallback lệch. Có glyph VN: Roboto Mono, Space Mono (đã verify subset?), VT323, Be Vietnam Pro, Inter
- Line length: 45-75 ký tự/dòng (65 lý tưởng) — `max-width: 65ch` cho đoạn văn

## 6. SPACING — 4pt GRID (Atlassian, UX Planet)

Mọi spacing/sizing là **bội số của 4** (4, 8, 12, 16, 24, 32, 48, 64...):
- Button padding: 12px+ (mobile), space giữa buttons 8-16px
- Card padding: 16-24px
- Section gap: 32-64px
- Gutter page mobile: 16px, desktop: 24-32px
- Dùng CSS var cho spacing tokens, không hardcode rải rác

## 7. LAYOUT PATTERNS

- **Mobile:** 1 cột, content-first, nút bấm dễ chạm, hamburger menu khi nav dài
- **Desktop:** multi-column, content centered, max-width container
- **Nav mobile:** bottom nav hoặc hamburger — KHÔNG dồn hết link vào 1 hàng nhỏ
- **Footer/back-to-top/overlay:** check z-index + không che content (position: fixed overlap)
- **Form:** label + input ≥44px height, error message đủ contrast, không chỉ dùng màu để báo lỗi

## 8. CHECKLIST NHANH (chạy trước khi xong)

- [ ] Contrast ≥4.5:1 text, ≥3:1 non-text (kiểm tra màu mờ/dim)
- [ ] Tap target ≥44px mobile, ≥24px tối thiểu
- [ ] Không scroll ngang ở 320px (WCAG Reflow)
- [ ] 3 breakpoint test: 375px / 768px / 1280px
- [ ] Base font ≥16px, line-height ≥1.5, chữ VN đủ dấu (font có glyph)
- [ ] Spacing bội số 4
- [ ] Images max-width 100%, không fixed width
- [ ] Console 0 lỗi JS

## Liên hệ skill khác

- **Đẹp/sáng tạo (anti-slop):** `taste-skill` (landing/portfolio), `popular-web-designs` (54 design system mẫu), `claude-design` (quy trình design)
- **QA thực chiến:** `frontend-ui-workflow` (checklist UI change), `mobile-ui-usability` (đo tap target/font bằng CDP), `fe-qa-checklist` (QA btdat.io.vn)
- **Đo lường thật:** dùng JS snippet trong `mobile-ui-usability` để đếm tap target <40px, font <10px; dùng agent-browser `set viewport 375 667` để test mobile nhanh
