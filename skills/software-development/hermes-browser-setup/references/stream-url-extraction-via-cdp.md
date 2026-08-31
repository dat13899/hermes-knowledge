# Stream URL Extraction via CDP Performance API

Extract live HLS/DASH stream URLs from dynamic SPA websites (React, Vue, etc.) where the stream URL is loaded at runtime via JavaScript and not present in the static HTML.

## When To Use

- yt-dlp / curl can't find the stream (SPA-based live streaming sites)
- The video element uses a `blob:` URL (MSE playback)
- Age/R18 gate blocks navigation
- Stream URL is loaded dynamically via XHR/fetch

## Workflow

### 1. Launch Chrome with CDP

Kill all Chrome instances, then start a fresh headed Chrome with remote debugging:

```bash
taskkill /F /IM chrome.exe
sleep 2
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/<user>/chrome-debug" \
  --no-first-run --no-default-browser-check
```

Verify: `curl -s http://localhost:9222/json/version`

### 2. Navigate to the page

Use `browser_navigate(url)` — this creates a page target. If the page has an age gate, handle it:

```javascript
// CDP eval on the target tab
document.querySelector('.r18-entry, .age-gate-entry, .confirm-18').click()
```

Or use local storage bypass if available:
```javascript
localStorage.setItem('r18', '1')
```

### 3. Wait for the page to fully render the player

SPAs load asynchronously. Wait 5-10 seconds for the player to initialize and start fetching the stream.

### 4. Extract stream URL via Performance API

Query all network resources from the Performance API, filtering for HLS/DASH streams:

```javascript
performance.getEntriesByType('resource')
  .filter(e => e.name.includes('.m3u8') || e.name.includes('.mpd'))
  .map(e => ({url: e.name, duration: e.duration}))
```

The m3u8 URL typically appears as an `xmlhttprequest` entry type.

### 5. Verify

Download the m3u8 playlist to confirm it's live:

```bash
curl -sL -H "Referer: https://the-site.com/" "https://cdn.example.com/stream.m3u8?token=..."
```

Should return a valid `#EXTM3U` header with `#EXT-X-MEDIA-SEQUENCE` and segment URIs.

## Common API Patterns

SPA live streaming sites often expose REST endpoints for room/stream metadata:

| Pattern | Endpoint |
|---------|----------|
| Room info | `GET /api/live/room-info?roomId=X` or `POST /api/room/token` |
| Stream token | `POST /api/live/get-token` with `{aid, roomId}` |
| CDN pattern | `https://<cdn>.com/live/<streamId>.m3u8?expire=<ts>&sign=<hash>` |

Look for these in the Performance API entries to find the API base URL (often a different domain like `api.example.com` or `cdn-api.example.com`).

## Pitfalls

- **Expiring links**: m3u8 URLs often have `expire` timestamps. The link is only valid for a limited window (often 10-30 minutes). Refreshing requires re-extracting.
- **Referer header**: Some CDNs require a `Referer: https://the-site.com/` header. Add it to curl/ffplay commands.
- **Token auth**: Some streams need a session token fetched from a separate API endpoint before the m3u8 URL works.
- **Performance API truncation**: `performance.getEntriesByType('resource')` returns only entries up to `performance.maxResourceTimingBufferSize` (default 250-500). For long-lived streams, extract early.
- **Blob URLs**: The video element's `src` will be `blob:https://...` when using MSE (MediaSource Extensions). The real m3u8 URL is never in the DOM — only via network intercept or Performance API.
- **CSP restrictions**: Some sites block `fetch()` calls from CDP eval. Use Performance API instead (it's read-only, no CSP impact).
