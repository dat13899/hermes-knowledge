# Random Widget Page — July 2026

Latest version: 28 widgets, hash-based grid→detail navigation, category filter bar, single HTML file.

v1: 8 tabs (Bulma `.tabs`). v2: grid→detail with hash routing. v3: +10 widgets. v4: +10 widgets + category filter.

## Architecture

```
random-widget.html
├── Grid view (default)     → 5-column card grid (28 cards)
├── Detail view (on hash)   → panel-[id] shown, rest hidden
├── Filter bar              → auto-generated from WIDGETS categories
└── Init: check window.location.hash → showGrid() or showDetail(id)
```

## Widget Registry

```javascript
const WIDGETS = [
  { id:'random',     icon:'🎲', title:'Khám phá ngẫu nhiên', desc:'...', cat:'Ngẫu nhiên', color:'#818cf8' },
  // add new entries here — grid + filter auto-build
];
```

Each widget needs:
1. Panel `<div class="widget-panel" id="panel-${id}">` in HTML
2. Init call in `showDetail(id)` — e.g. `if(id==='pomodoro')pomoReset()`
3. JS function for widget logic

## Navigation Flow

```javascript
function initPage(){
  const hash = window.location.hash.slice(1);
  if(hash && WIDGETS.find(w=>w.id===hash)) showDetail(hash);
  else showGrid();
}
function showGrid(){
  document.getElementById('grid-view').classList.add('active');
  document.getElementById('detail-view').classList.remove('active');
  window.location.hash = '';
}
function showDetail(id){
  document.getElementById('grid-view').classList.remove('active');
  document.getElementById('detail-view').classList.add('active');
  document.querySelectorAll('.widget-panel').forEach(p=>p.style.display='none');
  const panel = document.getElementById('panel-'+id);
  if(panel) panel.style.display = 'block';
  const w = WIDGETS.find(x=>x.id===id);
  if(w) document.getElementById('detail-title').textContent = w.icon+' '+w.title;
  if(id==='colors') genPalette();
  if(id==='password') genPassword();
  // ... other init calls
}
function openWidget(id){ window.location.hash = id; showDetail(id); }
function closeWidget(){ showGrid(); }
window.addEventListener('hashchange', () => {
  const hash = window.location.hash.slice(1);
  if(hash && WIDGETS.find(w=>w.id===hash)) showDetail(hash);
  else showGrid();
});
```

## All 28 Widgets

### Batch 1 (v1 — 7 widgets)

| # | ID | Type | Notes |
|---|-----|------|-------|
| 1 | random | Khám phá ngẫu nhiên | Server API `/api/utilities/random` |
| 2 | colors | Bảng màu | HSL golden ratio palette |
| 3 | food | Ăn gì hôm nay? | 30 Vietnamese dishes embedded |
| 4 | games | Mini Game | Dice/coin/number, CSS reflow restart |
| 5 | password | Mật khẩu | Strength meter, options |
| 6 | activities | Làm gì? | 30 activities, dedup guard |
| 7 | gradient | Gradient | Random linear/radial CSS |
| 8 | brain | Brain Dump | Sticky notes, drag, localStorage, export |

### Batch 2 (v3 — 10 widgets)

| # | ID | Type | Notes |
|---|-----|------|-------|
| 9 | 8ball | Magic 8-Ball | 20 answers + Vietnamese translation, shake animation |
| 10 | cards | Rút bài | Fisher-Yates deck, 1/5 card deal with stagger |
| 11 | emoji | Emoji Mix | 40 emojis, random pair, pop animation |
| 12 | challenge | Random Challenge | 24 challenges, 5 category filter buttons |
| 13 | list | Random List | Textarea input, 3 modes (pick/shuffle/pick N) |
| 14 | pomodoro | Pomodoro Timer | 25/5/15 min, Web Audio beep, session count |
| 15 | textgen | Text Generator | Lorem/words/names/ipsum-vi + quantity slider |
| 16 | history | Hôm nay trong lịch sử | 52 events, filter by today or random |
| 17 | workout | Workout Random | 18 exercises, target muscle badge |
| 18 | countdown | Countdown | Date picker → days/hours/min/sec |

### Batch 3 (v4 — 10 widgets)

| # | ID | Type | Notes |
|---|-----|------|-------|
| 19 | rps | Oẳn tù tì | Rock-paper-scissors vs CPU, score tracking |
| 20 | van | Random Văn | 22 quotes (TA+VI) + 20 dev jokes, toggle mode |
| 21 | bmi | BMI Calculator | Weight/height input, 6-level classification |
| 22 | tarot | Tarot 1 Lá | 22 major arcana, CSS 3D flip animation |
| 23 | calendar | Lịch Tháng | Full month grid, prev/next, today highlight |
| 24 | guess | Đoán Số | 1-100 guessing game, win counter |
| 25 | counter | Counter | +/- step config, +10/+100 shortcuts, localStorage |
| 26 | convert | Unit Converter | Temp/length/weight, conversion factor map |
| 27 | idea | Idea Generator | 24 random ideas, color tag per category |
| 28 | mood | Mood Tracker | 6 moods, daily save, 7-day history |

## Category Filter Bar

Auto-generated from `WIDGETS[].cat`. Dynamically creates pill buttons with "📦 Tất cả" default active. Cards get `data-cat` attribute. Filter function shows/hides by `data-cat` match.

```javascript
function filterGrid(cat){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===cat));
  document.querySelectorAll('.widget-card').forEach(c=>c.style.display=(cat==='all'||c.dataset.cat===cat)?'':'none');
}
```

Categories across 28 widgets: Ngẫu nhiên, Tiện ích, Đời sống, Giải trí, Bảo mật, Ghi chú, Sáng tạo, Học tập, Dev (9 total).

## Grid Layout

- Desktop: `grid-template-columns:repeat(5,1fr)` 
- Mobile (<768px): `repeat(2,1fr)`
- Card: icon (2rem), title (1rem, bold), desc (.75rem, line-clamp 2), badge (absolute top-right)
- Glassmorphism: `.glass-card` with `backdrop-filter:blur(20px)`, `border:1px solid var(--glass-border)`, hover lift

## Commit History

```
9a2a7e2 — v1: 6 widgets, tab-based
db04101 — v2: grid→detail layout, hash navigation
10e28a3 — v3: +10 widgets (8ball, cards, emoji, challenge, list, pomodoro, textgen, history, workout, countdown)
158e847 — v3.1: mobile 2 cols, card-desc line-clamp, card-badge absolute
ceb1cb8 — v3.2: desktop grid 5 columns
43c2e7e — v3.3: 8ball bigger ball + answer label below
69a91a2 — v3.4: 8ball Vietnamese translation
4c9a8aa — v4: +10 widgets batch 2 (rps, van, bmi, tarot, calendar, guess, counter, convert, idea, mood)
61fc625 — v4.1: add category filter bar on grid view
```

## File Stats

- Single file: `public/random-widget.html`
- ~120 KB, ~1878 lines
- 28 widgets, 100% client-side (except widget #1 random discovery)
- Add new widget = 4 spots: WIDGETS array, HTML panel, showDetail init, JS code
