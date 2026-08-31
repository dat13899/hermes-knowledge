---
name: zalo-oa-integration
description: Use when tích hợp Zalo OA — webhook, verify signature.
---

# Zalo OA Integration

Tích hợp chatbot với Zalo Official Account (OA): nhận tin nhắn user qua webhook, gửi tin nhắn qua OpenAPI, verify chữ ký, auto-refresh token. Đã triển khai tại `~/zalo-oa-bot` (TS + Express + OmniRoute).

## Kiến trúc chuẩn

```
User Zalo → OA → POST webhook (https://zalo.btdat.io.vn/zalo/webhook)
  → verify X-ZEvent-Signature → trả 200 NGAY (≤2s)
  → xử lý bất đồng bộ → AI (OmniRoute) → POST https://openapi.zalo.me/v3.0/oa/message/cs → user
```

## 4 credentials (lấy từ 2 nơi KHÁC NHAU — lỗi phổ biến nhất)

| Var | Lấy ở đâu | Ghi chú |
|---|---|---|
| `ZALO_APP_ID` | developers.zalo.me → App | Số dài ~19 chữ số |
| `ZALO_APP_SECRET` | developers.zalo.me → App → Cài đặt → "Copy secret key" | Chuỗi dài, KHÁC App ID |
| `ZALO_OA_SECRET_KEY` | **oa.zalo.me** → Cài đặt → **Công cụ lập trình** | **KHÁC App Secret!** — verify webhook |
| `ZALO_ACCESS_TOKEN` + `ZALO_REFRESH_TOKEN` | developers.zalo.me → API Explorer | Access 25h, Refresh 3 tháng |

⚠️ **OA Secret Key ≠ App Secret Key.** App Secret chỉ dùng lấy token; OA Secret Key (trên oa.zalo.me) dùng verify webhook. Nhầm 2 cái này → MAC không bao giờ khớp.

⚠️ **Access token chỉ sống 25 giờ** (không phải 90 ngày). Refresh token sống 3 tháng, **chỉ dùng 1 lần** — sau refresh phải lưu refresh token MỚI ngay.

## Webhook — quy tắc bắt buộc

1. **LUÔN trả HTTP 200** cho mọi request (kể cả sai signature, sai JSON). Zalo hủy webhook nếu nhận ≠200. Signature sai → log + bỏ qua, vẫn 200.
2. **Trả 200 trong ≤2 giây** — xử lý bất đồng bộ (fire-and-forget) sau khi respond.
3. **Webhook URL phải HTTPS public** — dùng Cloudflare Tunnel (xem skill cloudflare-tunnel).
4. **Xác minh website**: Zalo yêu cầu thẻ meta `<meta name="zalo-platform-site-verification" content="...">` ở đầu `<head>` trang chủ. Nếu trang chủ là JSON API, phải trả HTML chứa meta.

## Verify X-ZEvent-Signature (2 bug chí mạng)

Header: `X-ZEvent-Signature: mac=<hex>` — có prefix **`mac=`**, phải strip.

Công thức: `mac = hmac_sha256(OAsecretKey, appId + rawBody + timestamp)`

- **`rawBody`**: body JSON NGUYÊN GỐC (chuỗi nhận được, không JSON.stringify lại — Zalo Support xác nhận).
- **`timestamp`**: nằm TRONG BODY (`payload.timestamp`, milliseconds) — KHÔNG phải header `X-ZEvent-Timestamp` (header này undefined!).
- **`appId`**: `payload.app_id` (hoặc env ZALO_APP_ID).

```ts
const cleanSig = signature.startsWith("mac=") ? signature.slice(4) : signature;
const mac = crypto.createHmac("sha256", oaSecretKey).update(appId + rawBody + timestamp).digest("hex");
// so sánh timing-safe, length-check trước
```

## Gửi tin nhắn

```
POST https://openapi.zalo.me/v3.0/oa/message/cs
Header: access_token: <token>
Body: { "recipient": { "user_id": "<user_id>" }, "message": { "text": "<text max 2000 chars>" } }
```

- **user_id lấy từ webhook** `payload.sender.id` — KHÔNG hardcode (ID thật ≠ ID trong docs).
- Lỗi thường gặp:
  - `-209 "App has been not approved"` → App chưa **kích hoạt** trên developers.zalo.me (không phải "chờ duyệt").
  - `-201 "user_id is invalid"` → user_id sai/giả.
  - `-216/-124` → token hết hạn → auto-refresh rồi gửi lại.
- **Quota**: trong 48h sau tương tác cuối user, tin tư vấn (cs) miễn phí không giới hạn; ngoài 48h phải dùng welcome (3 lượt) hoặc ZNS/broadcast trả phí.

## Refresh token tự động

```
POST https://oauth.zaloapp.com/v4/oa/refresh_token
Content-Type: application/x-www-form-urlencoded
app_id=<appId>&grant_type=refresh_token&refresh_token=<refreshToken>
```

- Refresh token dùng 1 lần → **persist ngay** access + refresh mới vào `.env`.
- Bọc trong send: khi gặp lỗi token, refresh → set env → gửi lại 1 lần.

## Debug log cho người dùng

Zalo gửi request nhưng bot không trả lời → **nghi signature sai trước tiên**. Log mọi webhook ra FILE (không chỉ stdout — background bị buffer), và dựng trang log public để user tự theo dõi:
- `GET /log` — HTML card UI, màu theo loại (WEBHOOK/EVENT/AI/SEND/ERROR), filter chips, thống kê, auto-refresh 3s.
- `GET /api/log` — JSON trả entries parse sẵn.
- Format dòng log chuẩn: `[ISO time] [TAG] message` — tag viết HOA để parse dễ.
- User phàn nàn "khó nhìn" → card-based UI (không phải raw text).

## Pitfalls

- **Docs SPA**: developers.zalo.me dùng iframe docs — đọc bằng `goto_url` thẳng URL iframe (`https://stc-developers.zdn.vn/docs/v2/...`), không đọc được qua `contentDocument` (cross-origin).
- **Lọc cú pháp**: nếu bật "Lọc cú pháp" trên webhook, chỉ nhận tin bắt đầu bằng `#` — phải TẮT.
- **Event tối thiểu**: chỉ cần bật "Người dùng gửi tin nhắn văn bản" (`user_send_text`) cho chatbot text.
- **express.json({verify})**: bắt rawBody bằng `verify` callback của express.json — KHÔNG dùng middleware lắng nghe `req.on('data')` (bị express.json consume trước → treo).

## Support files
- `references/zalo-webhook-notes.md` — chi tiết payload, event list, error codes, community insights
- `templates/zalo-oa-server.ts` — server Express template hoàn chỉnh (webhook + send + refresh + log)
