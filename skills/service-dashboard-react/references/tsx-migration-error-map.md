# TSX Migration Error Map — src/pages/ (tsc audit 2026-08-02)

Full `npx tsc --noEmit` audit of the .jsx → .tsx migration for the service-dashboard frontend.
146 errors total, **ALL under `src/pages/`** (zero elsewhere). Run the audit with:
`cd C:/Users/datel/service-dashboard/frontend && npx tsc --noEmit 2>&1 | tee /tmp/tsc_errors.txt`

## Error count by file
| File | Errors | Cause |
|---|---|---|
| pages/docs/DocSidebar.tsx | 24 | defaulted props infer `() => void`; `s` style objects not typed `CSSProperties`; `e.style` on EventTarget; unknown in `key`/children |
| pages/HomePage.tsx | 17 | ALL `ease: 'steps(N)'` TS2322 (see fix 1) |
| pages/docs/DocReader.tsx | 17 | `window.marked`; `s` style objects; prop name mismatch |
| pages/docs/DocEditor.tsx | 13 | `window.marked`; `s` style objects; `e.target.style` |
| pages/widgets/* (13 files) | 61 | same `s`-style-object + misc patterns |
| pages/DocumentsPage.tsx | 8 | see fixes 2–5 |
| pages/DashboardPage.tsx | 3 | API shape mismatches (fix 7) |
| pages/dashboard/ServiceForm.tsx | 3 | `field()` helper missing default (fix 6) |

Zero errors already: StreamPage, UtilitiesPage, HermesPage, VoicePage, WidgetPage,
dashboard/LogMonitor, dashboard/ServiceCard.

## Fixes (mechanical — tsconfig is strict:false, skipLibCheck:true, so `as any` casts are acceptable)

1. **motion/react `Easing` does NOT accept CSS `steps(N)` strings** — motion-utils
   `Easing = EasingDefinition | EasingFunction`; `'steps(8)'` works at runtime (WAAPI)
   but fails TS2322. Fix: `ease: 'steps(8)' as any` — type-only, zero runtime change.
   17 occurrences in HomePage (lines 99,112,151,195,210,228,246,262,278,287,311,353,380,430,457,540,641).
2. **DocEditor requires a `saving` prop** — pass `saving={docsCtrl.saving}` (useDocuments exposes it).
3. **DocReader expects `onDownloadDoc`, DocumentsPage passes `onDownload`** — rename at the call
   site (real runtime bug; matches pre-migration .jsx which used `onDownloadDoc`).
4. **`window.marked` has no global type** — add to a .d.ts:
   `declare global { interface Window { marked?: any } }`
   Needed in DocumentsPage L15, DocEditor L176-177, DocReader L234-235.
5. **DocSidebar defaulted props** (`setSelectedTags = () => {}` etc.) infer `() => void`,
   so call-site `setSelectedTags={setSelectedTags}` (a `Dispatch<SetStateAction<...>>`) fails.
   Fix: type the optional props explicitly in the destructure.
6. **ServiceForm `field(label, key, type='text', required)`** — `required` param has no default
   → TS2554 "Expected 4 arguments, but got 3" on 3-arg calls. Fix: `required = false`.
7. **API shapes in src/types/index.ts do NOT match the real backend** (server.js is source of truth):
   - `/api/system/resources` returns `{id, pid, memMB, name}[]` — NOT `ResourceInfo`.
     `setResources(await fetchResources())` into `useState([])` fails TS2345.
   - `/api/files` returns `{entries, path}` (`FileList`) — `setFiles(await fetchFiles(p))` fails;
     state should be `FileList | null`, reads become `files?.entries...`.
   - `/api/scan` returns `{port, pid, name, known}[]`.
   - Verify shapes in server.js handlers: getResources L35-59, scanPorts L249-259, listFiles L309-323.
8. **`Object.values(r)` in a table row renderer yields `unknown`** → `<td>{v as any}</td>`;
   type rows as `{[k: string]: any}[]`.

## Workflow notes
- Backend API shapes: always read server.js before typing fetch state — never trust types/index.ts blindly.
- Pre-migration .jsx originals recoverable via `git show HEAD:frontend/src/pages/<File>.jsx`
  (repo root C:/Users/datel/service-dashboard) — they show the intended prop names/behavior.
- Scope guidance: main pages + dashboard/ = 31 errors; docs/ (54) + widgets/ (61) = 115 remaining
  — treat as a separate follow-up task.
