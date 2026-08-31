# JS → TS7 Migration Playbook (React + Vite)

Verified 2026-08-02 on service-dashboard (React 19 + Vite, 78 .jsx + 17 .js files,
~11,400 lines) migrated to TypeScript 7 (Go compiler). Zero errors at the end,
type-check 0.8s.

## Strategy: batch-rename first, then fix errors by PATTERN

Do NOT convert file-by-file manually. The fast path:

1. **Setup tsconfig with `allowJs: true, checkJs: false, strict: false`** first —
   the whole project type-checks clean immediately. Add `"typecheck": "tsc --noEmit"`.
2. **Mass-rename** extensions with one shell loop:
   ```bash
   find src -name "*.jsx" -exec sh -c 'mv "$1" "${1%.jsx}.tsx"' _ {} \;
   find src -name "*.js" ! -name "index.js" -exec sh -c 'mv "$1" "${1%.js}.ts"' _ {} \;
   ```
   Imports without extensions (`'../hooks/useTheme'`) keep resolving — bundler
   moduleResolution handles .ts/.tsx automatically. No import edits needed.
3. **Run `tsc --noEmit`** — every error is now visible. Group by file, count by
   error code (`grep -oE "TS[0-9]+" | sort | uniq -c | sort -rn`).
4. **Fix by error-pattern with python/sed scripts**, not one-by-one edits. Most
   errors are 4-5 recurring patterns (below).

## The recurring error patterns (and one-shot fixes)

| Error | Pattern | Fix |
|---|---|---|
| `TS2322 ... not assignable to CSSProperties` | inline style objects with `position: string` etc. | `const s: Record<string, any> = {` for the style map — kills all CSSProperties errors in the file at once |
| `TS2322 ease: 'steps(8)' not assignable to Easing` | motion v12 dropped steps-string from `Easing` union (runtime still works!) | `transition={({ duration: 0.3, ease: 'steps(8)' } as any)}` — wrap whole object; `as const` does NOT help |
| `TS2339 Property 'marked' does not exist on Window` | markdown lib loaded via CDN as `window.marked` | `(window as any).marked` |
| `TS2339 Property 'style' does not exist on EventTarget` | `e.target.style` in mouse handlers | `(e.target as HTMLElement).style` |
| `TS2554 Expected 0 arguments, but got 1` | destructured setter default `setX = () => {}` used as `setX(prev => ...)` | `setX = (() => {}) as Props['setX']` — cast the no-op default to the real setter signature |
| `TS2554 Expected 4 arguments, but got 3` | JSDoc-typed helper with required params | make the param optional (`required?: boolean`) or give default |
| `TS2362/2363 arithmetic on unknown` | `new Date(x.created || 0) - new Date(...)` where fields are `unknown` | wrap `Number(new Date(String(x || 0)))` |
| `TS2322 unknown not assignable to ReactNode/Key` | `.map(v => <td>{v}</td>)` over unknown-typed values | `String(v)` / annotate `(v: string)` |
| `TS2741 Property X is missing` | parent passes fewer props than child destructures | add prop at call site (e.g. `saving={docsCtrl.saving}`, `isMobile={isMobile}`) OR make child prop optional |

## Order of migration (safest)

1. `types/index.ts` + typed `services/api.ts` (`request<T>()` + return types) —
   API contract first
2. hooks `.js → .ts` (pure logic, few errors)
3. components `.jsx → .tsx` (pixel/ → shared/ → layout/ — least deps first)
4. pages `.jsx → .tsx` (largest, most errors — do last)
5. Build + typecheck + deploy after EACH phase (rollback = git revert)

## Strict mode: defer it

`strict: true` on a legacy codebase exploded to **483 errors** (mostly
strictNullChecks + implicit any on old files). If the codebase wasn't strict
before, keep `strict: false` in the first migration pass. Enabling strict is a
separate, multi-hour cleanup — budget it as its own phase, not part of the
rename. Zero-error `strict: false` + TS7 Go compiler (0.8s typecheck) is a fine
deliverable.

## Pitfalls

- `npm uninstall three ...` may be blocked; edit package.json directly then `npm install`.
- Windows `git add -A` can fail with `error: open("frontend/nul")` — a stray file
  named `nul` (Windows reserved device name) breaks git. `rm -f frontend/nul` then re-add.
- Deleted `.jsx` + new `.tsx` show as `D` + `??` in git — `git add -A` picks both up;
  add untracked dirs (e.g. `voice/`) to .gitignore first if they shouldn't be committed.
