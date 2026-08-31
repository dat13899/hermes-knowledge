Tên của Hermes Agent này (tôi/em) là "Cu em". Là đệ của Anh Đạt.
§
'Điểm tin sáng' cron (d555ab2a98ca) daily 7AM via ddgs + agent-daily-briefing. VN+world+tech+World Cup news → Telegram.
§
dlv: ~/dlv/dlv.py. yt-dlp via uv. <50MB→MEDIA, ≥50MB→catbox. React: fix 1 bug mà vẫn crash→kiểm tra props+imports cha-con.
§
Prefer inline MEDIA: images.
§
UX: khó nhìn→fix contrast trước (accent ≥#ad80ff); 'var(--x)' trong JSX phải quote (crash esbuild). Hermes config: dùng `hermes config set` (KHÔNG sửa config.yaml trực tiếp); memory limits hiệu lực phiên sau. Chuẩn UI/UX → skill web-ui-standards.
§
Pref: ghi quy trình vào SKILL.md body; support files → skill_manage write_file references/. Ưu tiên (1) patch skill/memory sẵn có, (2) chỉ tạo skill mới khi tên dùng lâu dài.
§
codegraph_explore MCP (mcp-codegraph): projectPath là REQUIRED — luôn truyền "C:/Users/datel/service-dashboard" hoặc ~/omniroute.
§
Đừng kill quick tunnel OmniRoute (cloudflared --url 127.0.0.1:20128); phân biệt cloudflared bằng CommandLine, PID đổi mỗi boot.
§
btdat.io.vn (đang chạy) = service-dashboard: node server.js port 3000 serve dist/, tunnel cloudflared PID đổi mỗi boot. Đã gỡ route /rune (game rune-fate xoá 27/08), giữ /liquid-glass. Restart server: kill-node.sh rồi node server.js nền.
§
daily.btdat.io.vn V2 (10/08): cấm game 2 ngày liên tiếp, ưu tiên app/tool/viz, ≥3 màn hình, WebAudio, touch+keyboard, Roboto Mono. Cron 62c3fee9aaf7.
§
Agency Agents plugin (agency-agents-router): 4 tools agency_agents_* sẵn mọi session; repo clone ~/agency-agents. Chi tiết → skill agency-agents.
§
OmniRoute (20128): vision=deepseek-v4-flash-vision-exp CHẠY (default+aux); MiniMax-M3 chạy; aug/* SSE rỗng, Gemini MODEL_NOT_IN_PLAN. Model picker đã lọc còn 39 command-code (providers.omniroute discover_models:false + models dict; xoá legacy custom_providers 'Local 127.0.0.1') — chi tiết skill omniroute-management.
§
zalo-oa-bot (~/zalo-oa-bot, 4810, zalo.btdat.io.vn): OA Zalo cho bhviet.vn — verify sha256(appId+body+ts+OAsecret) KHÔNG HMAC, luôn 200. Token API Explorer 25h KHÔNG refresh được (404)→lấy thủ công, cron 8h; curl VN từ bash→lỗi font (dùng TS script). KB SQLite + admin /admin. Chi tiết → skill zalo-oa-bot.
§
Skill 'angular' (frontend/angular): best-practices chính thức v22 (standalone, signals, OnPush mặc định, SSR/hydration/incremental hydration, signal forms, CLI MCP server, Agent Skills). Reference: references/angular-best-practices-prompt.md. Dùng khi code/review/migrate/setup Angular.
§
angular.btdat.io.vn = Angular 22 demo (D:\angular-demo, SSR port 4300, tunnel cloudflared). Đạt chọn stack B: Angular Material 22 + SCSS thuần + design tokens, BỎ Tailwind v4 (gây vỡ layout). Làm Angular UI → verify bằng mắt Chrome thật (chụp + vision), không chỉ đo headless.
§
diagram-service (:3100): chat() cần setTimeout+destroy (tránh hang khí gateway chết); /list trả JSON hoặc HTML; restart netstat :3100 + taskkill + node server.js nền.