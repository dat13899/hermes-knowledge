---
name: yystream
description: Extract HLS m3u8 from yy-live.top rooms via Chrome CDP.
---

# yy-live.top Stream Extractor

Trích xuất link HLS stream từ yy-live.top dùng Chrome remote debugging.

## Prerequisites

- Chrome remote debugging đang chạy trên port **9222** với profile `C:\Users\datel\chrome-debug`
- R18 gate đã được bypass (localStorage `r18=1` đã lưu từ lần trước)
- CDP endpoint: `http://localhost:9222`

## Workflow

### 1. Navigate tới room

Dùng `browser_cdp` với target ID hiện tại:

```
method=Page.navigate
params={"url": "https://yy-live.top/room/{ROOM_ID}?gameId=...&gameName=...&bgUrl=...&type=home"}
target_id=346F6F99FD89C46828858B47A98FC4A2
```

### 2. Đợi load + capture network

Dùng `Runtime.evaluate` với awaitPromise để đợi 8s rồi query performance entries:

```js
new Promise(r => setTimeout(r, 8000)).then(() => 
  performance.getEntriesByType('resource')
    .filter(e => e.name.includes('cdnsi'))
    .map(e => ({url: e.name.substring(0,250)}))
)
```

### 3. Lấy m3u8 URL

Kết quả trả về chứa base `.m3u8` URL. Lọc lấy entry đầu tiên có `?expire=` và không có `_HLS_msn` (tracking params).

### 4. Verify (tuỳ chọn)

```bash
curl -sL --connect-timeout 10 --max-time 15 \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://yy-live.top/" \
  "M3U8_URL" | head -5
```

Expected: bắt đầu bằng `#EXTM3U`

## Stream URL Pattern

```
{pull|web}.cdnsi.com/live/511_{ROOM_ID}_{HASH}[_DQSK].m3u8?expire={UNIX_TIMESTAMP}&sign={MD5}
```

- `web.cdnsi.com` — stream không có `_DQSK` suffix
- `pull.cdnsi.com` — stream có `_DQSK` suffix
- Expire timestamp: Unix, link sống tầm 10-15 phút
- Cần dùng lại `Page.navigate` + capture lại nếu link hết hạn

## Fallback API endpoints

Nếu performance entries không có:
- `GET https://sw.fnccdn.com/511/api/zbliv/public/live/h5/get-room-info.json?aid={ROOM_ID}&mctId=511&lang=VIT`
- `POST https://sw.fnccdn.com/511/api/zbliv/public/live/get-room-token`

## Notes

- R18 gate tự bypass nhờ localStorage `r18=1` đã lưu
- LL-HLS stream, partial segments ~0.5s, target duration 5-9s
- Container: MPEG-TS (.ts), CDN: VolcEngine (ByteDance)
- Trang đích paste link xem: https://btdat.io.vn/stream
