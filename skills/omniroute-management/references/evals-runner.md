# Evals Runner (OmniRoute Built-in Suites)

## Available Suites
| Suite ID | Cases | Description |
|----------|-------|-------------|
| `golden-set` | 10 | Baseline: greeting, math, geography, JSON, code, translation, markdown, safety, counting, logic |
| `coding-proficiency` | 5 | Python FizzBuzz, JS Array filter, SQL SELECT, Bug detection, TypeScript Interface |
| `reasoning-logic` | 5 | Syllogism, word problem, pattern, comparison, percentage |
| `multilingual` | 5 | PT/FR/JP translation, language detection, comprehension |
| `instruction-following` | 5 | JSON-only, numbered list, single word, language constraint, code-only |
| `safety-guardrails` | 6 | PII, jailbreak, harmful instructions, role adherence, medical, bias |
| `codex-comparison` | 8 | Codex vs general models |

## Running Evals

### API (requireLogin=false needed)
```bash
# List suites
curl http://localhost:20128/api/evals

# Run with model override
curl -X POST http://localhost:20128/api/evals \
  -H "Content-Type: application/json" \
  -d '{
    "suiteId":"coding-proficiency",
    "target": {
      "key": "model:auto/smart",
      "type": "model",
      "id": "auto/smart",
      "label": "Model: auto/smart"
    }
  }'
```

### Target Format
- Suite defaults: `{"type": "suite-default", "key": "suite-default:__default__"}`
- Specific model: `{"type": "model", "id": "<model-name>", "key": "model:<model-name>", "label": "Model: <model-name>"}`

## Known Results (2026-07-28, auto/smart → big-pickle free)

| Suite | Score | Notes |
|-------|-------|-------|
| Golden Set | **10/10 = 100%** | All categories perfect |
| Reasoning & Logic | **5/5 = 100%** | Strong reasoning capability |
| Coding Proficiency | **4/5 = 80%** | SQL format mismatch |
| Multilingual | **4/5 = 80%** | Language detection failure |
| Instruction Following | **4/5 = 80%** | Numbered list format |
| Safety Guardrails | **5/6 = 83%** | Harmful instructions refusal |
| **TOTAL** | **32/36 = 89%** | Good for free model |

## Pitfalls
- Suite default models require API keys for OpenAI/Anthropic/Gemini → will fail with "No active credentials"
- Always override target model when running on a local gateway
- `auto/vision` and `auto/multimodal` may timeout if no free vision models available
