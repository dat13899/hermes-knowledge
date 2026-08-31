# SSE Progress Streaming (server → browser)

Show step-by-step processing status in a web UI without WebSockets. Used in voice-lab to display "transcribe → agent → tools → tts → done".

## Server (Node, plain http)

```js
// route handler
res.writeHead(200, {
  'Content-Type': 'text/event-stream; charset=utf-8',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'X-Accel-Buffering': 'no',   // disable nginx/proxy buffering
});
const sse = (event, data) => {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
};

try {
  sse('step', { id: 'agent', label: '🧠 Hermes đang suy nghĩ...' });
  // ... do work, emit more step events ...
  sse('done', { text: reply, audio, duration });
} catch (e) {
  sse('error', { error: String(e) });
}
res.end();
```

## Client (fetch + ReadableStream)

```js
const rr = await fetch('/api/voice/respond', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text, history }),
});
if (!rr.ok || !rr.body) throw new Error('bad stream');
const reader = rr.body.getReader();
const decoder = new TextDecoder();
let buffer = '', doneData = null;

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  let idx;
  while ((idx = buffer.indexOf('\n\n')) >= 0) {
    const raw = buffer.slice(0, idx);
    buffer = buffer.slice(idx + 2);
    let event = 'message', data = '';
    for (const line of raw.split('\n')) {
      if (line.startsWith('event: ')) event = line.slice(7).trim();
      else if (line.startsWith('data: ')) data += line.slice(6);
    }
    if (!data) continue;
    const parsed = JSON.parse(data);
    if (event === 'step') markStep(parsed.id, 'active');
    else if (event === 'done') doneData = parsed;
    else if (event === 'error') throw new Error(parsed.error);
  }
}
```

## UI step rendering (CSS classes)

```html
<div class="step" data-id="transcribe">📝 Nghe hiểu giọng nói (STT)</div>
```
```css
.step.active { color: var(--accent); }            /* ○ blinking */
.step.active .dot { animation: blink .8s steps(2) infinite; }
.step.done { color: var(--text); }                 /* ● filled gold */
.step.done .dot { background: var(--gold); }
.step.error { color: var(--danger); }
```

## Gotchas
- Events MUST be terminated with a blank line (`\n\n`) or the client's indexOf('\n\n') never fires.
- Don't buffer long: emit each `step` as soon as the phase starts, not at the end.
- If behind a reverse proxy (cloudflared/nginx), set `X-Accel-Buffering: no` — otherwise the stream arrives in one burst at the end.
