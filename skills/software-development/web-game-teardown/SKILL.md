---
name: web-game-teardown
description: Use when user asks how a web game is made. Detect engine.
---

# Web Game Teardown

Analyze how an HTML5 browser game is built: engine, architecture, UI framework, networking protocol, assets, SDKs. If the user asks about cheating/hacking the game (resources, currency, items), follow the methodology in `references/cheat-analysis-methodology.md`. Battle-tested on Cocos Creator 2.x (Frost Kingdom case study in `references/cocos-creator-2x.md`); generic steps apply to other engines.

## Workflow

1. **Fetch index.html** — `curl -sSL -A "Mozilla/5.0" <url> -o $HOME/x.html` (save to `$HOME`, not `/tmp` — see Pitfalls). Engine fingerprints:
   - Cocos Creator 2.x: `src/settings.<hash>.js` (defines `window._CCSettings`), `main.<hash>.js` boot script, `cocos2d-js-min.<hash>.js`, `<meta name="renderer" content="webkit">`, `#GameCanvas` / `#Cocos2dGameContainer`, `splash` div
   - Others: phaser / pixi / three / egret / laya / unity-webgl `.loader.js`
2. **Parse _CCSettings** (Cocos 2.x): `platform`, `launchScene` (e.g. `db://assets/scenes/login.fire`), `orientation`, `jsList` (custom libs: fairyui, pako, auto.js), `bundleVers` (bundle → version hash, incl. language bundles vi/en/cn/ko/...)
3. **Download bundles** — version suffix REQUIRED:
   - `assets/<bundle>/config.<ver>.json` — manifest
   - `assets/<bundle>/index.<ver>.js` — code (can be 10+ MB, browserify-style require map)
   - Bare names (no version) → 404. If stuck, grab real URLs from the browser: `performance.getEntriesByType('resource')` in browser_console.
4. **Read config.json**: `paths` (uuidIdx → [path, typeIdx]), `types[]`, `uuids[]`, `scenes{}`, `redirect[]`, `deps[]`, `packs{}`, `versions.import/native` (flat [uuidIdx, ver] arrays), `importBase`/`nativeBase` = `import`/`native`. Import data: `import/<packId>.<ver>.json`; native files: `native/<uuidIdx>.<ver>`.
5. **Extract code modules** with `scripts/cocos-module-extract.py`. Module body = brace-matched span after `Name:[function(e,t,i){` — naive regex fails on nested braces. Module ids also appear in `cc._RF.push(t,"<uuid>","<Name>")`. Count class-name families (`*Wnd`, `*Cell`, `*Panel`, `*Mgr`, `*Data`) to characterize architecture.
6. **Networking**: grep for `WebSocket` + wrappers (HTML5Websocket / EWebSocket / EByteArray in egret-style stacks), compression (pako / SnappyJS), obfuscation (per-byte XOR), message shape (`{"C2S_Login":{...}}` — first JSON key = message name), event bus (`MessageCenter.dispatch`), ping messages (e.g. `S2C_WG`).
7. **UI framework**: `fgui.UIPackage.addPackage` / `GRoot` / `GComponent` → FairyGUI (UI is NOT Cocos native nodes). Gauge usage with python `src.count(kw)` — e.g. fgui 7k hits, Spine 3.3k hits → UI = FairyGUI, animation = Spine.
8. **SDK inventory**: login/payment configs (gamepot-config, google/apple client ids), esm.sh imports.
9. **Summarize**: engine, UI framework, animation system, networking protocol, asset count/types, localization bundles, SDKs — as a recipe the user can learn from ("công thức").

## Pitfalls

- **Version-suffixed bundle URLs**: always `config.<ver>.json` / `index.<ver>.js` — never the bare name. Guessing paths costs many 404s.
- **MSYS /tmp trap** (git-bash/Windows): `$TMP` env var ≠ `/tmp`; a file written to `/tmp` may be unfindable via `$TMP`. Save scratch files under `$HOME`.
- **curl exit 23 on MSYS**: `curl -o /dev/null` can exit 23 (write error) even with valid HTTP responses; trust `-w "%{http_code}"`, not the exit code.
- **Login/ad SDK redirects**: games with Google/Apple sign-in iframes or ad SDKs can redirect the browser page (e.g. to chrome://new-tab-page), wiping resource-timing evidence. Prefer curl + static analysis; use the browser only for a fast resource-URL grab, then re-navigate.
- **rg regex**: escape `{`/`}` in ripgrep patterns (`\{name:`), or use python re — unescaped braces cause `repetition quantifier` parse errors.
- **Big bundles**: 10+ MB single files — process with python (regex + brace matching), never read the whole file into context.

## Support files
- `scripts/cocos-module-extract.py` — list module keys / dump a module body from a Cocos Creator bundle index.js
- `references/cocos-creator-2x.md` — Cocos Creator 2.x bundle anatomy + Frost Kingdom case study (networking protocol, UI layers, SDKs)
- `references/cheat-analysis-methodology.md` — systematic cheat/hack analysis (C2S/S2C review, protocol weakness, GM/command injection, attack surface classification, decision tree)
- `references/protocol-patterns.md` — common networking patterns (XOR+Snappy, WebSocket wrapper, message naming, ping mechanism)
