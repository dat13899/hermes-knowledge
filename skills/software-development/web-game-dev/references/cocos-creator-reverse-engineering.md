# Reverse-engineering Cocos Creator 2.x HTML5 games (web-mobile builds)

Session: phân tích Frost Kingdom (frostkingdom.onechain.nexus) — SLG mobile
H5 (game chiến thuật, FairyGUI UI + Spine anim + WebSocket JSON protocol).

## Build layout (Cocos Creator 2.x web-mobile)

- `index.html` → loads `src/settings.<hash>.js` (window._CCSettings) then `main.<hash>.js` (boot).
- `_CCSettings` = gold: `platform:"web-mobile"`, `launchScene:"db://assets/scenes/login.fire"`,
  `orientation`, `jsList` (extra libs: fairygui, pako, auto.js), `bundleVers` map
  (`internal`, `resources`, `main`, + one bundle PER LANGUAGE: vi, en, cn, ko, th, tr, tw, id-id).
- Bundles live at `assets/<name>/config.<ver>.json` + `assets/<name>/index.<ver>.js` — NOT at root.
- `config.<ver>.json` fields: `paths` (uuidIdx → [path, typeIdx]), `types` (asset type names),
  `uuids`, `scenes` (scene uuid → index), `redirect`, `packs` (uuid group → pack uuid),
  `versions` (`import`: [uuidIdx, ver, ...], `native`: [uuidIdx, ver, ...]).
- Imported assets resolve at `assets/<bundle>/import/<packUuid>.<ver>.json`; native at
  `assets/<bundle>/native/<uuidIdx>.<ver>` — but exact URL form varies; check browser
  `performance.getEntriesByType('resource')` when guessing 404s.
- Game code = ONE giant bundled CommonJS file `assets/main/index.<ver>.js` (13MB here,
  ~4900 modules). Module map pattern: `Name:[function(e,t,i){...}]` — extract with a
  brace-depth scanner, not regex on `\n},` (modules are minified, may be single-line).

## Data classes vs real code

- `src/assets/scripts/auto/auto.<hash>.js` (auto-generated) = ONLY data/config classes:
  `ns.cfg.*`, `ns.msg.*` (protocol message names!), `ns.e.*` (event ids). Here: 3152 data
  classes incl. every `C2S_*`/`S2C_*` message as an EMPTY class (`class a{}a.ClassName=...`).
  Protocol names fully readable: `C2S_Login`, `C2S_UserLogin`, `C2S_Ping`, `S2C_WG`...
- Real logic (managers, scenes, UI windows) is in the main bundle.

## Architecture fingerprints (SLG genre)

- **UI = FairyGUI** (fgui.*): `fairygui.UIPackage.addPackage`, `GRoot.inst.addChild(layer)`,
  GComponent/GObject everywhere. Layer stack via custom `LayerDefine`: GameMain (sprite),
  UIMain/TweenLayer/UITips/UIGuide/UINetTip (EUI layers on GRoot).
- **Scene management**: custom `SceneManager` (register/runScene/changeScene), scenes extend
  `BaseScene` (onEnter/onExit, addLayer/addTopLayer). Login scene = `LoginScene`.
- **Managers everywhere**: `Net`, `ResourceMgr`, `SoundManager`, `LoginMgr`, `ChatMgr`,
  `ArenaMgr`, `ShopMgr`... classes named `*Wnd` (window), `*Cell` (list item), `*Panel`,
  `*Mgr`, `*Data`. Singleton via `static it()`.
- **Spine** for character/effect animation (3386 refs), `soundMusic/` audio, `map/CityBuild/`
  city art, `res_hd/raid/Monster/` battle monsters.
- Asset paths in `config-resources.json` `paths` reveal the whole content tree:
  `spine/ui/`, `dynamicImageRes/`, `fairyUIRes/`, `citySkin/`, `godbeast/UI/`...

## Network protocol (weak — the interesting part)

- WebSocket (egret-style wrapper `HTML5Websocket`/`EWebSocket` + `EByteArray`), binary frames.
- Frame: JSON `{"C2S_Name": {...}}` → UTF8 bytes → **SnappyJS.compress** → **XOR each byte
  with `byte ^ (length - position)`** (key = message length!) → send. Receive = reverse.
- i.e. "encryption" is trivially reversible: decompress + XOR. MessageCenter dispatches by
  first JSON key: `MessageCenter.it().dispatch(d, m[d])`.
- HTTP side: `Http`/`HttpSingle` queue, `EHttpRequest`, POST JSON; login via GamePot SDK
  (Google/Apple OAuth) — `gamepot-config.<hash>.js` holds projectId/api_key/client ids.

## Client-side security assessment (what "hacking" looks like)

Possible (easy): full traffic decode (sniff WS frames, Snappy+XOR), patch client JS
(display-only values), auto-click/bot. Message classes are empty → client sends any fields.
NOT possible (server-authoritative): real resource/combat/balance changes — server computes
all logic, validates sign/token (659 `sign`, 491 `token` refs). Real SLG hacks are social
engineering/account-related, not packet forging.

## Reusable recipe for future recon

1. `curl` index.html + `src/settings.*.js` + `main.*.js` — read `_CCSettings` first.
2. Pull `assets/main/config.*.json`, `assets/resources/config.*.json` (paths+types reveal content).
3. Pull main bundle `assets/main/index.*.js` — grep module keys, extract with depth scanner.
4. Pull `src/assets/scripts/auto/auto.*.js` for protocol names.
5. Browser: watch `performance.getEntriesByType('resource')` for REAL asset URLs when
   guessing bundle/import paths 404s. Note: ad/login SDKs (GamePot, cross-pay, Google gsi)
   may redirect the page / block headless console — re-navigate and re-grab quickly.
