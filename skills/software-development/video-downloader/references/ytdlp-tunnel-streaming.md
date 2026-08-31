# yt-dlp → Browser Audio Through a Cloudflare Tunnel — Critical Pitfalls

Verified 15/08/2026 while building `btdat.io.vn/yt` (YouTube Audio player). Serving audio through a tunnel (btdat.io.vn → localhost:3000 via cloudflared) behaves VERY differently from serving locally.

## 1. Realtime pipe streaming stalls through the tunnel

`spawn('yt-dlp', ['-f','bestaudio','-o','-','--no-warnings', url])` piped straight to the HTTP response:
- ✅ works on localhost
- ❌ through Cloudflare the browser timeline advances with **no audio** (data arrives too slowly to decode)

**User-visible symptom:** timeline runs, `readyState` climbs, `paused=false`, no sound → "đang phát mà không có tiếng".

## 2. Fix: download whole file, then serve static with Range

```
yt-dlp -o - --quiet --no-progress  →  ffmpeg → /tmp/yt-<md5(url)[:10]>.mp3   (~3s for 3-min song)
```
Then serve the file with `Content-Length` + `Accept-Ranges: bytes` + 206 partial responses. Browser buffers fully, `duration` known, sound guaranteed. Cache by URL hash → repeat plays instant.

## 3. `--quiet --no-progress` is MANDATORY when piping yt-dlp stdout

Without it, the `\r` progress lines interleave into stdout on Windows → ffmpeg dies:
```
[in#0 @ ...] Error opening input: Invalid data found when processing input
```
Direct `yt-dlp -o - | head -c` tests HIDE this (shell buffering). Only visible in the real pipe chain.

## 4. Format selection: `-f bestaudio` + transcode, NOT m4a

- `-f bestaudio[ext=m4a]` → frequently **blocked by YouTube** (exit code 1, 0 bytes). Opus/webm (`bestaudio`) works.
- Raw opus/webm often fails to decode in Chromium: `PipelineStatus::DEMUXER_ERROR_COULD_NOT_OPEN: FFmpegDemuxer: open context failed`.
- So: always `-f bestaudio` → ffmpeg `-f mp3 -ac 2 -b:a 128k`. MP3 plays everywhere.

## 5. EPIPE crashes naive node servers

`ffmpeg.stdout.pipe(res)` throws `EPIPE` (errno -4047) when the browser cancels the fetch → whole server dies → 502 for everyone. Attach error handlers on: `res`, `ffmpeg`, `ffmpeg.stdin`, and `req.on('close')`. All paths must kill child processes and clear the active-stream ref.

## 6. Download-then-serve race → 502

Holding the response open while the ~3s download runs → tunnel times out → 502. Pattern that works:

```js
// server: trigger background download, respond 404 {downloading:true} until file ready
// frontend:
fetch(streamUrl).catch(()=>{});           // trigger background download
for (let i=0;i<20;i++){                   // poll HEAD up to ~12s
  const p = await fetch(streamUrl,{method:'HEAD'});
  if (p.ok || p.status===206) break;
  await new Promise(r=>setTimeout(r,600));
}
audio.src = streamUrl; audio.play().catch(()=>{});
```

Server must accept `HEAD` on the stream endpoint (return headers + `res.end()`, no body).

## 7. Verifying audio truly plays (headless proof)

`readyState / paused / currentTime` can claim "playing" while silence plays. Real proof = AnalyserNode:

```js
// in page context after clicking play:
const actx = new AudioContext();
const src = actx.createMediaElementSource(document.getElementById('yt-audio'));
const analyser = actx.createAnalyser(); analyser.fftSize = 256;
src.connect(analyser); analyser.connect(actx.destination);
// then sample: analyser.getByteFrequencyData(arr); peak/avg > 0  ⇒ real audio
```

Music track gave `peak≈190/255, avg≈47` = confirmed audible. Launch Chromium with `--autoplay-policy=no-user-gesture-required` or `play()` gets rejected headless.

## Related

Full player UI pattern (timer auto-stop, kill-stream-before-replay, example chips, clipboard paste): `references/youtube-audio-player-ui.md`. Deploy/routing for `btdat.io.vn` (server.js with `/vtts` + `/yt` exceptions, SPA fallback, Vite `preview.allowedHosts`): see `fe-deploy-troubleshooting`.
