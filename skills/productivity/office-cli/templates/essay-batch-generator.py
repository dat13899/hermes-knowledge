#!/usr/bin/env python3
"""
OfficeCLI batch JSON generator for academic essays (Word .docx).
Generates styles, title page, TOC, tables, headings, paragraphs, bullets, page breaks.

Usage:
  python essay-batch-generator.py
  officecli create output.docx
  officecli batch output.docx --input batch_commands.json
  officecli close output.docx

Pitfalls:
  - DON'T set lineSpacing on Normal style (breaks layout)
  - style, alignment, listStyle go in "props", NOT top-level
  - Use _break for page breaks (Python keyword workaround)
  - Use _id for style identifiers
  - Use elem_type for the "type" field (top-level JSON)
  - After opening in Word, press Ctrl+A → F9 to update the TOC
"""

import json

F = r"C:\path\to\output.docx"

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

P = []  # pipeline

# === Styles ===
P.append(addp("/styles", elem_type="style", name="Heading1", _id="Heading1",
    bold=True, size=28, color="1F3864", font="Times New Roman", spaceBefore=24, spaceAfter=12))
P.append(addp("/styles", elem_type="style", name="Heading2", _id="Heading2",
    basedOn="Heading1", bold=True, size=22, color="2E75B6", font="Times New Roman", spaceBefore=18, spaceAfter=8))
P.append(addp("/styles", elem_type="style", name="Heading3", _id="Heading3",
    basedOn="Heading1", bold=True, italic=True, size=18, color="404040", font="Times New Roman", spaceBefore=12, spaceAfter=6))
P.append(addp("/styles", elem_type="style", name="Normal", _id="Normal",
    font="Times New Roman", size=13))  # ⚠️ NO lineSpacing!
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
P.append(addp(text="TITLE TEXT HERE", bold=True, size=26, color="1F3864", alignment="center"))
for _ in range(6): P.append(addp(text=""))
P.append(addp(text="Giảng viên hướng dẫn: [NAME]", size=13, alignment="center"))
P.append(addp(text="Sinh viên thực hiện: [NAME]", size=13, alignment="center"))
P.append(addp(text="Mã số sinh viên: [ID]", size=13, alignment="center"))
P.append(addp(text="Lớp: [CLASS]", size=13, alignment="center"))
for _ in range(2): P.append(addp(text=""))
P.append(addp(text="TP. Hồ Chí Minh, 2025", size=13, alignment="center"))
P.append(addp(text="", _break="page"))

# === TOC ===
P.append(addp(text="MỤC LỤC", style="Heading1", alignment="center"))
P.append(addp(elem_type="toc", levels="1-3", hyperlinks=True, pagenumbers=True))
P.append(addp(text="", _break="page"))

# === Paragraph helpers ===
def add_heading1(text): P.append(addp(text=text, style="Heading1"))
def add_heading2(text): P.append(addp(text=text, style="Heading2"))
def add_heading3(text): P.append(addp(text=text, style="Heading3"))
def add_para(text): P.append(addp(text=text, style="Normal"))
def add_bullet(text): P.append(addp(text=text, style="ListParagraph", listStyle="bullet"))

# === Write batch JSON ===
with open("batch_commands.json", "w", encoding="utf-8") as f:
    json.dump(P, f, ensure_ascii=False, indent=2)
print(f"Batch commands: {len(P)}")
