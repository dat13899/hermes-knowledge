# Page layout view — reference implementation

## Background

User wanted reading view to look like Google Docs mobile: white page on dark desk surface, not a print dialog. The 🖨 button should just call `window.print()` (browser-native print preview). The reading view itself is the "page layout".

## Key CSS variables

```css
[data-theme="dark"] {
  --page: #fff;           /* article bg — always white like paper */
  --surface-2: #1e293b;   /* desk surface around the paper */
}
[data-theme="light"] {
  --page: #fff;
  --surface-2: #f1f5f9;   /* lighter desk surface for light mode */
}
```

## Reader structure

```
.layout (display:grid; grid-template-columns:260px 1fr; height:calc(100vh - 52px))
├── .sidebar (260px, height:100%, flex column — doc list)
└── .reader (height:100%, flex column, overflow:hidden)
    ├── .reader-header (flex:0 — title, meta, action buttons)
    └── .reader-content (flex:1 1 0, min-height:0, overflow-y:auto, bg:var(--surface-2))
        └── .article (max-width:780px, margin:2rem auto, bg:var(--page), color:#1e293b, padding, shadow)
```

Note: `.layout` uses CSS grid (not flex) to give definite height to both columns. Grid cells get `height: 100%` from `calc(100vh - 52px)` on the grid container. Inside each cell, flex handles internal layout. This avoids the nested-flexbox scroll bug where children can't shrink below content height.

Mobile override: `.reader` becomes `position:fixed; inset:52px 0 0; min-height:0` — definite height via positioning, same internal flex chain.

## Article children — fixed colors

Article uses hardcoded light-theme colors (NOT CSS vars) to always look like paper:

| Element      | Colors                                     |
|-------------|--------------------------------------------|
| h1, h2, h3  | `#0f172a` (very dark)                      |
| body p      | `#1e293b` (dark)                           |
| code        | bg `#f1f5f9`, text `#0f172a`              |
| pre         | bg `#f8fafc`, border `#e2e8f0`            |
| blockquote  | left border `#6366f1`, text `#64748b`     |
| table th/td | border `#e2e8f0`, th bg `#f8fafc`         |
| hr          | `#e2e8f0`                                  |
| img         | `max-width:100%`, `box-shadow`, rounded    |
| links       | `#6366f1` hover `#4f46e5`                 |

## Mobile breakpoint

```css
@media(max-width:720px) {
  .reader-content .article {
    margin: .75rem auto;
    padding: 1rem 1.2rem;
  }
}
```

## Print (window.print)

```javascript
function onPrint() { window.print(); }
```

`@media print` CSS:
- Hide everything except `.layout`
- Inside layout: hide `.sidebar`, `.reader-header`, `.theme-btn`
- `.reader-content` becomes visible, no padding/no background
- `.article` loses max-width, margin, padding, shadow, border-radius
- page-break helpers on pre, img, h1-h4
