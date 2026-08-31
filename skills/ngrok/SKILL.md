---
name: ngrok
description: Cài đặt, xác thực và chạy ngrok tunnel trên Windows/git-bash
---

# Ngrok Tunnel

Cài đặt và chạy ngrok để expose local service ra public URL.

## Cài đặt

```bash
# Download
curl -L -o /tmp/ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip

# Giải nén
cd /tmp && unzip -o ngrok.zip

# Copy vào ~/bin (tạo nếu chưa có)
mkdir -p ~/bin && cp /tmp/ngrok.exe ~/bin/ngrok

# Thêm vào PATH
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc && source ~/.bashrc
```

## Xác thực

Lấy authtoken từ https://dashboard.ngrok.com/get-started/your-authtoken

```bash
ngrok config add-authtoken <token>
```

## Chạy tunnel

```bash
# Expose port
ngrok http <port> --log=stdout
```

Dùng `background=true` + `notify_on_complete=false` vì ngrok chạy vĩnh viễn (daemon).

## Kiểm tra

- Web UI dashboard: `http://127.0.0.1:4040`
- Public URL: log output có dòng `started tunnel ... url=https://xxxx.ngrok-free.dev`

## Pitfalls

- Chạy trong git-bash/MSYS2: dùng `~/bin/ngrok` thay vì `/usr/local/bin/ngrok` (ko có quyền ghi)
- Port cần có service thật chạy trước, ko thì ngrok tunnel mở ko nhưng request timeout
- Kill tunnel: `taskkill /f /im ngrok.exe`
