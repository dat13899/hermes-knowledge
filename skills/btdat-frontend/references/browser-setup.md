# Chrome Remote Debugging Setup for Hermes

## Why
Hermes `browser_navigate`, `browser_console`, `browser_snapshot`, and `browser_vision` tools need a CDP (Chrome DevTools Protocol) endpoint. Chrome must run with `--remote-debugging-port=9222`.

## First-time Setup
Chrome's default profile may refuse debug mode. Use a dedicated profile:
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\datel\chrome-debug" --no-first-run --no-default-browser-check
```

## Daily Workflow

### Start (every time Chrome was closed)
```bash
# Kill any existing Chrome
taskkill /F /IM chrome.exe

# Launch with debug port
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\datel\chrome-debug"
```

### Verify
```bash
curl -s http://127.0.0.1:9222/json/version
# Should return JSON with webSocketDebuggerUrl
```

### Hermes tools then work
```
browser_navigate("https://btdat.io.vn/")   # load page
browser_console(expression="...")            # run JS
browser_snapshot(full=true)                  # full DOM tree
browser_vision(...)                          # screenshot
browser_cdp(method="Page.reload")            # raw CDP
```

## Troubleshooting

### Port 9222 not open after launch
- Chrome may have crashed silently. Check `tasklist | grep chrome` returns processes.
- Chrome background processes from previous session must die: `taskkill /F /IM chrome.exe` before launching.
- The `--user-data-dir` flag is essential — without it, Chrome may ignore `--remote-debugging-port` when the default profile is locked.

### "Blocked: URL targets a private or internal address"
- Hermes gateway blocks `browser_navigate` to localhost/127.0.0.1.
- Use the public URL: `https://btdat.io.vn/` or `http://<lan-ip>:5173/` for dev.
- Only `browser_cdp` can reach localhost directly.

### Model has no vision
- `browser_vision` saves a screenshot but the current model may not analyze it.
- Fall back to `browser_console` for DOM checks + `browser_snapshot` for accessibility tree.
- To get true visual analysis, switch to a vision model (GPT-4o, Claude Sonnet, Gemini).

## Live Browser Checklist (run after deploy)
```js
// 1. SVG logo renders
document.querySelector('nav svg rect')  // should exist, fill: url(#lg)

// 2. Footer dock position
getComputedStyle(document.querySelector('.glass-dock')).bottom  // "24px"

// 3. Back-to-top above dock
var bt = document.querySelector('[aria-label="Back to top"]');
bt ? getComputedStyle(bt).bottom : 'N/A'  // "64px"

// 4. Hamburger not inline-hidden
document.querySelector('.hamburger-btn').style.display  // "" (empty = CSS controls)
getComputedStyle(document.querySelector('.hamburger-btn')).display  // "none" on desktop (correct)

// 5. Fixed elements z-index map
[].map.call(document.querySelectorAll('*'), el => {
  var s = getComputedStyle(el);
  return s.position === 'fixed' ? {tag: el.tagName, z: s.zIndex, bottom: s.bottom} : null;
}).filter(Boolean)
```
