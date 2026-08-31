# Zalo OA — Credentials, Token Lifecycle & Error Codes

Kinh nghiệm thực tế từ session build `~/zalo-oa-bot` (08/2026).

## Credentials (5 giá trị)

| Var | Lấy ở đâu | Hạn |
|---|---|---|
| App ID | developers.zalo.me → App → Cài đặt | - |
| App Secret | App → Cài đặt → nút **"Copy secret key"** | - |
| OA Secret Key | **CHÍNH LÀ App Secret** (mỗi app chỉ 1 key — xác nhận từ community Zalo) | - |
| Access Token | API Explorer `https://developers.zalo.me/tools/explorer/<APP_ID>` | **25 giờ** |
| Refresh Token | đi kèm access token ngay lúc tạo | **3 tháng**, dùng 1 lần |

## Quy tắc token

- Để lấy OA Access Token phải là **admin của OA**.
- **Lưu refresh token NGAY lúc tạo** — Zalo không cho xem lại token cũ; "bị giới hạn" khi lấy lại là bình thường (authorization code dùng 1 lần, sống 10 phút).
- Auto-refresh endpoint: `POST https://oauth.zaloapp.com/v4/oa/refresh_token`
  - Body form-urlencoded: `app_id`, `grant_type=refresh_token`, `refresh_token`
  - Trả về `access_token` mới + `refresh_token` mới.
  - **Persist cả 2 ngay** — refresh token cũ vô hiệu sau khi dùng; access token cũ hết hiệu lực ngay khi access mới tạo.

## Error codes thường gặp

| Mã | Ý nghĩa | Xử lý |
|---|---|---|
| -209 | "App has been not approved" — App **chưa kích hoạt** | developers.zalo.me → App → nút **"Kích hoạt"**; xong token cũ vẫn dùng được |
| -216, -124 | Access token hết hạn / không hợp lệ | gọi refresh token → gửi lại |
| -224 | OA cần nâng cấp gói tier | nâng gói OA |

## Express webhook — raw body pattern

Verify `X-ZEvent-Signature` cần RAW body byte-for-byte. Middleware tự viết `req.on('data')` treo request vì `express.json()` consume stream trước. Pattern đúng:

```ts
app.use(express.json({
  verify: (req, _res, buf) => { (req as any).rawBody = buf.toString("utf8"); },
}));
```

So sánh signature bằng `crypto.timingSafeEqual`. Test bằng ASCII thuần (tránh lỗi encoding tiếng Việt node/curl trên Windows).

## Pitfalls

- **dotenv KHÔNG override key trùng**: append dòng mới với key đã tồn tại → giá trị cũ (rỗng) vẫn được dùng. Sửa đúng dòng bằng sed (`sed -i '12s/.*/KEY=value/'`) hoặc xoá dòng cũ. Restart server sau khi sửa .env — `tsx watch` không reload env.
- Quota tin tư vấn (cs): **trong 48h** sau tương tác cuối → **miễn phí, không giới hạn**; ngoài 48h → chỉ welcome (3 lượt) hoặc broadcast/ZNS trả phí.
- DNS nội bộ công ty (vinnet) cache chậm: `nslookup domain` fail với record mới → dùng `nslookup domain 1.1.1.1` hoặc `curl --resolve domain:443:<cf-ip>`. Zalo dùng DNS public nên không ảnh hưởng.

## Project mẫu đã chạy

`~/zalo-oa-bot` (TS + Express + OmniRoute):
- `src/index.ts` — server + webhook (respond 200 trước, xử lý bất đồng bộ — Zalo yêu cầu ≤2s)
- `src/zaloSignature.ts` — verify X-ZEvent-Signature
- `src/zaloSend.ts` — gửi tin + auto-refresh khi lỗi -216/-124
- `src/zaloToken.ts` — refresh token + persist vào .env
- `src/ai.ts` — gọi OmniRoute (parse SSE delta, history 6 tin/user)
- Webhook public: `https://zalo.btdat.io.vn/zalo/webhook` (Cloudflare Tunnel port 4810)
