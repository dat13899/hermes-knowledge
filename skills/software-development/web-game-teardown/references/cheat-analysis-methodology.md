# HTML5 Game Cheat/Hack Analysis Methodology

Systematic approach to assess whether a web game client can be exploited for resources, currency, or items. Battle-tested on Cocos Creator 2.x SLG (Frost Kingdom, Aug 2026) — the analysis process generalizes to any client-server game.

## Prerequisites

Complete a full teardown first (engine, protocol, code modules, message catalog). You need the complete list of C2S (client→server) and S2C message pairs before you can assess vulnerabilities.

## Phase 1: Protocol Security Assessment

### 1.1 Is the wire protocol encrypted or obfuscated?

Patterns found (weak to strong):

- **XOR with static/derived key** — zero real security. Frost Kingdom used `byte ^= length - position` — reverse in 10 minutes. No MITM protection at all.
- **Snappy/zlib compression only** — not encryption, just reducing bandwidth.
- **No TLS/wss** — traffic is fully readable.
- **AES/RSA** — check if key is hardcoded in client JS (still weak) or only server-side (strong).

### 1.2 Can messages be replayed?

Key indicators:
- **No nonce/timestamp/sequence** in message fields → replay is possible.
- **AwardId + SwitchId pattern** — server assigns IDs; replaying same ID gets rejected (server tracks claimed IDs). Replay is blocked if IDs are unique per claim.
- **BattleToken** — server issues per-battle token → replay is blocked.

## Phase 2: Message Structure Analysis

### 2.1 What fields does the client send?

Extract all message construction patterns from bundled JS:

```python
# Find all "new ns.msg.C2S_XXX" and the field assignments after
for match in re.finditer(r'new ns\.msg\.(C2S_\w+).*?\.(\w+)=\s*([^;,]+)', src):
    print(match.groups())
```

### 2.2 Does client send quantities?

RED FLAG messages where client specifies `Num`, `Count`, `Amount`, `Qty`. These are the highest-value targets. Search pattern:

```python
# Find messages with client-sent quantity fields
for m in re.finditer(r'new ns\.msg\.(C2S_\w+).*?\.(\w+)=\s*([^;,]+)', src):
    if any(kw in m.group(2).lower() for kw in ['num','count','amount','qty']):
        print(f'{m.group(1)}.{m.group(2)} = {m.group(3)}')
```

In Frost Kingdom, this found `C2S_HeroLevel.Nums`, `C2S_DecomposeItem.Num`, `C2S_ForbesBuy.Num`, etc. — but all are bound by server-side resource checks (server verifies you own N items before decomposing, server checks gold before buying). **Client-sent quantity ≠ client-controlled outcome.**

## Phase 3: Server Authority Verification

### 3.1 The definitive test: who decides the reward?

The single most important pattern in any game protocol:

```
Client sends:  C2S_ClaimReward { AwardID, SwitchId }  ← ONLY IDs
Server replies: S2C_ClaimReward { Ret, Reward[] }      ← SERVER defines reward content
Client shows:  if (Ret==1) showGetAwardTip(Reward)     ← pure display
```

If the client NEVER sends `Amount`, `Gold`, `Diamond`, `ItemId` in reward-claim messages — **server is fully authoritative**. Client hacking is limited to display manipulation only (refresh reverts it).

### 3.2 GM/Admin mode detection

Search the bundled JS for:
- `getUserData().GM` — Frost Kingdom has this field from server login response
- `S2C_NGM` — GM notification handler (`if ret==0 showTip`)
- `changeDes(e)` — chat censorship function; if `GM!=1`, messages are filtered

GM is **server-controlled** — client cannot toggle it. The check `1!=s.App.P.getUserData().GM` gates chat features, not resource manipulation.

### 3.3 Battle result validation

Look for `BattleToken` in battle messages:
```
Server: S2C_BattleEx { Ret, CLog, BattleToken }   ← server issues token
Client: C2S_BattleRet { BattleToken, Order }        ← client reports back with token
Server: S2C_BattleRet { Ret, Win }                  ← server decides win/loss
```
The `BattleToken` prevents replay and fake-win reports. Server computes the actual battle outcome.

### 3.4 Chat command injection

Search ChatMgr for hidden commands (`/gm`, `/addgold`, `/item`). In Frost Kingdom: no slash-command parsing found. Chat text goes through `changeDes()` censorship then direct to `C2S_Chat { Text, Horn, Type }`.

### 3.5 localStorage persistence

```python
for m in re.finditer(r'cc\.sys\.localStorage\.setItem\("([^"]+)"', src):
    print(m.group(1))
```

Frost Kingdom only stores UI preferences (`isPlayer4GAutoUnDowm`) — no resource/currency data in localStorage. All state comes from server sync.

### 3.6 Minigame scoring

Games with minigames (2048, tower defense, food party) are high-value targets. Look for:
- `C2S_CompleteMiniGame { Id, SId }` — only IDs, no score → server computed
- `C2S_Activity2048End { Id }` — server already has the game state

If the client sends `Score`, `Points`, or `Level` → potential exploit vector.

## Phase 4: Conclusion Framework

### THREE outcomes, ordered by severity:

1. **Server-authoritative (Frost Kingdom case)**: All resources computed server-side, client sends only IDs, server returns reward content. Protocol is readable (XOR+Snappy) but un-exploitable. Only cheat possible: display manipulation (useless after refresh).

2. **Client-trusted with validation**: Client sends quantities but server validates (e.g. `C2S_BuyItem { ItemId, Count }` — server checks inventory before deducting gold). Integer overflow or negative values may bypass weak validation.

3. **Client-trusted without validation** (RARE in commercial games): Client sends reward values directly. These games are trivially exploitable via packet injection.

### Red flags that indicate category 2 or 3:
- No BattleToken in battle result messages
- Client sends `Score` or `Result` in minigame completion
- `C2S_CompleteMiniGame { Id, Score }` with no server-side replay verification
- Tutorial/guide battles that bypass normal validation
- Messages with `Num`/`Count` fields sent without corresponding server-side inventory sync
- Award messages that include `Amount`/`Gold`/`Diamond` fields set by client
- If S2C returns `Ret==1` + `Reward[]` → server validates, quantity is just "how many to apply"
- If S2C just acknowledges the value → possible exploit (but extremely rare in commercial games)

### 2.3 Are message classes empty shells?

In many Cocos Creator games, the auto-generated `ns.msg.C2S_*` classes are empty — just `ClassName` metadata:

```js
class a{} a.ClassName="C2S_Activity2048Save",s.C2S_Activity2048Save=a
```

No field schema, no client-side validation. This means:
- Client can send ANY JSON fields with ANY values
- All validation is server-side by design
- It's NOT a bug — it's the architecture: server is always authoritative

## Phase 3: Authorization & Authentication

### 3.1 How does login work?

- **OAuth (Google/Apple/GamePot)** → token → game server session. Without a valid OAuth token, you can't even make game protocol calls.
- **Guest login** (C2S_Visitor) — may have rate limits but is the easiest to use for testing.
- **GM flag** — check for `getUserData().GM` — if this field exists, it's server-set only (field in UserData from login response). Not exploitable by client.

### 3.2 Is there a GM/Admin backdoor?

Check ALL of these:
1. **Chat commands** — search `C2S_Chat` construction for prefix parsing (`/gm`, `/add`, `/gold`)
2. **GM message handlers** — `S2C_NGM`, `S2C_GM`, any admin-flagged handler
3. **Client-side GM checks** — `getUserData().GM == 1` only bypasses UI restrictions (chat censorship, feature gates), NEVER grants items/resources
4. **Auto-generated message classes** — grep for `C2S_GM`, `C2S_Admin`, `C2S_Debug`, `C2S_Cheat` in auto.js
5. **Cfg classes** — grep `ClassName=".*[Gg][Mm].*"` for GM-only data tables

### 3.3 What does the GM flag actually do?

In Frost Kingdom, `getUserData().GM == 1` only:
- Bypasses chat text censorship (`changeDes()` filter)
- Enables guild chat before the normal unlock level
- Does NOT grant any items, currency, or admin commands

## Phase 4: The Authoritative Server Check

### 4.1 The critical pattern to look for

The #1 indicator that a game CANNOT be exploited for resources:

```
Client: C2S_Award { AwardID: <server-assigned>, SwitchId: <server-assigned> }
Server: S2C_Award { Ret: 1/0, Reward: [...server-calculated items...] }
Client: if (Ret==1) showGetAwardTip(Reward)  // just display what server sent
```

When you see this pattern across all resource-related messages, the game is server-authoritative. Client never specifies WHAT the reward is — only WHICH reward (by ID) to claim.

### 4.2 Counter-patterns that LOOK exploitable but aren't

| Message pattern | Why it looks exploitable | Why it's not |
|---|---|---|
| `C2S_DecomposeItem { Id, Num }` | Client sends quantity! | Server checks inventory has N items first |
| `C2S_HeroLevel { CId, Nums }` | Client sends levels | Server checks available XP/items against cost |
| `C2S_CompleteMiniGame { Id, SId }` | Client claims completion | Server simulates or validates game state independently |
| `C2S_ChapterBattleRet { BattleToken }` | Client reports battle result | Server already knows outcome from the BattleToken |

### 4.3 The definitive test

If you can answer YES to all of these, the game is uncheatable for resources:
1. Does every resource-granting message get its `Reward[]` list FROM the server, not FROM the client?
2. Does every award/shop message use a server-assigned AwardId (not a client-chosen one)?
3. Does the login require an OAuth flow (Google/Apple/GamePot) to get a session?
4. Are battle/game results validated server-side (not just client-reported)?

### 4.4 What IS exploitable (even on authoritative servers)

- **UI bypass** — patch JS to show invisible buttons, skip tutorials, auto-click
- **Botting** — automate real actions (farming, daily quests) — ban risk
- **Traffic sniffing** — read other players' positions/troops from broadcast messages
- **Account sharing/selling** — social, not technical

## Phase 5: Reporting Results

When the user asks "can I cheat this game?" or "can I get free gold/diamonds/resources?", be DIRECT:

1. State the finding upfront: YES or NO
2. Explain WHY with evidence from the code (specific message patterns, not hand-waving)
3. If NO, be honest — don't sugar-coat with "maybe you could try X" when X won't work
4. Offer the realistic alternatives (botting, UI mods) but with clear caveats about ban risk
5. If the user seems to want to learn game architecture, pivot to that — share the interesting protocol details even if they can't be weaponized

### The "circumstantial evidence" trap

Be careful not to equate "protocol is weak" with "game is hackable":
- XOR obfuscation → can READ traffic, can't MODIFY server state
- 13MB client JS → easy to analyze, doesn't mean server trusts client
- 800+ C2S messages → many attack vectors, but each individually blocked
- These are often DESIGN decisions (optimize for bandwidth, not secrecy) not SECURITY failures

### The Command Code / OmniRoute provider angle

When checking which provider/model an OmniRoute combo uses:
- `hermes config get model` shows current default (e.g. `cmd/deepseek/deepseek-v4-flash`)
- `GET /v1/models` lists all available with provider prefix
- `GET /api/providers` shows connection details (keys, sync, proxy)
- Model version suffixes (e.g. `-0731`) are NOT visible in the API — they're upstream details
- Models with `autoSync: true` use the latest upstream version automatically
