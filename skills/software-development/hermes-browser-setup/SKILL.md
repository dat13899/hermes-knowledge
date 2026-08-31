---
name: hermes-browser-setup
description: >-
  Configure Hermes browser tools: local Chrome, CDP override, cloud
  providers (Browserbase, Camofox). Platform-specific pitfalls and
  troubleshooting for the browser_navigate/click/snapshot/console tools.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, browser, chrome, cdp, setup, windows]
    related_skills: [hermes-agent, systematic-debugging]
---

# Hermes Browser Setup

Configure Hermes's browser automation tools (`browser_navigate`, `browser_click`, `browser_snapshot`, `browser_console`, `browser_vision`, `browser_cdp`, etc.).

> **CDP multi-tab:** `references/cdp-multitab-pitfalls.md` — when calling `browser_cdp` directly (stateless calls, `Emulation.setDeviceMetricsOverride`, `Runtime.evaluate`), always pass `target_id` from `Target.getTargets` and check `location.href` first; the tools can silently evaluate on a different tab (e.g. `chrome://new-tab-page/`), making console/screenshot results disagree.

## Complement: `agent-browser` CLI (vercel-labs) — dùng khi Hermes browser yếu

`agent-browser` (⭐40k, Rust CLI, daemon native) **bổ trợ** Hermes browser, KHÔNG thay thế. Dùng cho các trường hợp Hermes yếu:

| Hermes browser yếu | agent-browser bù |
|---|---|
| web_extract fail trang JS-heavy/SPA | `read` đọc rendered DOM active tab |
| web_extract fail vì ddgs backend (search-only, không extract) | `read <url>` fetch thẳng — đã verify đọc WCAG/W3C, blog (10/08/2026) |
| Mở Chrome nặng chỉ để lấy text | `read <url>` fetch thẳng không cần Chrome (~1.4s) |
| Output text khó parse | Mọi lệnh hỗ trợ `--json` |
| Phải CDP thủ công cho drag/upload/download | Có sẵn `drag`, `upload`, `download`, `check`, `select` |
| Snapshot ít refs | Snapshot chi tiết (hàng nghìn refs, `@e1`...) |

**Cài đặt (Windows):**
```bash
npm install -g --allow-scripts=agent-browser   # allow-scripts bắt buộc (postinstall download Chrome)
agent-browser install                          # tải Chrome for Testing 151 (~192MB)
```

**Lệnh chính (đã test OK 10/08/2026):**
```bash
agent-browser open <url>          # mở + navigate (alias: goto/navigate)
agent-browser snapshot            # accessibility tree với refs @e1... (giống Hermes)
agent-browser click @e2           # click theo ref
agent-browser type @e145 "text"   # type vào element
agent-browser press Enter         # phím
agent-browser read [url]          # ⭐ fetch text không cần Chrome; bỏ url = đọc rendered DOM tab hiện tại
agent-browser read <url> --json   # agent-readable JSON
agent-browser screenshot <path>   # ⭐ path phải là WINDOWS path (C:\Users\...), MSYS /c/... bị lỗi os error 3
agent-browser screenshot --annotate --screenshot-dir <dir>  # screenshot có số refs
agent-browser screenshot --full "C:\path\full.png"          # full page
agent-browser console             # xem console log/JS errors (giống browser_console)
agent-browser get url|title|text <sel>|box|styles|count
agent-browser close               # đóng browser (daemon tự spawn lại khi open)
agent-browser skills get core     # workflow patterns tích hợp
```

**Pitfalls (đã test 10/08/2026):**
- `npm install -g agent-browser` KHÔNG chạy postinstall (npm 12 chặn allowScripts) → phải `--allow-scripts=agent-browser`
- Screenshot path: bắt buộc path Windows `C:\Users\...` — MSYS `/c/...` → `os error 3`
- KHÔNG click theo text ("Learn more" → lỗi) — chỉ ref/selector
- Google search bị CAPTCHA (automation detection) — dùng DuckDuckGo khi test
- `screenshot --full` đôi khi treo daemon (os error 10060) — daemon tự recover ở lệnh open kế
- Daemon là `agent-browser-win32-x64.exe` — `close` chỉ đóng browser tab, daemon vẫn chạy
- Chrome for Testing 151 riêng (192MB) — không đụng Chrome chính của user
- ⚠️ `open <url>` CLI có thể TIMEOUT (60s) dù navigation ĐÃ THÀNH CÔNG — daemon spawn + load page xong nhưng command không trả exit. Đừng tin exit code/timeout: verify bằng `get url` / `get title` / `snapshot` sau đó.
- ⚠️ Viewport: dùng `agent-browser set viewport <w> <h>` — KHÔNG phải `agent-browser viewport <w> <h>` (help in "viewport <w> <h>" dưới mục "Browser Settings: agent-browser set <setting>" = danh sách setting, không phải command độc lập).

**Verify SPA React nhanh (btdat.io.vn, daily ideas...):** recipe đầy đủ đã test — `references/agent-browser-spa-verify.md`

## How the Browser Tool Decides Its Backend

Resolution order (browser_tool.py `_get_cdp_override()` → `_is_local_mode()` → `_is_camofox_mode()`):

1. **BROWSER_CDP_URL** env var — live override, set by `/browser connect` or manual export
2. **browser.cdp_url** in `config.yaml` — persistent config, read at session start
3. **Browserbase** — cloud provider, requires `BROWSERBASE_API_KEY`
4. **Camofox** — cloud provider, set `CAMOFOX_PROXY_URL`
5. **Local `agent-browser`** — auto-launches bundled Chrome

When (1) or (2) is set, the tool connects directly to a running Chrome via CDP and skips local auto-launch and cloud providers entirely.

## Setup Methods

### Method A: CDP Override (recommended for Windows)

Best when Chrome fails to auto-launch (common on Windows with `exit code: 0 without DevToolsActivePort`).

**Step 0 — Kill ALL existing Chrome processes first (CRITICAL):**
```bash
# Windows (git-bash / MSYS) — must kill before debugging-port launch works
taskkill /F /IM chrome.exe 2>&1
sleep 2
```

**CRITICAL: Use regular (non-headless) Chrome for pages with WebGL/3D/Canvas content.** Headless Chrome (`--headless=new`) does NOT render WebGL textures, 3D scenes (Three.js, React Three Fiber), or complex canvas elements properly — resulting screenshots show blank areas, missing textures, or broken visuals. For any page with WebGL/3D content, launch Chrome WITHOUT `--headless`.

**CRITICAL: Always include `--remote-allow-origins=*` flag.** Without it, CDP WebSocket handshake from external tools (e.g., Python `websocket` library, `browser_navigate`) returns HTTP 403. Essential for `browser_vision`, `browser_navigate`, and direct CDP WebSocket connections.

**Launch command for 3D/WebGL pages with full CDP access:**
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir=C:/Users/<user>/chrome-debug \
  --no-first-run \
  --no-default-browser-check \
  --remote-allow-origins=* \
  --window-size=1920,1080 \
  "https://target-url.com"
```

If Chrome is already running (even a background process), `--remote-debugging-port=9222` opens a new tab in the EXISTING profile WITHOUT the debug flag and the port NEVER opens. Kill everything first. Check with `netstat -ano | grep ":9222"`.

**Step 1 — Launch Chrome HEADED (not headless) with dedicated profile:**
```bash
# Use a separate user-data-dir to avoid profile lock conflicts
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/<user>/chrome-debug" \
  --no-first-run --no-default-browser-check 2>&1 &
```

`--headless=new` is NOT needed and often fails on Windows when other Chrome instances existed. Headed mode with a dedicated `--user-data-dir` prevents profile lock conflicts with the user's normal Chrome profile. The `--no-first-run` and `--no-default-browser-check` flags skip setup dialogs.

On other platforms, find Chrome at `/usr/bin/google-chrome` (Linux) or `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (macOS).

**Step 3 — Verify it's listening:**
```bash
curl -s http://localhost:9222/json/version
```
Expect: `{"Browser": "Chrome/150.0.7871.46", ...}`

**Step 3b — CDP endpoint not a WebSocket URL (dead port diagnosis):**
If `browser.cdp_url` is set (config or `BROWSER_CDP_URL`) but no Chrome is
actually listening on that port, every `browser_navigate` — even to
`example.com` — times out with "Operation timed out", and `browser_cdp`
reports `CDP endpoint is not a WebSocket URL: 'http://127.0.0.1:9222'`.
This is a **dead CDP port**, not a site problem and not a browser-tool bug.
Diagnosis: `curl -s http://127.0.0.1:9222/json/version` returns nothing, and
`netstat` shows no LISTEN on 9222. Fix: relaunch Chrome on the port (Step 1)
and re-verify (Step 3). A page failing to load on a healthy site while even
example.com times out is the signature of this state.
If empty or connection refused, Chrome didn't start — check `tasklist | grep chrome` and `netstat -ano | grep ":9222"`.

**Step 3 — Tell Hermes to use it (pick one):**

*Option A — persistent config (takes effect on next tool call, no /reset needed):*
```yaml
# ~/.hermes/config.yaml
browser:
  cdp_url: "http://127.0.0.1:9222"
```
Note: `browser.cdp_url` does take effect without `/reset` — Hermes reads it at tool invocation time, not session start.

*Option B — env var (live immediate override):*
```bash
export BROWSER_CDP_URL="http://127.0.0.1:9222"
```

*Option C — slash command (CLI/TUI only):*
```
/browser connect http://127.0.0.1:9222
```

**Step 4 — Test:**
```
browser_navigate(url="https://btdat.io.vn/")
browser_console(expression="document.title")
```

### Method B: Local agent-browser (default)

Hermes auto-launches a bundled Chrome via `npx agent-browser`. Works out of the box on most Linux/macOS. On Windows, often crashes with `exit code: 0 without DevToolsActivePort` — fall back to Method A.

### Method C: Cloud providers

- **Browserbase:** Set `BROWSERBASE_API_KEY` in `.env` (plus optional `BROWSERBASE_PROJECT_ID`, `BROWSERBASE_REGION`). Browser tool auto-detects.
- **Camofox:** Set `CAMOFOX_PROXY_URL` in `.env` + set `browser.camofox: true` in config.

## Pitfalls & Troubleshooting

### browser_vision fails with vision model 401 or timeout
When `browser_vision` hangs/times out because the auxiliary vision model returns 401 (common when routing through OmniRoute with limited vision provider support), fall back to direct CDP screenshot capture:
1. Use `browser_cdp` with `Page.captureScreenshot` — returns base64 image data
2. For small screenshots (<1MB base64): decode inline via Python `base64.b64decode()`, save, deliver via `MEDIA:<path>`
3. For large screenshots that get truncated: use Python `websocket` library to connect to CDP WebSocket directly and capture JPEG at quality 25-30. **Requires `--remote-allow-origins=*`** on Chrome launch.
4. Prefer JPEG format at lower quality (25-50) for file size — invisible difference for UI review, much smaller payload.

### Chrome port 9222 never opens despite Chrome running

**Root cause:** If Chrome was already running (even a background process or tray icon), launching `chrome.exe --remote-debugging-port=9222` opens a new tab in the EXISTING profile WITHOUT the debug flag. The port never opens because the debug flag is ignored when attaching to a running instance.

**Detection:** `tasklist | grep chrome` shows processes but `netstat -ano | grep 9222` returns nothing.

**Fix:** Kill ALL Chrome processes first, then launch with a dedicated `--user-data-dir`:
```bash
taskkill /F /IM chrome.exe
sleep 2
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/<user>/chrome-debug" \
  --no-first-run --no-default-browser-check &
```

### Config takes effect on tool call, not session start

`browser.cdp_url` in `config.yaml` is read at tool invocation time — no `/reset` needed. If setting mid-session:
- `hermes config set browser.cdp_url "http://127.0.0.1:9222"` and the next `browser_navigate` call picks it up

### BROWSER_CDP_URL not persisting

- Terminal `export BROWSER_CDP_URL=...` only affects the shell's subprocesses, not the running Hermes Python process
- Git-bash/MSYS on Windows may not propagate env vars to npx/node correctly
- The `.env` file (`~/.hermes/.env`) is read at startup and reloaded by `/reload` (CLI only)

### agent-browser not found or npx failed

- `npx agent-browser install` installs Chrome locally
- Bundled Chrome lives at `~/.agent-browser/browsers/chrome-*/`
- If npx is missing, install Node.js or use a direct Chrome binary path

### Chromium/Blink engine assumption

Hermes browser tools assume Chrome/Chromium via CDP. Firefox, Safari, and other engines are NOT supported. If you need those, use CDP mode with a compatible browser or fall back to `curl`/`web_extract` via terminal.

## Vision / Screenshot Analysis (browser_vision, vision_analyze)

`browser_vision` takes a screenshot then routes it through `auxiliary.vision.*` config — a SEPARATE model/provider from the main chat model. If vision returns errors (401, 403, empty responses), the auxiliary model is the problem, not the browser connection.

### Quick fix

```bash
# Check current config
hermes config | grep auxiliary

# Set a working OmniRoute vision model
hermes config set auxiliary.vision.provider omniroute
hermes config set auxiliary.vision.model "cmd/MiniMaxAI/MiniMax-M3"
hermes config set auxiliary.vision.base_url "http://localhost:20128/v1"
```

**Config takes effect after gateway restart** (`/restart` in Telegram, or `hermes gateway restart`), NOT mid-session. Unlike `browser.cdp_url` (read at tool invocation), `auxiliary.*` config is read at session start.

See `references/omiroute-vision-setup.md` for full model compatibility matrix and direct API test script.

## Verification

```bash
# Is Chrome running on CDP?
curl -s http://localhost:9222/json/version | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('Browser',''))"

# Quick end-to-end test (after config):
# browser_navigate(url="https://example.com") should return page content
```

## Alternative: Browser-Use (external skill)

[Browser-Use](https://github.com/browser-use/browser-use) is an open-source Python library that lets an AI agent control a browser directly via CDP — click, type, navigate, fill forms. It runs as a `browser-use` CLI backed by a Rust core + browser harness, not through Hermes's built-in browser tools. Use it when you need a different action space, persistent browser harness, or Rust-core agent loop.

### Install

```bash
uv pip install browser-use
```

### Register skill for other agents

Installs SKILL.md to `~/.agents/skills/`, `~/.claude/skills/`, `~/.cursor/skills/`, etc.

```bash
browser-use skill install
```

### Enable in Hermes

The installer does NOT write to Hermes skills directory. Copy manually:

```bash
mkdir -p ~/AppData/Local/hermes/skills/browser-use
cp ~/.agents/skills/browser-use/SKILL.md ~/AppData/Local/hermes/skills/browser-use/SKILL.md
```

Then `/reload` or start a new session (`/reset`). Hermes only scans skills at session start — a mid-session copy won't show in skills_list.

### Verify

```bash
browser-use --help
```

### When to use which

| | Hermes built-in browser tools | Browser-Use |
|---|---|---|
| Interface | tool calls (browser_navigate, browser_click, etc.) | `browser-use` CLI + Python SDK |
| Action space | navigation, click, type, scroll, snapshot, CDP | click-at-xy, CDP, JS eval, screenshots, tabs |
| Setup | auto-launch or CDP override | `uv pip install` + `skill install` + manual copy |
| Best for | quick inspection, form filling, scraping | complex multi-step workflows, persistent harness |
| Chrome needed | bundled or manual | bundled or manual (same CDP endpoint) |

### Gotchas

- `browser-use` CLI is NOT on PATH after `uv pip install` on Windows (uv installs into internal venv, not system PATH). Use `uv run browser-use ...` or `python -m browser_use ...`.
- The skill installer supports `--target agents,claude,codex,cursor,gemini,opencode` but NOT `hermes` — manual copy always needed.
- New skills in Hermes need `/reload` or new session to appear.
- browser-use also needs Chrome running with CDP. Reuse the same CDP setup from Method A above.

## Related

- `references/stream-url-extraction-via-cdp.md` — Extract live HLS/DASH stream URLs from dynamic SPA websites using CDP + Performance API. Covers age-gate bypass, m3u8 discovery, CDN patterns, and expiring-link pitfalls.
- `agent`/`browser_cdp_tool.py` — raw CDP escape hatch (`browser_cdp` tool)
- `tools/browser_tool.py` — main browser implementation
- `hermes_cli/browser_connect.py` — `/browser connect` slash command
- The `browser` toolset is separate from the `web` toolset (web search/extraction). Some features require both enabled.
- `references/omiroute-vision-setup.md` — OmniRoute vision model setup and test results. Use `cmd/MiniMaxAI/MiniMax-M3` via OmniRoute at localhost:20128. Working as of July 2026. Covers failed models, direct API test script, and provider config.
