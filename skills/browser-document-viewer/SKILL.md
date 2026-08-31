---
name: "browser-document-viewer"
title: "Browser Document Viewer"
description: "Build a web document viewer that renders .md (marked.js) and .docx (via server-side LibreOffice → PDF) in the browser — hash routing, upload, CRUD API, Bulma UI"
category: "software-development"
triggers: ["documents viewer", "docx viewer", "markdown viewer", "render docx in browser", "docx-preview", "document management", "web file viewer", "read docx online", "browser document", "libreoffice pdf", "docx to pdf", "react document viewer", "vite document editor", "react markdown editor", "react doc viewer jsx", "useDocuments hook", "documents page react"]
version: "3.0"
---

## Mô tả

Web document viewer tích hợp trong Node.js server — render .md (markdown) và .docx (Word) trực tiếp trong browser.

> **React/Vite users:** This skill covers the vanilla JS approach. For the **React 19 + Vite 6 + React Router 7** variant of the same document viewer, see `references/react-document-viewer.md`. Same concepts (sidebar, reader, editor, marked.js rendering, TOC, reading progress, auto-save) but implemented as JSX components with hooks and inline styles.

**Two rendering paths for .docx:**
1. **Preferred: LibreOffice headless → PDF** — highest fidelity, preserves page layout, fonts, tables, images exactly as in Word. Served via `<embed>` in the browser's native PDF viewer.
2. **Fallback: docx-preview.js** — client-side HTML rendering, faster (no server conversion), lower fidelity. Use for quick previews where exact page layout doesn't matter.

## Kiến trúc

```
┌──────────────────────────────────────────────────┐
│  Node.js server (zero dep except LibreOffice)    │
│  ┌────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │Static  │  │Docs API  │  │LibreOffice soffice│ │
│  │/public │  │CRUD      │  │docx → PDF on-demand│ │
│  │*.html  │  │md + docx │  │PDF cached on disk  │ │
│  └────────┘  └──────────┘  └──────────────────┘ │
│                                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │ Frontend (single HTML)                       │ │
│  │  marked.js → .md → HTML                      │ │
│  │  <embed> → .docx → PDF (preferred)           │ │
│  │  docx-preview.js → .docx → HTML (fallback)   │ │
│  │  Bulma CSS → UI                              │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## CDN dependencies (minimal, no docx-preview if using PDF)

```html
<script src="https://cdn.jsdelivr.net/npm/marked@5/marked.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1/css/bulma.min.css">
```

Only add JSZip + docx-preview when using the client-side fallback:
```html
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/docx-preview@0.4.0/dist/docx-preview.min.js"></script>
```

## PDF conversion via LibreOffice (preferred approach)

### Install LibreOffice on Windows

```bash
winget install --id TheDocumentFoundation.LibreOffice --exact --accept-package-agreements
```

Installs to `C:\Program Files\LibreOffice\program\soffice.exe`.

### Node.js endpoint

```javascript
const SOFFICE = 'C:\\Program Files\\LibreOffice\\program\\soffice.exe';
const DOCS_DIR = path.join(__dirname, '..', 'documents');

// GET /api/documents/:id/pdf — convert docx to PDF and serve
const mPdf = u.pathname.match(/^\/api\/documents\/([^\/]+)\/pdf$/);
if (mPdf && method === 'GET') {
  const baseName = mPdf[1];
  const docxPath = path.join(DOCS_DIR, baseName + '.docx');
  if (!docxPath.startsWith(DOCS_DIR)) return json(res, { error: 'invalid' }, 400);
  if (!fs.existsSync(docxPath)) return json(res, { error: 'not-found' }, 404);

  const pdfPath = path.join(DOCS_DIR, baseName + '.pdf');

  // Convert if PDF doesn't exist or docx is newer
  if (!fs.existsSync(pdfPath) || fs.statSync(docxPath).mtime > fs.statSync(pdfPath).mtime) {
    try {
      const outDir = DOCS_DIR.replace(/\\/g, '/');
      const inFile = docxPath.replace(/\\/g, '/');
      execSync(`"${SOFFICE}" --headless --convert-to pdf --outdir "${outDir}" "${inFile}"`, {
        timeout: 30000, windowsHide: true
      });
    } catch(e) { return json(res, { error: 'conversion-failed' }, 500); }
  }

  const buf = fs.readFileSync(pdfPath);
  res.writeHead(200, {
    'Content-Type': 'application/pdf',
    'Content-Length': buf.length,
    'Cache-Control': 'public, max-age=3600',
  });
  return res.end(buf);
}
```

### Frontend (embed PDF in reader)

```javascript
if (currentExt === 'docx') {
  $('article').innerHTML = `<embed src="/api/documents/${curId}/pdf"
    type="application/pdf" style="width:100%;min-height:80vh;border:none">`;
}
```

### LibreOffice conversion characteristics

- **First run slow (~15s)**: LibreOffice initializes its runtime on first call. Subsequent calls instant.
- **Cached**: PDF is saved alongside the docx file. Only re-converts when docx is newer.
- **Fidelity**: 100% — preserves fonts (embedded TrueType), page layout (A4 margins), tables (merged cells, borders, backgrounds), images, headers/footers. Output is standard PDF 1.7.
- **Font handling**: Cambria, Calibri, and common fonts are available out of box. Custom fonts not installed on the system may fall back.
- **Concurrent conversion**: LibreOffice uses a lock file — concurrent calls may conflict. Either serialize or use a queue. For low-throughput viewers (<1 req/s), a simple lock suffices.

See `references/libreoffice-pdf.md` for complete setup and troubleshooting.

## Conditional rendering (md vs docx)

```javascript
async function renderDoc(data) {
  if (data.ext === 'docx') {
    // Preferred: serve PDF via embed (LibreOffice conversion)
    $('article').innerHTML = `<embed src="/api/documents/${data.id}/pdf"
      type="application/pdf" style="width:100%;min-height:80vh;border:none">`;
  } else {
    $('article').innerHTML = marked.parse(data.content || '');
    $('article').querySelectorAll('a').forEach(a => {
      if (a.href) a.target = '_blank';
    });
  }
}
```

### Fallback path (client-side docx-preview, no PDF conversion)

Use when LibreOffice is not available or for quick previews where exact page layout doesn't matter:

```javascript
if (data.ext === 'docx') {
  $('article').innerHTML = '';
  const uint8 = Uint8Array.from(atob(data.content), c => c.charCodeAt(0));
  await docx.renderAsync(uint8, $('article'), null, {
    inWrapper: false,
    breakPages: true,
    ignoreLastRenderedPageBreak: false,
    useBase64URL: true
  });
}
```

With `inWrapper: false` to avoid the page-width wrapper. Content fills the container naturally.

---

## Backend API (Node.js) — common patterns

### Serve .docx as base64 (for client-side docx-preview)

```javascript
const buf = fs.readFileSync(filePath);
res.end(JSON.stringify({ id: 'doc-id', content: buf.toString('base64'), ext: 'docx', size: buf.length }));
```

### Serve .docx as file download

```javascript
res.writeHead(200, {
  'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'Content-Disposition': 'attachment; filename="file.docx"',
  'Content-Length': buf.length
});
res.end(buf);
```

### Upload .docx (base64 JSON — no multipart needed)

Backend route (POST /api/documents/upload):
```javascript
const { title, data } = JSON.parse(body);
const id = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || Date.now().toString(36);
const buf = Buffer.from(data, 'base64');
fs.writeFileSync(path.join(DOCS_DIR, id + '.docx'), buf);
res.end(JSON.stringify({ ok: true, id }));
```

Frontend:
```javascript
function openUpload() { document.getElementById('upload-input').click(); }

function uploadFile(input) {
  const f = input.files[0]; if (!f) return;
  const title = prompt('File name:', f.name.replace(/\.docx$/i, ''));
  if (!title) { input.value = ''; return; }
  const reader = new FileReader();
  reader.onload = async (e) => {
    const data = e.target.result.split(',')[1]; // strip "data:...;base64,"
    const r = await fetch('/api/documents/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, data })
    });
    const d = await r.json();
    if (d.ok) { await loadList(); loadDoc(d.id); }
    input.value = '';
  };
  reader.readAsDataURL(f);
}
```

Note: uses `prompt()` for rename before upload. The `id` is generated by slugifying the `title`.

### List both .md and .docx

```javascript
const files = fs.readdirSync(DOCS_DIR)
  .filter(f => f.endsWith('.md') || f.endsWith('.docx'))
  .sort().reverse()
  .map(f => {
    const ext = path.extname(f).toLowerCase();
    const stat = fs.statSync(path.join(DOCS_DIR, f));
    if (ext === '.docx') {
      return { id: f.replace(/\.docx$/, ''), file: f, title: f.replace(/\.docx$/, ''), ext: 'docx', size: stat.size };
    }
    // .md: parse frontmatter for title/date/tags
    const raw = fs.readFileSync(...);
    const m = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    // extract meta from frontmatter
    return { id: f.replace(/\.md$/, ''), file: f, title: meta.title || id, ext: 'md', ... };
  });
```

### .md frontmatter format

```markdown
---
title: Document Title
date: 2026-07-23
tags: tag1, tag2
status: draft
---

Body content here...
```

`status: draft` — used for draft filter checkbox, shows ✏️ badge in sidebar.

On read, strip frontmatter — return only body as `content`.

### Path traversal protection

```javascript
const filePath = path.join(DOCS_DIR, fileName);
if (!filePath.startsWith(DOCS_DIR)) return res.end(JSON.stringify({ error: 'invalid' }));
```

## Frontend

### Layout

```
┌──────────────────────────────┐
│ Top bar: brand | [New][Upload]│
├──────────────┬───────────────┤
│ Sidebar 260px │ Reader        │
│ Search input  │ Header (title)│
│ Doc list      │ Meta (date)   │
│ (active item) │ Article body  │
│ Footer count  │ (rendered /   │
│               │  PDF embed)   │
└──────────────┴───────────────┘
```

Main container uses **CSS grid** (not nested flex) to give both columns a definite viewport height:

```css
.layout{ display:grid; grid-template-columns:260px 1fr; min-height:0; height:calc(100vh - 52px); }
.sidebar, .reader{ height:100%; }
```

Inside each grid cell, standard flex controls internal layout:
- `.sidebar` = flex column (search + doc list + footer)
- `.reader` = flex column (reader-header + reader-content)

The article body fills `width:100%` of the reader (no `max-width` constraint — prevents docx content from overflowing):

```css
.reader-content{ flex:1 1 0; min-height:0; overflow-y:auto; padding:2rem 1.5rem; background:var(--bg); }
.reader-content .article{ width:100%; line-height:1.8; font-size:.95rem; }
```

Mobile: `.reader` switches to `position:fixed; inset:52px 0 0` to overlay the sidebar.

### docx-preview CSS (fallback only)

When using docx-preview client-side, add CSS to contain output, prevent image/table overflow:

```css
.reader-content .article .docx{ width:100%; overflow-x:auto; }
.reader-content .article .docx p{ margin:0 0 .5rem; }
.reader-content .article .docx img{ max-width:100%; height:auto; }
.reader-content .article .docx table{ max-width:100%; }
```

Do NOT override inline `font-size`, `color`, `font-family` — those come from the document's own formatting via docx-preview's inline styles.

See `references/docx-preview.md` for complete API reference and rendering options.

### Hash routing for shareable links

```javascript
function setHash(id) { history.replaceState(null, '', '#' + encodeURIComponent(id)); }
function clearHash() { history.replaceState(null, '', ' '); }

window.addEventListener('hashchange', () => {
  const h = location.hash.slice(1);
  if (h && h !== curId && docs.find(d => d.id === h)) loadDoc(h);
});

// On page load: open doc from hash
if (location.hash.slice(1)) {
  setTimeout(() => {
    loadList().then(() => {
      const h = location.hash.slice(1);
      if (docs.find(d => d.id === h)) loadDoc(h);
    });
  }, 100);
}
```

Note: `history.replaceState` with empty string for clearing hash must pass `' '` (space), not `''` (empty — may create empty URL).

### Editor (for .md only)

Full-screen overlay, split layout:
- Left: `<textarea>` for markdown
- Right: live preview (re-render on `input` event)

```javascript
function updatePreview() {
  try { preview.innerHTML = marked.parse(editor.value || ''); } catch(e) {}
}
editor.addEventListener('input', updatePreview);
```

Save: PUT /api/documents/:id with `{ content, tags }` → close editor → refresh reader.

### Inline rename (double-click title)

Double-click title text → hidden input field appears → Enter saves (POST /api/documents/:id/rename) → Escape/Cancel restores. Title is slugified server-side for filename.

```javascript
function renameStart() {
  if (currentExt !== 'md') return;
  titleEl.style.display = 'none';
  titleInputEl.style.display = '';
  titleInputEl.value = titleEl.textContent;
  titleInputEl.focus(); titleInputEl.select();
}
async function renameSave() {
  const v = titleInputEl.value.trim();
  if (!v || v === titleEl.textContent) { renameCancel(); return; }
  titleInputEl.style.display = 'none';
  const r = await fetch(API + '/' + curId + '/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: v }) });
  const d = await r.json();
  if (d.ok) { if (d.id !== curId) curId = d.id; await loadList(); loadDoc(curId); }
  else { titleEl.style.display = ''; }
}
```

HTML: `span.title (ondblclick)` + `input.title-input (onkeydown/onblur)`, hidden by default.

### Sorting dropdown

```html
<select id="sort-select" onchange="renderList()">
  <option value="newest">Newest</option>
  <option value="oldest">Oldest</option>
  <option value="name-asc">A→Z</option>
  <option value="name-desc">Z→A</option>
</select>
```

```javascript
function getSortFn() {
  const v = sortSelect.value;
  if (v === 'newest') return (a,b) => new Date(b.created) - new Date(a.created);
  if (v === 'oldest') return (a,b) => new Date(a.created) - new Date(b.created);
  if (v === 'name-asc') return (a,b) => a.title.localeCompare(b.title);
  if (v === 'name-desc') return (a,b) => b.title.localeCompare(a.title);
}
```

### Tag filter chips

Auto-extract unique tags from all docs. Click chip filters by tag:

```javascript
function renderTagFilter() {
  const tags = [...new Set(docs.flatMap(d => (d.tags||'').split(',').map(t=>t.trim()).filter(Boolean)))].sort();
  filterEl.innerHTML = '<button class="tag-chip active" onclick="setTag(null)">All</button>' +
    tags.map(t => `<button class="tag-chip" onclick="setTag('${esc(t)}')">${esc(t)}</button>`).join('');
}
```

`.tag-chip.active { background:var(--accent); color:#fff; }`

### Draft filter checkbox

In sort bar: `<input type="checkbox" id="status-filter" onchange="renderList()"> Draft`. Filter: `f = f.filter(d => d.status === 'draft')`. Docs with `status: draft` in frontmatter show ✏️ badge in meta.

### Word count + read time

Appended after article content:

```javascript
const words = md.trim() ? md.split(/\s+/).length : 0;
const chars = md.length;
const mins = Math.max(1, Math.ceil(words / 200));
const wc = document.createElement('div');
wc.className = 'word-count';
wc.textContent = '📝 ' + words.toLocaleString() + ' từ · ' + chars.toLocaleString() + ' ký tự · 📖 ' + mins + ' ph đọc';
article.appendChild(wc);
```

### Table of Contents

Built from rendered HTML's h1/h2/h3. Toggle dropdown in reader header:

```javascript
function buildToc(html) {
  const tmp = document.createElement('div'); tmp.innerHTML = html;
  const links = [];
  tmp.querySelectorAll('h1,h2,h3').forEach(h => {
    const level = h.tagName.slice(1);
    const id = 'toc-' + (links.length + 1);
    h.id = id;
    links.push({ level, text: h.textContent, id });
  });
  tocEl.innerHTML = links.map(l => `<a class="toc-h${l.level}" href="#${l.id}" onclick="closeToc()">${esc(l.text)}</a>`).join('');
}
```

Position reader header's TOC button. `.toc-drop` positioned absolute, max-height 300px, scrollable. Close on outside click.

### Reading progress bar

Fixed thin bar at top of reader:

```css
.reading-progress { position:fixed; top:52px; left:0; height:3px; background:var(--accent); z-index:200; transition:width .1s; width:0; }
```

```javascript
readerContent.addEventListener('scroll', function() {
  const h = this.scrollHeight - this.clientHeight;
  if (h <= 0) return;
  progressBar.style.width = Math.min(100, Math.round(this.scrollTop / h * 100)) + '%';
});
```

### Font size controls

A−/A+ buttons in top bar. Adjust CSS custom property:

```javascript
function fontSize(delta) {
  const r = document.querySelector(':root');
  let cur = parseFloat(getComputedStyle(r).getPropertyValue('--font-size')) || .95;
  cur = Math.max(.7, Math.min(1.5, cur + delta * .05));
  r.style.setProperty('--font-size', cur + 'rem');
}
```

### Auto-save (debounce 3s)

In editor textarea input handler:

```javascript
editor.addEventListener('input', function() {
  clearTimeout(autoSaveTimer);
  indicator.textContent = 'Unsaved changes…';
  indicator.className = 'auto-save saving';
  autoSaveTimer = setTimeout(async () => {
    if (!editorOverlay.classList.contains('show')) return;
    await fetch(API + '/' + curId, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: editor.value, tags: tagsInput.value }) });
    indicator.textContent = '✓ Auto-saved';
    indicator.className = 'auto-save saved';
    setTimeout(() => indicator.textContent = '', 2000);
  }, 3000);
});
```

`css .auto-save.saving { color: var(--amber) } .auto-save.saved { color: var(--green) }`

### Markdown toolbar

Buttons that wrap selected text with syntax. Shared handler:

```javascript
function mdWrap(before, after) {
  const start = editor.selectionStart, end = editor.selectionEnd;
  const sel = editor.value.slice(start, end) || 'text';
  editor.value = editor.value.slice(0,start) + before + sel + after + editor.value.slice(end);
  editor.focus(); updatePreview();
}
```

Buttons: **B** (`**` `**`), *I* (`*` `*`), H (`## ` ``), 🔗 (`[` `](url)`), {} (``` `` ``` `` ```), ⋮ (`- ` ``).

### Search history

Last 5 queries in localStorage. Click search input → show dropdown of recent queries:

```javascript
let searchHistory = JSON.parse(localStorage.getItem('doc-search-hist') || '[]');
function addSearchHistory(q) {
  if (!q || q.length < 2) return;
  searchHistory = searchHistory.filter(s => s !== q);
  searchHistory.unshift(q);
  if (searchHistory.length > 5) searchHistory.pop();
  localStorage.setItem('doc-search-hist', JSON.stringify(searchHistory));
}
```

### Bulk delete

Checkbox on hover per doc item. `selectedCb` Set tracks. Footer shows "Delete selected N" when >0:

```javascript
const selectedCb = new Set();
function toggleCb(id) {
  if (selectedCb.has(id)) selectedCb.delete(id); else selectedCb.add(id);
  bulkDelBtn.classList.toggle('show', selectedCb.size > 0);
}
async function bulkDelete() {
  if (!selectedCb.size || !confirm('Delete ' + selectedCb.size + ' docs?')) return;
  for (const id of selectedCb) { try { await fetch(API + '/' + id, { method: 'DELETE' }); } catch(_) {} }
  selectedCb.clear(); bulkDelBtn.classList.remove('show'); loadList();
}
```

CSS: `.d-cb { opacity:0; transition:.15s; } .doc-item:hover .d-cb { opacity:1; } .d-cb.show { opacity:1; }`

### Sidebar collapse

☰ button in top bar → toggles `.collapsed` class:

```css
.sidebar.collapsed { width:0; overflow:hidden; border-right:none; margin-left:-1px; transition:width .2s,margin .2s; }
```

```javascript
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('collapsed'); }
```

### Clear cache button

Footer link, clears all Cache API storage then reloads:

```javascript
function clearCacheAndSW() {
  if ('caches' in window) {
    caches.keys().then(ks => Promise.all(ks.map(k => caches.delete(k)))).then(() => toast('🧹 Cache cleared', 'success'));
  }
  setTimeout(() => location.reload(), 500);
}
```

No SW code needed — just cache deletion. Place in: sidebar footer (documents), navbar (dashboard), page footer (home).

### Mobile responsive

Break at 720px: sidebar full-width, reader as overlay (position:fixed), editor body stacked (textarea top, preview bottom). Article fills full width.

```css
@media(max-width:720px) {
  .sidebar{ width:100%; }
  .reader{ position:fixed; inset:52px 0 0; display:none; flex-direction:column; min-height:0; }
  .reader.show{ display:flex; }
  .sidebar.hide{ display:none; }
  .editor-body{ flex-direction:column; }
  .editor-body textarea{ width:100%; height:50%; }
  .editor-body .preview-pane{ width:100%; height:50%; background:var(--bg); padding:1.2rem 1rem; }
  .reader-content{ padding:1.2rem 1rem; }
}
```

## CSS framework choice

Use **Bulma** (component-rich, CDN, responsive). Avoid Pico CSS (minimal/classless — users often find it too plain).

Dark mode: Bulma v1 uses CSS custom properties. Override in `[data-theme="dark"]`:
```css
[data-theme="dark"] {
  --bulma-scheme-main: #0a0e17;
  --bulma-text: #f1f5f9;
  --bulma-link: #818cf8;
  --bulma-card-background-color: #111827;
  /* etc */
}
```

Theme toggle: save per-page key in localStorage, fallback to `prefers-color-scheme`.

### Async PDF conversion (spawn, non-blocking)

Convert `execSync` → `spawn` so LibreOffice doesn't block the Node.js server:

```javascript
function convertDocxToPdf(docxPath, pdfPath, cb) {
  if(!isSafePath(DOCS_DIR, docxPath) || !isSafePath(DOCS_DIR, pdfPath)) return cb(new Error('invalid-path'));
  if(fs.existsSync(pdfPath) && fs.statSync(docxPath).mtime <= fs.statSync(pdfPath).mtime) return cb(null, pdfPath);

  const child = spawn(SOFFICE, ['--headless', '--convert-to', 'pdf', '--outdir', DOCS_DIR, docxPath], {
    windowsHide: true, timeout: 30000,
  });
  let err = '';
  child.stderr.on('data', d => err += d);
  child.on('close', code => {
    if(code !== 0) return cb(new Error(`soffice exited ${code}: ${err.slice(0,200)}`));
    cb(null, pdfPath);
  });
  child.on('error', cb);
}
```

Route handler:
```javascript
convertDocxToPdf(docxPath, pdfPath, (err) => {
  if(err) return json(res, { error: 'conversion-failed', detail: err.message }, 500);
  const buf = fs.readFileSync(pdfPath);
  res.writeHead(200, { 'Content-Type': 'application/pdf', 'Content-Length': buf.length, 'Cache-Control': 'public, max-age=3600' });
  res.end(buf);
});
```

### gzip compression for JSON

```javascript
const zlib = require('zlib');
function json(res, data, code = 200) {
  const body = JSON.stringify(data);
  // check accept-encoding from req (stored as res._req)
  if(res._req?.headers?.['accept-encoding']?.includes('gzip') && body.length > 1024) {
    zlib.gzip(body, (_, buf) => { res.writeHead(code, { 'Content-Type': 'application/json', 'Content-Encoding': 'gzip' }); res.end(buf); });
  } else {
    res.writeHead(code, { 'Content-Type': 'application/json' });
    res.end(body);
  }
}
// In createServer handler: res._req = req;
```

### isSafePath helper

```javascript
function isSafePath(base, target) {
  return path.resolve(base, target).startsWith(base);
}
```

Replace all `if(!filePath.startsWith(DOCS_DIR))` checks.

### PORT from env

```javascript
const PORT = parseInt(process.env.PORT || '3000', 10);
```

### Optimize require('http')

Load `const http = require('http')` once at top. Remove inline `require('http')` in route handlers.

## Pitfalls

### General
- **marked async**: Use `marked@5` (CDN: `marked@5/marked.min.js`). Newer versions may return Promise.
- **path traversal**: Always validate filePath starts with DOCS_DIR. Check BOTH .md and .docx paths.
- **MSYS Unicode filenames**: python-docx save with Unicode filename (e.g. `tiểu-luận-mẫu.docx`) fails on MSYS/git-bash. Use ASCII-only or full Windows path with drive letter.
- **hash clear**: `history.replaceState(null, '', ' ')` with a space, not empty string.
- **marked links**: Auto-set `target="_blank"` on all `<a>` after rendering.
- **frontmatter parsing**: Regex `/^---\n[\s\S]*?\n---\n([\s\S]*)$/` — multiline YAML. If no frontmatter, return raw content.
- **Bulma modal**: Use `.modal.is-active` class. Modal-card structure: `.modal-background` + `.modal-card` (head + body + foot).
- **Edit only for .md**: Hide edit button when ext !== 'md'. docx files are view-only + download.
- **Article colors**: Do NOT hardcode article colors (white bg, black text, specific font-size). Let the theme's CSS variables (`var(--bg)`, `var(--text)`, `var(--text-strong)`, `var(--accent)`) control appearance. Users often prefer native theme inheritance over a fixed "paper on desk" Google Docs look.

### LibreOffice PDF
- **First conversion slow (~15s)** on first server run (LibreOffice runtime init). Need socket timeout > 20s on client. Serve a loading indicator while conversion runs.
- **Lock file conflicts**: LibreOffice uses a lock file — two simultaneous conversions fail. For low-traffic viewers, sequential calls via the single convert endpoint are fine. For concurrent traffic, use a queue or a persistent soffice listener (`soffice --accept=socket,...`).
- **Temp files**: soffice may leave `.~lock.*` files in the docs dir if killed mid-conversion. Periodic cleanup recommended.
- **SOFFICE path**: On Windows, `soffice.exe` is in `C:\Program Files\LibreOffice\program\`. The MSYS `/c/...` path works in bash but Node.js `execSync` needs the Windows path with backslashes escaped or forward slashes.
- **Font fallback**: Only fonts installed on the system are available. Custom fonts embedded in the docx but not on the system may be substituted. LibreOffice bundles common Windows fonts (Calibri, Cambria, Times New Roman, Arial) on a fresh install.
- **PDF caching**: Cache alongside the docx file. Check mtime before re-converting. Add `Cache-Control: public, max-age=3600` header for browser caching.
- **Windows path escaping**: In `execSync`, the `"${SOFFICE}"` must be quoted because path contains spaces. `--outdir` and input file paths also need quotes.

### docx-preview (fallback)
- **docx-preview large files**: Base64 decode 877KB+ docx in main thread blocks UI briefly. The `renderAsync()` is async but base64 decoding (`atob` + `Uint8Array`) is sync. For very large files (>5MB base64), consider showing a spinner before the sync decode.
- **docx-preview vs mammoth**: docx-preview preserves font size, color, alignment, tables with merged cells, headers/footers, footnotes, page breaks — mammoth strips most of these. Switch to docx-preview when formatting fidelity matters. mammoth is only suitable for simple text-heavy documents.
- **docx-preview CDN order**: JSZip must load BEFORE docx-preview. Reverse order = JSZip undefined error.
- **inWrapper: false**: When using client-side rendering (no PDF), use `inWrapper: false` to avoid the page-width wrapper that causes overflow. With `inWrapper: true` and `ignoreWidth: false`, the content is locked to A4 page width (~794px) and overflows on smaller screens.
- **docx-preview page layout limitation**: Even with optimal options, docx-preview cannot faithfully render complex page layouts (page numbers, columns, exact margins, floating images). This is why server-side PDF is the preferred approach.

### Layout & scrolling
- **Flexbox scroll needs `min-height: 0`**: A flex child with `overflow-y: auto` inside a flex column **requires `min-height: 0`** to actually shrink and scroll. Without it, the child assumes its content's intrinsic height and never scrolls.
  ```css
  .reader-content { flex: 1 1 0; min-height: 0; overflow-y: auto; }
  ```

- **Grid over nested flex**: When the height chain `body → .layout → .reader → #doc-view → .reader-content` doesn't scroll despite `min-height: 0` everywhere, use **CSS grid** for the top-level layout. Grid gives definite height to cells, breaking flexbox's ambiguous "height is a suggestion" behavior:
  ```css
  .layout{ display:grid; grid-template-columns:260px 1fr; height:calc(100vh - 52px); }
  .sidebar, .reader{ height:100%; }
  ```
  Grid children can still use flex internally (`.reader` = flex column for header + content).

- **`flex: 1 1 0` (flex-basis: 0)**: When `flex: 1` alone doesn't produce scroll in Chrome nested flexbox, use `flex: 1 1 0`. Explicit `flex-basis: 0` sets initial size to 0 before growing, which helps overflow calculations.

- **Mobile `.reader` fixed positioning**: On mobile, `inset: 52px 0 0` gives a definite height to `.reader` (bypassing grid/flex chain). Must include `min-height: 0` in the mobile rule for internal flex to scroll.

- **`calc(100vh - N)` with `flex: 1`**: Setting both on the same element creates a dual-constraint. The explicit height sets `min-height: auto` baseline. Prefer grid when exact viewport height is needed.

### Print mode (browser print dialog)

🖨 button → `window.print()` directly. Browser handles print preview UI.

```javascript
function onPrint() { window.print(); }
```

`@media print` CSS — show only article content, hide sidebar/header/buttons:

```css
@media print {
  body>*:not(.layout){ display:none!important; }
  .layout{ display:block!important; overflow:visible!important; }
  .sidebar,.reader-header,.theme-btn{ display:none!important; }
  .reader{ display:block!important; overflow:visible!important; }
  .reader-content{ overflow:visible!important; padding:0!important; background:none!important; }
}
```
