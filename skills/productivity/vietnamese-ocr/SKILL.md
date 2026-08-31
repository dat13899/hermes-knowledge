---
name: vietnamese-ocr
description: OCR Vietnamese text with marker-pdf — setup, image-to-PDF conversion, model caching, Tesseract comparison.
version: 1.0.0
author: Hermes Agent (Anh Đạt's session)
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [OCR, Vietnamese, Tiếng Việt, marker-pdf, PDF, document-extraction]
    related_skills: [ocr-and-documents]
---

# Vietnamese OCR

Tiếng Việt uses extended Latin (Â, Ô, Ư, Đ, Ã, Ă, Ê, Ơ) — traditional Tesseract struggles badly. marker-pdf handles all 90+ languages natively with correct diacritics.

## Quick Setup

```bash
uv pip install marker-pdf
```

**First run**: ~3-5 min download models (~3.3 GB total) + OCR time. Models cached to:
- Windows: `%LOCALAPPDATA%\datalab\datalab\Cache\models\`
- Linux: `~/.cache/datalab/datalab/Cache/models/`
*(Not HuggingFace cache — marker-pdf uses datalab hub.)*

## Workflow

### PDF → Markdown

```bash
marker_single document.pdf --output_dir ./out
```

Output: `./out/document/document.md` with embedded images.

### Image (JPG/PNG) → Markdown

marker-pdf works on PDFs only. Convert first:

```bash
python -c "from PIL import Image; Image.open('photo.jpg').save('photo.pdf', 'PDF', resolution=150)"
marker_single photo.pdf --output_dir ./out
```

### Batch directory

```bash
marker /path/to/pdfs --workers 4
```

## Tesseract vs marker-pdf (Vietnamese)

| Aspect | Tesseract | marker-pdf |
|--------|-----------|------------|
| Diacritics | Mostly fails (Ô → O, Â → A, Đ → D) | Correct ✓ |
| Layout | Raw text dump | Structured markdown |
| Speed | Instant | ~1-14s/page (CPU) |
| Language pack | Must download `vie` separately | Built-in 90+ langs |
| Install size | ~50 MB | ~3.3 GB models |
| Table detection | No | Yes |
| Image → OCR | Via pytesseract | Via PDF conversion |

**Real example** (insurance ad, 1920×1080):

| Tesseract output | marker-pdf output |
|---|---|
| `BAO HIEM TNDS` | **BẢO HIỂM TNDS** |
| `BAT BUOC O TO` | **BẮT BUỘC Ô TÔ** |
| `LAI XE AN TAM` | **LÁI XE AN TÂM** |
| `NHAN NGAY UU DAI` | **NHẬN NGAY ƯU ĐÃI** |
| `PH{ CHI TU 336K/NAM` | **PHÍ CHỈ TỪ 336K/NĂM** |

→ marker-pdf is the correct choice for any Vietnamese document.

## Pitfalls

- **Cache path is NOT `~/.cache/huggingface/`** — don't look for models there. They're in `%LOCALAPPDATA%\datalab\`.
- **First run is slow** — ~3-5 min model download on typical broadband (100 Mbps). Subsequent runs skip it.
- **Image ≠ PDF** — don't pass a JPG directly to `marker_single`. Convert first with PIL.
- **No GPU needed** — runs on CPU (i5-10400 does ~1-14s/page). PyTorch CPU-only installed automatically.
- **C: drive space** — verify ~5 GB free before install. Models + PyTorch take ~3.3 GB.
- **Tesseract is still fine** for quick English text extraction from clean images — no model downloads needed. Use pytesseract for that case.

## See also

- `ocr-and-documents` skill — broader PDF/DOCX/PPTX extraction (pymupdf fast path)
