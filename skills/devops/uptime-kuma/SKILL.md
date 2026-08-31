---
name: uptime-kuma
description: Uptime Kuma monitoring, standalone Node + Telegram notif
---

# Uptime Kuma (uptime.btdat.io.vn)

Uptime Kuma chạy standalone Node (không Docker) trên **port 3010**, SQLite, public qua Cloudflare Tunnel.

## Vị trí & chạy

```bash
cd ~/uptime-kuma
# Chạy (env bắt buộc để bỏ qua setup-database + đúng port):
UPTIME_KUMA_DB_TYPE=sqlite PORT=3010 UPTIME_KUMA_HOST=127.0.0.1 node server/server.js
```

- **DB**: `~/uptime-kuma/data/kuma.db` (SQLite, dùng `@louislam/sqlite3`)
- **Build frontend** (sau khi npm install): `npm run build` → tạo `dist/`
- **Startup tự động**: `~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/uptime-kuma-start.bat` (idempotent, kiểm tra port 3010)
- **SSH/HTTP**: Uptime Kuma cần `UPTIME_KUMA_DB_TYPE=sqlite` ngay lần đầu — nếu thiếu sẽ chạy vào mode `setup-database` (không nhận socket login).

## Cấu hình port

```js
// server/config.js
const port = [args.port, process.env.UPTIME_KUMA_PORT, process.env.PORT, 3001]
  .map(parseInt).find(v => !isNaN(v));
```
Ưu tiên `args.port` → `UPTIME_KUMA_PORT` → `PORT` → mặc định 3001. **Tránh 3001** (dành cho rag service).

## Admin & tự động hóa qua socket.io

Setup ban đầu cần admin account. Dùng **socket.io** (polling transport, tránh origin-check) — không cần Chrome:

```js
const { io } = require("socket.io-client");
const socket = io("http://127.0.0.1:3010", { transports: ["polling"], path: "/socket.io", reconnection: false });
// 1. Setup admin (lần đầu): sự kiện "setup"
socket.emit("setup", "admin", "password", cb => {});
// 2. Login: sự kiện "login" → trả {ok, token}; set socket.userID
socket.emit("login", { username, password }, res => {});
// 3. Thêm notif: sự kiện "addNotification" (notification, notificationID, callback)
//    notification phải là OBJECT đầy đủ config (JSON trong DB), KHÔNG chỉ id
// 4. Thêm monitor: sự kiện "add" (monitor, callback)
//    monitor.conditions phải là [] (JSON.stringify(undefined) → undefined gây NOT NULL lỗi)
//    notificationIDList phải là OBJECT map {"1": true} (không phải array — server dùng for..in)
```

**Pitfalls đã gặp (quan trọng):**
- `monitor.conditions` rỗng → `SQLITE_CONSTRAINT NOT NULL` → phải pass `conditions: []`
- `notificationIDList` là array `[1]` → server `for..in` đọc index `"0"` → FK lỗi `notification_id='0'`. **Phải là object** `{"1": true}`
- `addNotification` cần 3 args `(notification, notificationID, callback)`; `add` cần 2 args `(monitor, callback)`
- Socket bị lỗi origin-check → dùng `transports: ["polling"]` (polling không bị chặn origin) hoặc set env `UPTIME_KUMA_WS_ORIGIN_CHECK=bypass`

## Telegram notification

Config trong DB `notification.config` (JSON):
```json
{ "name":"...", "type":"telegram", "telegramBotToken":"<BOT_TOKEN>", "telegramChatID":"<chat_id>", "telegramSendSilently":false }
```
- Telegram bot token lấy từ `~/AppData/Local/hermes/.env` (`TELEGRAM_BOT_TOKEN`)
- Chat ID home: `1088711997`
- **Test**: `socket.emit("testNotification", fullNotifObj, cb)` — phải truyền OBJECT đầy đủ (đọc từ DB), không phải `{id}`.

## Monitor các port

Các monitor HTTP interval 60s: 3000 (btdat.io.vn), 3050 (daily), 3001 (rag), 4300 (angular), 4810 (zalo), 3100 (diagram), 20128 (omni), 3010 (uptime). Lưu ý: 3000/3050/3001/4300 thường DOWN (backend chưa chạy) — Uptime Kuma sẽ báo qua Telegram.

## Cloudflare Tunnel (ingress)

Thêm vào `~/.cloudflared/config.yml`:
```yaml
  - hostname: uptime.btdat.io.vn
    service: http://localhost:3010
```
Restart tunnel: `taskkill /f /im cloudflared.exe` (bỏ quick tunnel OmniRoute PID 8688) rồi chạy lại `cloudflared tunnel --config .../config.yml run`.

**DNS**: tạo CNAME `uptime` → `b3e9ea6a-9ed9-41fc-be71-66f52b31fef3.cfargotunnel.com` (tunnel id) trên Cloudflare dashboard. Không có cert.pem/CF API token → cloudflared không tự tạo DNS được.

**Pitfall DNS_PROBE_FINISHED_NXDOMAIN (19/08/2026):** Máy dùng DNS nội bộ Vinnet `10.20.1.12` (prod-ad.ad.vinnet.vn) giữ negative cache cho subdomain mới → trình duyệt báo NXDOMAIN dù Cloudflare record đúng. Fix: đổi DNS adapter Ethernet sang `1.1.1.1`/`1.0.0.1` (`Set-DnsClientServerAddress -InterfaceAlias Ethernet -ServerAddresses @('1.1.1.1','1.0.0.1')`) + `ipconfig /flushdns`. Đã chọn giữ nguyên 1.1.1.1 cho máy này.

## Verify

- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3010/` → 302 (dashboard, cần login)
- Query DB: `@louislam/sqlite3` → `SELECT id,name,type,url FROM monitor`
