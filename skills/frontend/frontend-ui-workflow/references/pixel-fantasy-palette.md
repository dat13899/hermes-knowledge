# Pixel Fantasy Palette — Design Rationale

> Reference for btdat.io.vn pixel fantasy theme. Dark mode only (light mode exists but hidden).

## Dark Palette — "Dungeon Tavern"

| Token | Value | Rationale |
|-------|-------|-----------|
| `--bg` | `#0a0705` | Sàn đá dungeon tối — tạo depth nền |
| `--surface` | `#18100a` | Gỗ tavern, tối hơn bg 1 bậc |
| `--surface-alt` | `#22180e` | Card/banner, layer thứ 3 |
| `--border` | `#3a281a` | Viền đậm, gần như nền |
| `--border-lt` | `#5a3a2a` | Viền sáng, visible rõ |
| `--text` | `#f0e2c8` | Parchment ink — ấm, readable |
| `--text-strong` | `#faf3e0` | Highlight |
| `--text-dim` | `#b8a080` | Mờ nhưng visible — WCAG AA compliant |
| `--accent` | `#ad80ff` | Magic purple — sáng hơn #7c4dff, readable |
| `--magic-blue` | `#64d8ff` | Phát quang rõ trên nền tối |
| `--ember-gold` | `#ffc400` | Ấm hơn #ffb300 |
| `--heal-green` | `#80d080` | Dễ đọc hơn #66bb6a |
| `--blood-red` | `#ff5252` | Sáng, cảnh báo rõ |

## Typography Hierarchy

| Role | Font | Size | Notes |
|------|------|------|-------|
| Display | Press Start 2P | 0.48–0.7rem | Logo + short labels ONLY |
| Heading | **VT323** | 0.85–1rem | Page titles, section headers — readable pixel look |
| Body | Geist Sans | 0.9rem | Paragraphs — never pixel font |
| Subtitle | Geist Sans | 0.75rem | Descriptions |
| Pixel badge | Press Start 2P | 0.3rem | Stats, level, labels |

## Lessons Learned

1. **Press Start 2P < 10px is unreadable** — never use for body text. Switch to VT323 for any heading longer than 2-3 words.
2. **Bottom nav** must use VT323 (--font-heading) at 0.55–0.6rem minimum, with glow-line active indicator (2px, 25%-75% width, box-shadow glow).
3. **Contrast escalation ladder** when user reports "khó nhìn":
   - Step 1: Darken bg (#1a0e0a → #0a0705), brighten text (#f4e8c1 → #f0e2c8), brighten dim (#a09080 → #b8a080)
   - Step 2: Switch to readable heading font, increase font-size
   - Step 3: Increase accent brightness (#7c4dff → #ad80ff)
4. **Depth illusion**: need 3+ surface levels for pixel themes to avoid flat muddy look: `bg → surface → surface-alt → border/border-lt`
5. **Mobile readability override**: bump `--text-dim` to `#c8b8a8` on mobile, `--text` to `#f5ead0`
6. **Light mode should be disabled/hidden** in pixel fantasy themes — the parchment palette is hard to make attractive. Default to dark, hide toggle.
