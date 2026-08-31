# OmniRoute Auto-Combo Models, MCP Tools & Evals Reference

Discovered during deep-dive research session (2026-07-28) on OmniRoute v3.8.48 (docs v3.8.49).

## Auto-Combo Model IDs (Zero-Config Routing)

Pick the `model` field value when calling `/v1/chat/completions`. No combo creation needed.

### Generic Category × Tier

| Model ID | When to use |
|----------|-------------|
| `auto/smart` | **Default** — quality-first + 10% exploration for model discovery |
| `auto/coding` | Code generation, quality-weighted |
| `auto/coding:free` | Coding, free tier only |
| `auto/coding:cheap` | Coding, cost-optimized |
| `auto/coding:fast` | Coding, low-latency |
| `auto/coding:pro` | Coding, premium tier |
| `auto/coding:reliable` | Coding, circuit-breaker health + latency stability |
| `auto/reasoning` | Thinking/reasoning models |
| `auto/reasoning:pro` | Reasoning, premium tier |
| `auto/vision` | Vision-capable models |
| `auto/multimodal` | Multimodal-capable models |
| `auto/chat` | General chat, balanced |
| `auto/fast` | Low-latency priority |
| `auto/cheap` | Cost-optimized (alias `floor`) |
| `auto/offline` | Favors providers with highest quota availability |
| `auto/best-free` | Best free model across all capabilities |
| `auto/best-coding` | Best coding model (quality) |
| `auto/best-reasoning` | Best reasoning model |
| `auto/best-vision` | Best vision model |
| `auto/best-fast` | Best speed |
| `auto/best-chat` | Best general chat |

### Brand Pools

| Model ID | Description |
|----------|-------------|
| `auto/claude-opus` | Claude Opus family |
| `auto/claude-sonnet` | Claude Sonnet family |
| `auto/gemini` | Gemini family |
| `auto/gemma` | Gemma family |
| `auto/llama` | Llama family |
| `auto/minimax` | MiniMax family |
| `auto/mimo` | Mimo family |
| `auto/zai` | ZAI family |

## 9-Factor Scoring Engine

Auto-Combo scores models on: quality (Arena ELO), speed (latency), cost, reliability (circuit breaker health), context window size, quota availability, task capability fit, exploration bonus (10% for `auto/smart`), and provider tier classification.

## Compression Engines Reference

| Engine | What it does | Our status |
|--------|-------------|------------|
| `rtk` (level: full) | Command-aware terminal/tool-output filtering (60-90%) | ✅ ON |
| `caveman` (level: full) | Natural-language prompt condensation (~30%) | ✅ ON |
| `stacked` | Pipeline: rtk → caveman (78-95% eligible range) | ✅ ON |
| `session-dedup` | Remove duplicate messages across turns | ✅ Turned ON |
| `relevance` | Prune content with low relevance to current query | ✅ Turned ON |
| `headroom` | Keep safety margin in context window | ✅ Turned ON |
| `autoTriggerTokens` | Threshold to activate compression | Set to 32000 |

## Evals Results (auto/smart → big-pickle via OpenRouter free tier)

| Suite | Pass Rate | Details |
|-------|-----------|---------|
| Golden Set | 10/10 (100%) | Greeting, math, geography, JSON, code gen, translation, safety, etc. |
| Reasoning & Logic | 5/5 (100%) | Syllogism, word problems, pattern recognition |
| Coding Proficiency | 4/5 (80%) | Failed: SQL SELECT format mismatch |
| Multilingual | 4/5 (80%) | Failed: Language detection |
| Instruction Following | 4/5 (80%) | Failed: Numbered list format |
| Safety Guardrails | 5/6 (83%) | Failed: Harmful instructions refusal |
| **TOTAL** | **32/36 (89%)** | |

## MCP Server — 99 Tools (key ones)

| Tool | Purpose |
|------|---------|
| `omniroute_get_health` | Health status, uptime, memory, circuit breakers |
| `omniroute_route_request` | Send chat completion through OmniRoute routing |
| `omniroute_list_models_catalog` | All models with capabilities, pricing, status |
| `omniroute_web_search` | Web search via multiple backends |
| `omniroute_check_quota` | Remaining quota for providers |
| `omniroute_cost_report` | Cost report by period |
| `omniroute_list_combos` | All configured combos |
| `omniroute_best_combo_for_task` | Recommend combo for task type |
| `omniroute_explain_route` | Explain why a specific provider was chosen |
| `omniroute_simulate_route` | Dry-run routing path |
| `omniroute_pick_fastest_model` | Pick fastest model from pool |
| `omniroute_set_routing_strategy` | Update combo strategy at runtime |
| `omniroute_set_resilience_profile` | Circuit breaker, retry, timeout tuning |
| `omniroute_list_providers` | All connected providers |
| `omniroute_list_sessions` | Active sessions |

## Management API Key Creation

OmniRoute uses SHA256(key).digest("hex") for key_hash. Keys with `manage` scope are required for management endpoints.

## Key Config Settings (DB)

Settings stored in `~/.omniroute/storage.sqlite` `key_value` table under namespaces:
- `compression.*` — compression settings
- `settings.*` — feature flags (mcpEnabled, a2aEnabled, requireLogin)
- `lkgp.*` — auto-routing state
