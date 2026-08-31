# Full-Site Themed Redesign Workflow

> Use when redesigning the entire btdat.io.vn site to a new visual theme.
> Sequence: Audit → Plan → Tokens → Components → Layout → Pages → Build → Verify.

## Step 1: Audit

Browse every route and document:
- Page title, purpose, key components
- Current design system (colors, fonts, radius, shadows from `tokens.css`)
- Shared components (Navbar, BottomSheet, Toast, 404)
- Routing structure (App.jsx lazy imports)
- Any runtime errors (e.g. Hermes page)

## Step 2: Plan

Write a phased plan with clear phases:
1. Design System (CSS tokens, fonts, components)
2. Layout (navbar, background, particles)
3. Pages (highest-impact first)

Get user approval before building.

## Step 3: Design Tokens

Create override CSS (e.g. `pixel-tokens.css`):
- Import AFTER `tokens.css` in `main.jsx`
- Override both `[data-theme="dark"]` and `[data-theme="light"]` variable blocks
- Set: `--bg`, `--surface`, `--border`, `--text`, `--accent`, fonts, radii, shadows
- Add utility classes (`.pixel-border`, `.pixel-glow-*`, etc.)
- Add Google Fonts links in `index.html`

## Step 4: Reusable Components

Build in `src/components/<theme>/`:
- **Button** — variants (primary/secondary/gold/danger/ghost), sizes, 3D chiseled effect via box-shadow stacking
- **Card** — variants, optional glow, hard drop shadows
- **Progress/Bar** — segmented fill with pixel steps
- Export from barrel `index.js`

## Step 5: Layout

- Navbar: restyle to fit theme
- Background: CSS pattern + ambient particles
- 404 page: themed error message

## Step 6: Convert Pages (one at a time)

For each page:
- Keep all functionality (API calls, state, events, refs)
- Replace styling only
- Use new themed components where applicable
- Test interactivity after each page

## Step 7: Build & Verify

```bash
# Clean cache
rm -rf node_modules/.vite dist
npm run build

# Restart server
kill node process
node server.js
```

Verify each page: visual consistency, interactivity, no console errors, mobile responsive.

## Common Pitfalls (for this project)

- **CSS import order:** `main.jsx` imports in specific order — new tokens must come AFTER `tokens.css`
- **data-theme default:** HTML root has `data-theme="dark"` — both themes must be overridden
- **Font loading:** Preconnect + stylesheet link in `index.html`, then reference via CSS `--font-*` variables
- **Vite cache:** After adding new CSS files, delete `node_modules/.vite` AND `dist` for clean rebuild
- **Ref timing:** After `setState()`, DOM isn't immediately updated — use `useEffect` to interact with newly rendered elements
