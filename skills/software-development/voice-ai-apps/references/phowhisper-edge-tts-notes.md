# Voice Lab — Session Notes & Exact Commands (2026-08-01)

Project: `~/voice-lab` (port 3100, standalone, git repo). Serves `https://voice.btdat.io.vn` via Cloudflare tunnel.

## Layout
```
~/voice-lab/
├── server.mjs          # HTTP + SSE + spawns worker + agent
├── src/agent.ts        # AI SDK 7 agent (TS7, runs via node --experimental-strip-types)
├── voice/
│   ├── stt_worker.py   # persistent faster-whisper worker (PhoWhisper-small-ct2)
│   ├── stt.py          # one-shot STT (deprecated, replaced by worker)
│   ├── tts.py          # edge-tts wrapper (--voice/--rate/--pitch)
│   └── phowhisper-small-ct2/  # converted PhoWhisper model (int8)
├── public/index.html   # standalone UI (no build step — plain HTML/JS)
└── package.json
```

## Server run
```bash
cd ~/voice-lab && node server.mjs   # port 3100
```
Boot sequence: starts STT worker (model load ~5s) → logs "✅ STT worker sẵn sàng" → HTTP ready.

## Key API endpoints
- `GET /api/status` → `{ok, name, port, ai}`
- `POST /api/voice/transcribe` — `{audio: base64, format: 'webm'|'wav'}` → `{text, duration}`. Server ffmpeg-converts webm→wav 16kHz.
- `POST /api/voice/respond` — `{text, history, voice}` → **SSE stream**: `step`(agent/tools/tts) then `done`(text, audio base64, duration).

## Model/voice defaults
- STT: `phowhisper-small-ct2` (startSttWorker arg in server.mjs)
- TTS voice: `vi-VN-HoaiMyNeural`, **rate +20%** (hardcoded in ttsArgs — user chose "D" variant)
- Agent: `cmd/deepseek/deepseek-v4-flash` via OmniRoute `createOpenAI({baseURL:'http://localhost:20128/v1'})`

## OmniRoute model migration (2026-08-01)
- `oc/deepseek-v4-flash-free` → died (500 Invalid API key). Live: `cmd/` prefix.
- Discover: `curl http://localhost:20128/api/models` → fullModel list.
- Free-ish working: `cmd/deepseek/deepseek-v4-flash` (tool calling works via AI SDK 7).
- **Python urllib needs `User-Agent: curl/8.0`** or 403 (see omniroute-management skill).

## Cloudflare tunnel DNS for new subdomain
- No CF API token on machine → cannot `cloudflared tunnel route dns` (needs cert.pem).
- Tunnel btdat.io.vn = 3 cloudflared processes (`cloudflared tunnel run b3e9ea6a-...`), killable via taskkill.
- PID 4604 = OmniRoute's quick tunnel (trycloudflare) — DO NOT kill.
- New subdomain: user must add CNAME manually in CF dashboard: `voice` → `b3e9ea6a-9ed9-41fc-be71-66f52b31fef3.cfargotunnel.com`, Proxied.
- After adding ingress to ~/.cloudflared/config.yml, restart tunnel processes for it to take effect.

## edge-tts quirks (verified)
- `--pitch` only accepts Hz (`+2Hz`), NOT `%` (`+10%` → "Invalid pitch").
- bash eats `-2Hz` as a flag → always pass `--pitch=-2Hz` (equals form) or quote.
- Only 2 VN voices: HoaiMy (female), NamMinh (male). No style options.
- Output is mp3; tts.py converts to wav 16kHz mono via ffmpeg for whisper/web.

## PhoWhisper pitfalls (verified)
- `initial_prompt` with any non-VN text (e.g. "Hermes, btdat.io.vn") → transcribe returns `.` (empty). Remove it; PhoWhisper needs no prompt.
- TransformersConverter needs `transformers` + `ctranslate2` installed; conversion ~1 min for small.
- Test comparison (4.5s audio): Systran small got "phố của Linh... túi này" (wrong), PhoWhisper got "phố cổ linh... tối nay" (correct). PhoWhisper wins for Vietnamese địa danh/context.

## TTS variant testing (user chose D)
A: HoaiMy +12% +1Hz — energetic
B: HoaiMy +8% -1Hz — soft/warm
C: NamMinh +12% — male
**D: HoaiMy +20% — lively, chosen as default** ✅
