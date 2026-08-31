# Windows Verification Workflow (git-bash/MSYS2)

When running the autonomous-agent loop on **Windows (git-bash/MSYS2)**, the
standard POSIX verification scripts often fail. Use this reference instead.

## Python Script (execute_code)

`execute_code` is preferred for structured verification because it handles
paths correctly. However, **string escaping** is fragile:

- Do NOT nest `'''` triple quotes inside `'''.txt'''` style arguments
- Do NOT use raw strings `r'...'` containing Windows backslashes inside the
  outer script — `\U`, `\x` prefixes in paths cause `unicodeescape` errors
- Solution: write the verification script to a temp file with `write_file`,
  then run it with `terminal` using `python "C:/path/to/script.py"`

## Terminal Commands

```bash
# Correct path forms on git-bash:
# ❌ Never: /c/Users/... from terminal tool (MSYS2 doesn't map this)
# ✅ Works: "C:/Users/...") in double quotes  
# ✅ Works: cd /c/Users/... then relative paths

# Verify HTTP 200:
# ❌ FAILS on git-bash: -o /dev/null returns exit code 23 (WRITE_ERROR)
# curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/hermes.html
# ✅ Works on git-bash: use -o nul and double-quote the format string
curl -s -o nul -w "%{http_code}" http://localhost:3000/hermes.html

# grep inspection:
grep -n "featureName|startsWith|key" /c/Users/datel/service-dashboard/public/hermes.html
```

## Verification in Cron Mode

`execute_code` is **BLOCKED** in cron mode — the tool refuses to run because it bypasses shell-string approval. Use one of these alternatives instead:

### Pattern A: Inline `node -e` (preferred — no temp files, works on MSYS2)

```bash
node -e "
const fs=require('fs');
const html=fs.readFileSync('C:/path/to/project/public/hermes.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/);
try{new Function(script[1]);console.log('JS_SYNTAX:OK')}catch(e){console.log('JS_SYNTAX:FAIL '+e.message)}
"
```

Advantages: zero temp files, no MSYS2 path translation issues, handles cron restriction.

### Pattern B: Multi-call terminal checks

```bash
# HTTP check
curl -s -o nul -w "%{http_code}" http://localhost:3000/hermes.html

# Feature check
grep -c "data-mode=" /path/to/hermes.html
```

### Pattern C: `write_file` + `terminal` (beware path mangling)

The `write_file` tool writes to disk correctly. But when you reference the path from `terminal`, MSYS2 may double-prefix it as `C:\\c\\Users\\...`. Options to avoid this:

1. Use absolute `C:/Users/...` paths in the `terminal` call (with forward slashes)
2. Prefer Pattern A (inline) instead

**If you MUST use a temp file** (e.g. a long verification script impractical inline), use `cygpath -w` to convert the MSYS2 path to Windows-native form at call time:

```bash
node "$(cygpath -w /c/Users/datel/AppData/Local/Temp/myscript.js)" "C:/target/file.html"
```

Without `cygpath -w`, passing a bare `/c/` path to `node` on git-bash produces `C:\c\Users\...` (the `/c` prefix gets mapped to `C:\` but MSYS2's argument splitter already strips the leading `/`, leaving `c\` appended). `cygpath -w` outputs correct `C:\Users\...` form. Works for any interpreter (node, python, etc.) where raw MSYS2 paths trigger the double-prefix bug.

## Reusable Script: `scripts/verify-cron.js`

The autonomous-agent-loop skill ships `scripts/verify-cron.js` — a Node.js script for single-call verification in cron mode. It checks JS syntax, DOM integrity, HTTP 200, brace/backtick balance, required element IDs, and optionally a feature inventory.

Run from the project root:

```bash
# Basic: syntax + DOM refs + HTTP + structure
node scripts/verify-cron.js public/hermes.html http://localhost:3000/hermes.html

# With feature inventory: verify build-intended identifiers exist
node scripts/verify-cron.js public/hermes.html http://localhost:3000/hermes.html \
  --features "cfgBtn,toggleConfigPanel,drawSceneTransition,getTunnelSpeed,showTrails"

# Help
node scripts/verify-cron.js --help
```

The `--features` flag is the cron-safe equivalent of `execute_code` + grep — it checks that identifiers your build step was supposed to create actually exist in the compiled HTML/JS. Use it at the end of every build iteration to confirm all new code elements are reachable.

## Ad-Hoc Verification (preferred pattern — cron-safe)

Do NOT use `execute_code` for verification — it's blocked in cron mode.
Do NOT use temp Python scripts — MSYS2 path mangling causes `C:\c\Users\...` errors.

Use the **inline `node -e`** pattern (see "Verification in Cron Mode" above) or the
reusable `scripts/verify-cron.js` script shipped with this skill:

```bash
# One-shot: all checks in a single terminal call
node scripts/verify-cron.js public/hermes.html http://localhost:3000/hermes.html
```

### When write_file + script is unavoidable

If you absolutely must run a standalone script from cron:
1. Write the script with `write_file` to the project directory (not AppData\Temp)
2. Run it with `node` using a relative path (no MSYS2 prefix issues)
3. Use `.js` files, not `.py` — Node is always available on the project, Python `execute_code` is blocked

## Common Windows Pitfalls

| Problem | Fix |
|---------|-----|
| `\UXXXXXXXX` / `unicodeescape` error | Use `r'raw string'` or double backslashes, or write to temp file first |
| `search_files` fails with "IO error: system cannot find path" | Use `grep` in terminal instead, with MSYS2-full `grep` (not Windows-native) |
| `terminal` fails with `can't open file 'C:\\c\\Users\\...'` | MSYS2 prefix `/c/` becomes `C:\c\` — use `"C:/..."` in double quotes |
| Temp file not found after write_file | Use absolute path with forward slashes in terminal: `python "C:/Users/.../Temp/script.py"` |
| Node server died between iterations | Always verify with `process(action="list")` first, restart if missing |
