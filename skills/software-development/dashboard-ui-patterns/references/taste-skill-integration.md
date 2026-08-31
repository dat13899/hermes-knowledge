# Taste Skill Integration (btdat.io.vn)

Ngày: 2026-07-25
Nguồn: https://www.tasteskill.dev + https://github.com/Leonxlnx/taste-skill

## Taste Skill là gì

Bộ SKILL.md mã nguồn mở của Leon Lin, giúp AI agents (Cursor, Claude Code, Codex, Copilot…) tạo frontend có "gu" thay vì "slop" (nhàm chán, generic). Từ "taste" ở đây = gu thẩm mỹ.

## Skills quan trọng cho btdat.io.vn

### `redesign-existing-projects` (SKILL.md: 15,060 chars)
**Protocol: Scan → Diagnose → Fix.** Audit codebase có sẵn, không đập đi xây lại.

Audit checklist gồm 8 nhóm:
1. **Typography** — font có character, headline presence, max-width 65ch, 4+ weights, text-wrap:balance, orphan words
2. **Color & Surfaces** — 1 accent color max, không pure-black background, shadow tinted, grain/noise overlay
3. **Layout** — asymmetry khi variant > 4, `min-h-dvh` thay `h-screen`, max-width 1200-1400, khác biệt border-radius, overlap/depth
4. **Interactivity & States** — hover states, active feedback (scale 0.98 / translateY 1px), transitions 200-300ms, focus ring, skeleton loaders
5. **Content** — không AI buzzwords, không Title Case everywhere, không Lorem Ipsum
6. **Component Patterns** — không chỉ card border+shadow+white, không chỉ filled+ghost buttons, không accordion FAQ
7. **Code Quality** — semantic HTML, không mix inline + class, relative units, z-index scale, valid imports
8. **Strategic Omissions** — legal links, "back" navigation, custom 404, skip-to-content, form validation

**Fix priority (theo Taste Skill):**
1. Font swap (impact cao nhất, rủi ro thấp nhất)
2. Color palette cleanup
3. Hover & active states
4. Layout & spacing fixes
5. Replace generic components
6. Add loading/empty/error states
7. Polish typography & spacing

### `design-taste-frontend` (SKILL.md: 87,253 chars)
**Greenfield skill.** Dùng khi làm landing page/portfolio từ đầu. Có các phần không trùng với `redesign-existing-projects`:

- **Brief Inference (Section 0):** Đọc page kind, vibe words, reference signals, audience, brand assets, quiet constraints → output "Design Read" 1 dòng trước khi code
- **Three Dials (Section 1):** `DESIGN_VARIANCE` (1-10), `MOTION_INTENSITY` (1-10), `VISUAL_DENSITY` (1-10). Baseline 8/6/4. Dial inference table cho từng loại brief
- **Anti-Default Discipline (Section 0.D):** Không default về AI-purple gradients, centered hero dark mesh, 3 equal feature cards, Inter+slate-900
- **Design System Map (Section 2):** Khi nào dùng real design system (Fluent UI, Material 3, Carbon, Polaris…) vs aesthetic-only (glassmorphism, bento, brutalism…)
- **Dependency Verification (Section 3.F):** Check package.json trước khi import bất kỳ library nào
- **Shape Consistency Lock (Section 4.4):** 1 corner-radius scale cho toàn page
- **Layout Discipline (Section 4.7):** Hero must fit viewport, navigation single line ≤80px, bento grid no repetition, eyebrow restraint (max 1 per 3 sections), split-header ban, section-layout-repetition ban (4+ layout families per page)

## Key Rules đã áp dụng cho btdat.io.vn

### Inter → Geist migration path
- Taste Skill cấm `Inter` làm default font (Section 4.1)
- Recommended pairing: `Geist` + `Geist Mono` (thay `JetBrains Mono` cho code)
- Giữ mono font cho số liệu (`font-variant-numeric: tabular-nums`)

### Purple accent ban (Lila Rule — Section 4.2)
- `#818cf8` (indigo/purple) là "AI default" bị cấm
- Thay bằng: Emerald, Electric Blue, Deep Rose, Burnt Orange
- Max 1 accent color, saturation < 80%

### Glassmorphism đúng cách (Section 4.4 + 2.B)
- `backdrop-filter: blur()` + 1px inner border + inner shadow = "true glassmorphism"
- Thêm grain/noise overlay (`pointer-events: none`) để tránh digital flatness
- Shadow must be tinted (không `rgba(0,0,0,…)` thuần)

### Hero discipline (Section 4.7)
- `min-h-[100dvh]` thay `min-height: 100vh`
- Max 4 text elements (eyebrow/brand-strip, headline, subtext, CTAs)
- Headline max 2 lines desktop, subtext max 20 words
- Hero top-padding cap: `pt-24` (≈6rem)

### z-index scale (Section 7 - Code Quality)
- Bỏ `z-index: 9999` hardcoded
- Lập scale trong tokens.css: `--z-base: 1`, `--z-dropdown: 100`, `--z-modal: 200`, `--z-toast: 300`

## Cách tích hợp vào Hermes

### Option 1: Dùng trực tiếp (recommended cho audit)
```bash
curl -sL https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/redesign-skill/SKILL.md
```
→ Load nội dung làm checklist audit. Không cần save thành Hermes skill.

### Option 2: Save làm Hermes skill
```bash
# Tạo Hermes skill từ Taste Skill
# skill_manage action=create name=taste-redesign
#   → paste nội dung redesign-skill/SKILL.md
# skill_manage action=create name=taste-design  
#   → paste condensed rules từ taste-skill/SKILL.md
```

### Option 3: Cài qua npx (cho Cursor/Claude Code)
```bash
npx skills add https://github.com/Leonxlnx/taste-skill
npx skills add https://github.com/Leonxlnx/taste-skill --skill "redesign-existing-projects"
```

## Audit results cho btdat.io.vn (2026-07-25)

Kết quả audit 8 nhóm (xem plan: `.hermes/plans/2026-07-25_230000-taste-skill-integration.md`):

| Nhóm | Issues found | Severity |
|------|-------------|----------|
| Typography | Inter default, no text-wrap:balance, no max-width-65ch | ⚠️ Medium |
| Color | 3 accent colors, AI purple, shadow pure-black | ❌ High |
| Layout | 100vh (not dvh), maxWidth too narrow, no asymmetry | ⚠️ Medium |
| States | Missing hover/active/focus on many buttons | ⚠️ Medium |
| Code | Div soup, inline+class mixed, z-index:9999 | ❌ High |
| Omissions | No legal links, no skip-to-content | ⚠️ Low |

## Pitfalls

- **Không dùng `design-taste-frontend` cho existing project** — nó là greenfield skill, sẽ muốn viết lại từ đầu. Luôn dùng `redesign-existing-projects` khi đã có codebase.
- **Taste Skill không phải là "design system"** — nó là bộ rules/guidelines, không có CSS file hay components. Phải tự implement.
- **Đừng áp dụng tất cả rules cùng lúc** — fix theo priority table trong `redesign-existing-projects`, test sau mỗi change.
- **Font swap cần test trên tất cả page** — Geist có metric khác Inter, có thể làm vỡ layout nếu không test kỹ.
- **1 accent color là hard rule** — nếu đã có `--accent-1`, `--accent-2` trong tokens.css, phải merge hoặc bỏ.
