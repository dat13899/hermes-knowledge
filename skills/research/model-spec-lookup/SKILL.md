---
name: model-spec-lookup
description: "Look up technical specifications (context length, parameters, pricing, provider support, recommended config) for any LLM model. Multi-source triangulation across GitHub repos, official API docs, models.dev, blog posts, and community issue trackers."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, llm, model-specs, context-length, pricing, provider-config]
    related_skills: [web-research, opencode, huggingface-hub, llama-cpp]
---

# Model Spec Lookup

Look up LLM model specs when user asks about context length, parameter counts, pricing, provider support, or recommended agent config for a specific model.

## When to Use

- User asks "what's the context length for Model X?"
- User asks "does OpenCode/Claude Code support Model Y?"
- User wants recommended config (limit.context, limit.output) for a model in Opencode.jsonc
- User asks about pricing, max output tokens, supported features (thinking, tool calling)
- User asks about model architecture (MoE params total/active, attention mechanism)

## Multi-Source Triangulation Strategy

Don't stop at one source. Cross-reference 3-4 of these:

### 0. Empirical Verification (When Docs Don't Match Reality)

Docs say 1M but endpoint acts smaller? **Probe it yourself.** See `references/empirical-context-probing.md` for the full binary-search technique.

Quick version:
1. Send ~200K tokens of natural text + simple instruction ("What is 2+2?")
2. If model answers correctly → try ~400K
3. If model returns empty → try ~150K → binary search down to find breakpoint
4. Compare tested limit vs documented limit — provider/proxy often caps lower

### 1. Official Model / API Docs (fastest, most authoritative)

Search or curl the official docs site:

```bash
# DeepSeek API Docs
curl -sL "https://api-docs.deepseek.com/news/news260424" | grep -iA5 "context\|1M\|tokens"

# Anthropic docs
web_search("claude sonnet 4 context length site:docs.anthropic.com")

# OpenRouter model list
curl -s "https://openrouter.ai/api/v1/models" | python -c "import json,sys; data=json.load(sys.stdin); [print(m['id'], m.get('context_length','?')) for m in data if 'deepseek' in m['id']]"
```

### 2. GitHub Repo + Config Files (for agent-tooling context)

When the model is used by an agent tool (OpenCode, Codex, Claude Code):

```bash
# Check the agent's model registry / config files
# OpenCode uses models.dev — search for provider/model
web_search("models.dev deepseek-v4-flash context limit")

# Check GitHub issues for feature requests / bug reports mentioning context limits
web_search("anomalyco/opencode deepseek-v4-flash context limit")

# Check raw config files in the repo
web_search("raw.githubusercontent.com/sst/opencode main deepseek-v4-flash context limit")
```

Look for:
- `limit.context` values in JSON configs
- `context_length` in provider definitions
- Issues about context limits, free-tier caps

### 3. HuggingFace Model Card

For open-weight models, check the HF card:

```bash
web_search("huggingface.co deepseek-v4-flash context window")
# Or direct:
web_search("huggingface.co/deepseek-ai/DeepSeek-V4-Flash context")
```

HF model cards reliably list: total params, active params, context length, architecture, license.

### 4. Web Search + Blog Posts

```bash
web_search("model X context length tokens")
web_search("model X pricing per token")
web_search("opencode model X recommended config context limit")
```

Blogs from aimadetools, haimaker.ai, morphllm.com often have detailed setup guides with exact config blocks.

### 5. Community Issue Trackers

GitHub issues often surface:
- Context limit bugs or caps
- Free-tier vs paid tier differences
- Recommended settings from maintainers

```bash
web_search("anomalyco/opencode issues deepseek-v4-flash context")
```

## Example Session: DeepSeek V4 Flash Context

When user asked "find context length for DeepSeek V4 Flash in OpenCode":

1. **GitHub README** — `web_extract("https://github.com/sst/opencode")` → didn't load (timeout)
2. **Web search** — `web_search("sst/opencode deepseek v4 flash context")` → found blog posts mentioning 1M
3. **Models.dev registry** — found `opencode/deepseek-v4-flash-free.limit.context = 200000` (free tier cap)
4. **Official DeepSeek API docs** — `curl api-docs.deepseek.com` → confirmed "Both models support 1M context"
5. **Community issues** — `anomalyco/opencode issue #27929` confirmed free tier capped at 200K, base model is 1M
6. **HuggingFace** — HF blog: "Both have a 1M-token context window"

**Verdict from triangulation:** DeepSeek V4 Flash native = **1M tokens**. Free tier in OpenCode Zen capped at **200K**. (Cross-reference confirmed.)

## Common Lookup Patterns

### Pattern A: Context Length
```
Sources to check in order:
1. Official docs (model card)
2. HuggingFace model page
3. Models.dev if for agent tooling
4. Community issues (verify against caps/tiers)
```

### Pattern B: Provider Config for OpenCode
```
Sources:
1. models.dev → `/providers/opencode/` or `/models/deepseek/deepseek-v4-flash`
2. OpenCode docs → `opencode.ai/docs/providers`
3. Blog guides → search "opencode MODEL setup guide"
4. Raw JSON config examples from search results
```

### Pattern C: Parameter Count + Architecture
```
Sources:
1. HuggingFace model card (best — total/active params clearly listed)
2. Official release blog
3. API docs pricing page
```

## Pitfalls

- **Free tier != base model cap.** Free/zen tiers often limit context below the model's native capability. Check both values.
- **Web_extract fails on GitHub pages** (timeout for JS-heavy pages). Fall back to web_search + curl for GitHub content.
- **DuckDuckGo (ddgs) backend can't extract full pages.** Use web_extract only if backend is Firecrawl/Tavily/Exa. Otherwise use curl.
- **Model names change.** Check for migration notices (e.g. deepseek-chat → deepseek-v4-flash, deprecated after a date).
- **Context in thinking mode may differ from non-thinking.** Some models consume more or have different limits with CoT.
- **OpenRouter / proxy providers may report different context than native model.** Always check the provider's docs not just the model's.
- **Docs !== reality.** Proxies, free tiers, and custom endpoints often cap context lower than documented. When in doubt, empirically probe via API — see `references/empirical-context-probing.md`.

## Verification

After lookup, verify you have these 3 pieces:
1. Native context length (e.g. 1M = 1,048,576 tokens)
2. Any tier cap (free tier capped at 200K, etc.)
3. Recommended `limit.context` for agent config
4. Source URLs for each claim, in case user asks for citation