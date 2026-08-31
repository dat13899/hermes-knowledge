---
name: zalo-oa-chatbot
description: Zalo OA chatbot — webhook nhận/gửi tin, verify signature.
---

# Zalo OA Chatbot

Chatbot cho Zalo Official Account: nhận tin nhắn qua Webhook, trả lời tự động qua OpenAPI (tin tư vấn). Project mẫu đã build: `~/zalo-oa-bot` (Express + TS, port 4810, webhook URL `https://zalo.btdat.io.vn/zalo/webhook`).

## Khi nào dùng
- Tích hợp chatbot vào Zalo OA (nhận + gửi tin nhắn 2 chiều)
- Cần verify webhook signature, gửi tin qua API, hiểu quota 48h
- Chỉ OA (Official Account) mới có API — Zalo cá nhân KHÔNG

## Kiến trúc
```
User → OA → Webhook POST (header X-ZEvent-Signature) → Express /zalo/webhook
   → verify HMAC-SHA256 → AI (OmniRoute/DeepSeek) → POST openapi.zalo.me/v3.0/oa/message/cs → User
```
Webhook phải **respond 200 trong ≤ 2s** (Zalo báo webhook chết nếu không) → respond trước, xử lý async sau.

## Luồng thiết lập
1. Có OA → developers.zalo.me tạo **Zalo App** → OA uỷ quyền `official_account_access_token`
2. Lấy 4 giá trị: `ZALO_APP_ID`, `ZALO_APP_SECRET`, `ZALO_OA_SECRET_KEY`, `ZALO_ACCESS_TOKEN`
3. Cấu hình Webhook URL (HTTPS domain cố định, KHÔNG host:port) + bật event "Người dùng gửi tin nhắn"
4. Expose qua Cloudflare Tunnel + CNAME (xem skill cloudflare-tunnel)

## API chính
- **Nhận**: Webhook POST, event `user_send_text` → `sender.id`, `recipient.id`, `message.text`, `msg_id`, `timestamp`
- **Verify**: `X-ZEvent-Signature = HMAC-SHA256(key=OAsecretKey, data=appId + rawBody + timestamp)`, timestamp từ header `X-ZEvent-Timestamp`, so sánh timing-safe
- **Gửi**: `POST https://openapi.zalo.me/v3.0/oa/message/cs` — header `access_token`, body `{recipient:{user_id}, message:{text}}`, text ≤ 2000 ký tự

## Quota (1/2026)
- **Trong 48h** sau tương tác cuối: tin tư vấn (cs) **miễn phí không giới hạn**
- **Ngoài 48h**: chỉ tin welcome (3 lượt) hoặc ZNS/broadcast trả phí
- Response trả `data.quota.remain/total`

## Pitfalls
1. **express.json({verify}) bắt raw body** — middleware đọc stream trước (express.json) thì KHÔNG lấy được raw body cho signature. Dùng `express.json({ verify: (req,_res,buf) => { (req as any).rawBody = buf.toString("utf8") } })`
2. **dotenv KHÔNG override key trùng** — append dòng `KEY=value` vào .env đã có key cũ → im lặng vô hiệu (giữ giá trị cũ). Phải SỬA dòng gốc (sed theo số dòng)
3. **tsx watch không reload .env** — sửa .env xong phải kill + start lại hoàn toàn, không chỉ chờ watch restart
4. **OmniRoute trả SSE kể cả stream:false** — `await res.json()` fail "Unexpected token 'd'". Parse dòng `data: {...}`, ghép delta.content (chi tiết skill omniroute-management)
5. **DeepSeek content rỗng → reasoning_content** — fallback khi content empty
6. **taskkill trong git-bash Hermes**: `taskkill //F` FAIL ("Invalid argument/option") vì MSYS conversion disabled — dùng `taskkill /F /PID <pid>` (1 slash)
7. **Docs developers.zalo.me là SPA**: nội dung trong iframe cross-origin (`stc-developers.zdn.vn/docs/v2/...?lang=vi`) — không đọc được qua `f.contentDocument`. Fix: lấy `iframe.src` rồi navigate thẳng vào URL đó
8. **Tiếng Việt trong curl -d qua bash** bị lệch encoding khi tính MAC test — test signature bằng payload ASCII

## Test cục bộ
- `scripts/zalo-signature-test.js` — tính MAC theo công thức Zalo (payload mẫu từ docs hoặc truyền args)
- Verify pass: gửi POST /zalo/webhook signature đúng → 200 `{"ok":true}`; sai → 401
- Endpoint dev: `GET /` health, `POST /zalo/webhook`, `POST /api/test-send` (header x-test-token), `GET /api/debug/history`

## Files
- `references/zalo-api.md` — chi tiết event list, payload, response, cấu hình webhook
- `scripts/zalo-signature-test.js` — tính MAC test cục bộ
