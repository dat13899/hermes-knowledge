# services.json Schema & Session Detail

## services.json Schema

```json
[
  {
    "id": "aterbot",
    "name": "AFK Bot",
    "description": "Minecraft AFK bot — tự động reconnect, tránh idle kick",
    "dir": "C:\\Users\\datel\\aterbot",
    "command": "cmd.exe /c npm start",
    "port": 5500
  }
]
```

### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | yes | string | Unique identifier, used in API paths (lowercase, hyphens) |
| `name` | yes | string | Display name on card in dashboard |
| `description` | yes | string | Card subtitle, shown below name |
| `dir` | yes | string | Absolute working directory for the spawned process |
| `command` | yes | string | Command to run. On Windows, prefix with `cmd.exe /c` for npm/npx |
| `port` | no | number | Port the service listens on — shown in card, used for display only |

## SSE Implementation (from session)

From the built dashboard (C:\Users\datel\service-dashboard):

**Backend SSE handler:**

```js
function sseSubscribe(res, filterId) {
  const target = filterId ? S.get(filterId) : S.get('__all__');
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'Access-Control-Allow-Origin': '*',
  });
  res.write(`event: connected\ndata: {}\n\n`);

  const cb = (entry, id) => {
    if (!res.writableEnded) {
      res.write(`id: ${entry.ts}\nevent: log\ndata: ${JSON.stringify({serviceId: id, line: entry.line, ts: entry.ts})}\n\n`);
    }
  };
  target.sseClients.add(cb);

  // Flush existing logs on connect
  if (filterId) {
    const st = S.get(filterId);
    if (st) for (const e of st.logs) sseSend(res, filterId, e);
  }

  res.on('close', () => { target.sseClients.delete(cb); });
}
```

**Frontend EventSource:**

```js
const evtSource = new EventSource('/api/logs/stream');

evtSource.addEventListener('log', (e) => {
  const { serviceId, line, ts } = JSON.parse(e.data);
  // Append to service's log buffer and render if selected
});

evtSource.onerror = () => {
  setTimeout(connectSSE, 2000); // auto-reconnect
};
```

Key: SSE auto-reconnects per spec — `onerror` handler just re-inits.

## Process Log State (ring buffer)

```js
const LOG_MAX = 3000;
function addLog(id, line) {
  const st = S.get(id);
  const entry = { ts: Date.now(), line: String(line) };
  st.logs.push(entry);
  if (st.logs.length > LOG_MAX) {
    st.logs.splice(0, st.logs.length - LOG_MAX);
  }
  // broadcast to SSE clients
  for (const cb of st.sseClients) {
    try { cb(entry, id); } catch (_) {}
  }
}
```

## Testing Commands (from session)

```bash
# Start dashboard
cd /c/Users/datel/service-dashboard && node server.js

# Test API
curl -s http://localhost:3000/api/services
curl -s -X POST http://localhost:3000/api/services/aterbot/start
curl -s -X POST http://localhost:3000/api/services/aterbot/stop
curl -s "http://localhost:3000/api/services/aterbot/logs?lines=50"

# Test SSE
curl -sN --max-time 3 http://localhost:3000/api/logs/stream
```
