---
name: docx-workflow
description: Tạo, sửa, xoá nội dung file .docx bằng python-docx, lưu vào ~/documents/, server tự refresh, gửi link btdat.io.vn/documents#<tên> cho user verify.
category: document
---

# Xử lý file DOCX trên server

## Cài đặt
```bash
uv pip install python-docx
```

## Workflow

1. **Tạo file mới** — viết script Python dùng `docx.Document`, lưu vào `C:\Users\datel\documents\<tên>.docx`
2. **Sửa file có sẵn** — mở file, tìm paragraph bằng index hoặc text, sửa `run.text`, lưu lại
3. **Thêm/xoá dòng** — dùng `p._element.addnext(new_p._element)` để chèn sau, `p._element.getparent().remove(p._element)` để xoá
4. **Gửi link** — `https://btdat.io.vn/documents#<tên-file-không-có-đuôi>`

## Các thao tác thường gặp

### Đọc nội dung
```python
from docx import Document
doc = Document('C:/Users/datel/documents/<file>.docx')
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t:
        print(i, '|', t[:200])
```

### Sửa text trong paragraph (theo index)
```python
p = doc.paragraphs[9]
for run in p.runs:
    run.text = run.text.replace('cũ', 'mới')
```

### Thêm dòng mới sau paragraph
```python
new_p = doc.add_paragraph()
run = new_p.add_run('Nội dung mới')
run.font.name = 'Times New Roman'
run.font.size = Pt(13)
p._element.addnext(new_p._element)
```

### Xoá dòng
```python
for p in doc.paragraphs:
    if 'text cần xoá' in p.text:
        p._element.getparent().remove(p._element)
        break
```

## Lưu ý
- Server DOCS_DIR: `C:\Users\datel\documents\`
- Server tự refresh danh sách mỗi GET `/api/documents` — không cần restart
- File `.docx` xem PDF qua LibreOffice (`/api/documents/:id/pdf`)
- File `.md` render markdown → HTML trực tiếp
