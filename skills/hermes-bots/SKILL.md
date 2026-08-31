---
name: hermes-bots
description: "Bot Mode profiles, group-room threads and multi-gateway."
version: 1.0.0
author: Cu em
platforms: [linux, macos, windows]
triggers:
  - cấu hình Bot Mode / group-room / 2 bot coder reviewer
  - hermes profile / gateway cho nhiều bot
  - group_sessions_per_user và group chat giữa các bot
  - SOUL.md phân vai, model pin, skills/toolsets per-bot
---

# Hermes Bots — Bot Mode, Profiles as Bots, Group-Room & Multi-Gateway

Mỗi **Bot = 1 Hermes profile** (`~/.hermes/profiles/<name>/` — isolated config, memory, skills, credentials, chat history). Bot Mode là UI trên primitive này (Desktop > Bots tab). Không có primitive mới.

## Khi nào dùng skill này
- User nói "Group-Room Bot", "2 con bot", "coder / reviewer", "bot mode"
- Audit / chuẩn hóa profile: SOUL, model, skills, gateway, keepalive
- Tạo Group-Room thread (Bot Mode group chat) hoặc Telegram group multi-bot
- Fix `api_key: dummy`, gateway `stopped`, SOUL generic, thiếu `ui_meta.hermes-bots`

## Audit checklist (chạy trước khi sửa)

```bash
hermes profile list
hermes profile show coder
hermes profile show reviewer
hermes gateway list          # default running? coder/reviewer stopped?
cat ~/AppData/Local/hermes/profiles/coder/config.yaml
cat ~/AppData/Local/hermes/profiles/coder/SOUL.md
cat ~/AppData/Local/hermes/profiles/coder/profile.yaml  # phải có ui_meta.hermes-bots
hermes -p coder config get group_sessions_per_user  # profile-level thường not set, default ở main config
cat ~/AppData/Local/hermes/config.yaml | grep group_sessions_per_user
```

7 điểm chuẩn:
1. SOUL phân vai rõ (không generic)
2. Model pin riêng (coder=pro, reviewer=flash/thinking)
3. Toolsets/skills thu gọn theo vai
4. Memory riêng (memory_enabled + seed)
5. api_key thật (không dummy)
6. Avatar + Bot Chat canonical = tạo qua Desktop Bots tab (sinh `profile.yaml: ui_meta.hermes-bots`, blob-face, `/new`→`/compact`)
7. Group-Room thread + routine (cron) nếu cần

## Hai kiểu "group" — đừng nhầm

| Kiểu | Ở đâu | Config | Dùng khi |
|---|---|---|---|
| **Desktop Group-Room** (Bot Mode) | Desktop > Bots > Create group chat | Tự sinh `Group: ...` session, `@mention` + `message_agent` tool | Anh + coder + reviewer bàn chung 1 thread |
| **Telegram Group** (gateway) | `platforms.telegram` + `group_sessions_per_user: true` (main config) | `true` = mỗi user trong group Telegram có session riêng; `false` = cả group chung 1 session | Nhiều người chat bot trong group Telegram |

Group-Room Threads (v0.20.5): `Bot Mode group-room threads — thread nhóm cho Bot Mode` — cho phép thread riêng trong group-room, không spam roster.

## Chuẩn hóa theo Bot Mode Desktop (khuyên dùng)

**Tạo qua Desktop, không `hermes profile create` tay** (tay tạo sẽ thiếu `ui_meta`, avatar, Bot Chat forever-chat):

- New Agent → Name `coder` → Title `Senior Coder` → Description `Chuyên viết code, refactor, tạo PR`
  - Advanced: Model `cmd/deepseek/deepseek-v4-pro`, SOUL coder, tick `terminal, file, code_execution, github, delegation`
- New Agent → Name `reviewer` → Title `Code Reviewer` → Description `Chuyên review, QA, bảo mật`
  - Model `cmd/deepseek/deepseek-v4-flash`, tick `file, github, delegation`, skill `code-review-agent`

SOUL mẫu xem `references/bot-soul-templates.md`.

Tạo Group-Room: Bots tab → Create group chat → chọn coder + reviewer → `Group: Dev Room` → chat `@coder làm feature X` / `@reviewer review`.

`message_agent` tool (Bot Chat only, fire-and-forget): code tham chiếu `tools/bot_mode_dm.py`, `tools/bot_mode_probe.py`, gate `BOT_CHAT_TITLE="Bot Chat"` + `agent.bot_mode_protocol` (default True). Không tự hand-assemble `hermes -p <bot> chat ...`.

## Chuẩn hóa Telegram multi-bot (nếu cần)

```bash
hermes -p coder config set providers.omniroute.api_key <real>
hermes -p reviewer config set providers.omniroute.api_key <real>
hermes -p coder gateway install   # Windows Scheduled Task per-profile
hermes -p reviewer gateway install
hermes gateway list  # cả 3 phải running
```
`coder/.env` và `reviewer/.env` phải có token riêng (không share). Xem `references/telegram-multi-bot.md`.

## Pitfalls

- `api_key: dummy` trong profile config → OmniRoute 401, bot im lặng.
- `hermes profile create` tay → thiếu `profile.yaml: ui_meta.hermes-bots` → không có Bot Chat, không hiện trong roster đúng cách. Fix: tạo lại qua Desktop hoặc patch profile.yaml.
- Gateway `stopped` cho coder/reviewer → Telegram không trả lời dù default running. Mỗi profile cần gateway riêng hoặc dùng Bot Mode routing (single gateway + `@mention`).
- SOUL generic giống nhau → 2 bot trả lời y hệt. Phải tách vai (coder vs reviewer).
- `group_sessions_per_user` chỉ ở main config (`hermes config get`), profile-level thường `not set` — đừng set per-profile nếu không hiểu.
- `message_agent` chỉ có trong canonical `Bot Chat` trên install có Bot Mode managed; không có trong CLI thường, group-room member sessions (`Group: ...`), cron, subagent.
- Desktop remote creation: `Clone source` là profile của máy đích, `Create on` picker chỉ hiện khi có nhiều Connections.

## Verify

```bash
hermes profile list
hermes gateway list
hermes -p coder chat -q "ping"
# Desktop: Bots tab hiện 2 bot + Active now strip, Group: Dev Room, @mention hoạt động
```

Chi tiết audit phiên 2026-08-22 và transcript group-room: `references/audit-20260822-coder-reviewer.md`.
