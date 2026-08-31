---
name: video-downloader
description: Build CLI/web tools to download videos from YouTube/TikTok/Instagram/700+ sites using yt-dlp. Covers installation, invocation, format extraction, playback, audio streaming, and web interface patterns.
tags:
  - yt-dlp
  - video-download
  - youtube-dl
  - media
  - python
  - audio-streaming
---

# Video Downloader (yt-dlp)

Build tools to download videos from any platform using yt-dlp, and stream YouTube audio to browser.

## Installation

```bash
uv pip install yt-dlp
```

Do NOT use `pip install` or `pip3` — Anh Đạt's env uses `uv`.

### Subprocess timeout

yt-dlp can be slow, especially for long videos or first runs (downloading extractor cache).

| Scenario | Recommended timeout |
|---|---|
| Metadata extraction (`--dump-json --no-download`) | 120s |
| Short video download (<10 min) | 300s |
| Long video download (>10 min, >500 MB) | 600s+ |

```python
subprocess.run(..., timeout=600)  # long video safe
```

### `--force-overwrites`

When re-downloading a URL that already has a file in the output directory, yt-dlp **skips** by default. If the format changed but the URL didn't, the stale cached file is returned — causing confusion ("why is my 1080p download still 360p?").

Always add `--force-overwrites` when:
- The user might request the same URL twice with different format settings
- You're iterating on format selection
- The output directory accumulates files across sessions

```python
args += ["--force-overwrites"]
```

Same pattern for every subprocess call (`run_ytdlp`, `download`, etc.).

## Data extraction

### YouTube Search (ytsearch)

Use yt-dlp to search YouTube for random/discovery features (not just known-URL extraction).

```bash
yt-dlp --dump-json --no-warnings --default-search "ytsearch" "search query"
```

Returns full JSON metadata. First result: `out.split('\n').filter(Boolean)[0]`.

#### Correct `--default-search` syntax

```
# ✅ CORRECT
--default-search "ytsearch" "query"

# ❌ WRONG — ytsearch1: etc. go INTO the URL arg, not --default-search
--default-search "ytsearch1:${q}" "${q}"
```

`--default-search` sets the search **prefix** (e.g. `ytsearch`). The query is the next argument. Embedding `1:` or the query inside `--default-search` double-prefixes the search → intermittent failures.

#### Reliability pattern (API endpoints)

yt-dlp search is unreliable due to YouTube rate-limiting. Always layer fallback:

```javascript
// 1. Try live fetch
let video = null;
try {
  const out = execSync(`yt-dlp --dump-json --no-warnings --default-search "ytsearch" "${keyword}"`,
    { timeout: 15000, maxBuffer: 512 * 1024, encoding: 'utf8', windowsHide: true });
  const v = JSON.parse(out.split('\n').filter(Boolean)[0]);
  if (v && v.id) { video = {...}; CACHE.push(video); }
} catch (_) { /* fall through */ }

// 2. Fall back to cache → built-in pool
if (!video) {
  const pool = CACHE.length ? CACHE : FALLBACK_POOL;
  const f = pool[Math.floor(Math.random() * pool.length)];
  video = { title: f.title, url: 'https://youtube.com/watch?v=' + f.id, ... };
}
```

Key parameters:
- **Timeout**: 15s minimum (search is slower than direct-URL extraction)
- **Fallback pool**: Pre-populated array of ~16 well-known video IDs + titles
- **Cache**: In-memory array; used when yt-dlp fails next time
- **Keywords**: Rotate through ~15 diverse terms per invocation

### Single video metadata + formats

```python
result = subprocess.run(
    [sys.executable, "-m", "yt_dlp", "--no-warnings",
     "--dump-json", "--no-download", "--no-playlist", url],
    capture_output=True, text=True, timeout=120
)
data = json.loads(result.stdout)
# data["title"], data["uploader"], data["formats"][...]
```

`formats` entries have: `format_id`, `format_note` / `quality` / `label`, `ext`, `filesize` / `filesize_approx`, `vcodec`, `acodec`, `url`.

### Channel / playlist listing

```python
result = subprocess.run(
    [sys.executable, "-m", "yt_dlp", "--no-warnings",
     "--dump-json", "--flat-playlist", url],
    capture_output=True, text=True, timeout=120
)
items = [json.loads(l) for l in result.stdout.strip().split("\n") if l]
# items[0]["title"], items[0]["original_url"] or items[0]["webpage_url"]
```

`--flat-playlist` suppresses per-video format extraction (faster).
`--no-playlist` ensures single-video mode (other direction).

### Download (save file)

```python
result = subprocess.run(
    [sys.executable, "-m", "yt_dlp",
     "-o", "%(title).100s.%(ext)s",  # clip long titles
     "--no-playlist", "--no-warnings",
     "-f", format_id_or_best, url],
    capture_output=True, text=True, timeout=300
)
```

For audio-only: use `-x --audio-format mp3` instead of `-f`.
For best mp4: `-f "best[ext=mp4]/best"`.

## HTTP 403 / YouTube blocking

YouTube sometimes returns `HTTP Error 403: Forbidden` for programmatic requests. Fix: inject a browser User-Agent header globally.

```python
# In every yt-dlp call:
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
subprocess.run(["python", "-m", "yt_dlp", "--user-agent", UA, ...], ...)
```

Apply to `--dump-json` AND download calls — the 403 can fire at both stages.

**Pitfall**: without `--user-agent`, all subsequent calls to the same host may keep failing. The header must be on EVERY invocation. Do NOT omit for metadata-only calls — the 403 is per-request, not per-download.

## Extractor cookies for private / logged-in content

Some platforms (Instagram) require authentication for certain content:

| Scenario | Fix |
|---|---|
| Instagram private video | Export cookies.txt via browser extension → pass `--cookies cookies.txt` |
| YouTube age-restricted | Use `--cookies-from-browser firefox` or export cookies |
| Daily rate-limit bypass | `--sleep-requests 1.0` between API calls |

On this machine, cookies.txt lives at `C:\Users\datel\cookies.txt` when set up.

## Windows-specific pitfalls

| Pitfall | Fix |
|---|---|
| `yt-dlp` not in PATH | `sys.executable -m yt_dlp` |
| `python3` opens MS Store | Use `python` (not `python3`) |
| subprocess `text_timeout` typo | Use `text=True, timeout=N` separately |
| `python3` piped commands | Replace `python3 -c "..."` with `python -c "..."` |
| yt-dlp first-call slow (~15s) | First run downloads extractor cache; subsequent calls are faster |

## Audio streaming (pipe to browser)

Stream bestaudio as HTTP response so client `<audio>` element plays YouTube audio without downloading. Works on mobile with screen off (standard `<audio>` behaviour — no special work needed).

### Metadata endpoint (Node.js)

```javascript
GET /api/utilities/youtube-audio?url=...
// Returns JSON: {title, thumbnail, duration, uploader}
// Uses: execSync(`yt-dlp --dump-json --no-warnings "${url}"`, {timeout:15000})
```

### Audio stream endpoint (Node.js)

```javascript
GET /api/utilities/youtube-audio/stream?url=...
const child = spawn('yt-dlp', ['-f', 'bestaudio', '-o', '-', '--no-warnings', url]);
res.writeHead(200, { 'Content-Type': 'audio/webm', 'Cache-Control': 'no-cache' });
child.stdout.pipe(res);
// Kill child when client disconnects:
req.on('close', () => { try { child.kill(); } catch (_) {} });
```

**Key details:**
- `-f bestaudio -o -` → pipe audio to stdout, no file written
- Content-Type `audio/webm` — works with `<audio>` in all browsers
- `req.on('close')` kills the yt-dlp process when user navigates away
- Client `<audio controls autoplay>` handles play/pause natively

### Stream lifecycle management

```javascript
let _activeStream = null;

// On new stream request — kill previous first:
if (_activeStream) { try { _activeStream.child.kill(); } catch (_) {} }
_activeStream = { url, child, req };
res.writeHead(200, { 'Content-Type': 'audio/webm' });
child.stdout.pipe(res);

// Client disconnect cleanup:
req.on('close', () => {
  try { child.kill(); if (_activeStream && _activeStream.child === child) _activeStream = null; } catch (_) {}
});

// Explicit kill endpoint (for timer or manual stop):
// POST /api/utilities/youtube-audio/stop
if (_activeStream) {
  try { _activeStream.child.kill(); _activeStream.req.destroy(); } catch (_) {}
  _activeStream = null;
  return { ok: true };
}
```

### Timer (auto-stop)

Frontend `setTimeout` → `fetch('/api/utilities/youtube-audio/stop', {method:'POST'})` → kills yt-dlp process + clears audio source. Covers CPU/network usage completely.

Timer buttons: 3p/5p/10p/30p. **5p mặc định** (user preference, đã đổi từ 20p).

### Important: kill stream BEFORE setting new audio src

```javascript
// Right pattern:
await killStream();  // POST /api/.../stop first
a.src = '/api/utilities/youtube-audio/stream?url=' + encodeURIComponent(url);
a.play();

// Without killStream(), old yt-dlp keeps running + new one starts → 2 processes
```

## Web server pattern

Simple HTTP server with two endpoints:

- `POST /api/info` — extract metadata + formats
- `GET /api/dl` — trigger download (proxy via yt-dlp or redirect to file)

Keep the HTML page inline as a Python string (single-file deploy). Use `SimpleHTTPRequestHandler` from stdlib — no Flask/fastapi needed for a small tool.

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self): ...
    def do_POST(self): ...
    def _json(self, obj): ...

HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
```

Run with `background=True` in terminal for testing. Start, test with curl, kill when done.

## Format selection — use yt-dlp sorting (`-S`)

**DO NOT** manually parse format lists and pick. Use yt-dlp's built-in `-S` (format sort) — it's more reliable and handles codec/height/bitrate tradeoffs correctly.

### Best quality 1080p H264 mp4 (RECOMMENDED)

```python
args = [
    "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "-S", "codec:h264,ext:mp4",
    "--merge-output-format", "mp4",
    "--force-overwrites",
    url
]
```

`-S "res:1080..."` was **removed** because yt-dlp interprets `res:1080` as "closest to 1080" — if 1440p exists, it picks 1440p instead. The `[height<=1080]` filter enforces the cap strictly.

Sort chain: prefer h264 codec, then mp4 extension. `bestvideo+bestaudio` merges video+audio streams; fallback to `best` single format.

### CRITICAL PITFALL: avoid `best[height<=N][ext=mp4]`

```python
# ❌ WRONG — selects single combined format only
# On YouTube the only single mp4 format below 1080p is format 18 (360p!)
"-f", "best[height<=1080][ext=mp4]/best"

# ✅ RIGHT — use bestvideo+bestaudio with format sort
"-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
"-S", "codec:h264,ext:mp4",
```

The single-format shortcut silently downloads 360p while reporting "1080p" (from the metadata scan).

### Format sort flags for different goals

| Goal | `-S` value |
|---|---|
| Best quality 1080p | `res:1080,codec:h264,ext:mp4` |
| Highest resolution possible | `res,codec:h264` |
| Smallest file | `+size,+br` |
| Best quality under size limit | Use `-f "bestvideo[filesize<N]+bestaudio/best[filesize<N]"` **without** manual picking |

### Legacy manual pick (fallback only)

Use when you already have the JSON metadata and need to decide before calling yt-dlp again:

```python
PREFERRED = [2160, 1440, 1080, 720, 480, 360, 240, 144]

def height_val(fmt):
    n = fmt.get("format_note") or fmt.get("quality") or ""
    if n.endswith("p"):
        try: return int(n[:-1])
        except: pass
    return fmt.get("height") or 0

def pick_best_format(formats):
    vids = [f for f in formats 
            if f.get("vcodec") and f.get("vcodec") != "none"
            and (f.get("filesize") or f.get("filesize_approx") or 0) > 0]
    if not vids: return None
    def sort_key(f):
        h = height_val(f)
        idx = next((i for i, ph in enumerate(PREFERRED) if ph <= h), len(PREFERRED))
        return (idx, 0 if f.get("ext") == "mp4" else 1, f.get("filesize") or 0)
    vids.sort(key=sort_key)
    return vids[0]
```

## Safe file serving

When serving downloaded files through the web server:

```python
# After download, get path via --print after_move:filepath
result = subprocess.run(..., capture_output=True, text=True)
fpath = result.stdout.strip().split("\n")[-1]

# Serve with Content-Disposition: attachment
self.send_response(200)
self.send_header("Content-Type", "application/octet-stream")
self.send_header("Content-Disposition", f'attachment; filename="{basename}"')
with open(fpath, "rb") as f:
    self.wfile.write(f.read())
```

🚨 For large files (≥500 MB) use chunked reading — `f.read()` loads entire file into memory.

## File size at download time

YouTube format metadata `filesize` / `filesize_approx` in `--dump-json` output is **estimated and often wrong** — actual downloaded file can be very different. Do not trust estimated size to make format decisions; only check real size after download.

## Post-download delivery

After download, check file size against Telegram limits:

| File size | Delivery method |
|---|---|
| < 48 MB | `MEDIA:/path/to/file` — agent includes in response, Telegram delivers inline video |
| > 50 MB | Compress with FFmpeg (see below) to try to fit under 48 MB. If still > 48 MB after compression, save to `C:\Users\datel\Downloads\dlv\` and report path. User transfers via **Telegram Desktop → Saved Messages** (native 2 GB limit, not Bot API 50 MB limit) |
| Upload hosts | **All failed** from this env (blocked/rate-limited/auth-required). See `references/telegram-delivery.md`. |

### User quality preference (Anh Đạt)

Priority order: **1080p → 720p → 480p → 360p → 240p → 144p**.

Do NOT pick smallest format automatically. Use format sort:
```python
# Current best (2026-07-11):
"-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
"-S", "codec:h264,ext:mp4",
```

`-S "res:1080,codec:h264,ext:mp4"` was **removed** because yt-dlp interprets `res:1080` as "closest to 1080" — if 1440p exists, it picks 1440p instead. The `[height<=1080]` filter enforces the cap strictly.

File size is secondary — user prefers quality over compression. The only hard cap is Telegram's 50 MB Bot API limit; files above that are compressed automatically, then saved to disk if still too large.

### File naming

Files save to `C:\Users\datel\Downloads\dlv\` with sanitized title. Strip Windows-illegal characters:
```python
safe = re.sub(r'[<>:"/\\|?*]', '_', title)
output = os.path.join(DOWNLOAD_DIR, f"{safe}.%(ext)s")
```

## Post-download compression via FFmpeg (telegram-cap)

When a downloaded file exceeds Telegram's 50 MB Bot API limit, compress it automatically with FFmpeg to try to fit under 48 MB.

### HW encoder detection (Windows)

This Windows machine has `h264_mf` (MediaFoundation — Windows built-in hardware encoder). It runs ~20x realtime. NVENC and AMF encoders are present in the `ffmpeg` binary but **FAIL** on this machine — do NOT attempt them.

Detection logic:
```python
r = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=10)
if "h264_mf" in r.stdout:
    enc = "h264_mf"  # Windows HW — use bitrate-based encoding
elif "h264_nvenc" in r.stdout:
    enc = "h264_nvenc"  # DO NOT use on this machine — fails with -22
elif "h264_amf" in r.stdout:
    enc = "h264_amf"  # DO NOT use — quality param range is -1..2 (not 0-51)
else:
    enc = "libx264"  # CPU fallback — use CRF-based
```

### MediaFoundation (h264_mf) — bitrate-based

`h264_mf` does NOT support CRF/CQ quality parameters — it uses **target bitrate** only.

```python
target_kbps = max(200, int(ENCODED_TARGET_BYTES * 8 / duration_seconds * 0.9 / 1000))

subprocess.run([
    "ffmpeg", "-y", "-i", input_file,
    "-c:v", "h264_mf", "-b:v", f"{target_kbps}k",
    "-c:a", "aac", "-b:a", "96k",
    "-movflags", "+faststart", "-f", "mp4", output_file
], timeout=600)
```

If still > 48 MB after first pass, halve bitrate + downscale to 720p.

### libx264 (CPU) — CRF-based escalation

```python
for crf in [23, 28, 32, 36, 40, 45]:
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", "libx264", "-crf", str(crf),
        "-preset", "veryfast",  # MUCH faster than medium
        "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart", "-f", "mp4", output_file
    ], timeout=600)
```

`-preset veryfast` is critical — `medium` takes 10-30x longer for negligible quality gain on Telegram-size files.

### Resolution downscale fallback

When CRF/CQ maxed and still > 48 MB:

```python
for crf, res in [(30, 720), (35, 720), (30, 480), (35, 480), (35, 360)]:
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", "libx264", "-crf", str(crf),
        "-vf", f"scale=-2:{res}",
        "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart", "-f", "mp4", output_file
    ], timeout=600)
```

### When compression is NOT worth it

- Video already < 48 MB → skip compression entirely
- Duration > 30 min at 1080p → file likely > 500 MB → takes very long to compress → fall back to disk save
- User wants maximum quality → respect `crf >= 23` ceiling and let it fail to disk

### Command reference at `C:\Users\datel\dlv`

| File | Purpose |
|---|---|
| `dlv_tg.py` | Main download+compress+send script. Embeds all compression logic above |
| `dlv.py` | Web server (port 5502) + CLI, no compression |

## References

| File | Content |
|---|---|
| `references/gendownload-analysis.md` | Reverse-engineering of gendownload.com web video downloader (stream proxy, API shape, client-side flow) |
| `references/telegram-delivery.md` | Telegram delivery patterns: MEDIA: convention, upload host status, format picking, Telegram Desktop fallback |
| `references/ffmpeg-compression.md` | FFmpeg command reference, HW encoder matrix, libx264 preset guide, real-world compression scenarios |
| `references/yt-dlp-403-bypass.md` | YouTube 403 Forbidden debugging: user-agent fix, cookies, rate-limiting |
| `references/youtube-audio-player-ui.md` | YouTube Audio Player utility page — full UI pattern, lifecycle mgmt, timer, glass CSS |

## Authoring note

This skill exists because Anh Đạt (user) needed a tool to download videos from YouTube/TikTok/Instagram and view them on his phone. Key sessions that shaped this skill:

- **2026-07-10**: Initial creation and refinement. Discovered format sort pitfalls. Established Telegram delivery workflow. Fixed Windows-specific subprocess patterns.
- **2026-07-11**: Added FFmpeg compression integration. Discovered `h264_mf` (MediaFoundation) as only working HW encoder on this machine (NVENC/AMF fail). Added automatic post-download compression with CRF escalation and resolution downscale fallback. Changed format selection from `-S "res:1080,..."` to `[height<=1080]` filter + `-S "codec:h264,ext:mp4"` because `res:1080` picks 1440p when available.
- **2026-07-23**: Added audio streaming via yt-dlp `-f bestaudio -o -` piped to HTTP. Added stream lifecycle management (kill on disconnect, kill on new request, explicit stop endpoint). Added timer auto-stop. Timer defaults to **5p** (user preference — buttons: 3p/5p/10p/30p, đã đổi từ 20p). Patterns for YouTube Audio Player utility at `/utilities`.
- **2026-07-24**: Added YouTube Search (ytsearch) section. Fixed `--default-search` syntax (was `"ytsearch1:${q}"` → `"ytsearch"`). Documented reliability pattern: fallback pool + cache when yt-dlp fails for random discovery endpoint.
