# Zalo OA API — chi tiết tham chiếu

## Webhook Overview
- Zalo POST JSON tới Webhook URL đã đăng ký khi có tương tác
- Yêu cầu: respond **200 OK ≤ 2 giây**, nếu không Zalo báo "webhook không hoạt động"
- Retry: 30s, 5 phút, 30 phút, 1h, 6h, 12h, 24h... (chỉ khi không mở được connection)
- Webhook URL nên dùng domain HTTPS, KHÔNG dùng host:port
- Có tính năng "Lọc cú pháp": chỉ nhận text bắt đầu bằng `#`
- App cần được OA cấp quyền `Official_Account_Access_Token`

## Verify signature
Header: `X-ZEvent-Signature` + `X-ZEvent-Timestamp`
```
mac = HMAC-SHA256(OAsecretKey, appId + data + timestamp)
```
- `data` = chuỗi JSON gốc của body (raw, không re-serialize)
- `timestamp` từ header X-ZEvent-Timestamp (milliseconds)
- So sánh timing-safe (crypto.timingSafeEqual)
- Dev mode có thể bỏ qua verify khi chưa có OA secret (log warning)

## Event list (event_name)
- `user_send_text` — văn bản (message.text)
- `user_send_image` — ảnh
- `user_send_link` — liên kết
- `user_send_audio` — âm thanh
- `user_send_video` — video
- `user_send_sticker` — sticker
- `user_send_location` — vị trí
- `user_send_business_card` — danh thiếp
- `user_send_file` — file
- (thêm: follow/unfollow OA, click menu, click nút nhắn tin...)

## Payload mẫu (user_send_text)
```json
{
  "app_id": "360846524940903967",
  "sender": {"id": "246845883529197922"},
  "user_id_by_app": "552177279717587730",
  "recipient": {"id": "388613280878808645"},
  "event_name": "user_send_text",
  "message": {"text": "message", "msg_id": "96d3cdf3af150460909"},
  "timestamp": "154390853474"
}
```

## Gửi tin tư vấn (cs)
```
POST https://openapi.zalo.me/v3.0/oa/message/cs
Headers: Content-Type: application/json, access_token: <token>
Body: {
  "recipient": {"user_id": "..."},
  "message": {"text": "..."}   // tối đa 2000 ký tự
}
```
Response:
```json
{ "data": { "quota": {"quota_type": "reply", "remain": "8", "total": "8"},
            "message_id": "...", "user_id": "...", "sent_time": "..." },
  "error": 0, "message": "Success" }
```

## Quota (cập nhật 1/1/2026)
- **Khung 48h**: tin tư vấn miễn phí, KHÔNG giới hạn (tính từ tương tác cuối của user)
- **Ngoài 48h**: tin welcome (3 lượt) / tin quảng bá / ZNS — trả phí
- Lấy user_id từ `sender.id` webhook, hoặc API truy xuất user

## Hướng dẫn tạo chatbot (docs chính thức)
1. Tạo OA (chỉ OA mới có API chatbot)
2. Tạo Zalo App + OA uỷ quyền
3. Cấu hình Webhook
4. Nghe event user_send_text → xử lý → gọi API gửi tin

## Docs URLs
- Webhook user gửi tin: developers.zalo.me/docs/official-account/webhook/tin-nhan/su-kien-nguoi-dung-gui-tin-nhan
- Gửi tin tư vấn text: developers.zalo.me/docs/official-account/tin-nhan/tin-tu-van/gui-tin-tu-van-dang-van-ban
- Tạo chatbot: developers.zalo.me/docs/official-account/phu-luc/lam-the-nao-de-tao-chatbot-tra-loi-tu-dong-voi-zalo-api
- Sitemap (tìm slug): stc-developers.zdn.vn/docs/sitemap.xml

## Đọc docs qua browser (SPA workaround)
Docs là SPA: nội dung trong iframe `stc-developers.zdn.vn/docs/v2/<slug>?lang=vi&ts=<ts>` (cross-origin, không đọc được contentDocument). Cách:
1. Mở trang developers.zalo.me → lấy `iframe.src`
2. Navigate thẳng vào URL đó (không cần referer)
3. Vài trang v2 cũ trả "Chúng tôi không tìm thấy nội dung" — dùng sitemap.xml tìm slug đúng
