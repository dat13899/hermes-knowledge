---
name: theme-migration
description: Migrate pages between themes. Preserves all functionality.
---
# Theme Migration

Use when you need to move a page or component from one theme system to another (e.g., glass to pixel fantasy, light to dark, custom to design-token driven).

## Workflow

1. **Audit the target theme** — understand the token system, available components, CSS classes, and CSS custom properties.
2. **Read the current code** — understand the page structure, imports, state management, hooks, and child components.
3. **Rewrite** — replace imports, swap CSS classes, apply new component variants, update empty/loading/error states, set appropriate font vars. Keep all CRUD handlers and state variables untouched.
4. **Verify** — run a systematic check that covers syntax, imports, theme elements, functional preservation, and file structure.

## Verification Checklist

### JSX Syntax
Use `@babel/parser` (not regex) — regex fails on arrow function props (`=>` contains `>` which fools naive tag matchers).

```js
const parser = require('@babel/parser');
const ast = parser.parse(src, {
  sourceType: 'module',
  plugins: ['jsx', 'objectRestSpread', 'optionalChaining', 'nullishCoalescingOperator'],
});
```

### Import Integrity
Every import from the new theme system must resolve. Check for:
- New component imports (`PixelButton`, `PixelCard`, etc.)
- New CSS/stylesheet imports
- Old imports that should have been removed or replaced

### Theme Element Coverage
For every visual requirement in the spec, assert the corresponding theme artifact exists:
- **CSS classes**: `pixel-border`, `pixel-divider`, etc.
- **CSS custom properties**: `--font-pixel`, `--font-sans`, `--ember-gold`, etc.
- **Component variants**: `variant="parchment"`, `variant="gold"`, `variant="danger"`
- **Icon replacements**: fantasy emoji or new icon components
- **Empty/loading/error states**: updated to match the new theme

### Functional Preservation
The page must handle the same lifecycle after the rewrite. Check:
- All handler function references (`handleCreateDoc`, `handleDelete`, etc.)
- All state variables (`searchQuery`, `sortBy`, `selectedTags`, etc.)
- All hook calls (`useDocuments`, `useToastContext`, `useMediaQuery`)
- All child-component props match the original interface
- Default export name unchanged

### File Structure Sanity
- Line count in a reasonable range (not truncated or bloated)
- Balanced parentheses and braces
- Correct export format (match what lazy import expects)

## Pitfalls
- **Arrow function `=>` breaks regex tag matchers**: Always use Babel parser, never regex, for JSX syntax validation. The `=>` token contains `>` which causes regex to match on the wrong `>` and misclassify self-closing tags.
- **Inline styles hide theme gaps**: CSS class name presence is a stronger verification signal than inline style properties. The spec may call for classes like `pixel-border` but the rewrite might accidentally use inline styles instead — verify class names are present.
- **Conditional rendering hides branches**: An expression like `{cond ? <A/> : <B/>}`. When scanning for function preservation, both branches may not appear in simple text search — verify branch variables are still referenced, not just the active branch visible in source order.
- **Exports must match lazy imports**: `App.jsx` typically uses `const Page = lazy(() => import('./...'))` — the export name must stay stable or the app won't render.
- **Children vs self-closing conversion**: Components can switch between self-closing (`<PixelButton .../>`) and wrapping (`<PixelButton>text</PixelButton>`) forms during a rewrite. Verify all prop bindings survive the form change.
