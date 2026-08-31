# Tester Lab — 8-step Playwright Automation (btdat.io.vn/tester)

Bọc `DEVfancybear/playwright-automation` thành tool web 1 màn hình cho tester thuần.

## Architecture

```
TesterPage.tsx (React 19)  --POST /api/tester/plan-->  tester.js (Node)
        |  SSE POST /api/tester/run (FRAME->EXPLORE->PLAN->CONFIRM->GENERATE->EXECUTE->HEAL->VERDICT)
        +-- GET /recon-output/<runId>/* (evidence static)
        +-- GET /api/tester/report?runId= (verdict.json)

tester-engine/
  scripts/explore.mjs, auth-login.mjs, scaffold.mjs, runtime-safety.mjs
  standards/iso25010.json, iso29119.json, wcag22.json, owasp-asvs.json
```

## Vendor steps

```bash
mkdir -p tester-engine/scripts tester-engine/standards dist/recon-output
curl -sL https://raw.githubusercontent.com/DEVfancybear/playwright-automation/master/scripts/explore.mjs -o tester-engine/scripts/explore.mjs
curl -sL .../auth-login.mjs -o ...
curl -sL .../scaffold.mjs -o ...
curl -sL .../runtime-safety.mjs -o ...
# standards: create 4 JSON with {id, name, clauses:[{id,title,check}]}
npm i -D @playwright/test
npx playwright install chromium
```

## Backend (tester.js) — required handlers

- `GET /api/tester/standards` — list standards
- `POST /api/tester/plan` — {url, feature, standardId, excelBase64?} → {runId, scenarios[], trace[]}. Tries OmniRoute deepseek-v4, falls back to fallbackPlan() (5 scenarios smoke/critical/edge/a11y/visual mapped to clauses).
- `POST /api/tester/run` — SSE `text/event-stream`. Emits {step,status,data} for 8 steps. FRAME (HEAD check), EXPLORE (`node tester-engine/scripts/explore.mjs --url --out`), PLAN, CONFIRM (relaxed auto-approve), GENERATE (playwright.config.ts + TC-*.spec.ts), EXECUTE (absolute playwright bin), HEAL (re-run once), VERDICT.
- `GET /api/tester/report?runId=` — plan + verdict + evidence list
- Static `/recon-output/*` from `dist/recon-output`

**Critical fix — Playwright binary path:**
`npx playwright test` with `cwd=specsDir` fails (no node_modules in specsDir). Use absolute bin:
```js
const pwBin = path.join(__dirname, 'node_modules', '.bin', 'playwright');
const pwCli = fs.existsSync(pwBin + '.cmd') ? `"${pwBin}.cmd"` : `"${pwBin}"`;
const cmd = `${pwCli} test --config="${path.join(specsDir,'playwright.config.ts')}" --workers=1 --retries=0`;
execSync(cmd, { cwd: __dirname });
```
Same for HEAL re-run.

**SSE impl:** `res.writeHead(200, {'Content-Type':'text/event-stream'})`, `send = obj => res.write(`data: ${JSON.stringify(obj)}\n\n`)`, end with `res.end()`.

## Frontend (TesterPage.tsx)

- Left form: URL, feature textarea (VN), standard select (from /api/tester/standards), Excel drag-drop (base64), mode relaxed/guarded toggle, buttons [Tạo kế hoạch] [Chạy 8 bước]
- Right: pipeline stepper 4-col grid (FRAME..VERDICT) with status colors, EXPLORE screenshot preview (`/recon-output/.../screenshot.png`), plan table, trace matrix, verdict card (PASS/FAIL + Export PDF via window.open print), log panel
- SSE: `fetch('/api/tester/run', {method:'POST', body:JSON.stringify({runId,mode})})` → `reader.getReader()` parse `data: ` lines
- Route: `frontend/src/App.jsx` lazy import + `<Route path="tester">`, Navbar add `{to:'/tester', label:'Tester', icon:'🧪'}`
- SPA fallback in server.js must include tester: `if (pathname === '/tester' || pathname.startsWith('/tester/') || ...)`
- Build: `cd frontend && npm run build` → `dist/assets/TesterPage-*.js` (~17kB)

## Pitfalls discovered

- Explorer timeout on self-host btdat.io.vn via Cloudflare loopback (45s) — external sites (example.com, playwright.dev) work; for self-test use localhost:3000 or increase timeout.
- Vietnamese encoding: JSON unicode escapes ok, but SSE log may show `?` if terminal not UTF-8 — frontend renders correctly.
- Evidence 404 until explore done — check `fs.existsSync(exploreOut)` before emitting evidencePath.
- Cloudflare Tunnel must be running (tasklist cloudflared.exe) for public https://btdat.io.vn/tester to serve new build — restart `node server.js` after build.

## Verification

```bash
curl -s http://localhost:3000/api/tester/standards | jq length # 4
curl -s -X POST http://localhost:3000/api/tester/plan -H "Content-Type: application/json" -d '{"url":"https://example.com","feature":"test","standardId":"iso25010"}' | jq .runId
timeout 90 curl -N -s -X POST http://localhost:3000/api/tester/run -H "Content-Type: application/json" -d '{"runId":"<id>","mode":"relaxed"}' | grep VERDICT
curl -s "http://localhost:3000/api/tester/report?runId=<id>" | jq .verdict
curl -s -I http://localhost:3000/recon-output/<id>/explore/screenshot.png # 200
curl -s https://btdat.io.vn/tester | head # SPA shell
```

Reference commit: `feat: tester lab 8-step tool at /tester` (15 files, 2966 insertions).
