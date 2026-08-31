# Vercel AI SDK 7 — API Reference (verified 2026-08-01, v7.0.47)

Source: `npm install ai@7.0.47 typescript@7.0.2 zod` + reading `node_modules/ai/dist/index.d.ts` + real `tsc -p .` type-check. Type-checked CLEAN (0 errors) with TS 7.0.2.

## Packages & versions (2026-08-01)
| Package | Version | Note |
|---|---|---|
| `ai` | 7.0.47 (latest) | core; engines node >=22 |
| `@ai-sdk/react` | 4.0.50 | `useChat`, `Chat`, `useCompletion`, `useObject` |
| `@ai-sdk/openai` | 4.0.27 | provider |
| `zod` | ^3.25.76 \|\| ^4.1.8 | ONLY peer dep — no TypeScript peer dep |

`ai` has 158 top-level exports including realtime, speech, video, transcription, translation, MCP app bridge.

## Core functions (top-level exports)
- `generateText({ model, prompt, system, tools, toolChoice, stopWhen, ... })` → `{ text, steps, ... }`
- `streamText({ model, prompt, system, tools, toolChoice, stopWhen, ... })` → stream result with `steps`
- `tool({ description, inputSchema })` — zod schema field is **`inputSchema`** (was `parameters` in v4/v5)
- Multi-step / agent loop control: `stopWhen: isStepCount(3)` or `stopWhen: isLoopFinished()`
  - `isStepCount(n)` and `isLoopFinished()` are exported helpers
  - `maxSteps` / `steps` options DO NOT exist in v7 call options (verified via type errors)

## Agents (v7 new)
- `ToolLoopAgent` (exported) — reasoning loop agent; also aliased `Experimental_Agent` / `Experimental_AgentSettings`
- No bare `agent` function export — `import { agent }` fails with TS2724 "no exported member named 'agent'" (did you mean `Agent`?)

## Chat / UI (breaking vs v4/v5)
- `useChat({ chat: new Chat({...}) })` — requires a `Chat` instance, NOT `{ model }`
- `ChatInit` (from `ai`): `{ id?, messages?, transport?, generateId?, onError?, onToolCall?, onFinish?, onData?, sendAutomaticallyWhen? }`
- `DefaultChatTransport` / `HttpChatTransport` / `DirectChatTransport` — transport-based design
- `UIMessage` replaces old message shape: **no `.content` string** — use parts API (`UIMessage<unknown, UIDataTypes, UITools>`)
- `useChat` return has NO `input`/`handleInputChange`/`handleSubmit` on `UseChatHelpers<UIMessage>` — those moved to Chat transport API

## Provider pattern
```ts
import { openai } from '@ai-sdk/openai';
const model = openai('gpt-4o');
```

## Verified working TS snippet (type-checks with TS7 strict)
```ts
import { generateText, streamText, tool, isStepCount } from 'ai';
import { z } from 'zod';

const weatherTool = tool({
  description: 'Get weather for a city',
  inputSchema: z.object({
    city: z.string().describe('City name'),
    unit: z.enum(['celsius', 'fahrenheit']).default('celsius'),
  }),
});

async function ask() {
  const result = await generateText({
    model: 'gpt-4o',
    prompt: 'Weather in Hanoi?',
    tools: { weather: weatherTool },
    stopWhen: isStepCount(3),
  });
  return result.text;
}
```

## Migration cheat-sheet v4/v5 → v7
| v4/v5 | v7 |
|---|---|
| `maxSteps: 5` | `stopWhen: isStepCount(5)` |
| `tool({ parameters, execute })` | `tool({ inputSchema })` (execute optional) |
| `useChat({ model, api })` | `useChat({ chat: new Chat({ transport: ... }) })` |
| `message.content` | `UIMessage` parts |
| — | `ToolLoopAgent` / `Experimental_Agent` for agents |
