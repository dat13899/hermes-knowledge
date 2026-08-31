---
name: autonomous-agent-loop
title: Autonomous Agent Loop (Self-Governing Cron)
description: >-
  Self-governing cron agent that reads state, self-decides phase (init/build/verify/eval/done),
  builds code, tests, evaluates with strict scoring, and iterates — all without user intervention.
  State file JSON pattern, phase machine, scoring rubric.
category: autonomous-ai-agents
triggers:
  - "hermes loop"
  - "loop agent"
  - "autonomous agent"
  - "self-governing cron"
  - "build tự trị"
  - "cron agent tự sáng tạo"
  - "hermes-loop"
  - "self-improving agent"
version: "1.1.1"
---

## Overview

Cron job that runs an agent with **full autonomy**: reads state, decides what to do next,
executes (code/verify/eval), records progress, and iterates. No user prompting between iterations.

Designed for creative/exploratory builds where the agent drives the roadmap.

## Architecture

```
Cron (every 30m minimum) → Hermes agent session
                              │
                              ▼
                       Read state.json
                              │
                              ▼
                      ┌── PHASE MACHINE ──┐
                      │ init → build      │
                      │      → verify     │
                      │      → eval       │
                      │      → (loop/done)│
                      └───────────────────┘
                              │
                              ▼
                       Write state.json
                              │
                              ▼
                       Git commit + push
                              │
                              ▼
                       Report to user
```

## State File (`hermes-state.json`)

```json
{
  "iteration": 0,
  "phase": "init",
  "vision": null,
  "goal": "Decide what to build",
  "built": [],
  "todo": ["First iteration — choose direction"],
  "critic": null,
  "score": null,
  "done": false
}
```

## Phase Machine

| Phase | Behavior | Exit |
|-------|----------|------|
| **init** | Decide vision & first goal. Start fresh or pick from scratch. | → build |
| **build** | Write/edit code. Git commit. Push. | → verify |
| **verify** | `curl` health check. Syntax check. Feature scan. | Fail → build. OK → eval or → build (see sub-modes). |
| **eval** | Review code. Self-score 1-10 (strict). Write critic. | Score < 9 → build. Score ≥ 9 & out of ideas → done. |
| **done** | No-op. Report final summary. Cron keeps running but does nothing. | ✅ |

### Sub-Modes

| Mode | Phase Cycle | Use When |
|------|------------|----------|
| **build-eval** (default) | init → build → verify → eval → (loop build or done) | Standard product: score, quality gate, eventual completion. |
| **perpetual-build** | init → build → verify → build → verify → … | Creative/artistic: no completion, no scoring — always add features. State `phase` stays `"build"` forever. `done` is always `false`. Eval phase is skipped entirely. |

**Perpetual-build cycle** (used by creative autonomous agents like Cosmic Dreamscape):
```
Read state → Decide next creative feature → Code → Git commit+push → Verify (200 + structural) → Write state (iteration++) → Report
```
No score, no eval, no done — the agent is the product owner and drives the roadmap.

### Scoring Rubric (MUST be strict)

| Score | Criteria |
|-------|----------|
| 1-3 | Runs but very basic, minimal effort |
| 4-5 | Functional, correct but nothing special |
| 6-7 | Good, has highlights, runs smoothly |
| 8-9 | Very good, creative, polished UI |
| 10 | Exceptional, unique, cannot improve |

Self-critic is mandatory — point out flaws even at score 9.

## Cron Setup

```bash
# Create the cron job:
cronjob action=create \
  name="my-agent-loop" \
  schedule="every 30m" \
  skills='["hermes-agent"]' \
  workdir="/path/to/project" \
  deliver="origin" \
  prompt="Self-contained prompt (see below)"
```

### Critical cron parameters

- **`workdir`** — MUST point to project root so relative paths work (state file, target files)
- **`skills`** — load `hermes-agent` so the agent knows its own tooling
- **`deliver: "origin"`** — results come back to this conversation
- **Model override** — DO NOT set model override on cron if the default provider has rate limits. Model override pattern: `{"model": null, "provider": null}` actually removes it; passing model without provider fails with "No LLM provider configured". Use `cronjob action=update job_id=X model={}` with empty object to clear, but this may not work — safer to delete and recreate.
- **Provider 429/rate limits** — if default provider is local (e.g. 127.0.0.1:XXXXX) and rate-limited, try OpenRouter as fallback with explicit model override, but verify OpenRouter API key exists in config first.

### Prompt structure

The prompt must be **fully self-contained** — no prior conversation context.

```
[Your identity & mission — one paragraph]
[Phase machine instructions — step by step]
[State file location and format]
[Rules: free to create, no asking user, always commit, strict eval]
[Report format for user at end]
```

## Linked Files

| File | Purpose |
|------|---------|
| `templates/perpetual-report.md` | Report template for perpetual-build mode (Vietnamese, no eval) |
| `references/windows-verify.md` | Windows/git-bash verification workflow — paths, scripts, pitfalls |
| `scripts/verify-cron.js` | Standalone Node.js HTML-project verifier for cron mode (no execute_code needed). Supports `--features \"id1,id2,...\"` for feature-inventory check. |

### Reusable Script: `scripts/verify-cron.js`

This script runs 6 checks in one call — preferred over multiple terminal calls or blocked `execute_code`:

```bash
# Basic: syntax + DOM + HTTP + structure + balance
node scripts/verify-cron.js public/hermes.html http://localhost:3000/hermes.html

# With feature inventory: verifies specific JS identifiers/element IDs exist
node scripts/verify-cron.js public/hermes.html http://localhost:3000/hermes.html --features "cfgBtn,toggleConfigPanel,drawSceneTransition,getTunnelSpeed,showTrails"

# Help
node scripts/verify-cron.js --help
```

The `--features` flag is the cron-safe equivalent of what you'd do with `execute_code` + grep — it checks that the identifiers your build step was supposed to create actually exist in the compiled HTML/JS.

## Common Pitfalls

- **State file stale** — cron opens fresh context each time. If state says `done`, phase machine no-ops properly. If state accidentally set `done: true` too early, agent won't build further. Fix: reset `done: false` + set `phase: "build"`.
- **Model provider fail** — "No LLM provider configured" error. Cron jobs don't inherit the current session provider automatically unless `model` field is omitted entirely. If cron fails with this error, delete and recreate without model override.
- **Provider 429/rate limit** — "Invalid SSE response for non-streaming request (reset after 20s)" = provider overloaded. Switch provider or add delay between iterations.
- **Git commit noise** — every iteration adds 1+ commits. OK for creative loop, but set `repeat` to a finite number or un-cron when `done: true`.
- **File target path** — workdir's `public/somefile.html` must match server static route. If target URL has path like `/hermes`, add redirect in server: `if (u.pathname === '/hermes') u.pathname = '/hermes.html'`.
- **Initial seed file** — create an empty/minimal target file before first cron run so `/hermes` returns 200 and the agent has something to start from.
- **Server restart after code changes** — agent must restart Node after git pull or code changes. Pattern: `process(action="list")` → find node session → `process(action="kill", session_id=...)` → `terminal(background=true, command="node server.js")` → `curl` verify.
- **State file write timing** — agent may crash mid-write. Use atomic write pattern if possible (write to temp, rename). For simple JSON, accept risk; state is small and regenerative.
- **Cache bust (Cloudflare)** — if production is behind CF, new HTML/CSS/JS won't show until cache purged. Bump `?v=N` on CSS/JS links each iteration.

### 💥 JS Syntax Gotcha — `?.number` (Ternary vs Optional Chaining)

When writing ternary expressions with numeric literal values, **the sequence `?.` is always parsed as the optional chaining operator** — JS doesn't see a ternary operator followed by a decimal point.

**BAD** — produces `SyntaxError: Unexpected number`:
```js
const a = wordFormed?.9:.6;           // → SyntaxError
ctx.lineWidth = isConstellation?.8:.5; // → SyntaxError
```

**Why:** `?.9` parses as `?.(optional-chaining) .9(number-literal)` — JS expects a property name after `?.`, not a numeric literal.

**FIX** — spaces around the ternary `?`:
```js
const a = wordFormed ? .9 : .6;
ctx.lineWidth = isConstellation ? .8 : .5;
```

⚠️ **Common in large creative canvas files** where numeric literals like `.8`, `.5`, `.1` appear in ternary expressions and spaces get lost.

**Detection (cron-safe inline):**
```bash
node -e "
const fs=require('fs');
const html=fs.readFileSync('target.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/);
if(script) try{new Function(script[1]);console.log('SYNTAX:OK')}catch(e){console.log('SYNTAX:'+e.message)}
"
```

**Find all instances:**
```bash
grep -n '?\\.[0-9]' path/to/file.html
```

### "Splash spins forever" Debugging Checklist

When a single-file HTML canvas app appears stuck on the loading/splash screen:

| Step | Check | Command |
|------|-------|---------|
| 1 | HTTP status | `curl -s -o nul -w "%{http_code}" https://site/page` |
| 2 | Real file size | `curl -s https://site/page | wc -c` (expect 100K+, not 0) |
| 3 | Content deployed | `curl -s https://site/page | grep "expected-text"` |
| 4 | JS parses? | Pipe curl through Node inline parse (see above) |
| 5 | `?.` + digit? | `grep -n '?\\.[0-9]' path/to/file` — the #1 cause |
| 6 | CF cache stale | Bump `?v=N` on assets, purge CF, or hard refresh |
| 7 | Browser console | 0 errors + `requestAnimationFrame(loop)` firing = it works |

**Root cause of "infinite splash"** is usually: HTML returns 200, file loads, but JS has a parse error → no `requestAnimationFrame(loop)` ever fires → splash CSS timeout never triggers fade → user sees spinner forever. Steps 4-5 catch this immediately.

### Cron-Specific Verification Pitfalls (Windows/git-bash)

- **`execute_code` is BLOCKED in cron mode** — Hermes blocks the tool when running as a cron job because it can bypass shell-string approval checks without a user present. Do NOT attempt to use `execute_code` for verification in cron sessions. Use these alternatives:
  1. **Inline `node -e`** for JS syntax + DOM structural checks (preferred on Windows)
  2. **Multiple `terminal` calls** for individual checks (curl, grep, file read)
  3. **`write_file` + `terminal("node script.js")`** — BUT beware MSYS2 path translation (see below)

- **`curl -o /dev/null` returns exit code 23 on git-bash/MSYS2** — the `/dev/null` device is emulated but curl's `-o` flag uses Win32 API which can't open it. Exit code 23 is `WRITE_ERROR`, NOT a connection failure. Use `-o nul` instead:
  ```bash
  curl -s -o nul -w "%{http_code}" http://localhost:3000/hermes.html
  ```
  This exits 0 on success. Always check the stdout body, not just the exit code.

- **`write_file` + `terminal` path mangling on MSYS2** — running a temp script via `terminal` may produce `C:\\c\\Users\\...` (double-mapped). **Prefer inline `node -e`** with `C:/...` absolute paths. No temp, no path issue, survives cron.

  When you MUST use a temp file (long verification script impractical inline), wrap the path with `cygpath -w`:
  ```bash
  node "$(cygpath -w /c/Users/datel/AppData/Local/Temp/myscript.js)" "C:/target/file.html"
  ```
  Without `cygpath -w`, the `/c/` prefix is mapped to `C:\` but MSYS2's argument splitter strips the leading `/`, leaving `c\` appended — producing `C:\c\Users\...`. This workaround applies to any interpreter (node, python, etc.). See `references/windows-verify.md` for the full explanation and the preferred Pattern A (inline `node -e`) alternative.

- **Terminal tool loop guard** — after 3+ identical terminal failures, Hermes flags `[Tool loop warning]`. If curl exits with code 23 every time, the agent retries it identically and burns turns. Detect exit code 23 as write-error (not connection error), then switch strategy immediately.

### Cron Verification Pattern (Inline Node.js)

Use this one-shot inline verification instead of `execute_code`:

```bash
node -e "
const fs=require('fs');
const html=fs.readFileSync('C:/Users/datel/service-dashboard/public/hermes.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/);
try{new Function(script[1]);console.log('JS_SYNTAX:OK')}catch(e){console.log('JS_SYNTAX:FAIL '+e.message)}
"
```

Replace the path and URL with the actual project. This works in cron, handles MSYS2 paths, needs zero temp files.
