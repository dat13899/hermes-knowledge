# Hermes MCP Integration with OmniRoute

## Architecture

```
Hermes Agent (MCP client)
  → streamable-http → http://localhost:20128/api/mcp/stream
  → OmniRoute MCP Server (99 tools)
```

## MCP Transport Configuration

OmniRoute MCP supports 3 transports. For Hermes, **streamable-http** is best:

```bash
# DB: Set transport to streamable-http
python -c "
import sqlite3
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
db.execute(\"INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpTransport', 'streamable-http')\")
db.execute(\"INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpEnabled', 'true')\")
db.commit()
"
```

Restart OmniRoute after change.

## Adding to Hermes

```bash
# Step 1: Add server (requireLogin must be false for this step)
echo "n" | hermes mcp add omniroute --url "http://localhost:20128/api/mcp/stream"
# Responds with: ✓ Connected! Found 99 tool(s)

# Step 2: Verify
hermes mcp list           # Should show 18 selected tools
hermes mcp test omniroute # Should show ✓ Connected

# Step 3: Restart Hermes session for tools to appear
```

## Complete ~/.hermes/config.yaml Entry

```yaml
mcp_servers:
  omniroute:
    url: "http://localhost:20128/api/mcp/stream"
    enabled: true
    timeout: 60
    tools:
      include:
        - omniroute_get_health
        - omniroute_route_request
        - omniroute_list_models_catalog
        - omniroute_web_search
        - omniroute_check_quota
        - omniroute_cost_report
        - omniroute_list_combos
        - omniroute_best_combo_for_task
        - omniroute_explain_route
        - omniroute_simulate_route
        - omniroute_pick_fastest_model
        - omniroute_list_providers
        - omniroute_list_connections
        - omniroute_set_routing_strategy
        - omniroute_set_resilience_profile
        - omniroute_get_provider_metrics
        - omniroute_list_sessions
        - omniroute_get_combo_metrics
```

## Auth Considerations

- With `requireLogin=false`: MCP works without headers (safe because LOCAL_ONLY tier)
- With `requireLogin=true`: MCP returns 401. Needs management API key in headers.
- Management API key insertion:
  ```python
  import sqlite3, hashlib, secrets
  db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
  raw_key = 'sk-manage-' + secrets.token_hex(16)
  key_hash = hashlib.sha256(raw_key.encode()).digest().hex()
  db.execute('INSERT INTO api_keys (id, name, key, key_hash, scopes, created_at, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)',
             ('mgmt-001', 'Management', raw_key, key_hash, '{"allow":["*"]}', datetime.utcnow().isoformat(), 1))
  db.commit()
  ```

## MCP Tool List (18 selected from 99)

| Hermes tool name | Purpose |
|-----------------|---------|
| `mcp__omniroute_get_health` | Health status |
| `mcp__omniroute_route_request` | Send LLM request through routing |
| `mcp__omniroute_list_models_catalog` | Browse all available models |
| `mcp__omniroute_web_search` | Web search via gateway |
| `mcp__omniroute_check_quota` | Provider quota remaining |
| `mcp__omniroute_cost_report` | Cost/spend report |
| `mcp__omniroute_list_combos` | List routing combos |
| `mcp__omniroute_best_combo_for_task` | Auto-recommend combo |
| `mcp__omniroute_explain_route` | Debug routing decisions |
| `mcp__omniroute_simulate_route` | Dry-run routing |
| `mcp__omniroute_pick_fastest_model` | Low-latency selection |
| `mcp__omniroute_set_routing_strategy` | Change strategy at runtime |
| `mcp__omniroute_set_resilience_profile` | Circuit breaker config |
| `mcp__omniroute_get_provider_metrics` | Provider perf data |
| `mcp__omniroute_list_sessions` | Active sessions |
| `mcp__omniroute_get_combo_metrics` | Combo performance metrics |
| `mcp__omniroute_list_providers` | All connected providers |
| `mcp__omniroute_list_connections` | Provider connections |

## Notes

- MCP tools appear with `mcp__` prefix only after Hermes session restart
- On Telegram, MCP tools may not appear in agent tool context (CLI-only limitation currently)
- `hermes mcp add` does NOT persist to config.yaml automatically — always verify with `hermes mcp list` and manually write to `~/.hermes/config.yaml` if needed
- For MCP config via `hermes config set`: scalar fields only (url, enabled, timeout). List fields (tools.include) require direct YAML edit
