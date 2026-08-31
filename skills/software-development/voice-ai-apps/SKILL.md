---
name: voice-ai-apps
description: "Build voice-to-voice apps: STT whisper + LLM + TTS pipeline."
---

# Voice AI Apps — STT + Agent + TTS Pipeline

Voice-to-voice web apps: user speaks → STT → LLM agent → TTS → speak back. Verified on voice-lab (~/voice-lab, port 3100, voice.btdat.io.vn).

## Architecture (proven stack, all local/free)
```
🎤 Browser MediaRecorder (webm, 128kbps) → POST base64 → server
→ ffmpeg convert webm→wav 16kHz mono → faster-whisper/PhoWhisper (STT)
→ LLM agent (AI SDK 7 + OmniRoute cmd/deepseek) with tools
→ edge-tts (TTS) wav → base64 → browser Audio playback
```

## STT: faster-whisper model choice (Vietnamese tested)
| Model | Size | Accuracy VN | Speed (i5-10400 CPU) |
|---|---|---|---|
| `base` | 74M | poor — mishears | fast |
| `small` (Systran) | 244M | good, proper capitalization | ~2s/5s audio |
| **`PhoWhisper-small`** ⭐ | 244M | BEST for VN — gets địa danh (Cổ Linh), Hán-Việt right | ~2s/5s audio |
| `medium` | 769M | better | ~5-8s |

**PhoWhisper** (vinai/PhoWhisper-*) is PyTorch format — faster-whisper (ctranslate2) can't read it directly. Convert once:
```python
from transformers import WhisperForConditionalGeneration
import ctranslate2
converter = ctranslate2.converters.TransformersConverter('vinai/PhoWhisper-small')
converter.convert(output_dir='phowhisper-small-ct2', quantization='int8', force=True)
# then: WhisperModel('phowhisper-small-ct2', device='cpu', compute_type='int8')
```
PITFALL: **do NOT pass `initial_prompt` with foreign words ("Hermes, btdat.io.vn") to PhoWhisper** — it returns empty/`.` transcript. The VN tokenizer chokes; plain transcribe works.

## TTS: edge-tts (free Microsoft neural voices)
- Vietnamese voices: ONLY `vi-VN-HoaiMyNeural` (Female), `vi-VN-NamMinhNeural` (Male)
- `--rate` (`+20%`) and `--pitch` (`+2Hz`) supported — `%` pitch INVALID (only Hz)
- PITFALL: bash eats `-2Hz` as flag → use `--pitch=-2Hz` (equals form)
- edge-tts returns mp3; convert to wav 16kHz for whisper/web playback
- Tuning: user picked HoaiMy female +20% rate ("Cu em" lively personality)

## Persistent STT worker pattern (critical for speed)
Spawning `python stt.py` per request reloads the model (~1-5s). Instead run a **stdin/stdout worker** that loads model once:
```python
# stt_worker.py: read JSON line from stdin → transcribe → print JSON line, flush=True
```
Node side: `spawn('python', [worker.py, '--model', ...])`, parse stdout lines, queue callbacks, write request via stdin. Model load ~5s once at boot, then every request ~2s.

## Browser recording → server
```js
recorder = new MediaRecorder(stream, { audioBitsPerSecond: 128000 }); // higher bitrate = clearer
// on stop: blob → arrayBuffer → base64 (chunked String.fromCharCode for large) → POST
```
Server converts webm→wav 16kHz via ffmpeg before STT (whisper reads wav better than webm).

## SSE progress streaming (UX)
`/api/voice/respond` returns SSE events so UI shows live steps:
```
event: step  {id:'agent', label:'🧠 Hermes đang suy nghĩ...'}
event: step  {id:'tools', ...}
event: step  {id:'tts', ...}
event: done  {text, audio, duration, tool_calls}
```
Client: `fetch` + `ReadableStream.getReader()` + TextDecoder, split on `\n\n`, parse `event:`/`data:` lines. UI: dot-per-step with active=blink, done=gold.

## LLM agent (AI SDK 7 + OmniRoute)
See `typescript-ecosystem` skill + `references/ai-sdk-7-migration.md` for AI SDK 7 API. Key: `generateText({ model, instructions, messages, tools, stopWhen: isStepCount(3) })` — `system` message → `instructions` option; `maxSteps` → `stopWhen: isStepCount(N)`.

## Support files
- `references/phowhisper-edge-tts-notes.md` — voice-lab specific quirks, exact commands
