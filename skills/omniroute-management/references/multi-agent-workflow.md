# Multi-Agent Workflow with OmniRoute Auto-Routing

## Pattern: Parallel Sub-Agents with Auto-Selecting Models

The combination of Hermes `delegate_task` + OmniRoute `auto/smart` routing enables parallel sub-agents that each automatically select the best model for their specific task.

### How It Works
1. Parent agent dispatches N independent tasks via `delegate_task()` (parallel)
2. Each sub-agent runs in isolated context with its own terminal + tools
3. Each sub-agent uses `auto/smart` routing — OmniRoute dynamically selects the optimal model based on the task's content
4. Results auto-merge into parent conversation when all complete

### Example: Code Review + Research in Parallel
```python
delegate_task(
    goal="Review the source code of the project and provide actionable improvements",
    context="Project is at ~/service-dashboard/, React 19 + Vite + Node.js",
    role="leaf"
)
delegate_task(
    goal="Research best practices for modern home lab service dashboards",
    context="Focus on Bulma CSS dark theme, responsive grid, monitoring widgets",
    role="leaf"
)
```

### When to Use
- 2+ independent workstreams (code review + research, debugging + implementation)
- Tasks that benefit from different model strengths (reasoning-heavy + creative)
- Long-running analysis where parallel execution saves time

### Demo Results (2026-07-28)
- Code review agent: 20 API calls, 164s — found command injection, path traversal, auth issues
- Research agent: 14 API calls, 163s — analyzed 8 dashboards, wrote 430-line report
- Wall time: ~2min 45s (vs ~5min if sequential)
- Both auto-selected `big-pickle` (the best available free model)

### Pitfalls
- Sub-agents have NO memory of parent conversation — pass all context via the `context` field
- Sub-agents cannot use `clarify` tool — no interactive user input
- Results are self-reported — verify side-effects (file writes, API calls) from parent
- All sub-agents share the same OmniRoute pool — if one exhausts quota, others are affected
