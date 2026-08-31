---
name: agent-browser-cli
description: "Use agent-browser CLI for fast browser automation."
category: software-development
---

# agent-browser CLI (vercel-labs)

Fast native-Rust browser automation CLI for AI agents: `open`/`read`/`snapshot`/`click`/`type`/`console`/`screenshot`. Installed globally on Anh Đạt's machine (v0.33.2, Chrome 151.0.7922.77 for Testing). Use when Hermes browser tools are slow, web_extract fails on JS-heavy pages, or you need fast rendered-DOM text extraction. **Complementary to Hermes browser tools, not a replacement** (Hermes `browser_cdp` is the raw-CDP escape hatch this CLI lacks).

## Install (Windows/git-bash)

```bash
# postinstall scripts are BLOCKED by default npm → must use --allow-scripts
npm install -g --allow-scripts=agent-browser agent-browser
agent-browser install   # downloads Chrome for Testing (~192MB) → ~/.agent-browser/browsers/
agent-browser --version
```

## Quick Start

```bash
agent-browser open "https://example.com"     # launch daemon + navigate (aliases: goto, navigate)
agent-browser snapshot                        # accessibility tree with @refs (like Hermes snapshot)
agent-browser click @e2                       # click by ref from snapshot
agent-browser type @e145 "query" && agent-browser press Enter
agent-browser read                            # rendered DOM of ACTIVE tab (SPA-friendly, includes auth state)
agent-browser read "https://example.com" --json   # fetch WITHOUT Chrome, ~1.4s, JSON out
agent-browser console                         # JS console logs/errors (like browser_console)
agent-browser screenshot "C:\path\shot.png"   # viewport shot; --annotate adds numbered @ref labels
agent-browser close                           # close browser (daemon stays; next open respawns it)
```

## Windows / git-bash Pitfalls (đã dính 10/08/2026)

- **Screenshot path MUST be native Windows** (`C:\Users\...\shot.png`). MSYS path `/c/Users/...` → `os error 3` "path not found". Same for `--screenshot-dir`.
- `open` spawns a background daemon `agent-browser-win32-x64.exe`. If a command hangs (e.g. `get url` timeout after a `--full` screenshot error), the daemon is stuck — a NEW `open` call respawns it automatically; no need to taskkill (and `taskkill //F //PID` syntax is wrong in git-bash anyway).
- `screenshot --full` can hang the daemon once; retry with explicit native path works.
- **click by text NOT supported** ("Learn more" → "Element not found"). Must use `@ref` from snapshot or CSS selector (`#id`, `.cls`).
- Google search → CAPTCHA "unusual traffic" (normal for automation). Use DuckDuckGo or Wikipedia for tests.
- `read <url>` sends `Accept: text/markdown`, walks `llms.txt`, falls back to readable HTML text. `--raw` = response body, `--filter <text>` narrows sections, `--outline` = heading outline.
- Every command supports `--json` for machine/agent consumption.
- Built-in skills: `agent-browser skills get core --full` — version-matched workflow patterns, prefer over guessing flags.

## vs Hermes browser tools (tested 10/08/2026)

| Capability | agent-browser | Hermes browser |
|---|---|---|
| read URL → text (no browser) | ⚡ ~1.4s, `--json` | web_extract (fails JS-heavy) |
| read active-tab rendered DOM (SPA) | ✅ GitHub nav rendered | web_extract often fails |
| open+snapshot throughput | ~0.57s | ~2-5s CDP round-trip |
| snapshot refs detail | up to ~3800 refs (Wikipedia) | ~200-500 typical |
| raw CDP escape hatch | ❌ none | ✅ browser_cdp |
| helpers (drag/upload/download/check/select) | ✅ built-in | manual via browser_cdp |

## Good use cases

- Verify daily-ideas pages: `open <url>` → `console` (0 JS errors) → `screenshot` 2 viewports.
- Web research fallback when web_extract/browser fail (JS SPAs, auth-state pages).
- Fast DOM text dumps via `read --json` without spinning up a browser.

Tested: v0.33.2 on Windows 10/git-bash, Chrome 151.0.7922.77 (10/08/2026).
