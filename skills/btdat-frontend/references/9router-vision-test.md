# 9Router Vision Test Results (2026-07-26)

Testing multimodal image requests through 9Router at `http://127.0.0.1:20128`.

## Test method

Raw Python script sending base64-encoded PNG with `image_url` content block:
```python
import base64, json, urllib.request
tiny_png = base64.b64decode('iVBORw0KGgo...')  # 1x1 red pixel
b64 = base64.b64encode(tiny_png).decode()
payload = json.dumps({
    'model': 'cmc/moonshotai/Kimi-K2.6',
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': 'What color?'},
        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}}
    ]}]
})
req = urllib.request.Request('http://127.0.0.1:20128/v1/chat/completions',
    data=payload.encode(), headers={'Content-Type': 'application/json'})
```

## Results

| Model | Capabilities from /v1/models | Actual vision result |
|-------|------------------------------|---------------------|
| `deepseek-v4-pro` | `vision: false` | "I can't see the image — this model doesn't have vision support" |
| `cmc/deepseek/deepseek-v4-pro` | `vision: false` | Same |
| `cmc/moonshotai/Kimi-K2.6` | `vision: true` | "Tôi không thể nhìn thấy hình ảnh" (image omitted) |
| `cmc/moonshotai/Kimi-K2.5` | `vision: true` | Not tested |
| `cmc/Qwen/Qwen3.6-Plus` | `vision: true` | `No available providers match the 'only' filter` (server error) |
| `mimo-auto` | Not listed | HTTP 400 Bad Request |

## Conclusion

9Router routes multimodal requests (200 OK, no 404) but **strips images before forwarding**
to the upstream model. All models respond as if no image was included.

GitHub issue: https://github.com/decolua/9router/issues/1078 (open since May 2026)
Related PRs: #1166 (vision/kimi parity), #2718 (codex images) — both unmerged.

## Workaround

Use Gemini auxiliary vision instead:
```bash
hermes config set auxiliary.vision.provider google
hermes config set auxiliary.vision.model gemini-2.0-flash
# Set GOOGLE_API_KEY in .env
```
