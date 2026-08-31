# Frost Kingdom — Full teardown and cheat analysis (Aug 2026)

**URL:** `https://frostkingdom.onechain.nexus/web/prod/index.html`
**Game type:** SLG (4X strategy — Kingdom Clash / Call of Dragons style)
**Publishers:** Nexus / OneChain

## Engine & Architecture

- **Cocos Creator 2.x** (web-mobile build)
- **Bundle structure:** `internal`, `resources`, `main`, + 8 language bundles: `vi`, `en`, `cn`, `ko`, `th`, `tr`, `tw`, `id-id`
- **Launch scene:** `db://assets/scenes/login.fire` (single scene, dynamic switching via custom SceneManager)
- **Boot:** `settings.74539.js` → `main.b58e4.js` → `cocos2d-js-min.68fa1.js` → bundles

## UI Framework

- **FairyGUI** (not Cocos native UI) — `assets/lib/fairygui.44fe0.js`
- Layer system: `GameMain` (sprite layer), `UIMain` (FGui layer), `TweenLayer`, `UITips`, `UIGuide`, `UINetTip`, `TopMain`
- Layers registered in `BaseEuiLayer` (FairyGUI GRoot) vs `BaseSpriteLayer` (Cocos canvas)

## Code Base

- **Single 13.3MB bundled JS:** `assets/main/index.c58c6.js` — 4,858 CommonJS modules
- **Data definitions:** `assets/scripts/auto/auto.55de8.js` (295KB) — 3,152 cfg data classes + 878 C2S/S2C message pairs (in `ns.msg` namespace)
- **Manager pattern:** Net, SceneManager, ResourceMgr, SoundManager, LoginMgr, ChatMgr, ArenaMgr, EquipMgr, ShopMgr, etc.
- **Subsystems:** `core/`, `ui/view/`, `map/`, `combat/`, `mgr/`, `player/`, `egret/`, `channel/`, `scene/`, `global/`, `stats/`, `MiniGame/` (2048, TowerRush, FoodParty...)

## Networking Protocol (fully reverse-engineered)

### Transport
- WebSocket (plain `ws://` or `wss://`), wrapper in `egret/net/websocket/EWebSocket`
- Binary mode (`socket.binaryType = "arraybuffer"`)

### Message Encode (obfuscation, NOT encryption)
1. Client builds JSON: `{"C2S_CommandName": {...fields}}`
2. Compress with **SnappyJS** (`SnappyJS.uncompress`/`.compress`)
3. **XOR every byte** with `length - position`: `byte ^= total_length - current_position`
4. Write to `EByteArray`, send via WebSocket

### Decode (receive)
1. XOR each byte: `byte ^= length - position` (same key, symmetric algorithm)
2. Decompress with SnappyJS
3. Parse JSON, dispatch via `MessageCenter.it().dispatch(msgName, payload)`

### Message Pattern
- Client sends: `C2S_<CommandName>` with parameters
- Server responds: `S2C_<CommandName>` or related name
- 878 matched C2S/S2C pairs total
- Message classes are **empty shells** — only `ClassName` property, no field schema, no client-side validation
- Revealed by: `auto.js` with 138 `.msg||(s.msg={})` namespace groups
- Ping tracked via `S2C_WG` / `C2S_WG` messages

### Obfuscation Assessment
- XOR + Snappy = **zero real security** — fully reversible in ~20 lines of Python
- No AES, no RSA, no TLS on the game protocol layer
- The `AESUtils` module is an empty stub (77 chars)

## Login & Auth

- **GamePot SDK (NHN/Naver Cloud):** `gamepot-sdk-javascript-1.0.44.min.js`
- `gamepot-config.fe629.js`: project_id, api_key, Google client_id, Apple client_id, agentName, paymentKey
- Google Sign-In + Apple ID login (`loginChannel: isAppleDevice() ? 'APPLE' : 'GOOGLE'`)
- **GM detection:** `getUserData().GM == 1` — server-set field in UserData; controls chat censorship bypass and guild chat early access
- **Nexus Cross Pay SDK** (esm.sh) for payments

## Assets

- **27,410 assets** in `resources` bundle
- Types: Texture2D, SpriteFrame, SpriteAtlas, Prefab, AnimationClip, AudioClip, BitmapFont, EffectAsset, **Spine skeleton** (sp.SkeletonData)
- Spine referenced **3,386 times** in code — core animation system
- 10,312 path entries: `spine/ui/`, `map/CityBuild/`, `res_hd/raid/Monster/`, `soundMusic/`, `citySkin/`

## localStorage Usage

- Primarily settings only, NOT game state: `isPlayer4GAutoUnDowm` (4G download preference)
- No player data, gold, or state cached client-side — all server-driven

## Chat Module

- `ChatMgr` (4,662 chars) — handles `S2C_Chat`, `S2C_NGM` (GM notice), `S2C_Bcst` (broadcast), `S2C_NoChat` (mute)
- `S2CNGM` handler: `if (!ret) showLabelTip(tip)` — server sends GM tip/error messages
- Chat text runs through `changeDes()` censorship filter unless `getUserData().GM == 1`
- No GM/cheat commands found in chat input processing

## Cheat Analysis: Authoritative Server — CANNOT cheat resources

### Why it's solid
1. All resource logic is server-side. Client only sends IDs (AwardID, SwitchId) — never amounts
2. Battle results use server-issued `BattleToken` → client can't fabricate wins
3. Every award uses unique server-tracked IDs → replay attacks blocked
4. No GM/admin/cheat commands in client code
5. No `/addgold`, `/gm`, or hidden chat commands
6. Award pattern: `C2S_X{AwardID, SwitchId}` → `S2C_X{Ret, Reward[]}` → client just `showGetAwardTip(Reward)`

### Attack surface that looks big but is closed
- Massive 13MB JS with 4,858 modules → tempting to search for exploits
- 878 C2S messages → suggests many attack vectors
- XOR "encryption" → looks amateur
- All misleading: the server is fully authoritative on every material transaction

### To actually cheat, you'd need
- A valid **GamePot OAuth token** (Google/Apple login) — mandatory to connect
- A real account → permanent ban risk
- No server-side exploit was found in client code analysis

### Messages with client-sent quantities (Num/Count fields)
These exist but are NOT exploitable — they're for things like how many items to decompose, how many times to buy — and server validates against inventory. Examples: `C2S_HeroLevel.Nums`, `C2S_DecomposeItem.Num`, `C2S_UseTreasure.Num`, `C2S_ForbesBuy.Num`
