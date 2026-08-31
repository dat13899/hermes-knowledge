---
name: zalo-oa
description: Use when building a Zalo OA webhook, chatbot, or API.
---

# Zalo Official Account (OA) Integration

Tích hợp chatbot 2 chiều cho Zalo OA: webhook nhận tin + API gửi tin. **Chỉ OA mới được dùng API chatbot — Zalo cá nhân không hỗ trợ.** Đã verify với docs Zalo (08/2026).

## Đọc tài liệu Zalo Developers (bắt buộc biết)

Trang `developers.zalo.me/docs/...` là **SPA**, nội dung nằm trong **iframe cross-origin** — `curl`/web_extract chỉ lấy shell HTML rỗng:

1. Dùng browser mở trang, bấm "Đồng ý" cookie banner nếu body trống.
2. Đọc `iframe.src` (dạng `https://stc-developers.zdn.vn/docs/v2/<path>?lang=vi&ts=<ts>`) — không đọc được `contentDocument` vì cross-origin.
3. **Navigate thẳng vào URL iframe đó** → mới có nội dung.
4. Guess slug sai → "Chúng tôi không tìm thấy nội dung trang này". Dùng sitemap tìm slug thật:
   `curl -s https://stc-developers.zdn.vn/docs/sitemap.xml | grep -o 'https://[^<]*gui-tin-nhan[^<]*'`

## Webhook (nhận tin nhắn)

- Zalo POST request HTTP tới **Webhook URL** đã đăng ký khi user nhắn OA. Content-Type `application/json`.
- Header **`X-ZEvent-Signature`**: `mac = sha256(appId + data + timeStamp + OAsecretKey)` — phải verify để chặn giả mạo.
- Events: `user_send_text`, `user_send_image`, `user_send_link`, `user_send_audio`, `user_send_video`, sticker, location, business_card, file.
- Payload mẫu (text):
```json
{
  "app_id": "...",
  "sender": {"id": "user_id"},
  "user_id_by_app": "...",
  "recipient": {"id": "oa_id"},
  "event_name": "user_send_text",
  "message": {"text": "...", "msg_id": "..."},
  "timestamp": "..."
}
```

## Gửi tin nhắn (API trả lời)

```
POST https://openapi.zalo.me/v3.0/oa/message/cs
Header: access_token: <token>
Body: {"recipient": {"user_id": "..."}, "message": {"text": "..."}}
```

- Text tối đa **2.000 ký tự**. `user_id` lấy từ webhook (`sender.id`).
- Response: `error: 0` = success, kèm `quota.quota_type` ("reply"), `remain`/`total`, `message_id`.

## Quota — khung 48h (quan trọng)

- **Trong 48h** sau tương tác cuối của user: gửi tin tư vấn **MIỄN PHÍ, không giới hạn** (thay đổi từ 01/01/2026).
- **Ngoài 48h**: chỉ còn tin welcome (3 lượt) hoặc broadcast trả phí → chatbot phản hồi trong khung 48h là đủ cho kịch bản hỗ trợ/tư vấn.

## Luồng dựng chatbot

1. Tạo OA + Zalo App, OA **uỷ quyền** app → lấy `access_token` (xem docs "Tạo ứng dụng" + "Xác thực và uỷ quyền").
2. Cấu hình Webhook URL — phải **HTTPS public** (dùng Cloudflare Tunnel như btdat.io.vn).
3. Endpoint webhook → verify `X-ZEvent-Signature` → parse event → gọi API gửi tin. Có thể nối OmniRoute/LLM để trả lời tự động (giống luồng Telegram bot / voice-lab).

## Pitfalls

- Không nhầm `user_id` (người gửi) với `recipient.id` (chính OA).
- Sitemap có 2 bản slug: cũ `/docs/official-account/...` và v2 `/docs/v2/...` — ưu tiên bản v2.
- Trang phụ lục "Làm thế nào để tạo chatbot trả lời tự động với Zalo API" là tóm tắt luồng chuẩn: `/docs/official-account/phu-luc/lam-the-nao-de-tao-chatbot-tra-loi-tu-dong-voi-zalo-api`.
