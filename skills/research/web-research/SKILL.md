---
name: web-research
description: "Web research via API fallbacks when browser and web_search tools are unavailable. Uses DuckDuckGo ddgs CLI, curl + public APIs (Wikipedia, restcountries, etc.). Includes Vietnamese-language research patterns and current-events/news summaries."
version: 3.0.0
author: Cu em
category: research
metadata:
  hermes:
    tags: [search, research, wikipedia, api, fallback, vietnamese, curl, duckduckgo]
    related_skills: [hermes-browser-setup, duckduckgo-search]
---

# Web Research (API Fallback)

## When to Use

- `web_search` tool does not exist in the current toolset/backend (tool call returns "Tool 'web_search' does not exist")
- Browser automation (`browser_navigate`) fails silently (Chrome exits with code 0, CDP port unreachable)
- User needs factual information from reliable, structured sources
- Vietnamese-language queries needing good regional coverage

## GitHub Trending & Repo Research — "cái gì đang hot trên GitHub?"

Khi user hỏi repo nào đang trend/hot (vd AI agents, MCP, frameworks) hoặc cần profile một repo:

1. **Scrape trending page**: `curl -sSL -A "Mozilla/5.0" "https://github.com/trending?since=weekly" > ~/tmp/trending.html` (`since=weekly|daily|monthly`)
2. **Lấy repo slugs bằng grep** — đừng over-invest regex vào HTML article (cấu trúc hay đổi, từng khớp 0 kết quả): `grep -oE 'href="/[^"]+/[^"]+"' | grep -vE '/(trending|topics|...)' | sort -u | sed 's|href="/||;s|"||'`
3. **Enrich metadata qua GitHub API** (không auth, ~60 req/h): `curl -s https://api.github.com/repos/<owner>/<repo>` → stargazers_count, language, description, topics, created_at/updated_at
4. **Discovery repo mới/star nhanh**: `curl -s "https://api.github.com/search/repositories?q=<terms>+created:%3E2026-01-01&sort=stars&order=desc&per_page=15"`
5. **Trình bày theo chủ đề** + ⭐ + ngôn ngữ + vì sao liên quan tới user (so stack họ đang dùng), kết bằng đề nghị đào sâu — đừng tự ý clone hàng loạt.

Pitfall Windows: dùng `~/tmp` (MSYS không có `/tmp` → curl exit 23 CURLE_WRITE_ERROR); dùng `python` chứ KHÔNG `python3` trong heredoc (alias này không tồn tại trên host).

Full recipe + lệnh mẫu + rate limit: `references/github-trending-research.md`

## Detection

Before falling back, confirm the primary tools are truly unavailable:

```python
# If web_search fails, try browser
# If browser_navigate fails too, this is your workflow
```

Do NOT assume the tools are broken permanently (environment may change between sessions).

---

## Vietnamese Mutual Fund (Quỹ Mở) Portfolio Research

For fund portfolio lookups (DCDE, DCDS, DCBF, ...): Dragon Capital report pages are
Framer sites — the tables live in PNG images. Technique, vision prompt, sources and
presentation rules: `references/vietnam-fund-research.md`.

## Extraction Fallback: Tavily MCP (when web_extract is DDG-only)

If `web_extract` errors with "DuckDuckGo (ddgs) is a search-only backend and
cannot extract URL content", the extract backend is DDG. Use the Tavily MCP
tools instead (keys in ~/.omniroute/.env):
`mcp__tavily__tavily_extract` (pages, same shape as web_extract) and
`mcp__tavily__tavily_search` (richer snippets, works where plain search
snippets are thin). Also effective on heavy JS sites that make the browser
time out.

## Vietnam Fund / ETF Portfolio Research

Finding danh mục đầu tư / tỷ trọng % NAV of VN open-end funds & ETFs (DCDE,
DCDS, DCBF, VFM...): fund-manager monthly reports > news articles with
"Cơ cấu danh mục" images (read via vision_analyze) > search-snippet mining >
FMarket (summary only, JS-rendered). Full playbook with tested URLs and the
DCDE example: `references/vietnam-fund-portfolio-research.md`.

---

## Primary Fallback: Wikipedia REST API

Wikipedia's REST API requires no API key, returns clean JSON, and has excellent Vietnamese coverage.

### 1. Quick Summary

```bash
curl -s "https://vi.wikipedia.org/api/rest_v1/page/summary/B%E1%BA%AFc_Ninh" | \
python -c "import json,sys; d=json.load(sys.stdin); print(d.get('extract','Not found'))"
```

Returns a concise extract (~2-5 paragraphs). Also returns `coordinates`, `thumbnail`, `content_urls` keys.

### 2. List All Sections (to find section index numbers)

```bash
curl -s "https://vi.wikipedia.org/w/api.php?action=parse&page=B%E1%BA%AFc_Ninh&prop=sections&format=json&utf8=1"
```

Example output:
```
   8 | Lịch sử (Lịch_sử)
  10 | Kinh tế (Kinh_tế)
  15 | Văn hóa (Văn_hóa)
```

### 3. Get Full Section Content

```bash
curl -s "https://vi.wikipedia.org/w/api.php?action=parse&page=B%E1%BA%AFc_Ninh&prop=text&section=8&format=json&utf8=1" | \
python -c "
import json,sys,re
data=json.load(sys.stdin)
html=data['parse']['text']['*']
text=re.sub(r'<ref[^>]*>.*?</ref>','',html,flags=re.DOTALL)
text=re.sub(r'<br\s*/?>','\n',text)
text=re.sub(r'<[^>]+>',' ',text)
text=re.sub(r'&#\d+;','',text)
text=re.sub(r'\[ ?\d+ ?\]','',text)
text=re.sub(r'\s+',' ',text)
print(text)
"
```

### 4. Get Infobox / Raw Wikitext (for structured data)

```bash
curl -s "https://vi.wikipedia.org/w/api.php?action=query&prop=revisions&titles=B%E1%BA%AFc_Ninh&rvprop=content&rvsection=0&format=json&utf8=1"
```

### 5. Key JSON fields from REST API summary

```python
{
  'title': 'Bắc Ninh',
  'extract': '...',          # Plain text summary
  'coordinates': {'lat': 21.18, 'lon': 106.07},
  'thumbnail': {'source': '...', 'width': 320, 'height': 240},
  'content_urls': {
    'desktop': {'page': 'https://vi.wikipedia.org/wiki/B%E1%BA%AFc_Ninh'},
    'mobile': {'page': 'https://vi.m.wikipedia.org/wiki/B%E1%BA%AFc_Ninh'}
  },
  'description': 'Tỉnh thuộc Đồng bằng sông Hồng'
}
```

---

## General Research Approach

```
1. Try web_search tool          → if exists and works, done
2. Try browser_navigate         → if Chrome/CDP works, use Google
3. Fall back to curl + API      → Wikipedia is the safest bet
4. For JSON/CMS content         → try direct curl to the endpoint (no browser needed)
```

### URL encoding for Vietnamese characters

Characters like ắ, ấ, ẩ, ô, ơ, ư, đ MUST be percent-encoded in URLs. Python's `urllib.parse.quote()` handles this, or simply copy the encoded form from the user's original Vietnamese message if they typed the unaccented/plain form.

Quick test of encoding:

```bash
# Instead of: https://vi.wikipedia.org/wiki/Bắc Ninh
# Use:        https://vi.wikipedia.org/wiki/B%E1%BA%AFc_Ninh
python -c "import urllib.parse; print(urllib.parse.quote('Bắc Ninh'))"
# → B%E1%BA%AFc%20Ninh (then replace %20 with _ for Wikipedia titles)
```

### Fallback for non-Wikipedia queries

| Source | API Pattern | Requires |
|--------|------------|----------|
| Wikipedia | `https://{lang}.wikipedia.org/api/rest_v1/page/summary/TITLE` | Nothing |
| OpenStreetMap | `https://nominatim.openstreetmap.org/search?q=...&format=json` | User-Agent header |
| REST Countries | `https://restcountries.com/v3.1/name/{name}` | Nothing |
| OpenLibrary | `https://openlibrary.org/search.json?q={query}` | Nothing |
| DuckDuckGo Instant | `https://api.duckduckgo.com/?q={query}&format=json` | Nothing |

---

## Primary Search: DuckDuckGo CLI (`ddgs`)

When `web_search` tool is unavailable (e.g. DeepSeek custom provider), **DuckDuckGo via `ddgs` CLI** is the best free search option — no API key, no signup, works for text/news/images/videos.

Install the official skill + Python package (one-time):
```bash
hermes skills install official/research/duckduckgo-search
pip install ddgs          # or: uv pip install ddgs
```

### Text Search (general research)
```bash
ddgs text -q "Bắc Ninh tỉnh thông tin địa lý" -m 5
```
Returns: `title`, `href`, `body`

### News Search (current events)
```bash
ddgs news -q "Bắc Ninh" -m 5 -t w
```
Flags: `-t d|w|m|y` (day/week/month/year). Returns: `date`, `title`, `body`, `url`, `source`

### JSON Output (for script processing)
```bash
ddgs text -q "fastapi tutorial" -m 5 -o json
```

### Region Filtering
```bash
ddgs text -q "best pho" -m 5 -r vn-vn
```

### Search → Extract Pipeline
DuckDuckGo returns snippets only. Full content requires a second step:
```bash
# Step 1: search
ddgs text -q "python async" -m 3
# Step 2: pick best URL, extract via browser or curl
browser_navigate("https://best-result-url.com")
```

### Limitations
- **Rate limiting**: DuckDuckGo throttles rapid requests. Add 1-2s delay between searches.
- **News endpoint fragile**: the Yahoo-powered news search is more prone to blocking than text search. Expect occasional `tls handshake eof` errors and have a fallback ready.
- **Snippets only**: no full page content from `ddgs` itself.
- **Cloud IP blocks**: some server IPs may be blocked. Local machine (Windows git-bash) works fine.
- **`max_results` is keyword-only** in Python API: `ddgs.text("q", max_results=5)` not positional.
- **Windows: `python3` is MS Store alias**: On Windows, `python3` invokes the Microsoft Store stub, NOT CPython. Always use `python` (3.11+). `python3 -c "..."` fails silently; `python -c "..."` works. Verify with `python --version`.
- **ddgs CLI may return empty for news on Windows**: The CLI path sometimes returns no output for `ddgs news` while the Python API from the same venv works. Workaround: use `python -c "from ddgs import DDGS; ..."` from the venv when CLI fails.

### Detection
```bash
command -v ddgs >/dev/null && echo "DDGS_CLI=installed" || echo "DDGS_CLI=missing"
```

### Search Priority Path
```
1. web_search tool            → if exists, use it (best, 0 setup)
2. ddgs CLI (DuckDuckGo)      → BEST free option, no API key (⬅ THIS)
3. Browser Google/Bing        → if CDP/Chrome works (search engines block headless)
4. Wikipedia API fallback     → factual queries only (no keys needed)
5. Tavily CLI                 → when more power needed (needs API key signup)
```

### News Scanning ("hôm nay có tin gì nổi bật" pattern)

For current-events / "what's breaking today" type queries:

```bash
# Strategy 1: broad English query (less rate-limited than Vietnamese)
ddgs news -q "breaking news today" -m 10

# Strategy 2: Vietnamese-specific, short query
ddgs news -q "tin nóng hôm nay" -m 8 -t d

# Strategy 3: technology-focused
ddgs news -q "công nghệ" -m 5

# Strategy 4: fallback — text search when news API is blocked (tls/connect errors)
ddgs text -q "Việt Nam tin nóng hôm nay" -m 5
```

**Rate limit survival tips for news queries:**
- DDGS news endpoint (Yahoo) rate-limits aggressively — errors like `ConnectError: tls handshake eof` or `DDGSException` mean wait 5-10s and retry with a different query
- Mix English + Vietnamese queries: English queries (`breaking news today`, `world news`) are less likely to be blocked
- Avoid `-t d` filter on first call — do a broad search first, let it sort by relevance
- When news fails entirely: fall back to `ddgs text -q "topic tin mới"` (text search still works when news endpoint is blocked)
- Space queries apart: don't call `ddgs news` more than 2x in quick succession

---

## GitHub Repository Research

When researching open-source project popularity, check GH stars directly via unauthenticated API.

### Batch star lookup

```bash
for repo in "facebook/react" "vuejs/vue" "vercel/next.js" "twbs/bootstrap"; do
  data=$(curl -s "https://api.github.com/repos/$repo")
  stars=$(echo "$data" | python -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"stargazers_count\"]:,}')")
  echo "$stars  $repo"
done
```

Returns `246,315  facebook/react` etc. No token needed for public repos (60 req/hr unauthenticated; add `Authorization: token ghp_...` for 5000 req/hr).

### Check single repo

```bash
curl -s "https://api.github.com/repos/vercel/next.js" | \
python -c "import sys,json; d=json.load(sys.stdin); print(d['stargazers_count'], '⭐', d['full_name'])"
```

### Search repos by topic

```bash
curl -s "https://api.github.com/search/repositories?q=topic:frontend+topic:framework&sort=stars&order=desc&per_page=5" | \
python -c "import sys,json; [print(f'{r[\"stargazers_count\"]:>7}  {r[\"full_name\"]}') for r in json.load(sys.stdin)['items']]"
```

### Caveats

- **Rate limit**: 60 req/hr (unauthenticated), 5000 req/hr (with token). Check remaining: `curl -sI https://api.github.com/rate_limit | grep -i x-ratelimit-remaining`
- **Star count != quality**: check `pushed_at`, `open_issues_count`, `forks_count` for health signals
- **Topic search** finds category leaders. Add `+language:typescript` filter as needed

### Star → ranking context

| Range | Tier |
|-------|------|
| >200k | Legendary (React, Vue) |
| 100k-200k | Industry standard (Bootstrap, Next.js) |
| 50k-100k | Very popular (Tailwind, Angular) |
| 10k-50k | Well-known (shadcn/ui, Zustand) |
| 1k-10k | Growing |

### Deep repo evaluation ("repo này có xịn không?" / "có tốt hơn cái đang dùng không?")

Stars alone don't answer that — especially for AI-skill repos where star
counts can be inflated. Go beyond the lookup above:

1. **Metadata first**: `full_name`, `description`, `default_branch`, stars, created/updated, language (`/repos/<owner>/<repo>`).
2. **README raw** — bypasses the `web_extract` ddgs limitation entirely:
   ```bash
   curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/README.md | head -200
   curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/README.md | sed -n '200,400p'
   ```
   (branch from metadata, không hardcode `main`).
3. **Repo tree** — see what's real vs. marketing:
   ```bash
   curl -s "https://api.github.com/repos/<owner>/<repo>/contents/" | \
   python -c "import json,sys; [print(f\"{x['type']:5} {x['name']}\") for x in json.load(sys.stdin)]"
   ```
4. **Sample the actual data** — for data-driven skills, `head` the data files
   (walk `.../contents/src/.../data`) to judge substance. Rác/generated filler
   lộ ngay trong 15 dòng đầu. Check `data-provenance.json`, license files
   (fonts/icons licenses) — dấu hiệu repo nghiêm túc.
5. **Health signals**: version churn + releases (skill.json `version`), update recency, premium-upsell footprint (free tier còn đủ phần core không).
6. **Compare, don't replace**: đánh giá so với thứ đang có sẵn. Lookup database
   (styles/products/palettes) bổ sung cho opinionated decision skill chứ
   không thay thế — kết luận thường là "bổ sung, không thay thế".

Example verdict for a real case: `references/ai-design-skill-evaluation.md`.

---

## References

See [`references/provider-context.md`](references/provider-context.md) for known model context lengths (DeepSeek V4 Flash = 1M, lookup strategy for custom endpoints).

See [`references/ai-fe-tools.md`](references/ai-fe-tools.md) for AI-powered frontend development tools catalog.

See [`references/vietnamese-daily-briefing.md`](references/vietnamese-daily-briefing.md) for daily "Điểm tin sáng" briefing workflow — Open-Meteo weather, ddgs news, web_search fallback, positivity.org quote API, cron-autonomous output format. Load when the cron system requests `agent-daily-briefing` (which is hub-installed and may be unsupported on Windows — this reference serves as the working substitute).

## Secondary: Wikipedia REST API

*(all existing Wikipedia API content stays as-is)*

## Pitfalls

- **Wikipedia Parse API returns HTML**, not plain text. Always strip tags.
- **Reference tags** (`<ref>...</ref>`) can be nested — use `flags=re.DOTALL` in regex.
- **&#NNNN; entities** (Unicode numeric entities) need decoding: `re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)`
- **UTF-8 BOM**: Windows Notepad may insert BOM. Pass `encoding='utf-8-sig'` in Python or use `--raw` in curl.
- **Rate limiting**: Wikipedia API is generous but avoid rapid-fire requests. Add `sleep(1)` between calls in loops.
- **Redirects**: Wikipedia pages may redirect. The REST API follows them, but the Parse API may not — check the page ID.
- **Disambiguation pages** return minimal content. Check `type` field in REST response (should be 'standard', not 'disambiguation').

---

---

## SPA API Discovery (when the page is client-rendered)

Some sites are SPAs (Angular/React/Vue) — initial HTML is a shell (`<app-root>`, `<div id="root">`), real content loads via JS → API calls. When the API blocks your IP, try these techniques to find endpoints and data shapes.

### 1. Detect SPA

```bash
# Angular: <app-root></app-root> + modulepreload chunks
curl -sL "https://example.com" | grep -oP '<app-root>'

# React: <div id="root"> + <script> with /static/js/
curl -sL "https://example.com" | grep -oP 'id="root"'

# Vue: <div id="app">
```

### 2. Find API base URL

Many SPAs load config from a simple file:

```bash
curl -sL "https://example.com/appconfig.json"
# Often returns: {"apiUrl": "https://api.example.com"}

# Also try: config.json, env.json, settings.json, runtime.json, environment.js
```

### 3. Extract API endpoints from JS chunks

Angular builds produce named chunks. Find service files and grep for API paths:

```bash
# Get all JS chunk URLs from the page HTML
curl -sL "https://example.com" | grep -oP 'src="([^"]+\.js)"' | cut -d'"' -f2

# Grep the main JS bundle for API routes
curl -sL "https://example.com/main-XXXXXX.js" | grep -oP '"[A-Z][a-zA-Z]+/[A-Z][a-zA-Z]+"'

# Search for 'apiDefault' or 'apiUrl' patterns
curl -sL "https://example.com/main-XXXXXX.js" | tr ';' '\n' | grep -i 'api\|endpoint\|get\|post'

# Look for HTTP service calls
curl -sL "https://example.com/main-XXXXXX.js" | grep -oP '`\$\{this\.apiDefault\}[^`]+`'
```

### 4. Understand the data shape from component templates

The component code shows which fields are rendered:

```bash
# Search for properties like: item.name, item.shortDescription, item.endDate, item.tag
# These reveal the API response shape
curl -sL "https://example.com/main-XXXXXX.js" | tr ',' '\n' | grep -oP 'item\.[a-zA-Z]+'
```

### 5. When the API is unreachable

If the API server times out (likely IP whitelisting / Vietnam-only):

- **Try the main domain as proxy**: sometimes `https://example.com/api/Endpoint` works when `https://api.example.com/Endpoint` doesn't — check for 406 vs timeout to distinguish blocked vs proxied
- **Check if it's a CDN file server**: `https://file.example.com/` — may host public assets and be accessible even when the API isn't
- **Google Cache**: `https://webcache.googleusercontent.com/search?q=cache:https://example.com/page`
- **Wayback Machine**: `https://web.archive.org/web/2025/https://example.com/page` — use CDX API to check for captures: `http://web.archive.org/cdx/search/cdx?url=example.com/*&output=json`
- **Web search with site: prefix**: `ddgs text -q "site:example.com promotion OR ưu đãi"` — may find if the SPA has prerendered pages indexed
- **Facebook/Google Cache**: sometimes the site's social share previews contain snippets

### 6. Blockers to report

| Symptom | Likely cause | What to tell user |
|---------|-------------|-------------------|
| Site HTML loads, API times out | API IP-whitelisted or geo-blocked | "Site loads (SPA shell) but API blocks our IP — may need Vietnam-based browser" |
| Site itself times out | Server down or global IP block | "Site unreachable entirely" |
| SPA loads but no API | SPA needs JS render | "Client-rendered site, try local browser with CDP" |

---

## Vietnamese Language Research (Specific to vi.wikipedia.org)

- Vietnamese Wikipedia covers provinces, districts, historical figures, and cultural topics extensively.
- Topic titles use underscores for spaces: `Bắc_Ninh`, `Hà_Nội`, `Lịch_sử_Việt_Nam`
- Section numbers vary by page — always fetch the section index first.
- The `extract` field in REST API is always in the page's language (Vietnamese for vi.wikipedia.org).
- For historical events, the language can be formal/classical Vietnamese — expect Sino-Vietnamese vocabulary.
