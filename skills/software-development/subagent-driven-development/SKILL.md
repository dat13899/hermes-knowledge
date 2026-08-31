---
name: subagent-driven-development
description: "Execute implementation plans by dispatching a fresh subagent per task, with spec-compliance + code-quality review after each task, and a whole-branch review at the end."
---

# Subagent-Driven Development

Execute plan by dispatching a fresh implementer subagent per task, a task review (spec compliance + code quality) after each, and a broad whole-branch review at the end.

**Core principle:** Fresh subagent per task + task review (spec + quality) + broad final review = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete.

## When to Use

Use when you have an implementation plan with mostly independent tasks and you can stay in the current session (no context switch).

vs. Executing Plans (parallel session):
- Same session, fresh subagent per task (no context pollution)
- Review after each task (spec compliance + code quality), broad review at the end
- Faster iteration (no human-in-loop between tasks)

## Model Selection

Use the least powerful model that can handle each role to conserve cost.

- **Mechanical implementation** (isolated functions, clear specs, 1-2 files): fast, cheap model
- **Integration and judgment tasks** (multi-file coordination, pattern matching): standard model
- **Architecture and design tasks, final whole-branch review**: most capable available model
- **Review tasks**: scale to diff's complexity

**Always specify the model explicitly when dispatching a subagent.** An omitted model inherits your session's model — often the most expensive.

**Turn count beats token price.** Cheap models routinely take 2-3× the turns on multi-step work. Use a mid-tier model as the floor for reviewers and implementers working from prose descriptions.

## Process

### Pre-Flight Plan Review

Before dispatching Task 1, scan the plan once for conflicts:
- tasks that contradict each other or the plan's Global Constraints
- anything the plan explicitly mandates that the review rubric treats as a defect

Present everything you find as one batched question before execution begins. If clean, proceed without comment.

### Per Task Cycle

1. **Create task brief** — run `scripts/task-brief PLAN_FILE N` to extract task to a file
2. **Record base commit** — `git rev-parse HEAD`
3. **Dispatch implementer subagent** with:
   - One line on where this task fits
   - Task brief path ("read this first — it is your requirements")
   - Interfaces and decisions from earlier tasks
   - Report file path and report contract
   - **Explicit model** (cheapest that can handle it)
4. **Handle implementer status:**
   - **DONE:** Generate review package, dispatch task reviewer
   - **DONE_WITH_CONCERNS:** Read concerns, address if about correctness
   - **NEEDS_CONTEXT:** Provide missing context, re-dispatch
   - **BLOCKED:** Assess and adjust (more context, better model, smaller task, or escalate)
5. **Task review** — dispatch reviewer with:
   - Same brief file, report file, review package path
   - Global constraints block (verbatim from plan)
   - **Explicit model** (mid-tier floor)
6. **Handle reviewer findings:**
   - Critical/Important findings → dispatch fix subagent and re-review
   - Minor findings → record in progress ledger for final review
   - "⚠️ Cannot verify from diff" items → you resolve before marking task complete
7. **Mark task complete** — append one line to progress ledger:
   `Task N: complete (commits <base7>..<head7>, review clean)`

### Final Whole-Branch Review

After all tasks:
1. Dispatch final code reviewer with full branch diff package
2. If findings returned, dispatch ONE fix subagent with complete findings list (not one fixer per finding)
3. Re-review fixes
4. Use finishing-a-development-branch skill

## File Handoffs

Everything you paste into a dispatch prompt stays resident in your context. Hand artifacts over as files:

- **Task brief:** `scripts/task-brief PLAN_FILE N` extracts task to a file. The brief is the single source of requirements.
- **Report file:** Name after the brief (`task-N-brief.md` → `task-N-report.md`). Implementer writes full report there.
- **Reviewer inputs:** Three paths — brief file, report file, review package — plus global constraints.
- **Fix dispatches:** Append fix report (with test results) to same report file.

**Review package:** Run `scripts/review-package BASE HEAD` — it prints the file path. BASE is the commit recorded before dispatching the implementer (never `HEAD~1`).

## Durable Progress

Track progress in a ledger file, not just in-memory todos:

- Check for existing ledger: `cat $(git rev-parse --show-toplevel)/.superpowers/sdd/progress.md`
- Tasks listed as complete are DONE — do not re-dispatch
- After clean review, append: `Task N: complete (commits <base7>..<head7>, review clean)`
- After compaction, trust the ledger and `git log` over your own recollection

## Handling Implementer Statuses

| Status | Action |
|--------|--------|
| DONE | Generate review package, dispatch reviewer |
| DONE_WITH_CONCERNS | Read concerns, address if correctness-related |
| NEEDS_CONTEXT | Provide missing context, re-dispatch |
| BLOCKED | More context → better model → smaller task → escalate |

**Never** ignore an escalation or force the same model to retry without changes.

## Handling Reviewer Findings

| Finding | Action |
|---------|--------|
| Critical/Important | Dispatch fix subagent → re-review |
| Minor | Record in progress ledger for final review |
| ⚠️ Cannot verify from diff | You resolve (holder of cross-task context) |

A finding labeled plan-mandated conflicts with the plan — present to human, don't dismiss or fix without asking.

## Key Principles

- Fresh subagent per task — no inherited context pollution
- Explicit model selection — cheap for mechanical, capable for judgment
- File handoffs — keep your context clean
- Durable ledger — survive compaction
- Continuous execution — don't pause between tasks
- Two-stage review: spec compliance → code quality
- ONE fix subagent per review wave, not one per finding
