# Telegram Multi-Bot — gateway per-profile

Mỗi profile cần gateway riêng nếu muốn token Telegram riêng.

## Setup

```bash
# 1. Set API key thật (không dummy)
hermes -p coder config set providers.omniroute.api_key <REAL_KEY>
hermes -p reviewer config set providers.omniroute.api_key <REAL_KEY>

# 2. Cấu hình Telegram (hoặc hermes gateway setup)
hermes -p coder gateway setup   # chọn telegram, dán token bot riêng
hermes -p reviewer gateway setup

# 3. Cài service auto-start
hermes -p coder gateway install
hermes -p reviewer gateway install

# 4. Verify
hermes gateway list
# phải thấy: default ✓, coder ✓, reviewer ✓
```

## Lưu ý

- `~/.hermes/profiles/<bot>/.env` phải có token riêng — không share token giữa bot.
- Windows: `hermes gateway install` tạo Scheduled Task `Hermes_Gateway_<profile>`, tự chạy lại sau reboot. Check `taskschd.msc`.
- `group_sessions_per_user` ở main config ảnh hưởng tất cả profile nếu không override. Để group Telegram chung 1 session: `hermes config set group_sessions_per_user false`.
- Log: `~/.hermes/profiles/<bot>/logs/` hoặc `hermes -p <bot> logs`.
