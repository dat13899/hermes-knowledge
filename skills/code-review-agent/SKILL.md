---
name: code-review-agent
description: >
  Subagent chuyên review HTML/CSS cho đúng cú pháp, responsive desktop & mobile.
  Tự động chạy review.py rồi kiểm tra server, page size, lỗi cú pháp.
trigger: user asks to review code, check responsive, fix layout bugs
---

# Code Review Agent

## Workflow

1. **Run review script**
   ```bash
   python ~/AppData/Local/hermes/scripts/review.py
   ```
   Script kiểm tra:
   - HTML: thiếu viewport, DOCTYPE, lỗi đóng tag, các string cấm (skip-link, kb-overlay)
   - CSS: @media queries, prefers-reduced-motion, px > 100
   - Server: localhost:3000 & btdat.io.vn reachable
   - Live pages: grep forbidden patterns, check size > 2KB

2. **If errors found** → delegate_task cho subagent sửa, pass full error list vào context

3. **If warnings found** → report cho user, hỏi có fix không

4. **After fix** → chạy lại `review.py` verify

## Responsive Checklist (manual)

| Item | Desktop (>960px) | Tablet (720-960) | Mobile (<720px) |
|------|-----------------|-----------------|----------------|
| No horizontal scroll | ✓ | ✓ | ✓ |
| Nav works (burger menu) | — | ✓ | ✓ |
| Text readable (no overflow) | ✓ | ✓ | ✓ |
| Sidebar collapses | — | — | documents |
| Reader panel full-width | — | — | documents |
| Dashboard swaps to column | — | 960px | ✓ |
| Touch targets >= 44px | — | — | ✓ |

## Review Sources

- Source: `~/service-dashboard/public/`
- Live: `https://btdat.io.vn`
- Local: `http://localhost:3000`

## Pitfalls

- **Patch nhỏ dễ hỏng** — dùng write_file full file thay patch nếu sửa > 3 dòng
- **Server die ngầm** — luôn curl health check sau restart
- **Cloudflared tunnel** nếu restart node mà không restart cloudflared → site serve cache nginx/CF
