# CDP Screenshot Workflow — btdat.io.vn Mobile QA

## When needed
Taking mobile screenshots via browser_navigate or browser_vision fails for 3 reasons:
1. `browser_navigate` times out on 3D-heavy pages (WebGL rendering)
2. `browser_vision` depends on OmniRoute vision model which often returns 401/502
3. `browser_cdp` with `Page.captureScreenshot` returns base64 too large for output truncation (>1MB)

## Reliable workflow

### 1. Start Chrome with debug port + allow-origins
```bash
taskkill /f /im chrome.exe 2>/dev/null
# Must include --remote-allow-origins=* for WebSocket access from tools
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir=C:/Users/datel/chrome-debug \
  --no-first-run --no-default-browser-check \
  --remote-allow-origins=* \
  --window-size=1920,1080 \
  "https://btdat.io.vn/"
```

### 2. Capture via Python WebSocket + CDP
```python
import json, base64, websocket, subprocess, time

tabs_raw = subprocess.run(['curl','-s','http://localhost:9222/json'], capture_output=True, text=True).stdout
tabs = json.loads(tabs_raw)
page = [t for t in tabs if 'btdat.io.vn' in t.get('url','')][0]
ws = websocket.create_connection(page['webSocketDebuggerUrl'])

# iPhone 12 viewport
ws.send(json.dumps({'id':1,'method':'Emulation.setDeviceMetricsOverride',
    'params':{'width':390,'height':844,'deviceScaleFactor':3,'mobile':True}}))
ws.recv()

# Navigate
ws.send(json.dumps({'id':2,'method':'Page.navigate','params':{'url':'https://btdat.io.vn/utilities'}}))
ws.recv()
time.sleep(3)  # wait for WebGL + React render

# Screenshot — JPEG quality 20 keeps size ~30-50KB, avoids base64 truncation
ws.send(json.dumps({'id':3,'method':'Page.captureScreenshot','params':{'format':'jpeg','quality':20}}))
data = json.loads(ws.recv())
img = base64.b64decode(data['result']['data'])
with open('C:/Users/datel/Downloads/screenshot.jpeg','wb') as f: f.write(img)
ws.close()
```

### 3. Deliver via MEDIA path
```
MEDIA:C:/Users/datel/Downloads/screenshot.jpeg
```

## Pitfalls
- **PNG format with full resolution** → base64 >1MB → tool output gets truncated → invalid base64 decode. Always use JPEG quality 25-30.
- **Headless mode** (`--headless=new`) does NOT render WebGL properly — the 3D mesh appears as blank/garbled. Use GUI Chrome.
- **Missing `--remote-allow-origins=*`** → WebSocket handshake 403. This flag is MANDATORY.
- **Do NOT use `browser_vision` for btdat.io.vn** — it routes vision through OmniRoute which uses MiniMax models that return 401.
