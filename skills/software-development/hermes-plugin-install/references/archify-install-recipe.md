# Install Agent Skill từ GitHub — Recipe Archify (2026-08-30)

Đây là ví dụ thực tế cài một repo **Agent Skill** (SKILL.md package, không phải tool plugin) vào
Hermes trên Windows/git-bash. Repo: `tt-a1i/archify` (32k★, MIT) — vẽ sơ đồ kiến trúc
tương tác. Package gốc nằm ở **subdir `archify/`** chứ SKILL.md + code renderer JS.

## Kết quả cuối
Skill nằm tại `C:/Users/datel/AppData/Local/hermes/skills/archify/` (190 files, ~7.6MB),
`SKILL.md` ở ngay level gốc. `npm install` + `node bin/archify.mjs doctor` pass toàn bộ.
Demo render `examples/web-app.architecture.json` ra HTML 729KB + sha256 receipt, validate pass.

## Các bước (rút ra từ lần cài thật, tránh lỗi đã gặp)

### 1. Clone VỀ WINDOWS TEMP, không dùng MSYS `/tmp`
Trên git-bash, `/tmp/archify-repo` resolve sai → `cp: cannot stat '/tmp/...'`.
```bash
git clone --depth 1 https://github.com/tt-a1i/archify.git \
  "C:/Users/datel/AppData/Local/Temp/archify-repo"
```

### 2. ĐỪNG copy cả repo root — chỉ copy subdir chứa package
Repo này có SKILL.md ở `archify/` (subdir), không phải root. Copy cả root sẽ lẫn
`README*.md`, `docs/`, `CHANGELOG.md`, `.git`, `archify.zip`... vào skill.
```bash
cd "C:/Users/datel/AppData/Local/hermes/skills"
rm  -rf archify_backup_old archify          # dọn bản lẫn trước đó
cp  -r "C:/Users/datel/AppData/Local/Temp/archify-repo/archify" ./archify
# xác nhận SKILL.md nằm ngay gốc:
ls  archify/SKILL.md  archify/bin  archify/schemas  archify/renderers  archify/package.json
```
> Pitfall đã dính: `cp -r X/. dest` khi `dest` vừa bị tạo rỗng sẽ copy cả tree lồng nhau
> (`archify/archify/...`). `rm -rf` rồi tạo lại sạch, copy bằng path subdir, là an toàn nhất.

### 3. Cài deps + verify trong skill dir
```bash
cd "C:/Users/datel/AppData/Local/hermes/skills/archify"
npm install                        # 10 packages, 0 vulnerabilities
node bin/archify.mjs doctor        # phải toàn bộ [ok]
node bin/archify.mjs --help        # xem subcommand: render/deliver/validate/check...
```

### 4. Render + verify output thật trước khi nói "xong"
```bash
node bin/archify.mjs deliver architecture examples/web-app.architecture.json \
  "C:/Users/datel/AppData/Local/Temp/archify-demo.html" --json   # trả sha256 + bytes
node bin/archify.mjs check        "<output.html>"                  # validate HTML/SVG
# chụp screenshot headless để xem bằng mắt (vision):
chrome.exe --headless=new --disable-gpu --hide-scrollbars \
  --virtual-time-budget=5000 --window-size=1600,1000 \
  --screenshot="C:/.../archify-demo.png" "file:///C:/.../archify-demo.html"
```
`validate`/`check` trả `ok:true` với các checks: single_svg, orthogonal_arrows,
relationship_corridors, label_route_clearance... Kèm `sha256` receipt là bằng chứng tra cứu.

> `visual-check` cần Chrome (báo `visualReview: pending` + cần executable) — chỉ chạy khi có
> muốn review bằng mắt, không phải bước bắt buộc để coi là render thành công.

## Nhận xét chất lượng (so với skill architecture-diagram cũ)
Archify có typed JSON IR (agent viết JSON, render deterministic), validation atomic trước khi
thay artifact, dark/light theme, motion hữu hạn, 5 loại sơ đồ (architecture/workflow/sequence/
dataflow/lifecycle), export PNG/JPEG/WebP/SVG/WebM + share card. Mạnh hơn hẳn skill SVG tĩnh cũ.
