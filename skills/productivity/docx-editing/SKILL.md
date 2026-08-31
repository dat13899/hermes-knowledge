---
name: docx-editing
description: "Create and edit .docx files using python-docx — academic essays, reports, Vietnamese documents with proper formatting (TNR, 1.5 spacing, first-line indent, cover pages, references). Also covers editing existing documents."
version: 1.0.0
author: Cu em (Hermes Agent)
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [docx, python-docx, word, editing, academic, vietnamese]
    related_skills: [ocr-and-documents, nano-pdf, powerpoint, office-cli]
---

# DOCX Editing (python-docx)

Edit `.docx` files programmatically when the `patch` tool cannot handle binary formats. Common use cases: restructuring academic papers, rewriting headings, inserting new sections, updating Vietnamese research documents.

## Setup

```bash
uv pip install python-docx
```

Verify:
```python
import docx; print(docx.__version__)
```

## Editing existing documents: insert content at specific positions

When inserting new paragraphs into an existing document (e.g., filling in blank sections of a research paper draft):

**Basic approach** (paragraphs have runs):
```python
from copy import deepcopy

def insert_after(ref_para, text):
    new_p = deepcopy(ref_para._element)
    for r in new_p.iterfind('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        r.text = ''
    first_t = new_p.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    if first_t is not None:
        first_t.text = text
    body = doc.element.body
    idx = list(body).index(ref_para._element)
    body.insert(idx + 1, new_p)
```

**For empty paragraphs (no `<w:t>` elements)**: `first_t` will be `None` and text won't show. Use lxml to create proper elements:
```python
from lxml import etree
nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
p_elem = etree.SubElement(body, '{%s}p' % nsmap['w'])
r_elem = etree.SubElement(p_elem, '{%s}r' % nsmap['w'])
t_elem = etree.SubElement(r_elem, '{%s}t' % nsmap['w'])
t_elem.text = 'Your text here'
t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
body.insert(target_idx + 1, p_elem)
```

**Finding the last real paragraph** (skip `sectPr` and empty trailing paragraphs):
```python
body = doc.element.body
children = list(body)
last_p = None
for elem in reversed(children):
    if elem.tag.endswith('p'):
        texts = elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        if any(t.text for t in texts):
            last_p = elem
            break
```

**Renaming heading text** while preserving style:
```python
def set_text(para, text):
    for run in para.runs:
        run.text = ''
    if para.runs:
        para.runs[0].text = text
    else:
        para.add_run(text)
```

## Document deployment — gửi link cho user

Khi tạo/sửa file `.docx` hoặc `.md`, có hai cách:

**Cách 1 — Document viewer API** (có PDF preview): lưu vào **`~/documents/<tên>`** — server document viewer (port 3000, Cloudflare Tunnel → `btdat.io.vn`) quét thư mục này mỗi request. Không cần restart server. Gửi link: `https://btdat.io.vn/documents#<tên-không-mở-rộng>`

**Cách 2 — Direct static file** (tải trực tiếp): copy vào **`~/service-dashboard/dist/documents/`**, file được serve tại `https://btdat.io.vn/documents/<tên>`. Phù hợp khi muốn gửi file docx gốc cho người dùng tải về.
- PDF preview tự động qua LibreOffice tại `/api/documents/:id/pdf`
- File gốc ở `C:\\Users\\datel\\documents\\<tên>.docx` hoặc `.md` — ghi nhớ để tìm lại sau
- Danh sách API: `GET /api/documents` quét `~/documents/` mỗi lần gọi
- `soffice --headless --convert-to pdf` dùng **`spawn` async** (ko execSync — block cả server). SOFFICE path: `C:\\Program Files\\LibreOffice\\program\\soffice.exe`
- Trên git-bash/MSYS, đường dẫn Windows: dùng `C:/Users/datel/...` (forward slash) hoặc `/c/Users/datel/...` để tránh lỗi `PackageNotFoundError` với python-docx
- Server DOCS_DIR: `path.join(__dirname, '..', 'documents')` — resolve từ `server.js` (nằm trong `service-dashboard/`, documents ở ngoài 1 cấp)

## Editing from user link — luồng sửa khi user gửi link

User gửi link dạng `https://btdat.io.vn/documents#<tên-file>` kèm yêu cầu sửa. Luồng xử lý:

1. **Parse hash**: `#tên-file` → không có đuôi mở rộng
2. **Xác định loại file**: thử `.md` trước (plain text, edit trực tiếp), nếu không tồn tại thì thử `.docx` (dùng python-docx)
3. **Sửa file gốc** tại `C:\Users\datel\documents\<tên-file>.docx` (hoặc `.md`)
4. **Gửi lại chính link đó** cho user verify: `https://btdat.io.vn/documents#<tên-file>`

File `.md` sửa trực tiếp bằng `patch` tool.
File `.docx` sửa bằng python-docx script.

## Git discipline — commit trước khi sửa code

Khi sửa code trong `~/service-dashboard/` (server.js, public/*.html, assets/*):
1. **Commit trước** khi sửa: `git add -A && git commit -m "state before: ..."` — lưu trạng thái gốc
2. **Sửa code**
3. **Commit lại** + `git push origin master`
4. Luôn có điểm rollback nếu lỗi

Áp dụng cho mọi thay đổi code — không chỉ docx.

## Creating documents from scratch

Use python-docx to create academic essays, reports, and Vietnamese documents. See `references/vietnamese-academic-creation.md` for complete template patterns including cover pages, chapter structure, and reference formatting.

### Quick-start: academic essay skeleton

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Page setup
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)

# Font base
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(13)
style.paragraph_format.line_spacing = 1.5

# Cover page
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('TIỂU LUẬN')
run.font.name = 'Times New Roman'
run.font.size = Pt(16)
run.bold = True

# Body helper
def para(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    p.paragraph_format.first_line_indent = Cm(1.27)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    return p

# Heading helper (black, TNR)
def heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = 'Times New Roman'
        run.font.color.rgb = RGBColor(0, 0, 0)
    return h

# Bullet helper
def bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    return p

para('Nội dung...')
doc.save('output.docx')
```

## Complete workflow (standalone script)

For multi-step edits, **write a standalone Python file** instead of running one-liners:

1. Write script to Desktop or project folder via `write_file`
2. Run via terminal: `python "path/to/script.py"`
3. Verify by re-reading key paragraphs after save

```bash
python -c "
import docx
doc = docx.Document('path/to/output.docx')
for i in [start, end]:
    print(f'{i:3d} | {doc.paragraphs[i].text}')
"
```

Always save **incrementally** (revised → revised2 → revised3...) so CTL+Z isn't your only undo.

## Workflow

### 1. Inspect paragraph structure

```python
import docx
doc = docx.Document("path/to/file.docx")
for i, p in enumerate(doc.paragraphs):
    style = p.style.name if p.style else 'None'
    text = p.text[:120]
    if text.strip():
        print(f'{i:3d} | {style:25s} | {text}')
```

This reveals the paragraph index and style for every non-empty paragraph.

### 2. Rewrite a paragraph heading or content

```python
def set_text(para, text):
    for run in para.runs:
        run.text = ''
    if para.runs:
        para.runs[0].text = text
    else:
        para.add_run(text)

set_text(doc.paragraphs[167], "1.6.1. New heading here")
```

### 3. Insert a new paragraph after an existing one (simple)

For quick insert without deepcopy:

```python
new_p = doc.add_paragraph()
run = new_p.add_run('Nội dung mới')
run.font.name = 'Times New Roman'
run.font.size = Pt(13)
ref_p._element.addnext(new_p._element)
```

`add_paragraph()` creates fresh `w:p`, `addnext()` places after ref's XML element.

### 4. Delete a paragraph (simple)

```python
for p in doc.paragraphs:
    if 'text to match' in p.text:
        p._element.getparent().remove(p._element)
        break
```

### 5. Insert a new paragraph before an existing one

```python
from copy import deepcopy

body = doc.element.body
ref_para = doc.paragraphs[194]  # reference paragraph
ref_elem = ref_para._element

# Clone a paragraph element to preserve style
new_elem = deepcopy(ref_elem)
# Clear and set text
for r in new_elem.iterfind('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
    r.text = ''
first_t = new_elem.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
if first_t is not None:
    first_t.text = "New content here"

# Insert before reference
body.insert(list(body).index(ref_elem), new_elem)
```

### 4. Delete a paragraph

```python
body = doc.element.body
ref_elem = doc.paragraphs[42]._element
body.remove(ref_elem)
```

### 6. Save

```python
doc.save("path/to/output.docx")
```

### 7. Insert multiple paragraphs sequentially after a reference

```python
def insert_after(ref_para, text):
    new_p = deepcopy(ref_para._element)
    for r in new_p.iterfind('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        r.text = ''
    first_t = new_p.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    if first_t is not None:
        first_t.text = text
    body = doc.element.body
    ref_elem = ref_para._element
    idx = list(body).index(ref_elem)
    body.insert(idx + 1, new_p)
    return new_p

def insert_multiple(ref_para, texts):
    """Insert several paragraphs after ref_para. Returns last inserted element."""
    current = ref_para._element
    body = doc.element.body
    for t in texts:
        new_p = deepcopy(current)
        for r in new_p.iterfind('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            r.text = ''
        first_t = new_p.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        if first_t is not None:
            first_t.text = t
        idx = list(body).index(current)
        body.insert(idx + 1, new_p)
        current = new_p
    return current
```

### 8. Handle sectPr as the last body element

The last child of `doc.element.body` is often a `sectPr` (section properties) element, NOT a paragraph. When finding the last paragraph to insert after:

```python
body = doc.element.body
all_children = list(body)
last_elem = None
for elem in reversed(all_children):
    if not elem.tag.endswith('sectPr'):
        last_elem = elem
        break
# Map XMl element back to paragraph
last_para = None
for p in doc.paragraphs:
    if p._element is last_elem:
        last_para = p
        break
if last_para:
    insert_multiple(last_para, new_paragraph_texts)
```

### 9. Add a numbered references section (Danh Mục Tài Liệu Tham Khảo)

Vietnamese academic papers use `[1]`, `[2]`... format with a closing section:

```python
refs = [
    "DANH MỤC TÀI LIỆU THAM KHẢO",
    "[1] Author, A. (Year). Title. Journal, Volume(Issue), Pages.",
    "[2] ...",
]
insert_multiple(last_para, refs)
```

Tip: Remove empty trailing paragraphs before inserting refs by scanning the body backwards for `p` elements with no text.

### 10. Download Google Doc as docx via curl

When the source is a Google Doc URL, download as docx for editing:

```bash
curl -sL -o "path/to/output.docx" "https://docs.google.com/document/d/DOCUMENT_ID/export?format=docx"
```

For text-only preview: `format=txt`. For docx: `format=docx`.

## Script: write-full-chapter.py

A reusable template at `scripts/write-full-chapter.py` automates the full workflow: renumber headings, insert content per section with citations, and append a numbered Danh Mục Tài Liệu Tham Khảo. Edit the content dicts, then run.

## Common academic document patterns

### Vietnamese heading convention

- **Mục lục / Phần**: uppercase, bold (e.g., `PHẦN I. MỞ ĐẦU`)
- **Chương**: `CHƯƠNG 1.` followed by title
- **Sub-headings**: `1.1.`, `1.1.1.`, `1.6.1.` — numbered hierarchical
- **Inline labels in headings**: abbreviations in parentheses (e.g., `(AUTH)`, `(SKE)`, `(VER)`, `(DEC)`)

### Splitting a section into sub-sections

When restructuring `1.6.x` from flat paragraphs to separate numbered sub-sections:

1. Identify the range of heading paragraphs (by index from inspection)
2. Use `set_text()` to change each heading to the new name
3. Move content paragraphs so each sub-section heading directly precedes its body
4. For new sub-sections, clone an existing heading paragraph (preserves style), then insert before the anchor paragraph (e.g., before "Tiểu kết Chương")

### Inserting new sections

To add e.g. `1.6.7` between `1.6.6` and "Tiểu kết Chương 1":

1. Find the "Tiểu kết Chương 1" paragraph index
2. Clone a nearby heading paragraph for the `1.6.7` heading
3. Clone a body paragraph for the content
4. Insert both before "Tiểu kết Chương 1" (insert the heading first, then the content — insertion order matters)

## OfficeCLI — preferred alternative

Consider **OfficeCLI** (`productivity/office-cli` skill) instead of python-docx for new work. Single binary, no Python deps, JSON output, HTML rendering, resident mode, template merge. Also handles Excel + PowerPoint.

**When python-docx is still the right choice:**
- Need built-in Heading styles from a template (OfficeCLI blank docx lacks them)
- Need to manipulate raw OOXML / namespace-level XML
- Working with existing python-docx pipelines

## Pitfalls

- **XML namespace**: When iterating over XML elements, always use the full namespace URI `http://schemas.openxmlformats.org/wordprocessingml/2006/main` — shorthand `w:` prefixes from `qn('w:t')` work only if the namespace is registered.
- **Style preservation**: Cloning an existing paragraph (`deepcopy`) preserves its style (bold, font size, indentation). Creating from scratch does NOT — always clone a semantically similar paragraph.
- **First-run text**: After clearing a paragraph's runs with `for r in para.runs: r.text = ''`, set `para.runs[0].text` if runs exist, otherwise `para.add_run(text)`.
- **Insert order**: When inserting multiple paragraphs, insert the one you want to appear first last — because each `insert()` before a reference pushes previous inserts further back.
- **read_file auto-extraction**: Using `read_file` on a `.docx` extracts its text content for quick inspection. For editing, switch to a python-docx script.
- **No undo**: Changes are applied in-place to the in-memory Document. Work on a copy, not the original.
- **Formatting loss**: `set_text()` replaces only the text of existing runs. Complex formatting (bullet lists, merged cells in tables, images) requires XML-level manipulation beyond this skill's scope.
