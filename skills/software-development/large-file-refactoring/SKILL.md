---
name: large-file-refactoring
description: "Break up large files (3000+ lines, 50KB+) into smaller, focused modules — JS, HTML, Python, or any language. Covers inline-script extraction, load-order dependencies, and refactoring while preserving runtime behavior."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [refactoring, modularization, large-files, web-development]
    related_skills: [frontend-coding, simplify-code, systematic-debugging]
---

# Large File Refactoring

Break up a monolithic file into smaller, focused modules while preserving exact runtime behavior.

## When to Use

- User says "file quá nặng, chia nhỏ ra" or "refactor this file"
- Single file > 50KB or > 1000 lines
- Inline `<script>` block in HTML is hard to debug (errors point to the same giant file)
- A cron/agent keeps adding features to one file

## General Strategy

1. **Map the structure** — grep for section headers, `function` declarations, module-scope vars
2. **Identify natural split points** — distinct capabilities (config, core, visuals, audio, UI, main loop)
3. **Decide module architecture** — script tags in order, ES modules, or dynamic import
4. **Extract JS from container** (HTML/PHP/JSX) then split
5. **Keep the init sequence in place** — remove module-scope init calls that need runtime setup
6. **Validate syntax** of every extracted file before deploy
7. **Test in production** — curl + browser console

## Reference Files

- `references/split-monolithic-inline-js.md` — detailed technique for extracting inline `<script>` blocks
- `references/mobile-responsive-canvas-app.md` — making full-screen canvas apps work on mobile (HUD → bottom bar, mode panel → bottom sheet, touch gestures, iOS audio)

## When Mobile-Responsive Follows Refactoring

After splitting a monolithic file, the user often asks to "làm dùng được trên mobile luôn". Plan for this upfront:

1. **Keep core HTML intact** — refactor JS first, then add CSS `@media` blocks
2. **Bottom sheet pattern** — mode/config panels slide up from bottom instead of sidebar
3. **HUD → full-width bar** — move from centered floating to edge-to-edge at bottom
4. **Touch gestures** — 2-finger swipe to cycle modes, pinch to open config
5. **Test on mobile** — verify buttons are tappable (min 44px), no overlap with HUD

## Pitfalls

### 1. Module-scope init calls that depend on runtime state
Variables like `W, H` from `resize()` are undefined when module scripts parse. Functions calling `Math.min(W,H)` at init time get **NaN** silently.
→ Move all init calls into a deferred inline script that runs after `resize()`.

### 2. const/redeclaration across files
If old file had `const X = ...` and inline script also assigns `X = ...`, the new file structure causes **SyntaxError: redeclaration**.
→ Keep `const/let` in module files, assign without keyword in inline init.

### 3. Patch tool eating closing braces
When replacing multi-line patterns like `}\n}\ninitFn();` with a comment, the closing `}` gets lost.
→ Always include BOTH closing braces in old_string; verify syntax after each patch.

### 4. Windows line endings (`\r\n`)
Regex `\n` won't match `\r\n` in JS string literals. Use `.replace(/\r/g, '')` or match with `[\s\S]*?`.

### 5. Order matters
Script tags load and execute in order. Put core/globals first, then functions, then main loop. Init inline script goes LAST.

### 6. `let`/`const` in module scripts does NOT create window globals
A `let audioInitialized=false;` in a loaded `.js` file is scoped to THAT file's execution context. An inline `<script>` tag in the HTML is a **separate** script context and cannot see it → **ReferenceError**.

**Fix**: Use `window.audioInitialized=false;` for any state that must be shared between module scripts and inline scripts. Reference it as `window.audioInitialized` everywhere. This is safe because the script execution is synchronous and single-threaded.

Alternatively, declare absolute globals at the top of the FIRST script loaded (the "core" module) — that file runs first and sets `window.X = ...` values that downstream files and inline code can use.

### 7. Scripts in `<head>` run before DOM is built
If `<script src="...">` tags are placed in `<head>`, `document.getElementById('c')` returns **null** because the `<body>` hasn't parsed yet. This crashes every function that needs a canvas ref immediately — before `DOMContentLoaded` ever fires.

**Fix**: ALWAYS move all `<script src="...">` tags to the bottom of `<body>`, right before any inline init script that references DOM elements:

```html
<body>
  <!-- DOM elements first -->
  <canvas id="c"></canvas>
  <canvas id="bloom"></canvas>

  <!-- Then load module scripts -->
  <script src="/hermes/hermes-core.js"></script>
  <script src="/hermes/hermes-visuals.js"></script>
  <script src="/hermes/hermes-main.js"></script>

  <!-- Then inline init that calls resize(), getElementById, etc. -->
  <script>
  try {
    resize(); // now 'c' exists
    initAuroraBands();
    requestAnimationFrame(loop);
  } catch(e) { ... }
  </script>
</body>
```

### 8. Node syntax check ≠ browser runtime validation
`new Function(code)` only validates JavaScript grammar — it does NOT execute in a browser environment. Code that references `document`, `window`, `canvas`, `AudioContext`, or `requestAnimationFrame` will PASS syntax check and crash at runtime.

**Always verify in a real browser after refactoring**:
1. Curl the page — confirm 200 + all modules load
2. Open DevTools Console — check for uncaught errors
3. Verify the splash screen disappears and the main canvas renders
4. Check network tab for 404s on module scripts
