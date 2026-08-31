# btdat.io.vn CI/CD + GitHub access notes

Repo: **`dat13899/service-dashboard`** (public, default branch `master`).
Local clone: `C:\Users\datel\service-dashboard`.

## The 502 root cause: CI/CD never runs (branch mismatch)

`btdat.io.vn/stream` returning **502** was traced not to the server, but to the
deploy pipeline never firing. The workflow file `.github/workflows/deploy.yml`
triggers on `main`, but the repo's **default branch is `master`**:

```yaml
name: CI/CD
on:
  push:
    branches: [main]   # ← mismatched: default branch is master
```

Because no push ever lands on `main`, the workflow shows **0 runs** and the
server on `:3000` (fronted by Cloudflare Tunnel) is never restarted → stale/empty
→ 502.

### Diagnostic sequence (verified this session)

```bash
# 1. Repo visibility + default branch (unauthenticated OK for public)
curl -s "https://api.github.com/repos/dat13899/service-dashboard" \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d.get('default_branch'), d.get('private'))"

# 2. Workflow runs — expect 0 here (the smoking gun)
gh run list --repo dat13899/service-dashboard

# 3. Confirm branch mismatch
#    compare repo.default_branch vs the `on: push: branches:` in the workflow
gh api repos/dat13899/service-dashboard --jq '.default_branch'
```

### Fix options

- **Edit the workflow** to trigger on the actual default branch:
  ```yaml
  on:
    push:
      branches: [master]
  ```
- **OR** change the repo's default branch to `main` (Settings → Branches), then
  update the local `.git` checkout path.

Either way, verify after the fix by triggering a run and confirming it fires.

## GitHub auth: keyring token invalid → `gh` 401

Symptom: `gh auth status` shows `The token in keyring is invalid`, and every
`gh` call returns `HTTP 401: Bad credentials`. The stored PAT was revoked/rotated.

Fix (non-interactive, one line):
```bash
printf '%s' '<NEW_PAT>' | gh auth login --with-token
```
Then verify (a successful login alone is not proof the token is valid):
```bash
gh auth status            # expect "✓ Logged in" (keyring)
gh api user --jq '.login' # expect username
gh repo list --limit 5    # expect repos, not 401
```

Token needs at least `repo` and `workflow` scopes for full PR/CI work.

## Repo listing: authenticated vs unauthenticated trap

- `curl https://api.github.com/users/<user>/repos` → **public only** (this user: 12)
- `gh repo list` (authenticated) → **public + private** (this user: 17)

Do not conclude "that's all the repos" from an unauthenticated scan; use
authenticated `gh` when the question is "what can I reach". This user has 5
private repos invisible to anonymous API.
