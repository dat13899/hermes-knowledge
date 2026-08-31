# Live Site QA Audit — 2026-08-01 (btdat.io.vn)

Full-page audit done via headless Chrome (CDP 9222) + codegraph + curl.
All 5 issues found were FIXED and deployed the same day (build
`index-BZQAKxgb.js`, all routes 200). Keep this as the record of what the
bugs looked like and exactly how they were fixed — the fix patterns are
reusable.

## ✅ P1 — Dashboard: progress bar bleeds across cards — FIXED
- Symptom: green (MP) progress bar ran horizontally through multiple
  service cards; cards looked squished/cut; purple divider lines extended
  past their parent.
- Root cause: `PixelProgress` bar container lacked `overflow: hidden`, so
  the fill (`width: N%`) escaped the bar bounds.
- Fix: `frontend/src/components/pixel/PixelProgress.jsx` — added
  `overflow: 'hidden'` to the bar container div.
- Note: vision-model screenshots are UNRELIABLE for this class of bug
  (reported a non-existent "50 Containers" card and a bleed that DOM
  measurement could not confirm). Verify with `Runtime.evaluate` +
  `getBoundingClientRect()` comparisons, not by eyeballing a screenshot.

## ✅ P2 — Documents: Vietnamese filenames lose diacritics — FIXED
- Symptom: files stored as `b-o-c-o-th-c-t-p-2.docx` instead of
  `báo-cáo-thực-tập-2.docx`.
- Root cause: server-side slug regex `[^a-z0-9]+` stripped ALL diacritics
  (every accented char became `-`). Slugging happens at upload/create/
  rename on the server (`server.js`).
- Fix: added `slugify()` to `server.js` using Unicode properties
  `[^\p{L}\p{N}]+gu` so diacritics survive ("Báo cáo" → `báo-cáo`).
  Replaced the old regex in all 4 call sites (addService, docx upload,
  md create, rename). Verified: POST with UTF-8 body created
  `kiểm-tra-dấu-tiếng-việt.md`.
- ⚠️ Old files keep their stripped names on disk — only NEW uploads are
  fixed. Don't try to back-rename via API (unicode id in URL path does
  not match the route regex); `rm` the file directly if needed.

## ✅ P3 — Dashboard: two filter buttons both labeled "ALL" — FIXED
- Fix: `frontend/src/pages/DashboardPage.jsx` — `⚔ ALL` → `▶ START ALL`,
  `⏹ ALL` → `⏹ STOP ALL`, added `title` tooltips. Verified on browser
  snapshot.

## ✅ P4 — Sticky dock/nav overlaps content on scroll — FIXED
- Fix: `frontend/src/components/layout/AppLayout.jsx` — main
  `paddingBottom` increased `calc(64px + 1rem)` → `calc(96px + 1.5rem)`
  so the fixed bottom dock never covers the last content row.

## ✅ P5 — Home hero: ~70% empty viewport on desktop — FIXED
- Fix: `frontend/src/pages/HomePage.jsx` `PixelHero` — `minHeight`
  `85dvh` → `46dvh`, padding tightened. Measured hero bottom dropped
  ~765px → ~542px in a 900px viewport.
- Remaining whitespace between hero and skills is intentional (hero is a
  centered RPG splash); further reduction is a design call, not a bug.

## Deploy recipe used (works every time)
```bash
cd ~/service-dashboard/frontend && npm run build        # → dist/
# kill server on :3000 (bg-session kill may leave the node PID behind):
PID=$(netstat -ano | grep ":3000" | grep LISTEN | head -1 | awk '{print $NF}')
[ -n "$PID" ] && taskkill /F /PID $PID
cd ~/service-dashboard && node server.js                 # run in background
sleep 4 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/  # 200
grep -o 'assets/index-[^"]*\.js' dist/index.html         # confirm new bundle hash
```
