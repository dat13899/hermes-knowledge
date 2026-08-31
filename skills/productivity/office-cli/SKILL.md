---
name: office-cli
description: "Create, read, edit Word (.docx), Excel (.xlsx), PowerPoint (.pptx) via OfficeCLI — single binary, no Office install, JSON output, render engine built-in."
version: 1.0.0
author: Cu em (Hermes Agent)
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [office, docx, xlsx, pptx, officecli, cli, automation]
    related_skills: [docx-editing, powerpoint]
---

# OfficeCLI — Office Document Automation via CLI

OfficeCLI (`officecli`) is a **single self-contained binary** that reads, edits, and creates Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) files. No Office installation, no Python libraries, no runtime dependencies. Ships with a built-in HTML rendering engine so the agent can *see* rendered documents.

## When to use

Use OfficeCLI instead of python-docx / python-pptx / openpyxl when:

- Creating, reading, or modifying Word / Excel / PowerPoint files
- Need JSON structured output from document content
- Need HTML or screenshot rendering of documents
- Need resident mode (keep file in memory for fast multi-step edits)
- Need template merge (`{{key}}` → JSON data)
- Need batch operations (multiple edits in one command)
- Need Excel formula evaluation (350+ built-in functions)
- Working across formats (Word + Excel + PPT in one tool)

**Fall back to python-docx / python-pptx** only when OfficeCLI lacks a specific feature (rare, check wiki first).

## Installation

```bash
# npm (all platforms, fetches native binary)
npm install -g @officecli/officecli

# Windows PowerShell
irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex

# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash

# Homebrew (macOS / Linux)
brew install officecli

# Scoop (Windows)
scoop install officecli
```

Verify: `officecli --version`

## Basic commands

| Command | Description |
|---------|-------------|
| `create file.docx` | Create blank document |
| `add file.docx / --type paragraph --prop text="..."` | Add element |
| `set file.docx '/path' --prop key=value` | Modify element |
| `get file.docx '/path' --json` | Read element as JSON |
| `query file.docx "selector" --json` | Search elements |
| `remove file.docx '/path'` | Delete element |
| `view file.docx outline` | View structure |
| `view file.docx html -o out.html` | Render as HTML (no browser needed) |
| `view file.docx screenshot -o out.png` | Render as PNG (requires Playwright) |
| `watch file.docx` | Live preview browser (auto-refresh on edit) |
| `close file.docx` | Flush + release resident session |
| `save file.docx` | Flush to disk, keep resident warm |
| `merge template.docx out.docx '{"key":"val"}'` | Template merge |
| `batch file.docx --input updates.json` | Apply multiple operations |

**JSON output**: Append `--json` to any command for structured output.

## Key features

### Resident mode

Opened files stay in memory for fast multi-step edits. Flush to disk with `save` or `close`. Other readers (python-docx, Word) must wait for `save`/`close` to see latest edits.

```bash
officecli open report.docx
officecli set report.docx '/body/p[1]/r[1]' --prop text="Hello"
officecli save report.docx     # flush to disk
officecli close report.docx    # flush + release
```

### Render engine

`view html` produces a standalone HTML file with all assets inlined. No browser needed at generation time.

`view screenshot` produces per-page PNG images. **Requires a headless browser** (`pip install playwright && playwright install chromium`).

`watch` starts a local HTTP server + auto-refreshing browser preview.

### Excel formula evaluation

OfficeCLI evaluates 350+ Excel functions on write. Write a formula, `get` the cell, the computed value is already there. No round-trip through Office.

```bash
officecli set sheet.xlsx '/Sheet1/B5' --prop formula='=SUM(B2:B4)'
officecli get sheet.xlsx '/Sheet1/B5' --json
# → {"tag": "cell", "path": "/Sheet1/B5", "attributes": {"formula": "=SUM(B2:B4)", "value": "4200000"}}
```

## Windows (MSYS/git-bash) pitfalls

### Path style

**Use Windows paths** (`C:\Users\...`), NOT MSYS paths (`/c/Users/...`). OfficeCLI is a native Windows binary and doesn't understand MSYS path translation. Passing `/c/Users/...` produces doubled paths like `C:\c\Users\...`.

```bash
# WRONG — produces C:\c\Users\... errors
officecli view file.docx html -o /c/Users/me/out.html

# RIGHT
officecli view file.docx html -o "C:\Users\me\out.html"
```

### Dollar signs in bash

OfficeCLI text values containing `$` (e.g. `$2.1M`) must use **single quotes** in bash to prevent shell variable expansion.

```bash
# WRONG — bash expands $2.1M
officecli set file.xlsx '/Sheet1/B2' --prop text="$2.1M"

# RIGHT
officecli set file.xlsx '/Sheet1/B2' --prop text='$2.1M'
```

### Styles in blank documents

`officecli create` produces a minimal docx without built-in Heading styles. Adding elements with `--prop style=Heading1` produces a warning and the style won't render correctly in Word.

**Fix**: Use a template with `officecli create --template template.docx`, or define styles explicitly after create, or accept that blank-create is for structural testing only.

python-docx uses a template with built-in styles (Title, Heading1-9, Normal, etc.) — one reason python-docx output files are larger (~37KB vs ~6KB for OfficeCLI).

### Screenshot requires Playwright

`view screenshot` needs a headless Chromium. Install:
```bash
pip install playwright
playwright install chromium
# Or: playwright install --with-deps chromium  (Linux)
```

Without it, `view html` still works for visual inspection.

## Batch mode (JSON pipeline)

`officecli batch file.docx --input commands.json` applies many operations in one pass. The JSON is an array of command objects.

### JSON command format

```json
[
  {"command": "add", "parent": "/styles", "type": "style", "props": {"name": "Heading1", "size": 28, "bold": true}},
  {"command": "add", "parent": "/", "type": "paragraph", "props": {"text": "Hello", "style": "Heading1", "alignment": "center"}},
  {"command": "add", "parent": "/", "type": "table", "props": {"rows": 3, "cols": 2}},
  {"command": "set", "path": "/body/tbl[1]/tr[1]/tc[1]", "props": {"text": "Header", "bold": true}},
  {"command": "set", "path": "/", "props": {"pageWidth": 12240, "marginTop": 1420}}
]
```

**Key rules:**

| CLI option | Batch JSON field | Notes |
|------------|-----------------|-------|
| `--type paragraph` | `"type": "paragraph"` (top-level) | Required for `add` — tells *what* to add |
| `--style Heading1` | `"props": {"style": "Heading1"}` | Goes **inside** `props`, NOT top-level |
| `--prop text=...` | `"props": {"text": "..."}` | All regular props go here |
| `path` (CLI arg) | `add` → `"parent"`, `set` → `"path"` | Different key per command |
| `--prop break=page` | `"props": {"break": "page"}` | Page break. In Python, use `_break` to avoid keyword clash |

### Python generator pattern

Recommended approach: write a Python script that builds the batch JSON array, then feed to `officecli batch`.

```python
def cmd(op, path, elem_type=None, **props):
    c = {"command": op}
    if op == "add":
        c["parent"] = path
    else:
        c["path"] = path
    if elem_type:
        c["type"] = elem_type
    rename = {"_break": "break", "_id": "id",
               "docDefaults_font": "docDefaults.font", "docDefaults_fontSize": "docDefaults.fontSize"}
    mapped = {}
    for k, v in props.items():
        if v is not None:
            mapped[rename.get(k, k)] = v
    if mapped:
        c["props"] = mapped
    return c

def addp(path="/", elem_type="paragraph", **props):
    return cmd("add", path, elem_type=elem_type, **props)

def setp(path, **props):
    return cmd("set", path, **props)

P = []
P.append(addp("/styles", elem_type="style", name="Heading1", _id="Heading1", bold=True, size=28))
P.append(addp(elem_type="table", rows=5, cols=3))
P.append(setp("/body/tbl[1]/tr[1]/tc[1]", text="Header", bold=True))
P.append(addp(text="", _break="page"))

import json
with open("batch_commands.json", "w", encoding="utf-8") as f:
    json.dump(P, f, ensure_ascii=False, indent=2)
print(f"Batch commands: {len(P)}")
```

Then:
```bash
officecli create output.docx
officecli batch output.docx --input batch_commands.json
officecli close output.docx
```

### Python reserved-word workarounds

Python keyword args can't use `break`, `type`, or `id` directly. Use underscore-prefixed names + the `rename` dict:

| Python kwarg | Maps to | Usage |
|-------------|---------|-------|
| `_break="page"` | `"break": "page"` | Page break prop |
| `elem_type="table"` | `"type": "table"` (top-level) | Element type for `add` |
| `_id="Heading1"` | `"id": "Heading1"` | Style identifier |

### Common element patterns

| Element | `elem_type` | Key props |
|---------|------------|-----------|
| Paragraph | `"paragraph"` | `text`, `style`, `alignment`, `bold`, `size`, `color`, `font` |
| Heading | `"paragraph"` | `text`, `style: "Heading1"` (always via helper) |
| Table | `"table"` | `rows`, `cols` |
| Style def | `"style"` | `name`, `_id`, `bold`, `size`, `color`, `font`, `basedOn`, `spaceBefore`, `spaceAfter` |
| Page break | `"paragraph"` | `text: ""`, `_break: "page"` |
| Bullet | `"paragraph"` | `text`, `style: "ListParagraph"` |

### Batch limitations

- **`lineSpacing` on Normal style breaks layout** — Setting `lineSpacing` with `lineRule="auto"` causes OfficeCLI to compute massive line-height values (413pt+) in the rendered HTML. The Normal style should omit `lineSpacing` entirely — rely on CSS defaults or set it inline on specific paragraphs instead.
- **TOC via batch** — Use `elem_type="toc"` with props `levels`, `hyperlinks`, `pagenumbers`. Creates a Word TOC field that renders placeholder content until user updates fields in Word (Ctrl+A → F9). Cannot pre-render TOC entries; Word rebuilds them from heading styles on update.
- `docDefaults.font` / `docDefaults.fontSize` produce warnings on `set` but still work in rendered output
- Styles defined in batch are minimal — no full theme; enough for formatted essay
- All commands share one resident session — no reopen between commands needed
- 200+ commands complete in ~2-3 seconds
- **`lineSpacing` on Normal style breaks layout** — Setting `lineSpacing` with `lineRule="auto"` causes OfficeCLI to compute massive line-height values (413pt+) in the rendered HTML. The Normal style should omit `lineSpacing` entirely — rely on CSS defaults or set it inline on specific paragraphs instead.
- **TOC via batch** — Use `elem_type="toc"` with props `levels`, `hyperlinks`, `pagenumbers`. Creates a Word TOC field that renders placeholder content until user updates fields in Word (Ctrl+A → F9). Cannot pre-render TOC entries; Word rebuilds them from heading styles on update.

## Recognized limitations

| Aspect | OfficeCLI | python-docx + python-pptx + openpyxl |
|--------|-----------|--------------------------------------|
| Install | npm i -g @officecli/officecli | pip install 3 separate libs |
| Dependencies | Zero (self-contained binary) | python-docx, python-pptx, lxml, Pillow, etc. |
| File size (simple docx) | ~6KB | ~37KB (includes theme + defaults) |
| Excel support | Full (cells, formulas, pivot, charts) | separate openpyxl |
| JSON output | Built-in (`--json` on every command) | Manual stdout parsing |
| Rendering | Built-in HTML/PNG engine | LibreOffice + pdftoppm pipeline |
| Resident mode | Yes (in-memory, near-zero latency) | No (load/save every time) |
| Template merge | Yes (`merge` command) | No |
| Batch operations | Yes (`batch` command) | No |
| MCP server | Yes (Claude Code, Cursor, VS Code) | No |
| Formula evaluation | 350+ functions auto-eval | Manual Python computation |
| Learning curve | CLI commands | Python API per library |

## Recognized limitations

- **Screenshots**: need Playwright (not bundled)
- **Blank docx styles**: no built-in Heading styles (use template)
- **MSYS path handling**: native Windows binary, use `C:\...` paths
- **Complex SmartArt**: round-trip only (can't fully manipulate)
- **PDF export**: requires format-handler plugin

## Scripts and references

- `references/comparison.md` — detailed test results from python-docx/pptx vs OfficeCLI comparison
- `references/batch-mode.md` — batch mode Python generator recipe, JSON format, key rules, common error fixes
- `templates/essay-batch-generator.py` — full working template for academic essay generation (title page, TOC, styles, tables, headings, bullet lists, page breaks)
