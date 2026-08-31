---
name: google-docs-formatting
description: "Rich-text formatting and image insertion in Google Docs via batchUpdate API."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [Google, Docs, Formatting, batchUpdate, API]
---

# Google Docs Formatting

Applies rich-text formatting (font, size, color, bold, alignment) and inline images in Google Docs via the `documents.batchUpdate` API. The `google-workspace` skill's CLI (`google_api.py`) only appends plain text — formatting and images require direct API calls.

## Prerequisites

- Google Workspace skill authenticated (token in `google_token.json`)
- Google Drive API enabled (needed for image upload → Docs insertion)
- `googleapiclient` library installed

## Text Style (updateTextStyleRequest)

Use `updateTextStyle` in a batchUpdate request. CRITICAL: the Google Docs API does **not** accept `fontFamily` directly on `textStyle`.

### Correct format:
```python
requests = [{
    "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 51},
        "textStyle": {
            "weightedFontFamily": {           # NOT "fontFamily" on its own
                "fontFamily": "Times New Roman",
                "weight": 400                 # 400=normal, 700=bold
            },
            "fontSize": {"magnitude": 14, "unit": "PT"},
            "foregroundColor": {
                "color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}
            },
            "bold": False,
        },
        "fields": "weightedFontFamily,fontSize,foregroundColor,bold"
    }
}]
docs_service.documents().batchUpdate(
    documentId=DOC_ID, body={"requests": requests}
).execute()
```

### fields mask
The `fields` parameter is **required**. List every TextStyle field you set, comma-separated, in camelCase. Missing a field name = that style is not applied.

### Heading style
For headings, set `bold=True` and `weight=700` plus a larger fontSize (e.g. 16 PT).

## Paragraph Style (updateParagraphStyleRequest)

```python
requests = [{
    "updateParagraphStyle": {
        "range": {"startIndex": 1, "endIndex": 100},
        "paragraphStyle": {
            "lineSpacing": 150,              # 100=single, 150=1.5x
            "spaceAbove": {"magnitude": 6, "unit": "PT"},
            "spaceBelow": {"magnitude": 12, "unit": "PT"},
            "alignment": "JUSTIFIED",         # START, CENTER, END, JUSTIFIED
        },
        "fields": "lineSpacing,spaceAbove,spaceBelow,alignment"
    }
}]
```

## Image Insertion (insertInlineImageRequest)

Three-step workflow to add images to a Doc:

### Step 1 — Upload image to Drive + make public
```python
from googleapiclient.http import MediaIoBaseUpload
import io

# Download or generate image bytes
# image_data = ...

media = MediaIoBaseUpload(io.BytesIO(image_data), "image/jpeg", resumable=True)
file = drive_service.files().create(
    body={"name": "photo.jpg", "mimeType": "image/jpeg"},
    media_body=media, fields="id"
).execute()
file_id = file["id"]

# Required: make publicly viewable so Docs API can access it
drive_service.permissions().create(
    fileId=file_id, body={"type": "anyone", "role": "reader"}
).execute()
```

### Step 2 — Use Google-hosted URI
```python
uri = f"https://lh3.googleusercontent.com/d/{file_id}"
```

### Step 3 — Insert at the correct index
```python
requests = [{
    "insertInlineImage": {
        "location": {"index": INSERT_INDEX},
        "uri": uri,
        "objectSize": {
            "height": {"magnitude": 180, "unit": "PT"},
            "width": {"magnitude": 324, "unit": "PT"},
        }
    }
}]
docs_service.documents().batchUpdate(
    documentId=DOC_ID, body={"requests": requests}
).execute()
```

### Index ordering (multi-insert)
Each image occupies ~1 character index. When inserting multiple images, **process from highest index to lowest** (bottom of doc to top), or make separate calls bottom-to-top. This prevents index shift from misaligning subsequent images.

## Finding Insertion Positions

Read the document structure to locate section boundaries:

```python
doc = docs_service.documents().get(documentId=DOC_ID).execute()
for element in doc["body"]["content"]:
    text = "".join(
        pe.get("textRun", {}).get("content", "")
        for pe in element.get("paragraph", {}).get("elements", [])
    )
    if text.strip():
        print(f"idx {element['startIndex']}-{element['endIndex']}: {text.strip()[:80]}")
```

For inserting an image after a heading, use the heading paragraph's `endIndex` as the insertion point (it places the image right after the heading line).

## Pitfalls

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Using `fontFamily` on textStyle | Google API expects `weightedFontFamily.fontFamily` | Nest under `weightedFontFamily: {fontFamily, weight}` |
| Omitting `fields` mask | Field is silently ignored | Always set `fields` to comma-separated camelCase names |
| Image not publicly shared | `insertInlineImage` gets 403 | Set Drive permission `{"type":"anyone","role":"reader"}` first |
| Wrong URI format | Unknown image provider | Use `https://lh3.googleusercontent.com/d/FILE_ID` |
| Inserting images top-to-bottom | Indices shift, misplacing later images | Process bottom-to-top (descending index) |
| batchUpdate requests in wrong order | Each request sees document state after previous | Sort descending index for images; or process one at a time |
