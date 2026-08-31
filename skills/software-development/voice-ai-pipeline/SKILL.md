---
name: voice-ai-pipeline
description: Voice-to-voice agents — whisper, edge-tts, SSE streaming.
triggers:
  - "voice-to-voice assistant / voice chat agent"
  - "speech-to-text or text-to-speech pipeline"
  - "faster-whisper / PhoWhisper / edge-tts / kokoro"
  - "reduce voice response latency (STT/TTS/LLM pipeline)"
---

# Voice AI Pipeline (home lab)

Voice-to-voice agent: mic → STT → LLM agent (AI SDK 7) → TTS → speaker. Verified on
Windows home lab (i5-10400, 32GB, no GPU) 2026-08-01.

## Architecture (all local/free, no cloud ASR/TTS API)

```
🎤 MediaRecorder(webm) → server ffmpeg → wav 16kHz → PhoWhisper (STT worker)
→ text → AI SDK 7 agent (OmniRoute LLM, streamText+tools) → text stream
→ edge-tts (TTS worker, MP3) → SSE audio parts → browser queue playback 🔊
```

## Key techniques (the hard-won lessons)

### 0. Model choice — PhoWhisper for Vietnamese, NO initial_prompt
- **PhoWhisper-small (vinai)** beats Systran `small` on Vietnamese: corrects
  Hán-Việt place names ("phố Cổ Linh" vs "phố của Linh") and time words
  ("tối nay" vs "túi này"). Systran `small` is still better for Latin words
  (Hermes→"Hêm" vs PhoWhisper→"ham").
- **CRITICAL: `initial_prompt` BREAKS PhoWhisper** — passing any prompt (even
  with the domain words you want it to learn) makes it return EMPTY text (`.`).
  PhoWhisper needs `initial_prompt` removed entirely; the Systran models handle
  it fine. Verify with `language='vi'`, `vad_filter=False` to isolate.
- `base` (74M) is too error-prone for Vietnamese; `small` (244M) is the floor on
  CPU. `compute_type='int8'` + `cpu_threads=6` on a 6-core i5 → ~2s/câu.
- PhoWhisper is PyTorch (pytorch_model.bin), NOT ctranslate2 — convert first:
  `transformers` load → `ctranslate2` convert → faster-whisper reads it.

### 0b. TTS output — MP3 direct, skip ffmpeg convert
- edge-tts outputs MP3 natively; the browser plays MP3 via HTML5 Audio — **no
  ffmpeg→WAV conversion needed**. Saves ~0.1-0.2s and shrinks payload 10x
  (36KB MP3 vs 152KB WAV for the same 6s clip). Send `data:audio/mpeg;base64,...`.
- For duration metadata use `mutagen` (`from mutagen.mp3 import MP3`) — `wave`
  module only reads WAV.
- **Tuning**: `vi-VN-HoaiMyNeural` (Nữ) + `rate='+20%'` reads lively/fast
  ("Cu em" personality). `pitch` uses `+NHz` format (e.g. `+2Hz`), NOT `%`.
  Only 2 VN voices exist (HoaiMy nữ, NamMinh nam) — style comes from rate/pitch.
- TTS per-sentence is NOT faster than one full-TTS call on a persistent worker:
  each request has connection overhead (~0.7s warm), so short sentences lose.
  One full-text call (0.7s warm) + sentence-level streaming of TEXT is the right split.

### 1. Persistent workers — the #1 latency win
Spawn Python once at server start, keep model/connection in memory, send requests via
stdin/stdout JSON lines. Do NOT spawn Python per request.
- **edge-tts persistent**: cold 5-7s → warm **0.7s** (keeps websocket to Microsoft).
- **faster-whisper persistent**: model load ~4-8s once, then ~2s/transcribe.
- Protocol: `{"text":..., "out":...}\n` in → `{"path":..., "duration":...}\n` out.
- Auto-restart worker on close (2s backoff). Queue requests while worker loads.

### 1b. Sentence-level TTS pipelining — perceived latency cut in halfBiggest UX win after persistent workers: don't wait for the FULL agent reply before TTS.
Split the LLM stream into sentences and TTS each one as it completes:
- Agent `streamText` → accumulate chunks → emit sentence on `.!?` boundary (regex
  `/^(.*?[.!?]+)([\s\S]*)$/` loop over a buffer).
- Server sends SSE `audio_part` per sentence (TTS queue processed serially, no overlap).
- Client pushes parts into a queue, plays sequentially (`playNextAudio()` shift-loop).
- Measured (2026-08-02): first text 2.79s, **first audio 3.47s** vs 7-10s waiting for
  full-reply TTS. Exactly how ChatGPT voice mode feels.
- Fallback: if no sentence boundary appears (short/garbled reply), TTS the whole text
  at the end — always keep a full-text TTS path when `audioParts.length === 0`.

### 1c. TTS timing facts (measured, 2026-08-02)
- edge-tts `stream()` first audio chunk ≈ **0.4s** warm, but TOTAL for full sentence
  ≈ 0.7s — so streaming chunks does NOT beat saving the whole file; don't bother.
- TTS sentence-by-sentence is WORSE than one full call (3-5s/cold request, network
  overhead per request). Only pipeline when you can overlap with the LLM still
  generating the NEXT sentence.
- `rate='+20%'` shortens audio ~30% — natural for a fast "assistant" persona.

### 1d. MP3 direct — skip ffmpeg entirely
edge-tts outputs MP3; browsers play `audio/mpeg` natively. Save `.mp3` straight from
the worker, send `data:audio/mpeg;base64,...`, no WAV conversion. MP3 ≈ 36KB vs
152KB WAV for same content — 10x smaller over the wire.

### 2. STT model choice (Vietnamese)
| Model | Accuracy VN | Speed (CPU) | Notes |
|---|---|---|---|
| Systran `base` | poor | fast | too many errors |
| Systran `small` | ok | ~2s | good but misses Hán-Việt words |
| **PhoWhisper-small** (convert) | **best** | ~2s | catches "Cổ Linh", "tối nay" — win on Hán-Việt/place names |

- Convert PhoWhisper (PyTorch) → ctranslate2 once:
  `ctranslate2.converters.TransformersConverter('vinai/PhoWhisper-small').convert(output_dir='phowhisper-small-ct2', quantization='int8')`
- **PITFALL**: PhoWhisper + `initial_prompt` with foreign words (e.g. "Hermes") → returns EMPTY. Drop initial_prompt for PhoWhisper.
- Use `cpu_threads=6` (match cores), `compute_type='int8'`, `beam_size=1`, `vad_filter=True`.

### 3. TTS — edge-tts MP3 direct (no WAV convert)
- edge-tts outputs MP3 → **browser plays MP3 natively**. Skip ffmpeg WAV convert (saves 0.1-0.2s + 10x smaller payload).
- Voices VN: `vi-VN-HoaiMyNeural` (nữ), `vi-VN-NamMinhNeural` (nam) — only 2.
- Personality via `rate`/`pitch`: `rate='+20%'` sounds energetic; `pitch='+1Hz'` brighter, `-1Hz` warmer. Bash pitfall: `--pitch -1Hz` parses as flag → use `--pitch=-1Hz`.
- Local Kokoro-VN tested: NOT faster than warm edge-tts (0.83s synth + 8s load), skip.

### 4. Streaming + sentence pipeline (cut perceived latency 60%)
- Stream LLM text chunks via SSE `text` events → user sees words in ~2.5s.
- Split sentences (`/^(.*?[.!?]+)([\s\S]*)$/`), TTS **each sentence as it completes** (parallel with LLM), send SSE `audio_part`, client plays queue sequentially.
- Measured: first text 2.79s, first audio **3.47s** (vs 7-10s full wait).
- Per-sentence TTS alone is NOT faster (0.7s overhead each) — the win is parallelism.

### 5. Audio in
- MediaRecorder `{ audioBitsPerSecond: 128000 }` for better quality.
- Server converts webm→wav 16kHz mono via ffmpeg before STT (whisper reads wav better).
- STT worker + transcribe endpoint must handle concurrent requests — serialize via queue.

## Latency budget (CPU i5-10400, no GPU)
| Stage | Time |
|---|---|
| STT (PhoWhisper-small) | ~2.0s |
| LLM agent (deepseek-flash, 1-2 steps) | 2.3-4.5s |
| TTS (edge-tts warm) | ~0.7s |
| **Total** | **~5-8s** (first audio 3.5s with pipeline) |

Floor limits: LLM ~2.3s (provider), STT ~2s (CPU). GPU or faster provider needed to go lower.

## Files layout
```
voice/
  stt_worker.py      # persistent faster-whisper/PhoWhisper
  tts_worker.py      # persistent edge-tts → MP3
  phowhisper-small-ct2/  # converted model (keep in repo)
server.mjs           # SSE endpoints: /api/voice/transcribe, /api/voice/respond
src/agent.ts         # AI SDK 7 streamText + tools (see typescript-ecosystem skill)
```
