# Cu em — Hermes Knowledge Backup

Backup "kiến thức" của Cu em (Hermes Agent profile default) — Anh Đạt.

## Nội dung
- **skills/** — 98 custom skills (do Cu em / Anh Đạt tự tạo, KHÔNG phải bundled của Hermes)
- **memories/** — MEMORY.md + USER.md (kiến thức về home lab, dự án, sở thích Anh Đạt)
- **BRIEFING.md / SOUL.md** — nhân cách & đặc điểm
- **cron/** — jobs.json + state (3 luồng tự động)
- **scripts/** — 16 script cron hoạt động

## 📖 Khôi phục / base lại trên máy mới
Xem hướng dẫn đầy đủ: **[RESTORE.md](./RESTORE.md)**

Tóm tắt nhanh:
1. `git clone` repo này (cần `gh` đăng nhập — repo private)
2. Copy `memories/` + `BRIEFING.md` + `SOUL.md` → `%LOCALAPPDATA%\hermes\`
3. Copy `skills/*` → `%LOCALAPPDATA%\hermes\skills\`
4. Copy `cron/` + `scripts/` → `%LOCALAPPDATA%\hermes\`
5. Verify: mở phiên mới, hỏi "Em là ai?" → em phải trả lời là **"Cu em"**

Chi tiết từng bước + cách xử lý sự cố trong `RESTORE.md`.

## Ghi chú
- KHÔNG chứa bundled skills (tải lại từ Hermes), cache, backups tarballs
- 6.2M, gọn gàng
