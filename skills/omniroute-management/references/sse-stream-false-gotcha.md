# OmniRoute SSE gotcha (kiểm chứng 2026-08-20, zalo-oa-bot)

## Vấn đề
`POST /v1/chat/completions` với `stream:false` VẪN trả SSE (`data: {...}\n\n`) từ OmniRoute.
`await res.json()` fail: `SyntaxError: Unexpected token 'd', "data: {"... is not valid JSON`.

## Pattern xử lý (đã chạy được)
```ts
const rawText = await res.text();
let content = "";
let reasoningContent = "";
if (rawText.trim().startsWith("{")) {
  const json = JSON.parse(rawText);
  content = json?.choices?.[0]?.message?.content || "";
  reasoningContent = json?.choices?.[0]?.message?.reasoning_content || "";
} else {
  const lines = rawText.split("\n").filter((l) => l.startsWith("data: "));
  for (const line of lines) {
    const payload = line.slice(6).trim();
    if (payload === "[DONE]") continue;
    try {
      const chunk = JSON.parse(payload);
      const delta = chunk?.choices?.[0]?.delta;
      if (delta?.content) content += delta.content;
      if (delta?.reasoning_content) reasoningContent += delta.reasoning_content;
    } catch { /* bỏ qua chunk lỗi */ }
  }
}
if (!content && reasoningContent) content = reasoningContent; // DeepSeek fallback
```

## Lưu ý
- Không lấy chunk cuối (chỉ có finish_reason, content rỗng) — phải GHÉP toàn bộ delta
- Kể cả khi gửi `stream:false` rõ ràng
- Test bằng curl thấy JSON thuần ở đầu có thể gây hiểu nhầm — đọc kỹ response
