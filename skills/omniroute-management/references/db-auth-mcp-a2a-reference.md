# DB Schema, Auth Bypass, MCP & A2A Reference

Discovered during 2026-07-28 research session on v3.8.48.

## 1. Key-Value Table Namespaces

The `key_value` table has `PRIMARY KEY (namespace, key)` — namespace is MANDATORY.

| Namespace | Typical Keys | Purpose |
|-----------|-------------|---------|
| `compression` | defaultMode, enabled, autoTriggerTokens, engines, cavemanConfig, cacheMinutes, preserveSystemPrompt | Compression settings |
| `settings` | requireLogin, mcpEnabled, a2aEnabled, mcpTransport, password, hasPassword, debugMode, hidePaidModels, proxyEnabled, tailscaleEnabled | Runtime settings (mirrors `/api/settings` GET) |
| `databaseSettings` | detailedLogsEnabled, callLogPipelineEnabled, maxDetailSizeKb, semanticCacheEnabled, semanticCacheMaxSize | DB-level behavior |
| `lkgp` | auto/reasoning:* | LKGP routing state per model key |

### Management Access via requireLogin toggle

When locked out of dashboard, disable auth directly in DB:

```python
import sqlite3
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'requireLogin', 'false')")
db.commit()
# Now `/api/settings`, `/api/evals`, `/api/a2a/*`, etc. are accessible without Bearer token
```

**Re-enable afterwards:** set `'requireLogin', 'true'` the same way.

**Password storage:** bcrypt hash `$2b$12$...` stored as `settings.password`. No plaintext recovery possible.

## 2. Management API Endpoints (requireLogin=false required)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/settings` | GET | List all runtime settings |
| `/api/settings` | POST | Set a setting (key/value body) |
| `/api/evals` | GET | List eval suites (built-in + custom) |
| `/api/evals/run` | POST | Run a suite against a model |
| `/api/a2a/status` | GET | Check if A2A is enabled |
| `/api/settings/reasoning-routing-rules` | GET/POST | Manage reasoning routing rules |
| `/api/keys` | POST | Create API keys |

Note: API key creation via `/api/keys` requires management auth. Direct DB insertion of api_keys fails because the `key_hash` mechanism (SHA-256 hashing with unknown salt/stretching) isn't trivial.

## 3. MCP Server Configuration

### MCP Transport Types

| Transport | Endpoint | When to use |
|-----------|----------|-------------|
| `stdio` | N/A (stdin/stdout) | IDE integrations (Claude Desktop, Cursor, Cline) |
| `sse` | `GET /api/mcp/sse` | Browser/agent clients needing event stream |
| `streamable-http` | `POST /api/mcp/stream` | Multi-session HTTP clients (`Mcp-Session-Id` header) |

### Enable MCP

```python
# Enable MCP (requires restart)
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpEnabled', 'true')")

# Switch transport from default (stdio) to streamable-http
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpTransport', 'streamable-http')")
db.commit()
# Then restart OmniRoute
```

### Access streamable-http MCP

```bash
# Session init (returns Mcp-Session-Id header)
curl -s -X POST http://localhost:20128/api/mcp/stream \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'

# List tools (104 total)
curl -s -X POST http://localhost:20128/api/mcp/stream \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list"}'
```

### Available MCP Tool Categories

| Category | Count | Examples |
|----------|-------|---------|
| Essential | 8 | omniroute_get_health, omniroute_route_request, omniroute_list_combos, omniroute_switch_combo, omniroute_check_quota, omniroute_cost_report, omniroute_list_models_catalog |
| Advanced | 11 | omniroute_simulate_route, omniroute_set_routing_strategy |
| Memory | 3 | memory CRUD |
| Skills | 4 | Omni skills injection |
| Cache | 2 | Cache operations |
| Pool | 6 | Provider pool management |
| Gamification | 8 | |
| Plugins | 8 | |
| Notion | 6 | |
| Obsidian | 22 | |
| RTK compression | 2 | |

## 4. A2A Agent Protocol

### Enable A2A

```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'a2aEnabled', 'true')")
db.commit()
# Then restart OmniRoute
```

### Agent Card

Available at `http://localhost:20128/.well-known/agent.json` (no auth needed):

```json
{
  "name": "OmniRoute AI Gateway",
  "version": "1.8.1",
  "skills": [
    { "id": "smart-routing", "name": "Smart Request Routing" },
    { "id": "quota-management", "name": "Quota & Cost Management" },
    { "id": "provider-discovery", "name": "Provider Discovery" }
  ]
}
```

### Test A2A

```bash
curl -s -X POST http://localhost:20128/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "skill": "smart-routing",
      "messages": [{"role": "user", "content": "Find best model for coding"}]
    }
  }'
```

Note: A2A endpoints **do not accept standalone management keys** at present (`AUTH_001`). When `requireLogin=false`, they work without auth headers.

## 5. Auto-Routing Test Results (2026-07-28)

When only free (`oc/*`) and cmd (`cmd/*`) models are connected:

| Auto Variant | Selected Model | Provider | Latency | Notes |
|-------------|---------------|----------|---------|-------|
| `auto/smart` | oc/big-pickle | OpenRouter | 8-9ms | Best free model across all categories |
| `auto/coding` | oc/big-pickle | OpenRouter | 9ms | Same — big-pickle tops the free pool |
| `auto/reasoning` | oc/big-pickle | OpenRouter | 8ms | Has thinking/reasoning capabilities |
| `auto/cheap` | oc/big-pickle | OpenRouter | 8ms | Only free choice available |
| `auto/offline` | oc/big-pickle | OpenRouter | 2ms | Lowest latency (quota available) |
| `auto/best-free` | oc/big-pickle | OpenRouter | 8ms | Free pool winner |
| `auto/vision` | — | — | Timeout | No free vision model available |
| `auto/multimodal` | — | — | 401 | All vision-capable options failed (401/429) |

**big-pickle specs:** 200K context, tool_calling=true, thinking=true, reasoning=true, effort_tiers=[none,low,medium,high,xhigh], owned_by=opencode, cost=$0, 0 token cost.

**Cmd models** were unreachable due to weekly quota exhaustion (429 "weekly usage limit", resets 31 Jul). When quota resets, auto-routing will include them in the pool.

## 6. DB Tables Overview

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `key_value` | Generic key-value with namespace | namespace, key, value |
| `api_keys` | Management API keys | id, key, key_hash (SHA-256), scopes, is_active, usage quotas |
| `combos` | Combo routing configurations | id, name, data (JSON), system_message, tool_filter_regex |
| `provider_connections` | Connected providers | id, provider, access_token, api_key, is_active, health status, rate limits |
| `provider_nodes` | Provider API endpoints | id, type, prefix, base_url, chat_path, models_path |

## 7. Auth Tiers (Route Guards)

From `src/server/authz/routeGuard.ts`:

1. **LOCAL_ONLY** — loopback only (localhost/127.0.0.1/::1). `/api/mcp/*`, `/api/cli-tools/runtime/*`. Blocked unconditionally from non-local unless manage-scope bypass enabled.
2. **ALWAYS_PROTECTED** — auth always required even when requireLogin=false. Destructive operations.
3. **MANAGEMENT** (default) — auth required, bypassed when requireLogin=false.
