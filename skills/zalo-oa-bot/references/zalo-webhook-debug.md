# Zalo Webhook Debug — hành trình + error codes

Ghi lại từ phiên debug thật (2026-08-20) trên `~/zalo-oa-bot`.

## Triệu chứng ban đầu

- Signature sai vẫn nhận `{"ok":true}` → hóa ra: server đang chạy bản .env CŨ (tsx watch không reload env, dotenv không override key trùng)
- Fix: kill hẳn process + start lại; sửa đúng dòng gốc trong .env bằng `sed -i '<line>s/.*/KEY=value/'`

## Zalo từ chối webhook: "nhận về http code 401"

Zalo yêu cầu webhook trả 200 cho MỌI request. Signature sai mà trả 401 → Zalo không nhận webhook. Fix: luôn trả 200, sai signature chỉ log + bỏ qua.

## Lộn xộn signature — các thứ đã thử và kết quả

| Công thức thử | Kết quả |
|---|---|
| HMAC-SHA256(appId+body+ts+secret) | ❌ |
| sha256(appSecret) | ❌ |
| sha256(body+appId+ts) / (ts+body+appId) / (appId+ts+body) | ❌ |
| **sha256(appId + rawBody + timestamp + oaSecretKey)** | ✅ MATCH |

- Signature header dạng `mac=<hex>` → strip `mac=`
- Timestamp từ `payload.timestamp` (TRONG BODY), không phải header
- OA Secret Key lấy ở **oa.zalo.me → Cài đặt → Công cụ lập trình**, KHÁC App Secret ở developers.zalo.me

## Error codes

| Code | Ý nghĩa | Xử lý |
|---|---|---|
| -209 | App has been not approved | Kích hoạt App trên developers.zalo.me |
| -201 | user_id không hợp lệ | Lấy user_id thật từ webhook sender.id |
| -216 | access token hết hạn | Refresh token (25h vòng đời) |
| -212 | App has not registed this api | Đăng ký API (cần duyệt) |
| -224 | OA needs to upgrade OA Tier | Nâng cấp gói OA |

## Vòng đời token

- Access token: 25 giờ (KHÔNG phải 90 ngày — thông tin cũ sai)
- Refresh token: 3 tháng, dùng 1 lần (sau refresh token cũ vô hiệu)
- Authorization code: 10 phút, dùng 1 lần
- Refresh: `POST https://oauth.zaloapp.com/v4/oa/refresh_token` body `{refresh_token, app_id, grant_type: "refresh_token"}`

## Website verification

- Zalo yêu cầu thẻ meta `<meta name="zalo-platform-site-verification" content="...">` trong `<head>` trang chủ
- Meta phải nằm trong 512KB đầu, không chặn IP nước ngoài
- Serve qua Express `res.type("html").send(...)`; verify bằng curl qua `--resolve` (DNS công ty chưa cập nhật)

## Pattern log file (thay vì stdout background bị buffer)

```ts
const LOG_FILE = "C:/Users/datel/zalo-oa-bot/webhook.log";
function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  console.log(msg);
}
```

- GET /api/log: đọc file, parse từng dòng `[ISO] [TYPE] msg`, trả JSON (entries + total)
- GET /log: trang web hiển thị, fetch /api/log, nút làm mới thủ công (KHÔNG auto-refresh — user không thích poll 3s)
- UI: danh sách user (card avatar + preview tin cuối) → bấm vào xem hội thoại chat (bubble user phải, bot trái)
- Event `user_received_message` (OA gửi tin): user thật là `recipient.id` chứ không phải sender (sender = OA)
- Entry AI/SEND không có user → gán user của EVENT trước đó (cùng luồng)

## Log viewer — lỗi inline script kinh điển

- `<script>` inline trong Express template literal chứa `replace(/</g,'&lt;')` → browser thấy `</` giữa script → cắt script tại đó → toàn bộ JS mất (len=0) → trang "chờ kết nối" dù fetch API OK
- Chẩn đoán: `document.querySelectorAll('script')` → script cuối `textContent.length === 0`
- Fix: tách JS ra `public/log.js` + `express.static` + `<script src="/log.js">`; trong JS dùng `\u003C`/`\u003E` thay `<`/`>` trong regex escape

## UX review (skill web-ui-standards) — đo bằng CDP

```js
// Tap targets < 44px
document.querySelectorAll('button,a,[role=button]').forEach(el => {
  const r = el.getBoundingClientRect();
  if (r.width>0 && r.height>0 && (r.width<44||r.height<44)) console.log(el.innerText, r.width, r.height);
});
```

- Nút Xóa log 28px → 40px; nút Làm mới wrap 2 dòng → `white-space: nowrap` + icon inline
- Font stats 10.5px → 12px (min 11px); avatar 40px → 44px
- 2 nút rời 2 mép → gom nhóm phải + label trái cân đối
