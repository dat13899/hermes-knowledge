# btdat.io.vn Dashboard — Full-Stack Code Audit (Reference)

**Date:** 2026-07-28
**Project:** service-dashboard (Node.js + React 19 + Vite)
**Files reviewed:** server.js (793 lines), frontend/ (~30 files), public/, services.json, package.json, .gitignore, DESIGN.md

## Project Layout

```
service-dashboard/
├── server.js              ← Node HTTP server (monolithic, 793 lines)
├── package.json           ← No dependencies (pure Node built-ins)
├── services.json          ← Config: 3 services (AFK Bot, RAG, Aternos)
├── .gitignore
├── public/                ← Legacy vanilla HTML dashboard (15 files)
│   ├── dashboard.html
│   ├── documents.html
│   └── assets/global.css  ← Theme system (dark + light)
├── frontend/              ← React 19 SPA (Vite + Motion)
│   ├── src/
│   │   ├── App.jsx             ← Lazy-loaded routes
│   │   ├── pages/              ← DashboardPage, HomePage, DocumentsPage...
│   │   ├── components/         ← Navbar, CommandPalette, ui/, shared/, layout/
│   │   ├── hooks/              ← useDocuments, useHaptic, useMediaQuery
│   │   └── services/api.js     ← API client (fetch wrapper)
│   └── vite.config.js
└── dist/                  ← Build destination
```

## Key Findings (summary)

| Severity | Finding | Location |
|----------|---------|----------|
| 🔴 P0 | Command injection — YouTube URL in shell string | server.js:641 |
| 🔴 P0 | execSync blocking event loop in HTTP handler | server.js:29,91,245,253,641 |
| 🟡 P1 | Monolithic 793-line server.js | server.js:all |
| 🟡 P1 | No auth, no rate limiting, proxy to any local port | server.js:386-391 |
| 🟡 P1 | Path traversal — file listing unbounded | server.js:383 |
| 🟡 P1 | Race condition — global `_ytStream` singleton | server.js:635 |
| 🟡 P1 | SSE no cleanup on client disconnect | server.js:256-268 |
| 🟡 P1 | useDocuments dependency cycle (fetchDoc depends on docs) | frontend |
| 🟡 P1 | .gitignore ignores all root JSON (including lockfile) | .gitignore |
| 🟡 P2 | Dual UI systems (legacy public/ + React frontend/) | project root |
| 🟢 P3 | Hardcoded LibreOffice path | server.js:7 |
| ✅ | Lazy loading pages | App.jsx |
| ✅ | ErrorBoundary with fallback UI | ErrorBoundary.jsx |
| ✅ | Toast via Context API | Toast.jsx |
| ✅ | Dark/light theme system | global.css |
| ✅ | Cache with TTL for netstat/resources | server.js:23-48,87-96 |

## Full Output

See conversation session `@session:default/<session-id>` for the complete formatted review delivered to the user.
