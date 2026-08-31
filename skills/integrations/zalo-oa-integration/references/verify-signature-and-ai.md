# Zalo Webhook Verify + AI tích hợp — bài học từ session thật (2026-08-20)

Tất cả đã test với traffic webhook THẬT từ Zalo OA. Những chi tiết này KHÔNG có trong docs một cách rõ ràng — tốn nhiều vòng debug để tìm ra.

## 1. Công thức verify X-ZEvent-Signature CHÍNH XÁC

```
mac = sha256( appId + rawBody + timestamp + oaSecretKey )
     ^^^^^^^^^^
     crypto.createHash('sha256')  — KHÔNG phải createHmac!
```

- Docs Zalo ghi "mac = sha256(appId + data + timeStamp + OAsecretKey)" — chữ "mac" gây hiểu nhầm là HMAC. **HMAC không bao giờ khớp** (test cả 2 hướng đều fail).
- Header thật: `X-ZEvent-Signature: mac=<64 hex>` → **strip prefix `mac=`** (slice(4)) trước khi so sánh.
- `timestamp` lấy từ **`payload.timestamp` TRONG BODY** (string epoch ms). Header `X-ZEvent-Timestamp` **không tồn tại** trong traffic thật (luôn undefined).
- `rawBody` phải là chuỗi body gốc y hệt nhận được. `JSON.stringify(parsedBody)` lại → key order/format đổi → hash hỏng.
- `oaSecretKey` = OA Secret Key từ **oa.zalo.me → Cài đặt → Công cụ lập trình** (khác App Secret trên developers.zalo.me). App Secret → MAC không khớp.

### Verify thủ công trước khi deploy (script mẫu)

```js
const crypto = require('crypto');
const body = '<rawBody từ log>';           // y hệt chuỗi nhận được
const mac = crypto.createHash('sha256')
  .update(appId + body + timestamp + oaSecretKey).digest('hex');
console.log(mac === receivedSig);            // phải true
```

## 2. Express bắt rawBody — đừng viết middleware stream

```ts
app.use(express.json({
  verify: (req, _res, buf) => { (req as any).rawBody = buf.toString("utf8"); }
}));
```
Middleware tự viết `req.on('data')` → **treo vĩnh viễn** vì express.json đã consume body stream trước khi middleware chạy.

## 3. Event `user_received_message` = biên nhận, ĐỪNG reply

Khi OA gửi tin, Zalo gửi webhook `user_received_message` (sender=OA, recipient=user, kèm msg_id của tin vừa gửi). Nếu xử lý event này như tin từ user → **vòng lặp echo vô hạn** (bot gửi → nhận biên nhận → gửi tiếp...). Chỉ xử lý `user_send_text` + `sender.id != recipient.id`.

## 4. AI reasoning model — lộ suy nghĩ là lỗi user-visible

- `cmd/deepseek/deepseek-v4-flash` (qua OmniRoute) trả `reasoning_content` trước, `content` sau.
- `max_tokens=500` → model hết budget khi đang reasoning → `content` rỗng → fallback reasoning_content → **gửi cả quá trình suy nghĩ cho user** (user phàn nàn "sao trả lời hiển thị cả quá trình suy nghĩ").
- Fix: KHÔNG fallback reasoning_content bao giờ; `max_tokens ≥ 2000`.
- OmniRoute luôn trả SSE ngay cả với `stream:false` — parse dòng `data: {...}`, **cộng dồn `delta.content`** (chunk cuối chỉ có `finish_reason`, không có content).

## 5. Log file cho process background

`terminal(background=true)` → stdout bị buffer, `process log` không thấy log mới. Giải pháp: `fs.appendFileSync(LOG_FILE)` mọi log + endpoint `GET /api/log` đọc file + trang HTML viewer. Format chuẩn `[ISO] [TYPE] msg` (TYPE hoa: WEBHOOK/EVENT/AI/SEND/ERROR) để parser tách loại.

## 6. Token lifecycle (cập nhật 2026)

- Access token: **25 giờ** (không 90 ngày như thông tin cũ).
- Refresh token: **3 tháng, dùng 1 lần** — sau refresh nhận refresh token MỚI, phải persist ngay (file .env).
- Refresh endpoint: `POST https://oauth.zaloapp.com/v4/oa/refresh_token` (form: `app_id`, `grant_type=refresh_token`, `refresh_token`).

## 7. Mã lỗi Zalo gặp trong session

| Mã | Ý nghĩa | Fix |
|---|---|---|
| -209 | App has been not approved | KÍCH HOẠT App trong trang App developers.zalo.me |
| -201 | user_id is invalid | Dùng `sender.id` thật từ webhook, không dùng ID giả |
| -212 | App has not registed this api | API cần đăng ký quyền/API riêng |
| -240 | UserInfo API shutdown | Dùng V3 thay v2.0 |
