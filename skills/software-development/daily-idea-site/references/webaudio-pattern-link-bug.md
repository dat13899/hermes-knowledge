# WebAudio app pitfalls — daily idea builds (15/08/2026)

Nguồn: "Nhịp Điệu Neon" drum machine (daily.btdat.io.vn/15082026) — bị CÂM hoàn toàn
khi bấm Play, đã fix + verify.

## Bug: UI pattern ↔ audio engine không link

Triệu chứng: bấm Play, playhead chạy, visualizer không nhảy, **không có âm thanh gì**.

Nguyên nhân (tách 2 module app.js + audio.js):
- audio.js `scheduleStep` đọc `state.curP` như **value**: `state.curP || [[],[],[],[],[],[],[]]`
  → `curP` undefined trong audio state → fallback pattern RỖNG → 0 note mỗi step.
- app.js định nghĩa `curP: () => state.patterns[state.pat]` — **function**, nhưng không bao giờ
  gắn vào `DN.state` của audio engine.

## Fix chuẩn (dùng cho mọi WebAudio tách module)

1. audio.js — nhận diện cả 2 dạng (function lẫn value):
```js
const p = (typeof state.curP === 'function') ? state.curP() : (state.curP || [[],[],[],[],[],[],[]]);
```
2. app.js boot() — link accessor vào audio state:
```js
DN.state.curP = () => state.curP();
```

## Verify âm thanh trong headless browser (không loa)

AudioContext headless vẫn `running`, setInterval vẫn fire — nên đếm note được schedule:
```js
let notes = 0; const orig = DN.state.vizHook;
DN.state.vizHook = (id, v, c, w) => { notes++; orig && orig(id, v, c, w); };
DN.toggle();
await new Promise(r => setTimeout(r, 300));
// notes > 0 = có âm thanh (trước fix: 0)
DN.state.curP().flat().filter(Boolean).length > 0; // pattern có beat
```
Kết quả verify thực tế sau fix: `notes: 3` trong 300ms, `patternSum: 25`, 0 errors.

## ⚠️ Visualizer "trống" trong screenshot ≠ lỗi

Headless không có audio device → `vizHook` không bao giờ được gọi → canvas chỉ có bass ring mờ.
KHÔNG được kết luận "visualizer hỏng". Verify bằng gọi thủ công rồi đếm pixel:
```js
DN.state.vizHook('kick', 0.8, 'rgba(0,229,255,.9)', performance.now());
// đếm non-black pixel canvas: 1102 (idle) → 11423 (sau 8 calls) = visualizer OK
```

## Trình tự debug âm thanh (checklist)

1. `grep curP` cả app.js + audio.js — có đúng 1 nguồn sự thật cho pattern?
2. `DN.state.curP` có tồn tại + đúng kiểu (function)?
3. Count note qua vizHook instrumentation (trên).
4. Check chain: `src → g → fxBus → wet → master → comp → destination` — mọi gain > 0.
