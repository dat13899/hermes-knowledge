# Bedrock Server tự host trên Windows

## Download latest version

API lấy link download:

```bash
curl -s "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links" | python -m json.tool
```

Field: `serverBedrockWindows` → URL dạng `https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-{version}.zip`

79.8 MB. Download thường timeout với curl (`exit_code 23` / write error). Dùng Python requests:

```python
import requests
url = "https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.26.33.2.zip"
r = requests.get(url, stream=True, timeout=30, 
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."})
with open("bedrock-server.zip", "wb") as f:
    for chunk in r.iter_content(8192): f.write(chunk)
```

## Tối ưu cho mobile (server.properties)

| Setting | Mặc định | Tối ưu | Tác dụng |
|---|---|---|---|
| view-distance | 32 | **8** | Giảm load chunks |
| max-players | 10 | **5** | Ít người = nhẹ server |
| player-idle-timeout | 30 | **5** | Kick AFK sớm |
| enable-lan-visibility | true | **false** | Tránh port conflict |
| disable-client-vibrant-visuals | #true | **true** | Đt ko render gfx nặng |

## Tunneling khi ko mở port được

### Tailscale (preferred — mạng cty/ko access router)

1. User cài Tailscale trên PC + đt (App Store / play.google.com)
2. Đăng nhập cùng tài khoản Google/GitHub/Microsoft
3. PC và đt join cùng mạng
4. Server chạy port 19132
5. Đt vô Minecraft PE → Add Server → IP là **Tailscale IP của PC** (100.x.x.x), port 19132
6. Không cần config gì thêm

### playit.gg (khi ko dùng Tailscale được)

- Free, no port forward
- **GUI required lần đầu claim:** Agent chạy → show claim URL → mở browser → login → claim
- Nếu trang playit bị chặn (mạng cty), user phải claim từ điện thoại
- Sau khi claim, vào website → Rules → Add Rule: TCP+UDP → 127.0.0.1:19132
- Copy public address (xxx.playit.gg:yyyyy)

**Hạn chế:**
- Trang playit.gg bị chặn ở nhiều mạng VN
- Agent Windows yêu cầu GUI claim (ko headless được)
- Free node chậm, dễ disconnect

## Xác thực Xbox Live

- `online-mode=true` — bắt buộc login Xbox (khuyến cáo)
- Nếu chơi LAN/internal network: có thể set `false`
- `allow-list=false` — ai cũng vô được (tiện), nếu muốn giới hạn thì set `true` + thêm vào `allowlist.json`

## Scripts

**start.bat:**
```bat
@echo off
cd /d %~dp0
start "" bedrock_server.exe
```

**stop.bat:**
```bat
@echo off
taskkill /f /im bedrock_server.exe
```
