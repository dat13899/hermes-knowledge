# Gendownload.com — Reverse Engineering Notes

Source: https://gendownload.com/video-downloader
Analyzed: 2026-07-10

## Architecture

**Client-side frontend** — the page is a thin UI wrapper. All heavy lifting happens server-side.

## API Endpoints

### `POST /api/extract`

Extract video info + available formats from a single video URL.

**Request:**
```json
{"url": "https://www.youtube.com/watch?v=..."}
```

**Response:**
```json
{
  "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "duration": 213,
  "source": "youtube",
  "author": "Rick Astley",
  "views": 1791122503,
  "likes": 19237835,
  "formats": [
    {"label": "2160p", "type": "video", "ext": "mp4", "filesize": 362057908,
     "url": "https://gendownload.com/api/stream?t=7611333ea9915c0173b3ef32&i=0"},
    ...
    {"label": "Audio", "type": "audio", "ext": "mp3", "filesize": null,
     "url": "https://gendownload.com/api/stream?t=7611333ea9915c0173b3ef32&i=8"}
  ]
}
```

- Server validates URL, runs extraction (likely yt-dlp `--dump-json`)
- Generates a signed token `t=` per request
- All download URLs route through `/api/stream` with token — never exposes CDN origin directly

### `POST /api/channel`

List items from a channel/playlist URL.

**Request:**
```json
{"url": "https://www.youtube.com/...", "limit": 50, "filter": "all"}
```

**Response:**
```json
{
  "items": [
    {"url": "...", "title": "...", "thumbnail": "..."},
    ...
  ]
}
```

### `GET /api/stream?t=<token>&i=<index>`

Proxy endpoint for actual video download:
- Validates token → looks up cached source URL → streams from source CDN → client
- No file stored on server — stream-through proxy
- Token-based: prevents direct CDN access and hotlinking

## Client-side download trigger

The page renders each format as a `<a>` tag. Two behaviors based on URL pattern:

```javascript
var inPlace = f.url.indexOf('/api/stream') >= 0 || f.url.indexOf('dl=1') >= 0;
var attrs = inPlace ? 'download' : 'target="_blank" rel="noopener nofollow"';
```

- `/api/stream` URLs: `download` attribute → in-page download (stream starts, browser saves)
- CDN URLs: `target="_blank"` → open new tab (for cross-origin CDN links from Twitter/Douyin)

## Likely backend toolkit

The pattern matches **yt-dlp** exactly:
- `--dump-json` output shape (title, formats array with label/filesize/ext, source, duration, views/likes)
- `--flat-playlist` for channel listing
- Format labels use yt-dlp's `format_note` (e.g., "1080p", "720p")
- "source" field = yt-dlp's extractor key (youtube, tiktok, instagram)

Server stack: Python backend (Flask/FastAPI/similar) wrapping yt-dlp, with a signed-token cache layer for stream URLs.

## Comparison with dlv

| Feature | Gendownload | dlv (our tool) |
|---|---|---|
| Output | Web UI + stream proxy | CLI + web UI |
| Download mechanism | Server proxy `/api/stream` | Direct yt-dlp download |
| File storage | None (stream-through) | Local disk |
| Auth | None | None |
| Delivery | Web download | Telegram MEDIA + disk save |
| yt-dlp | Server-side | Local invocation |
