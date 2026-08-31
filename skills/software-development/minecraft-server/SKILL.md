---
name: "minecraft-server"
title: "Minecraft Server Management"
description: "Setup, configure, and optimize Minecraft servers — Bedrock (self-hosted) and Aternos (free hosted)"
category: "software-development"
triggers: ["minecraft", "bedrock server", "aternos", "mc server", "minecraft server", "geyser", "self-host minecraft"]
version: "1.0"
---

## Mô tả

Setup, configure, và optimize Minecraft server. Gồm 2 loại:

1. **Self-hosted Bedrock** — chạy trên Windows, dùng `bedrock_server.exe` chính thức từ Mojang
2. **Aternos** — free hosted, quản lý qua python-aternos + dashboard

## Bedrock Server Setup

### Download

Dùng API endpoint chính thức để lấy URL mới nhất:

```bash
curl -s https://net-secondary.web.minecraft-services.net/api/v1.0/download/links | python -c "import sys,json; print([l['downloadUrl'] for l in json.load(sys.stdin)['result']['links'] if l['downloadType']=='serverBedrockWindows'][0])"
```

URL mẫu: `https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-{version}.zip`

**Lưu ý download:**
- File ~80 MB
- Dùng Python `requests` + `stream=True` + `iter_content(8192)` — curl hay urllib.retrieve dễ timeout
- Cần User-Agent trình duyệt (`Mozilla/5.0 ... Chrome/...`)
- API trả về Azure CDN, không cần auth

### Extract

```bash
cd C:\Users\datel\bedrockserver
python -c "import zipfile; zipfile.ZipFile('bedrock-server.zip').extractall('.')"
```

File chính: `bedrock_server.exe` (~200 MB). Cấu hình trong `server.properties`.

### Tối ưu cho mobile (low-end / điện thoại)

Các setting quan trọng trong `server.properties`:

| Setting | Default | Tối ưu | Lý do |
|---|---|---|---|
| `view-distance` | 32 | **5-8** | Chunks tải ít hơn → giảm bandwidth + CPU |
| `max-players` | 10 | **3-5** | Server nhỏ ko cần nhiều slot |
| `player-idle-timeout` | 30 | **5** | Kick người AFK nhanh, tiết kiệm tài nguyên |
| `tick-distance` | 4 | **4** | Ko đổi (tối thiểu là 4) |
| `difficulty` | easy | **peaceful** hoặc **easy** | Peaceful = ko spawn mob → nhẹ hơn |
| `disable-client-vibrant-visuals` | (commented) | **true** | Nếu có — tắt hiệu ứng xa hoa trên client |
| `enable-lan-visibility` | true | **false** | Ko cần nếu chơi qua external IP |
| `allow-list` | true | **false** | Nếu muốn cho ai cũng vào |
| `online-mode` | true | **true** | Giữ nguyên — xác thực Xbox bắt buộc cho remote |

### Start server

```batch
start /B /WAIT bedrock_server.exe
```

Server chạy console mode, port mặc định **19132** (UDP). Log hiển thị trực tiếp ra terminal.

## Self-hosted vs Aternos

| | Self-hosted (Bedrock) | Aternos (free) |
|---|---|---|
| Ping (VN) | **1-10 ms** (LAN) | ~200-300 ms (EU server) |
| RAM | ~300-500 MB | ~1-2 GB (limited) |
| Chạy 24/7 | Tuỳ a bật máy | Tắt sau idle, cần start lại |
| Cấu hình | Full control (`server.properties`) | Limited (ko chỉnh được qua API) |
| Plugin | Không có (Bedrock) | Không có |
| Chi phí | Điện + internet | Free (có queue) |
| Setup | Cần port forwarding | Ko cần |

## Aternos via python-aternos

Xem skill `local-service-dashboard` + `references/aternos-python-sdk.md` trong skill đó.

Tóm tắt:

```python
from python_aternos import Client
at = Client()
at.login('username', 'password')
s = at.account.list_servers()[0]
s.fetch()
print(s.status)  # 'offline' | 'online' | 'starting' | 'waiting'
s.start()
s.confirm()  # nếu queue
s.stop()
```

Status: `Status.off=0`, `Status.on=1`, `Status.starting=2`, `Status.loading=6`, `Status.error=7`, `Status.preparing=10` (queue/waiting).

**Auto-confirm start**: gọi `s.start()`, poll `s.status` 6 lần x 5s, nếu `preparing` → `s.confirm()`.

## Java + GeyserMC vs Bedrock gốc

| | Bedrock gốc | Java + Geyser |
|---|---|---|
| Engine | C++ (nhẹ) | Java (nặng) |
| RAM | ~300-500 MB | ~1-2 GB |
| Ping mobile | Thấp nhất | +5-15ms do translate |
| Plugin | Hạn chế | Vô số (Bukkit/Spigot/Paper) |
| Client | Chỉ Bedrock | Java + Bedrock (qua Geyser + Floodgate) |

Nếu chỉ chơi mobile → **Bedrock gốc** mượt hơn. Nếu muốn cả 2 → Java + Geyser (tốn tài nguyên hơn).

## Bedrock mobile version matching

- Điện thoại cần cùng phiên bản với server
- Server version = client version (Bedrock auto-update trên store)
- Aternos tự cập nhật bản mới
- Self-hosted: tải bản mới từ API → giải nén đè lên folder cũ (giữ `server.properties`, `worlds/`, `allowlist.json`)

## Pitfalls

- **Download timeout**: URL từ Azure CDN, dùng Python `requests` với `stream=True`, không dùng `curl` hoặc `urllib.request.urlretrieve` (dễ timeout vì file 80MB)
- **server.properties ko apply sau khi world tạo**: `force-gamemode` = false → server dùng value saved trong world, ignore giá trị trong file. Set `force-gamemode=true` nếu muốn ép.
- **online-mode=true bắt buộc**: Remote (non-LAN) ko thể tắt Xbox auth. Chơi LAN thì offline-mode OK.
- **Port forwarding**: Cần mở port **19132** UDP trên router cho remote connect. Ko mở được → chỉ chơi LAN.
- **Aternos config ko support Bedrock**: `cfg.set_server_prop()` không hoạt động với Bedrock server, chỉ Java.
- **Aternos EU-only**: Free tier chỉ có server EU. Ping VN ~200ms+.
- **python-aternos lxml bug**: `pip install` lỗi Access Denied → dùng `--no-deps` + cài `requests` `cloudscraper` riêng.
