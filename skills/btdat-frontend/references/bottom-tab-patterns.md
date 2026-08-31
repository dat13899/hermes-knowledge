# Bottom Tab / Floating Navigation Patterns (from BottomTab.jsx)

## Recurring Bugs & Fixes

### 1. Labels hidden behind conditional render
**Bad:**
```jsx
{active && <span>{tab.label}</span>}
```
→ Inactive tabs have no label, breaking visual structure.

**Good:**
```jsx
<span style={{ opacity: active ? 1 : 0.45, transition: 'all 0.2s ease' }}>
  {tab.label}
</span>
```
→ Always renders, differentiates active via opacity + font weight.

### 2. Fixed-width items overflow pill
**Bad:**
```jsx
width: active ? '72px' : '56px'  // per tab — different widths
width: '44px'                      // More button — yet another size
```
→ Total width unpredictable, More button clips pill edge.

**Good:**
```jsx
flex: '1 1 0'
minWidth: 0
```
→ ALL items (tabs + More) share equal width. Pill bounds via `minWidth`/`maxWidth` on nav container.

### 3. More button uses different layout structure than tabs
**Bad:** flex row, icon only, no label, different height → looks broken.
**Good:** Same column layout as tabs — `flexDirection: 'column'`, icon + label, equal `height: '54px'`.

### 4. Safe area CSS var wrong
**Bad:** `bottom: 'calc(14px + var(--safe-bottom))'`
**Good:** `bottom: 'calc(14px + env(safe-area-inset-bottom, 0px))'`
→ iOS `env()` constant with fallback. Works on all devices.

### 5. Background glow inset asymmetry
**Bad:** `inset: '3px 4px'` on one, `inset: '2px 2px'` elsewhere
**Good:** `inset: '2px 2px'` symmetric on all items.

## Ad-hoc Verification (no test suite)

When project has no UI component tests, verify source correctness with Node.js regex:

```bash
node -e "
const src = require('fs').readFileSync('src/components/layout/BottomTab.jsx','utf-8');

// Labels not inside conditional
const spanIdx = src.indexOf('{tab.label}');
const before = src.substring(0, spanIdx);
const lastCond = before.lastIndexOf('{active &&');
const lastMap = before.lastIndexOf('.map(');
console.log('Label in conditional?', lastCond > lastMap);

// Equal width: flex 1 1 0 appears once in map + once for More = 5 rendered items
const flexCount = (src.match(/flex:\s*'1 1 0'/g)||[]).length;
console.log('flex 1 1 0:', flexCount, '(expect 2 for 5 items)');

// No dynamic widths, safe area
console.log('Has 72px:', src.includes('72px'));
console.log('Safe area:', src.includes('env(safe-area-inset-bottom'));
"
```

Key checks: no `{active &&` wrapping content, no hardcoded px widths on nav items, `env()` safe-area, consistent heights.
