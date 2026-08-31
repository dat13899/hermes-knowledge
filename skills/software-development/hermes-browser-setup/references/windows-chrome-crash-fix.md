# Chrome Windows Crash — `exit code 0` / DevToolsActivePort Fix

## Symptom

Browser tool fails with:

> Auto-launch failed: Chrome exited early (exit code: 0) without writing DevToolsActivePort
> (also tried parsing stderr) Chrome exited before providing DevTools URL (no stderr output from Chrome)

## Root Cause

On Windows (git-bash/MSYS), the bundled Chrome (`agent-browser`'s `chrome-150.0.7871.46` or similar) crashes silently when launched by Hermes's browser tool. Exit code 0 is misleading — it means the Chrome process never reached the point of writing its DevTools port file. `--no-sandbox` is required for headless mode on Windows in many environments.

## Fix (CDP Override Pattern)

**1. Start Chrome headless manually in the background:**
```bash
"$HOME/.agent-browser/browsers/chrome-150.0.7871.46/chrome.exe" \
  --headless=new --remote-debugging-port=9222 \
  --no-sandbox --disable-gpu 2>&1 &
```

**2. Verify it's listening:**
```bash
curl -s http://localhost:9222/json/version
```
Expect: `{"Browser": "Chrome/150.0.7871.46", ...}`

**3. Tell Hermes to use the running Chrome:**

Edit `~/.hermes/config.yaml`:
```yaml
browser:
  cdp_url: "http://127.0.0.1:9222"
```

Or set env var:
```bash
export BROWSER_CDP_URL="http://127.0.0.1:9222"
```

**4. Start a fresh session** (`/reset` or `/new`) so Hermes picks up the new config.

## Before / After

| | Before | After |
|---|---|---|
| Config | (empty or missing `browser.cdp_url`) | `browser.cdp_url: "http://127.0.0.1:9222"` |
| Chrome lifecycle | Hermes auto-launches → crashes | Manual background process → stable |
| Result | ❌ `Chrome exited early (exit code: 0)` | ✅ browser_navigate works |
| Running Chrome | Not needed (auto-launch fails anyway) | Always running on port 9222 |

## Notes

- Config `browser.cdp_url` is only read at session start. A running session ignores config changes.
- The env var `BROWSER_CDP_URL` is a live override but must be set before the Python process starts (or use `/browser connect` in CLI/TUI).
- This also works for cloud VPS / remote machines where you have a Chrome process running elsewhere.
