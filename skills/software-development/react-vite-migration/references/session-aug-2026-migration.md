# Session: Full React + Vite Migration (July 2026)

## Context

Migrated `btdat.io.vn` — a Node.js Express static-file server serving ~7,100 lines of vanilla HTML/Bulma — to React 19 + Vite 6 + React Router 7.

## Project structure evolved

```
service-dashboard/
├── server.js              ← kept unchanged (+ SPA fallback)
├── dist/                  ← Vite build output
├── frontend/
│   ├── src/
│   │   ├── components/    Navbar, BlobBackground, ConfirmModal
│   │   ├── hooks/         useTheme, useToast, useSSE, useDocuments
│   │   ├── pages/         HomePage, DashboardPage, DocumentsPage,
│   │   │                  UtilitiesPage, WidgetPage, HermesPage
│   │   │   ├── docs/      DocSidebar, DocReader, DocEditor
│   │   │   └── widgets/   RandomDiscovery, DiceRoller, CoinFlip, etc.
│   │   ├── services/      api.js (36 endpoints)
│   │   ├── App.jsx        6 routes
│   │   └── main.jsx       Vite entry
│   ├── index.html
│   ├── vite.config.js     proxy /api → :3000
│   └── package.json
├── public/               ← preserved: old HTML + hermes-standalone.html
└── .gitignore
```

## Key numbers

- **6 React pages** built
- **69 modules** in production build
- **308 KB** main bundle (gzipped: 92 KB) + **12 lazy chunks** (~2-5 KB each)
- **0 build errors**
- **36 API endpoints** consumed
- **Old HTML preserved** — all original `.html` files still accessible
- **26 missing features identified post-migration** across 4 pages (HomePage, DashboardPage, DocumentsPage, WidgetPage)

## Feature drift post-migration (critical lesson)

Subagents built working React components from API specs + design specs, but missed 30-50% of interactive UX features from the original HTML:

### HomePage misses
- Status bar (running/stopped/uptime count) — fixed in v2
- Tech stack badges with hover — fixed in v2
- Contact section + footer with cache clear — fixed in v2
- Anchor nav links (#services, #stack, #contact) — fixed in v2

### DashboardPage misses
- Stats bar (running/stopped/error count cards) — fixed in v2
- Auto-restart badge (↻ auto) — fixed in v2
- Clickable port links (opens localhost:N) — fixed in v2
- 24h timeline chart in expanded details — already had this

### DocumentsPage misses (17 features)
- Search history (localStorage) + full-text search dropdown — missing
- Sort bar (newest/oldest/A→Z) — missing
- Draft filter checkbox — missing
- Bulk delete with checkboxes — missing
- Font size controls (A+/A-) — missing
- Markdown toolbar (Bold/Italic/Heading/Link/Code/List) — missing
- Print button — missing
- Download as .md — missing
- Export PDF button — missing
- Reading progress bar — missing
- Word count — missing
- Inline rename (double-click title) — missing
- Templates for new doc (Article/Report/Note) — missing
- New doc modal with title/tags/template/content — missing
- Drag-and-drop .docx upload — missing
- Cache clear button — missing
- Dynamic tag filter (from actual doc tags, not hardcoded) — missing

### WidgetPage misses (17/28 panels)
Had: random, dice, coin, number, password, palette, gradient, activity, 8ball, braindump, games (11)
Missing: food, bmi, calendar, cards, challenge, convert, countdown, counter, emoji, guess, history, idea, list, mood, pomodoro, rps, tarot, textgen, van, workout (20)

### Root cause
Subagent context only included API spec + design patterns, NOT the full original HTML file. The subagent had zero visibility into what interactive features existed in the original page and therefore couldn't replicate them.

### Fix strategy
Dispatched 2 subagents in parallel to fix DocumentsPage (add 17 features) and WidgetPage (add 20 widgets). Fixed HomePage and DashboardPage directly (smaller diffs).

## Deploy pattern

```bash
cd frontend && npm run build    # → dist/
# server.js SPA fallback serves dist/index.html for SPA routes
# Old public/*.html still served directly
```

## Routes built

| Route | Page | Size (JS) |
|---|---|---|
| `/` | HomePage — hero, typing effect, service cards | main bundle |
| `/dashboard` | Dashboard — 4 tabs, SSE logs, CRUD modals | main bundle |
| `/documents` | Documents — sidebar, reader, editor, auto-save | main bundle |
| `/utilities` | Utilities — YouTube audio player + timer | main bundle |
| `/random-widget` | Widget grid → detail view, 11 mini apps | 12 lazy chunks |
| `/hermes` | Canvas wrapper via iframe | main bundle |

## Tools used

- **delegate_task** with 2 parallel subagents for DocumentsPage and WidgetPage
- Direct file writes for smaller pages (UtilitiesPage, HermesPage)
- **server.js** patched twice for SPA fallback routing
- **hermes-standalone.html** — stripped-down canvas page for iframe embed
