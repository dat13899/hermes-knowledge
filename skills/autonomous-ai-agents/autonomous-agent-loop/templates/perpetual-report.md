# Perpetual-Build Report Template

Use this exact format when the autonomous loop is in **perpetual-build** mode
(no eval, no score, no done).

```
🌀 Hermes Loop #[iteration]
Goal: [one-line description of what you just built]
Built: [short summary — 1-2 sentences]
Todo: [ideas for next iteration, 2-3 items]
```

### Rules

- Language: Vietnamese (per the standard autonomous loop convention)
- Always start with the `🌀 Hermes Loop #N` header
- Goal is past-tense or immediate — what did you just do
- Built is short — bullet-style single line
- Todo is bullet-style, NOT numbered TODO items, just raw ideas
- Never include score, critic, or done status
- The system delivers your final response automatically — do NOT use send_message or equivalent
- If there's genuinely nothing to report (e.g. cron ran but state says `done: true`),
  respond with exactly `[SILENT]` — nothing else.
