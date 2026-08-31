---
name: web-game-dev
description: "Mobile web game dev: Canvas+React, VN fonts, E2E tests."
category: software-development
---

# Web Game Development (mobile-first HTML5)

Use when building a web game (canvas/HTML5), especially mobile-first, one-thumb, or Vietnamese-language. Proven end-to-end by VẬN RUNE (repo `~/rune-fate`, live at `btdat.io.vn/rune/`).

## Analyzing existing web games (recon / reverse-engineering)

When the user asks "game này làm như thế nào" / "hack được không" / "kiến trúc thế nào" for a browser game: read `references/cocos-creator-reverse-engineering.md` — full recipe for Cocos Creator 2.x web-mobile builds (settings.js → bundle configs → 13MB bundled code → protocol decode). Key facts: UI=FairyGUI, protocol = JSON → SnappyJS → XOR(len-pos) (trivially reversible), message classes are empty stubs in `auto.js`, server is authoritative so client patching only fakes display. Always frame the answer: what's technically possible vs what actually works against a server-authoritative SLG.

## Architecture (proven pattern)

- **React 19 + Vite + TS for UI overlay** (HUD, rune/card picker, menus, meta screens) + **Canvas 2D + requestAnimationFrame for the game loop** (combat, particles, shake). React re-renders only on discrete state changes; the engine owns per-frame state.
- Engine class holds all game state; callbacks (`onNarrator`, `onRuneOptions`, `onHud`, `onEnd`, `onPhase`) bridge to React state.
- GameCanvas component: `useEffect` creates engine + `startRun(config)`; cleanup calls `engine.destroy()` (cancelAnimationFrame + remove resize listener).
- ⚠️ **React StrictMode double-mounts effects in dev** — the destroy-on-cleanup pattern is mandatory, else two engines fight.
- Audio: **WebAudio procedural synth** (oscillators + noise buffers), NOT audio files → Safari autoplay-safe, tiny bundle. AudioContext starts suspended; unlock on first pointerdown/keydown.
- Save: localStorage JSON. Daily seed = hash(YYYY-MM-DD) for shared daily dungeons / leaderboards.

## Game feel checklist (what separates "tuyệt vời" from "tạm được")

- Hit-stop: freeze 2 frames on hit
- Screen shake: translate canvas by random ±shake, decay ~20/s
- Particles: cap ~250, gravity, alpha fade
- Floating damage numbers (crit bigger / gold-colored)
- Flash on damage; heal/shield feedback numbers
- Sound per event: swing, hit, crit, heal, coin, death, victory

## ⚠️ CRITICAL: Vietnamese + pixel fonts

Press Start 2P / Pixelify Sans / Silkscreen / Tiny5 / Micro 5 / DotGothic16 / Jacquard / Handjet **have NO Vietnamese glyphs** — diacritics render detached/broken ("Mở" → "M�", "Người" → glyph soup). A VN game with broken text is dead on arrival.

**Safe VN pixel font: VT323** (best pixel look, verified). Also Roboto Mono, Space Mono, Be Vietnam Pro. Put the safe font FIRST in the fallback chain: `--font-head: 'VT323', 'Press Start 2P', monospace;`

**Always verify with screenshot + vision_analyze** (home, battle, end screens). The font bug is invisible in code review — only visible in rendered screenshots. See `references/vn-pixel-fonts.md` for the safety table + verification recipe.

## Testing (playwright-core, proven)

- chrome-headless-shell at `C:/Users/datel/AppData/Local/ms-playwright/chromium_headless_shell-<ver>/chrome-headless-shell-win64/...` — check `ls` first, version dir changes.
- Mobile viewport `{ width: 390, height: 844 }`, deviceScaleFactor 2 for screenshots.
- Capture console errors + pageerror + requestfailed.
- Auto-play loop: poll for picker cards (e.g. `.rune-card` count === 3), click first, repeat until end screen or timeout — exercises death/victory flow end-to-end.
- Verify save persistence: reload page, check localStorage-driven UI.
- Test BOTH a local static server (tiny http server over dist/) AND the live public URL through the tunnel.
- Visual QA: `page.screenshot()` → `vision_analyze` — this caught 2 real bugs (broken font, duplicated epitaph) that assertions missed.
- `.mjs` test files run as plain JS — no TypeScript annotations.

See `references/playwright-game-testing.md` for a copy-paste skeleton.

## Deploy under a subpath on an existing Node server (proven)

1. `vite.config.ts`: `base: '/<game>/'` (NOT '/')
2. Fix absolute paths in index.html + manifest: `/rune/manifest.webmanifest`, `/rune/icons/...`, `start_url`
3. Add a route block to the existing server.js BEFORE the SPA fallback: exact path → index.html; `/game/` prefix → map to dist files with a MIME map; SPA fallback for deep links
4. Restart: `taskkill /F /PID <pid>` (git-bash needs `/F /PID`, NOT `//PID`) then relaunch `node server.js` in background
5. Verify: `curl -s -o /dev/null -w "%{http_code}" https://domain/<game>/` → 200, plus full playwright run against the public URL
6. Keep a `deploy.sh`: build → E2E tests → restart server → curl verify. One command redeploys.

## Pitfalls

- `npm create vite` refuses non-empty dirs (has .git/docs) — scaffold manually (write package.json/tsconfig/vite.config/index.html yourself).
- PWA icons: generate solid PNGs with pure Node zlib (no ImageMagick needed) — worked fine.
- Kill listeners on old PID before restart; `netstat -ano | grep ":<port>" | grep LISTEN` to find it.
- Engine timing: use accumulator-based attack cadence (hero/enemy separate accumulators) instead of per-tick randomness for stable combat.

## References

- `references/vn-pixel-fonts.md` — font safety table + verification recipe
- `references/playwright-game-testing.md` — copy-paste E2E skeleton
