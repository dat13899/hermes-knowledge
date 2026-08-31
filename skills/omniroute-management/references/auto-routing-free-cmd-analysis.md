# Auto-Routing Analysis: Free + Cmd Models

## Context
Research performed 2026-07-28. User (Đạt) asked to study OmniRoute v3.8.49 docs and identify what can make the Hermes agent (Cu Em) more powerful — specifically with a **zero-cost setup**: only OpenRouter free tier (`oc/*-free`) and Command Code subscription (`cmd/*`) models.

## Current Setup
- **OmniRoute**: v3.8.48, running on localhost:20128
- **Hermes config**: static model `cmd/deepseek/deepseek-v4-pro` via `omniroute` provider
- **Compression**: Stacked (RTK→Caveman), enabled, autoTrigger=64K
- **Memory**: Hermes memory enabled (facts/profile), OmniRoute memory likely disabled
- **Connected providers**: cmd (Command Code), oc (OpenRouter), others via OmniRoute

## Key Findings

### 1. Auto-Combo Routing Works with Free + Cmd
Available auto variants for zero-cost setup:
- `auto/coding:free` — coding pool, free tier only (routes to oc/*-free)
- `auto/best-free` — all free models
- `auto/cheap` — cost-optimized (mixes free + cheapest cmd)
- `auto/offline` — highest quota availability (good for Command Code monthly quota)
- `auto/coding`, `auto/reasoning` — full pool (cmd + free) without tier filter

### 2. Available Model Pool

**Free models** (via OpenRouter free tier):
oc/deepseek-v4-flash-free, oc/minimax-m2.5-free, oc/minimax-m3-free, oc/ling-2.6-1t-free, oc/nemotron-3-super-free, oc/qwen3.6-plus-free, oc/trinity-large-preview-free

**Cmd subscription models** (via Command Code):
Claude Opus 4-7/4-8/5, Sonnet 4-6/5, Haiku 4-5, DeepSeek V4 Pro/Flash, Gemini 3.x series, GPT 5.x (codex/5.4/5.4-mini/5.5/5.6), Qwen 3.6/3.7 Max/Plus, MiniMax M2.5/M2.7/M3, Kimi K2.5, Ling 3.0 Flash-free, Muse Spark 1.1, Poolside Laguna S-2.1-free

### 3. Underutilized Features
- **session-dedup + relevance engines**: disabled, would improve compression quality
- **autoTriggerTokens** at 64K: could lower to 32K for more savings
- **Reasoning Replay Cache**: essential for thinking models, likely not toggled
- **OmniRoute Memory**: off by default (v3.8.30+), could auto-inject context
- **MCP Server**: 104 tools including web search, routing control, compression management
- **Evals**: built-in golden set, coding, reasoning suites to benchmark providers

### 4. Features Not Applicable (paid-only)
- AgentBridge MITM proxy (primarily for IDE agent intercept)
- A2A protocol (multi-agent orchestration, needs paid routing)
- Qdrant tier of memory (overkill for local setup)

## Actionable Recommendations (priority order)

1. **Switch Hermes model to `auto/coding:free`** — zero-cost, auto-picks best free model per task, auto-failover
2. **Lower autoTriggerTokens to 32K, enable session-dedup + relevance** — better compression
3. **Enable Reasoning Replay** in OmniRoute dashboard — stable thinking model usage
4. **Run Evals** (golden-set + coding-proficiency) to measure which free model performs best
5. **Consider OmniRoute Memory** for automatic cross-session context injection

## Docs Reference
Source: https://github.com/diegosouzapw/OmniRoute/tree/release/v3.8.49/docs
Files studied: README.md, ROADMAP.md, combo-context-requirements.md, compression/ (COMPRESSION_GUIDE.md, COMPRESSION_ENGINES.md, CONTEXT_EDITING.md), routing/ (AUTO-COMBO.md, REASONING_ROUTING.md, REASONING_REPLAY.md), frameworks/ (MCP-SERVER.md, MEMORY.md, SKILLS.md, AGENT-SKILLS.md, EVALS.md, A2A-SERVER.md, AGENTBRIDGE.md), guides/FEATURES.md, reference/(FEATURE_FLAGS.md, ENVIRONMENT.md), architecture/ARCHITECTURE.md, PERF_BUDGETS.md
