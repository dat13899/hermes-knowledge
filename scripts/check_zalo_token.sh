#!/bin/bash
# Kiểm tra Zalo access token — CHỈ đọc log cục bộ, KHÔNG gửi gì vào Zalo.
# Output non-empty → Hermes deliver qua Telegram cho anh Đạt.
LOG=~/zalo-oa-bot/webhook.log
TOKEN=$(grep '^ZALO_ACCESS_TOKEN=' ~/zalo-oa-bot/.env | cut -d= -f2)

if [ -z "$TOKEN" ]; then
  echo "⚠️ ZALO_ACCESS_TOKEN trống trong .env — cần điền token mới"
  exit 0
fi

# 24h gần đây có lỗi -216 (token expired) không?
if [ -f "$LOG" ]; then
  RECENT=$(grep -- "-216" "$LOG" 2>/dev/null | tail -1)
  if [ -n "$RECENT" ]; then
    TS=$(echo "$RECENT" | grep -o '^\[[0-9T:.Z-]*\]' | tr -d '[]')
    echo "🔴 Zalo máy phát hiện lỗi token hết hạn (-216) lúc $TS"
    echo "→ Cần lấy token mới: https://developers.zalo.me/tools/explorer → Get Access Token"
    echo "→ Gửi token mới cho Cu em cập nhật .env (access token sống 25h)."
    exit 0
  fi
fi

# Gửi tin thành công trong 25h gần đây → token OK, im lặng
LAST_SEND=$(grep "\[SEND\]" "$LOG" 2>/dev/null | tail -1)
if [ -n "$LAST_SEND" ]; then
  TS=$(echo "$LAST_SEND" | grep -o '^\[[0-9T:.Z-]*\]' | tr -d '[]')
  LAST_EPOCH=$(date -d "$TS" +%s 2>/dev/null || echo "")
  if [ -n "$LAST_EPOCH" ]; then
    DIFF=$(( ($(date +%s) - LAST_EPOCH) / 3600 ))
    if [ "$DIFF" -lt 25 ]; then
      exit 0  # token OK — im lặng
    fi
  fi
fi

# Không chắc chắn → nhắc nhẹ qua Telegram
echo "ℹ️ Zalo máy chưa xác định trạng thái token (không có log gửi tin 25h gần đây)."
echo "→ Nếu khách nhắn mà bot không trả lời, cần lấy token mới từ developers.zalo.me/tools/explorer."
