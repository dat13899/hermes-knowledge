# Zalo token ops — vòng đời, giới hạn API Explorer, monitor

Ghi lại từ phiên vận hành thật (2026-08-21) trên `~/zalo-oa-bot`.

## Vòng đời token

- Access token: **25 giờ** (KHÔNG phải 90 ngày — thông tin cũ sai)
- Refresh token: 3 tháng, dùng 1 lần (sau refresh token cũ vô hiệu)
- Authorization code: 10 phút, dùng 1 lần
- Refresh endpoint: `POST https://oauth.zaloapp.com/v4/oa/refresh_token` body form `{app_id, grant_type: "refresh_token", refresh_token}`

## ⚠️ API Explorer token — KHÔNG refresh qua API được (quan trọng)

- Token lấy qua **API Explorer** (developers.zalo.me/tools/explorer) có kèm refresh_token NHƯNG gọi refresh API vẫn lỗi:
  `404 "You currently access to an empty api"` — cả khi thêm `secret_key` vào body.
- Zalo refresh v4 CHỈ hoạt động với token lấy qua OAuth v4 đầy đủ (Authorization code flow có redirect + app đăng ký).
- Hệ quả thực tế: access token hết hạn sau 25h → **lấy lại thủ công qua API Explorer mỗi ngày**, không có cron tự refresh.
- Dấu hiệu hết hạn trong `webhook.log`: `[SEND] failed: ... {"error":-216,"message":"Access token has expired"}`.

## Cập nhật token vào .env

- **KHÔNG dùng sed** — token chứa `/` và `-` làm sed fail (`unterminated s` command).
- Dùng python script:
```python
import re
env = open(r"C:\Users\datel\zalo-oa-bot\.env", encoding="utf-8").read()
env = re.sub(r"^ZALO_ACCESS_TOKEN=.*$", "ZALO_ACCESS_TOKEN=" + ACCESS, env, flags=re.M)
env = re.sub(r"^ZALO_REFRESH_TOKEN=.*$", "ZALO_REFRESH_TOKEN=" + REFRESH, env, flags=re.M)
open(r"C:\Users\datel\zalo-oa-bot\.env", "w", encoding="utf-8").write(env)
```

## Monitor token — KHÔNG gửi tin vào Zalo (user yêu cầu 2026-08-21)

- Zalo chỉ là kênh khách-chat-bot. **CẤM gửi tin test/quản trị/kiểm tra vào Zalo** (kể cả curl test, test-send endpoint, cron check). Mọi cảnh báo hệ thống → Telegram (`deliver: telegram:Home`).
- Cron `check_zalo_token.sh` (Hermes scripts dir) hoạt động bằng cách **đọc webhook.log**:
  - Có `-216` trong log gần đây → output cảnh báo (non-empty) → Hermes deliver Telegram.
  - Có `[SEND]` thành công < 25h → exit 0 (im lặng, watchdog pattern).
  - Không chắc chắn → nhắc nhẹ.
- Xóa log cũ khi đổi token (`rm -f webhook.log`) để script không báo lỗi -216 cũ.

## Encoding tiếng Việt (Windows git-bash)

- `curl -d '{"text":"tiếng Việt"}'` từ git-bash → **mojibake** khi tới Zalo (`?` thay dấu, `Lỗi font`). LUÔN dùng Node/tsx script cho payload UTF-8 (fetch chuẩn) — kể cả cron check token dùng `node -e "fetch(...)"` không dùng curl -d.
- Import dữ liệu tiếng Việt vào KB: dùng tsx script (`addDocument`), không dùng `curl -X POST -d` (sẽ ghi mojibake vào DB).

## Khi "bot trả lời trong log nhưng Zalo không thấy"

1. `tail webhook.log` → tìm `[SEND] failed` + error code.
2. Nguyên nhân phổ biến nhất: **server cũ vẫn chạy giữ port** (tsx watch/node process cũ giữ token cũ dù đã sửa .env). Kiểm tra `netstat -ano | grep ":4810" | grep LISTEN` lấy PID, so với process mới.
3. Fix: `taskkill /F /IM node.exe` (MSYS rewrite `//F` thành sai — dùng `/F` một gạch) → `rm -f webhook.log` → `npm run dev` → verify bằng `curl localhost:4810/api/test-send` trả `error:0`.
