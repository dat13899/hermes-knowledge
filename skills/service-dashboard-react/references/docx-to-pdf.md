# DOCX → PDF Conversion in DocReader

## Server Side (server.js)

### Endpoint: `GET /api/documents/:id/pdf`

```js
// Convert docx to PDF on demand
const mPdf = u.pathname.match(/^\/api\/documents\/([^\/]+)\/pdf$/);
if (mPdf && method === 'GET') {
  const baseName = mPdf[1];
  const docxPath = path.join(DOCS_DIR, baseName + '.docx');
  const pdfPath = path.join(DOCS_DIR, baseName + '.pdf');
  
  if (!fs.existsSync(docxPath)) return json(res, { error: 'not-found' }, 404);
  
  convertDocxToPdf(docxPath, pdfPath, (err) => {
    if (err) return json(res, { error: 'conversion-failed' }, 500);
    const buf = fs.readFileSync(pdfPath);
    res.writeHead(200, {
      'Content-Type': 'application/pdf',
      'Content-Length': buf.length,
      'Cache-Control': 'public, max-age=3600'
    });
    res.end(buf);
  });
}
```

### `convertDocxToPdf()` implementation

Uses LibreOffice headless (soffice.exe on Windows):

```js
const { execFile } = require('child_process');
const sofficePath = 'C:\\Program Files\\LibreOffice\\program\\soffice.exe';

function convertDocxToPdf(inputPath, outputPath, callback) {
  const outDir = path.dirname(outputPath);
  execFile(sofficePath, [
    '--headless',
    '--convert-to', 'pdf',
    '--outdir', outDir,
    inputPath
  ], { timeout: 30000 }, (err) => {
    if (err) return callback(err);
    // LibreOffice names output as <basename>.pdf
    const generated = path.join(outDir, path.basename(inputPath, '.docx') + '.pdf');
    if (generated !== outputPath) {
      try { fs.renameSync(generated, outputPath); } catch(e) { /* already named correctly */ }
    }
    callback(null);
  });
}
```

### Raw .docx download: `GET /api/documents/:id?dl=1`

```js
if (isDl) {
  const buf = fs.readFileSync(filePath);
  res.writeHead(200, {
    'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'Content-Disposition': 'attachment; filename="' + path.basename(filePath) + '"',
    'Content-Length': buf.length
  });
  return res.end(buf);
}
```

### Content fetch (non-download): `GET /api/documents/:id`

When `isDocx=true` and NOT download:
```js
if (isDocx) {
  const buf = fs.readFileSync(filePath);
  return json(res, {
    id: baseName,
    content: buf.toString('base64'),  // raw docx as base64
    ext: 'docx',
    size: buf.length
  });
}
```

**IMPORTANT:** The `content` field for docx is the raw binary as base64 — do NOT try to parse it as markdown or text. The DocReader detects `ext === 'docx'` and renders PDF instead.

## Client Side (DocReader.jsx)

### Detection

```js
const isDocx = doc?.ext === 'docx' || (doc?.file || '').endsWith('.docx');
const pdfUrl = isDocx ? `/api/documents/${doc?.id}/pdf` : null;
```

### Pre-fetch trigger (useEffect)

```js
const [pdfLoading, setPdfLoading] = useState(false);

useEffect(() => {
  if (isDocx) {
    setPdfLoading(true);
    fetch(pdfUrl).finally(() => setPdfLoading(false));
  }
}, [doc?.id, isDocx, pdfUrl]);
```

### Conditional rendering

```jsx
{isDocx ? (
  <div style={s.pdfContainer}>
    {pdfLoading ? (
      <div style={s.pdfLoading}>
        <i className="fas fa-spinner fa-spin" style={{ fontSize: '2rem', opacity: 0.6 }} />
        <span>Đang chuyển đổi DOCX sang PDF...</span>
        <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Quá trình này có thể mất vài giây</span>
      </div>
    ) : (
      <iframe
        style={s.pdfIframe}
        src={pdfUrl}
        title={doc.title}
      />
    )}
  </div>
) : (
  <div
    ref={contentRef}
    style={{ ...s.contentArea, fontSize: `${fontSize}rem` }}
    className="doc-reader-content"
    dangerouslySetInnerHTML={{ __html: renderedHtml }}
  />
)}
```

### PDF iframe styles

```js
pdfContainer: {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  minHeight: 0,
},
pdfIframe: {
  flex: 1,
  border: 'none',
  width: '100%',
  height: '100%',
  minHeight: '400px',
  borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
},
pdfLoading: {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'var(--text-dim)',
  gap: '0.75rem',
  fontSize: '0.9rem',
},
```

### Controls to hide for DOCX

- Font size controls (only for markdown text)
- TOC button (no headings in PDF)
- Edit button (can't edit docx in browser)
- Word count footer (not applicable)

### DOCX badge

```jsx
{isDocx && (
  <span style={{
    fontSize: '0.7rem', padding: '0.15rem 0.5rem',
    borderRadius: '999px',
    background: 'rgba(59,130,246,0.15)',
    color: '#60a5fa',
    border: '1px solid rgba(59,130,246,0.3)',
    fontWeight: 500,
  }}>
    <i className="fas fa-file-word" style={{ marginRight: '0.2rem' }} />
    DOCX
  </span>
)}
```

### Download raw .docx

```js
const handleDownload = useCallback(() => {
  if (isDocx) {
    const a = document.createElement('a');
    a.href = `/api/documents/${doc.id}?dl=1`;
    a.download = (doc.title || doc.id) + '.docx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return;
  }
  onDownloadDoc?.(doc);
}, [onDownloadDoc, doc, isDocx]);
```

## First-load latency

LibreOffice headless conversion takes 2-5 seconds on first access. Subsequent loads are instant because:
1. Server checks `fs.existsSync(pdfPath)` — if cached PDF exists, `convertDocxToPdf` returns cached
2. `Cache-Control: public, max-age=3600` — browser caches for 1 hour
3. Cloudflare caches the PDF response

## Error handling

If LibreOffice fails:
- Server returns 500 with `{ error: 'conversion-failed', detail: err.message }`
- Client should handle fetch errors gracefully (show error state in UI, not crash)
- Currently: fetch `.finally()` sets `pdfLoading=false` even on error — iframe will show browser's native error page for 500
