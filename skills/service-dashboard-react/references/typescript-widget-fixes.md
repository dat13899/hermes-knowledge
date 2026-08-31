# Fixing TS errors in widgets (TS2322 CSSProperties pattern)

Session: Aug 2026 — fixed all 61 TS errors across 13 `src/pages/widgets/*.tsx` files. Root cause + exact recipe below.

## Root cause

Almost every widget defines a module-level style map with NO type annotation:

```ts
const S = {
  container: { textAlign: 'center', padding: '1.5rem 1rem' },
  row: { display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap', ... },
};
```

Without an annotation, object literal properties get **widened** from literal types to `string`.
`CSSProperties` fields like `textAlign`, `flexDirection`, `flexWrap`, `position`, `userSelect`,
`overflowY`, `wordBreak`, `resize`, `boxSizing` are **string-literal unions** — `string` is not assignable.

Error count: 61 errors, ALL `TS2322` except 2 (`TS2362`/`TS2363` Date arithmetic, 1 `TS2339` EventTarget).

Key gotcha: the errors appear at the **usage site** (e.g. `style={{ ...S.note(color), left: ... }}`
or `style={S.row}`), NOT at the `const S` declaration. So when a fresh tsc run shows errors at
JSX `style=` props, suspect the unannotated style map first.

## The fix (2 variants)

**Variant A — plain style maps (no functions inside):** annotate with `Record<string, CSSProperties>`.

```ts
import type { CSSProperties } from 'react';

const S: Record<string, CSSProperties> = { ... };
```

**Variant B — style maps containing functions** (e.g. `diceBtn: (active) => ({...})`,
`toggle(active)`, `note: (color) => ({...})`): use `Record<string, any>`.

```ts
const S: Record<string, any> = { ... };
```

⚠️ DO NOT use `Record<string, CSSProperties | ((...args: any[]) => CSSProperties)>`.
Every access `S.x` then returns the union, and `S.note(color)` fails with
`TS2349: This expression is not callable` (CSSProperties has no call signatures) plus a flood of
TS2322 "has no properties in common with type 'Properties'" at every usage. The union breaks
narrowing. With `strict: false` (this project's tsconfig), `Record<string, any>` is the correct
lightweight fix.

## Other 3 errors

- `Countdown.tsx` `const diff = target - now;` (Date arithmetic) → `target.getTime() - now.getTime()`.
- `RandomDiscovery.tsx` `onError={(e) => { e.target.style.display = 'none'; }}` →
  `e.currentTarget.style.display = 'none'` (EventTarget has no `.style`; currentTarget is typed).

## Verification

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -c 'widgets/'
# → 0
```

## Pitfalls

- **Don't use `as const` on the whole map when functions are present** — it locks function
  signatures and still doesn't satisfy CSSProperties contextual typing at spread sites.
- Clean up the now-unused `import type { CSSProperties }` if you downgrade a Variant B file later
  (tsc flags unused? no — `noUnusedLocals` is off here, but keep it tidy anyway).
- `Record<string, CSSProperties>` can bite if a key is later made a function; switch that key's
  map to Variant B (or make the whole map `Record<string, any>`).
- Batch multi-file edits via python heredoc + `re.sub`; a single V4A multi-file patch failed on
  files whose `import { useState } from 'react';` line appears twice (patch validation requires
  unique matches). Apply per-file replacements instead.
