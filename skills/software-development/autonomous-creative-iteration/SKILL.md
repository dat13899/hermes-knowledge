---
name: autonomous-creative-iteration
description: "Autonomous state-file-driven creative development loop for cron/background agents. Self-deciding, self-coding, self-verifying iterative builds with no user input."
version: 1.3.0
author: Hermes Agent
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [autonomous, cron, iteration, creative-coding, canvas, html, visual, self-directed]
    related_skills: [verification-before-completion, frontend-coding]
---

# Autonomous Creative Iteration

A workflow pattern for AI agents running as cron jobs or background processes: **read state → decide → code → commit → verify → update state → report**. No user input, no planning phase, no stopping — the agent builds indefinitely.

This skill governs the loop structure and conventions, not the creative domain (which is guided by the project's state file).

## Trigger

Use this skill when:
- You are running as a **scheduled cron job** with no user present
- The project uses a **`<project>-state.json` file** as the single source of truth
- You are expected to **self-decide** what to build next (no instructions, just autonomy)
- The deliverable is a **web visual artifact** (HTML + inline CSS + JavaScript, either single-file or split across JS modules)
- The loop is **infinite** — always build, never eval, never done

## Workflow

### Step 1 — Read State

Read `<project-root>/<project>-state.json`. Key fields:

```jsonc
{
  "iteration": 11,         // increment each run
  "phase": "build",        // always "build" — never "eval" or "done"
  "vision": "...",         // one-line summary of latest state
  "goal": "...",           // what was just built
  "built": ["v1: ..."],    // running changelog, one entry per iteration
  "todo": ["..."],         // ideas for future iterations
  "done": false            // always false — never stop
}
```

Also read the current artifact file (e.g., `public/index.html`) — understand its size, structure, and all existing features before deciding what to add.

### Step 2 — Decide (Creative Autonomy)

You have **total freedom**. Do NOT ask the user or request permission. Pick ONE thing:

| Direction | Examples |
|-----------|----------|
| New scene/mode | New visual mode, new interaction, new animation system |
| Controls | Sliders, color pickers, toggles, keyboard shortcuts |
| Performance | Optimization, lower draw calls, better frame rate |
| Interaction | Mouse/touch/gesture, new physics, audio reactivity |
| Polish | Transitions, particles, visual effects, UI refinement |
| Features | Screenshot export, audio visualizer, preset system |

Select from the `todo[]` in state when applicable. If nothing in `todo[]` inspires you, invent something new.

**Rules of thumb:**
- Prefer additive changes (new mode, new feature) over refactoring — the goal is growth.
- Avoid breaking existing modes/features.
- Keep the artifact self-contained when possible (HTML + inline CSS + inline JS).
- You may add CDN library `<script>` tags if needed.

## Multi-File Architecture (Split JS Modules)

Some projects outgrow a single HTML file and split JS into separate `<script src>` files (e.g., `hermes-core.js` → `hermes-visuals.js` → `hermes-main.js`):

- **`hermes-core.js`** — globals, constants, PALETTES, SCENE_MODES, canvas refs, utility functions (`rand`, `lerp`, `clamp`), config panel state variables, paint mode vars.
- **`hermes-visuals.js`** — ALL render/update functions (drawXxx, updateXxx, initXxx), Web Audio setup, event listeners (keyboard, mouse, touch), UI helpers (mode panel, config panel, paint controls, word modal, help overlay, snapshot, bloom, palette indicator, gradient picker, constellation label, gravity indicator, storm overlays).
- **`hermes-main.js`** — `loop()` function (the render pipeline), startup sequence, splash fade, audio init trigger.

**Implications for patching:**
- A new scene mode touches all 3 files: `SCENE_MODES[]` entry in core.js → render functions in visuals.js → `update/drawXxx()` calls in main.js loop().
- Init functions go in visuals.js; the `initXxx()` call goes in main.js or the HTML inline script.
- Function definitions go in visuals.js; function calls go in main.js.
- Keyboard handlers and event listeners go in visuals.js.
- CSS stays in the HTML `<style>` block.
- After editing visuals.js or main.js, check syntax with `node --check <file>`.

**When to split vs stick to single-file:** The split happens when the single HTML file exceeds ~3000 lines and `read_file` pagination becomes impractical. The split allows reading just 80-100 lines of core.js to understand the module structure without reading the full 2500+ visuals file.

### Step 3 — Code

Edit the project files. Use `patch` (not write_file) for targeted changes — the file can be 2000+ lines and `write_file` risks losing changes if your context window doesn't hold the full file.

**Multi-file patch targets (split JS architecture):**

| File | What to patch |
|------|--------------|
| `hermes-core.js` | `SCENE_MODES[]` entry (id, label, icon, multipliers, badge, booleans), mode state variables, constants |
| `hermes-visuals.js` | Render/update/init functions, keyboard handlers, event listeners, setSceneMode wiring, CSS helpers (palette indicator), paint controls, gradient picker, help overlay entries. **This is the largest file — use `sed -n 'N,Mp'` to verify context before patching.** |
| `hermes-main.js` | `loop()` — add `updateXxx(dt)` and `drawXxx(time)` calls in correct layer order; comic/star dust timer; comet timer. Init calls in startup. |
| `hermes.html` (`<style>`) | CSS for new badge classes, transition delays for new mode buttons, any new DOM elements |

**Common patch targets (per layer):**
- HTML (`<style>` block): CSS for new badge class (`#mode-badge.<mode>-mode{...}`), transition delay for nth button (`#mode-panel.open .mode-btn:nth-child(N)`)
- HTML (`<body>`): button in mode panel (`<button class="mode-btn" data-mode="...">`), new DOM elements (storm overlays, canvas layers)
- HTML (inline `<script>`): `initXxx()` call in startup section and in resize event listener
- `hermes-core.js`: new scene `SCENE_MODES[]` entry, new constants
- `hermes-visuals.js`: keyboard shortcut handler, scene render function, setSceneMode wiring (`xxxMode=scene.id==='xxx'`), help overlay entries, title/hint version number bump
- `hermes-main.js`: `updateXxx(dt)` + `drawXxx(time)` calls in the correct layer order of `loop()`, comet spawning timer

After each patch, verify syntax of the changed file with `node --check <file>` before applying the next patch.

### Step 4 — Git Commit + Push

```bash
cd <project-root>
git add -A
git commit -m "hermes: [short description of what was built]"
git push
```

Commit message convention: `hermes: <noun phrase> — <key details>`

### Step 5 — Verify

```bash
curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/your-file.html
```

- **200** → OK, proceed
- **Anything else** → diagnose the issue and fix it. The file must return 200.

**Note:** On Windows/git-bash, `curl -o /dev/null` may exit with code 23 (`WRITE_ERROR`). Ignore the exit code; the `%{http_code}` value in stdout IS correct. MSYS2 `curl` can't write to MSYS2's `/dev/null` via Win32's `-o` flag but the HTTP response is received successfully.

**Multi-file syntax check (run after all patches):**

```bash
node --check public/hermes/hermes-core.js
node --check public/hermes/hermes-visuals.js
node --check public/hermes/hermes-main.js
```

`node --check` validates pure JS syntax only (no DOM). It catches syntax errors in split JS files that `node -e "new Function(...)"` on the HTML would miss because the HTML-inline script has DOM calls.

**Ad-hoc feature verification (dedicated temp script with proper exit codes):**

When you need to verify specific functions, constants, or wiring are present across multiple files, write a self-contained Node.js verification script to a temp file and run it. This is more reliable than inline `node -e` because:

1. It can read multiple files, check multiple patterns, and call `process.exit()` properly.
2. A single `FAIL` stops the script; you don't wait for all checks to finish.
3. The exit code is deterministic — the script succeeds or fails as a whole.

```bash
cat > /tmp/verify-xxx.js << 'SCRIPT'
const fs = require('fs'), http = require('http');
const base = 'public/hermes';
let ok = true;
function check(pass, msg) {
  console.log(pass ? 'PASS' : 'FAIL', '—', msg);
  if (!pass) ok = false;
}

// 1. Syntax validation
for (const f of ['hermes-core.js', 'hermes-visuals.js', 'hermes-main.js']) {
  try { new Function(fs.readFileSync(`${base}/${f}`, 'utf8')); check(true, `${f} syntax`); }
  catch(e) { check(false, `${f} syntax: ${e.message}`); }
}

// 2. Feature checks by scanning source
const v = fs.readFileSync(`${base}/hermes-visuals.js`, 'utf8');
check(v.includes('function myNewFeature('), 'myNewFeature function defined');
check(v.includes('MY_CONSTANT='), 'MY_CONSTANT defined');

// 3. Loop wiring check
const m = fs.readFileSync(`${base}/hermes-main.js`, 'utf8');
check(m.includes('updateMyFeature(dt)'), 'update call in loop');
check(m.includes('drawMyFeature(time)'), 'draw call in loop');

// 4. HTTP 200 live check
http.get('http://localhost:3000/hermes', (res) => {
  check(res.statusCode === 200, `HTTP ${res.statusCode} from /hermes`);
  console.log(ok ? '\n✅ ALL PASSED' : '\n❌ FAILURES DETECTED');
  process.exit(ok ? 0 : 1);
}).on('error', e => { check(false, `HTTP: ${e.message}`); process.exit(1); });
SCRIPT
node /tmp/verify-xxx.js
rm /tmp/verify-xxx.js
```

This pattern has several advantages over the old inline `node -e` approach:
- Longer scripts are easy to author in `write_file` then run.
- `process.exit(0/1)` makes shell pipelines reliable (`&&` chaining works).
- Cleanup (`rm`) leaves no temp files behind.
- The HTTP check is embedded in the same process — no separate curl call needed.
- Error messages include both the short failure ("FAIL") and full context.

### Step 6 — Update State

Write `hermes-state.json` (or `<project>-state.json`) with:

```json
{
  "iteration": <increment>,
  "phase": "build",
  "vision": "Updated summary — what this version looks like in one sentence.",
  "goal": "Mô tả ngắn gọn mục tiêu vừa hoàn thành (tiếng Việt ưu tiên).",
  "built": [
    "v1: ...",
    "v2: ...",
    "...append new entry..."
  ],
  "todo": [
    "Current active ideas"
  ],
  "done": false
}
```

- Increment `iteration` by 1.
- Append a new entry to `built[]`. Keep prior entries as historical record (they are the project's changelog and vision narrative).
- Update `vision` to reflect the new state succinctly.
- Update `goal` to state what was just accomplished (can be Vietnamese).
- Keep `phase` = `"build"` and `done` = `false` (always).

### Step 7 — Report

Return a compact report in the project's preferred language. For Vietnamese projects:

```
🌀 Hermes Loop #[iteration]
Goal: [mục tiêu vừa làm]
Built: [ngắn gọn]
Todo: [ý tưởng tiếp theo]
```

**For cron delivery:** put the full report as your final response. The cron system delivers it automatically.

**SILENT protocol:** If something genuinely failed and nothing changed (no file edits, no commit), respond with `[SILENT]` only. Never combine `[SILENT]` with content.

## Diagnostic — Splash Screen Spins Forever

When a single-file canvas app appears stuck on the loading spinner:

| Step | Check | How |
|------|-------|-----|
| 1 | JS syntax error | `grep -n '?\.[0-9]' file.html` — #1 cause (ternary vs optional chaining) |
| 2 | Element ID mismatch | Cross-reference all `getElementById('xxx')` calls vs HTML `id="xxx"` attributes |
| 3 | null.addEventListener | Any `getElementById('nonexistent')` returning `null` followed by `.addEventListener(...)` crashes immediately |
| 4 | `new Function()` parse | `node -e "const fs=require('fs'); const h=fs.readFileSync('file.html','utf8'); const m=h.match(/<script>([\s\S]*?)<\/script>/); try{new Function(m[1]);console.log('OK')}catch(e){console.log(e.message)}"` |
| 5 | Production content size | `curl -sL https://url/page \\| wc -c` — expect real content, not 0 or truncated |
| 6 | Temporal Dead Zone (TDZ) | `grep -n 'let \\|const ' file` — check declaration order vs call site. A `let` declared **after** a function that references it crashes at runtime with `ReferenceError: Cannot access 'X' before initialization` |

### Wrapping Script for Error Visibility

Fastest debug: wrap the entire `<script>` block + add `window.onerror`. Errors render ON the splash screen:

```html
<script>
try{
// ... ALL existing JS code unchanged ...
}catch(e){
  document.getElementById('splash').innerHTML = '<pre style="color:red;padding:40px">'+e.stack+'</pre>';
  document.getElementById('splash').classList.remove('fade');
}
window.onerror = function(msg, url, line, col, err){
  document.getElementById('splash').innerHTML = '<pre style="color:red;padding:40px">'+msg+'\nline '+line+'\n'+(err&&err.stack||'')+'</pre>';
  document.getElementById('splash').classList.remove('fade');
  return true;
};
</script>
```

- `try{}catch()` — catches **synchronous** errors (parse errors, null references at init)
- `window.onerror` — catches **async** errors (inside `requestAnimationFrame(loop)`, timeouts)
- Remove after diagnosis (~60 lines of scaffolding)

### Root Cause: Temporal Dead Zone (TDZ) — `let`/`const` Declaration After Call

When `let galaxyStars=[]` is declared **after** `initGalaxy()` is called, the JS engine throws `ReferenceError: Cannot access 'galaxyStars' before initialization` at runtime. Unlike `var` (hoisted as `undefined`), `let`/`const` enter a **temporal dead zone** from the start of the enclosing scope until the declaration is evaluated.

**Symptom:** Splash spins forever, `new Function(js)` parse check passes (it's a runtime error, not syntax), and `?.number` grep returns empty.

**Detection:**
```bash
# 1. Find the error function call site
grep -n "initGalaxy\|function initGalaxy\|let galaxyStars\|const galaxyStars" file.html

# 2. Cross-reference the call vs declaration lines
# If:  let galaxyStars=[] at line 2239
# But: initGalaxy() called at line 2081
# Then: TDZ crash. Move the `let`/`const` BEFORE the call site.
```

**Fix:** Move the `let`/`const` declarations **above** the call site. For `<script>` blocks where all code runs in sequence, the declaration must appear textually before any function call that references it:

```js
// BAD — TDZ crash
initGalaxy();          // ← called here, galaxyStars not yet declared
// ...200 lines of other code...
let galaxyStars = [];  // ← declared here, too late

// GOOD — works
let galaxyStars = [];  // ← declared before call
initGalaxy();          // ← called after, galaxyStars is initialized
```

**Common TDZ candidates in large canvas files:**
- `let galaxyStars`, `galaxyRotation` — galaxy mode variables
- `let fireflies`, `stormLightnings` — firefly/storm mode variables
- `let painting`, `paintingHistory` — paint mode state
- Any `let`/`const` variable declared as an empty array initializer that's referenced in a function called above its text

After moving declarations, verify the function body only **assigns to** (not `let` re-declares) the variable:
```js
// Inside initGalaxy():
function initGalaxy() {
  galaxyStars = [];     // ✅ assignment to outer variable — correct
  // let galaxyStars = [];  // ❌ creates NEW TDZ in function scope — wrong
}
```

### Root Cause: Element ID Mismatch

In large files, JS references and HTML elements drift out of sync:

```js
// JS line 1207:
const paintHueSlider = document.getElementById('paint-hue');
// But HTML only has:
<span id="paint-hue-indicator"></span>
//                                          ↑ 'paint-hue' never existed!
```

`paintHueSlider` is `null` → `paintHueSlider.addEventListener(...)` throws `TypeError` → script aborts → splash never fades.

**Prevention checklist after every major feature addition:**

```bash
# 1. Extract all JS element references
grep -oP "getElementById\('([^']+)'\)" file.html | sort -u > /tmp/js-ids.txt
# 2. Extract all HTML id attributes
grep -oP 'id="([^"]+)"' file.html | sort -u > /tmp/html-ids.txt
# 3. Find IDs referenced in JS but missing from HTML
diff /tmp/js-ids.txt /tmp/html-ids.txt | grep '^<'
```

Same applies to `querySelector('.xxx')` — mismatches crash silently. Keep references simple with `id`.

## Reading Large Files Before Patching

When the artifact is 2000+ lines, **never assume you know its structure** — always re-read with `read_file`:

1. **Read the first 50-100 lines** to see the <head>, title, splash, and main CSS.
2. **Read around line 100-400** to see CSS, HTML body structure, mode panel buttons, word modal, paint controls, config panel, HUD.
3. **Read around line 340-420** to see SCENE_MODES array, palette definitions, and keyboard helpers.
4. **Use `search_files` to find specific anchors** — e.g., `search_files(pattern="initFireflySwarm")` tells you exact line numbers.
5. **Read the end of the JS** (last 100 lines) to see the `loop()` function and startup sequence — this is where new `drawXxx()` calls must be inserted.
6. **Read the exact line ranges** where you'll patch using `read_file(path, offset=N, limit=5)` to confirm the old_string context before calling `patch`.

**Why this matters:** The `patch` tool warning `"was last read with offset/limit pagination (partial view). Re-read the whole file before overwriting it."` appears when you write_file after only reading snippets. Using `patch` avoids this issue since patch only touches matched strings.

## Scanning a 2600+ Line File — Offset Map

For a typical cosmic dreamscape HTML structure (proven pattern):

| Offset | Typical Content |
|--------|----------------|
| 1-50 | DOCTYPE, `<title>`, `<style>`, base CSS, canvas layers, HUD |
| 50-120 | Mode panel CSS (transition delays for .mode-btn:nth-child) |
| 120-215 | Paint controls, word modal, snapshot toast, config panel, transition overlay CSS |
| 215-350 | `</style>`, `<body>`, splash, hint, title, mode-badge, mode panel buttons, paint controls HTML |
| 350-420 | Help overlay HTML |
| 420-500 | `<script>` start, `resize()`, constants, palette definitions, SCENE_MODES array |
| 500-max | All render functions, init functions, loop(), startup |

**When adding a new scene mode, the common patch targets in order are:**

1. `<title>` — update version number (e.g., v13 → v14)
2. SCENE_MODES array — add new mode entry
3. Mode panel button HTML — `<button class="mode-btn" data-mode="...">` — add after the last button
4. CSS: `#mode-panel.open .mode-btn:nth-child(N)` — add transition delay for the new Nth button
5. CSS: new mode badge class (`.new-mode{...}`) — for badge coloring
6. HTML: any new DOM elements needed (storm-flash, storm-canvas, etc.)
7. Hint line — add keyboard shortcut (e.g., `"U storm"`)
8. Help overlay — add help entry
9. `initXxx()` call in startup section (after last init call)
10. `initXxx()` call in resize event listener
11. `xxxMode = scene.id==='xxx'` in setSceneMode
12. Keyboard handler: add `if(k==='u'||k==='U'){...}`
13. Main loop: add `updateXxx(dt)` + `drawXxx(time)` calls in correct layer order
14. Update version in title text (`<div id="title">... v14 ...</div>`)
15. Apply patches in THIS ORDER — dependency order matters (mode must exist before panel button references it)

## Verifying Patch Safety

When patching a large HTML file (2000+ lines):

1. **Use `read_file` with offsets** to navigate — never assume you know contents.
2. **Use `search_files`** to find exact line numbers before patching — avoids the "found N matches" error when old_string appears multiple times.
3. **Add surrounding context to make old_string unique** — include 2-3 lines before/after to disambiguate.
4. After each `patch`, verify with `search_files` or direct inspection that the change landed correctly.
5. Check for duplicate occurrences using `replace_all=false` — patch will error if a string appears >1 time.
6. Avoid the `"last read with offset/limit pagination"` warning by using `patch` (not `write_file`) for modifications after partial reads.
7. Run a structural tally before declaring done (count modes, functions, init calls).

### Final Verification — JS Parse + Structural Checks

Run the reusable verification script (see `scripts/verify-artifact.js`) **after all patches but before git commit** to catch silent failures:

```bash
node scripts/verify-artifact.js public/hermes.html 12
```

Or run an inline one-shot:

```bash
node -e "
const fs = require('fs');
const html = fs.readFileSync('public/hermes.html','utf8');

// 1. JS syntax check — catches ?.number errors, unmatched braces, missing parens
const scriptMatch = html.match(/<script>([\s\S]*)<\/script>/);
const js = scriptMatch[1];
try { new Function(js); console.log('✅ JS parses OK'); }
catch(e) { console.log('❌ JS syntax error:', e.message); }

// 2. Structural integrity checks (customize per project)
const lines = html.split('\n');
const checks = {
  title:       lines.some(l => l.includes('v14')),
  modeEntry:   lines.some(l => l.includes(\"id:'storm'\")),
  panelBtn:    lines.some(l => l.includes('data-mode=\"storm\"')),
  keyboard:    lines.some(l => l.includes('k===\\'u\\'') || l.includes('k===\\'U\\'')),
  hint:        lines.some(l => l.includes('U storm')),
  resize:      lines.some(l => l.includes('initStorm()')),
  loop:        lines.some(l => l.includes('updateStorm')) && lines.some(l => l.includes('drawStorm')),
  setMode:     lines.some(l => l.includes('stormMode=scene.id===\\'storm\\'')),
};

const fail = Object.entries(checks).filter(([,v]) => !v).map(([k]) => k);
console.log(fail.length === 0 ? '🎉 ALL CHECKS PASSED' : '⚠️  FAILED: ' + fail.join(', '));
"
```

**Always run this before `git commit`.** The `new Function(js)` trick catches JS syntax errors that would silently kill the page — the most common being `?.number` ternary errors (see "Common JS Syntax Error" section). However, `new Function()` does NOT catch **runtime errors** like TDZ (`ReferenceError: Cannot access 'X' before initialization`) or null-reference crashes — for those, use the `eval()` simulation with DOM stubs described in "Root Cause: Temporal Dead Zone".

### Ad-Hoc Feature Verification (When read_file is Dedup'd)

After patching, `read_file` may return stale cached content (see `references/tool-quirks.md`). For quick feature confirmation without the full verification script:

```bash
node -e "
const fs=require('fs');
const h=fs.readFileSync('public/hermes.html','utf8');
const checks = {
  thunder: /function playThunderRumble\(/.test(h),
  puddles: /\bstormPuddles\b/.test(h),
  tilt3d: /\btiltX=clamp\(/.test(h),
};
const fail = Object.entries(checks).filter(([,v])=>!v).map(([k])=>k);
console.log(fail.length ? 'FAIL: '+fail.join(', ') : 'ALL FEATURES PRESENT');
"
```

## Common JS Syntax Error — `?.number` in Ternaries

When packing ternary expressions with numeric literals, **`?.` is always parsed as optional chaining**, so `?.9` or `?.5` produces `SyntaxError: Unexpected number`:

**BAD:**
```js
const a = wordFormed?.9:.6;           // SyntaxError
ctx.lineWidth = isPaint?.5:1;         // SyntaxError
```

**FIX:** Add spaces after the `?`:
```js
const a = wordFormed ? .9 : .6;
ctx.lineWidth = isPaint ? .5 : 1;
```

**Detection:** `grep -n '?\\.[0-9]' yourfile.html`

This error causes the entire `<script>` block to silently abort — splash screens never fade, event listeners never attach, `requestAnimationFrame(loop)` never fires. The page appears stuck on "loading" but the HTML/network check out fine.

## Multi-Trigger Visual Effect Pattern (Resonance/FX Layer)

When adding a visual effect that fires from **multiple trigger points** (click explosions, gravity release, comet spawns, keyboard shortcuts), wire it as a standalone system with three functions and N call sites:

```
spawnEffect(x, y, intensity)    → triggers
updateEffect(dt)                 → physics/animation
drawEffect(time)                 → rendering
```

### Architecture

| File | What to add |
|------|-------------|
| `hermes-core.js` | State array (`let effectName=[];`), max count constant (`const MAX_EFFECT=N;`), counter (`let idCounter=0;`) |
| `hermes-main.js` (loop) | `updateEffect(dt)` + `drawEffect(time)` calls in correct z-order layer |
| `hermes-visuals.js` | Three functions: `spawnEffect`, `updateEffect`, `drawEffect` |
| `hermes.html` (config panel) | Slider row for adjustable intensity/speed |
| `hermes.html` (help/hint) | Keyboard shortcut docs |

### Wiring Call Sites

The pattern works because `spawnEffect` is called from multiple independent locations:

```
// 1. Click explosion
function doExplosion(x,y,count){ spawnEffect(x,y,count/50); ... }

// 2. Gravity release (mouseup)
if(gravityWell.strength>.3) spawnEffect(gravityWell.x,gravityWell.y,gravityWell.strength);

// 3. Comet spawn (periodic spawner or fragmentation)
spawnEffect(cometX,cometY,.5);

// 4. Keyboard shortcut (dedicated key)
spawnEffect(mouse.x, mouse.y, 1.2);
```

### Slider Wiring (Minimal Config Pattern)

Every configurable slider needs 3 edits:

1. **HTML** (`hermes.html`): `<div class="cfg-row"><span class="cfg-label">Label</span><input type="range" id="cfg-xxx" min="0" max="10" value="5"><span class="cfg-val" id="cfg-xxx-val">5</span></div>`
2. **Core** (`hermes-core.js`): `let cfgXxx=5;`
3. **Visuals** (`hermes-visuals.js`): Event listener that reads slider value, plus `if(cfgXxx<.5)return;` guard in the spawn function so the effect can be fully disabled at 0.

Then use `cfgXxx` inside the effect functions to modulate speed/size/decay:
```
speed: baseSpeed * (cfgXxx/5)      // scale by slider
decay: baseDecay * (6/(cfgXxx+.1)) // invert so higher = longer
```

### Verification

After adding a multi-trigger effect, verify each call site landed:
```
node -e "
const v=require('fs').readFileSync('public/hermes/hermes-visuals.js','utf8');
const checks = {
  doExplosion: v.indexOf('spawnEffect', v.indexOf('function doExplosion')) < v.indexOf('function doExplosion') + 200,
  gravityRelease: v.indexOf('spawnEffect', v.indexOf('gravityWell.strength>.3')) < v.indexOf('gravityWell.strength>.3') + 80,
  cometSpawn: v.indexOf('spawnEffect', v.indexOf('function spawnComet')) < v.indexOf('function spawnComet') + 200,
  keyboard: /k==='k'/.test(v) || /k===.K./.test(v),
};
const fail=Object.entries(checks).filter(([,v])=>!v).map(([k])=>k);
console.log(fail.length?'FAIL: '+fail.join(', '):'ALL WIRED');
"
```

Use generous distance thresholds (>= 200 chars) — function bodies have setup lines before the spawn call.

## Using `todo` Tool Inside Cron Loops

For cron-driven iterative builds with 3+ steps, use the `todo` tool to track progress. This prevents losing your place after a tool failure or mid-turn interruption:

```javascript
todo(todos=[
  {id: "1", content: "Read state and analyze current code", status: "completed"},
  {id: "2", content: "Add new scene mode (11th mode)", status: "in_progress"},
  {id: "3", content: "Test curl HTTP status", status: "pending"},
  {id: "4", content: "Git commit + push", status: "pending"},
  {id: "5", content: "Update state file", status: "pending"},
])
```

Mark items `completed` immediately when done, `cancelled` when failed. Call `todo()` (no args) to re-read the full list on each turn to reorient.

## Pitfalls

- **File too large for `write_file`:** If the file is >2000 lines, prefer `patch` over `write_file`. A write_file with outdated content (read from truncated view) can silently truncate the real file.
- **Broken HTML from incomplete patches:** Ensure every patch opens/closes tags correctly. A missing `</div>` or `</script>` will silently break the entire page.
- **Duplicate keyboard handlers:** Adding a new `addEventListener('keydown',...)` creates a second listener, not a replacement. If patching into the existing handler, the string must be unique.
- **Mode badge not showing:** The setSceneMode badge logic has conditional `classList.add('show')`. Check that your mode id passes the condition (paintMode=false, wordMode=false, not constellation/nebula → shows).
- **Resize reinit:** Every new geometry mode needs an `initXxx()` call in the resize event listener AND at the module level startup.
- **State file JSON:** Valid JSON required. No trailing commas. String values must be properly escaped.
- **Cron 3-minute hard limit:** If a render/init function is O(n²) with large n (e.g., 4000+ star loop), it must be fast enough to complete within 180 seconds total, including all patches, git push, and verification.
- **`curl -o /dev/null` exit code 23 on Windows/git-bash:** MSYS2 emulates `/dev/null` but curl's Win32 `-o` flag can't open it. Exit code 23 is `WRITE_ERROR`, not a connection failure — the HTTP status in stdout IS correct (e.g., `200`). Ignore exit code 23; trust the `%{http_code}` value.
- **`?.number` syntax error (see Common JS Syntax Error section):** The most common cause of "stuck on loading" in large creative canvas files. Always grep for this pattern after making ternary-related changes.
- **Keyboard shortcut collisions:** Before adding a new keyboard shortcut (e.g., `F` for firefly mode), grep for existing uses of that key. `F`/`f` may already be bound (audio-reactive toggle). If colliding, choose a different key (e.g., `B` for bugs/fireflies) and update the hint, help overlay, and key handler consistently.
- **`todo` tool for multi-step tracking:** Use the `todo` tool with a task list for cron loops with 3+ steps. Mark items `in_progress`/`completed`/`cancelled` so a mid-turn interruption doesn't lose your place (see section below).
