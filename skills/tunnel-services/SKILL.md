---
name: tunnel-services
description: Expose local ports ra public Internet qua tunnel — ngrok, Cloudflare Tunnel
---

# Tunnel Services

Expose local service ra Internet bằng tunnel. Ko cần public IP, ko cần port forwarding.

## Công cụ hỗ trợ

| Tool | Cài đặt | Auth | URL mẫu |
|---|---|---|---|
| **ngrok** | Download exe + authtoken | Bắt buộc | `xxx.ngrok-free.dev` |
| **cloudflared** | Download exe | Ko cần (quick tunnel) | `xxx.trycloudflare.com` |

Chi tiết từng tool xem skill `ngrok` (nếu đã tạo).

## Cài đặt nhanh cloudflared (Windows/git-bash)

```bash
bitsadmin /transfer "cloudflared" `
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
  "C:\Users\%USERNAME%\Downloads\cloudflared.exe"
cp /c/Users/<user>/Downloads/cloudflared.exe ~/bin/cloudflared
```

**bitsadmin** — cách tải ổn định nhất trên Windows. curl git-bash hay lỗi ghi file.

## So sánh

| Tiêu chí | ngrok | Cloudflare Tunnel |
|---|---|---|
| Auth | Bắt buộc authtoken | Quick: ko cần. Named: cần login |
| URL | `xxx.ngrok-free.dev` | `xxx.trycloudflare.com` hoặc domain riêng |
| Tốc độ | Trung bình | Nhanh (Cloudflare CDN) |
| Dashboard local | `localhost:4040` | Ko có |
| Domain riêng | Trả phí | Có — gắn domain mình (free) |
| Production | Paid plan | Named tunnel (free) |
| Kill | `taskkill /f /im ngrok.exe` | `taskkill /f /im cloudflared.exe` |

## Chạy

**ngrok:**
```bash
ngrok http <port> --log=stdout
```

**cloudflared (quick tunnel):**
```bash
cloudflared tunnel --url http://localhost:<port>
```

**cloudflared (named tunnel — production):**
```bash
cloudflared tunnel login
cloudflared tunnel create <tên>
cloudflared tunnel route dns <tên> <domain>
cloudflared tunnel run <tên>
```

## Pitfalls

- Port cần có service thật chạy trước khi start tunnel
- Dùng `background=true` + `notify_on_complete=false` (daemon, ko exit)
- git-bash curl lỗi ghi file → dùng bitsadmin