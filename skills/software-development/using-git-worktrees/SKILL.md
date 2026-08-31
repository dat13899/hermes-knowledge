---
name: using-git-worktrees
description: "Create isolated git worktree workspaces for feature branches. Detects existing isolation first, uses native tools then git fallback, verifies directory is ignored."
---

# Using Git Worktrees

## Overview

Ensure work happens in an isolated workspace. Prefer your platform's native worktree tools. Fall back to manual git worktrees only when no native tool is available.

**Core principle:** Detect existing isolation first. Then use native tools. Then fall back to git. Never fight the harness.

## Step 0: Detect Existing Isolation

Before creating anything, check if you're in an isolated workspace:

```bash
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null && pwd -P)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Check for submodule:** `git rev-parse --show-superproject-working-tree 2>/dev/null`

If GIT_DIR != GIT_COMMON (and not a submodule): you are in a worktree. Skip to Step 2.  
If GIT_DIR == GIT_COMMON (or in submodule): normal repo. Ask for consent before creating worktree.

## Step 1: Create Isolated Workspace

### 1a. Native worktree tools (preferred)
If you have a command like `EnterWorktree` or a `--worktree` flag, use it.

### 1b. Git worktree fallback
Only use if Step 1a does not apply.

**Directory priority:** explicit user preference > `.worktrees/` (hidden) > `worktrees/` (visible)

**Safety: MUST verify directory is gitignored before creating**
```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```
If not ignored, add to .gitignore and commit.

**Create the worktree:**
```bash
path="./$LOCATION/$BRANCH_NAME"
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

If permission error: tell the user and work in the current directory.

## Step 2: Project Setup

Auto-detect and run appropriate setup:
- package.json → npm/yarn install
- Cargo.toml → cargo build
- requirements.txt/pyproject.toml → pip/poetry install
- go.mod → go mod download

## Step 3: Verify Clean Baseline

Run project-appropriate test suite:

```bash
npm test / cargo test / pytest / go test ./...
```

If tests fail, report and ask whether to proceed. If they pass, report ready.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo |
| Native tool available | Use it |
| No native tool | Git fallback |
| .worktrees/ or worktrees/ exists | Use it, verify ignored |
| Directory not ignored | Add to .gitignore + commit |
| Permission error | Work in place |
| Tests fail at baseline | Report + ask permission to proceed |

## Common Mistakes

- **Fighting the harness:** Using git worktree when the platform already provides isolation
- **Skipping detection:** Creating nested worktree inside existing one
- **Skipping ignore verification:** Worktree content gets tracked
- **Assuming directory location:** Follow explicit instructions first

## Red Flags

Never create a worktree when Step 0 detects existing isolation. Never use git worktrees when a native tool is available. Never skip baseline test verification.
