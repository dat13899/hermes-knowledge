# Vietnam Mutual Fund (Quỹ Mở) Portfolio Research

Use when the user asks for danh mục đầu tư / cổ phiếu holdings of a Vietnamese fund
(DCDE, DCDS, DCBF, DCIP, VFM funds, ETFs...) — usually on Telegram in Vietnamese.

## Sources (in order of usefulness)

- `dautu.dragoncapital.com.vn/tin-tuc/` — Dragon Capital's own report hub; monthly
  "Báo cáo hoạt động quỹ tháng <MM/YYYY> - Quỹ <CODE>". Most reliable, has full tables.
- `fmarket.vn/quy/<CODE>` — NAV, tổng tài sản, but portfolio detail is NOT in the
  text extract (rendered via JS/images). Its JSON APIs (`/api/v5/fund/detail?fund_code=...`,
  `/api/v5/fund/portfolio?fund_code=...`) return 404 — do not waste time on them.
- `smoney.com.vn/quy-dau-tu/<CODE>` — summary page, sparse holdings text.
- Fund manager sites: `dragoncapital.com.vn`, `vfm.com.vn`.

## Key technique: Dragon Capital report pages are Framer sites with PNG report images

The report HTML embeds the whole report as high-res PNG screenshots. Text extraction
(Tavily/web_extract) only returns nav/breadcrumbs — the tables live in images:

1. curl the page with a browser UA:
   `curl -sL --max-time 60 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0" <url> -o page.html`
2. Find image URLs: `grep -oE 'https://framerusercontent.com/images/[A-Za-z0-9_-]+' page.html | sort -u`
3. Identify report images via alt text — grep around candidate hashes for
   `alt="... Báo cáo ... tháng 06/2026 - Phần 1|Phần 2"` (parts 1..N).
4. Download high-res: `curl -sL -A "Mozilla/5.0" "<img-url>?width=1860&height=2631" -o report_p1.png`
   (append `?width=1860&height=2631` — the srcset shows these are the full-res variants).
5. Read each PNG with `vision_analyze` — it extracts tabular data from report images well.

## Vision prompt that works (Vietnamese report images)

"Đây là trang N báo cáo hoạt động quỹ <CODE> tháng <MM/YYYY>. Đọc CHÍNH XÁC toàn bộ:
(1) NAV/hiệu suất; (2) phân bổ theo ngành (%); (3) Top 10 khoản đầu tư: mã cổ phiếu +
nhóm ngành + % NAV; (4) bảng danh mục khác. Liệt kê từng dòng số liệu."

## Cross-check

- The page's `<meta name="description">` contains a one-line summary with key figures
  (e.g. "VHM chiếm tỷ trọng lớn nhất danh mục với 8,1% NAV, nhóm ngân hàng (BID, STB,
  VPB, ACB, CTG, VCB)..."). Use it to verify the vision-extracted numbers.
- If numbers from two sources disagree, prefer the fund manager's official report.

## Cadence & presentation rules

- Funds publish monthly; latest report lags ~2-4 weeks. Always state the report date
  in the answer (e.g. "báo cáo 30/6/2026") and warn the portfolio changes monthly.
- Vietnamese number format: comma decimals (28.672,4 đồng), tỷ for billions.
- Answer shape: Top 10 table (mã / ngành / % NAV + tổng), sector allocation, and
  2-3 notable points (NAV, YTD vs VN-Index, recent buys/sells from news articles).

## Example output shape — DCDE, report 30/6/2026 (do NOT reuse as live data)

- NAV/CCQ 28.672,4 đ; tổng tài sản 956,2 tỷ; 35 cổ phiếu; YTD -8,0% vs VN-Index +4,2%.
- Top 10 (52,5% NAV): VHM 8,1% (BĐS KDC), MWG 5,8% (bán lẻ), BID 5,5%, STB/VPB/ACB
  4,9%, CTG 4,8%, VCB 4,7% (ngân hàng), GMD 4,7% (vận tải), HPG 4,2% (kim loại).
- Ngành: ngân hàng 39,2%, tiền 12,1%, BĐS KDC 11,0%, bán lẻ 8,7%, chứng khoán 5,8%,
  kim loại 5,2%, vận tải 4,7%, còn lại <4% mỗi ngành.
- Recent moves (from news, e.g. vietnambiz/dnse): tăng TCB/POW/HPG, giảm VHM/CTG/PNJ/FPT,
  mua mới VRE, bán hết DGW/GAS.
