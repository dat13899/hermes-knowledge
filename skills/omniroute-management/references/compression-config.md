# Prompt Compression — Full Configuration Reference

Applied for user: **Đạt**, session: 2026-07-28 (updated from 2026-07-26).

## ⚠️ CRITICAL: Namespace qualifier required

The `key_value` table has a **namespace** column (`PRIMARY KEY (namespace, key)`). All compression settings live under `namespace='compression'`. Writing without the namespace will raise `NOT NULL constraint failed: key_value.namespace`.

```python
# WRONG (fails):
db.execute("UPDATE key_value SET value = ? WHERE key = ?", ('"stacked"', 'defaultMode'))
# RIGHT:
db.execute("UPDATE key_value SET value = ? WHERE namespace = 'compression' AND key = ?", ('"stacked"', 'defaultMode'))
```

## Current applied configuration (2026-07-28)

### Auto-trigger lowered to 32K (was 64K)
```python
import sqlite3, json
db = sqlite3.connect(os.path.expanduser('~/.omniroute/storage.sqlite'))
NS = 'compression'

# Enable stacked mode
db.execute(f"UPDATE key_value SET value = ? WHERE namespace = '{NS}' AND key = ?", ('"stacked"', 'defaultMode'))
db.execute(f"UPDATE key_value SET value = ? WHERE namespace = '{NS}' AND key = ?", ('true', 'enabled'))

# Lower auto-trigger from 64K → 32K (faster compression activation)
db.execute(f"UPDATE key_value SET value = ? WHERE namespace = '{NS}' AND key = ?", ('32000', 'autoTriggerTokens'))

# Full engine configuration with NEW engines enabled
engines = {
    'session-dedup': {'enabled': True},    # NEW: dedup duplicate messages
    'relevance': {'enabled': True},         # NEW: prune irrelevant content
    'headroom': {'enabled': True},          # NEW: keep safety margin
    'rtk': {'enabled': True, 'level': 'full'},
    'caveman': {'enabled': True, 'level': 'full'},
    'stacked': {'enabled': True, 'pipeline': ['rtk', 'caveman']},
    'ccr': {'enabled': False},
    'lite': {'enabled': False},
    'aggressive': {'enabled': False},
    'ultra': {'enabled': False},
    'llmlingua': {'enabled': False},
}
db.execute(f"UPDATE key_value SET value = ? WHERE namespace = '{NS}' AND key = ?", (json.dumps(engines), 'engines'))

# Caveman config: compress user + assistant, min 50 chars
cavemanConfig = {
    'enabled': True,
    'compressRoles': ['user', 'assistant'],
    'skipRules': [],
    'minMessageLength': 50,
    'preservePatterns': [],
}
db.execute(f"UPDATE key_value SET value = ? WHERE namespace = '{NS}' AND key = ?", (json.dumps(cavemanConfig), 'cavemanConfig'))

db.commit()
```

## Engine descriptions (v3.8.48+)

| Engine | Savings | Latency | Purpose |
|--------|---------|---------|---------|
| `stacked` (RTK→Caveman) | 78-95% | ~250ms | **Recommended default.** RTK strips terminal/build noise, Caveman compresses prose. Code preserved. |
| `rtk` | 60-90% | ~150ms | Terminal, shell, build, test, git output filter. Command-aware. |
| `caveman` | ~30% | ~2ms | Filler word removal, sentence shortening. Code NEVER touched. |
| `session-dedup` | varies | ~1ms | **NEW.** Removes duplicate/redundant messages across turns. Safe always-on. |
| `relevance` | varies | ~5ms | **NEW.** Prunes content with low relevance to current query. Use with care on multi-step reasoning. |
| `headroom` | varies | ~1ms | **NEW.** Reserves token budget for upcoming tool calls. Keeps safety margin below context limit. |
| `lite` | ~15% | <1ms | Whitespace collapse, system prompt dedup, tool result compression. Zero semantic change. |
| `ccr` | varies | ~10ms | Context Compression Ratio optimizer. Experimental. |

## Auto-trigger threshold logic

| Context Window | Recommended Threshold | Reason |
|---|---|---|
| 128K | 32K | ~25%, saves most sessions uncompressed |
| 256K | 64K | ~25%, avoids wasting compression on short contexts |
| 1M | 200K | ~20%, very long sessions still benefit |

Rule: set at 20-25% of context window. Below threshold = uncompressed (preserves quality). Above = auto-compress (saves tokens).

## Key SQLite config keys for compression

| Key | Type | Values |
|---|---|---|
| `enabled` | bool string | `true` / `false` |
| `defaultMode` | string (quoted) | `"off"` / `"lite"` / `"standard"` / `"ultra"` / `"stacked"` |
| `autoTriggerTokens` | int string | `"0"` (always) / `"64000"` / `"128000"` |
| `engines` | JSON | Dict of engine configs |
| `cavemanConfig` | JSON | `enabled`, `compressRoles`, `minMessageLength`, `preservePatterns` |
| `rtkConfig` | JSON | `enabled`, `level` |
| `preserveSystemPrompt` | bool string | `true` / `false` |
| `comboOverrides` | JSON | Per-combo override settings |

## Restart required

SQLite changes only take effect after server restart:
```bash
# Find PID
PID=$(netstat -ano | grep 20128 | grep LISTENING | awk '{print $NF}' | head -1)
# Kill only that PID
/c/Windows/System32/taskkill.exe /F /PID $PID
# Restart
omniroute serve --port 20128 --no-open &
```
