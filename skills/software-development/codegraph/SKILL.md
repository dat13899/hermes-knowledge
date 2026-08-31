---
name: codegraph
description: "CodeGraph MCP: query symbols, callers, impact analysis."
trigger:
  - "cần tìm symbol, caller/callee, impact của 1 thay đổi trong codebase"
  - "muốn hiểu cấu trúc project lớn (OmniRoute, service-dashboard)"
  - "agent cần context code chính xác, ít tool calls / ít tokens"
---

# CodeGraph — Semantic Code Intelligence

## What it is
CodeGraph (github.com/colbymchenry/codegraph, MIT, Rust kernel, 100% local) indexes a codebase into a symbol + call-edge knowledge graph stored in `.codegraph/` (SQLite). Wires an MCP server into Hermes so the agent queries the graph instead of grep-mò: fewer tool calls, fewer tokens. README claims ~60% cheaper / 69% fewer tokens on big repos.

## Install status (this machine, 2026-07-31)
- CLI **v1.5.0** via `npm i -g @colbymchenry/codegraph` (self-contained, bundles Node runtime — no compile)
- MCP server already wired: `~/AppData/Local/hermes/config.yaml` → `mcp_servers.codegraph` (`command: codegraph serve --mcp`)
- ⚠️ **MCP changes require a NEW Hermes session** — the session active at install time does NOT see the new tools
- Indexed projects:
  - `~/service-dashboard` → 101 files, 864 nodes, 1,816 edges (4.3s)
  - `~/AppData/Roaming/npm/node_modules/omniroute` → 2,172 files, 31,822 nodes (15.7s — includes node_modules, noisy but works)

## Setup for a NEW project
```bash
cd <project>
codegraph init          # creates .codegraph/ + builds full graph (one time)
```
- Auto-sync via file watcher — never stale, nothing to re-run
- `codegraph status` (up-to-date check) · `codegraph index` (full rebuild) · `codegraph sync` (incremental)
- Remove: `codegraph uninit` (drops `.codegraph/` only)

## Wiring agents (only needed on reinstall)
```bash
codegraph install        # INTERACTIVE checkbox prompt — hangs without TTY, don't run bare in scripts
codegraph install --target hermes --location global --yes   # non-interactive, Hermes only
```
- Detects & configures: Claude Code, Cursor, Codex CLI, opencode, Hermes Agent, Gemini CLI, Antigravity, Kiro
- `codegraph uninstall` strips agent configs + CLI; `--keep-cli` keeps the CLI
- Verify config: grep `mcp_servers` in `~/AppData/Local/hermes/config.yaml`

## Usage (CLI mirrors the MCP tools)
```bash
codegraph query "Navbar"           # symbol search across index
codegraph explore "CommandPalette" # symbol source VERBATIM + call paths (same output as codegraph_explore MCP tool)
codegraph node <name>              # one symbol + caller/callee trail
codegraph files                    # project file structure from index
```
MCP tools (available after session restart): `codegraph_query`, `codegraph_explore`, `codegraph_node`, ...

## Verified on btdat codebase (2026-07-31)
- `query "Navbar"` disambiguated the TWO Navbar files, confirming `layout/Navbar.jsx` (real) vs `components/Navbar.jsx`
- `explore "CommandPalette"` returned verbatim current on-disk source + call paths — output states to treat as a Read already performed, do NOT re-read the file

## Pitfalls
- **Interactive prompts hang without PTY** — always pass `--target <agent> --location global --yes` for non-interactive install
- **Global npm packages get node_modules indexed** (omniroute: 2k+ files) — acceptable but noisy; configure ignores + `codegraph index` if it matters
- Telemetry on by default: `codegraph telemetry off` or `CODEGRAPH_TELEMETRY=0`
- Upgrade in place: `codegraph upgrade` (detects bundle/npm/npx install method)
