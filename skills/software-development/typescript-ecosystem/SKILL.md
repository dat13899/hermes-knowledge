---
name: typescript-ecosystem
description: "Use when upgrading TypeScript or AI SDK — version compat."
triggers:
  - "research or upgrade TypeScript version"
  - "TypeScript 7 / tsgo / native compiler"
  - "Vercel AI SDK version or API migration"
  - "typescript-eslint / ts-jest / ts-morph compatibility with TS version"
  - "strict mode migration"
---

# TypeScript Ecosystem

Research + migration knowledge for TypeScript versions and adjacent tooling (Vercel AI SDK). Verify claims against `npm view` + real type-check before advising.

> **AI SDK 7 migration?** See `references/ai-sdk-7-migration.md` — verified breaking changes (system→instructions, maxSteps→stopWhen/isStepCount, parameters→inputSchema, agent→ToolLoopAgent), working tool-calling pattern, and custom-gateway setup.
>
> **Migrating a whole legacy JS project to TS7?** See `references/js-to-ts7-migration.md` — batch-rename-then-fix-by-pattern strategy, the 10 recurring error patterns with one-shot fixes (CSSProperties, motion steps easing, window.marked, setter defaults, EventTarget.style...), and why to defer `strict: true`.
>
> **Browser chat UI hitting the LLM gateway?** See `references/chat-proxy-reasoning-models.md` — CORS proxy route, DeepSeek reasoning `content:""` trap (`reasoning_content` + max_tokens), required `User-Agent` header.

## How to verify a TS version claim (fast, no browser)

```bash
npm view typescript version          # latest
npm view typescript dist-tags --json # beta/rc/next
npm view ai version                  # Vercel AI SDK latest
npm view ai peerDependencies --json  # only zod ^3.25 || ^4.1 — NO TS peer dep
```

Then install + type-check in a scratch dir:
```bash
mkdir -p /tmp/ts-test && cd /tmp/ts-test && npm init -y
npm install typescript@<ver> ai@<ver> zod   # install ALL together — --no-save DROPS typescript
cat > tsconfig.json << 'EOF'
{ "compilerOptions": { "target": "es2022", "module": "esnext",
  "moduleResolution": "bundler", "strict": true, "noEmit": true, "skipLibCheck": true },
  "include": ["src/**/*"] }
EOF
./node_modules/.bin/tsc -p .   # type-check
```

PITFALL: `npm install X --no-save` after installing typescript REMOVES typescript
(npm prunes unlisted deps). Install everything in ONE command or use --save.

## Migrating a JS React project to TS7 — bulk workflow (verified 2026-08-02)

The fast path for a ~11k-line React 19 + Vite codebase (78 .jsx + 17 .js):

1. **Install & config**: `npm i -D typescript@7.0.2 @types/react @types/react-dom` +
   tsconfig with `allowJs: true, checkJs: false, strict: false, jsx: react-jsx,
   moduleResolution: bundler, skipLibCheck: true, types: ["vite/client"]` + script
   `"typecheck": "tsc --noEmit"`. TS7 Go compiler type-checks the whole project in
   **<1s** — cheap to iterate.
2. **Bulk rename first, fix types after**: `find src -name '*.jsx' -exec sh -c 'mv "$1" "${1%.jsx}.tsx"' _ {} \;`
   (same for `.js` → `.ts`, but skip barrel `index.js` files). Vite's bundler
   resolution finds `.tsx` from extensionless imports — **no import edits needed**.
   Then run typecheck and fix the error list file-by-file. Errors cluster by pattern:
   fix one instance, apply the same fix across the file.
3. **Recurring error patterns in a JS→TS migration** (all hit in one session):
   - `useState([])` → `useState<T[]>([])` / `useState<T | null>(null)` (services,
     resources, files...).
   - Destructured function params need an `interface Props {...}` — TS treats
     `({ x })` params as `{}` and errors on every property access.
   - `forwardRef((props, ref) => ...)` needs `forwardRef<HTMLButtonElement, ButtonProps>`.
   - Inline style objects: `import type { CSSProperties } from 'react'` +
     `const s: Record<string, CSSProperties> = {...}`, or `{...} as CSSProperties`
     per object for quick wins.
   - `{v}` rendering a value typed `unknown` → `{String(v)}` (ReactNode fix).
   - `new Error()` + custom fields (`err.status = ...`) → cast
     `as Error & { status: number }` or define a class.
   - Class components: `Component<Props, State>` +
     `static getDerivedStateFromError(error: Error)`.
   - **motion/react `transition={{ ease: 'steps(8)' }}` breaks TS**: motion's
     `Easing` type dropped the `steps(n)` string. Cast the whole object
     `transition={({ ... } as any)}` (NOT `as any` after `}}` — that lands outside
     the JSX expression and silently no-ops).
4. **Bulk mechanical fixes via python/sed**: for N occurrences of the same pattern
   (e.g. 17× `transition={{ ease: 'steps(N)' }}`), write a small python `re.sub`
   script instead of 17 patches. Verify with typecheck after; check the diff didn't
   mangle position (`as any` landing inside a string literal is the classic bug).

PITFALL: `npx tsc --noEmit` with `allowJs` still type-checks imported `.js` files as
`any` — errors only appear after you rename to `.ts/.tsx`. Rename first, then fix.

## Running TS7 code with Node without a build step

`node --experimental-strip-types --input-type=module -e "import('./src/agent.ts').then(...)"`
runs `.ts` files directly (Node ≥22.6). Great for a small TS agent/service — no
tsc emit, no tsx dependency. Needs `"allowImportingTsExtensions": true` +
`"types": ["node"]` in tsconfig (else `process` is unresrtingTsExtensions": true` +
`"types": ["node"]` in tsconfig (else `process` is unresolved; both were needed in
the voice-lab agent).

## AI SDK 7 — API migration cheat-sheet (breaking vs v4/v5)

Verified by type-checking `ai@7.0.47` + `typescript@7.0.2` + `zod` together (0 errors). These are the differences that actually bite when migrating code:

| Old (v4/v5) | AI SDK 7 | Notes |
|---|---|---|
| `maxSteps: 5` | `stopWhen: isStepCount(5)` | `isStepCount`/`isLoopFinished` are exports; bare `stopWhen.maxSteps()` does NOT exist |
| `tool({ parameters, execute })` | `tool({ inputSchema, execute })` | `parameters` → TS error "not assignable to type 'undefined'" |
| `messages: [{role:'system',...}]` | `instructions: '...'` | system role in messages → `AI_InvalidPromptError` |
| `useChat({ model })` | `useChat({ chat: new Chat({...}) })` | transport-based, `UIMessage` parts not `.content` |
| `tool().execute(input)` | `execute(input, options)` | 2-arg signature; single-arg closure still fine |
| OpenAI client | `createOpenAI({ baseURL, apiKey })` | point baseURL at any OpenAI-compatible gateway (e.g. OmniRoute `http://localhost:20128/v1`) |

### AI SDK 7 + a local OpenAI-compatible gateway (OmniRoute pattern)
```ts
import { generateText, tool, isStepCount } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';
const omniroute = createOpenAI({ baseURL: 'http://localhost:20128/v1', apiKey: 'sk-any' });
const model = omniroute('cmd/deepseek/deepseek-v4-flash');
const result = await generateText({ model, instructions: '...', tools: {...}, stopWhen: isStepCount(3) });
```
For a small TS service run it directly: `node --experimental-strip-types --input-type=module -e "import('./src/agent.ts').then(...)"` (see above). No build step needed.olved).

Full worked example: `references/voice-pipeline.md` — a voice-to-voice agent
(whisper STT + AI SDK 7 agent + edge-tts TTS) running on Node without a build step.

## AI SDK 7 agent runtime — errors you WILL hit (beyond type-check)

Type-check passes but runtime throws — these are API changes that only appear
when actually running generateText with tools:

1. **`system` in messages → `InvalidPromptError: System messages are not allowed...
Use the instructions option instead`** — move the system prompt to `instructions:`.
2. **`tool({ parameters })` → type error / execute not assignable** — AI SDK 7
   renamed to **`inputSchema`** (zod schema). `parameters` no longer exists.
3. **Multi-step tool loop: `generateText` with tools does NOT auto-continue** —
   it executes the tool but returns empty `text`. Add **`stopWhen: isStepCount(3)`**
   (import from `ai`) to force the agent loop to continue after tool results.
4. `maxSteps` / `steps` options do NOT exist in AI SDK 7 — replaced by
   `stopWhen` (StopCondition) + `isStepCount()` / `isLoopFinished()` helpers.
5. `@ai-sdk/react` v4: `useChat({ model })` → **`useChat({ chat: new Chat({...}) })`**
   (transport-based). `messages[].content` → UIMessage parts.
6. `createOpenAI({ baseURL, apiKey })` from `@ai-sdk/openai` points at ANY
   OpenAI-compatible endpoint — verified working against OmniRoute
   `http://localhost:20128/v1` with model `oc/deepseek-v4-flash-free`.

## Vercel AI SDK 7 (7.0.x) — API breaking changes (migrate from v4/v5)

AI SDK 7 (latest 7.0.47, `npm view ai version`) is a redesign: chat primitives → agent platform (158 exports incl. realtime/speech/video/transcription). Verified type-checks clean with TS 7.0.2 (`tsc -p .` 0 errors). **No TS peer dep** — only `zod ^3.25 || ^4.1`, engines node ≥22.

Breaking changes hit hard (verified against `node_modules/ai/dist/index.d.ts`):
- `maxSteps: 5` → **`stopWhen: isStepCount(5)`** (`isStepCount`/`isLoopFinished` exported helpers; `stopWhen` is the option name on both `streamText` and `generateText`). There is NO `steps`/`maxSteps` option anymore.
- `tool({ parameters, execute })` → **`tool({ inputSchema, ... })`** (zod schema; `parameters`+`execute` overload gone). `inputSchema` required for typed tool args.
- `useChat({ model })` → **`useChat({ chat })`** where `chat` is a `Chat` instance built on a transport (`ChatInit` includes `transport`, `id`, `messages`, callbacks; `DefaultChatTransport` for HTTP). `messages[].content` is gone → `UIMessage` parts.
- `agent` → **`ToolLoopAgent`** (exported as `Experimental_Agent` alias) with `Agent`/`AgentSettings` types.
- Top-level exports to use: `generateText`, `streamText`, `tool`, `isStepCount`, `Chat`, `DefaultChatTransport`. NOT exported: `agent`, `stopWhen` helper, `maxSteps`.

Tool-calling still works in agent loop: model returns `message.tool_calls` → append `tool` role message with `tool_call_id` → loop until no more calls. Test with `oc/deepseek-v4-flash-free` via OmniRoute (see omniroute-management skill for the 403-UA pitfall).

## TypeScript 7 (7.0.x, "Project Corsa") — as of 2026-08

- **Compiler rewritten in Go** (`tsgo` / native `tsc.exe` ~24MB). npm `typescript` is a thin wrapper (`lib/tsc.js` → `getExePath()` → `@typescript/typescript-<platform>-<arch>/lib/tsc.exe`).
- **~10x faster** than TS6 JS compiler. Measured: `tsc --version` 0.23s; 600-line file type-check 0.29s.
- **`--strict` is DEFAULT** — implicit any now errors out of the box.
- Deprecated-then-removed: `target: es5`, `baseUrl`, `moduleResolution: node` (use `bundler`/`node16`).
- `--checkers N` flag exists for parallel type-checking.
- **ECOSYSTEM BLOCKERS (do not upgrade blindly):**
  - typescript-eslint: does NOT support TS7 (issue #12518 closed, peer range `<6.1.0`) → ESLint crashes.
  - ts-jest, ts-morph, custom AST transformers: broken (need old JS compiler API).
  - Vue/Svelte/Astro template checking: blocked until stable API in **7.1**.
  - Safe to use TS7 now ONLY for pure `tsc` type-check projects (Vite build is fine — esbuild ignores tsc for transpile).
- **Recommendation:** projects using ESLint/Jest/ts-morph stay on TS 6.0.x until 7.1 ships stable API.

## Vercel AI SDK 7 (7.0.x) — API rewrite notes

AI SDK 7 = agent platform, NOT chat primitives. Full API details in `references/vercel-ai-sdk-7.md`.

Key breaking changes vs v4/v5:
- `maxSteps: 5` → `stopWhen: isStepCount(5)` (helper `isStepCount`/`isLoopFinished` from `ai`)
- `tool({ parameters, execute })` → `tool({ inputSchema, ... })` (zod schema renamed)
- `useChat({ model })` → `useChat({ chat: new Chat({...}) })` — transport-based (`DefaultChatTransport`)
- `messages[].content` → `UIMessage` parts API
- Agent = `ToolLoopAgent` / `Experimental_Agent` (not a bare `agent` export)
- 158 exports: realtime, speech, video, transcribe, translate, MCP app bridge...

Compatibility: `ai@7.0.47` + `typescript@7.0.2` type-checks clean (0 errors) — no TS peer dep, engines node >=22.

## References
- `references/vercel-ai-sdk-7.md` — AI SDK 7 export names, API signatures, migration table
