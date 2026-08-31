# Vite Content Hash + Cloudflare Cache Bypass

## Problem

Cloudflare caches `index-ABC123.css` at edge. Server fix is deployed, but Cloudflare keeps serving the **404 response** from before the fix. Even after the server correctly serves the file, CF edge cache returns the stale 404 because the URL (including hash) hasn't changed.

Direct Cloudflare cache purge requires API token we don't have. Manual purge via dashboard works but is slow.

## Solution: Change the content hash

Vite generates hashes (`index-CJpm7VkC.css`) based on file content. To force a new hash (bypassing the stale CF cache entry), you must change the **actual CSS content** — not just comments.

### ❌ Does NOT change hash
- Adding/removing CSS comments (`/* ... */`)
- Adding blank lines
- Changing spacing/indentation

### ✅ DOES change hash
- Adding a real CSS rule (even `.v2-trigger { margin: 0 }`)
- Changing a selector name
- Changing a property value
- Adding/removing any non-comment content

### Workflow

```bash
# 1. Add a benign CSS rule to trigger hash change
echo '.v2-cache-bypass { margin:0 }' >> frontend/src/styles/components.css

# 2. Rebuild (hash will change)
cd frontend && npm run build

# 3. Verify new hash
grep -o 'index-[A-Za-z0-9]*\.css' ../dist/index.html
# Old: index-CJpm7VkC.css → New: index-CALdfVI2.css

# 4. Restart server
fuser -k 3000/tcp
cd .. && node server.js &

# 5. Verify both local and CDN
for path in "/assets/index-NEWHASH.css" "/assets/index-OLDHASH.css"; do
  echo "local: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000$path)"
  echo "cdn:   $(curl -s -o /dev/null -w '%{http_code}' https://btdat.io.vn$path)"
done
# New hash → 200 on both. Old hash → 404 on both (expected — old file doesn't exist).

# 6. Revert the trigger rule (optional — small CSS rule is harmless)
git checkout -- frontend/src/styles/components.css
```

## After hash rotation

The old hash URL (`index-CJpm7VkC.css`) will forever return 404. That's correct — it was the stale cached URL. The new hash (`index-CALdfVI2.css`) is a fresh URL that Cloudflare has never seen → no stale cache → 200 OK.

## Diagnosis: verify which assets are cached stale

```bash
# Check which assets index.html references vs which are reachable
for path in $(grep -oP '(?:src|href)="(/assets/[^"?]+)' dist/index.html | cut -d'"' -f2 | sort -u); do
  local_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$path")
  cdn_code=$(curl -s -o /dev/null -w "%{http_code}" "https://btdat.io.vn$path")
  echo "$local_code / $cdn_code  $path"
done
# If LOCAL=200 but CDN=404 → CF edge cache serving stale 404 → rotate hash
# If LOCAL=404 → server handler is broken → fix server code, then rotate hash
```

## Alternative: Add cache-busting query param

For non-hashed assets (global.css, theme.js), adding `?v=N` to each deploy helps. But for Vite-hashed assets, query params don't help because CF caches by URL path, and the hash already changes per build. The real fix is **ensure the asset handler serves all file types** — if it only serves `.js`, hashed `.css` will always 404 on first access, and CF caches that 404.
