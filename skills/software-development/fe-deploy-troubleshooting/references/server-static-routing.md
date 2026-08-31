# Server.js static file routing map

## Directory layout

| Dir | Path | Served via | URL pattern |
|---|---|---|---|
| `PUBLIC_DIR` | `service-dashboard/public/` | Direct static serve (line 882-886) | Any path → `public/<path>` |
| `DOCS_DIR` | `C:\Users\datel\documents\` | API-only (`/api/documents/*`) | API endpoints, not direct-serve |
| `dist/` | `service-dashboard/dist/` | React SPA build | SPA fallback (line 889-894) |

## Routing priority (top to bottom, first match wins)

1. **API routes** — `/api/*`, `/proxy/*` → handler functions
2. **SPA route list** (line 731) — `/`, `/dashboard`, `/documents`, `/documents/`, `/utilities`, `/widgets`, `/hermes`, `/ts7/voice`, `/ts7/*` → serve `dist/index.html` (React SPA)
3. **`/assets/*` in dist** (line 749) → `dist/assets/<path>` with immutable cache
4. **`PUBLIC_DIR` static** (line 882-886) — `public/<path>` → serve if file exists
5. **SPA fallback** (line 889-894) — any path without extension and not `/api/` → `dist/index.html`
6. **File not found** → 404

## Critical pitfall: `/documents/*` is SPA, not static

Route `/documents/vtts/` matches line 731 (`/documents/` prefix) → React SPA is served, NOT the file in `dist/documents/`. Any `dist/documents/` subdirectory is invisible to direct HTTP access.

## Hosting a plain HTML file (no React build)

**Correct way:** Copy to `PUBLIC_DIR`:
```bash
cp file.html /c/Users/datel/service-dashboard/public/name.html
# URL: https://btdat.io.vn/name.html
```

**Wrong way (will serve SPA instead):**
- `dist/documents/sub/index.html` → `/documents/sub/` → SPA fallback
- Any path matching the SPA route list → SPA

## Uploading documents via API (for .md/.docx)

Use `DOCS_DIR` (the `C:\Users\datel\documents\` folder) which is accessed exclusively through `/api/documents/*` endpoints:
- `GET /api/documents` — list all .md/.docx files
- `GET /api/documents/<name>` — read content
- `POST /api/documents` — write new
- These are NOT directly served at `/documents/<name>` — the SPA renders that URL instead
