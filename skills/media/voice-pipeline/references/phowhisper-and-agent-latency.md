# PhoWhisper (Vietnamese STT) + Agent Latency — voice-lab, 2026-08-01

Measured on i5-10400 / 32GB / no GPU.

## PhoWhisper — Vietnamese-specialized STT (beats Systran small)

`vinai/PhoWhisper-small` is a Vietnamese fine-tune of Whisper. It ships as PyTorch
(`pytorch_model.bin`) — faster-whisper needs ctranslate2, so convert once:

```python
from transformers import WhisperForConditionalGeneration
import ctranslate2
converter = ctranslate2.converters.TransformersConverter('vinai/PhoWhisper-small')
converter.convert(output_dir='phowhisper-small-ct2', quantization='int8', force=True)
# then: faster_whisper.WhisperModel('phowhisper-small-ct2', device='cpu', compute_type='int8', cpu_threads=6)
```

A/B comparison (same Vietnamese sentence, "phở bò ở phố Cổ Linh..."):

| Model | Transcript | Verdict |
|---|---|---|
| Systran `small` | "phố **của Linh**... **túi này**" | wrong toponym + wrong time phrase |
| **PhoWhisper-small** | "phố **cổ linh**... **tối nay**" | ✅ correct |

PhoWhisper wins on Vietnamese toponyms (Hán-Việt) and context. It outputs lowercase
(Systran preserves capitalization) and slightly slower (~2.0s vs 1.9s for 5s audio) —
accuracy wins for VN. Model load cached ~4-8s (keep the persistent worker).

### ⚠️ PITFALL: `initial_prompt` BREAKS PhoWhisper
Passing `initial_prompt="Hermes, btdat.io.vn, Hà Nội..."` to PhoWhisper returns an
**empty transcript** (`.`) — its VN tokenizer chokes on foreign tokens. Systran
whisper tolerates initial_prompt fine. → For PhoWhisper, DO NOT set initial_prompt.

## Agent (LLM) latency — the post-TTS bottleneck

| Question type | Latency | Why |
|---|---|---|
| Simple (no tool) | ~2.3s | 1 LLM call via OmniRoute |
| Tool question ("service nào chạy?") | ~4.5s | 2 steps (call tool + synthesize) |

- `stopWhen: isStepCount(N)` — N = max LLM calls. Tool questions need 2 (call +
  synthesize). Lower from 3 → 2 for simple voice replies (avoid a 3rd speculative call).
- Model floor ~2.3s on this stack (deepseek-flash). `cmd/claude-haiku-4-5-20251001`
  → 403 `MODEL_NOT_IN_PLAN` (Pro-only). `cmd/gpt-5.4-mini` → "No output generated"
  (broken via OmniRoute). `Kimi-K2.6` 5.9s (slower). `MiniMax-M2.5` ≈ deepseek.
- **Measure per-stage before optimizing** — `date +%s%3N` around each curl/agent
  call. The bottleneck moved: STT 2s → agent 2.3-4.5s → TTS 0.7s.

## Perceived-latency win: text-stream + sentence-level audio pipelining

Verified working (contrary to the "per-sentence TTS is worse" note for pure TTS):
streaming the LLM text out via SSE `text` events AND feeding completed sentences
(`match(/^(.*?[.!?]+)([\s\S]*)$/)` on the chunk buffer) to the TTS worker as they
finish, pushing `audio_part` SSE events that the client queues and plays sequentially:

- **First text on screen: 2.79s** (vs waiting for full response)
- **First audio heard: 3.47s** (vs ~7-10s before)
- Agent keeps generating sentence 2 while TTS speaks sentence 1.

Client side: keep `audioParts[]` + `isPlaying` flag; `audio_part` events push to
queue, `playNextAudio()` shifts and plays with `onended` → next. Server: TTS queue
processed serially (`synthBusy` guard) so parts don't overlap; fall back to full-text
TTS if no parts arrived (agent error / no punctuation).

AI SDK 7 streamText note: `result.toolCalls` is a Promise — `await` it. Use
`for await (chunk of result.textStream)` to collect text. For sentence callbacks,
pass `onSentence` through the same IPC channel (prefix `SENT:` lines).
