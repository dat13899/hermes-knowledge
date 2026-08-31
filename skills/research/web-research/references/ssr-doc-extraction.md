# Extracting content from doc / reference sites (curl + HTML-strip)

When the `web_extract` / `web_extract` tool's backend is search-only (e.g. DuckDuckGo ddgs), it returns:
> "DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content."

That means you must fetch and extract the page yourself. This worked reliably on doc sites this session (angular.dev/guide/ssr, /hydration, /incremental-hydration, /ai/*).

## Step 1 — Detect SSR vs client-side SPA BEFORE investing in parsing

Fetch the page and check whether the real content marker-text is present in raw HTML. This determines your whole strategy.

```bash
# Fetch with a real browser UA (many doc sites 403 a curl default UA)
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -sL -A "$UA" "https://angular.dev/guide/ssr" -o page.html

# Is the content IN the HTML (SSR-rendered) or does it need the JS bundle?
grep -o "hydrat\|Server-side rendering\|Server rendering" page.html | sort | uniq -c
ls -la page.html   # large file (400KB+) + content markers present = SSR, strip HTML is enough
```

- **Content markers found in raw HTML** → the page is server-rendered (or pre-rendered). `curl` + HTML-strip gives you the real text. This is the common case for docs sites.
- **No content markers, mostly `<script>` bundles (reference: Angular's framework JS chunks, Next.js `__NEXT_DATA__`, `data-page`) → client-side SPA. Stripping HTML gives you nothing but nav/menu. For SPAs you must instead: use the browser tool (browser-use / CDP), or fetch the docs' `llms.txt` / `llms-full.txt` if it exists (doc sites increasingly ship these for LLMs), or fetch the raw markdown/JSON source, or use the explicit export URL (`export?format=txt` for Google Docs).

## Step 2 — Strip HTML to clean text (Python stdlib, no deps)

```python
import re, html
raw = open('page.html', encoding='utf-8').read()
raw = re.sub(r'<script[^>]*>.*?</script>', ' ', raw, flags=re.S|re.I)   # JS
raw = re.sub(r'<style[^>]*>.*?</style>', ' ', raw, flags=re.S|re.I)    # CSS
raw = re.sub(r'<svg[^>]*>.*?</svg>', ' ', raw, flags=re.S|re.I)        # inline icons
# block-level tags → newline so text doesn't run together
for t in ['h1','h2','h3','h4','p','li','pre','code','tr','br','div']:
    raw = re.sub(r'</?%s[^>]*>' % t, '\n', raw, flags=re.I)
raw = re.sub(r'<[^>]+>', '', raw)          # any remaining tag
raw = html.unescape(raw)
lines = [re.sub(r'[ \t]+',' ',l).strip() for l in raw.split('\n')]
lines = [l for l in lines if l]            # drop empties
text = '\n'.join(lines)
open('page.txt','w',encoding='utf-8').write(text)
print('chars:', len(text))
```

### Strip the persistent nav/sidebar
Doc sites render the same left-nav (~70 lines) before the real content. Strip it in Python before reading, using the last occurrence of a unique nav-exit marker:

```python
def strip_nav(p):
    lines = open(p, encoding='utf-8').read().split('\n')
    idxs = [i for i,l in enumerate(lines) if 'Back to the top' in l]  # or another nav-only marker
    start = idxs[-1]+1 if idxs else 0
    return '\n'.join(lines[start:]).strip()
```

## Pitfalls

- **Watch the page's `<title>`** to confirm you actually fetched the intended page (some routes redirect: `https://angular.dev/ai` → "Get Started", not the content you wanted — check the sub-paths e.g. `/ai/agent-skills`, `/ai/mcp`).
- **Doc content that needs the JS bundle is NOT extractable via curl** — a large HTML file does not guarantee content is SSR'd. Verify the content marker first (Step 1).
- `read_file` truncates ~100K chars; a full page is often 25-30K chars of text, so grab sections with `offset`/`limit` rather than assuming a single read is complete.
- Python here: `python` (3.11) is available; `python3` is missing on this box. Use `python`.
