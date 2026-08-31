# Minecraft Bedrock Server Download API

## Official API endpoint

```
GET https://net-secondary.web.minecraft-services.net/api/v1.0/download/links
```

Returns JSON với `result.links` array, mỗi entry:
- `downloadType`: một trong `serverBedrockWindows`, `serverBedrockLinux`, `serverBedrockPreviewWindows`, `serverBedrockPreviewLinux`, `serverJar`
- `downloadUrl`: URL tải về

## Response mẫu

```json
{
  "result": {
    "links": [
      {
        "downloadType": "serverBedrockWindows",
        "downloadUrl": "https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.26.33.2.zip"
      },
      {
        "downloadType": "serverBedrockLinux",
        "downloadUrl": "https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-1.26.33.2.zip"
      },
      {
        "downloadType": "serverJar",
        "downloadUrl": "https://piston-data.mojang.com/v1/objects/.../server.jar"
      }
    ]
  }
}
```

## URL pattern

```
# Windows
https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-{version}.zip

# Linux
https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-{version}.zip
```

**Lưu ý**: trước đây URL ở `minecraft.azureedge.net/bin-win/` — đã đổi sang `minecraft.net/bedrockdedicatedserver/` từ cuối 2024.

## Download script mẫu (Python)

```python
import requests

url = 'https://net-secondary.web.minecraft-services.net/api/v1.0/download/links'
r = requests.get(url, timeout=15)
links = r.json()['result']['links']
dl = [l for l in links if l['downloadType'] == 'serverBedrockWindows'][0]['downloadUrl']

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(dl, headers=headers, stream=True, timeout=30)
with open('bedrock-server.zip', 'wb') as f:
    for chunk in resp.iter_content(8192):
        f.write(chunk)

# File ~80 MB, extract with:
import zipfile
zipfile.ZipFile('bedrock-server.zip').extractall('.')
```

## Known URLs (fallback nếu API down)

- Win: `https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.26.33.2.zip`
- Linux: `https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-1.26.33.2.zip`
- Preview Win: `https://www.minecraft.net/bedrockdedicatedserver/bin-win-preview/bedrock-server-1.26.40.30.zip`
- Java server JAR: `https://piston-data.mojang.com/v1/objects/823e2250d24b3ddac457a60c92a6a941943fcd6a/server.jar`

## Pitfalls

- curl thường timeout / trả về empty → dùng Python requests
- Cần User-Agent trình duyệt, ko thì Azure CDN reject
- HEAD request cũng timeout → dùng GET + stream
- Server version đổi theo update Minecraft (check API để lấy link mới nhất, ko hardcode version)
