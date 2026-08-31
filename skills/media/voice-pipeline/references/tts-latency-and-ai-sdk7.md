# TTS Latency Optimization + AI SDK 7 Streaming (voice-lab, 2026-08-01)

Measured on i5-10400 / 32GB / no GPU, `~/voice-lab` port 3100.

## TTS — edge-tts latency (the #1 pipeline bottleneck, FIXED)

Raw edge-tts timings (same sentence, `rate=+20%`):

| Scenario | Time |
|---|---|
| Spawn Python + synth (per-request) | **4.75s** |
| Fresh process, first synth (cold websocket) | 5.0–7.0s |
| **Same process, 2nd+ synth (warm connection)** | **0.66–0.73s** |

**Fix = persistent TTS worker** (same stdin/stdout JSON protocol as the STT worker).
Keeps the Microsoft websocket alive; every request after the first costs ~0.7s.
Node side: spawn worker at server start, keep a request queue, write JSON lines to
stdin, resolve on stdout line. Worker auto-restarts on close.

### MP3 direct — skip ffmpeg wav convert entirely

- edge-tts saves MP3; browsers play it natively via
  `new Audio('data:audio/mpeg;base64,' + b64)`.
- MP3 ≈ 36KB vs wav ≈ 152KB for the same 6s sentence → 10x smaller base64 payload.
- Use `mutagen` (`pip install mutagen`) for MP3 duration: `MP3(path).info.length`.
- No `ffmpeg` in the TTS path at all. (ffmpeg is still used on the STT side to
  convert webm → wav 16kHz mono before whisper.)

### Streaming audio chunks does NOT help (verified)

`edge_tts.Communicate(...).stream()` first audio chunk arrives at ~0.35–0.43s on a
warm connection (total ~0.55–0.65s) — only ~0.3s earlier than `save()` full file,
and MP3 chunks must be decoded client-side before playback. Not worth the complexity.
Per-sentence TTS (pipelining with the LLM) is also WORSE: each request carries
network overhead, so many short requests beat one long one.

## OmniRoute quirks (agent calls)

- **OmniRoute blocks Python-urllib User-Agent (403 insufficient_quota)**. Fix:
  `headers={"User-Agent": "curl/8.0"}` on urllib requests. Curl works because it
  sends a browser-like UA. Diagnose by comparing the same POST via curl vs urllib.
- **Model prefix changed `oc/` → `cmd/`** (2026-08-01). Working: `cmd/deepseek/deepseek-v4-flash`.
  Check live catalog: `curl http://localhost:20128/api/models` (fields `fullModel`, `available`).
- `cmd/claude-haiku-4-5-20251001` → 403 `MODEL_NOT_IN_PLAN` (not in this plan).
- AI SDK 7 (v7.0.47) + TS 7 (v7.0.2) work together: `createOpenAI({ baseURL: 'http://localhost:20128/v1' })`.
- AI SDK 7 breaking changes vs v4/v5: `system` messages → `instructions` option;
  `maxSteps` → `stopWhen: isStepCount(n)`; tool `parameters:` → `inputSchema:`;
  `streamText().toolCalls` is a **Promise** → `await result.toolCalls`.

## Agent text streaming (reduce perceived wait)

`generateText` waits for the full answer (~2.3–5s with tools). To stream:

1. agent.ts: use `streamText` with an `onText(chunk)` callback param
   (`for await (const chunk of result.textStream) { onText(chunk); }`).
2. server: child process writes `TEXT:<chunk>\n` per chunk and `DONE:<json>\n` at
   end; parent parses stdout line-by-line, forwards chunks as SSE `text` events.
3. client: on `event: text`, append chunk to the reply box — first text visible in
   ~2.5s instead of waiting ~7s for the full audio round-trip.

Model choice (measured via OmniRoute, 2026-08-01): `cmd/deepseek/deepseek-v4-flash`
~2.3s/call; `cmd/moonshotai/Kimi-K2.6` ~5.9s; `cmd/MiniMaxAI/MiniMax-M2.5` ~2.3s;
`cmd/gpt-5.4-mini` errors ("No output generated"). DeepSeek-flash is the fastest
reliable free option; LLM call time is the remaining bottleneck after TTS fix.

## PhoWhisper (Vietnamese-specialized whisper)

- `vinai/PhoWhisper-small` is PyTorch format — **convert to ctranslate2** for
  faster-whisper:
  `ctranslate2.converters.TransformersConverter('vinai/PhoWhisper-small').convert(output_dir='phowhisper-small-ct2', quantization='int8', force=True)`
- Wins on Hán-Việt / địa danh vs Systran small: "phố **Cổ Linh**" & "**tối nay**"
  correct where Systran said "phố **của Linh**" / "**túi này**". Costs ~same speed
  (~2s/5s audio), but outputs lowercase (no capitalization).
- **Pitfall: `initial_prompt` BREAKS PhoWhisper** — transcribe returns empty `"."`
  when given a prompt containing foreign tokens ("Hermes, btdat.io.vn..."). Remove
  `initial_prompt` for PhoWhisper; it doesn't need prompting for Vietnamese.
- WhisperModel init: `cpu_threads=6, num_workers=1` helps a little on 6C/12T CPU.
