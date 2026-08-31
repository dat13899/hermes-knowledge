# Archify — Full Per-type Field Reference & Starter Specs

Hard-won during a live session where 4 of 5 types failed schema validation on the first try. This is the **validated** contract (all 5 types rendered OK). Use these as starter specs; iterate via the CLI's `diagnostics[]`.

## Common base (all types)

```json
{
  "schema_version": 1,
  "diagram_type": "<type>",
  "meta": {
    "title": "My Diagram",
    "visual_preset": "classic"            // classic|signal-flow|blueprint|editorial
    // ,"animation": "trace"               // trace|none (omit for static)
    // ,"locale": "en"                     // en|zh-CN
  }
}
```

ID pattern: `^[a-zA-Z][a-zA-Z0-9_-]*$`. `from`/`to` must reference existing item ids.

---

## 1. architecture

Top-level: `components[]`, `connections[]`.

```json
{
  "schema_version": 1, "diagram_type": "architecture",
  "meta": { "title": "Web App" },
  "layout": { "mode": "grid", "cols": 4, "origin": [40, 80], "gapX": 30, "gapY": 40, "cellW": 130, "cellH": 64 },
  "components": [
    { "id": "client", "type": "frontend", "label": "Client", "row": 0, "col": 0 },
    { "id": "api", "type": "backend", "label": "API", "row": 0, "col": 1 },
    { "id": "db", "type": "database", "label": "Database", "row": 0, "col": 2 }
  ],
  "connections": [
    { "id": "c1", "from": "client", "to": "api", "label": "HTTPS" },
    { "id": "c2", "from": "api", "to": "db", "label": "SQL" }
  ]
}
```

- **component required:** `id, type, label`. Optional: `sublabel, tag, brand, sources[], row, col, pos, size`.
- **connection required:** `from, to`. Optional: `label, id, variant, fromSide, toSide, route (auto|straight|orthogonal-h|orthogonal-v), via[], labelAt, width`.
- `component.type` enum: `frontend, backend, database, cloud, security, messagebus, external`.
- **Gotcha:** with no `layout`, every component MUST have `pos:[x,y]` (and non-finite pos/size also fails). Easiest: `layout:{mode:"grid",cols:N}` + integer `row`/`col` per component. `pos` wins over `row`/`col` when both present. `row`/`col` are integers ≥ 0, `col` must be < `grid.cols`.

---

## 2. sequence

Top-level: `participants[]`, `messages[]`.

```json
{
  "schema_version": 1, "diagram_type": "sequence",
  "meta": { "title": "Cache Miss" },
  "participants": [
    { "id": "user", "type": "external", "label": "User" },
    { "id": "app", "type": "frontend", "label": "App" },
    { "id": "srv", "type": "backend", "label": "Server" }
  ],
  "messages": [
    { "id": "m1", "from": "user", "to": "app", "y": 160, "label": "request" },
    { "id": "m2", "from": "app", "to": "srv", "y": 210, "label": "GET /data" },
    { "id": "m3", "from": "srv", "to": "app", "y": 260, "label": "response" }
  ]
}
```

- **participant required:** `id, type, label` (`type` = component-type enum).
- **message required:** `from, to, y, label`. Optional: `id, variant (solid|dashed|emphasis|return), note`.
- **Gotcha:** message `y` (vertical position) **must be ≥ 160**. `60`/`110` fail with "must be >= 160". `meta.column_fit` optional (`fixed`|`spread`).

---

## 3. dataflow

Top-level: `stages[]`, `nodes[]`, `flows[]`. (**`additionalProperties:false` — no extra fields** on stages/nodes.)

```json
{
  "schema_version": 1, "diagram_type": "dataflow",
  "meta": { "title": "ETL" },
  "stages": [ { "label": "Ingest" }, { "label": "Transform" }, { "label": "Load" } ],
  "nodes": [
    { "id": "src", "label": "Source", "type": "external", "stage": 0, "row": 0 },
    { "id": "etl", "label": "ETL", "type": "backend", "stage": 1, "row": 1 },
    { "id": "ware", "label": "Warehouse", "type": "database", "stage": 2, "row": 2 }
  ],
  "flows": [
    { "id": "f1", "from": "src", "to": "etl", "label": "raw" },
    { "id": "f2", "from": "etl", "to": "ware", "label": "clean" }
  ]
}
```

- **stage required:** `label` **only** — do NOT add `id` (schema rejects it). Optional: `row`? (stage schema has just label; check schema).
- **node required:** `id, type, label, stage, row`. `stage`/`row` are **integers** (index into stages). Optional: `sublabel, tag, width, height, yOffset`.
- **flow required:** `from, to, label`. Optional: `id, classification, variant, route, fromSide, toSide, channelX, channelY, width`.
- **Gotcha:** extra props on stage/node → immediate schema failure (e.g. adding `id` to a stage).

---

## 4. workflow

Top-level: `lanes[]`, `nodes[]`, `edges[]` (+ optional `phases[]`, `groups[]`, `mainPath[]`, `semanticChecks`).

```json
{
  "schema_version": 1, "diagram_type": "workflow",
  "meta": { "title": "CI/CD" },
  "lanes": [ { "id": "dev", "label": "Dev" } ],
  "nodes": [
    { "id": "start", "label": "Start", "type": "backend", "lane": "dev", "col": 0 },
    { "id": "build", "label": "Build", "type": "backend", "lane": "dev", "col": 1 },
    { "id": "deploy", "label": "Deploy", "type": "cloud", "lane": "dev", "col": 2 }
  ],
  "edges": [
    { "id": "e1", "from": "start", "to": "build", "label": "commit" },
    { "id": "e2", "from": "build", "to": "deploy", "label": "artifact" }
  ]
}
```

- **lane required:** `id, label`. Optional: `variant`.
- **node required:** `id, lane, col, type, label`. `lane` = a lane id; `col` = integer column. Optional: `sublabel, tag, width, height, yOffset`.
- **edge required:** `from, to`. Optional: `id, label, variant, role, fromSide, toSide, route, via[], labelAt, width`.
- **phase required:** `id, label, fromCol, toCol`.
- `mainPath` items reference node ids.

---

## 5. lifecycle

Top-level: `lanes[]`, `states[]`, `transitions[]`.

```json
{
  "schema_version": 1, "diagram_type": "lifecycle",
  "meta": { "title": "Order" },
  "lanes": [ { "id": "main", "label": "System" } ],
  "states": [
    { "id": "pending", "type": "start", "label": "Pending", "lane": "main", "col": 0 },
    { "id": "running", "type": "active", "label": "Running", "lane": "main", "col": 1 },
    { "id": "done", "type": "success", "label": "Done", "lane": "main", "col": 2 }
  ],
  "transitions": [
    { "id": "t1", "from": "pending", "to": "running", "label": "start" },
    { "id": "t2", "from": "running", "to": "done", "label": "finish" }
  ]
}
```

- **lane required:** `id, label`.
- **state required:** `id, type, label, lane, col`. `lane` must reference a lane id; `col` integer. Optional: `sublabel, tag, step, width, height, yOffset`.
- **state `type` enum:** `start, active, waiting, decision, success, failure, neutral, external`. (`kind` is NOT a field — using `kind` fails.)
- **transition required:** `from, to`. Optional: `id, label, note, variant, route, fromSide, toSide, channelX, channelY, cornerRadius, labelAt`.
- **Gotcha:** a lane with `id:"main"` is **mandatory** (the phase rail). Using e.g. `sys` fails with "Lifecycle diagrams need a lane with id 'main'".

---

## Service endpoint reference (`~/diagram-service`, port 3100)

| Method & path | Body | Returns |
|---------------|------|---------|
| `POST /api/diagram` | `{type, spec}` | 201 `{ok, id, url:"/diagram/<id>", artifact:{sha256,bytes}, output}` |
| `POST /api/diagram/preview` | `{type, spec}` | 200 same shape, id=`preview`, writes fixed `preview.html` (does not grow data dir) |
| `GET /diagram/<id>` | — | streams `data/<id>.html` |
| `GET /diagram/preview` | — | streams `preview.html` |
| `GET /` | — | builder `index.html` |
| `GET /builder.css`, `/builder.js` | — | static assets |
| `GET /health` | — | `{ok, uptime}` |

- 422 bodies carry `diagnostics[]` from the Archify repair receipt.
- `data/` holds `<id>.json`, `<id>.html`, `<id>.meta.json` per saved diagram.

## Builder UI (3-column, `public/`)
- Left: visual form per type (metadata + item lists with `+ Add`/`✕`). Type-specific fields; `addItem` injects schema-valid defaults.
- Middle: in visual mode a **live read-only JSON mirror**; in JSON mode an editable textarea (parse-on-input re-renders preview).
- Right: live preview iframe → `/diagram/preview?ts=<n>` (debounced 350ms via `/api/diagram/preview`).
- Header: type tabs (5), mode toggle (Trực quan/JSON), `↺ Mới`, `Copy JSON`, `💾 Lưu` (→ `POST /api/diagram`), `Generate ⚡`.
