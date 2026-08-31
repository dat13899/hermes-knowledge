# docx-preview.js API & reference

> **⚠️ Limitation notice**: docx-preview renders .docx as HTML in the browser. For documents where exact page layout matters (A4 margins, page breaks, floating images, complex tables), prefer server-side PDF conversion via LibreOffice headless. See `references/libreoffice-pdf.md`.
>
> docx-preview is best suited for quick previews, text-heavy documents, or scenarios where server-side conversion tools are not available.

## Library info

- **npm**: `docx-preview` (GitHub: `VolodymyrBaydalka/docxjs`)
- **CDN**: `https://cdn.jsdelivr.net/npm/docx-preview@0.4.0/dist/docx-preview.min.js`
- **Dependency**: requires JSZip loaded first
  `https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js`
- **Global**: `docx.renderAsync()`
- **Bundle size**: docx-preview ~200KB minified, JSZip ~100KB minified

## API

```typescript
renderAsync(
  document: Blob | ArrayBuffer | Uint8Array,
  bodyContainer: HTMLElement,      // element to render content into
  styleContainer?: HTMLElement | null,  // null = use bodyContainer
  options?: DocxRenderOptions
): Promise<WordDocument>
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `className` | `"docx"` | Class prefix for generated elements |
| `inWrapper` | `true` | Wrap content in `.docx` container |
| `ignoreWidth` | `false` | If true, let container control width (recommended for embedded viewers) |
| `ignoreHeight` | `false` | If true, let content flow naturally (recommended) |
| `ignoreFonts` | `false` | Skip font rendering |
| `breakPages` | `true` | Break on manual page breaks `<w:br w:type="page"/>` |
| `ignoreLastRenderedPageBreak` | `true` | Set `false` to break on MS Word's auto page breaks |
| `useBase64URL` | `false` | If true, use base64 data URLs for images (slower but compatible everywhere) |
| `renderHeaders` | `true` | Render document headers |
| `renderFooters` | `true` | Render document footers |
| `renderFootnotes` | `true` | Render footnotes |
| `renderEndnotes` | `true` | Render endnotes |
| `renderComments` | `false` | Render comments (experimental) |
| `experimental` | `false` | Enable tab stop calculation (experimental) |
| `debug` | `false` | Logging |

## Usage patterns

### From base64 content (stored in API response)

```javascript
const uint8 = Uint8Array.from(atob(base64Content), c => c.charCodeAt(0));
const container = document.getElementById('article');
container.innerHTML = ''; // clear previous content
await docx.renderAsync(uint8, container, null, {
  inWrapper: true,
  ignoreWidth: true,     // fill container width
  ignoreHeight: true,    // flow naturally
  breakPages: true,
  ignoreLastRenderedPageBreak: false, // show MS Word auto page breaks
  useBase64URL: true     // images as data URLs
});
```

### From File input

```javascript
const file = input.files[0];
docx.renderAsync(file, document.getElementById('container'), null, options);
```

### From fetch/HTTP

```javascript
const response = await fetch('/document.docx');
const blob = await response.blob();
docx.renderAsync(blob, document.getElementById('container'), null, options);
```

## Comparison: docx-preview vs mammoth.js

| Feature | docx-preview | mammoth.js |
|---------|-------------|------------|
| Font size | ✅ inline style | ❌ stripped |
| Font color | ✅ inline style | ❌ stripped |
| Text alignment | ✅ | ❌ (all left) |
| Tables (merged cells) | ✅ | ⚠️ basic |
| Table background | ✅ | ❌ |
| Images (base64/blob) | ✅ | ✅ |
| Headers/footers | ✅ | ❌ |
| Footnotes | ✅ | ❌ |
| Page breaks | ✅ | ❌ |
| Subscript/superscript | ✅ | ❌ |
| Code highlighting | ✅ | ❌ |
| Output | renders into DOM (no HTML string) | returns HTML string |
| Bundle size | ~200KB + 100KB (JSZip) | ~50KB |
| Formatting fidelity | **high** — preserves document appearance | low — semantic HTML, formatting stripped |

**When to use mammoth**: simple text extraction where clean HTML matters more than fidelity (e.g., converting .docx to markdown).

**When to use docx-preview**: any case requiring WYSIWYG fidelity — formatted tables, colored text, aligned paragraphs, headers/footers, page breaks.

## CSS for embedded rendering

docx-preview renders with inline styles from the document. Only constrain the wrapper and media elements:

```css
.container .docx { margin:0; padding:0; background:transparent; }
.container .docx p { margin:0 0 .5rem; }
.container .docx table { border-collapse:collapse; margin:.5rem 0; }
.container .docx img { max-width:100%; height:auto; }
.container .docx .page-break { display:block; border-top:2px dashed #ccc; margin:1.5rem 0; }
```

Do NOT override inline `font-size`, `color`, `font-family` — those come from the document and carry the original formatting.

## Limitations

- Renders into HTML — limited by browser's CSS capabilities (e.g. complex page layout, exact A4 rendering).
- Real-time page breaking (recalculate on each edit) is not implemented.
- TOC fields are not supported (http://officeopenxml.com/WPtableOfContents.php).
- Thumbnail generation is not part of the library.
- Only `renderAsync()` is stable API — internal parsing/rendering may change between minor versions.
