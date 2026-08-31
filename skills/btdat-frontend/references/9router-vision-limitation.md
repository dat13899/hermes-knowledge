# 9Router Vision Support — Proven Limitations

Date: 2026-07-26. Environment: Windows 10, 9Router at `localhost:20128`.

## Test Methodology

1. Enumerated `/v1/models` — multiple models report `vision: true` in capabilities  
2. Tested direct `curl` to `localhost:20128/v1/chat/completions` with base64 image payloads  
3. Tested via Hermes `auxiliary.vision` config + `vision_analyze()` tool  

## Models Tested

| Model | Capabilities (from /v1/models) | Direct curl result |
|-------|-------------------------------|-------------------|
| `mimo-auto` | No capabilities listed | HTTP 400 |
| `cmc/moonshotai/Kimi-K2.6` | `vision: true` | **200 OK** but "không thấy ảnh" |
| `cmc/Qwen/Qwen3.6-Plus` | `vision: true` | No available providers error |
| `deepseek-v4-pro` | `vision: false` | "model doesn't have vision support" |
| `cmc/deepseek/deepseek-v4-pro` | `vision: false` | N/A |
| `cmc/deepseek/deepseek-v4-flash` | `vision: false` | N/A |

## Root Cause (updated July 26)

9Router **routes** multimodal requests (HTTP 200, not 404) but **strips image payloads** before forwarding to upstream models. The model receives only the text portion, never sees the image, and responds with "I can't see the image."

This is tracked as GitHub issue **decolua/9router#1078** "Missing vision/context metadata for chat models" (open since May 13, 2026). Two related PRs (#1166, #2718) reference vision fixes but are unmerged as of July 2026.

The `/v1/models` response correctly reports upstream capabilities but the combo/router translation layer does not preserve `image_url` content blocks.

## Workaround

Use a direct vision-capable provider configured as Hermes auxiliary vision model:

```bash
hermes config set auxiliary.vision.provider google
hermes config set auxiliary.vision.model gemini-2.0-flash-001
# Set GEMINI_API_KEY in ~/.hermes/.env (free from https://aistudio.google.com/apikey)
```

This keeps main chat on DeepSeek through 9Router while vision requests bypass 9Router entirely and go direct to Gemini.

## Gemini Free Tier Limits (2026)

| Model | RPM | RPD | Vision |
|-------|-----|-----|--------|
| Gemini 2.0 Flash | 10-15 | 250 | Yes |
| Gemini 2.5 Flash | 10 | 250 | Yes |

Ample for screenshot analysis. No credit card required.

## 9Router Skills — What They Do

Skills at https://github.com/decolua/9router/tree/master/skills:

| Skill | Function | Vision? |
|-------|----------|---------|
| `9router-chat` | Chat completion (text) | No |
| `9router-image` | Text→image GENERATION (DALL-E, FLUX, Imagen) | No — generates, doesn't analyze |
| `9router-video` | Text→video generation (Grok Imagine) | No |
| `9router-embeddings` | Text→vector embeddings | No |
| `9router-stt` | Speech→text | No |
| `9router-tts` | Text→speech | No |

None provide image ANALYSIS (vision input) — only image GENERATION (output).
