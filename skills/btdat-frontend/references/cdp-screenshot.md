# CDP Chrome Screenshot — Quick Reference

## Start Chrome with CDP
```
taskkill /f /im chrome.exe 2>/dev/null
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:/Users/datel/chrome-debug --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1920,1080 "URL"
```

Then verify: `curl -s http://localhost:9222/json/version`

## Python CDP Screenshot (mobile iPhone 12)
```python
import json, base64, websocket, subprocess, time

tabs = json.loads(subprocess.run(['curl','-s','http://localhost:9222/json'], capture_output=True, text=True).stdout)
page = [t for t in tabs if 'btdat.io.vn' in t.get('url','')][0]
ws_url = page['webSocketDebuggerUrl']
ws = websocket.create_connection(ws_url)

# iPhone 12
ws.send(json.dumps({'id':1,'method':'Emulation.setDeviceMetricsOverride',
    'params':{'width':390,'height':844,'deviceScaleFactor':3,'mobile':True}}))
json.loads(ws.recv())

# Navigate
ws.send(json.dumps({'id':2,'method':'Page.navigate','params':{'url':'https://btdat.io.vn/TARGET_PAGE'}}))
json.loads(ws.recv())
time.sleep(3)

# Screenshot JPEG (small, won't truncate)
ws.send(json.dumps({'id':3,'method':'Page.captureScreenshot','params':{'format':'jpeg','quality':25}}))
data = json.loads(ws.recv())
img = base64.b64decode(data['result']['data'])
with open('C:/Users/datel/Downloads/btdat-TARGET-mobile.jpeg','wb') as f: f.write(img)

ws.close()
```

## Sharing: MEDIA: path
Use `MEDIA:C:/Users/datel/Downloads/btdat-xxx-mobile.jpeg` to send inline (not as file attachment).

## Common failures
- **PNG > 1MB base64 truncated**: always use JPEG quality=25-30
- **403 WebSocket**: must use `--remote-allow-origins=*` flag
- **Headless no WebGL**: 3D/Three.js pages look broken — use non-headless Chrome (omit `--headless`)
- **browser_vision tool**: NEVER use — routes through OmniRoute MiniMax-M3 vision which returns 401
