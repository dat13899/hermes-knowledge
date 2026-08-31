---
name: full-stack-code-audit
description: >
  Comprehensive audit of full-stack projects — security analysis, performance
  review, code quality, project structure, and frontend patterns with actionable
  severity-ranked findings. Backend (Node/Python/PHP) + Frontend (React/Vanilla)
  in a single pass.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [code-review, security, performance, architecture, full-stack]
    related_skills: [code-review-agent, requesting-code-review, large-file-refactoring, systematic-debugging]
---

# Full-Stack Code Audit

Structured methodology for reviewing an entire project's source code — backend,
frontend, configuration, and project structure — and producing actionable,
severity-ranked improvements.

## When to Use

- User asks "review source code", "audit this project", "tìm lỗi security",
  "cải thiện code quality"
- Taking over an unfamiliar codebase that needs assessment
- Before or after a major refactoring
- When deploying a home-lab project publicly

**Not for:** pre-commit verification (`requesting-code-review`),
HTML/CSS-specific review (`code-review-agent`), or debugging a specific bug
(`systematic-debugging`).

## Workflow

### Phase 1 — Discover the project

```yaml
Steps:
  1. Find the root: look for package.json, requirements.txt, setup.py,
     composer.json, or a known path from the user
  2. List top-level structure: search_files(target='files') with no filter
  3. Identify:
     - Backend entry points (server.js, app.py, index.php, main.go)
     - Frontend dir (src/, app/, public/)
     - Config files (package.json, .env.example, vite.config.*, tsconfig.*)
     - Build artifacts to ignore (node_modules, dist, .git)
     - Database/schema files
     - Tests directory
  4. Read README, DESIGN.md, or docs/ for project intent
```

### Phase 2 — Read key source files

```yaml
Priority order:
  1. # Backend entry point (server.js, app.py, etc.) — read ALL lines
  2. # Frontend entry (App.jsx, main.jsx, index.html)
  3. # API layer (services/api.js, routes/)
  4. # Core components + pages (largest files first)
  5. # Shared components (ErrorBoundary, Toast, providers)
  6. # Hooks / custom logic
  7. # Build config (vite.config.js, webpack, tsconfig)
  8. # CSS / theme files (global.css, theme files)
  9. # Package manifests (package.json - both root + frontend)
 10. # Tests (if any)
```

- Use `read_file` for content exploration (pagination via offset/limit)
- Use `search_files(target='content')` to find specific patterns across files
- For very large files (>500 lines), read in sections
- Always check `.gitignore` — it reveals the project's hygiene level

### Phase 3 — Analyze across dimensions

Audit **every** file through these lenses:

#### 🔴 Security
- **Command injection**: `execSync`/`exec` with string interpolation of user input
  ```js
  // BAD
  execSync(`yt-dlp "${url}"`, ...)
  // GOOD
  execFile('yt-dlp', ['--dump-json', url], ...)
  ```
- **Path traversal**: file reads that don't resolve against a safe base
- **No auth**: open API endpoints on a public-facing dashboard
- **No rate limiting**: start/stop APIs unprotected
- **Hardcoded secrets**: passwords, API keys, tokens in source
- **SSRF via proxy**: `/proxy/:port` endpoints that can hit internal services
- **File listing**: directory listing APIs with no sandbox

#### 🟡 Performance
- **Blocking I/O in request handlers**: `execSync`, `readFileSync`,
  `writeFileSync` inside HTTP routes block the event loop for ALL clients
- **No caching**: repeat expensive ops (netstat, tasklist, port scans) on every request
- **Large buffers**: `maxBuffer` > 256KB should be justified
- **No streaming for large responses**: loading entire files into memory
- **Sync file ops before response**: converting docx → pdf synchronously

#### 🟢 Code Quality
- **Monolithic files**: >500 lines doing routing + business logic + I/O
- **Inconsistent error handling**: try/catch that silently swallow errors
- **Race conditions**: mutable globals (`let _ytStream = null`)
- **No input validation**: API params used directly
- **Callback hell vs async/await**: mixed patterns
- **Hardcoded paths**: machine-specific directory paths
- **Dead code**: unused variables, commented-out blocks, legacy fallbacks

#### 🟣 Project Structure
- **Dual systems**: two implementations of the same feature
- **Bad .gitignore**: ignores lockfiles, ignores critical configs
- **Missing lockfiles**: no `package-lock.json` or equivalent
- **No `.env`**: machine-specific config baked into source
- **No process manager**: node server without PM2/supervisor
- **Poor separation**: backend + frontend + docs + scripts all in root

#### 🔵 Frontend Patterns
- **Dependency cycles**: hooks that depend on state they also modify
- **Direct DOM manipulation**: `document.body.classList` in React components
- **Missing key props**: in lists
- **No PropTypes / TypeScript**: loose component contracts
- **Inline styles over CSS**: when CSS variables exist
- **CDN dependencies**: external resources with no fallback
- **Stale closures**: `useCallback`/`useEffect` with stale deps
- **SSR hydration issues**: `typeof window` checks

### Phase 4 — Structure the output

Rank every finding by severity and present in a consistent format:

```markdown
### 🔴 CRITICAL: [Title — reason it matters]

**File:** `path/to/file:line` — **short explanation**

```code
specific vulnerable line
```

<details>
<summary>💡 Fix</summary>

Safe alternative code
</details>

#### 🟡 HIGH: [Title]

...

#### 🟡 MEDIUM: [Title]

...

#### 🟢 LOW: [Title]

...
```

**Severity guide:**
| Severity | Meaning | Response |
|----------|---------|----------|
| 🔴 CRITICAL / P0 | Remote exploit possible, data loss, crash | Fix immediately before next deploy |
| 🟡 HIGH / P1 | Significant quality/performance issue | Fix within 1-2 sprints |
| 🟡 MEDIUM / P2 | Should fix, not urgent | Add to backlog |
| 🟢 LOW / P3 | Nice-to-have, cosmetic, optional | Monitor |

### Phase 5 — Also highlight what's GOOD

Every review should call out things done well. Developers need to know what
to keep doing. Use ✅ prefix.

```markdown
✅ TỐT: Lazy loading pages
✅ TỐT: Toast system với Context API đúng pattern
```

## Vietnamese Delivery

When the user's language is Vietnamese, deliver the review in Vietnamese:

- Use natural Vietnamese tech terms (bảo mật, hiệu năng, chất lượng mã nguồn)
- Keep code examples in English (they're universal)
- Use Vietnamese for explanations, severity labels (CRITICAL, HIGH remain English)
- Start with a summary table, then go deep per dimension

## Pitfalls

- **Don't only read the backend** — full-stack means both backend + frontend
- **Don't skip .gitignore** — reveals project hygiene
- **Don't forget package.json** — dependency choices reveal security posture
- **Don't stop at the first finding** — go through ALL dimensions systematically
- **Don't make claims without evidence** — include the exact line and code snippet
- **Don't assume auth is out of scope** — even home-lab projects may go public
- **Don't praise without specificity** — "good job" is useless; "lazy loading pages is good because..." is useful
- **Don't fabricate findings** — cite real code, real lines. If you can't find an issue, say the code is clean in that dimension.

## Reference Files

- `references/btdat-dashboard-audit.md` — the full audit from the session that created this skill (real-world example)

## Related Skills

- `code-review-agent` — HTML/CSS-specific review (narrower)
- `requesting-code-review` — pre-commit verification before git push
- `large-file-refactoring` — breaking monolithic files into modules
- `systematic-debugging` — root-cause debugging approach
