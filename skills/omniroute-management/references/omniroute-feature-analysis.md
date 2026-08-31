# OmniRoute Feature Analysis — Key Capabilities for Hermes

**Source**: https://github.com/diegosouzapw/OmniRoute/tree/release/v3.8.49/docs  
**Version installed**: 3.8.48  
**Docs reference**: 3.8.49  
**Last updated**: 2026-07-28

## Available Auto-Routing Variants (36 total)

All accessible via model ID in any OpenAI-compatible client. Tested with Hermes via omniroute provider.

| Variant | Purpose |
|---------|---------|
| `auto/smart` | Quality-first + 10% exploration — recommended default |
| `auto/coding` | Coding-quality weighted |
| `auto/reasoning` | Thinking/reasoning pool |
| `auto/vision` | Vision-capable models |
| `auto/multimodal` | Multimodal-capable |
| `auto/coding:free` | Coding pool, free tier only |
| `auto/coding:cheap` | Coding pool, cost-optimized |
| `auto/coding:fast` | Coding pool, low-latency |
| `auto/coding:pro` | Coding pool, premium tier |
| `auto/coding:reliable` | Coding pool, circuit-breaker health + latency stability |
| `auto/cheap` | Cost-optimized (lowest cost first) |
| `auto/offline` | Prefers providers with highest quota |
| `auto/best-free` | Best free model across all categories |
| `auto/best-coding` | Best for coding |
| `auto/best-reasoning` | Best for reasoning |
| `auto/best-vision` | Best for vision |
| `auto/best-fast` | Best for speed |
| `auto/best-chat` | Best for general chat |
| `auto/reasoning:pro` | Reasoning, premium tier only |
| `auto/vision` | Vision pool |
| `auto/fast` | Low-latency weighted |
| `auto/chat` | General chat pool |
| `auto/claude-opus` | Claude Opus family |
| `auto/claude-sonnet` | Claude Sonnet family |
| `auto/gemini` | Gemini family |
| `auto/pro-*` | Premium-tier variants (coding, reasoning, vision, chat, fast) |
| `auto/<model-family>` | Model-family-specific: gemma, llama, glm, minimax, mimo, zai |

## Free Model Pool (oc/*)

Models available via OpenRouter free tier:
- `oc/big-pickle` — 200K context, tool-calling, thinking/reasoning, effort tiers. Selected by auto/smart as best free model.
- `oc/deepseek-v4-flash-free`
- `oc/minimax-m3-free`, `oc/minimax-m2.5-free`
- `oc/ling-2.6-1t-free`
- `oc/nemotron-3-super-free`
- `oc/qwen3.6-plus-free`
- `oc/trinity-large-preview-free`

## Provider Prefixes Observed

| Prefix | Provider |
|--------|----------|
| `oc/` | OpenRouter (free tier) |
| `cmd/` | Command Code subscription |
| `command-code/` | Command Code (alias) |
| `ddgw/` | DuckDuckGo Web |
| `aug/` | Auggie |
| `tllm/` | Together/Local LLM |
| `pepper/` | Pepper |
| `mcode/` | Mimo Code |

## MCP Server Details

- **Transport**: Streamable HTTP at `/api/mcp/stream`
- **Tools**: 99 tools across routing, cache, compression, memory, skills, proxy, pool, context source ops
- **Auth**: LOCAL_ONLY tier (loopback only). Requires `mcp-session-id` header for session management.
- **Hermes integration**: `hermes mcp add omniroute --url http://localhost:20128/api/mcp/stream`

## Key Management API Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `POST /api/evals` | Run eval suite | management |
| `GET /api/evals` | List eval suites | management |
| `GET /api/a2a/status` | A2A status | management |
| `POST /a2a` | A2A JSON-RPC | Bearer token |
| `GET /api/settings` | List settings | management |
| `POST /api/settings` | Update setting | management |
| `/.well-known/agent.json` | A2A agent card | none |

## API Key Hash (for DB management key creation)

```python
key_hash = hashlib.sha256(raw_api_key.encode()).digest().hex()
```

The hash is stored in `api_keys.key_hash` column. The raw key is stored in `api_keys.key` column. Validation query: `SELECT ... FROM api_keys WHERE key = ? OR key_hash = ?`.
