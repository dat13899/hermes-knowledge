# Playwright Gameplay Verification Recipe (canvas games)

Verified 10/08/2026 on Đảo Trọng Lực (gravity-flip platformer). Use when the
daily idea is a canvas game and `verify-day.sh` (DOM dump + screenshots) is not
enough — you need to prove the GAMEPLAY works, not just that the page renders.

## Setup

- Thư mục `~/daily-test/` đã có `node_modules/playwright-core` (dùng lại, đừng
  cài lại). Chạy: `cd /c/Users/datel/daily-test && node test-<game>.js`
- Executable: `C:\Users\datel\AppData\Local\ms-playwright\chromium_headless_shell-<ver>\chrome-headless-shell-win64\chrome-headless-shell.exe`
  (glob version mới nhất giống verify-day.sh)
- **Viết test script bằng tool `write_file`** — KHÔNG dùng `cat > file << 'EOF'`
  trong terminal: heredoc nuốt backslash của Windows path → executable path vỡ
  (`C:UsersdatelAppData...`). Đã dính 2 lần trong 1 session.

## Bắt buộc: expose debug hooks trong game code

Trong index.html, sau khi khai báo biến state:

```js
window.__p=()=>player; window.__gems=()=>gems; window.__goal=()=>goal;
window.__state=()=>state; window.__lvl=()=>level;
```

Nếu không có hooks, test không thể teleport/đọc state → chỉ verify được bề mặt.

## Test flow chuẩn (11 bước, đều cho mọi game platformer)

1. `#ovStart` visible
2. Click `#bStart` → `window.__state()==='play'`
3. Press Space → đọc `window.__p().vy`/`.y`: nhảy lên = vy âm, y giảm
4. Press Shift (flip) → `window.__p().flip` toggle false→true
5. Keyboard down ArrowRight → `vx>0`, x tăng
6. HUD text đọc được (`#hLvl`, `#hScore`, `#hGem`)
7. **Chết**: teleport player xuống đáy (`p.y=99999; p.vy=2000`) → `#ovDead`
   visible + reason text
8. Click `#bRetry` → state==='play', overlay ẩn
9. **Gem**: teleport player lên gem đầu `p.x=g.x-13; p.y=g.y-15` → gems got +1,
   HUD cập nhật
10. **Clear**: teleport tới goal → `#ovClear` visible + stats text chứa "+..."
11. Click `#bNext` → `#hLvl` tăng

Mỗi bước in kết quả có số liệu thực (vy 0→-420, y 490→422) — bằng chứng, không
phải "should work". Collect `page.on('pageerror')` + `console` errors, in cuối.

## Screenshot script (2 viewport + gameplay state)

Click BẮT ĐẦU → chụp gameplay; loop teleport-tới-goal + bNext để chụp màn sau
(có platform động/hazard). Desktop dùng page riêng 1280x800.

## Pixel sampling — bằng chứng khách quan khi vision model "mù"

`vision_analyze` KHÔNG thấy được chi tiết nhỏ (outline 1-2px quanh sprite,
crop 74x78px). Đừng sửa code vì vision nói "không thấy" — sample pixel trước:

```js
const at = (x,y) => { const d = ctx2.getImageData(Math.round(x*dpr), Math.round(y*dpr), 1, 1).data; return [d[0],d[1],d[2]]; };
// so sánh: body tím [146,102,231] vs mép outline [236,225,199] vs nền [12,12,17]
```

Nếu pixel data chứng minh đủ tương phản → outline CÓ hiện, vision chỉ không
phân biệt ở scale nhỏ. Kết luận dựa trên số liệu, không dựa trên mô tả model.

## Pitfalls đã dính (chi tiết thêm trong SKILL.md mục "Pitfalls build game canvas")

- Hitstop decay phải ở `loop()` ngoài update — để trong update mà update bị
  skip khi hitstop>0 → tự khoá game vĩnh viễn sau chết/retry.
- Spawn player phải chạm đất `py=(R-1)*TILE-PH`, không dùng `player.h` lúc
  khởi tạo (player chưa tồn tại → TypeError). Jump ngược dấu khi flip.
