# MCP Server Integration (OmniRoute → Hermes)

## MCP Endpoint

OmniRoute exposes 104 MCP tools. Transport options:

| Transport | URL | When to Use |
|-----------|-----|-------------|
| `stdio` | N/A (CLI) | IDE integrations |
| `sse` | `/api/mcp/sse` | Browser/agent clients |
| `streamable-http` | `/api/mcp/stream` | Multi-session HTTP clients |

Enable via DB:
```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpEnabled', 'true')")
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpTransport', 'streamable-http')")
```

## Connecting from Hermes

### Via CLI (per-session, not persistent)
```bash
hermes mcp add omniroute --url "http://localhost:20128/api/mcp/stream"
# Answer "n" to auth prompt
```

### Via Config (persistent)
Add to `~/.hermes/config.yaml` (user override) or `~/AppData/Local/hermes/config.yaml` (main):

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
        - omniroute_set_routing_strategy
        - omniroute_set_resilience_profile
        - omniroute_get_provider_metrics
        - omniroute_list_sessions
```

### Recommended Tools (18 core tools)
- **Health**: omniroute_get_health
- **Routing**: omniroute_route_request, omniroute_simulate_route, omniroute_explain_route, omniroute_best_combo_for_task, omniroute_pick_fastest_model, omniroute_set_routing_strategy
- **Search**: omniroute_web_search
- **Models**: omniroute_list_models_catalog, omniroute_list_providers, omniroute_list_connections
- **Quota/Cost**: omniroute_check_quota, omniroute_cost_report, omniroute_set_budget_guard
- **Combos**: omniroute_list_combos, omniroute_get_combo_metrics, omniroute_switch_combo
- **Resilience**: omniroute_set_resilience_profile
- **Sessions**: omniroute_list_sessions

### Auth Note
MCP endpoint is LOCAL_ONLY tier (localhost only). When `requireLogin=true`, MCP returns 401. Either:
- Set `requireLogin=false` (safe for localhost)
- Or pass a valid management API key via `headers.Authorization: Bearer <key>`

### Known Limitation
on Telegram, `mcp__*` tools may not appear in the agent's tool list. Use terminal to call them directly via curl, or use OmniRoute REST API as equivalent.
