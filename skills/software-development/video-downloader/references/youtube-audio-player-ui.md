# YouTube Audio Player UI (Utilities Page)

Full web UI at `/utilities` for playing YouTube audio in browser background. Works on mobile with screen off.

## Frontend HTML structure

```
┌─────────────────────────────────────────┐
│ 🧰 Tiện ích                            │
├─────────────────────────────────────────┤
│ ┌──── YouTube Audio Player ───────────┐ │
│ │ 🎵 Dán link → phát âm thanh.       │ │
│ │    Timer 5p mặc định, tắt hẳn       │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ [ Dán link YouTube vào đây...  ] [Play]  │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ [thumb] ▷ Title by Uploader · 5:30 │ │
│ │         ═══════════════════ [▶⏸]   │ │
│ │ ⏱ Tắt sau: [3p] [5p✓] [10p] [30p] │ │
│ │                      ⏳ Tắt sau 5p  │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Key JS patterns

### auto-select + default timer
```javascript
selectUt('youtube');                         // on load
// Inside loadYt(), after play:
setTimer(300);                                // default 5p
```

### kill stream before new stream
```javascript
async function killStream() {
  await fetch('/api/utilities/youtube-audio/stop', {method:'POST'});
  const a = document.getElementById('yt-audio');
  a.pause(); a.src = ''; a.load();
}
```
**Must** call before setting new src — otherwise 2 yt-dlp processes run.

### setTimer with auto-stop
```javascript
function setTimer(seconds) {
  if (timerId) clearTimeout(timerId);
  // highlight active button
  timerId = setTimeout(async () => {
    await killStream();
    showStatus('Đã tắt');
    toast('Audio đã tắt hoàn toàn');
  }, seconds * 1000);
}
```

## Server endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/utilities/youtube-audio?url=...` | GET | JSON: title, thumbnail, duration, uploader |
| `/api/utilities/youtube-audio/stream?url=...` | GET | Pipe yt-dlp `-f bestaudio -o -` stdout as `audio/webm` |
| `/api/utilities/youtube-audio/stop` | POST | Kill active yt-dlp process + cleanup |

### Stream lifecycle (server)
```javascript
let _activeStream = null;

// On new stream:
if (_activeStream) { _activeStream.child.kill(); }
_activeStream = { url, child, req };
child.stdout.pipe(res);

// On client disconnect:
req.on('close', () => {
  child.kill();
  if (_activeStream?.child === child) _activeStream = null;
});

// On explicit stop:
POST handler → _activeStream.child.kill(); _activeStream.req.destroy();
```

## CSS classes for glass theme

| Class | Purpose |
|---|---|
| `.ut-grid` | auto-fill grid (minmax 320px) |
| `.ut-card` | glass card with active border |
| `.player-area` | glass backdrop section (hidden `.show`) |
| `.timer-bar` | flex row with timer buttons |
| `.yt-input` | flex input + button row |

## Timer preference (Anh Đạt)

Options: **3p / 5p / 10p / 30p**. Default: **5p**.
