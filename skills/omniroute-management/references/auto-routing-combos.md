# Auto-Routing Variants (OmniRoute v3.8.48+)

## Model ID Syntax

```
auto/<category>:<tier>
```

## Available Variants (36 total)

### By Category
| Variant | Use Case |
|---------|----------|
| `auto/coding` | Code generation, quality-first |
| `auto/reasoning` | Thinking/reasoning tasks |
| `auto/vision` | Vision-capable models |
| `auto/multimodal` | Multi-modal (vision+text+audio) |
| `auto/chat` | General conversation |
| `auto/fast` | Low latency priority |

### By Tier
| Variant | Behavior |
|---------|----------|
| `auto/cheap` | Cost-optimized (cheapest first) |
| `auto/offline` | Favors providers with quota available |
| `auto/smart` | Quality-first + 10% exploration |
| `auto/best-free` | Free models only |
| `auto/best-coding` | Best overall coding models |
| `auto/best-reasoning` | Best thinking/reasoning models |
| `auto/best-vision` | Best vision-capable models |

### Composed (Category:Tier)
| Example | Resolves To |
|---------|-------------|
| `auto/coding:free` | Coding pool, free tier |
| `auto/coding:cheap` | Coding pool, cost-optimized |
| `auto/coding:fast` | Coding pool, low-latency |
| `auto/coding:pro` | Coding pool, premium tier |
| `auto/coding:reliable` | Coding pool, reliability-focused |
| `auto/reasoning:pro` | Reasoning models, premium |

## Scoring Factors (9-factor engine)
- Quality (Arena ELO rankings)
- Speed (latency)
- Cost
- Reliability (circuit-breaker health)
- Context window size
- Quota availability
- Category fitness
- Tier filter
- Exploration rate (10% for smart, 0% for most)

## Fallback Behavior
- Auto-routing is **fail-open**: if no model matches constraints, full pool is used
- Combo fallback chain: tries model #1 → on failure → model #2 → ... → model N
