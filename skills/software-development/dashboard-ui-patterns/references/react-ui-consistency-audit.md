# React Multi-Page UI Consistency Audit

Khi user phàn nàn giao diện "xấu với loạn" trên site React multi-page, nguyên nhân gốc thường là mỗi page dùng một hệ thống style khác nhau. Audit pattern này phát hiện inconsistency trong 5 phút.

## Step 1: Audit CSS variable usage per page

```bash
cd frontend/src/pages
for f in HomePage HermesPage DashboardPage DocumentsPage; do
  [ -f "${f}.jsx" ] && echo "=== ${f}.jsx ===" && \
  echo -n "  glass-bg: " && grep -co "var(--glass-bg)" "${f}.jsx" 2>/dev/null || echo 0 && \
  echo -n "  glass-border: " && grep -co "var(--glass-border)" "${f}.jsx" 2>/dev/null || echo 0 && \
  echo -n "  border (bare): " && grep -c "var(--border)" "${f}.jsx" 2>/dev/null || echo 0 && \
  echo -n "  inline style={{: " && grep -c "style={{" "${f}.jsx" 2>/dev/null || echo 0 && \
  echo -n "  chars: " && wc -c < "${f}.jsx"; echo
done
```

## Step 2: Interpret results

| Signal | Interpretation |
|---|---|
| `glass-bg: 0` trên tất cả page | Không ai dùng glass tokens → mỗi page tự define style |
| `glass-border` count biến động lớn (0-20) | Mỗi page 1 hệ thống border khác nhau |
| `inline style={{` > 50 trên 1 page | Monolith component, khó maintain |
| 1 page có CSS file riêng (`.css`) | Isolation — visual language khác hẳn các page khác |
| Page < 1KB | Placeholder/iframe — chưa có style |

## Step 3: Real-world example (btdat.io.vn)

| Page | glass-bg | glass-border | inline styles | Size | Issue |
|---|---|---|---|---|---|
| HomePage | 0 | 0 | 2 | 5KB | Dùng `home.css` riêng 116 dòng, 0 glass |
| HermesPage | 0 | 0 | 2 | 880B | iframe trần |
| DashboardPage | 0 | 20 | 69 | 22KB | Monolith inline-style |
| DocumentsPage | 0 | 0 | 7 | 9.8KB | Sub-components |

→ **4 page, 4 visual language khác nhau** → user nói "xấu với loạn"

## Step 4: Double-rendering detection

Kiểm tra component được render 2 lần (1 trong page + 1 trong layout):

```bash
# Footer rendered in both HomePage AND AppLayout?
grep -n "<footer\|<Footer" src/pages/HomePage.jsx src/components/layout/AppLayout.jsx
```

Pattern phổ biến: `AppLayout` có `<Footer />`, nhưng `HomePage` cũng tự render footer → 2 footer chồng nhau.

## Step 5: Fix order

1. **Xoá trùng lặp trước** (double footer, double navbar)
2. **Bỏ CSS files riêng** → chuyển sang inline styles + shared class
3. **Tách monolith** (page > 15KB) thành component con
4. **Đồng bộ section spacing** (uniform `padding: 3rem 1.5rem`)
5. Build + deploy + verify
