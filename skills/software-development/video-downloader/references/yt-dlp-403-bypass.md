# YouTube 403 Forbidden — Debugging & Bypass (video-downloader skill)

## Symptom

```
ERROR: unable to download video data: HTTP Error 403: Forbidden
```

Can fire on:
- `--dump-json --no-download` (metadata extraction)
- Actual download
- One specific video URL but not another
- All YouTube URLs after a burst of requests

## Root causes

| Cause | Trigger | Fix |
|---|---|---|
| Missing/old User-Agent | YouTube now rejects bare python-requests/yt-dlp UA | Inject browser UA globally |
| Rate limiting | Too many requests from same IP in short window | Add `--sleep-requests 1` + rotate IP/use cookies |
| Geo-blocked content | Video restricted to specific country | Use `--geo-bypass` + proxy |
| Expired stream URL | Long time between metadata fetch and download | Download within same session, reduce delay |
| Age-restricted video | YouTube login required | Use `--cookies-from-browser` or cookies.txt |

## Primary fix: User-Agent header

**Always** add this to every yt-dlp invocation — metadata AND download:

```python
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

# In the subprocess args list:
args = [
    sys.executable, "-m", "yt_dlp",
    "--no-warnings",
    "--user-agent", UA,
    # ... rest of args
]
```

**Pitfall**: applying UA only to download but not to `--dump-json` — both stages make HTTP requests and can get 403 independently.

## Secondary fix: cookies

When UA header alone isn't enough (age-restricted, private videos, or persistent rate-limiting):

```bash
# Export cookies via browser extension "Get cookies.txt LOCALLY"
# Save to C:\Users\datel\cookies.txt
python -m yt_dlp --cookies C:\Users\datel\cookies.txt <URL>

# Or use browser cookies directly:
python -m yt_dlp --cookies-from-browser chrome <URL>
python -m yt_dlp --cookies-from-browser firefox <URL>
```

## Rate-limit avoidance

```python
args += ["--sleep-requests", "1.0"]  # 1s between API calls
```

When processing multiple videos in sequence, insert a delay between calls to `yt-dlp --dump-json`:

```python
import time
for url in urls:
    data = ytdlp(["--dump-json", ...])
    time.sleep(2)  # avoid burst
```

## Testing 403 fix

```bash
# Quick test — download a known-good public video:
python -m yt_dlp --no-warnings --user-agent "..." \
  -f "best[height<=720]" \
  -o "%(title)s.%(ext)s" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

If this works but a larger download failed, the 403 was format/stream-specific (not a global block).

## History

Encountered 2026-07-11 during dlv_tg.py development. All YouTube calls started returning 403 after several test downloads. Adding `--user-agent` to both `--dump-json` and download calls resolved immediately. Root cause: yt-dlp's default UA was being rejected by YouTube's frontend.
