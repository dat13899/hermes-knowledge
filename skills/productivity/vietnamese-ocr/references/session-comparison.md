# Session Comparison: Tesseract vs marker-pdf on Vietnamese

## Environment
- Windows 10, i5-10400, 32 GB RAM, no GPU
- Python 3.11.15
- Tested on: insurance ad JPG (1920×1080, 324 KB)

## Tesseract (v5.5.0)

### Setup
```bash
winget install Google.TesseractOCR
uv pip install pytesseract Pillow
# Download vie language pack
curl -o vie.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata
cp vie.traineddata "C:/Program Files/Tesseract-OCR/tessdata/"
```

### Command
```python
pytesseract.image_to_string(img, lang='vie+eng')
```

### Output
```
i. MB | ||) BHVIET

AT > CAN LO

LAI XE AN TAM - NHAN NGAY UU DAI

BAO HIEM TNDS
BAT BUOC O TO
30%:
PH{ CHI TU 336K/NAM
```

**State**: Poor. Most Vietnamese diacritics lost or corrupted. Layout absent.

## marker-pdf (v1.10.2)

### Setup
```bash
uv pip install marker-pdf
```
~2 min install. PyTorch CPU installed automatically.

### Command
```bash
# Convert JPG to PDF first
python -c "from PIL import Image; Image.open('test.jpg').save('test.pdf', 'PDF', resolution=150)"

# OCR
marker_single test.pdf --output_dir ./out
```

### First-run timing
- **Model download**: ~4 min on 100 Mbps connection
- **Models downloaded**: layout (1.35 GB), text_recognition, table_recognition (201 MB), text_detection (73 MB), ocr_error_detection (258 MB) — total ~3.3 GB
- **Cache location**: `C:\Users\<user>\AppData\Local\datalab\datalab\Cache\models\`
- **OCR time**: 41.88 seconds (including model download)

### Output
```markdown
![](_page_0_Picture_0.jpeg)

LÁI XE AN TÂM - NHẬN NGAY ƯU ĐÃI

## BẢO HIỂM TNDS BẮT BUỘC Ô TÔ

3 O GIẢM %

PHÍ CHỈ TỪ 336K/NĂM

![](_page_0_Picture_5.jpeg)
```

**State**: Excellent. All Vietnamese diacritics correct. Layout detected (markdown headers). Only minor error: "GIẢM 30%" rendered as "3 O GIẢM %" (layout ordering glitch).

## Disk & Memory
| | C: free before | C: free after | Models cache |
|---|---|---|---|
| Tesseract | 53 GB | 52.9 GB | ~100 MB |
| marker-pdf | 53 GB | 48.3 GB | 3.3 GB |

## Key Takeaway
For any Vietnamese text OCR: **Use marker-pdf directly.** Tesseract cannot handle Vietnamese diacritics reliably, even with the `vie` language pack installed. The ~3.3 GB model download is a one-time cost.
