# DeepSeek V4 Flash Spec Reference (2026-07-08)

## Context Length

| Source | Value | Notes |
|--------|-------|-------|
| DeepSeek official API docs | **1M tokens** | "1M context is now the default across all official DeepSeek services" |
| HuggingFace blog | **1M tokens** | "Both have a 1M-token context window" |
| Models.dev (OpenCode) | **1,048,576** (paid) / **200,000** (free/zen tier) | Free tier capped by OpenCode Zen |
| OpenCode config example | **1,048,576** | `limit: { context: 1048576, output: 262144 }` |
| Combo CMC proxy (`cmc/deepseek/deepseek-v4-flash`) | **~250K** ⚠️ | Tested empirically — model returns `""` (empty) beyond ~300K tokens. Server-side cap, not model limitation |

## Parameters

| Spec | Value |
|------|-------|
| Total params | 284B |
| Active params | 13B |
| Architecture | Mixture-of-Experts (MoE) |
| Attention | Token-wise compression + DSA (DeepSeek Sparse Attention) |
| Context default | 1M (1,048,576 tokens) |

## Naming

- **DeepSeek-V4-Flash** — official model name
- `deepseek-v4-flash` — API model ID
- Legacy `deepseek-chat` (non-thinking) and `deepseek-reasoner` (thinking) route to V4 Flash until Jul 24, 2026

## OpenCode Config

```jsonc
"deepseek-v4-flash": {
  "name": "DeepSeek-V4-Flash",
  "limit": { "context": 1048576, "output": 262144 },
  "options": { "reasoningEffort": "max" }
}
```

Using OpenCode's built-in deepseek provider, auto-resolves to 1M for paid tiers.

## Sources

- https://api-docs.deepseek.com/news/news260424
- https://huggingface.co/blog/deepseekv4
- https://models.dev/models/deepseek/deepseek-v4-flash
- https://github.com/anomalyco/opencode/issues/27929 (free tier cap)

## Related Models

| Model | Params (total) | Params (active) | Context |
|-------|------|-------|---------|
| DeepSeek-V4-Pro | 1.6T | 49B | 1M |
| DeepSeek-V4-Flash | 284B | 13B | 1M |