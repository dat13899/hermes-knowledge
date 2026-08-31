---
name: tunnel
description: Tunnel tools — Cloudflare Tunnel (cloudflared), localtunnel, bore. Cài đặt, chạy trên Windows/git-bash.
---

# Tunnel — expose local service ra public URL

Covers: Cloudflare Tunnel (cloudflared, ưu tiên), localtunnel, bore.

## So sánh nhanh

| Tool | Lệnh | Auth | Dashboard |
|---|---|---|---|
| **ngrok** | `ngrok http <port>` | Token required | `localhost:4040` |
| **cloudflared** | `cloudflared tunnel --url http://localhost:<port>` | Ko cần (quick tunnel) | Metrics `:20241/metrics` |
| **localtunnel** | `npx localtunnel --port <port>` | Ko cần | Ko |
| **bore** | `bore local <port> --to bore.pub` | Ko cần | Ko |

> **Ngrok** có skill riêng (vì cần auth token + dashboard riêng). Skill này tập trung cloudflared và các tool ko cần auth.

---

## Cài đặt Cloudflare Tunnel (cloudflared)

⚠️ **Cảnh báo curl/MSYS2:** Trên Windows git-bash, curl hay lỗi write file. Dùng **BITSAdmin** thay thế:

```bash
bitsadmin /transfer "cloudflared" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" "C:\Users\%USERNAME%\Downloads\cloudflared.exe"
cp /c/Users/<user>/Downloads/cloudflared.exe ~/bin/cloudflared
```

### Chạy quick tunnel (ko cần tài khoản)

```bash
cloudflared tunnel --url http://localhost:<port>
```

Dùng `background=true` + `notify_on_complete=false`.

Public URL xuất hiện trong log sau ~5s:
```
Your quick Tunnel has been created! Visit it at:
https://<random>.trycloudflare.com
```

### Named tunnel (cần tài khoản Cloudflare + domain)

```bash
cloudflared tunnel login
cloudflared tunnel create <name>
cloudflared tunnel route dns <name> <domain>
cloudflared tunnel run <name>
```

---

### Restart named tunnel an toàn trên Windows (nhiều process cloudflared)

⚠️ Trên máy của Đạt có NHIỀU process cloudflared chạy cùng lúc — kill nhầm là sập service:

- **Quick tunnel OmniRoute**: `cloudflared.exe tunnel --url http://127.0.0.1:20128` (binary trong ~/.omniroute) — **KHÔNG bao giờ kill**
- **Named tunnel b3e9ea6a**: `cloudflared tunnel run b3e9ea6a-9ed9-41fc-be71-66f52b31fef3` (binary ~/bin, KHÔNG đuôi .exe) — process cần restart khi sửa config.yml

**PID đổi mỗi lần boot → không bao giờ kill theo PID.** Phân biệt bằng CommandLine. Viết file .ps1 rồi chạy (inline `powershell -Command` bị MSYS biến dạng `$_` khi cwd là path-like):

```bash
# cfcheck.ps1:
#   Get-CimInstance Win32_Process | Where-Object { $_.Name -like '*cloudflared*' } | ForEach-Object {
#     "PID=$($_.ProcessId) PARENT=$($_.ParentProcessId) CMD=[$($_.CommandLine)]" }
powershell -NoProfile -ExecutionPolicy Bypass -File cfcheck.ps1
```

Restart đúng process:

```bash
taskkill -F -PID <pid_named_tunnel>     # dùng -F -PID — KHÔNG //F (MSYS lỗi "Invalid argument/option")
# start lại y hệt startup bat:
cd ~/bin && ./cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
```

Verify sau restart: `curl -s -o /dev/null -w "%{http_code}" https://btdat.io.vn` → 200.

### Test subdomain mới khi DNS chưa propagate

DNS corporate (10.20.1.12) cache âm subdomain mới dù Cloudflare đã có record (nslookup local fail, nhưng `nslookup <sub> 1.1.1.1` thấy). Test xuyên CF edge bằng `--resolve`:

```bash
nslookup btdat.io.vn 1.1.1.1        # lấy CF IP: 104.21.83.43 / 172.67.212.135
curl -s -o /dev/null -w "%{http_code}" --resolve daily.btdat.io.vn:443:104.21.83.43 https://daily.btdat.io.vn/
```

HTTP 200 = ingress + tunnel hoạt động, chỉ thiếu DNS propagate. Thêm subdomain mới: CNAME `<sub>` → `<tunnel-id>.cfargotunnel.com`, Proxy ON. Restart named tunnel (ở trên) để config.yml ingress mới có hiệu lực.

---

## Cài đặt localtunnel (ko cần cài, chạy qua npx)

```bash
npx localtunnel --port <port>
```

Public URL: `https://<random>.loca.lt`

## Cài đặt bore (Rust, 1 binary)

```bash
cargo install bore-cli
# hoặc download release từ GitHub
bore local <port> --to bore.pub
```

---

## Pitfalls

- **Port cần có service thật** — tunnel mở ko thì request timeout / 502
- **Kill tunnel:** `taskkill /f /im cloudflared.exe` (hoặc process tương ứng)
- **MSYS2/git-bash:** Copy binary vào `~/bin/`, ko vào `/usr/local/bin/` (ko có quyền ghi)
- **Download thất bại trên git-bash curl:** Thay bằng `bitsadmin /transfer` (xem ở trên)
- **Cloudflared quick tunnel** ko có uptime guarantee — production dùng named tunnel
