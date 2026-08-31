---
name: voice-pipeline
description: STT→TTS voice pipelines (whisper + edge-tts + LLM agent).
---

# Voice Pipeline (STT → LLM → TTS)

Class of task: web page or service that listens to speech, understands it (STT), responds via an LLM agent, and speaks back (TTS). Built 2026-08-01 as `~/voice-lab` (port 3100, standalone Node server + Python scripts, exposed at `voice.btdat.io.vn`).

## Architecture (proven)

```
Browser MediaRecorder → base64 audio → POST /api/voice/transcribe
  → faster-whisper (persistent Python worker, stdin/stdout JSON protocol)
  → text → POST /api/voice/respond (SSE stream)
  → LLM agent (AI SDK 7 / OmniRoute) with tools (text streamed realtime)
  → edge-tts (persistent Python worker) → MP3 → base64 → browser Audio playback
```

Key design decisions:
- **STT and TTS MUST be Python** (faster-whisper, edge-tts have no good Node equivalents). Only the LLM agent can be TS/Node.
- **Persistent STT worker** (not spawn-per-request): whisper model load is ~5-50s; keeping it in memory makes transcribe ~2s for 5s audio.
- **Persistent TTS worker TOO — biggest latency win**: edge-tts keeps a websocket to Microsoft; first synth in a fresh process is 5-7s (cold), subsequent ones **0.66-0.73s** (warm). Spawn-per-request TTS is the #1 voice-pipeline latency trap.
- **SSE stream for progress** so the UI can show step-by-step status (transcribe → agent → tools → tts → done).
- webm from MediaRecorder → convert to wav 16kHz mono via ffmpeg before whisper (better accuracy than feeding webm).
- **TTS outputs MP3 directly — NO ffmpeg wav convert**: browsers play MP3 natively (`new Audio('data:audio/mpeg;base64,...')`), and MP3 is ~10x smaller than wav (36KB vs 152KB for same sentence) → faster base64 transfer, especially mobile.

Detail & recipes: `references/tts-latency-and-ai-sdk7.md` (edge-tts persistent-worker numbers, MP3-direct, AI SDK 7 streaming, OmniRoute UA/model quirks, PhoWhisper convert + pitfalls). Templates: `templates/stt_worker.py`, `templates/tts_worker.py`.

## STT — faster-whisper

### Model selection for Vietnamese (i5-10400 CPU, 6C/12T, 32GB, no GPU)

| Model | Params | Load (cached) | Speed | VN accuracy |
|---|---|---|---|---|
| `base` | 74M | ~1s | fastest | ⭐ poor ("Thân chào anh đạt, em là hêm") |
| **`small`** ⭐ | 244M | ~5s | ~2s/5s-audio | ⭐⭐⭐ good ("Xin chào anh Đạt... em là Hêm trợ lý") |
| `medium` | 769M | slower | ~5-8s | ⭐⭐⭐⭐ |
| `large-v3` | 1.5B | slow | ~15s | ⭐⭐⭐⭐⭐ |

- First load downloads from HuggingFace (~464MB for small) — be patient; cached reload is fast.
- **`small` is the sweet spot** for CPU + Vietnamese.
- **PhoWhisper** (`vinai/PhoWhisper-small`) is Vietnamese-specialized but ships as PyTorch (`pytorch_model.bin`); convert to ctranslate2 via `ctranslate2.converters.TransformersConverter(...).convert(output_dir=..., quantization='int8')`. In practice PhoWhisper-small was NOT better than Systran small ("Hermes"→"ham" vs "Hêm") — don't bother unless testing medium/large.
- Foreign names (e.g. "Hermes") get mangled at small size. Fix: `initial_prompt="Hermes"` to bias the model.

### Persistent worker pattern
`stt_worker.py`: loads model once, reads JSON lines from stdin (`{"path": ..., "lang": "vi"}`), writes `{"text": ...}` per line. Server spawns it at startup, keeps stdin/stdout pipe, queues requests, auto-restarts on close.

## TTS — edge-tts (free, Microsoft)

- `python tts.py --text "..." --out out.wav --voice vi-VN-HoaiMyNeural`
- Vietnamese voices: `vi-VN-HoaiMyNeural` (female), `vi-VN-NamMinhNeural` (male)
- edge-tts outputs MP3 → convert to wav 16kHz mono via ffmpeg (`-ar 16000 -ac 1 -c:a pcm_s16le`) for web playback/STT round-trip
- Ensure output directory exists BEFORE writing (mp3 temp file fails with Errno 2 if dir missing)
- Needs internet (Microsoft service); fallback: Hermes TTS provider

## LLM agent — no audio capability!

**LLMs (DeepSeek, Claude, GPT) CANNOT process audio.** STT must always precede the LLM. OmniRoute has zero audio/ASR models — see `omniroute-management` skill.

## Frontend recording tips
- `new MediaRecorder(stream, { audioBitsPerSecond: 128000 })` — higher bitrate = better STT
- Convert blob → base64 in chunks (`String.fromCharCode.apply(null, bytes.subarray(i, i+0x8000))`) to avoid call stack overflow
- Play response as `data:audio/wav;base64,...`

## SSE progress pattern
Server: `res.writeHead(200, {'Content-Type':'text/event-stream', 'Cache-Control':'no-cache'})`, write `event: step\ndata: {...}\n\n` per stage, final `event: done`.
Client: `fetch` + `response.body.getReader()` + `TextDecoder`, buffer until `\n\n`, parse `event:`/`data:` lines.

## Pitfalls
- Python urllib → OmniRoute 403 (User-Agent) — see omniroute-management skill
- On Windows, Python scripts need Windows paths (`C:/...`), not MSYS `/c/...` paths
- `runPy` helper: pass script args WITHOUT repeating script name (`runPy('tts.py', ['--text', ...])` — NOT `['tts.py', '--text', ...]`)
