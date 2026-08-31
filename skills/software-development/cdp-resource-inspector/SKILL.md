---
name: cdp-resource-inspector
description: "Extract stream URLs from JS SPAs via CDP ResourceTiming."
tags:
  - cdp
  - network
  - hls
  - stream-extraction
  - performance-api
  - browser-automation
---

# CDP Resource Inspector

Extract dynamically-loaded resources (HLS streams, API endpoints, media URLs)
from web pages using Chrome DevTools Protocol (CDP). The key technique is
reading the browser's **Resource Timing API** — `performance.getEntriesByType('resource')`
— which captures every HTTP request the page makes, including ones not visible
in the DOM.

## When To Use

- A page loads a video/audio player but the stream URL is hidden in a `blob:` MediaSource
- You need to find API endpoints called by a React/Vue SPA
- You want to monitor what resources load after user interaction
- The page is a single-page app where static HTML analysis yields nothing

## Core Technique

### Pitfalls & Field Notes

**Performance buffer clears on reload.** `performance.getEntriesByType('resource')` is a snapshot of the current page lifetime. Calling `Page.reload` or navigating away RESETS the buffer. Always capture entries **before** any reload. If you need a fresh page state, use `Page.navigate` to a clean URL — do NOT use `Page.reload`.

**Memory/performance API self-clears.** On long-lived SPA pages, the browser may evict old entries from the Resource Timing buffer. Poll within 10–15s of navigation. For streams that start later (e.g. after a paywall timer), check every 2s with a `setInterval`-backed Promise.

**Paywall/subscribe overlay blocks stream requests.** On gated content (private rooms, subscriber-only streams), the page may never fetch CDN URLs — it only shows a subscribe dialog. The Resource Timing API will have zero media entries. Check `document.body.innerText` for gate messages (e.g. "Đăng ký để tiếp tục xem"). Fall back to:
- Room-info / stream-info API endpoints (often unauthenticated via curl)
- Scanning `localStorage` for Vuex/Pinia state: `JSON.parse(localStorage.getItem('vuex'))` often contains stream config
- Token/auth APIs (may need auth headers or `atr`/`wsu` values from room-info)

**`blob:` video.src means MSE (MediaSource Extensions).** When `video.src` is a `blob:` URL, the page feeds video through MediaSource — the actual `.m3u8`/`.mpd` URL is invisible in the DOM. Only Resource Timing or network-level interception reveals it.

**CDP evaluate with promises may return `{}`.** `Runtime.evaluate` with `awaitPromise: true` and `.then()` chains sometimes serializes as empty `{}`. Prefer synchronous expressions or IIFEs that return values directly. Polling with plain `Runtime.evaluate` (no promise) works reliably.

**Service Workers can intercept streaming requests.** If a page has a registered Service Worker (check `Target.getTargets` for `type: "service_worker"`), it may modify or cache streaming URLs before they reach the page's fetch/XHR handlers. Your injected fetch-interception scripts may not fire. Use CDP network-level capture or Resource Timing as the primary extraction path.

**Auth token patterns from room-info APIs.** Some live platforms return auth values in the room-info response:
- `atr`: base64-encoded auth token (sends as 401 Unauthorized if used as Bearer — needs specific header or cookie format)
- `wsu`: base64-encoded watermark secret/key
- `secret: true` field = private/subscriber-only room; `_DQSK` suffix in URL = server-side blurred variant

### 1. Navigate & Wait

```
Page.navigate({ url: targetUrl });
// Wait for page to fully render and player to initialize
// Typical delay: 5–8 seconds for media-heavy SPAs, 10–12s for live streams
await new Promise(r => setTimeout(r, 10000));
```

### 2. Query Resource Timing

```
Runtime.evaluate({
  expression: `performance.getEntriesByType('resource')
    .filter(e => e.name.includes('{cdn-pattern}'))
    .map(e => ({ url: e.name, type: e.initiatorType, duration: e.duration }))`,
  returnByValue: true,
  target_id: tabId
});
```

### 3. Filter & Extract

Filter for known resource patterns:
- `.m3u8`, `.m3u` — HLS playlists
- `.mpd` — MPEG-DASH manifests
- `.ts`, `.m4s`, `.m4v` — media segments
- `.flv` — FLV streams
- `cdn` — CDN hostnames
- `live`, `stream`, `play` — common stream path segments
- `cdnsi` — ByteDance/VolcEngine live CDN

### Filtering out tracking / internal params

When filtering m3u8 URLs, exclude entries that contain `_HLS_msn` or `_HLS_part` — these are LL-HLS (Low-Latency) tracking parameters for partial segments, not the base playlist. Pick the first entry with `?expire=` and no `_HLS_msn`.

The first entry matching the stream manifest pattern is usually the base URL.

## Verification

```
curl -sL -H "Referer: <original-page-domain>" "$MANIFEST_URL" | head -5
```

Should return a valid playlist starting with `#EXTM3U` (HLS) or `<?xml` (DASH).

## Pitfalls

- **Link expiry**: Many live streams embed an `expire` Unix timestamp in the URL.
  Links typically last 10–15 minutes. Re-navigate to get a fresh URL.
- **CORS**: The `performance` API only captures resources loaded by the page.
  Scripts blocked by CORS won't appear.
- **R18/Gate pages**: Some sites show an age gate overlay. Click it first or
  set a localStorage flag (e.g. `localStorage.setItem('r18', '1')`).
- **Player warmup**: Some players pre-buffer before fetching the manifest. Wait
  longer (10–12s) if no entries appear at 8s.

## Real-World Example

See `references/hls-live-stream-extraction.md` for a complete worked example
extracting HLS streams from Chinese live-streaming SPA (yy-live.top),
including CDN patterns, link expiry handling, and verification steps.
