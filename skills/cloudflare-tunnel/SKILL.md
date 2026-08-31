---
name: cloudflare-tunnel
description: Cài đặt, xác thực và chạy Cloudflare Tunnel để expose local service ra public domain
---

# Cloudflare Tunnel

Expose local service ra internet qua Cloudflare CDN. Nhanh hơn ngrok, không cần auth token cho quick tunnel, production-grade.

## Noise ≠ Error: QUIC timeout logs (đừng hoảng)

Log `ERR failed to accept QUIC stream ... timeout: no recent network activity` + `WRN Serve tunnel error` + `INF Retrying connection in up to 1s` xuất hiện định kỳ trên tunnel chạy lâu là **bình thường** — edge (HKG/SIN...) xoay kết nối QUIC khi idle. Kiểm tra nhanh:
- Có `INF Registered tunnel connection ... protocol=quic` ngay sau đó? → tự phục hồi, KHÔNG cần action.
- Process còn chạy (uptime dài, PID ổn định)? → khỏe.
- Chỉ lo khi: ERR lặp liên tục nhiều phút, không có `Registered`, hoặc site public trả 530/1033.

**Hermes watch_patterns caveat:** Nếu dùng `watch_patterns=["ERR"]` để monitor tunnel log, sau 3 cửa sổ 15s liên tiếp có match bị rate-limit drop, watch tự disabled và fallback sang `notify_on_complete` (chỉ báo 1 lần khi process exit). Đây là behavior đúng — QUIC timeout định kỳ, không cần alert mỗi lần. Không cần enable lại.

Đừng kill/restart tunnel chỉ vì log này — kill nhầm sẽ gây downtime thật.

## Diagnose & Recover (HTTP 530 — origin unreachable)

Cloudflare 530 = tunnel connected nhưng origin không reachable. Fix từng bước:
```bash
# 1. Origin server alive?
curl -sI --max-time 5 http://localhost:3000/
curl -sI --max-time 10 https://yoursite.com/   # 530 = tunnel on, origin down

# 2. Cloudflared process running?
ps aux | grep cloudflared   # Linux
tasklist | grep cloudflared  # Windows

# 3. Tunnel list (check health)
cloudflared tunnel list
```

Nếu origin + tunnel đều down, restart theo thứ tự:

```bash
# Step A — Start origin first
cd ~/service-dashboard && node server.js &
sleep 2 && curl -sI http://localhost:3000/  # verify 200

# Step B — Start cloudflared
cloudflared tunnel --config "C:\Users\<user>\.cloudflared\config.yml" run &
# Wait for "Registered tunnel connection" log

# Step C — Verify public URL
curl -sI https://yoursite.com/  # expect 200
```

**Pitfall:** Nếu restart origin mà tunnel vẫn 530, tunnel có thể đã cache connection cũ. Kill cloudflared rồi start lại.

## Diagnose & Recover (Error 1033 — tunnel DOWN hoàn toàn)

Error 1033 = **toàn bộ tunnel chết** (khác 530: tunnel sống nhưng origin down). Triệu chứng: Cloudflare báo "Cloudflare Tunnel error" + Ray ID. Thường do process cloudflared không chạy (chết hoặc startup bat fail).

```bash
# 1. Kiểm tra cloudflared process (Windows)
tasklist //FI "IMAGENAME eq cloudflared.exe"   # lưu ý: file có thể KHÔNG có .exe
# 2. Origin server vẫn sống? (phân biệt với 530)
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3050/
#   200 = origin OK → chắc chắn tunnel chết

# 3. Binary + config
ls -la ~/bin/cloudflared        # file KHÔNG có .exe
cat ~/.cloudflared/config.yml   # ingress map: daily→3050, rag→3001, voice→3100, www/root→3000

# 4. Fix: start lại (long-lived → terminal background=true, absolute path KHÔNG .exe)
/c/Users/datel/bin/cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
#    Đợi log "Registered tunnel connection connIndex=0..3 ... location=hkg.. protocol=quic"
#    Rồi curl -sI https://daily.btdat.io.vn/ → 200
```

**Pitfall startup bat:** `btdat-startup.bat` (Startup folder) gọi `cloudflared.exe tunnel ...`
nhưng binary là `cloudflared` (không .exe) → bat fail âm thầm sau reboot, tunnel không dậy.
Fix: bỏ `.exe`. Chi tiết đầy đủ (debug path, verify, giữ process sống): `references/error-1033-tunnel-down.md`.
curl -s -o /dev/null -w '%{http_code}' http://localhost:3050/   # 200 = origin OK, tunnel mới chết
# 3. Khởi động lại tunnel (named tunnel btdat.io.vn)
/c/Users/datel/bin/cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
# Chờ log "Registered tunnel connection" rồi verify:
curl -s -o /dev/null -w '%{http_code}' https://daily.btdat.io.vn/   # expect 200
```

**Pitfall — tên file cloudflared trên Windows:** `~/bin/cloudflared` KHÔNG có đuôi `.exe` (ngrok cũng vậy). Startup bat `btdat-startup.bat` gọi `cloudflared.exe` → fail âm thầm khi logon → tunnel chết sau reboot. Dùng đúng tên file không đuôi, hoặc sửa bat thành `cloudflared tunnel ...`.

**Pitfall — chạy qua Hermes background:** khi dùng `terminal(background=true)` phải dùng absolute path `/c/Users/datel/bin/cloudflared` — `cd ~/bin && ./cloudflared.exe` fail với "No such file or directory" (subshell không giữ cwd + sai tên file).

### Restart an toàn — PHÂN BIỆT quick tunnel vs named tunnel (Windows)

Máy Đạt có thể chạy **nhiều process cloudflared cùng lúc**:
- **Quick tunnel** (OmniRoute MCP): cmdline chứa `--url http://127.0.0.1:20128` — **KHÔNG ĐƯỢC KILL** (memory: "PID 4604 quick tunnel OmniRoute đừng kill")
- **Named tunnel** (btdat.io.vn): cmdline chứa `tunnel --config C:\Users\datel\.cloudflared\config.yml run` — cái này mới restart

`tasklist` chỉ cho PID, không phân biệt được → **phải đọc cmdline đầy đủ**. `wmic` không có trên git-bash; dùng ps1:

```powershell
# cfcheck.ps1 — đặt ở C:\Users\datel
Get-CimInstance Win32_Process | Where-Object { $_.Name -like '*cloudflared*' } | ForEach-Object {
  "PID=$($_.ProcessId) CMD=[$($_.CommandLine)]"
}
# chạy: powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\datel\cfcheck.ps1
```

⚠️ Không viết `powershell -Command "..."` inline chứa `$_` — MSYS biến `$_` thành path khi cwd là path-like (vd `/d/daily`). Luôn dùng file .ps1.

Kill đúng process:
```bash
taskkill -F -PID <named-tunnel-pid>   # dùng -F, KHÔNG dùng //F (MSYS mangle)
```
Rồi start lại:
```bash
/c/Users/datel/bin/cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
```
⚠️ Binary là `cloudflared` KHÔNG có `.exe` (dù tasklist hiện `cloudflared.exe`) — `cloudflared.exe` sẽ "No such file or directory".

### Verify DNS subdomain chưa propagate — dùng `--resolve` bỏ qua DNS local

Sau khi thêm DNS record Cloudflare nhưng DNS local (công ty) chưa cập nhật, `curl https://sub.domain` fail "Could not resolve host". Verify xuyên Cloudflare edge:

```bash
# Lấy IP Cloudflare của domain chính (cùng edge cho mọi subdomain):
nslookup btdat.io.vn 1.1.1.1   # → 104.21.x.x / 172.67.x.x
curl -s -o /dev/null -w "HTTP %{http_code}\n" -m 30 \
  --resolve daily.btdat.io.vn:443:104.21.83.43 https://daily.btdat.io.vn/
# HTTP 200 = tunnel + ingress + DNS record ĐỀU OK (DNS local chỉ là cache chậm)
```

**Thêm subdomain mới (ví dụ `voice.btdat.io.vn`) — DNS record phải thêm tay:**
- Sửa `~/.cloudflared/config.yml` thêm ingress `- hostname: voice.btdat.io.vn\n    service: http://localhost:3100` rồi restart tunnel.
- **NHƯNG**: nếu máy không có `cert.pem` (`~/.cloudflared/cert.pem`) và không có Cloudflare API token, tunnel KHÔNG tự tạo DNS record — `cloudflared tunnel route dns` báo "Cannot determine default origin certificate path". Phải thêm record CNAME thủ công trên dashboard:
  - Type `CNAME`, Name `voice`, Target `<tunnel-id>.cfargotunnel.com` (VD: `b3e9ea6a-9ed9-41fc-be71-66f52b31fef3.cfargotunnel.com`), Proxy ON.
  - Xác minh: `nslookup voice.btdat.io.vn 8.8.8.8` — "Non-existent domain" = chưa thêm record.
- Subdomain đã có sẵn (`rag`, `www`) resolve được qua nslookup — dùng làm chuẩn so sánh.

**Windows process management (multiple cloudflared):** Có thể có NHIỀU cloudflared process chạy đồng thời:
- Tunnel chính (btdat.io.vn): 2-3 process `cloudflared tunnel run <tunnel-id>` — kill được bằng `taskkill /F /PID <pid>` rồi start lại 1 cái.
- **Quick tunnel của OmniRoute** (trycloudflare → localhost:20128): process cha là OmniRoute (node.exe), PID ghi trong `~/.omniroute/cloudflared/quick-tunnel-state.json` — **KHÔNG kill** cái này (nó quản lý bởi OmniRoute, access denied).
- Kiểm tra cmdline từng process: `powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Process -Filter 'ProcessId=<pid>').CommandLine"` — nếu là `tunnel run <id>` thì là tunnel chính, nếu là quick tunnel thì bỏ qua.

### Thêm subdomain mới — cần DNS CNAME record thủ công (không tự tạo)

Thêm hostname mới vào `config.yml` ingress **KHÔNG tự tạo DNS record**. Nếu máy không có `cert.pem` hoặc Cloudflare API token (chỉ có `credentials.json`), `cloudflared tunnel route dns` sẽ fail với "Cannot determine default origin certificate path", và subdomain mới → `could not resolve host`.

**Phải thêm CNAME thủ công trên Cloudflare dashboard** (dash.cloudflare.com → domain → DNS → Add record):
| Field | Value |
|---|---|
| Type | `CNAME` |
| Name | `<sub>` (vd `voice`) |
| Target | `<TUNNEL_ID>.cfargotunnel.com` (vd `b3e9ea6a-...cfargotunnel.com`) |
| Proxy | ON (orange) |
| TTL | Auto |

Tunnel ID lấy từ `~/.cloudflared/credentials.json` (field `TunnelID`) hoặc `cloudflared tunnel list`. DNS propagate 1-2 phút.

**Pitfall — nhiều cloudflared process:** máy có thể chạy NHIỀU `cloudflared.exe` cùng lúc: 3 process `tunnel run <ID>` cho btdat.io.vn + 1 quick tunnel của OmniRoute (trycloudflare → 20128, cha là node/OmniRoute — KHÔNG kill cái này, nó do OmniRoute quản lý). Khi restart tunnel: kill các process `tunnel run` (taskkill OK), để nguyên quick tunnel của OmniRoute. Kiểm tra cmdline: `powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Process -Filter 'name=''cloudflared.exe''').CommandLine"`.

---

## Cài đặt cloudflared (Windows/git-bash)

```bash
# Download (dùng bitsadmin vì curl hay lỗi ghi file trên MSYS2)
bitsadmin /transfer "cloudflared" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" "C:\Users\%USERNAME%\Downloads\cloudflared.exe"

# Copy vào ~/bin
mkdir -p ~/bin
cp /c/Users/<user>/Downloads/cloudflared.exe ~/bin/cloudflared

# Verify
~/bin/cloudflared version
```

## Xác thực

### Cách 1 — Browser login (dễ nhất)

```bash
~/bin/cloudflared tunnel login
# Mở URL hiện ra trong browser → authorize → cert.pem tự sinh
```

### Cách 2 — API Token (khi browser callback không về máy)

1. Vào https://dash.cloudflare.com/profile/api-tokens → Create Token
2. Permissions: `Account:Cloudflare Tunnel:Edit`, `Zone:DNS:Edit`, `Zone:Zone:Edit`
3. Dùng token để thao tác API trực tiếp

## Tạo tunnel

### Cách 1 — cloudflared CLI (cần cert.pem)

```bash
export CLOUDFLARE_API_TOKEN="<token>"
~/bin/cloudflared tunnel create <tên-tunnel>
```

### Cách 2 — API trực tiếp (ko cần cert.pem, dùng token)

```bash
# Generate tunnel secret (32 bytes base64)
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Create tunnel
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"<tên-tunnel>","tunnel_secret":"<secret>"}'
```

## Cấu hình tunnel

Viết config.yml tại `C:\Users\<user>\.cloudflared\config.yml`:

```yaml
tunnel: <tunnel-id>
credentials-file: C:\Users\<user>\.cloudflared\credentials.json
ingress:
  - hostname: <domain>
    service: http://localhost:<port>
  - service: http_status:404
```

Viết credentials.json tại `C:\Users\<user>\.cloudflared\credentials.json`:

```json
{
  "AccountTag": "<account-id>",
  "TunnelSecret": "<base64-secret>",
  "TunnelID": "<tunnel-id>"
}
```

## Route DNS

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"<domain>","content":"<tunnel-id>.cfargotunnel.com","proxied":true,"ttl":1}'
```

### Subdomain routing

Mỗi service có web UI có thể có subdomain riêng qua tunnel:

1. **Tạo CNAME record** cho subdomain trỏ tới tunnel:
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"<subdomain>","content":"<tunnel-id>.cfargotunnel.com","proxied":true}'
```

2. **Thêm ingress rule** trong `config.yml` — rule cụ thể trước, catch-all cuối:
```yaml
ingress:
  - hostname: <subdomain>.domain.com
    service: http://localhost:<port>
  - hostname: domain.com
    service: http://localhost:3000
  - service: http_status:404
```

3. **Restart tunnel** để áp dụng: kill process cũ → chạy lại `cloudflared tunnel --config "..." run`.

Thứ tự ingress rules quan trọng: rule cụ thể (subdomain) đặt trước rule mặc định. Rule cuối cùng phải là `http_status:404` catch-all.

## Chạy tunnel

```bash
# Dùng config file (Windows path format)
~/bin/cloudflared tunnel --config "C:\Users\<user>\.cloudflared\config.yml" run
```

Chạy background: dùng `terminal(background=true, notify_on_complete=false)` vì là daemon.

## Đổi nameserver (bước cuối)

Sau khi tunnel chạy, vào registrar (Nhân Hòa, etc.) đổi NS về Cloudflare:
- `xxx.ns.cloudflare.com`
- `yyy.ns.cloudflare.com`

Đợi propagation (vài phút → 24h).

## API endpoints hữu ích

| Action | Method | URL |
|---|---|---|
| List accounts | GET | `/client/v4/accounts` |
| Get zone ID by domain | GET | `/client/v4/zones?name=<domain>` |
| Check zone status + NS | GET | `/client/v4/zones/<zone_id>` |
| Create tunnel | POST | `/client/v4/accounts/<aid>/cfd_tunnel` |
| Get tunnel token | GET | `/client/v4/accounts/<aid>/cfd_tunnel/<tid>/token` |
| Delete tunnel | DELETE | `/client/v4/accounts/<aid>/cfd_tunnel/<tid>` |
| Create DNS record | POST | `/client/v4/zones/<zid>/dns_records` |

## So sánh với ngrok

| Tiêu chí | Cloudflare Tunnel | ngrok |
|---|---|---|
| Auth quick tunnel | Ko cần | Bắt buộc token từ dashboard |
| URL quick | `xxx.trycloudflare.com` | `xxx.ngrok-free.dev` |
| Tốc độ | Nhanh (Cloudflare CDN) | Trung bình |
| Web UI local | Ko có | Có tại localhost:4040 |
| Domain riêng | Có — gắn domain qua Cloudflare DNS | Cần trả phí |
| Production | Named tunnel = production-grade | Paid plan |

## Pitfalls

- **`cloudflared tunnel login` ko work trên headless/server**: lệnh mở browser để auth — callback ko về được nếu ko có GUI. Dùng API token + direct API call.
- **Windows path cho --config**: cloudflared là Windows native EXE. Dùng `C:\\\\Users\\\\...\\\\config.yml`, ko dùng `~/.cloudflared/config.yml`. `~/` path gây lỗi "The system cannot find the path specified".
- **`--config` flag bị reject trên cloudflared 2026+ với MSYS2/git-bash**: `cloudflared tunnel run --config /c/Users/.../config.yml` in ra help text và thoát. Nguyên nhân: MSYS2 chuyển path thành Windows path có dấu cách hoặc xung đột argument parser. **Fix:** dùng `cloudflared tunnel run <tunnel-id>` — nó tự đọc `~/.cloudflared/config.yml` và `credentials.json`.
- **tunnel_secret**: phải là base64 của 32 bytes random. Dùng: `python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"`
- **curl download lỗi trên MSYS2**: dùng `bitsadmin /transfer` thay vì `curl -L` (curl ghi file lỗi "Failed to open the file").
- **DNS propagation**: sau đổi NS, zone status = `pending` với `activation_failure_reason: ns_delegated_from_provider`. Đợi vài phút→24h.
- **Tunnel restart**: kill process (process kill hoặc taskkill) rồi chạy lại. Chạy background với `notify_on_complete=false`.
- **Subdomain DNS**: sau tạo CNAME record, subdomain có hiệu lực ngay (cùng zone Cloudflare, ko cần đợi NS propagation).
- `.io.vn`, `.id.vn`, `.ai.vn` là ccSLD của VN (VNNIC). Cloudflare hỗ trợ từ mid-2023.
- **Kill tunnel**: `taskkill /f /im cloudflared.exe`
- **Start tunnel đơn giản nhất**: `cloudflared tunnel run <tunnel-id>` — không cần `--config` flag. Nếu config.yml và credentials.json ở `~/.cloudflared/`, cloudflared tự detect. Chạy background với `terminal(background=true, notify_on_complete=false)`. Sau khi chạy, verify bằng `curl -sI https://domain.com/` (expect 200).

## References
- Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps
- API endpoints: https://developers.cloudflare.com/api/operations/tunnel-create
