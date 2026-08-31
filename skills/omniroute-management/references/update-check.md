# Checking for OmniRoute updates (verified 2026-08-17)

OmniRoute **không tự update** — service vẫn chạy bản cũ trên port 20128 cho đến khi restart.

## Commands

- Latest npm: `npm view omniroute version`
- Installed (npm global): `npm ls -g omniroute` hoặc grep `"version"` trong `~/AppData/Roaming/npm/node_modules/omniroute/package.json`
- Process check: `wmic process where "name='node.exe'" get ProcessId,CommandLine | grep -i omniroute` (có thể rỗng — process có thể chạy dưới tên khác; dùng tasklist + lsof nếu cần)
- Update: `npm i -g omniroute@latest` → restart service (ngắt kết nối vài giây)

## Release/changelog sources

- GitHub releases: `https://github.com/diegosouzapw/OmniRoute/releases` — body mỗi release link CHANGELOG.md (release body bị trim ở 125K chars, xem CHANGELOG.md cho đầy đủ)
- API: `curl -sL "https://api.github.com/repos/diegosouzapw/OmniRoute/releases?per_page=3"` (không cần token)
- Cadence ~1-2 tuần/version (vd: 3.8.48 = 07-13 → 3.8.49 = 07-30)

## ⚠️ Pitfall: minor release mới có thể crash khi boot

v3.8.47 (07-13) ship npm tarball thiếu file → crash MỌI boot với `ERR_MODULE_NOT_FOUND` (lần 3 của class này: sau tls-options/3.8.41; hotfix 3.8.48 ra vài giờ sau). Nếu release mới < ~1 tuần, check GitHub releases xem có hotfix chưa TRƯỚC khi upgrade.

## API routes dùng để health check (verified 2026-08-17)

- ✅ `GET /api/models` — danh sách model đầy đủ (cột fullModel + available), filter `?provider=cmd`
- ✅ `GET /v1/models` — OpenAI-compatible list (combo như `auto/best-coding` cũng nằm trong đó)
- ❌ `GET /api/health` và `GET /api/version` — KHÔNG tồn tại → 404 `{"error":{"code":"unknown_route"}}`. Đừng dùng để health check.

## 3.8.48 → 3.8.49 diff highlights (07-30)

- ensureThinkingBudget generalized to all providers
- Effort-tier aliases cho GLM-5.2 & Mimo-V2.5
- OpenRouter embeddings catalog + specialty merge
- Opt-in auto-ping giữ Codex quota window ấm
- Provider mới: Agnes AI (native support)
- 306 commits trong cycle
