# Style consistency — Site design variables + button + layout patterns

Khi thêm UI element mới vào trang có sẵn: KHÔNG dùng inline styles.
Luôn copy pattern CSS từ element cùng loại trên cùng trang. Dùng `var(--glass-*)` cho glass surfaces, ko `var(--border)`.

## Core design variables

| Variable | Usage |
|---|---|
| `--glass-bg` | Semi-transparent frosted bg (card/surface/toolbar) |
| `--glass-border` | Subtle border for glass surfaces (dùng ưu tiên) |
| `--border` | Standard border (darker/solid hơn, dùng nếu ko phải glass — background bars, skeleton gradients) |
| `--glass-shadow` | Shadow cho glass elements: `0 8px 32px var(--glass-shadow)` |
| `--surface-2` | Hover/active background |
| `--text` | Body text |
| `--text-strong` | Heading/label |
| `--text-dim` | Muted/secondary |
| `--accent` | Primary (indigo) |
| `--green` | Success |
| `--red` | Danger |
| `--amber` | Warning |
| `--radius-sm` | 6px — buttons, inputs, small panels |
| `--radius-md` | 12px — stat cards, svc cards, widget cards, player area |
| `--radius-lg` | 16px — glass-card, main panels |
| `--radius-xl` | 20px (sparingly — hero cards, large modals) |

Thay hardcoded `border-radius:12px`, `border-radius:8px`, `border-radius:6px` bằng `var(--radius-md)`, `var(--radius-sm)` tương ứng. Batch replace across all pages.

## Glass surface pattern

Mọi element có glass style PHẢI có đủ 3 thuộc tính:

```css
.glass-surface {
  background: var(--glass-bg);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
}
```

Thêm `border-radius: 12px` + `box-shadow: 0 8px 32px var(--glass-shadow)` nếu là card riêng biệt.

## Button patterns

### Glass ghost button (ưu tiên dùng cho toolbars)

```css
.my-btn {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 5px;
  color: var(--text-dim);
  padding: .25rem .55rem;
  font-size: .7rem;
  cursor: pointer;
  transition: .15s;
  line-height: 1.4;
}
.my-btn:hover {
  background: rgba(255,255,255,.08);
  color: var(--text);
  border-color: var(--accent);
}
```

### Global button classes (in global.css, use directly)

```html
<!-- Ghost: glass bg, subtle border, dim text → hover accent -->
<button class="btn-ghost">↻ Refresh</button>

<!-- Primary: solid accent fill, white text -->
<button class="btn-primary">✓ Save</button>

<!-- Danger variant: red border + text -->
<button class="btn-ghost btn-danger">✕ Delete</button>

<!-- Small variant -->
<button class="btn-ghost btn-sm">✕</button>

<!-- Icon-only -->
<button class="btn-icon">☰</button>
```

### Section headings

```html
<h2 class="section-title"><span class="section-icon">📦</span> Services</h2>
<p class="section-sub">3 services — 2 running</p>
```

### Outline glass variant (accent / green — hover fill)

```css
.my-btn.accent { color: var(--accent); border-color: var(--accent); background: var(--glass-bg); }
.my-btn.accent:hover { background: var(--accent); color: #fff; }
.my-btn.green  { color: var(--green);  border-color: var(--green);  background: var(--glass-bg); }
.my-btn.green:hover  { background: var(--green);  color: #fff; }
```

### Icon-only variant (toggle buttons, ☰)

```css
.my-btn.icon-only { background: none; border: none; font-size: .9rem; padding: 0; color: var(--text-dim); }
.my-btn.icon-only:hover { background: none; color: var(--text); }
```

## App-style page → homepage glass card layout

Khi trang có layout app (sidebar + reader full-height, documents page), restyle để match homepage:

```css
/* Before: full-height viewport, sát viền */
.layout { height: calc(100vh - 52px); }
.sidebar { border-right: 1px solid var(--border); height: 100%; }

/* After: glass cards floating, canh giữa */
.layout {
  display: flex;
  gap: .8rem;
  padding: .8rem;
  max-width: 1320px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  height: calc(100vh - 96px);
}
.sidebar {
  border-radius: 16px;
  box-shadow: 0 8px 32px var(--glass-shadow);
  border: 1px solid var(--glass-border);
  overflow: clip;  /* clip border-radius, allow dropdowns inside */
}
.reader {
  border-radius: 16px;
  box-shadow: 0 8px 32px var(--glass-shadow);
  border: 1px solid var(--glass-border);
  /* no border-left — card separated by gap */
}
```

## Glass classes already in global.css

Don't redefine — use these directly:

| Class | Properties |
|---|---|
| `.glass` | `background:var(--glass-bg); backdrop-filter:blur(20px); border:1px solid var(--glass-border); box-shadow:0 8px 32px var(--glass-shadow)` |
| `.glass-card` / `.card.glass-card` | Same as `.glass` + `border-radius:16px` + hover lift/scale |
| `.navbar.is-glass` | Fixed nav, transparent bg, scroll→glass blur |

```html
<div class="card glass-card">...</div>
```

## Comprehensive "glass sweep" approach

When user says page doesn't look like homepage liquid glass, **don't incrementally tweak**. Do ONE comprehensive sweep:

1. **Find all `var(--border)`** in the page's CSS → replace each with `var(--glass-border)` in border properties. `--border` is opaque which ruins the glass illusion. Keep `var(--border)` ONLY in background/gradient contexts (progress bars, skeleton shimmer).

2. **Add border-radius to main panels**: sidebar, reader, card containers → `border-radius:12px` or `16px`.

3. **Add box-shadow**: `0 8px 32px var(--glass-shadow)` on all glass panels.

4. **Repair input/search fields**: use `background:rgba(255,255,255,.06)` + `border:1px solid var(--glass-border)` + `border-radius:8px`.

5. **Repair hover states**: use `rgba(255,255,255,.06)` background + accent border, not `var(--surface-2)`.

6. **Add blob-container** if missing — 4 `<div class="blob">` in `class="blob-container"`.

7. **Center layout**: `max-width:1320px; margin:0 auto; padding:.8rem; gap:.8rem`.

## The full-pass rule

**NEVER apply liquid glass via 3+ incremental small patches.** User will reject each one with escalating frustration (`"để ý style ý"` → `"chưa giống"` → `"khác hẳn"`). Always do the full sweep in one pass.

Signals that you're doing incremental wrong-fixes:
- You're adding inline `style=""` to fix a visual issue → STOP, use CSS class
- You're changing only 1-2 elements → STOP, check ALL elements with `var(--border)`/`no-border-radius`
- You're fixing one button's border when 5 others have the same wrong style → STOP, fix all at once

## Utility classes pattern (reusable across pages)

Khi cleanup inline styles, tạo utility classes dùng chung:

```css
/* Spacing */
.mt-1{margin-top:.3rem}  .mt-2{margin-top:.5rem}  .mt-3{margin-top:.8rem}
.mb-1{margin-bottom:.3rem}  .mb-2{margin-bottom:.5rem}
.ml-1{margin-left:6px}  .m-0{margin:0}
/* Layout */
.flex-1{flex:1}  .jcc{justify-content:center}  .jcc-mt{justify-content:center;margin-top:.6rem}
.tc{text-align:center}  .tl{text-align:left}
/* Typography */
.fs-sm{font-size:.75rem;color:var(--text-dim)}
.fs-xs{font-size:.7rem;color:var(--text-dim)}
.fs-muted{font-size:.8rem;color:var(--text-dim)}
.fw-400{font-weight:400;color:var(--text-dim)}
.op-5{opacity:.5}
/* Display */
.dn{display:none}  .cursor-dflt{cursor:default}
/* Colors */
.bg-red{background:#ef4444}  .bg-green{background:#22c55e}
.tag.accent{background:var(--accent);color:#fff}
/* Page-specific — documents */
.doc-icon-btn{background:none;border:none;color:var(--text-dim);cursor:pointer;padding:0}
.doc-icon-sm{background:none;border:1px solid var(--glass-border);border-radius:5px;color:var(--text-dim);padding:.2rem .5rem;font-size:.8rem;cursor:pointer}
.editor-input{background:var(--surface-2);border:1px solid var(--glass-border);border-radius:5px;color:var(--text);padding:.25rem .5rem;font-size:.75rem;outline:none}
.editor-btn-accent{background:var(--accent);color:#fff;border:none;border-radius:5px;padding:.3rem .7rem;font-size:.8rem;cursor:pointer;font-weight:600}
.editor-btn-ghost{background:none;border:1px solid var(--glass-border);border-radius:5px;color:var(--text-dim);padding:.3rem .7rem;font-size:.8rem;cursor:pointer}
.mono-textarea{min-height:160px;font-family:monospace;font-size:.85rem}
/* Page-specific — dashboard */
.col-header{margin-bottom:.3rem}  .tab-desc{font-size:.75rem;margin-bottom:.3rem}
.dashed-btn{border-style:dashed;flex:1}
```

### Inline style cleanup workflow

1. Scan: `grep -oP 'style="[^"]{8,80}"' file.html | sort | uniq -c | sort -rn`
2. Group >=2 occurrences → utility class. Single if generic.
3. Skip: JS template literals, widget-specific colors, animation-delay random
4. Python batch replace: `str.replace(old, new)` per pattern
5. Add utility classes to page `<style>` block
6. Verify: `grep -c 'style="' file.html` — target <15 small, <30 large

## Pitfall: solid accent buttons vs outline glass buttons

Old style (doc-toolbar New/Upload): `background:var(--accent); color:#fff; border:none;` + `border-radius:6px`.

Liquid glass style (homepage): `background:var(--glass-bg); color:var(--accent); border:1px solid var(--accent);` → hover fills solid accent.

Use outline glass for toolbar buttons (`accent`/`green` variants), not solid fill. Exception: primary CTA buttons on landing page can be solid.

## Systematic large-scale CSS variable replacement

Khi cần thay `var(--border)` → `var(--glass-border)` trên multiple files:

```bash
# Use Python for precise replacement (border properties only, skip background)
python -c "
import re
for fname in ['page1.html','page2.html']:
    with open(fname, encoding='utf-8') as f: content = f.read()
    def replace_border(m):
        full = m.group(0); prop = m.group(1)
        if prop and 'background' in prop.lower(): return full
        return full.replace('var(--border)', 'var(--glass-border)')
    content = re.sub(r'([a-zA-Z-]+\\s*:\\s*[^;}]*?)var\\(--border\\)', replace_border, content)
    with open(fname, 'w', encoding='utf-8') as f: f.write(content)
"
```

Then verify: `grep -nP 'border[^:]*:\\s*[^;]*var\\(--border\\)' *.html` → should return nothing.

## When to use inline styles (by exception only)

- 1-2 properties that truly differ (e.g. margin-left to nudge)
- Dynamic values from JS (e.g. display:none on hidden elements)
- Never for: backgrounds, borders, colors, padding, font-size, border-radius

## User signals

| User says | Meaning | Fix |
|---|---|---|
| "để ý style ý" | Dùng inline styles thay vì CSS class + design vars | Extract thành CSS class, dùng `--glass-bg`, `--glass-border` |
| "Nhìn chưa giống style liquid glass như ở trang chủ" | Element thiếu glass-bg, backdrop-filter, glass-border, box-shadow | Thêm `background:var(--glass-bg)`, `backdrop-filter:blur(16px)`, `border:1px solid var(--glass-border)`, `box-shadow:0 8px 32px var(--glass-shadow)` |
| "màn này ý nhìn khác hẳn style trang chủ" | Layout khác biệt (full-height app panel vs content page) | Thêm max-width, padding, gap, border-radius, box-shadow — biến panel thành card nổi |
| "có 2 div col-header nhìn xấu quá" trên mobile | Running/stopped counters tách riêng 1 row → Services title row → tốn chỗ | Gộp cả 2 vào 1 `<div class="level col-header">`: **level-left** = title + counters kế nhau; **level-right** = layout toggle. Xem `references/dashboard-layout.md`.
