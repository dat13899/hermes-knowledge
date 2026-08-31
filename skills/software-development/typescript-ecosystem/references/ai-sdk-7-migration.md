# Vercel AI SDK 7 — API Migration Notes (verified 2026-08-01)

Verified with `ai@7.0.47` + `typescript@7.0.2` + `@ai-sdk/openai@4.0.27` — type-check 0 errors,
working tool-calling agent against OmniRoute gateway.

## Package facts
- `ai@7.0.47` latest. Peer deps: ONLY `zod ^3.25 || ^4.1` — **no TypeScript peer dep**, so TS7 works side-by-side (verified).
- `@ai-sdk/react@4.0.50`, `@ai-sdk/openai@4.0.27`, engines Node ≥22.
- AI SDK 7 core exports: `generateText`, `streamText`, `tool`, `isStepCount`, `ToolLoopAgent` (alias `Experimental_Agent`), `Chat`/`ChatInit`/`DefaultChatTransport` (transport-based chat, new in v7).

## Breaking changes vs v4/v5 (the ones that actually bite)
| Old (v4/v5) | New (v7) | Error you get if you keep old |
|---|---|---|
| `system:` message in messages[] | `instructions:` option on generateText/streamText | `AI_InvalidPromptError: System messages are not allowed in the prompt or messages fields. Use the instructions option instead.` |
| `maxSteps: N` | `stopWhen: isStepCount(N)` (import `isStepCount` from 'ai') | `maxSteps` silently ignored |
| `tool({ parameters, execute })` | `tool({ inputSchema, execute })` | type error: `parameters` not assignable |
| `agent` | `ToolLoopAgent` / `Experimental_Agent` | `Module '"ai"' has no exported member 'agent'` |
| `useChat({ model, ... })` | `useChat({ chat: new Chat({...}) })` — transport-based | useChat signature changed |

## streamText pitfall (verified 2026-08-01)
- `result.toolCalls` is a **Promise** in streamText — must `await result.toolCalls` before iterating. Without await: `TypeError: result.toolCalls is not iterable` / TS2488.
- Collect text via `for await (const chunk of result.textStream)`, then `const calls = await result.toolCalls`.
- `stopWhen: isStepCount(N)` — each step = 1 LLM call. Tool questions cost 2 steps (call + synthesize). Lower N to 2 for speed.

## Sentence-split streaming pipeline (verified 2026-08-01 — voice agent)
Split streamed text into sentences and TTS each one as it completes → first audio heard in **~3.5s** vs ~7-10s waiting for full text. Pattern:
```ts
let buf = '';
for await (const chunk of result.textStream) {
  buf += chunk; onText(chunk);
  let m;
  while ((m = buf.match(/^(.*?[.!?]+)([\s\S]*)$/))) { onSentence(m[1]); buf = m[2]; }
}
if (buf.trim()) onSentence(buf);  // leftover without terminal punctuation
```
- Server: each `onSentence` → TTS (persistent worker) → SSE `audio_part` event. Client queues parts and plays sequentially (`onended` → next).
- Pipeline measured: agent first text 2.79s, first audio 3.47s (vs 7-10s before).
- **Per-sentence TTS is NOT faster per-se** (each request has network overhead ~0.7s warm) — the win is *parallelism*: sentence 1 speaks while LLM still generates sentence 2.

## Child-process IPC pattern for TS7 agents (verified 2026-08-01)
Server (`.mjs`) can't import `.ts` directly → spawn node with strip-types and stream via stdout prefixes:
```js
const p = spawn('node', ['--experimental-strip-types', '--input-type=module', '-e', script], { cwd: __dirname });
// script: process.stdout.write('TEXT:' + chunk + '\n')  → server parses lines by prefix
//         process.stdout.write('DONE:' + JSON.stringify({...}) + '\n')
```
Parse `TEXT:` (stream chunks), `SENT:` (sentence), `DONE:` (final JSON) line prefixes. Keeps AI SDK 7 + TS7 agent working behind a plain Node http server.eed.
- Latency per model via OmniRoute (2026-08-01, single call): deepseek-v4-flash ~2.3s, MiniMax-M2.5 ~2.3s, Kimi-K2.6 ~5.9s, haiku = 403 not-in-plan. ~2.3s is the floor on this setup.

## Tool calling pattern that works (verified)
```ts
import { generateText, tool, isStepCount } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';

const omniroute = createOpenAI({ baseURL: 'http://localhost:20128/v1', apiKey: 'x' });
const model = omniroute(process.env.OMNI_MODEL || 'cmd/deepseek/deepseek-v4-flash');

const svcTool = tool({
  description: '...',
  inputSchema: z.object({}),
  execute: async 

const result = await generateText({
  model,
  instructions: '...',      // NOT system message
  messages: [{ role: 'user', content: text }],
  tools: { service_status: svcTool },
  toolChoice: 'auto',
  stopWhen: isStepCount(3), // maxSteps replacement
  maxOutputTokens: 300,
});
// result.text = final answer after tool loop; result.toolResults available
```

## Pointing AI SDK at a custom OpenAI-compatible gateway
```ts
const client = createOpenAI({ baseURL: 'http://localhost:20128/v1', apiKey: 'any' });
```
Works for OmniRoute (and any OpenAI-compatible proxy). `generateText` streams via SSE internally.

## Gotchas
- AI SDK 7 does auto-execute tools but does NOT auto-loop unless `stopWhen` is set — tool results
  come back but final text can be empty without a loop condition.
- Tool execute can return a plain string; result is surfaced as `result.text` after the loop.
- `toolChoice: 'auto'` + a model that returns empty `content` (reasoning-only models like
  deepseek-v4-flash) → final text may be empty if the model never emits a text answer. Add
  `stopWhen` and prompt the model to answer in Vietnamese/user language.
