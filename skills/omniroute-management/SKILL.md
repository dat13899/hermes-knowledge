---
name: omniroute-management
description: Manage OmniRoute AI Gateway (localhost:20128) — restart, settings via SQLite, compression, combo routing, auto-routing, reasoning replay, memory, MCP, evals
---

# OmniRoute AI Gateway Management

OmniRoute is the local AI gateway on `localhost:20128` that routes LLM requests across 290+ providers. Hermes connects to it via the `omniroute` provider.

Current installed version: v3.8.48. Docs reference: v3.8.49.

## Evals Results (2026-07-28)
auto/smart (big-pickle free) scored **89%** across 6 suites:
- Golden Set: 10/10 (100%), Reasoning: 5/5 (100%), Coding: 4/5 (80%)
- Multilingual: 4/5 (80%), Instruction Following: 4/5 (80%), Safety: 5/6 (83%)
Run via `POST /api/evals` with model target. See `references/evals-runner.md`.

## OpenAI-Compatible API (for scripts/agents)

OmniRoute exposes an **OpenAI-compatible chat endpoint** at `http://localhost:20128/v1/chat/completions` (Hermes itself uses this as `base_url: http://localhost:20128/v1`).

Working models (verified 2026-08-01 — provider `oc/` đã hết key, đổi sang `cmd/`):
- **`cmd/deepseek/deepseek-v4-flash`** — free tier, dùng cho voice agent + tool calling (streamText OK)
- Xem danh sách đầy đủ: `curl http://localhost:20128/api/models` (cột fullModel + available)
- `cmd/claude-haiku-4-5-20251001` → 403 MODEL_NOT_IN_PLAN (plan không có)
- Không có model audio nào (18 model toàn chat) — STT/TTS phải dùng local (whisper/edge-tts)

Streaming works (`stream:true` returns SSE chunks). Tool calling (`tools` + `tool_choice:auto`) works — the agent loop pattern (assistant→tool_calls→tool→assistant) runs fine.

### Model discovery

**List all models (flat, with status):** `GET /api/models` — returns `[{provider, model, name, fullModel, alias, available}]`. Filterable with `?provider=cmd`.

**Get single model detail:** `GET /v1/models/<provider>/<model>` — returns context_length, capabilities, max_output_tokens, root/parent chains. Example: `GET /v1/models/command-code/deepseek/deepseek-v4-flash`.

**Provider connections:** `GET /api/providers` — returns all configured provider connections with `id, provider, name, priority, isActive, testStatus, backoffLevel, authType, maxConcurrent, quotaWindowThresholds, rateLimitOverrides`. Use this to check which keys are active and their priority order.

## Filter Hermes model picker to command-code/* only (v3.8.48, 2026-08-27)

`/api/models` trả về **18 model `cmd/*`** (cột `available`), nhưng `/v1/models`
(cái Hermes live-probe khi chọn Provider `omniroute`) trả về **345 model** —
thêm nhiều nhóm *routing alias ảo*: `auto/*`, `aug/*`, `tllm/*`, `no-think/*`,
`oc/*`, `felo/*`, `ddgw/*`, `mcode/*`... Đây KHÔNG phải model command-code thật,
chỉ là luồng định tuyến nên picker hiện quá nhiều.

**Tại sao `/api/models` `available=true` không đáng tin:** nó báo `gpt-5.5`,
`claude-opus-4-7`... available nhưng request thật lại `403 MODEL_NOT_IN_PLAN`
(giới hạn plan). Nguồn sự thật PHẢI là probe thực tế, không phải cờ available.

### Cách lọc (fix đã áp dụng 2026-08-27)

Thêm `discover_models: false` + khoá cứng `models:` vào **`providers.omniroute`**
trong `config.yaml`. Khi `discover_models: false`, Hermes **ngừng probe** `/v1/models`
và hiển thị đúng danh sách `models:` khai báo. Xem `hermes_cli/model_switch.py`
section 3/4 (`_models_config_is_allowlist`, `_discovery_allowed`).

```yaml
providers:
  omniroute:
    base_url: http://localhost:20128/v1
    api_key: YOUR_OMNIROUTE_API_KEY_HERE
    discover_models: false        # BẮT BUỘC — nếu thiếu sẽ vẫn probe 345 model
    models:
      command-code/deepseek/deepseek-v4-flash-vision-exp: {}
      command-code/deepseek/deepseek-v4-flash: {}
      # ... (39 model command-code chạy được)
```

### Các bước làm (đúc kết từ task 2026-08-27)

1. **Lấy danh sách command-code thật:** `curl -s "http://localhost:20128/api/models?all=true" -H "Authorization: Bearer $MK"` (dùng mgmt key `~/.omniroute/management_key.txt`). Lọc `provider == 'cmd'`.
2. **Probe từng model** bằng `POST /v1/chat/completions` max_tokens=1. Chú ý quirk:
   - Model chạy được trả về **SSE** (bắt đầu bằng `data:`) → ghi nhận OK.
   - `403 MODEL_NOT_IN_PLAN` → loại (giới hạn plan).
   - `403 ...not recognized` → loại (đặc biệt các biến thể `-high/-low/-medium/-xhigh` của Claude).
   - **Dùng script Python probe** (urllib, đọc SSE), đừng dùng `curl` đọc JSON thuần vì mất cú pháp SSE dễ ghi nhầm "KO".
3. **Ghi config:** thêm `discover_models: false` + `models: {<mỗi model>: {}}` vào `providers.omniroute`.
4. **Xoá entry legacy trùng:** `custom_providers[0]` ("Local (127.0.0.1:20128)", model rác `deepseek_v4_flash`) trỏ cùng gateway qua `127.0.0.1` — xoá để picker không còn 2 dòng trùng. `custom_providers` không được dùng ở đâu vì model/vision/web_extract đều chạy qua `providers.omniroute`.
5. **Verify bằng function thật** (không chỉ đọc YAML):
   ```python
   from hermes_cli.config import load_config, get_compatible_custom_providers
   from hermes_cli.model_switch import list_picker_providers
   rows = list_picker_providers(current_provider='omniroute',
       current_base_url='http://localhost:20128/v1',
       user_providers=cfg['providers'], custom_providers=compatible, current_model=...)
   # dòng omniroute phải models=39, all_command-code=True
   ```

**Pitfall bổ sung:**
- `hermes config set providers.omniroute.<k> <v>` hoạt động đúng (dotted path).
  Nhưng `hermes config set custom_providers[0].<k> <v>` tạo **key rác** `custom_providers[0]` ở top-level — KHÔNG dùng, chọn path `providers.` thay thế.
- `models:` nhận JSON dict: `hermes config set providers.omniroute.models '{"command-code/x":{}}'`.
- `config.yaml` không có comment → `yaml.safe_dump` round-trip an toàn (verify byte-identical trước).
- **Cần session mới/new chat** để picker dùng config mới (giống memory limit).
- Backup: `cp config.yaml config.yaml.bak.$(date)` trước khi sửa.

**Response headers** (useful for debugging routing):
- `x-omniroute-route-class`: e.g. `CLIENT_API`
- `x-request-id`: unique per request
- `x-correlation-id`: ties related requests
- `x-omniroute-session-id`: persistent client session

### Non-streaming mode

OmniRoute may default to SSE streaming. For scripts that need JSON responses, pass `"stream": false` explicitly in the request body. Python httpx example:

```python
import httpx
r = httpx.post('http://localhost:20128/v1/chat/completions',
    headers={'Authorization': 'Bearer sk-omniroute', 'Content-Type': 'application/json'},
    json={'model': 'cmd/deepseek/deepseek-v4-flash', 'max_tokens': 200, 'stream': False,
          'messages': [{'role': 'user', 'content': 'hello'}]},
    timeout=60)
body = r.json()
```

## Introspection / Admin API Endpoints

These endpoints are available for inspecting provider and model configuration (NOT part of OpenAI-compatible `/v1/` surface):

| Endpoint | Method | Use |
|---|---|---|
| `/api/models` | GET | Full model catalog with `fullModel`, `provider`, `available` |
| `/api/models?provider=cmd` | GET | Filter models by alias |
| `/v1/models/:id?provider=X` | GET | Single model metadata (context_length, capabilities, thinking tiers) |
| `/api/providers` | GET | Provider connections: API keys, priorities, `autoSync`, proxy settings |

### Determining actual upstream model version

Provider wrappers (Command Code, etc.) may not expose upstream version in the model ID. To investigate:

1. **Check provider config**: `GET /api/providers` → look for `autoSync: true` (means provider auto-updates to latest upstream)
2. **Make a test call**: check the response `model` field — wrappers may return their own ID, not upstream
3. **Ask the model directly**: unreliable — wrappers rebrand identity (e.g. DeepSeek via CC calling itself "Claude")

Example: checking command-code's deepseek-v4-flash:
```bash
curl -s http://localhost:20128/v1/models/command-code/deepseek/deepseek-v4-flash \
  -H "Authorization: Bearer sk-omniroute" | jq '{id, context_length, capabilities}'
# → context_length: 1000000, capabilities.thinking: true, effort_tiers: [none,low,medium,high,xhigh]

### ⚠️ Python urllib bị chặn 403 (verified 2026-08-01)
OmniRoute chặn `User-Agent: Python-urllib/3.x` → HTTP 403 `insufficient_quota` ngay cả khi curl OK. Khi gọi `/v1/chat/completions` từ Python phải set header `User-Agent: curl/8.0`:
```python
req = urllib.request.Request(url, data=..., headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"}, method="POST")
```
Triệu chứng: cùng payload curl chạy OK nhưng Python bị 403. Fix 1 dòng header.

### ⚠️ Model catalog CHANGED (2026-08-01): `oc/` → `cmd/` prefix
Provider setup đổi — `oc/deepseek-v4-flash-free` ngừng hoạt động (500 Invalid API key). Model hiện tại dùng prefix **`cmd/`**: `cmd/deepseek/deepseek-v4-flash`, `cmd/claude-opus-4-7`, `cmd/gpt-5.5`, `cmd/moonshotai/Kimi-K2.6`, `cmd/MiniMaxAI/MiniMax-M2.5`, `cmd/Qwen/Qwen3.6-Plus`...

**Danh sách model khả dụng (authoritative):**
```bash
curl -s http://localhost:20128/api/models | python -c "import json,sys; [print(m['fullModel'],'|',m['available']) for m in json.load(sys.stdin)['models']]"
# cũng có: GET /v1/models (OpenAI-style, id = "auto/best-coding" combos)
```

**Lưu ý availability (test 2026-08-01):**
- `cmd/claude-haiku-4-5-20251001` → 403 `MODEL_NOT_IN_PLAN` (chỉ Pro+ plan)
- `cmd/gpt-5.4-mini` → lỗi "No output generated" khi tool calling
- `cmd/deepseek/deepseek-v4-flash` + `cmd/MiniMaxAI/MiniMax-M2.5` → nhanh nhất (~2.3s/call), tool calling OK
- `cmd/moonshotai/Kimi-K2.6` → chậm (~5.9s)

### ⚠️ OmniRoute chặn User-Agent `Python-urllib/*` — set UA curl/8.0
Gọi từ Python (`urllib`/`requests` mặc định) → HTTP **403 insufficient_quota** với body `[403]: <!doctype html>`, trong khi curl cùng payload chạy OK. Khác biệt duy nhất là User-Agent. Fix: set `User-Agent: curl/8.0` (hoặc bất kỳ UA browser/curl nào):
```python
req = urllib.request.Request(url, data=..., headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"}, method="POST")
```
Các thư viện khác gọi OmniRoute (AI SDK Node fetch, curl) không bị ảnh hưởng.
Model prefixes/IDs change when OmniRoute updates provider configs. On 2026-08-01 `oc/deepseek-v4-flash-free` started returning `[500]: Invalid API key` (then `model_not_found`); the live catalog moved to **`cmd/`** prefix with provider-qualified IDs. **Don't hardcode model IDs in scripts** — discover them:

```bash
curl -s http://localhost:20128/api/models | python -c "
import json,sys
for m in json.load(sys.stdin)['models']:
    print(m['fullModel'], '|', m['available'])"
# e.g. cmd/deepseek/deepseek-v4-flash, cmd/claude-haiku-4-5-20251001, cmd/gpt-5.4-mini
```

Also `GET /v1/models` returns combo IDs (`auto/best-coding`, `auto/best-reasoning`, ...) — useful for routing presets. When a model 500s "Invalid API key" via BOTH curl and SDK, re-list `/api/models` before debugging further — the ID itself is stale. `omniroute_list_models_catalog` MCP (no capability filter) lists models too, but `/api/models` is the authoritative full list.

### ⚠️ OmniRoute blocks Python `urllib` — User-Agent 403 quirk
Python's `urllib.request` gets **HTTP 403 `insufficient_quota`** (error body: `[403]: <!doctype html>`) when calling `/v1/chat/completions`, while curl with the same payload succeeds. Root cause: OmniRoute rejects the default `User-Agent: Python-urllib/3.x`. Fix: set a curl-like User-Agent on every urllib request:
```python
req = urllib.request.Request(OMNI_URL, data=payload.encode(),
    headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"}, method="POST")
```
This bit hard in the voice-lab agent (2026-08-01) — the failure signature (curl OK / Python 403) is the tell. Symptom can masquerade as "insufficient quota" even when quota is fine.

### Model names CHANGE over time — discover via `/api/models` (not the catalog MCP)
The free model `oc/deepseek-v4-flash-free` can start returning `500 Invalid API key` (or `model_not_found`) when OmniRoute's provider setup rotates — this happened 2026-08-01. Do NOT assume the old name still works. Discover current models with:
```bash
curl -s http://localhost:20128/api/models | python -c "import json,sys; [print(m['fullModel'], m['available']) for m in json.load(sys.stdin)['models']]"
```
This returns `fullModel` entries like `cmd/claude-sonnet-4-6`, `cmd/deepseek/deepseek-v4-flash` — **the `cmd/` prefix is the working provider prefix** (not `cc/`, not `command-code/`, not `oc/`). The catalog MCP (`omniroute_list_models_catalog`) returns `provider: "command-code"` which is NOT a valid request prefix — trust `/api/models` over the MCP catalog for exact model IDs.

**As of 2026-08-01**: the free model rotated from `oc/deepseek-v4-flash-free` → **`cmd/deepseek/deepseek-v4-flash`** (works with tool calling + streaming via curl, AI SDK, and Python).

**⚠️ No audio/ASR models**: OmniRoute's 18 chat models are all text-only (DeepSeek, Claude, GPT, Kimi, GLM, MiniMax, Qwen). There is NO whisper/audio/transcribe model — STT must be done locally (faster-whisper) before calling the LLM.
curl -s http://localhost:20128/api/models | python -c "import json,sys; [print(m['fullModel'],'|',m['available']) for m in json.load(sys.stdin)['models']]"
```
The `fullModel` field carries the real prefix (e.g. `cmd/deepseek/deepseek-v4-flash`, `cmd/claude-sonnet-4-6`). Also note the catalog MCP (`omniroute_list_models_catalog`) may show a provider label like `command-code` that does NOT match the API prefix — trust `/api/models` `fullModel` instead. Model IDs like `cc/claude-*` or `lma/*` → "No active credentials" are wrong guesses; the working prefix was `cmd/`.

```bash
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"oc/deepseek-v4-flash-free","messages":[{"role":"user","content":"hi"}],"max_tokens":20,"stream":false}'
```

### PITFALL: Python urllib gets 403 `insufficient_quota` — OmniRoute blocks the Python UA

Python `urllib.request` sends `User-Agent: Python-urllib/3.x` by default and OmniRoute **rejects it with HTTP 403** (`insufficient_quota`, body `[403]: <!doctype html>`), even when the identical payload works via curl. **Fix: set `User-Agent: curl/8.0` (or any curl-ish UA) on the request.**

```python
req = urllib.request.Request(url, data=body, headers={
    "Content-Type": "application/json",
    "User-Agent": "curl/8.0",   # REQUIRED — python-urllib UA gets 403
}, method="POST")
```

Also: urllib treats HTTPError as exception — catch `urllib.error.HTTPError` and surface `e.code` + `e.read().decode()[:200]` for diagnostics.

Node is NOT blocked: AI SDK 7 `createOpenAI({ baseURL: 'http://localhost:20128/v1' })` + `generateText` works with no special UA (Node's fetch is allowed). Only Python urllib needs the header.

### PITFALL: quick-tunnel PID belongs to OmniRoute — do NOT kill
The `trycloudflare.com` quick-tunnel process is spawned by OmniRoute (parent `node.exe` PID 7780); killing it breaks OmniRoute's public URL. The btdat.io.vn tunnel runs as SEPARATE `cloudflared tunnel run <id>` processes (3 of them) — safe to `taskkill /F` + restart to apply `~/.cloudflared/config.yml` changes. No CF API token on this machine → new ingress hostnames need a manual CNAME on the Cloudflare dashboard: `CNAME <name> → <tunnel-id>.cfargotunnel.com` (proxy ON).

## Search Priority Preference
Order: 1) tavily_search (MCP) 2) web_search (DDG) 3) SerpAPI (curl) 4) Serper (curl).
Tavily keys rotateable via MCP servers (tavily/tavily-2/tavily-3 + 2 reserve in .env).
See `references/search-providers.md`.

## Location & Process

- **Install**: `npm i -g omniroute` (global, at `~/AppData/Roaming/npm/omniroute`)
- **Data dir**: `~/.omniroute/` — `.env`, `storage.sqlite`, logs, backups
- **Port**: 20128 (CRITICAL — never kill all node.exe, this port hosts RAG/other services too)
- **Dashboard**: `http://localhost:20128/dashboard` (requires login)
- **Version check**: `omniroute --version`

## Safe Restart (Background Mode for Hermes)

```bash
# Find PID
PID=$(netstat -ano | grep 20128 | grep LISTENING | awk '{print $NF}' | head -1)

# Kill ONLY that PID (NOT taskkill /f /im node.exe!)
/c/Windows/System32/taskkill.exe /F /PID $PID

# Start in foreground (use Hermes terminal background=true)
cd ~/.omniroute && omniroute serve --port 20128 --no-open
```

When running via Hermes terminal tool, always use `terminal(background=true, command="cd ~/.omniroute && omniroute serve --port 20128 --no-open")` — never use shell-level `&` or nohup. Verify with `netstat -ano | grep 20128 | grep LISTENING` after a 5-second sleep.

## Management API Access

Management endpoints (`/api/evals`, `/api/a2a/status`, `/api/settings`, `/api/mcp/`) require auth. Two approaches:

### A) Bypass requireLogin (safe for localhost)
```python
import sqlite3, os
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'requireLogin', 'false')")
db.commit()
```

### B) Create a Management API Key
Insert an API key into SQLite with SHA-256 hash:
```python
import sqlite3, os, hashlib, secrets
from datetime import datetime, timezone

db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
raw_key = 'sk-manage-' + secrets.token_hex(16)
key_hash = hashlib.sha256(raw_key.encode()).digest().hex()
now = datetime.now(timezone.utc).isoformat()
db.execute('''INSERT INTO api_keys (id, name, key, key_hash, key_prefix, scopes, created_at, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    ('mgmt-001', 'Management', raw_key, key_hash, raw_key[:16], '{"allow":["*"]}', now, 1))
db.commit()
print(f'Key: {raw_key}')
```
The key_hash must be SHA-256 hex digest (matching Node.js `crypto.createHash("sha256").digest("hex")`).

### Header format for API calls
```bash
curl -H "Authorization: Bearer <key>" http://localhost:20128/api/evals
```

Note: MCP endpoint `/api/mcp/stream` is LOCAL_ONLY tier. With `requireLogin=true`, it returns 401 unless a valid management API key is passed via `headers.Authorization` in the MCP client config.ace, key, value) VALUES ('settings', 'requireLogin', 'false')")
db.commit()
# Re-enable with 'true'
```

This allows local curl/browser access to management APIs. Re-enable after use.

## Settings Management

Read all runtime settings:
```bash
curl -s http://localhost:20128/api/settings
```

Set a setting via API:
```bash
curl -s -X POST http://localhost:20128/api/settings \
  -H "Content-Type: application/json" \
  -d '{"key": "settingKey", "value": "settingValue"}'
```

Set via SQLite directly:
```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'key', 'value')")
```

Common settings toggled this way: `mcpEnabled`, `a2aEnabled`, `requireLogin`, `mcpTransport`.

## Safe Restart

```bash
# Find PID
PID=$(netstat -ano | grep 20128 | grep LISTENING | awk '{print $NF}' | head -1)

# Kill ONLY that PID (NOT taskkill /f /im node.exe!)
/c/Windows/System32/taskkill.exe /F /PID $PID

# Start again in background
omniroute serve --port 20128 --no-open &
```

**CRITICAL**: NEVER run `taskkill /f /im node.exe` — this kills all Node.js processes including RAG server, bot server, and other critical services on port 20128. Always kill by specific PID.

## Auto-Routing with Free & Cmd Models (Zero-Config)

OmniRoute supports zero-config auto-routing via the `auto/` model prefix. This user **only uses free tier + Command Code (cmd) subscription** — no paid API keys. Auto-routing works with this setup.

### Available Variants

| Variant | Purpose | Free-friendly? |
|---------|---------|:---:|
| `auto/smart` | **Default.** Quality-first + 10% exploration for model discovery | ✅ |
| `auto/coding:free` | Coding tasks, free tier pool only | ✅ |
| `auto/best-free` | Best model from free pool across all categories | ✅ |
| `auto/cheap` | Cost-optimized (lowest cost first) | ✅ |
| `auto/offline` | Prefers providers with highest quota available (good for cmd monthly quota) | ✅ |
| `auto/coding` | Coding pool, balanced weights | ✅ |
| `auto/reasoning` | Thinking/reasoning models only | ✅ |
| `auto/vision` | Vision-capable models (⚠ may fail if no free vision models available) | ⚠️ |
| `auto/coding:fast` | Coding pool + low-latency weights | ✅ |
| `auto/coding:cheap` | Coding pool + cost-optimized | ✅ |
| `auto/coding:pro` | Coding pool + premium tier (ptional, may route to cmd models) | ℹ️ |

### Hermes Config Integration

Set in `~/AppData/Local/hermes/config.yaml`:

```yaml
model:
  default: auto/smart
  provider: omniroute
  fallbacks:
    - auto/coding:free
    - auto/cheap
    - auto/offline
    - oc/deepseek-v4-flash-free
    - cmd/deepseek/deepseek-v4-flash
```

Or via CLI:
```bash
hermes config set model.default auto/smart
hermes config set model.fallbacks '["auto/coding:free","auto/cheap","auto/offline","oc/deepseek-v4-flash-free","cmd/deepseek/deepseek-v4-flash"]'
```

### Current Best Free Model

As of v3.8.48, the auto-routing scoring engine consistently selects **`big-pickle`** (`oc/big-pickle`) as the best free model:
- **200K context** (vs 32K on older models)
- **Tool calling** ✅
- **Thinking/Reasoning** ✅ (effort tiers: none, low, medium, high, xhigh)
- **Provider**: OpenRouter (`oc/`) — $0 cost
- **Fallback chain**: works across auggie, duckduckgo, opencode providers

### Limitations

- **Vision**: No free vision-capable model currently available (`auto/vision` fails with 401/403 on all fallbacks)
- **Cmd quota**: Weekly limit (~$1 Go Plan). Hitting 429 means quota exhausted; auto-routing falls back to free pool automatically
- **Pool size**: Auto-routing is only as good as the connected providers — add more free providers to expand options

## 9-Factor Scoring Engine

Auto-routing uses a multi-factor scorer to rank models per request:

1. **Quality** — Arena ELO rankings (live from models.dev)
2. **Speed** — Latency measurements
3. **Cost** — Token pricing (free = highest score)
4. **Reliability** — Circuit breaker health
5. **Context window** — Size requirement matching
6. **Capability fitness** — Tool calling, vision, reasoning match
7. **Quota availability** — Remaining quota balance
8. **Category affinity** — Coding vs reasoning vs chat specialization
9. **Exploration** — Random discovery rate (10% on `auto/smart`)

## Compression Settings (via SQLite)

Compression runs transparently before requests hit upstream providers. Settings live in namespace='compression' in the key_value table.

For coding workflows, **Stacked (RTK → Caveman)** mode saves 78-95% eligible tokens.

### Key settings in `key_value` table

```sql
-- Always specify namespace='compression'! The table has a NOT NULL constraint.
INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('compression', 'key', 'value');
```

| Key | Recommended | Meaning |
|-----|-------------|---------|
| `defaultMode` | `"stacked"` | Default compression mode for all requests |
| `enabled` | `true` | Master toggle |
| `autoTriggerTokens` | `32000` | Only compress when context exceeds this. Lowered from 64K for tighter savings |
| `preserveSystemPrompt` | `true` | Never compress the system message |
| `engines` | `{...}` | Per-engine config blob. Namespace = `compression`. |

### Engine modes & tuning

Stacked pipeline is the most aggressive — applies RTK (terminal/tool output) then Caveman (prose) in sequence.

**Recommended engine config for free/cheap providers:**
```python
engines = {
    'session-dedup': {'enabled': True},   # Remove duplicate messages
    'rtk': {'enabled': True, 'level': 'full'},
    'headroom': {'enabled': True},        # Keep safety margin for context window
    'relevance': {'enabled': True},       # Prune low-relevance content
    'caveman': {'enabled': True, 'level': 'full'},
    'stacked': {'enabled': True, 'pipeline': ['rtk', 'caveman']},
    # Disabled: ccr, lite, aggressive, llmlingua, ultra
}
```

### Pitfalls

- **ALWAYS include namespace='compression'** in SQLite INSERT/UPDATE. Omitting it fails with `NOT NULL constraint failed: key_value.namespace`.
- Settings take effect at runtime — no restart needed for compression configs.
- Currently running Caveman full-level (mọi engine đều bật hết). Có thể tune xuống 'standard' nếu thấy response quality giảm.

| Engine | Key | Benefit |
|--------|-----|---------|
| `session-dedup` | `engines.session-dedup.enabled=true` | Removes duplicate messages within a session |
| `relevance` | `engines.relevance.enabled=true` | Strips low-relevance content based on current query |
| `headroom` | `engines.headroom.enabled=true` | Reserves safety margin below context limit |
| `ccr` | `engines.ccr.enabled=true` | Context Compression Ratio optimization |
| `lite` | `engines.lite.enabled=true` | Always-on formatting cleanup (safe) |

### Compression Modes Quick Reference

| Mode | Engine | Savings | Best for |
|------|--------|:-------:|----------|
| `off` | none | 0% | Exact preservation |
| `lite` | Caveman lite helpers | ~15% | Always-on safe cleanup |
| `standard` | Caveman | ~30% | NL prompt condensation |
| `aggressive` | Caveman + summaries | ~50% | Long chat sessions |
| `ultra` | Caveman + pruning | ~75% | Context-limit recovery |
| `rtk` | RTK engine | 60-90% | Terminal, build, git output |
| `stacked` | RTK → Caveman pipeline | 78-95% | **Default. Mixed tool logs + prose** |

## Reasoning Replay Cache

Thinking-mode models (DeepSeek R1, Claude thinking, Gemini thinking) require `reasoning_content` from prior turns or they return HTTP 400. OmniRoute caches and replays this automatically.

### Architecture

```
Turn N → Assistant generates reasoning_content
       → cached by tool_call.id in memory + SQLite
Turn N+1 → Client sends follow-up (usually strips reasoning)
       → OmniRoute restores from cache before forwarding
       → Upstream sees consistent history → no 400
```

### Config

Enable via **Settings → AI → Reasoning Replay Cache** or SQLite:
- Key: `reasoningCacheEnabled` → `true`
- The `x-omniroute-reasoning-replay` header confirms replay during request

### Impact

Essential for stable use of thinking models (DeepSeek R1, Claude with extended thinking, Gemini thinking). Without it, multi-turn conversations hit provider errors mid-stream.

## MCP Server (104 Tools)

OmniRoute exposes a built-in MCP server with 104 tools across routing, cache, compression, memory, skills, proxy, pool, and context sources.

### Key Tool Groups

| Group | Count | Tools |
|-------|:-----:|-------|
| Essential routing | 8 | `omniroute_get_health`, `omniroute_route_request`, `omniroute_list_combos`, `omniroute_switch_combo`, `omniroute_check_quota`, `omniroute_cost_report`, etc. |
| Advanced routing | 11 | `omniroute_simulate_route`, `omniroute_set_routing_strategy`, etc. |
| Search | — | `omniroute_web_search` (multi-backend) |
| Cache | 2 | Cache management |
| Memory | 3 | CRUD memory operations |
| Skills | 4+3 | Omni skills + GitHub skills |
| Pool | 6 | Pool management |
| Gamification | 8 | Gamification tools |
| Plugins | 8 | Plugin management |
| Obsidian | 22 | Obsidian vault integration |
| Notion | 6 | Notion integration |

### Start MCP Server

```bash
# Standalone
omniroute --mcp

# Via HTTP (auto-starts with --dev on port 20130)
omniroute --dev
```

### Transports

- `stdio` — IDE integrations (Claude Desktop, Cursor)
- `sse` — `POST/GET /api/mcp/sse` (browser/agent clients)
- `streamable-http` — `POST/GET/DELETE /api/mcp/stream` (multi-session)

### Cmd Provider Quota

Command Code (cmd/) models require a subscription (Go Plan $1 CLI-only, or Provider Plan $15 for HTTP API). Weekly quota applies:
- **429 "weekly usage limit"** = quota exhausted
- Reset time in error message: `resets at 2026-MM-DDTHH:MM:SS`
- Auto-routing falls back to free pool when cmd quota is out
- No special config needed — quota handling is automatic
| `cavemanConfig` | `{"enabled":true,"compressRoles":["user","assistant"],"minMessageLength":50}` | Caveman compression rules |
| `mcpAccessibility` | `{"enabled":true,"maxTextChars":50000,"collapseThreshold":30}` | MCP tool output handling |
| `stackedPipeline` | Not set (default: RTK → Caveman) | Override stacked engine order |
| `compression_combos` | Not set | Per-combo compression overrides |

### Available compression modes

| Mode | Engine path | Savings | Use case |
|------|-------------|---------|----------|
| `off` | none | 0% | Exact preservation |
| `lite` | Caveman lite helpers | ~15% | Always-on safe cleanup |
| `standard` | Caveman | ~30% | NL prompt condensation |
| `aggressive` | Caveman + summarizers | ~50% | Long chat sessions |
| `ultra` | Caveman + pruning | ~75% | Context-limit recovery |
| `rtk` | RTK | 60-90% | Terminal/build/test/output |
| `stacked` | Pipeline (RTK→Caveman) | 78-95% | Mixed tool logs + prose |

### Additional engine configs (all disabled by default, can be enabled)

| Engine | Key | Effect |
|--------|-----|--------|
| `session-dedup` | `engines.session-dedup.enabled=true` | Removes duplicate messages across turns |
| `relevance` | `engines.relevance.enabled=true` | Prunes content irrelevant to current query |
| `headroom` | `engines.headroom.enabled=true` | Reserves safety margin in context window |
| `ccr` | `engines.ccr.enabled=true` | Context Compression Ratio optimization |
| `lite` | `engines.lite.enabled=true` | Always-on pre-filter formatting cleanup |

**Recommendation for coding tasks**: enable `session-dedup` and `relevance` alongside stacked mode. Consider lowering `autoTriggerTokens` from 64K to 32K for more aggressive savings.

### Tuning via Python

```python
import sqlite3, json
db = sqlite3.connect("$HOME/.omniroute/storage.sqlite")

# Change auto-trigger threshold
db.execute("REPLACE INTO key_value(key, value) VALUES (?, ?)",
           ("autoTriggerTokens", json.dumps(32000)))

# Enable session-dedup
db.execute("REPLACE INTO key_value(key, value) VALUES (?, ?)",
           ("engines", json.dumps({"session-dedup":{"enabled":true},"rtk":{"enabled":true,"level":"full"},"caveman":{"enabled":true}})))
db.commit()
```

## Auto-Combo Routing (zero-config)

OmniRoute v3.8+ has a **9-factor scoring engine** that dynamically selects the best model per request based on: quality (Arena ELO), speed, cost, reliability (circuit breaker health), context window size, quota availability, and category fitness. Fallback is automatic — if the top model fails, the next best is tried transparently.

### Available auto/ variants

Use these as model IDs in any OpenAI-compatible client:

| Variant | Behavior | Use case |
|---------|----------|----------|
| `auto/smart` | Quality-first + 10% exploration | Daily driver |
| `auto/coding` | Quality-first weights, code generation | Programming tasks |
| `auto/reasoning` | Reasoning/thinking models only | Complex analysis |
| `auto/vision` | Vision-capable models only | Image tasks |
| `auto/fast` | Low-latency weighted selection | Speed-critical |
| `auto/cheap` | Cost-optimized (cheapest first) | Budget mode |
| `auto/offline` | Highest quota availability | When provider limits matter |
| `auto/best-free` | Free models only | Zero-cost operation |
| `auto/multimodal` | Multimodal-capable models | Mixed media |

### Category × Tier composition

Compose freely: `auto/<category>:<tier>`

**Categories** (filter candidate pool by capability): `coding`, `reasoning`, `vision`, `chat`, `multimodal`

**Tiers** (scoring weights / pool filter): `fast`, `cheap` (alias `floor`), `reliable`, `free`, `pro`

Examples:
- `auto/coding:free` — coding pool, free tier only
- `auto/coding:cheap` — coding pool, cost-optimized
- `auto/reasoning:pro` — reasoning models, premium tier
- `auto/vision` — vision-capable, balanced weights

### How auto-routing works with free + cmd models

This setup (no paid API keys, only Command Code subscription + OpenRouter free tier) works well:

- **Free tier**: `auto/coding:free`, `auto/best-free`, `auto/cheap` — routes to models from OpenRouter free tier (`oc/*-free`) and command-code free models
- **Cmd subscription**: `auto/coding`, `auto/reasoning`, `auto/smart` — includes `cmd/` models (DeepSeek V4, Claude Opus 4-7/5, Gemini 3.x, GPT 5.x, Qwen, MiniMax, etc.) via Command Code API subscription
- **Fallback chain**: auto-routing auto-fails over — if free models are rate-limited, falls to next best in pool

**Available free models (oc/*-free)**:
`oc/deepseek-v4-flash-free`, `oc/minimax-m2.5-free`, `oc/minimax-m3-free`, `oc/ling-2.6-1t-free`, `oc/nemotron-3-super-free`, `oc/qwen3.6-plus-free`, `oc/trinity-large-preview-free`

**Available cmd/ models** (Command Code):
Claude Opus 4-7/4-8/5, Sonnet 4-6/5, Haiku 4-5, DeepSeek V4 Pro/Flash, Gemini 3.x, GPT 5.x (codex/5.4/5.4-mini/5.5/5.6), Qwen 3.6/3.7 (Max/Plus), MiniMax M2.5/M2.7/M3, Kimi K2.5, Ling 3.0, Muse Spark 1.1

### Setting auto-routing in Hermes config

```yaml
model:
  default: auto/smart     # or auto/coding, auto/coding:free, etc.
  provider: omniroute
```

Or per-request via the model parameter in tools.

### Quota routing (`auto/offline`)

`auto/offline` favors providers with the most remaining quota — ideal for Command Code's monthly subscription model where quota refreshes monthly. The scoring engine checks each provider's remaining quota and picks the one with the most headroom.

## Reasoning Replay Cache

**Purpose**: Prevents HTTP 400 errors from thinking-mode providers (DeepSeek, etc.) that require `reasoning_content` to be passed back on follow-up turns.

**How it works**:
1. On each assistant response, OmniRoute captures `reasoning_content` (keyed by `tool_call.id`)
2. Caches it in memory + SQLite (survives restarts)
3. On the next turn, if the client stripped reasoning_content from the history, OmniRoute replays it from cache before forwarding to upstream

**Enable**: Settings → AI → Reasoning Replay Cache toggle, or via feature flag.

**Without this**: thinking models (DeepSeek R1/V4, Claude thinking, Gemini thinking) fail on multi-turn conversations with "reasoning_content must be passed back" errors.

## Memory System (3-tier)

OmniRoute has persistent conversational memory separate from Hermes memory.

**Tiers** (auto-degrade):
- **Tier 0**: SQLite FTS5 full-text search (always available)
- **Tier 1**: sqlite-vec semantic search (int8 quantization, fallback)
- **Tier 2**: Qdrant vector DB (production, configured separately)

## MCP Server Integration

OmniRoute ships a built-in MCP server with **99 tools**. Currently configured for Hermes via `~/.hermes/config.yaml`. See the reference file `references/hermes-mcp-integration.md` for step-by-step setup, config examples, and the full tool list.

### Hermes Integration

```bash
# Add OmniRoute MCP server to Hermes
echo "n" | hermes mcp add omniroute --url "http://localhost:20128/api/mcp/stream"

# Config written to ~/.hermes/config.yaml:
# mcp_servers:
#   omniroute:
#     url: "http://localhost:20128/api/mcp/stream"
#     enabled: true
#     timeout: 60
#     tools:
#       include:
#         - omniroute_get_health
#         - omniroute_route_request
#         - omniroute_list_models_catalog
#         - omniroute_web_search
#         - omniroute_check_quota
#         - omniroute_cost_report
#         - omniroute_best_combo_for_task
#         - omniroute_explain_route
#         - omniroute_simulate_route
#         - omniroute_pick_fastest_model
#         - omniroute_list_providers
#         - omniroute_list_sessions
#         - omniroute_set_routing_strategy
#         - omniroute_set_resilience_profile
#         - omniroute_get_provider_metrics
#         - omniroute_list_combos
#         - omniroute_get_combo_metrics
```

### MCP Transport

MCP defaults to `stdio`. Change to `streamable-http` for HTTP access via DB:

```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpTransport', 'streamable-http')")
```

After changing transport, restart OmniRoute:
- Streamable HTTP: `POST /api/mcp/stream` (requires `mcp-session-id` header)
- SSE: `GET /api/mcp/sse` (requires transport set to `sse`)

## Evals Framework

### Search API Keys (Web Search Providers)

OmniRoute's search gateway supports multiple backends. Add API keys to `~/.omniroute/.env`:

#### Serper (recommended — 2500 free queries/month, $0.004/query after)
Best balance of quality vs free tier. Google search with position ranking.
```env
SERPER_API_KEY=<your_key>
```
Test: `curl -s -X POST https://google.serper.dev/search -H "X-API-KEY: $KEY" -H "Content-Type: application/json" -d '{"q":"<query>","num":5}'`

#### SerpAPI (100 free queries/month, $0.01/query after)
Better for queries needing Knowledge Graph, Related Questions, or Shopping results.
```env
SERPAPI_API_KEY=<your_key>
```
Test: `curl -s "https://serpapi.com/search?q=<query>&api_key=$KEY&num=5"`

#### Tavily (1000 free queries/month)
Configured as a separate MCP server (see Tavily MCP section). Best for search + content extraction + summarization.

### Multi-Agent Workflow with delegate_task

Use Hermes `delegate_task(goal=..., context=...)` to spawn independent sub-agents. Each sub-agent automatically uses `auto/smart` routing to pick the best model for its task.

**Pattern:**
```python
# Dispatch multiple tasks in parallel — all run concurrently
delegate_task(goal="Review code", context="...", role="leaf")
delegate_task(goal="Research topic", context="...", role="leaf")
```

Both run in the background. Results arrive as separate messages when each finishes.

**When to use:** multiple independent tasks (code review + research + testing), tasks needing different model capabilities, time-sensitive parallel work.

**Pitfalls:**
- Sub-agents have NO memory of your conversation — pass all context explicitly
- Sub-agents cannot use `clarify` or `delegate_task` themselves (leaf role)
- Summaries are self-reported — verify file writes, HTTP calls, and external side effects
- Live transcripts available at `~/AppData/Local/hermes/cache/delegation/live/<delegation_id>/task-0.log`

## Evals Framework

Built-in benchmarking for routing configs, providers, and models.

**Dashboard**: Usage → Evals

**7 built-in suites**: `golden-set` (10 baseline cases), `coding-proficiency` (5), `reasoning-logic` (5), `multilingual` (5), `safety-guardrails` (6), `instruction-following` (5), `codex-comparison` (8)

**Custom suites**: stored in SQLite, editable via API/UI

**Mechanism**: dispatches real calls to `/v1/chat/completions`, captures latency + output, aggregates scorecards

**Use case**: run evals to determine which provider/model combination performs best for coding vs reasoning vs translation tasks.

### Running Evals via API

```python
# Critical: use 'target' object, NOT just 'model' field!
POST /api/evals
Body: {
    "suiteId": "coding-proficiency",
    "target": {
        "key": "model:auto/smart",
        "type": "model",
        "id": "auto/smart",
        "label": "Model: auto/smart"
    }
}
```

Without `target`, evals use suite-default models (gpt-4o, claude-sonnet) which fail if no credentials exist for those providers. The `"target"` object forces all cases through one model.

### Actual benchmark results with auto/smart (big-pickle free) — 89% overall

| Suite | Pass Rate |
|-------|-----------|
| Golden Set | 10/10 = 100% |
| Reasoning & Logic | 5/5 = 100% |
| Coding Proficiency | 4/5 = 80% |
| Multilingual | 4/5 = 80% |
| Instruction Following | 4/5 = 80% |
| Safety Guardrails | 5/6 = 83% |
| **Total** | **32/36 = 89%** |

All tests run with auto/smart routing on OpenRouter free tier (big-pickle model, 200K context).

## A2A Protocol (Agent-to-Agent)

OmniRoute implements Google's A2A v0.3 protocol.

**Endpoint**: `POST /a2a` (JSON-RPC 2.0), disabled by default.

**Enable**: Dashboard → Endpoints → A2A toggle, OR via DB:
```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'a2aEnabled', 'true')")
# Requires restart
```

**Methods**: `message/send` (synchronous), `message/task/send` (async with task tracking), `message/task/get` (poll status).

**Agent Card**: `GET /.well-known/agent.json` (no auth required).

**3 built-in skills**: `smart-routing`, `quota-management`, `provider-discovery`.

### Multi-Agent Workflow via Hermes

Use Hermes' built-in `delegate_task()` tool for parallel sub-agent orchestration. Each sub-agent independently routes through OmniRoute's `auto/smart`:

```
Hermes (orchestrator)
  → delegate_task(goal="code review task A")   # auto/smart routing  
  → delegate_task(goal="research task B")       # auto/smart routing
  → delegate_task(goal="testing task C")        # auto/smart routing
```

A2A is useful when an external agent (not Hermes) needs to dispatch routing requests through OmniRoute. For Hermes-native multi-agent, `delegate_task()` is simpler and more capable.

## AgentBridge (MITM Proxy)

Intercepts HTTPS traffic from IDE AI agents (Copilot, Cursor, Claude Code, Codex CLI, Zed, Kiro, Antigravity, OpenCode, Trae) and reroutes through OmniRoute without agent config changes.

**Dashboard**: Tools → Agent Bridge

**Capabilities**:
- Reroute any IDE agent to any provider transparently
- Model mapping: `deepseek-v4` → `claude-sonnet-4.7` at handler level
- Apply combo routing, circuit breakers, fallbacks, cost tracking to IDE traffic
- Traffic Inspector shows all intercepted requests in real-time

## Feature Flags (38 flags, 6 categories)

Runtime toggles changed via dashboard or API — no redeploy needed.

**Resolution order** (highest wins): DB override → env var → definition default.

**Key categories**:
- AI: model selection, auto-combo presets, reasoning replay, skill/memory
- Routing: model aliases, sticky routing, fallback delay
- Resilience: circuit breaker, rate limit persistence, Context Relay handoff

## Managing Providers (Connected)

Check connected providers (and their model pool) via API (requires manage-scope API key):

```bash
curl -s http://localhost:20128/api/providers \
  -H "Authorization: Bearer $OMNIROUTE_API_KEY"
```

List available auto/ routing models:

```bash
curl -s http://localhost:20128/v1/models |
  python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data'] if m['id'].startswith('auto/')]"
```

Provider prefixes:
- `oc/` — OpenRouter (free tier)
- `cmd/` — Command Code subscription
- `command-code/` — Command Code (alias)
- `ddgw/` — DuckDuckGo Web
- `aug/` — Auggie
- `tllm/` — Together/Local LLM
- `pepper/` — Pepper
- `mcode/` — Mimo Code

## Management API Key (via SQLite)

Create a management API key for programmatic access to management endpoints:

```python
import hashlib, secrets
from datetime import datetime, timezone

raw_key = 'sk-manage-' + secrets.token_hex(16)
key_hash = hashlib.sha256(raw_key.encode()).digest().hex()
now = datetime.now(timezone.utc).isoformat()

db.execute('''INSERT INTO api_keys (id, name, key, key_hash, key_prefix, scopes, created_at, is_active) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    ('mgmt-001', 'Management', raw_key, key_hash, raw_key[:16], '{"allow":["*"]}', now, 1))
```

The raw key is stored in `key` column, SHA-256 hex digest in `key_hash`. Validation queries `WHERE key = ? OR key_hash = ?`.

### Auth Bypass (Development Only)

For testing, temporarily disable login requirement:
```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'requireLogin', 'false')")
# Re-enable after testing:
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'requireLogin', 'true')")
```

## Reference Files

- `references/omniroute-feature-analysis.md` — Full feature inventory, auto-routing variants table, free model pool, provider prefixes, MCP tool list, API endpoints, key hash details

## Perf Budgets (SLO targets)

OmniRoute targets: Availability 99.9% (30d), p95 latency ≤1.5s, p99 ≤4.0s for `/v1/*` endpoints. Full budgets in reference docs at `docs/PERF_BUDGETS.md`.

## Reference Files

This skill ships with reference files under `references/`:

- [`references/compression-config.md`](file://references/compression-config.md) — Full compression Python config with namespace-qualified SQLite commands, engine descriptions, tuning guide
- [`references/auto-routing-free-cmd-analysis.md`](file://references/auto-routing-free-cmd-analysis.md) — Auto-routing analysis for free + Command Code subscription models
- [`references/compression-guide.md`](file://references/compression-guide.md) — OmniRoute compression pipeline architecture extracted from official docs
- [`references/db-auth-mcp-a2a-reference.md`](file://references/db-auth-mcp-a2a-reference.md) — DB schema (namespace in key_value), auth bypass via requireLogin toggle, MCP transport config (stdio/sse/streamable-http), A2A protocol enabling, auto-routing live test results, key DB table structures, auth tiers
- [`references/auto-combo-models-and-tools.md`](file://references/auto-combo-models-and-tools.md) — Full auto-combo model ID catalog (36+ variants), 99 MCP tools list with descriptions, evals results (89% pass rate), compression engines reference, management API key creation

## Pitfalls

- NEVER `taskkill /f /im node.exe` — kills all Node on the box
- Auto-routing `auto/*` requires at least one connected provider with relevant models — check `/v1/models` to see what's available
- Memory is OFF by default since v3.8.30 — opt in explicitly or add `x-omniroute-no-memory: true` to opt out per-request
- A2A is disabled by default — must toggle in dashboard
- Compression `autoTriggerTokens` should be ~25% of context window (64K for 256K context) — too low triggers compression on every request unnecessarily
- Reasoning Replay is essential for multi-turn thinking model usage — without it, strict providers return HTTP 400
- `auto/offline` is not magic — it only routes to providers that are already connected and have quota
