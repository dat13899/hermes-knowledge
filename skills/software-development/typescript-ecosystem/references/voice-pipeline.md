# Voice-to-Voice Pipeline — voice-lab (~/voice-lab, port 3100)

Built 2026-08-01. Voice chat page at `voice.btdat.io.vn` (subdomain; main site
route `/ts7/voice` was the original plan, moved to standalone subdomain).

## Architecture (all-local, free)

```
Mic (MediaRecorder webm) → POST /api/voice/transcribe → stt.py (faster-whisper)
                        → POST /api/voice/respond → agent (AI SDK 7 + TS7) → tts.py (edge-tts) → base64 wav
```

| Layer | Tech | Notes |
|---|---|---|
| STT | `voice/stt.py` | faster-whisper 1.2.1, model `base`, `vad_filter=True`, `beam_size=1`, lang `vi`. CUDA if available else CPU int8. |
| Agent | `src/agent.ts` | AI SDK 7 `generateText` + `tool()` + `isStepCount(3)`, model `oc/deepseek-v4-flash-free` via `createOpenAI({baseURL:'http://localhost:20128/v1'})`. Tools: `service_status` (→:3000/api/services), `rag_query` (→:3001/query). |
| TTS | `voice/tts.py` | edge-tts → mp3 → ffmpeg → wav 16kHz mono PCM. Voices: `vi-VN-HoaiMyNeural` (Nữ, default), `vi-VN-NamMinhNeural` (Nam). |
| Server | `server.mjs` | Node http on 3100, spawns python for stt/tts, spawns `node --experimental-strip-types` for agent.ts. |

## Key implementation details

- **Run TS7 agent without build**: `spawn('node', ['--experimental-strip-types', '--input-type=module', '-e', script])` where script does `import('./src/agent.ts')`.
- **runPy helper**: `spawn('python', [scriptPath, ...args], { cwd: VOICE_DIR })`. PITFALL: args must NOT repeat the script name (`python tts.py tts.py --text...` → "No such file").
- **TTS must create output dir** — edge-tts `save()` fails if parent dir missing. `os.makedirs(out_dir, exist_ok=True)` first.
- **Edge-tts output is mp3** — always ffmpeg-convert to wav 16k mono (`-ar 16000 -ac 1 -c:a pcm_s16le`) for browser `Audio('data:audio/wav;base64,...')`.
- **Transcribe accepts webm** (MediaRecorder default) — whisper handles it; keep the `format` field in the request.
- Browser: `new Audio('data:audio/wav;base64,' + b64)` plays fine. `audio.onended` → reset status.
- MediaRecorder auto-stop timer 15s + `stopLevel`/`startLevel` via AnalyserNode for mic visual.

## AI SDK 7 notes that bit during build

- `system` in messages → error. Use `instructions:` option.
- `tool({ parameters })` → use `inputSchema` (zod).
- `generateText` + tools needs `stopWhen: isStepCount(3)` to continue after tool results.
- `toolChoice: 'auto'` works with `oc/deepseek-v4-flash-free`.

## Verify commands

```bash
cd ~/voice-lab && node server.mjs            # port 3100
curl -s http://localhost:3100/api/status     # {"ok":true,...}
curl -s -X POST http://localhost:3100/api/voice/respond -H 'Content-Type: application/json' \
  -d '{"text":"Service nào đang chạy?","history":[],"voice":"vi-VN-HoaiMyNeural"}' | python -c "import json,sys; d=json.load(sys.stdin); print(d['text'], len(d.get('audio') or ''))"
```

Type-check: `cd ~/voice-lab && npx tsc --noEmit` (needs `"types": ["node"]`, `"allowImportingTsExtensions": true`).

## Cloudflare subdomain (voice.btdat.io.vn)

- `~/.cloudflared/config.yml` ingress: `- hostname: voice.btdat.io.vn / service: http://localhost:3100`
- Restart: kill the 3 `cloudflared tunnel run b3e9ea6a-...` PIDs (`taskkill /F /PID`), start `cloudflared tunnel run b3e9ea6a-9ed9-41fc-be71-66f52b31fef3`.
- DNS CNAME `voice → b3e9ea6a-9ed9-41fc-be71-66f52b31fef3.cfargotunnel.com` (proxy ON) — manual on dashboard, no CF API token.
- Do NOT kill the OmniRoute quick-tunnel PID (parent node.exe).
