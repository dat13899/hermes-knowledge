# Streaming YouTube audio to a browser — pitfalls & working pattern

Context: btdat.io.vn/yt (Node server.js, port 3000, behind Cloudflare tunnel). Goal: `<audio>` element plays a YouTube URL. Lessons are hard-won; each pitfall below cost real debugging time.

## Pitfall 1: yt-dlp progress output corrupts piped stdout
`yt-dlp -o -` writes the download progress bar to **stderr**, but when piped into another Windows process (ffmpeg), the interleaved progress can corrupt the pipe — ffmpeg fails with `Error opening input: Invalid data found when processing input`, close code like `3199971767`.

**Fix:** always pass `--quiet --no-progress --no-warnings` when piping:
```js
spawn('yt-dlp', ['-f', 'bestaudio', '-o', '-', '--quiet', '--no-progress', '--no-warnings', url], {windowsHide: true, stdio: ['ignore','pipe','pipe']})
```

## Pitfall 2: webm/Opus audio doesn't decode in Chromium
`bestaudio` returns format 251 (Opus in webm/matroska). Chromium `<audio>` throws `PipelineStatus::DEMUXER_ERROR_COULD_NOT_OPEN: FFmpegDemuxer: open context failed` — and the timeline runs with **no sound** (looks playing, silent).

`bestaudio[ext=m4a]` / format 140 direct download can fail too (YouTube returns HTTP error for m4a dash in some regions/setups).

**Working approach: transcode webm → MP3 via ffmpeg**:
```js
const ffmpeg = spawn('ffmpeg', ['-i','pipe:0','-f','mp3','-ac','2','-b:a','128k','pipe:1'], {windowsHide:true, stdio:['pipe','pipe','pipe']})
ytdlp.stdout.pipe(ffmpeg.stdin)
ffmpeg.stdout.pipe(res)
```
Drain child stderr with `.resume()` or `on('data',()=>{})` — otherwise backpressure blocks the child.

## Pitfall 3: realtime streaming stalls through Cloudflare tunnel
Piping yt-dlp→ffmpeg→HTTP response live works on localhost but **stalls through Cloudflare** (or any buffering proxy): browser gets dribbled data, timeline advances but no audio decodes. Symptom: `curl` via domain returns 0 bytes at ~2s while localhost returns full 3.4MB.

**Working approach: download to temp file, then serve static with Range:**
1. First request: kick off background download (yt-dlp → ffmpeg `-y tmpfile`), return `404 {downloading:true}` — do NOT hold the response open.
2. Client polls HEAD until `206`/`200`, then sets `audio.src`.
3. Static serve with `Content-Length` + `Content-Range` + `Accept-Ranges: bytes` + 206. Browser buffers whole file → plays with sound guaranteed.
4. Cache key = md5(url).slice(0,10) → `tmp/yt-<hash>.mp3`; second play of same URL is instant.

Download takes ~3s for a 3:33 track (ffmpeg ~63x realtime). Poll every ~600ms, cap ~20 tries, show toast "Đang tải audio..." while waiting.

## Verify audio ACTUALLY plays (not just timeline)
Media element `readyState>=3, paused:false` is NOT proof of sound. Use an AudioContext analyser:
```js
const actx = new AudioContext();
const src = actx.createMediaElementSource(document.getElementById('yt-audio'));
const analyser = actx.createAnalyser(); analyser.fftSize = 256;
src.connect(analyser); analyser.connect(actx.destination);
// sample: analyser.getByteFrequencyData(arr) → peak ~180/255 & avg > 10 = real sound
```
Launch Chromium with `--autoplay-policy=no-user-gesture-required` so `a.play()` isn't blocked.

## Windows Node ESM gotchas
- `require('node:crypto')` throws in ESM — `import {createHash} from 'node:crypto'`.
- Client disconnect mid-pipe → unhandled `EPIPE` kills the whole server. Add `res.on('error', ()=>{kill children})` AND `child.on('error', ()=>{})` / `stdin.on('error', ()=>{})` on every spawned stream.
