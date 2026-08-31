---
name: zalo-oa-bot
description: "Dùng khi làm/tích hợp chatbot Zalo OA."
version: 1.1.0
author: Cu em
platforms: [linux, macos, windows]
triggers:
  - làm / sửa / mở rộng chatbot Zalo Official Account (OA)
  - webhook Zalo không verify được signature
  - cấu hình webhook, access token, secret key Zalo OA
  - knowledge base cho bot Zalo
---

# Zalo OA Bot — tích hợp chatbot Official Account

Xây dựng/bảo trì chatbot cho Zalo OA: nhận webhook, verify chữ ký, trả lời bằng AI (OmniRoute), gửi tin, kèm knowledge base + trang admin. Project tham chiếu: `~/zalo-oa-bot` (TS + Express, port 4810, tunnel `zalo.btdat.io.vn`).

## Kiến trúc

```
User Zalo → OA → POST webhook (Zalo → Cloudflare Tunnel → Express :4810/zalo/webhook)
  → verify signature → parse event user_send_text → AI (OmniRoute /v1)
  → gửi reply qua POST https://openapi.zalo.me/v3.0/oa/message/cs
```

## WEBHOOK SIGNATURE (quan trọng nhất — debug lâu nhất)

- Header: `X-ZEvent-Signature: mac=<hex>` — **phải strip tiền tố `mac=`**
- Timestamp: **nằm TRONG body** (`payload.timestamp`); header `X-ZEvent-Timestamp` thường undefined
- Công thức: `mac = sha256(appId + rawBody + timestamp + oaSecretKey)` — **SHA-256 thường, KHÔNG phải HMAC!** (thử HMAC → fail; plain sha256 mới khớp)
- `rawBody` = body nguyên gốc: bắt qua `express.json({ verify: (req,_res,buf) => { (req as any).rawBody = buf.toString("utf8") } })` — middleware đặt TRƯỚC route
- Chỉ tin tưởng khi verify khớp với request Zalo THẬT từ log (không phải giả lập)

Script kiểm tra nhanh: `scripts/verify-zalo-mac.mjs`. Hành trình debug + error codes: `references/zalo-webhook-debug.md`.

## Credentials — 4 giá trị, chỗ lấy KHÁC NHAU

| Biến | Lấy ở đâu |
|---|---|
| ZALO_APP_ID | developers.zalo.me → App → Thông tin ứng dụng |
| ZALO_APP_SECRET | developers.zalo.me → App → Cài đặt → Secret Key |
| ZALO_OA_SECRET_KEY | **oa.zalo.me → Cài đặt → Công cụ lập trình → Secret Key — KHÁC App Secret!** Dùng verify webhook |
| ZALO_ACCESS_TOKEN | developers.zalo.me → tools/explorer → Get Access Token (sống 25h) |
| ZALO_REDIRECT_URI | URL callback OAuth v4: `https://zalo.btdat.io.vn/oauth/callback` |

⚠️ App Secret ≠ OA Secret Key. Nhầm chỗ lấy → signature không bao giờ khớp (đã tốn nhiều thời gian). **Chú ý 2 secret này khác nhau: ZALO_APP_SECRET dùng cho OAuth access/refresh; ZALO_OA_SECRET_KEY dùng cho webhook signature.**

## App phải "kích hoạt" trước khi gọi API

- `-209 App has been not approved` → App mới tạo chưa kích hoạt: developers.zalo.me → App → bấm Kích hoạt (điền thông tin). Token cũ dùng được luôn sau đó
- `-201` = user_id sai; `-216` = access token hết hạn; `-212` = App chưa đăng ký API đó

## Website verification (Zalo yêu cầu xác minh domain)

- Thêm `<meta name="zalo-platform-site-verification" content="...">` vào `<head>` trang chủ
- Serve từ Express: `res.type("html").send(...)`; Zalo quét HTTPS public (Cloudflare OK)

## AI trả lời

- Model `cmd/deepseek/deepseek-v4-flash` qua OmniRoute `http://localhost:20128/v1` (stream:false trả JSON thuần)
- **DeepSeek là reasoning model**: `reasoning_content` = suy nghĩ nội bộ, TUYỆT ĐỐI không gửi cho user. Content rỗng → trả null, KHÔNG fallback sang reasoning (tránh lộ "Analyze the User's Request...")
- `max_tokens` ≥ 2000 (500 → hết token khi reasoning, content rỗng → lộ suy nghĩ)
- Trả lời có markdown `**` → **cleanMarkdown()** xóa trước khi gửi Zalo (Zalo hiển thị thô)

## 🔑 OAuth v4 — tự động refresh access token (deploy 2026-08-22)

Access token sống **25h** (API Explorer) hoặc **1h** (OAuth v4). Để không phải lấy thủ công mỗi ngày, chuyển sang OAuth v4 với refresh token thật (sống 3 tháng, dùng 1 lần).

### ✅ ĐÃ HOẠT ĐỘNG THÀNH CÔNG (2026-08-22)
- Token OAuth v4 mới prefix `kKbIJh7LZnIp...` trong `.env`, refresh token `dqlx3FCjQmsL...` — bot tự refresh, không cần lấy thủ công.
- Webhook URL (`/zalo/webhook`) ≠ OAuth Callback URL (`/oauth/callback`) — **2 chỗ khác nhau trên Zalo**, hay nhầm lẫn.
- Zalo OAuth v4 **bắt buộc PKCE** (`code_challenge` ở permission URL + `code_verifier` khi đổi code).

### ⚠️ Lỗi `-14003` — HAI nghĩa khác nhau (đừng nhầm)
Mã `-14003` xuất hiện ở 2 giai đoạn với 2 nguyên nhân riêng — chẩn đoán theo `error_name` trong trang lỗi, không chỉ con số:
| error_name | Nguyên nhân | Fix |
|---|---|---|
| `Invalid code verifier` | **Thiếu PKCE** — URL ủy quyền không gửi `code_challenge` | Thêm `code_challenge` + `code_challenge_method=S256` vào permission URL, `code_verifier` khi đổi code |
| `Invalid redirect uri` | **Callback URL không khớp** — URL khai báo trên Zalo ≠ `redirect_uri` bot gửi | Đối chiếu tuyệt đối (kể cả `/` cuối, `https://`) grep `redirect_uri` bot gửi vs cái đã khai báo |

Chuỗi lỗi nhìn thấy trong 1 phiên: `-14003 Invalid code verifier` (thiếu PKCE) → fix PKCE → `-14003 Invalid redirect uri` (khai báo callback không khớp). Cứ lần lượt theo `error_name`.

### Khai báo Callback URL — chỗ ĐÚNG cho OA API
- Với **Official Account API** (không phải Social Login), callback URL nằm ở **oa.zalo.me** → Official Account → **Cài đặt → General settings → "Official Account Callback URL"** (Công cụ lập trình / API). Không dùng developers.zalo.me cho OA API.
- Devs/zalo.me có mục "Callback URL / Redirect URI" là dành cho **Login Zalo** (Social) — nhầm chỗ này là cái bẫy hay gặp.
- Sau khi điền, mở `https://zalo.btdat.io.vn/oauth/authorize` → đồng ý → redirect về `/oauth/callback?code=` → bot đổi code → lưu token → thấy trang "✅ OAuth v4 thành công".

### Vì sao token API Explorer KHÔNG refresh được

- Token lấy qua **API Explorer** dù có refresh_token vẫn refresh qua API bị `404 "empty api"` (Zalo chỉ nhận refresh từ token OAuth v4 đầy đủ — Authorization Code flow có callback URL + app đăng ký).
- Lỗi gửi tin khi hết hạn: `-216 "Access token has expired"`.

### Module `src/zaloOAuth.ts` (mới) — thay cho `zaloToken.ts` cũ

- `buildAuthUrl(appId, redirectUri)` → tạo link ủy quyền `https://oauth.zaloapp.com/v4/oa/permission`
- `exchangeCodeForToken(appId, appSecret, code, redirectUri)` → đổi code → access+refresh
- `refreshZaloToken(appId, appSecret, refreshToken)` → tự refresh
- **BẮT BUỘC** header `secret_key` = **ZALO_APP_SECRET** (không phải OA Secret Key) cho cả access_token lẫn refresh_token. Thiếu secret_key → `404 empty api`.

### Routes trong `index.ts`

- `GET /oauth/authorize` → redirect tới Zalo ủy quyền
- `GET /oauth/callback?code=...` → đổi code thành access+refresh token, persist vào .env

### Flow setup 1 lần (sau đó tự động)

1. Khai báo **Official Account Callback URL** trong developers.zalo.me (hoặc app settings) = `ZALO_REDIRECT_URI`
2. Mở `https://zalo.btdat.io.vn/oauth/authorize` → đồng ý → Zalo redirect về callback kèm `?code=`
3. Bot đổi code → access+refresh token → lưu .env
4. Từ đó `sendTextMessage` tự refresh khi gặp -216, persist token mới

### `zaloSend.ts` đã đổi

- Import `refreshZaloToken` từ `./zaloOAuth.js` (không còn `zaloToken.js`)
- `sendTextMessage` nhận thêm `appSecret`; khi token lỗi → gọi `refreshZaloToken(appId, appSecret, refreshToken)`.

## Knowledge Base (KB) + Admin

- SQLite qua `node:sqlite` (Node 24 built-in, không cài gì): `import { DatabaseSync } from "node:sqlite"`
- TS cast: `db.prepare(...).all()` trả `Record<string,SQLOutputValue>[]` → `as unknown as KbDocument[]`
- Bảng `documents`: title, content, keywords, category, enabled, created_at
- Search: điểm keywords (×5) > title (×3) > content (×1), chỉ lấy enabled; append kết quả vào system prompt dạng `=== DỮ LIỆU THAM KHẢO ===`
- Import Q&A: split `/\n(?=\d{1,2}\s*[.、]\s*[^\n]*\?)/` — **chỉ tách khi dòng đầu kết thúc bằng `?`** để không tách nhầm mục con đánh số (1., 2., 3...) trong câu trả lời (bài 10 câu hỏi hồ sơ bồi thường từng tách thành 18 mục sai)
- Admin: `/admin` (static html+js trong public/) + API `/api/kb` bảo vệ bằng header `x-admin-token` (so ADMIN_TOKEN trong .env)

## Pitfalls

1. **Inline `<script>` trong Express template literal**: JS chứa `</` (vd regex `replace(/</g,'&lt;')`) → browser hiểu đóng tag sớm → script cắt rỗng → trang "chờ kết nối" mãi. FIX: tách file .js riêng (express.static), dùng `\u003C` thay `<`
2. **dotenv không override**: 2 dòng cùng key → giữ dòng đầu; append trùng key vô dụng. Sửa đúng dòng gốc (sed theo số dòng)
3. **tsx watch không reload env**: sửa .env phải kill + start lại cả process
4. **SQLite "database is locked"**: 2 instance server cùng mở DB (tsx watch restart cũ chưa chết). Kill hết node cũ rồi start lại
5. **DNS công ty không resolve subdomain mới**: test bằng `curl --resolve domain:443:<cloudflare-ip>`; Zalo dùng DNS public nên không ảnh hưởng
6. **Log stdout background bị buffer**: không thấy log qua process poll → ghi log ra FILE (`fs.appendFileSync`) + API đọc + trang web xem log (pattern UI: `references/zalo-webhook-debug.md`)
7. **UI chuẩn áp dụng cho trang log/admin** (đo bằng CDP): tap target ≥ 40px, font ≥ 11px, padding card đều; xem skill `web-ui-standards`
8. **Kill đúng process bot, không kill session bash**: lọc `CommandLine -like '*tsx*src/index.ts*'` — pattern `*zalo-oa-bot*` dính cả bash session của lệnh đang chạy (`cd ~/zalo-oa-bot`). Dùng pattern căn chỉnh chi tiết hơn.
9. **OAuth secret_key**: dùng **ZALO_APP_SECRET** trong header `secret_key`, KHÔNG dùng ZALO_OA_SECRET_KEY (2 giá trị khác nhau, hay nhầm dẫn đến 404).
10. **Bot/cloudflared tự chết ngắt quãng**: chạy trong background session tạm của Hermes → session chết thì process chết → user thấy "bot không trả lời"/"site 530". FIX: Task Scheduler watchdog mỗi 5' + Startup folder (script start idempotent). Chi tiết recipe → `references/windows-service-keepalive.md`.

## Tích hợp vietnamese-business-comms (BHViet chat)
- Prompt + runtime validator JS đã gắn trong `src/ai.ts` — xem chi tiết `references/vietnamese-business-comms-integration.md`.
- Cài skill: `npx skills add trussary/vietnamese-language-skill -y` (project) + `-g -y` (global symlink).
- Full audit: `python .agents/skills/vietnamese-business-comms/scripts/validate_copy.py <file> --register consult`.

## Verify nhanh

```bash
# Tính MAC từ dữ liệu thật (log request Zalo)
node scripts/verify-zalo-mac.mjs <appId> <rawBody> <timestamp> <oaSecretKey> [signature-từ-header]
# MATCH = verify OK; mismatch → sai secret hoặc sai công thức
```
