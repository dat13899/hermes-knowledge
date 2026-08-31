# OmniRoute chat helper (Node.js) — production-verified 2026-08-30

Built for `diagram.btdat.io.vn` (Archify AI builder at `~/diagram-service/llm.js`).
Calls `http://localhost:20128/v1/chat/completions` from a plain Node `http`
service to turn a natural-language system description into an Archify diagram
JSON. This is the pattern to reuse; every pitfall below was hit and fixed.

## The `chat()` helper

```js
const http = require('http');
const OMNI = { host: '127.0.0.1', port: 20128, path: '/v1/chat/completions', method: 'POST' }; // <-- method is CRITICAL
const LLM_MODEL = process.env.DIAGRAM_LLM_MODEL || 'command-code/deepseek/deepseek-v4-flash-vision-exp';

function chat(model, messages, opts = {}) {
  return new Promise((resolve) => {
    const body = JSON.stringify({ model, messages, max_tokens: opts.max_tokens || 8000, stream: true }); // no temperature for reasoning models
    const req = http.request({ ...OMNI, headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) } }, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        let content = '';
        for (const line of data.split('\n')) {
          if (!line.startsWith('data:')) continue;            // skip non-data + ": x-omniroute-*" passthrough
          const payload = line.slice(5).trim();
          if (!payload || payload === '[DONE]') continue;
          try { const j = JSON.parse(payload); const d = j.choices?.[0]?.delta?.content; if (typeof d === 'string') content += d; } catch (e) {}
        }
        if (content) return resolve({ ok: true, content });
        try { const j = JSON.parse(data); return resolve({ ok: true, content: j?.choices?.[0]?.message?.content || '' }); }
        catch (e) { return resolve({ ok: false, error: 'parse_failed', raw: data.slice(0, 250) }); }
      });
    });
    req.on('error', (e) => resolve({ ok: false, error: e.message }));
    req.write(body); req.end();
  });
}
```

## `extractJSON()` — tolerant parser

```js
function extractJSON(text) {
  if (!text) return null;
  let t = text.trim();
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i);   // strip ```json fences
  if (fence) t = fence[1].trim();
  const s = t.indexOf('{'), e = t.lastIndexOf('}');
  if (s === -1 || e === -1 || e <= s) return null;
  try { return JSON.parse(t.slice(s, e + 1)); } catch (err) { return null; }
}
```

## Coercions to apply after parse (models are sloppy)

- `schema_version` is often returned as a string `"1.0"` — coerce to int:
  `Number(String(v).replace(/\..+$/, '')) || 1`.
- Force `spec.diagram_type = typeHint` when the user picked a type.
- For `architecture`: LLM tends to put every component on `row:0` (one line),
  which makes connections cross unrelated nodes and trips Archify's
  `edge-through-node` + `label overlaps component` layout checks. Run a
  BFS-layer auto-layout (see below).

## Auto-layout so Archify passes validation

Archify's grid layout requires every architecture component to have integer
`row`/`col`, and it rejects layouts where an edge crosses an unrelated
component ("clean-flow/edge-through-node") or a label sits on a box. A
BFS-layered layout (sources → row 0, their targets → row 1, ...) avoids
crossing; offset labels so they clear the boxes.

```js
function autoLayoutArchitecture(spec) {
  const comps = spec.components || [], conns = spec.connections || [];
  const targets = new Set(conns.map(c => c.to).filter(Boolean));
  const sources = comps.map(c => c.id).filter(id => !targets.has(id));
  const layer = {}, queue = [...sources];
  sources.forEach(s => layer[s] = 0);
  while (queue.length) { const cur = queue.shift(); for (const c of conns)
    if (c.from === cur && layer[c.to] === undefined) { layer[c.to] = layer[cur] + 1; queue.push(c.to); } }
  comps.forEach(c => { if (layer[c.id] === undefined) layer[c.id] = 0; });
  const byLayer = {};
  comps.forEach(c => { const l = layer[c.id] ?? 0; (byLayer[l] = byLayer[l] || []).push(c); });
  let maxCol = 0;
  Object.entries(byLayer).forEach(([l, list]) => { list.forEach((c, i) => { c.row = Number(l); c.col = i; }); maxCol = Math.max(maxCol, list.length); });
  spec.layout = { mode: 'grid', cols: Math.max(3, maxCol + 1), origin: [40, 80], gapX: 40, gapY: 40, cellW: 150, cellH: 64 };
  conns.forEach(c => { const f = comps.find(x => x.id === c.from), t = comps.find(x => x.id === c.to);
    if (f && t && f.row !== t.row) { c.labelDx = c.labelDx ?? 14; c.labelDy = c.labelDy ?? 26; }
    else if (f && t && f.col !== t.col) { c.labelDy = c.labelDy ?? -14; } });
}
```

## Model choice

- `deepseek-v4-flash` = thinking model; returns `content: ""` and puts the
  answer in `reasoning_content` when its reasoning budget is burned. Unreliable
  for direct-answer generation.
- `deepseek-v4-flash-vision-exp` = returns `content` directly; use THIS for
  JSON-generation / diagram-authoring tasks.

## Fallback

If the gateway is down, fall back to a hand-built template so the caller never
dead-ends. For architecture, generate `n` components (`c1..cn`) with a `grid`
layout and `c{i}->c{i+1}` links.
