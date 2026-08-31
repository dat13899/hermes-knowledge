#!/usr/bin/env python3
# Kiểm tra Zalo access token — CHỈ đọc log cục bộ, KHÔNG gửi gì vào Zalo.
# Output non-empty → Hermes deliver qua Telegram cho anh Đạt.
import os, re, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

HOME = Path.home()
LOG = HOME / "zalo-oa-bot" / "webhook.log"
ENV = HOME / "zalo-oa-bot" / ".env"

token = ""
try:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("ZALO_ACCESS_TOKEN="):
                token = line.split("=", 1)[1].strip()
                break
except: pass

if not token:
    print("⚠️ ZALO_ACCESS_TOKEN trống trong .env — cần điền token mới")
    sys.exit(0)

# 24h gần đây có lỗi -216 (token expired) không?
if LOG.exists():
    try:
        text = LOG.read_text(encoding="utf-8", errors="ignore")
        # tìm dòng chứa -216
        recent = None
        for line in text.splitlines():
            if "-216" in line:
                recent = line
        if recent:
            m = re.search(r"\[([0-9T:.Z\-+]+)\]", recent)
            ts = m.group(1) if m else recent[:30]
            print(f"🔴 Zalo máy phát hiện lỗi token hết hạn (-216) lúc {ts}")
            print("→ Cần lấy token mới: https://developers.zalo.me/tools/explorer → Get Access Token")
            print("→ Gửi token mới cho Cu em cập nhật .env (access token sống 25h).")
            sys.exit(0)
    except: pass

# Gửi tin thành công trong 25h gần đây → token OK, im lặng
try:
    if LOG.exists():
        text = LOG.read_text(encoding="utf-8", errors="ignore")
        last_send = None
        for line in text.splitlines():
            if "[SEND]" in line:
                last_send = line
        if last_send:
            m = re.search(r"\[([0-9T:.Z\-+]+)\]", last_send)
            if m:
                ts_raw = m.group(1)
                # parse ISO
                try:
                    # 2026-08-26T08:00:00.000Z hoặc với timezone
                    ts_raw2 = ts_raw.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts_raw2)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    diff_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    if diff_h < 25:
                        sys.exit(0)  # token OK — im lặng
                except: pass
except: pass

print("ℹ️ Zalo máy chưa xác định trạng thái token (không có log gửi tin 25h gần đây).")
print("→ Nếu khách nhắn mà bot không trả lời, cần lấy token mới từ developers.zalo.me/tools/explorer.")
