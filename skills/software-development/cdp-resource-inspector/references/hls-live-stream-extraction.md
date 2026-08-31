# HLS Stream Extraction from yy-live.top

Complete worked example of extracting HLS stream URLs from the Chinese
live-streaming React SPA at yy-live.top.

## Page Structure

yy-live.top is a React SPA served by an nginx-like backend on port 443.
Each room URL has the format:

```
https://yy-live.top/room/{roomId}?gameId={gameId}&gameName={gameName}&bgUrl={bgUrl}&type=home
```

The page has an **R18 age gate** overlay that must be dismissed before the
room content loads. The site sets `localStorage.r18 = '1'` after bypass,
so subsequent page loads auto-dismiss it.

## Stream Architecture

- Uses **LL-HLS** (Low-Latency HLS) with partial TS segments (~0.5s each)
- Player: custom React component using `plyr` wrapper around native `<video>` + MediaSource
- CDN: VolcEngine (ByteDance's CDN) via `cdnsi.com` domain
- Two CDN hostnames observed: `web.cdnsi.com` and `pull.cdnsi.com`
- Stream manifests include `_DQSK` suffix in the stream ID on some CDN nodes

## Extraction Steps

### Step 1: Navigate

```cdp
Page.navigate({
  url: 'https://yy-live.top/room/{roomId}?gameId=...',
  target_id: tabId
});
```

### Step 2: Wait (R18 bypass + player init)

The R18 gate stores `localStorage.r18 = '1'` on first click. With
persistent browser profile (e.g. `--user-data-dir=`), subsequent visits
auto-bypass.

```cdp
// Wait 8 seconds for full page render + player to start loading
Runtime.evaluate({
  awaitPromise: true,
  expression: `new Promise(r => setTimeout(r, 8000))
    .then(() => window.location.href)`,
  returnByValue: true,
  target_id: tabId
});
```

### Step 3: Extract m3u8 URL

```cdp
Runtime.evaluate({
  expression: `performance.getEntriesByType('resource')
    .filter(e => e.name.includes('cdnsi'))
    .map(e => ({ url: e.name.substring(0, 250) }))`,
  returnByValue: true,
  target_id: tabId
});
```

The first entry in the result array is the base m3u8 playlist URL.

**Example output:**
```
https://pull.cdnsi.com/live/511_2044300713413763074_720bf896f28f8df3a0bb49caa527e181_DQSK.m3u8?expire=1785300336&sign=757c273b52563e29ca038eb493e2e8fb
```

Additional entries include partial segment requests (`.ts?volcDst=...`)
and reloaded m3u8 with `_HLS_msn` & `_HLS_part` tracking params.

### Step 4: Verify

```bash
curl -sL -H "Referer: https://yy-live.top/" "$M3U8_URL" | head -5
# Expect: #EXTM3U
#         #EXT-X-VERSION:3
#         #EXT-X-TARGETDURATION:5-9
```

## URL Structure

| Component | Example |
|-----------|---------|
| CDN | `pull.cdnsi.com` or `web.cdnsi.com` |
| Path | `/live/` |
| Merchant ID | `511_` |
| Room ID | `2044300713413763074_` |
| Stream Hash | `720bf896f28f8df3a0bb49caa527e181` |
| Suffix (some CDNs) | `_DQSK` |
| Extension | `.m3u8` |
| Expire param | `?expire=1785300336` (Unix ts, ~10-15min) |
| Signature | `&sign=...` |

## API Endpoints

These may provide the stream URL programmatically without a browser:

```
GET  https://sw.fnccdn.com/511/api/zbliv/public/live/h5/get-room-info.json?aid={roomId}&mctId=511&lang=VIT&spH5=0&area=VN&t={timestamp}
POST https://sw.fnccdn.com/511/api/zbliv/public/live/get-room-token
```

## Pitfalls

- **Link expiry**: The `expire` parameter is a Unix timestamp — typically
  10–15 minutes from page load. After expiry, the CDN returns 403/404.
  Re-navigate to the room page to get a fresh link.
- **No stream if offline**: If the broadcaster is offline, no m3u8 entries
  appear. The video element may show a static poster image.
- **R18 gate on fresh profile**: First visit to any room shows an overlay.
  Click `.r18-entry button` or set `localStorage.r18 = '1'` manually.
