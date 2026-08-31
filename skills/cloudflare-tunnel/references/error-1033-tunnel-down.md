# Error 1033 — Tunnel chết hoàn toàn (Windows)

Triệu chứng: Cloudflare trả "Error 1033 / Cloudflare Tunnel error" + Ray ID.
Khác 530 (tunnel sống, origin down) — 1033 = **process cloudflared không chạy**.

## Debug path (đã dùng thành công 08/2026)

```bash
# 1. Process có chạy không? (Windows)
tasklist //FI "IMAGENAME eq cloudflared.exe"
wmic process where "name='cloudflared.exe'" get ProcessId,CommandLine
#   → file thật có thể KHÔNG có .exe (tên là `cloudflared`), nên tasklist theo
#     .exe có thể miss dù process đang chạy. Kiểm tra `tasklist | grep -i cloud`

# 2. Origin còn sống không? (phân biệt 1033 vs 530)
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:3050/
#   200 = origin OK → chắc chắn tunnel chết

# 3. Config + binary ở đâu
cat ~/.cloudflared/config.yml      # ingress map: daily→3050, rag→3001, voice→3100, www/root→3000
ls -la ~/bin/cloudflared            # có thể KHÔNG có .exe
```

## Fix — start lại cloudflared (long-lived → terminal background=true)

```bash
# ĐÚNG (không .exe, absolute path):
/c/Users/datel/bin/cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
# Sai: cd ~/bin && ./cloudflared.exe  → "No such file or directory" (file không có .exe)

# Verify: đợi log "Registered tunnel connection connIndex=0..3 ... location=hkg.. protocol=quic"
# Rồi: curl -sI https://daily.btdat.io.vn/ → 200
```

## Root cause phổ biến — startup bat gọi sai tên file

`btdat-startup.bat` (Startup folder) chạy lúc logon:
```
start "Cloudflare Tunnel" /min cloudflared.exe tunnel --config "..."
```
Nhưng binary là `cloudflared` (không .exe) → bat fail âm thầm, tunnel không bao giờ
dậy sau reboot. Fix: bỏ `.exe`:
```
start "Cloudflare Tunnel" /min cloudflared tunnel --config "C:\Users\datel\.cloudflared\config.yml" run
```

## Lưu ý giữ cloudflared sống

- Chạy qua Hermes `terminal(background=true)` = process con của Hermes session; nếu Hermes
  restart/đóng, tunnel chết. Muốn độc lập: `schtasks` hoặc Windows Service.
- Tránh kill nhầm: phân biệt bằng CommandLine (có `--config ...cloudflared...`),
  PID đổi mỗi boot.
