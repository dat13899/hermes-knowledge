# Archify AI diagram service — architecture & per-type schema contracts

Session 2026-08-30. Outcome: live service at `https://diagram.btdat.io.vn/`
(`~/diagram-service/server.js`, port 3100, zero-dep Node `http`). It accepts a
natural-language description, calls the OmniRoute LLM (`/api/generate`), gets an
Archify JSON, renders it via the Archify skill CLI, and serves the interactive
HTML at `/diagram/<id>`. The builder frontend is 3 panes: describe → JSON →
preview.

## The API surface

- `POST /api/diagram` `{type?, spec}` → `{ok, id, url}` (persists a real diagram).
- `POST /api/diagram/preview` `{type?, spec}` → renders to a fixed
  `data/preview.html` (does NOT fill the data dir). Used for live preview.
- `POST /api/generate` `{description, type?}` → LLM → Archify JSON → render to
  preview. Returns `{ok, type, id, spec, url, preview}`.
- `GET /diagram/<id>` → the interactive HTML.
- `GET /` → the builder UI (served from `public/index.html`).

## Archify CLI invocation (from the service)

`spawnSync('node', [ ARCHIFY_DIR/bin/archify.mjs, 'deliver', type, inJsonPath, outHtmlPath ])`.
The validation is EXPENSIVE and strict — an invalid spec returns a rich
diagnostic JSON (repair receipt). Use `validate <type> <in.json> --json` first to
get `{ok, diagnostics}` and surface `diagnostics[].message` to the user.

## Per-type schema contracts (the strict bits that trip validation)

- **architecture**: needs `layout: {mode:'grid', cols, origin, gapX, gapY, cellW, cellH}`
  AND every component with integer `row`/`col`. If layout omitted, components
  must each carry `pos:[x,y]`. Connections must reference existing component ids
  in `from`/`to`. Watch `edge-through-node` (edge crossing an unrelated
  component) and `label overlaps component` — fix via layered layout + labelDx/labelDy.
- **sequence**: participants need `{id,type,label}`; messages need
  `{from,to,y,label}` where `y` is a number **>= 160 and strictly increasing**
  (160, 210, 260...). No `y` = validation error.
- **dataflow**: `stages` is an array of `{label}` ONLY (no `id`, and the schema is
  `additionalProperties:false` so extra fields fail). `nodes` need
  `{id,type,label,stage,row}` where `stage` is the integer index into `stages`.
  `flows` need `{from,to,label}`.
- **workflow**: top-level requires `lanes`, `nodes`, `edges`. `nodes` need
  `{id,lane,col,type,label}` (lane must be an existing lane id, col integer). `edges`
  need `{from,to}`.
- **lifecycle**: MUST include a lane with `id:"main"` (the phase rail). `states`
  need `{id,type,label,lane,col}` where `type` is one of
  `start|active|waiting|decision|success|failure|neutral|external`. `transitions`
  need `{from,to}`.

## Builder defaults (valid + renderable)

Every diagram type's default spec should ship with 3 sample items so the preview
renders immediately. Use `layout:{mode:'grid',cols:4}` for architecture with
`row`/`col` on each component; lane `id:"main"` for lifecycle; `y:160,210,260`
for sequence messages.

## Exposing over Cloudflare Tunnel (the exact steps)

1. `nslookup diagram.btdat.io.vn` → must resolve (record exists).
2. Add ingress to `C:\Users\datel\.cloudflared\config.yml` before the
   `http_status:404` fallback:
   `- hostname: diagram.btdat.io.vn\n    service: http://localhost:3100`.
3. DNS: CNAME `diagram` → `<tunnel-uuid>.cfargotunnel.com`, Proxied.
4. Restart cloudflared: `tasklist | grep -i cloudflared` to find PID, then
   `taskkill /F /IM cloudflared.exe` and relaunch
   `cloudflared tunnel --config .../config.yml run` as a **background** process.
   (Node service also restarts via `node server.js` background.)

## Gotcha: `node -c` (syntax check) is a great pre-restart gate

After editing `server.js`/`llm.js`/`builder.js`, run `node -c <file>` before
restarting the background service. Cheap way to catch a syntax error so the
long-running service never goes down silently.
