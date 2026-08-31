# Vietnamese + Pixel Font Safety Table (Google Fonts)

Verified 2026-08 (VẬN RUNE project). **Always load via Google Fonts css2 URL and VERIFY with a screenshot** — a font can claim latin-ext yet still miss Vietnamese combining marks.

## Fonts with NO Vietnamese glyphs (dấu bị vỡ/tách rời — DO NOT use for VN UI)

Press Start 2P, Pixelify Sans, Silkscreen, Tiny5, Micro 5, DotGothic16, Jacquard, Handjet

Broken look: "Mở khóa" renders "M� kh�a", "Người" becomes glyph soup, tone marks detached or replaced with boxes.

## Fonts WITH Vietnamese glyphs (verified)

| Font | Vibe | Notes |
|---|---|---|
| **VT323** | pixel/terminal | ⭐ Best pixel look with full VN support; chosen for VẬN RUNE headings |
| Roboto Mono | monospace | safe, slightly less "game" feel |
| Space Mono | monospace | safe |
| Be Vietnam Pro | modern | safe sans for body |

## Fallback chain pattern (proven)

```css
--font-head: 'VT323', 'Press Start 2P', monospace;   /* safe first! */
--font-body: 'Geist Sans', 'VT323', 'Roboto Mono', monospace;
```

Putting the safe font FIRST means VN diacritics always render; the pretty-but-broken font only kicks in for ASCII.

## Verification recipe (mandatory)

The bug is INVISIBLE in code review — fonts load at runtime from Google Fonts CDN. Only a rendered screenshot shows it.

1. Build + serve the page
2. playwright screenshot of home / battle / end screens at mobile viewport, deviceScaleFactor 2
3. `vision_analyze` each shot asking specifically: "Có lỗi font tiếng Việt (dấu bị vỡ/tách rời) không? Các chữ Mở, Người, kể, chuyện đọc được chứ?"
4. Confirm diacritics (ạ, ệ, ộ, ứ, ầ...) sit cleanly ON their base letters

## Also caught by visual QA (VẬN RUNE)

- Duplicated epitaph on end screen (summary rendered twice) — only visible in screenshot, assertions passed
- 3-rune picker mid-screen emptiness — layout feedback from vision analysis
