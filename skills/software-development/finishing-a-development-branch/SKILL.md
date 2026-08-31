---
name: finishing-a-development-branch
description: "Guide completion of development work by verifying tests, detecting environment, and presenting structured options for merge, PR, keep, or discard."
---

# Finishing a Development Branch

## Overview

Guide development completion with a clear workflow. Verify tests → detect environment → present options → execute choice → clean up.

**Core principle:** Verify tests → Detect environment → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, run the test suite:**
```bash
npm test / cargo test / pytest / go test ./...
```
If tests fail: Show failures and stop. DO NOT proceed.

If tests pass: Continue to Step 2.

### Step 2: Detect workspace state

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

| State | Menu | Cleanup |
|-------|------|---------|
| GIT_DIR == GIT_COMMON (normal repo) | Standard 4 options | No cleanup |
| GIT_DIR != GIT_COMMON, named branch | Standard 4 options | Provenance-based |
| GIT_DIR != GIT_COMMON, detached HEAD | Reduced 3 options | No cleanup |

### Step 3: Determine the base branch

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```
Or ask: "This branch split from [base] - is that correct?"

### Step 4: Present options

**Normal repo and named worktree - present exactly these 4:**
```
Implementation complete. What would you like to do?
1. Merge back to <base> locally
2. Push and create a Pull Request
3. Keep as-is (I'll handle it)
4. Discard this work
```

**Detached HEAD - present exactly these 3:**
```
Implementation complete. Detached HEAD detected.
1. Push as new branch and create a Pull Request
2. Keep as-is (I'll handle it)
3. Discard this work
```

Don't add explanation. Keep options concise.

### Step 5: Execute choice

**Option 1 - Merge locally:**
```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
git checkout <base-branch> && git pull
git merge <feature-branch>
# Verify tests on merged result
<test command>
# then cleanup (Step 6) and delete branch
git branch -d <feature-branch>
```

**Option 2 - Push and PR:**
```bash
git push -u origin <feature-branch>
``` 
Do NOT clean up the worktree.

**Option 3 - Keep as-is:**
Report keeping the branch, preserve worktree.

**Option 4 - Discard:**
Require typed confirmation: "discard". On confirm: cleanup (Step 6) and force-delete branch.

### Step 6: Cleanup workspace

Only for Options 1 and 4.

If GIT_DIR == GIT_COMMON: normal repo, no cleanup needed.

If worktree path under `.worktrees/` or `worktrees/`:
```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
git worktree remove "$WORKTREE_PATH" && git worktree prune
```

Otherwise: hoc environment owns this workspace - do NOT remove.

## Quick Reference

| Option | Merge | Push | Keep Branch | Cleanup Worktree |
|--------|-------|------|-------------|------------------|
| 1. Merge Locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| 4. Discard | - | - | - | yes (force delete) |

## Red Flags

Never: Proceed with failing tests. Merge without verifying result. Delete work without typed confirmation. Force-push without explicit request. Remove a worktree before merge confirmation. Run git worktree remove from inside the worktree. Always: Verify tests before offering options. Present exactly 4 options (or 3 for detached). Get typed confirmation for discard.
