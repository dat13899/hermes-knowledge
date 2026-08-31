# Zalo X-ZEvent-Signature — dữ liệu thật đã kiểm chứng (2026-08-20)

## Công thức ĐÚNG (verified match 100% với 2 request thật)

```
Header: X-ZEvent-Signature = "mac=<64 hex chars>"
mac = sha256(appId + rawBody + timestamp + oaSecretKey)   // PLAIN SHA-256, KHÔNG phải HMAC!
```

- **`crypto.createHash("sha256")`** — docs Zalo ghi "sha256(...)" nhưng nhiều người hiểu nhầm thành HMAC-sha256. HMAC → fail.
- `rawBody` = chuỗi JSON gốc y nguyên (không re-stringify — đổi thứ tự key là fail)
- `timestamp` = `payload.timestamp` TRONG BODY (string ms, ví dụ `"1787209817225"`), header `X-ZEvent-Timestamp` là undefined
- Strip prefix `mac=` trước khi so hex

## Ví dụ request thật (đã khớp)

```json
{"event_name":"user_send_text","app_id":"2334789304983807556","sender":{"id":"675059164343092785"},"recipient":{"id":"3674338702778449434"},"message":{"text":"Alo","msg_id":"b2db3895fe26797f2030"},"timestamp":"1787209817225"}
```

- appId = `2334789304983807556`
- timestamp = `1787209817225`
- oaSecretKey = `55nwOtnbXRcr5ZN8UXiE` (OA Secret Key từ oa.zalo.me — KHÔNG phải App Secret `RHTyNGiIfn2J8d8CggRp`)
- signature nhận = `mac=9bcf7a5c4da74ba68b8d6e637a4c3c6e1a4e2f6af72a11e5bbafb0aa65b212da`
- `sha256(appId + body + ts + secret)` → khớp 100% ✅

## Debug nhanh

1. Log đầy đủ header + body thật (đừng cắt 200 ký tự — signature 64 hex + body)
2. Tách riêng: `sig` (strip `mac=`), `ts` (từ body), `appId`, `secret` (thử CẢ App Secret lẫn OA Secret Key)
3. Tính `createHash('sha256').update(appId+body+ts+secret).digest('hex')` so với sig
4. Nếu không khớp → thử từng biến thể (secret khác, sha vs hmac, thứ tự concat) để cô lập

## Header thật Zalo gửi

```
x-zevent-server: OA OpenAPI
x-zevent-signature: mac=<hex>
user-agent: ZaloWebhook
```
