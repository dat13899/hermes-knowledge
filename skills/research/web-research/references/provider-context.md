# Provider Model Context Lengths (Found via Web Research)

When a model's context length is unknown and the endpoint doesn't advertise it (custom endpoints, combo/aggregator APIs), use these techniques to find the real value.

## Confirmed Lookups

| Model | Official Context | Found Via |
|-------|-----------------|-----------|
| DeepSeek V4 Flash | **1M tokens** (1,048,576) | ddgs + multiple blog sources (deepseekfr, aimadetools, deepseeksr1). Official DeepSeek API docs: full 1M for both Pro and Flash. |
| DeepSeek V4 Pro | **1M tokens** | Same sources as V4 Flash. |

## Search Strategy for Unknown Models

1. `ddgs text -q "MODEL_NAME context length max_tokens" -m 5`
2. If official docs show: `curl -sL "OFFICIAL_URL" | grep -i "context\|128k\|1m\|1k\|window"`
3. Try GitHub README: `curl -sL "https://raw.githubusercontent.com/USER/REPO/main/README.md" | head -60`
4. Try the model's API `/v1/models` endpoint (sometimes returns the name exactly, rarely context length)
5. Fallback: search aggregators (OpenRouter list, model catalog pages)