# Empirical Context Length Probing (API Binary Search)

When docs say "1M" but the endpoint acts differently — probe it yourself.

## Technique: Binary Search via API

Send increasing context sizes, check when model stops producing meaningful output.

### 1. Baseline Check

```python
python -c "
import json, urllib.request, re

payload = json.dumps({
    'model': 'model_name',
    'messages': [{'role': 'user', 'content': 'What is 2+2? One number.'}],
    'max_tokens': 5
}).encode()

req = urllib.request.Request('http://endpoint/v1/chat/completions',
    data=payload, headers={'Content-Type': 'application/json'}, method='POST')
resp = urllib.request.urlopen(req, timeout=30)
raw = resp.read().decode()
match = re.search(r'({.*?})\s*(?:data:|$)', raw, re.DOTALL)
obj = json.loads(match.group(1))
print(f'prompt_tokens={obj[\"usage\"][\"prompt_tokens\"]}|{obj[\"choices\"][0][\"message\"][\"content\"]}')
"
```

### 2. Binary Search

```python
import json, urllib.request, re

# Start with natural text to fill context
chunk = 'DeepSeek V4 Flash is a large language model. '

# Use unique factual sentences to avoid token compression skewing counts
sentences = [f'Fact {i}: sentence. ' for i in range(500)]
content_base = ''.join(sentences)

# Try different multipliers
for mult in [50, 100, 150, 200, 300]:
    content = content_base * mult
    content += '\n\nWhat is 2+2? One number.'
    
    # ... API call same as baseline ...
    
    print(f'mult={mult}|prompt_tokens={usage}|\"{content_out}\"')
```

### 3. Interpretation

| Signal | Meaning |
|--------|---------|
| Returns correct answer ("4") | Within working context |
| Returns empty string `""` | Context overflow — not producing output |
| Returns truncated/garbled | Edge of context — partial attention |
| Error 400/413/504 | Hard limit hit (reject before inference) |
| Error timeout | Processing but can't finish in window |

### 4. Key Decisions

**Content pattern matters:**
- Repeated text → token compression undercounts (prompt_tokens < actual)
- Unique sentences per chunk → more accurate token counts
- Natural paragraphs ("DeepSeek V4 Flash is a...") → realistic but slower to generate
- Short instruction at end → must be readable despite preceding noise

**Stream vs non-stream response:**
- Some endpoints return SSE (`data: ...` lines) even when `stream=false`
- Extract first JSON object: `re.search(r'({.*?})\s*(?:data:|$)', raw, re.DOTALL)`
- Handle `data: [DONE]` trailer

**Endpoint quirks recorded from real sessions:**

| Endpoint | Doc'd Limit | Tested Limit | Notes |
|----------|------------|--------------|-------|
| DeepSeek official API | 1M | 1M | Full support |
| combo CMC (`cmc/deepseek/deepseek-v4-flash`) | 1M | ~250K | Server-side cap, returns `""` beyond |
| DeepSeek via OpenRouter | 1M | Depends on tier | Check provider page |
| OpenCode Zen free tier | 200K | 200K | Hard cap in OpenCode, not model |

### 5. Why Not Just Trust Docs

- **Proxy/providers** (combo, OpenRouter, CMC) apply their own caps below model's native limit
- **Free tiers** artificially reduce context
- **Legacy endpoints** may route to older models with smaller context
- **Cost-saving** — providers limit context to reduce compute
- **Bug** — some endpoints silently truncate or ignore overflow

### 6. Pitfalls

- **Token count inflation**: Repeated text compresses more than unique text. `prompt_tokens` from usage may undercount vs what model actually sees.
- **Empty response != error**: Many endpoints return HTTP 200 with empty `content` on overflow. Check `finish_reason` if available.
- **Timeout vs overflow**: Distinguish by testing a smaller payload that times out too (likely network) vs one that returns instantly empty (overflow).
- **SSE parsing**: Endpoints mixing SSE + JSON can confuse naive json.loads(). Always use regex to extract first JSON block.
- **One-shot vs conversational context**: Some endpoints apply different limits for a single message vs accumulated conversation history.
