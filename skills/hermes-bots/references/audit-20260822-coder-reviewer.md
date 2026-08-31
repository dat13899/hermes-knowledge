# Audit 2026-08-22 — coder / reviewer (Group-Room Bot)

Ngày: 2026-08-22, user: Tiến Đạt, session: Group-Room Bot nghiên cứu cấu hình 2 bot cho chuẩn.

## Kết quả audit

- `hermes profile list`: default (running), coder (stopped), reviewer (stopped) — 82 skills mỗi profile.
- `hermes profile show coder/reviewer`: SOUL.md generic Hermes mặc định, config.yaml chỉ 4 dòng `model: command-code/deepseek/deepseek-v4-flash` + `api_key: dummy`, `.env` trống, `profile.yaml` thiếu `ui_meta.hermes-bots`.
- `group_sessions_per_user: true` chỉ ở main config (`~/.hermes/config.yaml`), profile-level `not set`.
- Gateway: chỉ default PID 12364 running, coder/reviewer không có Scheduled Task riêng.

## Nguyên nhân

Tạo bằng `hermes profile create` tay, không qua Desktop > Bots > New Agent. Thiếu avatar/blob-face, Bot Chat forever-chat (`BOT_CHAT_TITLE="Bot Chat"`), và gate `tools/bot_mode_probe.py` + `tools/bot_mode_dm.py` không inject `message_agent`.

## Cách fix đã đề xuất

1. Tạo lại qua Desktop Bots tab để có `ui_meta.hermes-bots`, hoặc patch `profile.yaml`.
2. Tách SOUL (coder=pro code, reviewer=QA), model pin riêng, skills/toolsets thu gọn.
3. Fix `api_key: dummy` → real OmniRoute key.
4. `hermes -p <bot> gateway install` nếu cần Telegram multi-bot.
5. Tạo Group-Room: Bots tab → Create group chat → `Group: Dev Room` (v0.20.5 group-room threads).

## Link tham chiếu

- Docs: https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode
- Source: `apps/desktop/src/plugins/hermes-bots/plugin.js`, `tools/bot_mode_dm.py`, `tools/bot_mode_probe.py`, `agent/system_prompt.py` (gate `agent.bot_mode_protocol`)
- Changelog v0.20.5: Bot Mode group-room threads
