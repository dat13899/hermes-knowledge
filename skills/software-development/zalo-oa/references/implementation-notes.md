# Zalo OA Bot — Implementation Notes (session 2026-08-20)

Đã build xong chatbot Zalo OA hoàn chỉnh tại `~/zalo-oa-bot`. Chi tiết vận hành + pitfalls đã verify thực tế.

## Project layout

- Express + TypeScript (tsx), port **4810**. Run `npm run dev` (background), typecheck `npx tsc --noEmit`.
- Webhook public: `https://zalo.btdat.io.vn/zalo/webhook` (Cloudflare Tunnel, tunnel id `b3e9ea6a-9ed9-41fc-be71-66f52b31fef3`).
- Endpoints: `GET /` health; `POST /zalo/webhook`; `POST /api/test-send` (header `x-test-token`); `GET /api/debug/history` (xem history in-memory — log stdout bị buffer khi chạy background, dùng endpoint này để debug).
- Files: `src/index.ts` (server + webhook handler), `src/ai.ts` (OmniRoute SSE parser + history 6 tin/user), `src/zaloSend.ts` (POST /v3.0/oa/message/cs), `src/zaloSignature.ts` (verify), `src/types.ts`.
- Lệnh đặc biệt: `reset` → xoá history user.
- .env.example đã có đủ 8 biến (ZALO_*, OMNIROUTE_URL, AI_MODEL, PORT, WEBHOOK_TEST_TOKEN, AI_SYSTEM_PROMPT).

## Pitfalls đã gặp (verified)

1. **`express.json()` nuốt body stream** → không thể dùng middleware `req.on('data')` riêng để lấy rawBody (request TREO, không bao giờ `end`). Đúng: `express.json({ verify: (req,_res,buf)=>{ (req as any).rawBody = buf.toString('utf8'); } })`.
2. **dotenv không override key trùng** — thêm dòng `KEY=value` mới sau dòng cũ vô tác dụng (giữ giá trị đầu tiên). Sửa .env phải `sed -i 'Nd s/.*/KEY=value/'` vào dòng gốc, rồi xoá dòng thừa. Khi sửa .env xong phải RESTART process (tsx watch không reload env).
3. **OmniRoute trả SSE cả khi `stream:false`** — `res.json()` fail `Unexpected token 'd'`. Fix: `res.text()` → nếu startsWith `{` thì JSON.parse, else tách dòng `data: ` và ghép TẤT CẢ `choices[0].delta.content` (không lấy chunk cuối — thường chỉ finish_reason). Fallback `delta.reasoning_content` khi content rỗng (DeepSeek). Xem `src/ai.ts`.
4. **Ký tự tiếng Việt lệch signature khi test giả lập** (encoding node/curl trên Windows) → test verify signature bằng body ASCII trước, tiếng Việt sau.
5. **DNS công ty cache lâu** — `prod-ad.ad.vinnet.vn` không thấy record mới. Test: `nslookup domain 1.1.1.1`; HTTPS: `curl --resolve domain:443:<CF-IP> https://domain/`.
6. Zalo gửi `access_token` trong **header** (không phải Authorization Bearer).
7. `cloudflared tunnel route dns` fail "Cannot determine default origin certificate path" nếu chưa `cloudflared tunnel login` → thêm CNAME thủ công trên Cloudflare dashboard.
8. Khi sửa `~/.cloudflared/config.yml` phải restart tunnel process: `taskkill /F /PID <pid>` (không dùng `//F` trong bash — MSYS biến thành đường dẫn) rồi `cloudflared tunnel --config C:/Users/datel/.cloudflared/config.yml run`. PHÂN BIỆT tunnel OmniRoute (`--url http://127.0.0.1:20128`, KHÔNG kill).

## Signature verify test đã dùng

```bash
MAC=$(node -e "
const crypto = require('crypto');
const appId = '360846524940903967';
const oaSecret = 'mysecretkey';
const body = JSON.stringify({app_id: appId, sender:{id:'246845883529197922'}, recipient:{id:'388613280878808645'}, event_name:'user_send_text', message:{text:'hello', msg_id:'96d3cdf3af150460909'}, timestamp:'154390853474'});
process.stdout.write(crypto.createHmac('sha256', oaSecret).update(appId + body + '154390853474').digest('hex'));
")
curl -X POST http://localhost:4810/zalo/webhook -H "X-ZEvent-Signature: $MAC" -H "X-ZEvent-Timestamp: 154390853474" -d '<body>'
# Kỳ vọng: sig đúng → {"ok":true}; sig sai (deadbeef) → 401 {"error":"invalid signature"}
```

## OmniRoute AI response shape

`POST http://localhost:20128/v1/chat/completions` với `stream:false` vẫn trả SSE:
```
data: {"id":"...","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}
data: {"id":"...","choices":[{"index":0,"delta":{"reasoning_content":"Ch..."},"finish_reason":null}]}
...
data: {"id":"...","choices":[{"index":0,"delta":{"content":"Chào bạn!"},"finish_reason":null}]}
data: {"id":"...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
data: [DONE]
```
Model verified: `cmd/deepseek/deepseek-v4-flash` (free).
