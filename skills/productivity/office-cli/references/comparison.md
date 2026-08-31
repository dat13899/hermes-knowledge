# OfficeCLI vs python-* library comparison test results

Tests run: 2026-07-17, Windows 10, git-bash/MSYS, OfficeCLI v1.0.136

## Test structure

Each test created equivalent documents with both OfficeCLI and the corresponding Python library (python-docx for Word, python-pptx for PowerPoint). Excel tested OfficeCLI only (no existing openpyxl skill).

## Word test results

| Property | python-docx | OfficeCLI |
|----------|-------------|-----------|
| File size | 37,109 bytes | 5,787 bytes |
| Build-in styles | Yes (Title, Heading1-9, Normal) | Minimal (no Heading styles) |
| Table support | Yes | Yes |
| Bold text | Yes | Yes |
| Color text | Yes | Yes |
| Font size | Yes | Yes |
| Outline view | 9 paragraphs, 1 table | 8 paragraphs, 1 table (missing "3. Bảng Số Liệu" heading) |
| HTML render | N/A | 56,783 bytes, high fidelity |

**Issues found:**
- OfficeCLI blank `create` produces no built-in Heading styles → warnings on style usage
- Table section heading "3. Bảng Số Liệu" not shown in OfficeCLI outline view (but table is present)
- python-docx file is ~6x larger due to embedded theme/styles template

## PowerPoint test results

| Property | python-pptx | OfficeCLI |
|----------|-------------|-----------|
| File size | 29,416 bytes | 10,909 bytes |
| Slide count | 2 | 2 |
| Shapes per slide | S1:1 (textbox multi-para), S2:2 | S1:1 shape, S2:4 shapes |
| Background color | Yes (slide 1 dark navy) | Yes (slide 1 dark navy) |
| Text formatting | Yes (bold, size, color, alignment) | Yes (bold, size, color) |
| HTML render | N/A | 23,934 bytes |
| Screenshot | N/A | Requires Playwright |

**Issues found:**
- OfficeCLI creates separate shapes for each text line; python-pptx uses one textbox with multiple paragraphs
- Screenshot not available without Playwright (`pip install playwright && playwright install chromium`)

## Excel test results

| Property | openpyxl (estimate) | OfficeCLI |
|----------|---------------------|-----------|
| File size | N/A | 4,628 bytes |
| Headers | N/A | Yes |
| Data rows | N/A | Yes (3 rows) |
| Formula SUM | N/A | Yes — auto-evaluated: B5=`4200000` |
| Currency format | N/A | Yes (`$#,##0`) |
| Percentage format | N/A | Yes (`0%`) |
| Output formatting | N/A | 25%, 30%, 15% rendered correctly |

**Formula evaluation works correctly** — SUM formula written to B5 auto-evaluates to 4,200,000.

## Environment gotchas

### Windows path handling (OfficeCLI)
```
# WRONG — produces C:\c\Users\...\out.html
officecli view file.docx html -o /c/Users/me/out.html

# RIGHT
officecli view file.docx html -o "C:\Users\me\out.html"
```

### Bash dollar sign expansion
```
# WRONG — $2.1M expands to .1M (bash variable)
officecli set file.xlsx '/Sheet1/B2' --prop text="$2.1M"

# RIGHT
officecli set file.xlsx '/Sheet1/B2' --prop text='$2.1M'
```

## Conclusion

OfficeCLI is suitable for production use. The main drawbacks vs python libraries:
1. No built-in Heading styles in blank docx (use template or accept)
2. Screenshot needs Playwright (HTML render works without it)
3. MSYS path handling requires Windows-style paths
