# OfficeCLI batch mode — session-specific reference

## Full Python generator recipe

Working script used to generate a 246-command batch JSON for a ~10-page essay Word document (`tieu_luan_AI_mam_non.docx`, 15KB officecli vs 47KB python-docx). Covers: styles, document defaults, title page, TOC, tables, headings, body paragraphs, bullet lists, page breaks.

```python
import json

def cmd(op, path, elem_type=None, **props):
    c = {"command": op}
    if op == "add":
        c["parent"] = path
    else:
        c["path"] = path
    if elem_type:
        c["type"] = elem_type
    # Python keyword/name workarounds
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

P = []  # pipeline

# === Styles ===
P.append(addp("/styles", elem_type="style", name="Heading1", _id="Heading1",
    bold=True, size=28, color="1F3864", font="Times New Roman", spaceBefore=24, spaceAfter=12))
P.append(addp("/styles", elem_type="style", name="Heading2", _id="Heading2",
    basedOn="Heading1", bold=True, size=22, color="2E75B6", font="Times New Roman", spaceBefore=18, spaceAfter=8))
P.append(addp("/styles", elem_type="style", name="Heading3", _id="Heading3",
    basedOn="Heading1", bold=True, italic=True, size=18, color="404040", font="Times New Roman", spaceBefore=12, spaceAfter=6))
P.append(addp("/styles", elem_type="style", name="Normal", _id="Normal",
    font="Times New Roman", size=13))  # ⚠️ DON'T set lineSpacing — causes massive line-height in rendered output
P.append(addp("/styles", elem_type="style", name="ListParagraph", _id="ListParagraph",
    basedOn="Normal", leftIndent=720))

# === Document defaults ===
P.append(setp("/", docDefaults_font="Times New Roman", docDefaults_fontSize="13pt",
    pageWidth=12240, pageHeight=15840, marginTop=1420, marginBottom=1420,
    marginLeft=1701, marginRight=1134))

# === Title page ===
for _ in range(6): P.append(addp(text=""))
P.append(addp(text="BỘ GIÁO DỤC VÀ ĐÀO TẠO", bold=True, size=13, alignment="center"))
P.append(addp(text="TRƯỜNG ĐẠI HỌC SƯ PHẠM KỸ THUẬT", bold=True, size=13, alignment="center"))
for _ in range(4): P.append(addp(text=""))
P.append(addp(text="TIỂU LUẬN", bold=True, size=22, color="1F3864", alignment="center"))
P.append(addp(text=""))
P.append(addp(text="ỨNG DỤNG TRÍ TUỆ NHÂN TẠO...", bold=True, size=26, color="1F3864", alignment="center"))
for _ in range(6): P.append(addp(text=""))
P.append(addp(text="Giảng viên hướng dẫn: PGS.TS. Nguyễn Văn A", size=13, alignment="center"))
P.append(addp(text="Sinh viên thực hiện: Nguyễn Thị B", size=13, alignment="center"))
P.append(addp(text="Mã số sinh viên: 12345678", size=13, alignment="center"))
P.append(addp(text="Lớp: Mầm non K46", size=13, alignment="center"))
for _ in range(2): P.append(addp(text=""))
P.append(addp(text="TP. Hồ Chí Minh, 2025", size=13, alignment="center"))
P.append(addp(text="", _break="page"))  # page break

# === TOC (Table of Contents) ===
# TOC uses `elem_type="toc"` to create a proper Word TOC field.
# It will show placeholder content until updated in Word (Ctrl+A → F9).
P.append(addp(text="MỤC LỤC", style="Heading1", alignment="center"))
P.append(addp(elem_type="toc", levels="1-3", hyperlinks=True, pagenumbers=True))
P.append(addp(text="", _break="page"))

# === Paragraph helpers ===
def add_heading1(text): P.append(addp(text=text, style="Heading1"))
def add_heading2(text): P.append(addp(text=text, style="Heading2"))
def add_heading3(text): P.append(addp(text=text, style="Heading3"))
def add_para(text): P.append(addp(text=text, style="Normal"))
def add_bullet(text): P.append(addp(text=text, style="ListParagraph"))

# === Tables ===
# The add for a table uses elem_type="table" with rows/cols
P.append(addp(elem_type="table", rows=8, cols=2))
# Then set commands target each cell
P.append(setp("/body/tbl[1]/tr[1]/tc[1]", text="Header", bold=True))
P.append(setp("/body/tbl[1]/tr[2]/tc[1]", text="Cell value"))

# === Write batch JSON ===
with open("batch_commands.json", "w", encoding="utf-8") as f:
    json.dump(P, f, ensure_ascii=False, indent=2)
print(f"Batch commands: {len(P)}")
```

## Incremental development notes

1. First attempt used bash script with 346 lines of `officecli add` commands → timed out after 120s (exit 124), file 5.1KB incomplete
2. Switched to batch mode via Python generator → more reliable, 246 commands in 2-3s
3. Key errors encountered with fixes:
   - Python `_type` kwarg → `elem_type` parameter (type is top-level JSON field)
   - `type=` in addp kwargs → delete, use `elem_type=` instead
   - `id=` kwarg → fine in Python but renamed to `_id` for consistency
   - `style` field error → put inside `props` (not top-level), vs `type` which IS top-level
   - `alignment` field error → put inside `props`, not top-level
   - `listStyle` field error → put inside `props`, not top-level

## Batch mode vs CLI mode

| Operation | CLI (sequential) | Batch (single pass) |
|-----------|-----------------|---------------------|
| Add paragraph | `add file.docx / --type paragraph --prop text=...` | `{"command":"add","parent":"/","type":"paragraph","props":{"text":"..."}}` |
| Add table | `add file.docx / --type table --prop rows=5 --prop cols=3` | `{"command":"add","parent":"/","type":"table","props":{"rows":5,"cols":3}}` |
| Add style | `add file.docx /styles --type style --prop name=H1 --prop id=H1` | `{"command":"add","parent":"/styles","type":"style","props":{"name":"H1","id":"H1"}}` |
| Set property | `set file.docx /path --prop key=val` | `{"command":"set","path":"/path","props":{"key":"val"}}` |
