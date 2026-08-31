# Zalo OAuth refresh bug — 2026-08-24 (bot có log nhưng không rep)

Triệu chứng: `webhook.log` có `[EVENT] user=... text=em ơi` + `[AI] reply=...` nhưng `[SEND] msg_id=undefined quota_remain=undefined` — user không nhận được tin nhắn. Trước đó bot chạy ổn, sau đó đột ngột không rep.

## Root cause

1. **Token hết hạn**: Zalo trả `{"error":-216,"message":"Access token has expired"}` khi POST `openapi.zalo.me/v3.0/oa/message/cs`. Token OAuth v4 chỉ sống ~1h (Explorer 25h).

2. **Refresh URL sai — bug chính**: `src/zaloOAuth.ts` định nghĩa:
   ```ts
   const REFRESH_URL = "https://oauth.zaloapp.com/v4/oa/refresh_token"; // SAI
   ```
   Endpoint này KHÔNG tồn tại → Zalo trả `{"error":"404","message":"You currently access to an empty api..."}`. Dù `zaloSend.ts` đã có logic retry khi gặp -216, retry luôn fail do sai URL nên log chỉ còn `msg_id=undefined`.

   **Fix**: `REFRESH_URL = TOKEN_URL = "https://oauth.zaloapp.com/v4/oa/access_token"` — cả exchange code và refresh đều POST cùng URL, chỉ khác `grant_type`:
   - `grant_type=authorization_code` (kèm `code` + `code_verifier`)
   - `grant_type=refresh_token` (kèm `refresh_token`)

   Verify: `curl POST https://oauth.zaloapp.com/v4/oa/access_token` với `secret_key: ZALO_APP_SECRET` + `refresh_token` → trả `{"access_token":"...","refresh_token":"...","expires_in":"90000"}`. Còn `/refresh_token` luôn 404 ngay cả với token hợp lệ.

3. **Hot-reload token**: `persistTokens()` chỉ ghi `.env` nhưng `index.ts` cache `const ZALO_ACCESS_TOKEN = process.env.ZALO_ACCESS_TOKEN` lúc startup. Sau refresh, `.env` mới nhưng process vẫn dùng token cũ → request tiếp theo vẫn -216. Fix: `persistTokens()` cập nhật `process.env.ZALO_ACCESS_TOKEN` + `process.env.ZALO_REFRESH_TOKEN`, và `sendReply()` đọc `process.env.ZALO_* || cachedConst` mỗi lần gửi.

4. **Log thiếu chi tiết**: `sendReply` cũ chỉ log `msg_id`/`quota`, khi lỗi thì `undefined` không biết vì sao. Fix: nếu `result.error` thì log `error`, `message`, `raw`.

## Cách debug khi gặp lại

```bash
# 1. Xem log
cat ~/zalo-oa-bot/webhook.log | tail -20
grep SEND ~/zalo-oa-bot/webhook.log | tail -5  # msg_id=undefined = lỗi gửi

# 2. Test token trực tiếp
node -e "
const m={}; require('fs').readFileSync('C:/Users/datel/zalo-oa-bot/.env','utf8').split('\n').forEach(l=>{let p=l.split('='); if(p[0]) m[p[0].trim()]=p.slice(1).join('=').trim()});
fetch('https://openapi.zalo.me/v3.0/oa/message/cs',{method:'POST',headers:{'Content-Type':'application/json','access_token':m.ZALO_ACCESS_TOKEN},body:JSON.stringify({recipient:{user_id:'675059164343092785'},message:{text:'test'}})}).then(r=>r.json()).then(console.log)
"
# -216 = hết hạn, -14002 = appId sai, 0 = ok

# 3. Test refresh
node -e "
const fs=require('fs'); const m={}; fs.readFileSync('C:/Users/datel/zalo-oa-bot/.env','utf8').split('\n').forEach(l=>{let p=l.split('='); if(p[0]) m[p[0].trim()]=p.slice(1).join('=').trim()});
fetch('https://oauth.zaloapp.com/v4/oa/access_token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','secret_key':m.ZALO_APP_SECRET},body:new URLSearchParams({app_id:m.ZALO_APP_ID,grant_type:'refresh_token',refresh_token:m.ZALO_REFRESH_TOKEN})}).then(r=>r.text()).then(console.log)
"
# Phải ra access_token mới, không phải 404
```

## Files đã sửa (2026-08-24)

- `src/zaloOAuth.ts`: `REFRESH_URL` → `access_token`, `persistTokens()` thêm `process.env` update
- `src/index.ts`: `sendReply()` đọc `process.env` động + log error chi tiết
- `.env`: cập nhật token mới `aNnaRi-...` sau manual refresh, restart bot (kill 11352 → new 6432)

## Liên quan

- `references/zalo-token-ops.md` ghi `REFRESH endpoint: POST https://oauth.zaloapp.com/v4/oa/refresh_token` — **Sai, cần sửa đồng bộ** (đúng là `/access_token`).
- Skill section "Vì sao token API Explorer KHÔNG refresh được" nói 404 do Explorer token — đúng nhưng dễ nhầm với bug URL này. Bug URL này 404 ngay cả với OAuth v4 token hợp lệ.
