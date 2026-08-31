# OmniRoute SQLite Operations Reference

## Schema

All configuration is stored in `~/.omniroute/storage.sqlite` with namespace-based key-value table:

```sql
CREATE TABLE key_value (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (namespace, key)
);
```

Other tables: `provider_connections`, `provider_nodes`, `combos`, `api_keys`, `routing_cache`, `memory_entries`.

## Common Namespaces

| Namespace | Purpose | Examples |
|-----------|---------|---------|
| `compression` | Prompt compression settings | autoTriggerTokens, engines, defaultMode, enabled, cavemanConfig |
| `settings` | Runtime application settings | requireLogin, mcpEnabled, a2aEnabled, mcpTransport |
| `lkgp` | Auto-routing LKGP provider selections | auto/reasoning:combo-xyz mappings |
| `databaseSettings` | Internal DB configuration | semanticCacheEnabled, promptCacheStrategy |

## Auth & Access

### Disable login requirement (local dev)

```python
import sqlite3
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'requireLogin', 'false')")
db.commit()
# Re-enable: set to 'true'
```

Management endpoints unlocked: `/api/evals`, `/api/a2a/status`, `/api/settings`, `/api/mcp/*`

## Compression Operations

### Read current settings

```python
rows = db.execute('SELECT key, value FROM key_value WHERE namespace = "compression"').fetchall()
```

### Change auto-trigger threshold

```python
db.execute("UPDATE key_value SET value = ? WHERE namespace = 'compression' AND key = 'autoTriggerTokens'", ('32000',))
```

### Enable/disable engines

```python
import json
engines = {
    'session-dedup': {'enabled': True},  # Deduplicate messages
    'relevance': {'enabled': True},      # Prune irrelevant content
    'headroom': {'enabled': True},       # Keep safety margin
    'rtk': {'enabled': True, 'level': 'full'},
    'caveman': {'enabled': True, 'level': 'full'},
    'stacked': {'enabled': True, 'pipeline': ['rtk', 'caveman']},
    'ccr': {'enabled': False},
    'lite': {'enabled': False},
    'aggressive': {'enabled': False},
    'ultra': {'enabled': False},
    'llmlingua': {'enabled': False},
}
db.execute("UPDATE key_value SET value = ? WHERE namespace = 'compression' AND key = 'engines'", (json.dumps(engines),))
db.commit()
```

## Runtime Settings Operations

### Toggle features via DB

```python
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpEnabled', 'true')")
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'a2aEnabled', 'true')")
db.execute("INSERT OR REPLACE INTO key_value (namespace, key, value) VALUES ('settings', 'mcpTransport', 'streamable-http')")
db.commit()
```

### Read all settings via API

```bash
curl -s http://localhost:20128/api/settings | python -c "import sys,json; d=json.load(sys.stdin); [print(f'{k} = {v}') for k,v in d.items()]"
```

## Evals Operations

### List available suites

```python
import json, urllib.request
resp = urllib.request.urlopen('http://localhost:20128/api/evals').read()
data = json.loads(resp)
for s in data['suites']:
    print(f"{s['id']}: {s['name']} ({s.get('caseCount')} cases)")
```

Available suites: `golden-set` (10), `coding-proficiency` (5), `reasoning-logic` (5), `multilingual` (5), `instruction-following` (5), `safety-guardrails` (6), `codex-comparison` (8).

### Run a suite against auto/smart

```bash
curl -s -X POST http://localhost:20128/api/evals \
  -H "Content-Type: application/json" \
  -d '{
    "suiteId": "golden-set",
    "target": {
      "key": "model:auto/smart",
      "type": "model",
      "id": "auto/smart",
      "label": "Model: auto/smart"
    }
  }'
```

The `target` field overrides per-case models (gpt-4o, claude-sonnet, gemini) with a single model.

### Parse results

```python
for run in data.get('runs', []):
    s = run.get('summary', {})
    print(f"Passed: {s['passed']}/{s['total']} ({s['passRate']}%)")
    for r in run.get('results', []):
        status = 'PASS' if r.get('passed') else 'FAIL'
        print(f"  {status} {r['caseName']} ({r.get('durationMs')}ms)")
```

### Known benchmark: auto/smart (big-pickle free) — 2026-07-28

| Suite | Rate |
|-------|------|
| Golden Set | 10/10 = 100% |
| Reasoning & Logic | 5/5 = 100% |
| Coding Proficiency | 4/5 = 80% |
| Multilingual | 4/5 = 80% |
| Instruction Following | 4/5 = 80% |
| Safety Guardrails | 5/6 = 83% |
| **Total** | **32/36 = 89%** |

## API Key Management (DB-level)

The `api_keys` table schema supports full management. Direct DB insertion:
```python
import hashlib, secrets
from datetime import datetime, timezone
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
raw_key = 'sk-manage-' + secrets.token_hex(16)
# Note: key_hash format may not be SHA256 alone — OmniRoute validates it in auth middleware.
db.execute('''INSERT INTO api_keys 
    (id, name, key, key_hash, scopes, created_at, is_active) 
    VALUES (?, ?, ?, ?, ?, ?, ?)''',
    (id, name, raw_key, hashlib.sha256(raw_key.encode()).hexdigest(),
     json.dumps({"allow": ["*"]}),
     datetime.now(timezone.utc).isoformat(), 1))
db.commit()
```

## Restart Required After Changes

Settings changed via DB (`mcpEnabled`, `a2aEnabled`, `mcpTransport`) require a full process restart:
```bash
PID=$(netstat -ano | grep 20128 | grep LISTENING | awk '{print $NF}' | head -1)
/c/Windows/System32/taskkill.exe /F /PID $PID
# Then restart via Hermes terminal(background=true, command="cd ~/.omniroute && omniroute serve --port 20128 --no-open")
```
Settings via runtime API (`POST /api/settings`) and most compression settings take effect immediately.
