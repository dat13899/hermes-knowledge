# OmniRoute Vision Setup — Configuring Auxiliary Vision via OmniRoute

## Context

OmniRoute at `localhost:20128` replaced 9Router (same port, different software). OmniRoute properly routes multimodal image payloads to upstream models — **no image stripping bug**. Vision works when you pick a model that both (a) supports vision and (b) is available in your plan/account.

## Working Vision Model

**`cmd/MiniMaxAI/MiniMax-M3`** — tested and confirmed working (July 2026):

```
model: cmd/MiniMaxAI/MiniMax-M3
provider: omniroute
base_url: http://localhost:20128/v1
capabilities: vision: true, tool_calling: true, reasoning: true, thinking: true
input_modalities: ["text", "image"]
context_length: 1,048,576
max_output_tokens: 512,000
```

Tested via direct API call with base64 PNG image → successfully analyzed the image content. Also tested via `vision_analyze` tool → correctly identified Google logo colors/letters.

### Hermes Config

```bash
hermes config set auxiliary.vision.provider omniroute
hermes config set auxiliary.vision.model "cmd/MiniMaxAI/MiniMax-M3"
hermes config set auxiliary.vision.base_url "http://localhost:20128/v1"
```

Config takes effect after gateway restart (`/restart` in Telegram, or `hermes gateway restart` from terminal). **Not** mid-session — `auxiliary.*` configs are read at session start, unlike `browser.cdp_url` which reads at tool invocation time.

## Failed Vision Models (July 2026)

All tested through OmniRoute `localhost:20128`. Results may change as OmniRoute updates.

| Model | Error | Notes |
|-------|-------|-------|
| `oc/minimax-m2.5-free` | 401 — Model not supported | OpenCode free tier doesn't include this |
| `oc/minimax-m3-free` | 401 — Model not supported | Same — OpenCode free models not in OmniRoute plan |
| `ddgw/gpt-4o-mini` | 418 — DDG anti-abuse challenge | DuckDuckGo rate-limiting the IP |
| `ddgw/claude-3-5-haiku-20241022` | 418 — DDG anti-abuse challenge | Same DDG block |
| `cmd/google/gemini-3.5-flash` | Timeout (15s+) | Command Code Gemini slow/unreachable |
| `cmd/claude-sonnet-4-6` | 403 — MODEL_NOT_IN_PLAN | Requires Pro plan |
| `aug/claude-haiku-4.5` | Empty response | Auggie models return no content |
| `aug/gemini-3.1-pro` | Empty response | Same — no content in response |

## Direct API Test (for verifying any vision model)

```python
import base64, json, urllib.request

# Test with a small red pixel PNG
red_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

data = json.dumps({
    'model': 'cmd/MiniMaxAI/MiniMax-M3',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'What color is this image? Reply in max 5 words.'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{red_pixel}'}}
        ]
    }],
    'max_tokens': 30
}).encode()

req = urllib.request.Request(
    'http://localhost:20128/v1/chat/completions',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_OMNIROUTE_API_KEY_HERE'
    }
)
resp = urllib.request.urlopen(req, timeout=60)
body = resp.read().decode()
for line in body.split('\n'):
    if line.startswith('data: ') and '[DONE]' not in line:
        chunk = json.loads(line[6:])
        if 'error' in chunk:
            print('ERROR:', chunk['error'])
        elif 'choices' in chunk and chunk['choices']:
            delta = chunk['choices'][0].get('delta', {})
            if 'content' in delta:
                print(delta['content'], end='')
print()
```

## OmniRoute Provider Config (main model)

```yaml
# config.yaml
model:
  default: cmd/deepseek/deepseek-v4-pro
  provider: omniroute
  context_length: 250000
  base_url: http://localhost:20128/v1

providers:
  omniroute:
    base_url: http://localhost:20128/v1
    api_key: <from .env>
```

Custom provider (legacy, pre-OmniRoute provider support):
```yaml
custom_providers:
  - name: Local (127.0.0.1:20128)
    base_url: http://127.0.0.1:20128/v1
    api_key: <from .env>
    models:
      - deepseek-v4-pro
      - mimo-auto
      - cmc/deepseek/deepseek-v4-pro
      # ... etc
```
