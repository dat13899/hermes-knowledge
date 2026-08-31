---
name: archify-diagrams
description: "Author and self-host Archify diagrams (5 types)."
---

# Archify Diagrams — Authoring & Self-Hosting

Archify (github.com/tt-a1i/archify, ~32k★) is an agent skill that turns a **typed JSON IR** into a **deterministically-compiled, self-contained interactive HTML/SVG diagram**. Unlike hand-drawn SVG, the agent writes JSON nodes/relations; Archify validates + lays out + renders them. No auto-layout guesswork: you control hierarchy, spacing, and routes.

## When to use
- You need a professional, verifiable diagram to demo/present (5 types: architecture, workflow, sequence, dataflow, lifecycle).
- You need interactive features (focus, route probe, role compare), dark/light theme, motion, or PNG/JPEG/WebP/SVG/WebM export + a 1200×630 share card.
- You want **schema + layout + SVG validation** before an artifact replaces "last known good" (atomic validation, `before/delta/after` diffs).
- You're serving a persistent diagram service at `diagram.btdat.io.vn/<id>`.

## Installed layout (this machine)
- Repo (upstream, read-only): `C:/Users/datel/AppData/Local/hermes/skills/archify/` — SKILL.md at its root, renderers in `renderers/<type>/`, schemas in `schemas/<type>.schema.json`, examples in `examples/*.json`. **Treat as upstream — patch YOUR umbrella, not upstream.**
- Node required (v24 present). `npm install` already done.
- CLI entrypoint: `node bin/archify.mjs`.

## CLI workflow
```
cd .../skills/archify
node bin/archify.mjs doctor                        # verify core template, 5 renderers, schema validators
node bin/archify.mjs validate architecture input.json --json    # schema+layout+SVG validation
node bin/archify.mjs deliver architecture input.json out.html    # validate + render, prints sha256 receipt
node bin/archify.mjs check out.html                # post-render structural check
node bin/archify.mjs visual-check out.html --json  # needs a real browser; browser_exec blocks localhost
```
- `deliver` writes the html AND prints an `artifact: {sha256, bytes}` receipt. `validate` on an invalid spec prints a **repair receipt** with `diagnostics[]` (code/severity/message/evidence) — render machine-readable 422 bodies from this.
- Input path can be absolute. `spawnSync` from Node (service) works; `cwd` = skill root.

## The JSON schema contract — per type (the part you WILL get wrong)

This is the hard-won, validated contract. Each type has a `schema_version:1`, `diagram_type:<type>`, and `meta` (min `title`; optional `visual_preset` [classic|signal-flow|blueprint|editorial], `animation` [trace|none], `locale`).

| Type | Required arrays | Per-item `required` fields | Gotchas |
|------|----------------|----------------------------|---------|
| **architecture** | `components`, `connections` | component: `id,type,label`; connection: `from,to` | **Needs `layout:{mode:"grid",cols:N}` OR each component with `pos:[x,y]`.** Grid mode: component needs integer `row`+`col` (else "must include pos"); pos wins over row/col. component `type` enum: `frontend,backend,database,cloud,security,messagebus,external` |
| **sequence** | `participants`, `messages` | participant: `id,type,label`; message: `from,to,y,label` | Message **`y` must be ≥160** (vertical position) — 60 fails "must be >= 160". Participants share the component-type enum. |
| **dataflow** | `stages`, `nodes`, `flows` | stage: `label` only (NO id); node: `id,type,label,stage,row`; flow: `from,to,label` | **`additionalProperties:false`** — extra fields on stages/nodes reject (e.g. stage `id` is forbidden). `stage`/`row` are integers. |
| **workflow** | `lanes`, `nodes`, `edges` (+ optional `phases`) | lane: `id,label`; node: `id,lane,col,type,label`; edge: `from,to` | **node/lane/col reference**: node needs `lane` (→ a lane id) and `col` (integer). Lane ids are your bridges. |
| **lifecycle** | `lanes`, `states`, `transitions` | lane: `id,label`; state: `id,type,label,lane,col`; transition: `from,to` | **A lane with `id:"main"` is mandatory** (the phase rail) — a lane `sys` fails "need a lane with id main". State `type` enum: `start,active,waiting,decision,success,failure,neutral,external`. `lane`/`col` required on every state. |

**Universal helpers:** id pattern `^[a-zA-Z][a-zA-Z0-9_-]*$`. Connection/transition ids optional. `from`/`to` must reference existing item ids.

**Bottom line:** when a type's render fails, read the `diagnostics[]` — it names the exact missing property + the enum allowed. Iterate from there; don't guess.

## Self-hosting service (this machine)
A zero-dep Node service (`~/diagram-service/server.js`, port **3100**) wraps the CLI:
- `POST /api/diagram` — `{type, spec}` → validates via CLI → persists `data/<id>.{json,html,meta.json}` → returns `{id, url:"/diagram/<id>", artifact:{sha256,bytes}}`. 422 body carries `diagnostics[]`.
- `POST /api/diagram/preview` — same but **renders to a fixed `preview.html`, does NOT grow the data dir** (used by the builder's live preview/debounce).
- `GET /diagram/<id>` and `GET /diagram/preview` — stream the html.
- `GET /` and `/builder.css`, `/builder.js` — the 3-column builder UI (visual form + live JSON mirror + live preview iframe).
- Static files in `public/`; `serveStatic` whitelists `.css`/`.js`, `allowHtml` only for `index.html`.

Serving is via Cloudflare named tunnel: ingress `diagram.btdat.io.vn -> localhost:3100` in `~/.cloudflared/config.yml`, DNS CNAME `diagram -> <tunnel-id>.cfargotunnel.com`. Service + tunnel are background processes; both need restarting if the machine boots.

## Pitfalls
- **`crypto.randomBytes(n).toString('base36')` throws "Unknown encoding"** in Node — use `.toString('hex')` and slice.
- **`hermes config set` cannot index list elements** (`custom_providers[0].x`) — it creates a stray top-level key. Edit the YAML directly, or use dotted `providers.<slug>.x` paths (those work).
- **`/api/models` `available=true` is unreliable** for OmniRoute — a model can be plan-blocked at request time (403 MODEL_NOT_IN_PLAN) despite "available". Probe for real only when it matters.
- **Chrome headless screenshot on this machine:** works with `--headless --disable-gpu --hide-scrollbars --run-all-compositor-stages-before-draw --window-size=WxH --screenshot=C:/.../out.png <url>`; the plain `--screenshot`/`--virtual-time-budget` combo can silently produce no file. `browser_exec` refuses localhost. Vision on the resulting PNG may report "can't view images" if the active model lacks vision.
- **Service restart counts as a separate background process each time** — keep only the newest alive; kill the old session id.

See `references/archify-schema-and-service.md` for the full per-item field tables + a copy-paste starter spec for each of the 5 types.
