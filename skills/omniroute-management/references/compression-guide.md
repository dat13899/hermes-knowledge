{success: true, data: {web: [{title: "OmniRoute/docs/guides/FEATURES.md at release/v3.8.49...", url: "https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.49/docs/guides/FEATURES.md", description: "RTK+Caveman stacked compression saves 15-95% tokens, smart auto-fallback, MCP/A2A, multimodal APIs, Desktop/PWA."}]}}

# OmniRoute Compression — Key Facts

From FEATURES.md (v3.8.49) + COMPRESSION_GUIDE.md (v3.8.40):

## Pipeline Architecture

```
Client Request
  → Compression Strategy Selector
    → Combo override? → Use combo setting
    → Auto-trigger threshold? → Use auto mode
    → Default mode? → Use global setting
    → Off? → Skip compression
  → Selected Compression Mode
    → Off: No compression
    → Lite: Safe whitespace/formatting cleanup (~15%)
    → Standard: Caveman-speak filler removal (~30%)
    → Aggressive: History aging + summarization (~50%)
    → Ultra: Heuristic pruning + code-block thinning (~75%)
    → RTK: Command-aware terminal/tool-output filtering (60-90% upstream range)
    → Stacked: Ordered multi-engine pipeline, usually RTK then Caveman (78-95% eligible range)
  → Compressed Request → Provider
```

## Mode Details

### Lite (~15%, <1ms latency)
- collapseWhitespace: Merge blank lines and trailing spaces
- dedupSystemPrompt: Remove duplicate system messages
- compressToolResults: Compress verbose tool/function outputs
- removeRedundantContent: Strip repeated instructions

### Caveman (~30%)
- Filler word removal: "essentially", "basically", "I think", "you know"
- Sentence shortening without changing meaning
- Verbosity reduction while preserving intent
- Code blocks NEVER touched (preservePatterns)

### RTK (60-90%)
- Terminal output filtering: git logs, build output, test results
- Command-aware: understands shell output structure
- Preserves errors/stack traces (important debugging info)
- Level: minimal → full (aggressiveness control)

### Stacked (78-95%)
- Ordered pipeline: RTK runs first, then Caveman
- RTK strips tool-output noise
- Caveman compresses remaining conversation text
- Best for: coding agents with heavy tool use

## Auto-Trigger

When `autoTriggerTokens` > 0:
- Compression activates only when context exceeds threshold
- Short sessions remain untouched
- Recommended: 8000 tokens for coding agents

## Per-Combo Override

Each combo can have its own compression mode in `comboOverrides`:
```json
{
  "my-coding-combo": "stacked",
  "my-fast-combo": "off"
}
```
