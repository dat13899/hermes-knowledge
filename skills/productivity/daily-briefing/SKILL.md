---
name: daily-briefing
description: "Generate morning briefing in Vietnamese — weather, news, tech, sports. Cron job pattern with BRIEFING.md config."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [briefing, cron, vietnamese, news, weather, daily]
    related_skills: [duckduckgo-search]
---

# Daily Briefing (Điểm tin sáng)

Generate morning briefing in Vietnamese. Cron job pattern. Reads `BRIEFING.md` for config.

## Config File

Path: `$HERMES_HOME/BRIEFING.md` (e.g. `C:\Users\datel\AppData\Local\hermes\BRIEFING.md`)

Sections:
- **Delivery:** time, channel
- **Human Context:** name, location, language
- **Sections:** weather (yes/no), calendar, tasks, pending, news, quote
- **News Topics:** what to search for
- **Tone:** style guide (emoji per section, short, closing quote)
- **Weekend Mode:** different send time

## Weather via Open-Meteo (Free, No Key)

Open-Meteo is free, no API key. Use for Hanoi (21.02, 105.85):

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=21.02&longitude=105.85&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia%2FBangkok" | python -c "
import sys,json; d=json.load(sys.stdin); c=d['current_weather']; dly=d['daily']
print(f\"Nhiệt độ hiện tại: {c['temperature']}°C, Gió: {c['windspeed']} km/h, Mã thời tiết: {c['weathercode']}\")
print(f\"Cao nhất: {dly['temperature_2m_max'][0]}°C, Thấp nhất: {dly['temperature_2m_min'][0]}°C\")
"
```

Weather codes: 0=clear, 1=mainly clear, 2=partly cloudy, 3=overcast, 45=fog, 48=depositing rime fog, 51=light drizzle, 61=slight rain, 71=slight snow, 95=thunderstorm.

## News Gathering (Fallback Chain)

ddgs CLI often blocked from cloud IPs. Use this fallback chain:

1. `ddgs news -q "query" -m N -o json` — try first
2. If empty → `web_search(query, limit=N)` — built-in tool
3. For structured content → Wikipedia API: `curl -sL "https://en.wikipedia.org/w/api.php?action=query&titles=PAGE&prop=extracts&explaintext=1&format=json"`
4. For Vietnamese news → RSS feeds: `vnexpress.net/rss/thoi-su.rss`, `thanhnien.vn/`

## Format Template

```
☀️ **ĐIỂM TIN SÁNG — Thứ X, ngày/tháng/2026**

🌤 **THỜI TIẾT HÔM NAY**
• ...

🇻🇳 **TIN VIỆT NAM**
• ...

🌍 **THẾ GIỚI**
• ...

⚡ **CÔNG NGHỆ**
• ...

🏆 **THỂ THAO**
• ...

💬 **"Quote"** — Author

Chúc {name} một ngày tốt lành! ☕
```

## Cron Job Delivery

- Final response auto-delivered by cron system
- If nothing new to report, respond with exactly `[SILENT]` (nothing else)
- Never combine `[SILENT]` with content

## Pitfalls

- **ddgs often blocked from cloud IPs** — returns empty results silently. Fall back to `web_search` immediately.
- **web_extract may not work** if backend is ddgs-only. Use curl + Wikipedia API or RSS feeds for structured content.
- **VnExpress uses JS rendering** — RSS feed (`vnexpress.net/rss/thoi-su.rss`) works for headlines.
- **Weather code 3** = overcast. Map codes: 0=clear, 1=mainly clear, 2=partly cloudy, 3=overcast, 45=fog, 51=drizzle, 61=rain, 71=snow, 95=thunderstorm.
- **Today's date** comes from conversation start time, not system clock.
- **Cron delivery** is automatic — do NOT use send_message. Final response is the delivery.
- **SILENT** when nothing new — exact string `[SILENT]`, nothing else.
