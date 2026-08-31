# Zalo OA Webhook — Ghi chú chi tiết

## Payload webhook (user_send_text)

```json
{
  "app_id": "2334789304983807556",
  "sender": { "id": "675059164343092785" },
  "recipient": { "id": "3674338702778449434" },
  "event_name": "user_send_text",
  "message": { "text": "Alo", "msg_id": "b2db3895fe26797f2030" },
  "timestamp": "1787209817225"
}
```

- `timestamp` = milliseconds epoch, TRONG BODY (header `X-ZEvent-Timestamp` không tồn tại — undefined).
- `sender.id` = user_id dùng để gửi trả lời.

## Header thật từ Zalo (quan trọng cho verify)

```
x-zevent-signature: mac=9bcf7a5c4da74ba68b8d6e637a4c3c6e1a4e2f6af72a11e5bbafb0aa65b212da
x-zevent-server: OA OpenAPI
user-agent: ZaloWebhook
```

Lưu ý: KHÔNG có `X-ZEvent-Timestamp` header — timestamp chỉ trong body.

## Event list (event_name)

| event_name | Mô tả |
|---|---|
| `user_send_text` | Tin nhắn văn bản |
| `user_send_image` | Hình ảnh |
| `user_send_link` | Liên kết |
| `user_send_audio` | Âm thanh |
| `user_send_video` | Video |
| `user_send_sticker` | Sticker |
| `user_send_location` | Vị trí |
| `user_send_business_card` | Danh thiếp |
| `user_send_file` | File |

## Error codes (API gửi tin)

| Code | Ý nghĩa | Cách xử lý |
|---|---|---|
| `-209` | App has been not approved | App chưa KÍCH HOẠT trên developers.zalo.me → kích hoạt |
| `-201` | user_id is invalid | user_id sai/giả → lấy từ webhook sender.id |
| `-216` / `-124` | Token hết hạn / không hợp lệ | Auto-refresh token rồi gửi lại |
| `-212` | App has not registed this api | App chưa đăng ký quyền API đó |
| `-240` | UserInfo API shut down | API v2 cũ → dùng V3 |
| `-221` / `-222` | Token lỗi | Refresh |

## Quy tắc webhook Zalo (bắt buộc)

- Phản hồi **200 OK** cho mọi sự kiện — nếu ≠200, Zalo báo webhook không hoạt động và có thể hủy cấu hình.
- Phản hồi **≤2 giây** — nếu chậm, Zalo coi như fail và retry sau 30s, 1p, 5p... 
- Retry: Zalo gửi lại sau 30 giây, 1 phút, 5 phút... nếu không mở được connection.
- Webhook URL nên dùng domain (không host:port), bắt buộc HTTPS.
- "Lọc cú pháp" bật → chỉ nhận tin bắt đầu bằng `#` → phải TẮT cho chatbot.

## OAuth token lifecycle (docs chính thức)

- Authorization Code: dùng 1 lần, sống 10 phút.
- **Access Token: 25 giờ.**
- Refresh Token: 3 tháng, dùng 1 lần, sau refresh cấp refresh mới.
- Mỗi OA giới hạn số App được ủy quyền.
- Để lấy OA Access Token phải là admin của ít nhất 1 OA.

## Community insights (đã verify qua docs)

- "mỗi app chỉ có 1 key thôi" — nhưng OA Secret Key (oa.zalo.me → Công cụ lập trình) khác App Secret (developers.zalo.me).
- Zalo Support: "để nguyên payload ở dạng string nhận được để verify" — không re-stringify.
- API getfollowers v2 bị shutdown → dùng V3 `/v3.0/oa/user/getlist` (cần App đăng ký API, có thể lỗi -212).
- user_id thật từ webhook, không nên hardcode ID trong docs (khác hoàn toàn).

## Docs access pattern

developers.zalo.me là SPA + iframe docs (`https://stc-developers.zdn.vn/docs/v2/...`):
- Đọc bằng `goto_url` thẳng URL iframe + `document.body.innerText`.
- Không đọc được qua `contentDocument` (cross-origin).
- URL docs cũ redirect về docs mới chung.
