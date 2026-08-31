# CSS Consistency Audit — Multi-page liquid glass site

When user says "style trang này khác hẳn trang chủ", do a quantified audit before touching any CSS.

## Audit commands

### 1. Count glass vs non-glass CSS variables per page

```bash
for f in index.html dashboard.html documents.html utilities.html random-widget.html; do
  echo "=== $f ==="
  echo -n "  --glass-bg: ";    grep -co 'var(--glass-bg)'    "$f" || echo 0
  echo -n "  --glass-border: "; grep -co 'var(--glass-border)' "$f" || echo 0
  echo -n "  --glass-shadow: "; grep -co 'var(--glass-shadow)' "$f" || echo 0
  echo -n "  --border (leak): "; grep -co 'var(--border)'     "$f" || echo 0
done
```

Key interpretation:
- `--border` count > 0 on a page = CSS variables not migrated to glass-border
- `--glass-border` count low = page uses custom borders instead of theme
- `--glass-shadow` = 0 = no glass depth at all

### 2. Inline CSS size (redundant with global.css)

```bash
for f in *.html; do
  sz=$(perl -0777 -ne 'print length($1) if /<style>(.*?)<\/style>/s' "$f" 2>/dev/null)
  echo "$f: ${sz:-0}c"
done
```

Pages with >2000c inline CSS likely have duplicated global.css components.

### 3. Check glass-card class usage

```bash
for f in *.html; do echo "$f: $(grep -c 'glass-card' "$f") glass-card refs"; done
```

- 0 refs = page doesn't use the reusable glass component at all
- Low counts (<3) = only partial adoption

### 4. Check redundant component CSS (already in global.css)

Check if inline `<style>` blocks redefine global components:

```bash
for comp in 'blob-container' 'toast-container' 'reading-progress' 'kb-hint' 'drop-zone' 'skeleton' 'spinner' '::-webkit-scrollbar' 'font-controls'; do
  for f in *.html; do
    c=$(grep -c "$comp" "$f")
    [ "$c" -gt 0 ] && echo "$f: $comp x$c"
  done
done
```

If a page defines its own `@keyframes shimmer` or `.toast` CSS while global.css already has it — that's duplication.

## Plan structure (Phase-based)

When audit reveals multiple issues, present a numbered Phase plan:

```
Phase 1 — Fix all var(--border) → var(--glass-border)  [visual impact, safe]
Phase 2 — Remove redundant inline CSS (duplicates global.css)
Phase 3 — Add glass-card / glass class to missing pages
Phase 4 — Extract shared JS (navbar fetch, toast)
Phase 5 — Page-specific optimization
Phase 6 — Remove inline styles → CSS classes
```

## Full sweep rule

**NEVER apply glass fixes incrementally (3+ small patches).** User escalates frustration:
"để ý style ý" → "chưa giống" → "khác hẳn" → "trả lại code đi"

When you finally do the complete sweep, the user says "ok được rồi".

Correct approach for one page: patch ALL `--border`, ALL border-radius, ALL box-shadow, ALL hover states in ONE edit.

## How to revert (when user says "trả lại code đi")

```bash
git log --oneline -10 public/<page>.html   # find commit before your changes
git checkout <commit-hash> -- public/<page>.html   # restore single file
git add -A && git commit -m "revert <page> to pre-<feature>"
git push
```

Don't use `git revert` (creates inverted commit). Use `git checkout` + new commit.
