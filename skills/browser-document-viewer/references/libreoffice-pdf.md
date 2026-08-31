# LibreOffice headless PDF conversion — setup & reference

## Install

### Windows (winget)

```bash
winget install --id TheDocumentFoundation.LibreOffice --exact --accept-package-agreements
```

Installs to `C:\Program Files\LibreOffice\program\soffice.exe`.
First run may download ~300MB MSI. Takes 1-3 minutes depending on connection.

### Verify

```bash
"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir "%TEMP%" --help
```

Or just try converting a small docx:
```bash
"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir "." "test.docx"
```

## Node.js endpoint (full)

```javascript
const SOFFICE = 'C:\\Program Files\\LibreOffice\\program\\soffice.exe';
const DOCS_DIR = path.join(__dirname, '..', 'documents');

// GET /api/documents/:id/pdf
const mPdf = u.pathname.match(/^\/api\/documents\/([^\/]+)\/pdf$/);
if (mPdf && method === 'GET') {
  const baseName = mPdf[1];
  const docxPath = path.join(DOCS_DIR, baseName + '.docx');
  if (!docxPath.startsWith(DOCS_DIR)) return json(res, { error: 'invalid' }, 400);
  if (!fs.existsSync(docxPath)) return json(res, { error: 'not-found' }, 404);

  const pdfPath = path.join(DOCS_DIR, baseName + '.pdf');

  if (!fs.existsSync(pdfPath) || fs.statSync(docxPath).mtime > fs.statSync(pdfPath).mtime) {
    try {
      // Convert paths to forward-slash for soffice
      const outDir = DOCS_DIR.replace(/\\/g, '/');
      const inFile = docxPath.replace(/\\/g, '/');
      execSync(`"${SOFFICE}" --headless --convert-to pdf --outdir "${outDir}" "${inFile}"`, {
        timeout: 30000,
        windowsHide: true,
        maxBuffer: 50 * 1024 * 1024, // 50MB for large files
      });
    } catch(e) { return json(res, { error: 'conversion-failed' }, 500); }
  }

  const buf = fs.readFileSync(pdfPath);
  res.writeHead(200, {
    'Content-Type': 'application/pdf',
    'Content-Length': buf.length,
    'Content-Disposition': 'inline',
    'Cache-Control': 'public, max-age=3600',
  });
  return res.end(buf);
}
```

## Frontend (embed)

```javascript
// In loadDoc:
if (currentExt === 'docx') {
  $('article').innerHTML = `<embed src="/api/documents/${curId}/pdf"
    type="application/pdf" style="width:100%;min-height:80vh;border:none">`;
}
```

Loading state (optional, for slow first conversion):
```javascript
if (currentExt === 'docx') {
  $('article').innerHTML = `<p style="color:var(--text-dim);padding:2rem">
    <i class="fas fa-spinner fa-pulse"></i> Đang chuyển đổi...</p>`;
  // The embed loads asynchronously, so the spinner stays until PDF arrives
  const embed = document.createElement('embed');
  embed.src = `/api/documents/${curId}/pdf`;
  embed.type = 'application/pdf';
  embed.style.cssText = 'width:100%;min-height:80vh;border:none';
  // Replace spinner when embed loads
  embed.onload = () => { $('article').innerHTML = ''; $('article').appendChild(embed); };
  // Fallback: just replace after 1s anyway
  setTimeout(() => { $('article').innerHTML = ''; $('article').appendChild(embed); }, 1000);
}
```

## Performance

| Metric | First call | Subsequent calls |
|--------|-----------|-----------------|
| Conversion time | ~12-18s (LibreOffice runtime init) | ~1-3s |
| PDF size (typical A4 docx) | ~65KB for text, ~500KB+ with images | same as cached |
| Memory | soffice uses ~150MB during conversion | 0 (exits after each call) |

## Troubleshooting

### soffice hangs or times out
- Kill leftover soffice processes: `taskkill /f /im soffice.exe`
- Delete lock files: `del /q "C:\Users\datel\documents\.~lock.*"`
- LibreOffice may leave background process `soffice.bin`. Kill it too.

### "cannot find soffice" in execSync
- Verify path: `dir "C:\Program Files\LibreOffice\program\soffice.exe"`
- Check 32-bit vs 64-bit: LibreOffice 64-bit installs to `Program Files`, 32-bit to `Program Files (x86)`
- Use forward slashes or double-escaped backslashes in Node.js string

### Conversion returns empty PDF
- Ensure source docx is valid (open with Word/Google Docs)
- Check soffice stderr for errors: `execSync(..., { stdio: ['pipe', 'pipe', 'pipe'] })`
- LibreOffice may silently fail on corrupted OOXML files

### Vietnamese characters not rendered in PDF
- LibreOffice ships with Cambria + Calibri font families which support Vietnamese diacritics
- Custom fonts: install them on the system first, or embed them in the docx as TrueType
- Check font availability: `fc-list` (not available on Windows by default; use font viewer)

### Concurrent conversion conflicts
LibreOffice creates a lock file `.~lock.<filename>#` in the output directory during conversion.
Two simultaneous calls to soffice for the SAME file may conflict.
**Fix**: always check existence first (mtime cache), so only the first request triggers conversion.

For high-traffic scenarios:
1. Pre-convert all docx files on server start (cron or startup script)
2. Or use a conversion queue with a single soffice listener:
   ```bash
   soffice --headless --accept="socket,host=localhost,port=2002;urp;" --norestore
   ```
   Then use UNO API to convert (more complex, rarely needed for low-traffic viewers).

## Alternative: avoid soffice cache entirely

For one-shot servers or test environments, convert fresh each time (no caching):

```javascript
const fs = require('fs');
const tmpDir = require('os').tmpdir();
const tmpPdf = path.join(tmpDir, baseName + '.pdf');
try {
  execSync(`"${SOFFICE}" --headless --convert-to pdf --outdir "${tmpDir}" "${docxPath}"`, { timeout: 30000 });
  const buf = fs.readFileSync(tmpPdf);
  fs.unlinkSync(tmpPdf); // cleanup
  // serve buf...
} catch(e) { /* handle */ }
```

But caching alongside the docx is preferred — avoids re-converting on every view.
