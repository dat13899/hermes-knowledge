# Dashboard Warning Lights — Data Sources & Diagnosis Architecture

Research done 2026-08-17 for the VTTS Drive "AI chẩn đoán taplo xe" feature (btdat.io.vn/vtts). User plan: vision model scans dashboard photo → checks RAG (brand = parent node, icon data = children) → if no exact match, list top-5 nearest for user to pick.

## Data sources (viability ranked)

| Source | Data | Images | Scrape-ability |
|---|---|---|---|
| **warninglightfinder.com** | 113+ icons, sections by Red/Amber group + system (Engine/Brake/Safety/Reminder) | Per-icon images | ⭐⭐⭐⭐⭐ best text source |
| **vehiclefreak.com** guide (113 symbols) | Same style, ~360KB page | Sprite sheets (Icons-30.png, Icons-28.png) | ⭐⭐⭐⭐ |
| **VinFast VF9 Owner's Manual Condensed PDF** — https://vinfastowners.org/manuals/VF9_2023-2024-2025_Owners_Manual_Condensed.pdf | Official, 466 pages | Yes | Warning-light mentions SCATTERED (pages 46, 79, ...), NO consolidated table → needs text mining across pages |
| **OBD Advisor** (obdadvisor.com/dash-lights/) | 1,700+ symbols, 24 brands | Infographic images (banner-*.jpg), NOT per-icon text | ⭐⭐ content is images, hard to extract text per icon |
| **ISO 2575** (http://auto.gosstandart.info/data/documents/ISO-2575.pdf) | International symbol standard | Yes | Reference only, not brand-specific |
| **SAE J2395/J2400** | US warning standards | — | Reference only |
| **Wikipedia "Dashboard"** | General symbol table | Some | Generic |
| **om.vinfastauto.com** | Official VN manual portal | — | SPA shell (8.4KB), needs browser |

## Scraping pitfalls (verified)

- `web_extract` with ddgs backend is SEARCH-ONLY → cannot extract URLs. Use curl or browser_exec.
- **obdadvisor.com returns Cloudflare 403 to curl** — but `browser_exec` (Browser Use CDP) reads it fine.
- warninglightfinder/vehiclefreak use ewww lazy-load images → real URL is in `data-src-img` / `data-srcset-img` attributes, NOT `src`.
- pymupdf: `import pymupdf` (the `fitz` name is deprecated in 1.28.2+).

## Architecture (validated design)

```
User picks brand → upload dashboard photo
  → Vision LLM: "which icons are lit? return JSON {icons:[...], confidence}"
  → RAG lookup in collection filtered by brand
  → match ≥ threshold → show code + description + severity + advice
  → match < threshold → top-5 nearest by embedding similarity → user picks
```

Key decisions:
- **One Chroma collection with metadata `brand` field** + `where: {brand: ...}` filter — NOT one collection per brand (cheaper, easier to extend).
- **Store icon TEXT descriptions, not image embeddings** first (cheap, sufficient). CLIP embeddings only if icons are visually too similar to disambiguate by text.
- Have the vision model ALSO return **icon shape/color description** ("red droplet", "steering wheel + exclamation") → catches unknown icons with no DB code match.
- Cheap vision models via OmniRoute: `cmd/google/gemini-3.1-flash-lite`, `aug/gemini-3.0-flash`, `ddgw/gpt-4o-mini`, `aug/claude-haiku-4.5`.

## Next steps (agreed with user)

1. Scrape warninglightfinder → JSON ~113 icons: `{name, color_group, description, icon_image, severity}`
2. Mine VinFast VF9 PDF for warning-light section
3. Merge → build RAG collection "vinfast" on `rag_server.py` (port 3001, Chroma + all-MiniLM-L6-v2)
4. Test with a real dashboard photo

## Copyright note

- Brand PDF manuals: OK for internal/training data, don't republish wholesale.
- Web icon images: use for reference/internal, or redraw as SVG; buy stock if commercial product.
