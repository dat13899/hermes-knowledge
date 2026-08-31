# Giữ dịch vụ Windows luôn chạy (Startup + Watchdog) — recipe đã kiểm chứng 2026-08-22

Vấn đề lặp lại trong phiên: bot Zalo (`tsx`, port 4810) và tunnel Cloudflare (`cloudflared`) **tự chết** khi chạy trong background session tạm của Hermes. Khi session kết thúc → process chết → user thấy "bot không trả lời" / "site 530". Giải pháp: **Windows Task Scheduler watchdog** + **Startup folder** (tự chạy khi đăng nhập), KHÔNG phụ thuộc session Hermes.

## Mẫu 1: script start idempotent (`.bat`)
Dùng cho từng service — **đã chạy thì thoát, chưa chạy thì start**.

```bat
@echo off
set "BOT_DIR=C:\Users\datel\zalo-oa-bot"
set "NODE=C:\Program Files\nodejs\node.exe"
set "LOG=%BOT_DIR%\server.log"

REM Neu da chay (port listen) thi thoat
netstat -ano | findstr ":4810" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo [%date% %time%] Bot da chay - thoat. >> %LOG%
  exit /b 0
)

cd /d %BOT_DIR%
echo [%date% %time%] Khoi dong Bot... >> %LOG%
start "ZaloBot" /b "%NODE%" --require "%BOT_DIR%\node_modules\tsx\dist\preflight.cjs" --import "file:///C:/Users/datel/zalo-oa-bot/node_modules/tsx/dist/loader.mjs" "%BOT_DIR%\src\index.ts"
exit /b 0
```

> ⚠️ Chạy `tsx` qua node trực tiếp với `--require preflight.cjs` + `--import loader.mjs` (giống hệt lệnh `tsx src/index.ts` nhưng không qua npm wrapper — gọn, đỡ lỗi path).
> Phiên bản cloudflared: `start "CloudflareTunnel" /b "%CF_BIN%" tunnel --config "%CF_CFG%" run`

## Mẫu 2: Watchdog mỗi 5 phút (Task Scheduler)
Tạo task chạy lại script start (idempotent) — chết thì start, sống thì bỏ qua.

```bash
# Tạo task chạy mỗi 5 phút (không cần quyền admin cho /sc minute)
schtasks /create /tn "ZaloBot-Watchdog" /tr "C:\Users\datel\zalo-oa-bot\start-zalo-bot.bat" /sc minute /mo 5 /rl LIMITED /f
# Cloudflare tương tự
schtasks /create /tn "CloudflareTunnel-Watchdog" /tr "C:\Users\datel\bin\start-cloudflared.bat" /sc minute /mo 5 /rl LIMITED /f
```

Trên máy này đã tạo: `ZaloBot-Watchdog`, `CloudflareTunnel-Watchdog` (đều /sc minute /mo 5 /rl LIMITED).

## Mẫu 3: Startup folder (tự chạy khi đăng nhập)
Copy script start vào Startup để chạy mỗi lần login, thay cho task Boot (bị "Access denied" khi dùng /sc onlogon không admin).

```bash
STARTUP="$APPDATA/Microsoft/Windows/Start Menu/Programs/Startup"
cp ~/zalo-oa-bot/start-zalo-bot.bat "$STARTUP/zalo-bot-start.bat"
cp ~/bin/start-cloudflared.bat "$STARTUP/cloudflare-tunnel-start.bat"
```

Đã đặt: `zalo-bot-start.bat`, `cloudflare-tunnel-start.bat`.

## Lưu ý / pitfall
- **`/sc onlogon` cần quyền admin** → `Access is denied`. Dùng **Startup folder** thay thế.
- Task `/sc minute /mo 5` là **tần suất giám sát** (watchdog) — không phải thời điểm chạy cố định. Task có thể không chạy đúng giờ nếu máy ngủ nhưng vẫn restart khi thức dậy.
- Script start **bắt buộc idempotent**: kiểm tra `netstat`/`tasklist` (cloudflared check bằng `tasklist /FI "IMAGENAME eq cloudflared.exe"`), nếu đã chạy thì thoát — tránh start trùng làm 2 instance đụng SQLite ("database is locked") hoặc 2 tunnel.
- Sau khi chạy script thủ công lần đầu, verify bằng `netstat -ano | grep :<port> | grep LISTENING` rồi `curl localhost:<port>` và `curl https://<domain>`.
- Đây là cách giữ service bền vững trên Windows khi KHÔNG muốn dùng pm2/service. Đã khắc phục "bot/site tự chết" lặp lại nhiều lần.
