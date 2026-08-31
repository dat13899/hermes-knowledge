# Taste Skill Integration — btdat.io.vn (2026-07-25)

## What is Taste Skill

[**Taste Skill**](https://www.tasteskill.dev) is an open-source collection of SKILL.md files by [Leon Lin](https://github.com/Leonxlnx/taste-skill) that give AI coding agents "good taste" — stopping them from generating generic, boring frontends ("slop").

GitHub: https://github.com/Leonxlnx/taste-skill

## Skills installed in Hermes

Two Hermes skills created from Taste Skill source:

### 1. `taste-redesign` (category: frontend)
Source: `skills/redesign-skill/SKILL.md`  
Purpose: Audit + fix existing codebase. Protocol: **Scan → Diagnose → Fix**  
Use when: fixing existing UI, redesigning pages, consistency cleanup

### 2. `taste-design` (category: frontend)
Source: `skills/taste-skill/SKILL.md` (condensed)  
Purpose: Build new components with anti-slop rules.  
Use when: creating new pages/components, verifying designs

## Changes applied to btdat.io.vn (Session 2026-07-25)

### Priority 1: Font swap (Inter → Geist)
- Removed Google Fonts CDN for Inter
- Installed `@fontsource/geist-sans` (400/500/600/700) + `@fontsource/geist-mono` (400/500)
- Updated `tokens.css`: `--font-sans: 'Geist'`, `--font-mono: 'Geist Mono'`
- Imported font CSS in `main.jsx`
- Taste rule: Inter is the #1 AI default font — replace with character font (Geist pair)

### Priority 2: Color cleanup
- Accent: AI purple (#818cf8) → Emerald (#34d399)
- Reduced 3 accent colors → 1 single accent
- Shadows: `rgba(0,0,0,...)` → `rgba(10,14,23,...)` (tinted to bg)
- `--glass-shadow` tinted same way
- Blob colors → emerald family (#34d399, #10b981, #059669, #6ee7b7)
- `@keyframes logoPulse` + `navLinkGlow` → emerald box-shadow
- Swept all hardcoded #818cf8 across codebase → replaced with `var(--accent)`
- Taste rule: 1 accent color, no AI purple, tinted shadows, palette consistent

### Priority 3: Interactive states
- Added `.btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }`
- Existing hover + active states verified on all button classes
- Taste rule: every interactive element needs hover + active + focus + transition

### Priority 4: Layout fixes
- HeroSection: `minHeight: '100vh'` → `minHeight: '100dvh'` (iOS Safari viewport bug)
- ServicesSection + TechStackSection: `maxWidth: 1000` → `maxWidth: 1200`
- Taste rule: `100dvh` mandatory, container 1200-1440px

### Priority 5-7: Polish
- Added noise overlay: SVG fractalNoise texture, fixed, pointer-events none, opacity 0.025
- Added `<div className="noise-overlay" />` in AppLayout
- Taste rule: flat digital surfaces feel sterile, add grain/noise

## How to use in future sessions

### Before any UI work:
```
skill_view("taste-redesign")  → read audit checklist → check current page against it → fix in priority order
```

### Before shipping:
```
skill_view("taste-design")  → run Pre-Flight Check → verify all 10 checkboxes
```

### Color consistency sweep (when changing accent):
```bash
cd frontend/src && grep -rn '818cf8\|6366f1\|#a855f7\|#06b6d4' . --include='*.jsx' --include='*.css' | grep -v node_modules
```

## Plan file
See: `.hermes/plans/2026-07-25_230000-taste-skill-integration.md`
