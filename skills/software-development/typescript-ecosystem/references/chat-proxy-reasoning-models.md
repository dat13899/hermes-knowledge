# Browser Chat UI → LLM Gateway (CORS + reasoning models)

Verified 2026-08-02 on service-dashboard ChatPage (`/chat`) calling OmniRoute
(localhost:20128) through a Node server proxy.

## Why a server proxy, not direct fetch

Browser JS calling `http://localhost:20128/v1/chat/completions` directly hits
CORS. Fix: add a plain Node `http` proxy route in the existing server (port 3000):

```js
// server.js — proxy /api/chat → OmniRoute (OpenAI-compatible)
if (u.pathname === '/api/chat' && method === 'POST') {
  let b = '';
  req.on('data', c => b += c);
  req.on('end', () => {
    const r = http.request({
      hostname: 'localhost', port: 20128, path: '/v1/chat/completions', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'User-Agent': 'curl/8.0' }, // UA REQUIRED (gateway blocks Python-urllib)
      timeout: 120000,
    }, (r2) => {
      res.writeHead(r2.statusCode, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      r2.pipe(res);
    });
    r.on('error', (e) => { try { json(res, { error: 'gateway-unreachable: ' + e.message }, 502); } catch (_) {} });
    r.write(b); r.end();
  });
  return;
}
```

Frontend then `fetch('/api/chat', {method:'POST', body: JSON.stringify({model, stream:false, messages, max_tokens})})`.

## DeepSeek reasoning models — the content-empty trap

`deepseek-v4-flash` (and other reasoning models) return:
```json
{ "choices": [{ "message": { "content": "", "reasoning_content": "The user asked...", }, "finish_reason": "length" }] }
```
- With low `max_tokens` (e.g. 100) the budget is consumed by `reasoning_content`
  → `content` is EMPTY and `finish_reason` = `length`. Bump `max_tokens` (400-500)
  and/or fall back: `const answer = msg?.content || msg?.reasoning_content || data.error`.
- When building `messages[]` to send back, strip any prior placeholder/empty
  assistant messages and pass `{role, content}` only.

## Gotchas
- Server must be RESTARTED after adding the proxy route (an old process serving
  the old build won't have it).
- `stream:false` + `max_tokens:500` on a reasoning model returns real Vietnamese
  answers reliably; streaming via SSE works too (see voice-ai-pipeline).
- Keep `User-Agent: curl/8.0` header — OmniRoute returns 403 `insufficient_quota`
  for Python-urllib UA.
