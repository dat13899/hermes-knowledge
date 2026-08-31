# Vietnamese Daily Briefing Workflow

Produce "Điểm tin sáng" (morning briefing) via cron. No user interaction.

## Config file

`C:\\Users\\<user>\\AppData\\Local\\hermes\\BRIEFING.md`

Controls which sections enabled (Weather, Calendar, Tasks, News, Quote) and news topics. Read this first every run.

## Weather — Open-Meteo (free, no key)

Hà Nội (lat=21.02, lon=105.85):

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=21.02&longitude=105.85&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia%2FBangkok&forecast_days=7"
```

Parse with python in same curl pipe (works on git-bash):
```bash
curl -s "..." | python -c "import sys,json; d=json.load(sys.stdin); c=d['current_weather']; print(f\"Nhiệt độ: {c['temperature']}°C, Gió: {c['windspeed']} km/h, Mã thời tiết: {c['weathercode']}\")"
```

WMO weather codes seen in practice:
- 0=trong xanh, 1=chủ yếu trong, 2=nhiều mây, 3=u ám
- 45=sương mù, 48=sương muối
- 51=mưa phùn nhẹ, 53=mưa phùn vừa, 55=mưa phùn dày
- 61=mưa nhẹ, 63=mưa vừa, 65=mưa nặng hạt
- 80=mưa rào nhẹ, 81=mưa rào vừa, 82=mưa rào dữ dội
- 95=dông, 96=dông kèm mưa đá nhẹ, 99=dông kèm mưa đá nặng

## Quote of the day — positivity.org (free, no key)

```bash
curl -sL "https://positivity.org/quotes/daily-quotes/$(date +%Y-%m-%d)" | grep -oP 'description"[^>]*content="\K[^"]+' | head -1
```

Returns format: `Today's quote of the day: "..." — Author.` Extract the quote text and author for the briefing.

## State file for deduplication

Path: `C:\\Users\\<user>\\AppData\\Local\\hermes\\cron\\state\\briefing_bank.json`

Purpose: track used URLs and headlines so news isn't repeated across days.

Structure:
```json
{
  "last_briefing_date": "2026-07-21",
  "used_urls": ["https://..."],
  "sent_headlines": ["Spain vô địch World Cup 2026", "..."]
}
```

Workflow:
1. Read file at start → check `last_briefing_date` and `used_urls`/`sent_headlines`
2. File missing = first run → no dedup needed
3. After building briefing → write file with new URLs + headlines + today's date
4. Use `write_file` tool (not execute_code — blocked in cron mode)

## News gathering — search + extract cycle

The tooling landscape often requires multiple fallback layers:

```
ddgs news → ddgs text → web_search → curl scrape
```

### Step 1: ddgs (preferred but fragile)

```bash
# Check CLI first
command -v ddgs >/dev/null && echo "DDGS_CLI=installed" || echo "DDGS_CLI=missing"

# News search (most fragile — watch for TLS errors)
ddgs news -q "Việt Nam hôm nay thời sự" -m 5 -t d -o json

# If news fails with TLS error — text search as fallback
ddgs text -q "world news today" -m 5 -t d -o json

# If text search also returns empty — rate limited, fall through
```

Known failure modes:
- `tls handshake eof` on news endpoint → text search may still work
- Empty output from ALL query types → rate-limited/blocked entirely
- **`-o json` vs non-JSON inconsistency**: `-o json` can silently produce empty stdout on some queries where the same query without `-o json` returns results. Troubleshoot empty JSON output by first trying without `-o json`. When JSON output is empty and text output has results, use text output directly (parse with grep/sed if needed).
- **Vietnamese news coverage is weak**: `ddgs news` via Yahoo backend has poor Vietnamese-language coverage. Queries like `"Việt Nam kinh tế thời sự"` may return articles from months or years ago. Workarounds: (a) use `ddgs text -q` instead of `ddgs news` for Vietnamese topics (text returns fresher results), (b) use shorter English-mixed queries like `"Vietnam news July 2026"`, (c) fall back to RSS feeds or `web_search` tool.
- **Vietnamese text queries often return portal homepages** (vietnamnet.vn/thoi-su, thanhnien.vn/thoi-su.htm, baomoi.com/) rather than specific articles. This is a Yahoo backend limitation for non-English searches. Get specific articles from RSS feeds or use `web_search` tool instead.

### Step 2: web_search tool

```
# Built-in search tool, works when ddgs is blocked
web_search(query="Việt Nam tin tức hôm nay", limit=5)
```

### Step 3: RSS feeds (Vietnamese news, curl-parseable, no JS needed)

```bash
# VnExpress Thời sự
curl -sL "https://vnexpress.net/rss/thoi-su.rss" | grep -oP '(?<=<title>)[^<]+' | head -10

# Thanh Niên
curl -sL "https://thanhnien.vn/rss/home.rss" | grep -oP '(?<=<title>)[^<]+' | head -10

# VietNamNet
curl -sL "https://vietnamnet.vn/rss/home.rss" | grep -oP '(?<=<title>)[^<]+' | head -10
```

### Step 4: Content extraction from HTML pages

web_extract may be unavailable (ddgs-only backend). Use curl for extraction:

```bash
# Strip HTML to plain text
curl -sL --max-time 15 "URL" | sed 's/<[^>]*>//g' | sed '/^[[:space:]]*$/d' | head -60

# Extract titles from link elements
curl -sL --max-time 15 "URL" | grep -oP '(?<=title=")[^"]+' | head -20

# Extract specific content with grep
curl -sL --max-time 15 "URL" | grep -i -E 'topic1|topic2' | head -30
```

## Topic-specific search patterns

### Vietnam news
- `ddgs news -q "Việt Nam thời sự hôm nay" -m 5 -t d`
- RSS: VnExpress, Thanh Niên, VietNamNet RSS (step 3)
- NSO: `curl -sL "https://www.nso.gov.vn/..."` for economic data

### World news
- `ddgs news -q "world news today July 2026" -m 5 -t d`
- Aggregator: `curl -sL "https://www.worldtopnewsnow.com/2026/07" | sed 's/<[^>]*>//g'`
- Guardian: `curl -sL "https://www.theguardian.com/international"`

### Tech/AI
- `ddgs news -q "AI technology news 2026" -m 5 -t d`
- Guardian AI section: `curl -sL "https://www.theguardian.com/technology/artificialintelligenceai"` — extract headlines with `grep -i -E 'AI|artificial'`

### World Cup / Sports
- `ddgs text -q "World Cup 2026 results" -m 5`
- SportPaedia: `curl -sL "https://www.sportpaedia.com/world-cup-2026-knockout-stage/"` — detailed match data in HTML
- Search: `web_search(query="World Cup 2026 knockout stage results", limit=5)`

## Content extraction from specific domains

### sportpaedia.com
Full match details embedded in page HTML (not JS-rendered). Grep for final score/champion info:
```bash
curl -sL "https://www.sportpaedia.com/world-cup-2026-knockout-stage/" | grep -oP 'Spain beat Argentina[^<]+'
```

### worldtopnewsnow.com
Article content in HTML, not JS-rendered. Use `sed` to strip tags.

### theguardian.com
JS-heavy — curl gets CSS/JS config bloat. Search for topic headlines via grep:
```bash
curl -sL "URL" | grep -oP '>[^<]{10,200}</a>' | grep -i "AI\|topic"
```

## Rate limit survival

- Space ddgs calls 3-5s apart, max 2-3 per run
- English queries (`world news today`) less rate-limited than Vietnamese
- News endpoint (Yahoo) fragile: fall back to `ddgs text -q "topic tin mới"` when news fails
- When ALL ddgs queries return empty: use `web_search` tool (Firecrawl/Tavily backend) as primary fallback
- `execute_code` blocked in cron mode — use `terminal` tool directly
- Sequence calls: news first (most fragile), then text, then web_search

## Output format

```
☀️ ĐIỂM TIN SÁNG — Thứ X, ngày/tháng/2026

🌤 THỜI TIẾT HÔM NAY
• ...

🇻🇳 TIN VIỆT NAM
• ...

🌍 THẾ GIỚI
• ...

⚡ CÔNG NGHỆ
• ...

🏆 THỂ THAO
• ...

💬 "Câu nói hay trong ngày"
Chúc Anh Đạt một ngày tốt lành! ☕
```

## Day of week in Vietnamese

- Monday=Thứ Hai, Tuesday=Thứ Ba, Wednesday=Thứ Tư, Thursday=Thứ Năm, Friday=Thứ Sáu, Saturday=Thứ Bảy, Sunday=Chủ Nhật

## Cron notes

- No user present — must be fully autonomous
- No `execute_code` — use `terminal` tool only
- DELIVERY is automatic via final response — do NOT use send_message
- `[SILENT]` output suppresses delivery when nothing new
- Write `briefing_bank.json` state file after each run to avoid duplicate news
