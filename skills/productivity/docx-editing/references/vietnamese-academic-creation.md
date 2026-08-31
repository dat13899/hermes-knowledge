# Vietnamese Academic Document Creation (python-docx)

Complete template for creating academic essays from scratch. Used in session 2026-07-23 for "Tác động của AI lên các ngành nghề".

## Document structure

```
┌─ Cover page ─────────────────────────┐
│  BỘ GIÁO DỤC VÀ ĐÀO TẠO             │
│  TRƯỜNG ĐẠI HỌC …………               │
│        -----❧-----                    │
│                                       │
│          TIỂU LUẬN                    │
│                                       │
│  [Title in all caps]                  │
│                                       │
│  Giảng viên hướng dẫn: …………………  │
│  Sinh viên thực hiện: …………………  │
│  Lớp: …………  –  MSSV: ……………  │
│  [City], tháng [month] năm [year]    │
├───────────────────────────────────────┤
│  MỤC LỤC (manual entries)            │
├───────────────────────────────────────┤
│  LỜI MỞ ĐẦU                         │
├───────────────────────────────────────┤
│  CHƯƠNG 1: [TITLE]                   │
│  1.1. [Sub-section]                   │
│  1.2. [Sub-section]                   │
├───────────────────────────────────────┤
│  CHƯƠNG 2: [TITLE]                   │
│  2.1–2.N                              │
├───────────────────────────────────────┤
│  CHƯƠNG 3: [TITLE]                   │
├───────────────────────────────────────┤
│  KẾT LUẬN                            │
├───────────────────────────────────────┤
│  TÀI LIỆU THAM KHẢO                  │
└───────────────────────────────────────┘
```

Page break between every major section.

## Formatting rules

| Element | Value |
|---------|-------|
| Font | Times New Roman |
| Body size | 13pt |
| Line spacing | 1.5 |
| First-line indent | 1.27cm |
| Page margins | T/B 2.5cm, L 3cm, R 2cm |
| Cover title | 16pt bold centered |
| Chapter headings | 15pt bold centered, "CHƯƠNG X: TITLE" |
| Sub-section | 13pt bold, "X.Y. Title" |
| References | 12pt, hanging indent 1.5cm |
| Bullets | TNR 13pt, style='List Bullet' |

## Code patterns by section

### Cover page

```python
# Blank line separator
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('-----❧-----')
run.font.name = 'Times New Roman'

# Main title
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('TIỂU LUẬN')
run.font.name = 'Times New Roman'
run.font.size = Pt(16)
run.bold = True

# Topic
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('TÁC ĐỘNG CỦA TRÍ TUỆ NHÂN TẠO (AI)\nĐỐI VỚI CÁC NGÀNH NGHỀ')
run.font.name = 'Times New Roman'
run.font.size = Pt(15)
run.bold = True

# Meta
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Giảng viên hướng dẫn: ………………………\nSinh viên: ………………………………………\nLớp: …………  –  MSSV: …………………\nHà Nội, tháng 7 năm 2026')
run.font.name = 'Times New Roman'
run.font.size = Pt(13)
```

### Headings (black not blue)

```python
def heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = 'Times New Roman'
        run.font.color.rgb = RGBColor(0, 0, 0)
    return h
```

### Body paragraph with first-line indent

```python
def para(text, bold=False, align=None, size=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    if size: run.font.size = Pt(size)
    if bold: run.bold = True
    if align: p.alignment = align
    p.paragraph_format.first_line_indent = Cm(1.27)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    return p
```

### Bullets

```python
def bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    return p
```

### References (hanging indent)

```python
p = doc.add_paragraph()
run = p.add_run('Author (Year). "Title". Publisher.')
run.font.name = 'Times New Roman'
run.font.size = Pt(12)
p.paragraph_format.left_indent = Cm(1.5)
p.paragraph_format.first_line_indent = Cm(-1.5)
p.paragraph_format.line_spacing = 1.5
p.paragraph_format.space_after = Pt(4)
```

## Typical content sections for AI essay

1. **LỜI MỞ ĐẦU** — context, research question, essay structure
2. **CHƯƠNG 1: TỔNG QUAN VỀ [TOPIC]** — definition, history, key technologies, current status
3. **CHƯƠNG 2: TÁC ĐỘNG ĐẾN CÁC NGÀNH NGHỀ** — 6-8 industries, each with: AI application → employment impact → future trend
4. **CHƯƠNG 3: CƠ HỘI VÀ THÁCH THỨC** — opportunities, challenges, recommendations
5. **KẾT LUẬN** — summary, forward-looking statement
6. **TÀI LIỆU THAM KHẢO** — 8-12 entries, APA-like format

## Pitfalls

- **Don't use `\n`** inside runs. Use separate `add_paragraph()` calls.
- **Heading color**: python-docx headings default to blue. Always set `RGBColor(0,0,0)` on each run.
- **Font name on runs**: Setting `Normal` style font.name does NOT propagate to runs you add. Explicitly set `run.font.name` every time.
- **Blank lines between cover elements**: Use `doc.add_paragraph()` — paragraph spacing alone often won't create enough visual separation on title pages.
- **Page breaks**: Insert as `doc.add_page_break()` between major sections.
- **Unicode filenames**: python-docx handles them fine, but MSYS/git-bash may mangle tilde expansion. Use absolute paths.
- **No embedded fonts**: python-docx does not embed fonts. Receiver needs TNR/Calibri installed.
