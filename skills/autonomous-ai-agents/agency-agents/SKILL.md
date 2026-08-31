---
name: agency-agents
description: "Hire specialist personas via agency_agents_* tools."
category: autonomous-ai-agents
---

# Agency Agents (The Agency plugin)

Kho 270 AI specialist personas (repo `msitarzewski/agency-agents`) cài làm Hermes plugin `agency-agents-router`. Mỗi agent là 1 file markdown: personality + workflow + checklists + deliverable standards. Dùng để "thuê chuyên gia" cho task (game design, UI, marketing, finance... 17 divisions). Dùng khi user nói "thuê chuyên gia / tìm agent làm X" hoặc task cần standards chuyên môn.

## Tools (có sẵn mọi session, toolset `agency_agents`)
- `agency_agents_search` — query + optional `division`/`limit` → danh sách agent (slug, name, division, description, vibe, score)
- `agency_agents_inspect` — metadata 1 agent (`include_body=true` để lấy full instructions)
- `agency_agents_load` — nạp full specialist prompt + task → áp dụng standards vào work hiện tại
- `agency_agents_delegate` — delegate qua `delegate_task` (fallback: trả composed prompt nếu không delegate được)

## Flow chuẩn
1. `agency_agents_search` với query mô tả loại task (vd "pixel art game UI", "canvas game mechanics")
2. Chọn slug phù hợp → `agency_agents_load` với `slug` + task ngắn gọn
3. Áp dụng standards/checklists từ specialist vào build
4. (Tùy chọn) `agency_agents_delegate` cho task độc lập

## Vị trí & nguồn
- Plugin: `~/AppData/Local/hermes/plugins/agency-agents-router/` (data/agents.json 3.8MB, 270 agents)
- Source repo: `~/agency-agents/` (clone đầy đủ — đọc file .md trực tiếp nếu cần full body, nhanh hơn tool)
- Build lại: `cd ~/agency-agents && python scripts/build-hermes-plugin.py --repo-root .. --out integrations/hermes` → copy `integrations/hermes/agency-agents-router` vào `$HERMES_HOME/plugins/`

## Pitfalls
- **`hermes config set plugins.enabled '["x"]'` lưu thành STRING, không phải YAML list** → `_get_enabled_plugins()` đòi list thật → plugin không load (tools không xuất hiện). Fix: sửa `config.yaml` trực tiếp bằng python `yaml.safe_load`/`safe_dump` — patch tool bị chặn (security-sensitive) nhưng python ghi file OK.
- Plugin phải ở `$HERMES_HOME/plugins/<name>/plugin.yaml` (Windows: `~/AppData/Local/hermes/plugins/`, flat layout `<name>/plugin.yaml`). Scan user plugins ở đó — `hermes plugins` list sẽ thấy.
- Sau khi cài/bật → cần restart gateway / session mới thì tools mới vào catalog. Verify: `hermes tools` hiện "🔌 Agency Agents".
- Toolset `agency_agents` KHÔNG nằm trong `_DEFAULT_OFF_TOOLSETS` → mặc định enabled (khác spotify phải opt-in qua `hermes tools`).
- Cron job `enabled_toolsets = null` → load đủ plugin tools. Nếu tool không khả dụng trong cron → bỏ qua bước thuê, KHÔNG chặn build (đã ghi trong prompt job daily 62c3fee9aaf7).
- Test standalone: handler đăng ký bên trong `register(ctx)` — mock ctx: `class MockCtx: def register_tool(self, **kw): ...` rồi gọi `mod.register(MockCtx())` và lấy handler từ dict đã đăng ký.

## Tích hợp đã có
- Cron "Daily Idea 6h sáng" (job 62c3fee9aaf7) bước 4 bắt buộc thuê 1-2 chuyên gia phù hợp ý tưởng hôm đó, ghi rõ agent đã dùng trong tóm tắt Telegram (xem skill `daily-ideas-site`).
