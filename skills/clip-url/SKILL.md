---
title: clip-url
name: clip-url
description: Tự động lưu URL/file vào Obsidian vault — extract nội dung, tóm tắt, tạo markdown.
category: productivity
---

# Clip URL → Obsidian

Tự động khi user gửi link article hoặc file vào Telegram:
1. Detect URL trong message
2. Chạy `python /c/Users/datel/dlv/clip.py <URL>`
3. Đọc kết quả: đường dẫn file .md
4. Báo user: tiêu đề, tags, đường dẫn

## Cách dùng

**User gửi link:**
- Nếu chỉ có link + ko có instructions khác → auto clip
- Nếu link + "clip" → cũng clip
- Báo kết quả: `📥 Clipped: {title} | {tags}`

**User gửi file (PDF/DOCX/txt):**
- Detect file path → `python clip.py <path>`
- Báo kết quả tương tự

## Script

Script: `/c/Users/datel/dlv/clip.py`
- Dùng `trafilatura` extract nội dung web
- Lưu vào `~/Documents/Obsidian Vault/inbox/` dạng `YYYY-MM-DD - slug.md`
- Frontmatter: source, clipped date, tags, author
- Body: tóm tắt + nội dung gốc

## Cài đặt

```bash
uv pip install requests trafilatura
```

Obsidian vault path: `C:\Users\datel\Documents\Obsidian Vault`
