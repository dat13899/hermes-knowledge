# Zalo OA production ops — token verify + cron deliver gotchas

Ghi từ phiên vận hành 2026-08-22 (`~/zalo-oa-bot`, port 4810, tunnel `zalo.btdat.io.vn`).

## ✅ Verify access token HỢP LỆ mà KHÔNG gửi tin vào Zalo

Luật: Zalo là kênh khách-chat-bot — **CẤM gửi tin test/quản trị/kiểm tra** (kể cả curl test-send). Muốn xác nhận token còn sống (hoặc token mới thay vào đúng) mà không spam khách → gọi API **chỉ đọc**:

```python
import urllib.request
# TOKEN HỢP LỆ → phân biệt bằng MÃ LỖI, KHÔNG phải "thành công":
#   -216 / -201 / -204        = token hết hạn / sai / không hợp lệ
#   -200 "POST not supported" = API đúng nhưng sai method (thử GET)
#   -240 "UserInfo API shut down, switch to V3" = token ĐÃ QUA XÁC THỰC! (V2 ngừng — đây chính là bằng chứng token OK)
#   404 "empty/invalid API"   = path API sai (không phải lỗi token)
#   => Không gặp -216/-201/-204 => token hợp lệ
AT = open('.env', encoding='utf-8').read()
# test chuẩn:
url = 'https://openapi.zalo.me/v2.0/oa/getfollowers?offset=0&limit=1'
req = urllib.request.Request(url, headers={'access_token': AT}, method='GET')
r = urllib.request.urlopen(req, timeout=15)
print(r.read().decode())   # ra -240 => token OK
```

**Bẫy đã gặp:** 
- `get_profile` / `getfollowers` trả `-200 POST not supported` nếu gọi bằng POST → thử GET.
- Dùng POST mà ra `-240`/`-200` là do sai method, KHÔNG phải token hỏng.
- Tuyệt đối không test bằng gửi tin thật `/v3.0/oa/message/cs` để xác minh (vi phạm luật + tốn quota khách).
- Dùng **Python** để cập nhật/so sánh token — token chứa `/` `-` làm sed fail (`unterminated s`).

## ⚠️ Cron theo dõi token — deliver target sai thì cảnh báo bị NUỐT IM LẶNG

Cron "Check Zalo token" (`check_zalo_token.sh`, 8h sáng) từng **phát hiện đúng** lỗi `-216` (token hết hạn) NHƯNG **không gửi được cảnh báo** cho anh:

```
last_delivery_error: live adapter send failed: Chat not found; delivery error: Telegram send failed: Chat not found (target telegram:Home)
```

→ Hệ quả: bot chết vì token hết hạn mà anh Đạt **không hề được báo**. Chẩn đoán chỉ ra lỗi ở `deliver: telegram:Home` (Home channel chưa được wire đúng / đã đổi).

**Fix:**
- Đổi `deliver` sang `origin` (deliver về chính chat nơi tạo job) hoặc đúng `platform:chat_id` — **KHÔNG dùng `telegram:Home`** trừ khi chắc chắn Home channel còn hoạt động.
- Kiểm tra: `cronjob action=list` → cột `last_delivery_error`. **Rỗng = OK; không rỗng = cảnh báo đang bị nuốt** (kể cả khi `last_status: error`).
- Sau khi thay token mới: **xóa `webhook.log` cũ** (đang chứa `-216` của token đã hết) để lần chạy cron tới không báo lại lỗi cũ.

## Vòng đời token + nơi lấy credentials

- Access token: **25h** (API Explorer) / **1h** (OAuth v4). Refresh token: **3 tháng, dùng 1 lần**.
- API Explorer token → **KHÔNG refresh qua API** (luôn `404 empty api`) → phải lấy thủ công. Chỉ token sinh qua OAuth v4 Authorization Code flow mới refresh được.
- Endpoint refresh: `POST https://oauth.zaloapp.com/v4/oa/refresh_token` — **bắt buộc** header `secret_key = ZALO_APP_SECRET` (KHÔNG phải `ZALO_OA_SECRET_KEY`).
- Nguồn: `ZALO_APP_SECRET` (developers.zalo.me → App → Cài đặt → Secret Key) KHÁC `ZALO_OA_SECRET_KEY` (oa.zalo.me → Cài đặt → Công cụ lập trình → Secret Key, dùng verify webhook).

## Giao diện Zalo — nơi khai báo Callback URL (OA)

- Với **OA**: vị trí chính là `oa.zalo.me → Cài đặt → Official Account Callback URL` (trang quản trị OA, không phải developers.zalo.me). Nếu không thấy ở đó, tìm trong developers.zalo.me → App → Cài đặt → Callback URL / Redirect URI.
- Sau khi điền, mở đúng URL lên browser — ra trang bot (không 404) = OK.
- Lưu ý: trang docs developers.zalo.me render bằng JS + cần đăng nhập → `urllib`/`curl` chỉ lấy được title rỗng; nội dung thật phải qua browser đã đăng nhập.
