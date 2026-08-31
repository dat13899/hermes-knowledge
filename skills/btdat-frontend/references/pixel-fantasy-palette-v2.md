# Pixel Fantasy Palette v2 — btdat.io.vn

Updated 2026-07-30 after UI/UX overhaul.

## Dark Mode — "Dungeon Tavern"

```
--bg:              #0a0705     ← dungeon floor
--surface:         #18100a     ← tavern wood
--surface-alt:     #22180e     ← card/banner bg
--border:          #3a281a     ← subtle line
--border-lt:       #5a3a2a     ← component border
--text:            #f0e2c8     ← parchment text
--text-strong:     #faf3e0     ← emphasis
--text-dim:        #b8a080     ← muted (mobile: #c8b090)
--accent:          #ad80ff     ← primary (was #7c4dff)
--accent-hover:    #c4a0ff
--magic-blue:      #64d8ff     ← was #4fc3f7
--magic-purple:    #b388ff
--ember-gold:      #ffc400     ← was #ffb300
--healing-green:   #80d080     ← was #66bb6a
--blood-red:       #ff5252     ← was #e53935
--stone-gray:      #8d6e63
```

## Light Mode — "Parchment Scroll"

```
--bg:              #f5eed5
--surface:         #ede2c0
--surface-alt:     #e2d4aa
--border:          #c4a86a
--border-lt:       #d4bc84
--text:            #2a1a0a
--text-strong:     #0d0805
--text-dim:        #8a7050
--accent:          #7c4dff     (same as old dark — works on light)
--magic-blue:      #2196f3
--ember-gold:      #e6a800
```

## Font Tokens

```
--font-display:  'Press Start 2P', 'VT323', 'Geist Mono', monospace
--font-heading:  'VT323', 'Press Start 2P', monospace       ← USE THIS FOR HEADERS
--font-pixel:    'Press Start 2P', 'VT323', monospace        ← SMALL DISPLAY ONLY
--font-sans:     'Geist Sans', 'VT323', sans-serif
--font-body:     'Geist Sans', sans-serif                    ← ALL BODY TEXT
--font-mono:     'JetBrains Mono', 'Fira Code', monospace
```

## Key Rules
- Press Start 2P: max 3–4 words, 0.38rem+ only
- VT323 headings: 0.85–1rem, readable
- Geist Sans body: 0.9–1rem, good contrast
- Shadows: always hard hex `#0a0505`, no CSS vars for pixel shadows
- Scanlines: opacity 0.025, 3px gap. Let user ask for stronger.
