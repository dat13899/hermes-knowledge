---
name: dispatching-parallel-agents
description: "Dispatch one agent per independent problem domain when facing 2+ independent tasks — concurrent investigation, no shared state, faster resolution."
---

# Dispatching Parallel Agents

## Overview

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

Use when:
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

Don't use when:
- Failures are related (fixing one might fix others)
- Need to understand full system state
- Agents would interfere with each other

## The Pattern

### 1. Identify Independent Domains

Group failures by what's broken:
- File A tests: Tool approval flow
- File B tests: Batch completion behavior
- File C tests: Abort functionality

Each domain is independent.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** One test file or subsystem
- **Clear goal:** Make these tests pass (or investigate this failure)
- **Constraints:** Don't change other code
- **Expected output:** Summary of findings and changes

### 3. Dispatch in Parallel

Issue all dispatches in the same response — they run in parallel. Each goes to a fresh subagent with focused scope.

### 4. Review and Integrate

When agents return:
- Read each summary
- Verify fixes don't conflict
- Run full test suite
- Integrate all changes

## Agent Prompt Structure

Good agent prompts are:
1. **Focused** — One clear problem domain
2. **Self-contained** — All context needed
3. **Specific about output** — What to return

**Bad:**
```
❌ "Fix all the tests" — too broad, agent gets lost
❌ "Fix the race condition" — no context
❌ No constraints — agent might refactor everything
❌ Vague output — you don't know what changed
```

**Good:**
```
✅ Specific scope: "Fix agent-tool-abort.test.ts"
✅ Context: paste error messages and test names
✅ Constraints: "Do NOT change production code"
✅ Specific output: "Return summary of root cause and changes"
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Too broad | One test file or subsystem per agent |
| No context | Paste error messages and test names |
| No constraints | Set clear boundaries on what to change |
| Vague output | "Return summary of root cause and changes" |

## When NOT to Use

- Related failures: investigate together first
- Need full system context: understanding requires entire system
- Exploratory debugging: you don't know what's broken yet
- Shared state: agents would interfere (editing same files)

## Key Benefits

1. **Parallelization** — Multiple investigations happen simultaneously
2. **Focus** — Each agent has narrow scope, less context to track
3. **Independence** — Agents don't interfere
4. **Speed** — N problems solved in time of 1

## Verification

After agents return:
1. **Review each summary** — Understand what changed
2. **Check for conflicts** — Did agents edit same code?
3. **Run full suite** — Verify all fixes work together
4. **Spot check** — Agents can make systematic errors
