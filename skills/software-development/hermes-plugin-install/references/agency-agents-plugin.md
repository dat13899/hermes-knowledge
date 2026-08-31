# The Agency Agents → Hermes plugin (session detail, 2026-08-08)

Repo: `https://github.com/msitarzewski/agency-agents` — "The Agency": 270 agent
personalities (17 divisions) as markdown files. Not a standalone app — a
personality library you install into agent tools (Claude Code, Cursor, Codex,
Gemini, OpenCode, **Hermes**, vibe...).

## Build

```bash
cd ~/agency-agents
./scripts/build-hermes-plugin.py --repo-root .. --out integrations/hermes
# → integrations/hermes/agency-agents-router/  (plugin.yaml + __init__.py + data/agents.json 3.8MB)
python scripts/check-hermes-plugin.py   # PASSED — schema + routing valid
```

The generated plugin is a **lazy router**: keeps the roster in on-disk
`data/agents.json` (avoids advertising 270 agents in Hermes' skill catalog),
exposes a small fixed tool surface. 4 tools:

| Tool | Args | Purpose |
| --- | --- | --- |
| `agency_agents_search` | query (req), division, limit | find specialists by capability |
| `agency_agents_inspect` | agent\|slug, include_body | metadata / full body |
| `agency_agents_load` | agent\|slug, task | compose specialist prompt block |
| `agency_agents_delegate` | agent\|slug, task, toolsets | delegate via `delegate_task` |

Flow: search → take slug → load/delegate.

## Install on this machine

- Copy: `cp -r integrations/hermes/agency-agents-router "$HERMES_HOME/plugins/"`
  ($HERMES_HOME = `C:\Users\datel\AppData\Local\hermes`).
- Enable: `plugins.enabled: [agency-agents-router]` in config.yaml (list-form!
  — `hermes config set` stringifies it, see SKILL.md pitfall #1).
- Toolset `agency_agents` NOT in `_DEFAULT_OFF_TOOLSETS` → auto-enabled.
- After gateway restart, `agency_agents_*` appear as real tools (verified live:
  search "pixel art game UI designer" → ui-designer, game-designer, level-designer).

## Cron integration (daily idea, job 62c3fee9aaf7)

Prompt step added: after choosing idea → `agency_agents_search` + `agency_agents_load`
with the task → apply specialist standards into build → mention hired agent in
summary. Fallback: "if tool unavailable, skip" (cron jobs run fresh sessions;
plugin loads because job `enabled_toolsets = null`).

## Gotchas hit

- `hermes config set plugins.enabled '[...]'` → string, plugin silently not
  loaded (0 errors). Fixed with Python yaml rewrite.
- `hermes plugins` interactive list shows only bundled — a user plugin working
  won't appear there; verify via PluginManager instead.
- Agent source files are markdown with YAML frontmatter (name/description/
  color/emoji/vibe) — `agency_agents_load` returns composed prompt from body.
