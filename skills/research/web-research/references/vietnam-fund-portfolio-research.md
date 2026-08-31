# Vietnam Fund / ETF Portfolio Research (quỹ mở, chứng chỉ quỹ)

Goal: find current holdings (danh mục đầu tư) + weights (tỷ trọng % NAV) of
Vietnamese open-end funds / ETFs (Dragon Capital DCDE/DCDS/DCBF, VFM, etc.).
Tested 2026-07 with DCDE.

## Source hierarchy (most → least reliable)

1. **Fund manager monthly reports** — e.g. Dragon Capital:
   `dautu.dragoncapital.com.vn/tin-tuc/bao-cao-hoat-dong-quy-thang-<MM>.<YYYY>-quy-<FUND>`
   (slug: `bao-cao-hoat-dong-quy-thang-06.2026-quy-dcde`). Contains NAV/CCQ,
   YTD return vs VN-Index, top holdings with % NAV, sector allocation.
   Tavily extract returns the headline summary; full tables may be images or
   truncated — pair with vision_analyze on embedded images.
2. **News articles with "Cơ cấu danh mục" images** — vietnambiz.vn, dnse.com.vn
   publish portfolio tables as IMAGES, not HTML tables. Extract the image URL
   (often CDN, e.g. `cdn.vietnambiz.vn/...jpeg?width=1000`) then
   `vision_analyze` it. Worked: read full top-10 holdings (VIC 11.2, BID 8.1,
   HPG 7.2, VHM 6.0, STB 4.7, MWG 4.7, TCB 4.6, HDB 3.4, VPB 3.3, NVL 2.8 —
   total 56.0% NAV) from a vietnambiz CDN image. Also read holding-quantity
   change tables (cuối tháng N / thay đổi) the same way.
3. **Search snippet mining** — when pages fail to load, search result
   descriptions often carry the key facts (e.g. "VHM chiếm tỷ trọng lớn nhất
   danh mục với 8,1% NAV, nhóm ngân hàng (BID, STB, VPB, ACB, CTG, VCB) chiếm
   tỷ trọng đáng kể"). Query template: `<FUND> báo cáo hoạt động quỹ tháng
   <MM>/<YYYY> top <N> <ticker hints>`.
4. **FMarket (fmarket.vn/quy/<CODE>)** — good for NAV, fund size (tài sản ròng),
   sector bar chart; but holdings table is JS-rendered: raw HTML shows only the
   summary, API endpoints 404 (e.g. `/api/v5/fund/portfolio?fund_code=DCDE` →
   404 page), and browser navigation may time out. Don't rely on it for full
   holdings.

## Techniques & pitfalls

- `web_extract` fails when the extract backend is DDG: "DuckDuckGo (ddgs) is a
  search-only backend and cannot extract URL content" → use
  `mcp__tavily__tavily_extract` instead (keys in ~/.omniroute/.env). Same for
  heavy JS sites: Tavily often succeeds where browser times out.
- Vietnamese comma decimals: `30,1` = 30.1%; `956.2 tỷ` = 956.2 billion VND.
- DCDE context: open-end dividend-focused equity fund, ~956 tỷ VND NAV
  (06/2026), Ngân hàng sector ~30% NAV. DCDS is the sibling dynamic fund —
  news tables often show DCDS + DCDE side by side; verify which table you read.
- Compare fund YTD return vs VN-Index for performance context.
