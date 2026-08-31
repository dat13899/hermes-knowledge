# Astryx API Quirks — Full Detail

Session-derived from building the astryx-demo landing page (Aug 2026),
package versions: `@astryxdesign/core@0.4.1`, `@astryxdesign/theme-neutral@0.4.1`,
React 19, Vite 8 (rolldown).

## How to discover API (the reliable path)

Read the `.d.ts` files in `node_modules/@astryxdesign/core/dist/<Component>/`.
The doc header comment in each `.d.ts` lists the synced props — fastest source
of truth. Examples:

- `Button.d.ts` — header: "Last synced props: label, variant, size, isDisabled,
  isLoading, isInterruptible, clickAction, icon, isIconOnly, width, children,
  tooltip, endContent, href, as, target, rel"
- `Badge/index.d.ts` — `BadgeVariantMap` interface
- `Grid/Grid.d.ts` — `GridColumns` type: `number` or `{minWidth, max?, repeat?}`
- `Stack/stack.stylex.d.ts` — exports `SpacingStep`

## Exports map gotcha (Vite build breaker)

`@astryxdesign/core` package.json `exports` maps ONLY these CSS subpaths:
`./reset.css`, `./astryx.css`, `./tailwind-theme.css`. The files physically live
at `dist/astryx.css` but the exports map does NOT expose `./dist/astryx.css`.
Import `@astryxdesign/core/reset.css` (NOT `.../dist/reset.css`).

Theme CSS: `@astryxdesign/theme-neutral/theme.css` → physically
`dist/theme.css`; same rule — use the export subpath.

## SpacingStep scale

```ts
export type SpacingStep = 0 | 0.5 | 1 | 1.5 | 2 | 3 | 4 | 5 | 6 | 8 | 10;
```
≈ 4px per step (step 6 ≈ 24px). Used by `gap`, `padding`, `paddingX/Y`-style
props on HStack/VStack/Grid. Passing arbitrary numbers → TS error
`Type '24' is not assignable to type 'SpacingStep | undefined'`.

## Component props that surprised

| Component | Truth |
|---|---|
| Button | `label` required; `variant`: primary/secondary/ghost/destructive; `size`: sm/md/lg |
| Badge | variants: neutral/info/success/warning/error/blue/cyan/green/orange/pink/purple/red/teal/yellow (NO primary, NO subtle) |
| Grid | `columns` number OR `{minWidth, max}` for responsive; `gap` SpacingStep |
| HStack/VStack | props: as, align, gap, padding, wrap, className, style; NO Spacer, NO paddingX/paddingY |
| Theme | `Theme` from `@astryxdesign/core/theme`; `neutralTheme` from `@astryxdesign/theme-neutral/built` |

## Theme tokens (neutral)

- `--color-accent: #0074e2` (light-dark: `#262626`/`#ebebeb`)
- Font sizes: `--font-size-4xs` 0.375rem … `--font-size-3xl` 1.8125rem
- Override via CSS custom properties on `[data-astryx-theme]` (or your own
  `:root` cascade — the demo used custom CSS vars layered after the theme CSS).

## StyleX note

`@stylexjs/stylex` is a peer dependency — install it even if you never import it
directly (components import it internally). Component `.d.ts` shows StyleX
class types (`stylex.StyleXClassNameFor<...>`).
