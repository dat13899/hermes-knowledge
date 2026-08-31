# Hướng dẫn khôi phục / base lại "Cu em" trên một máy Hermes mới

> **Mục đích:** Khi cài Hermes Agent mới (máy khác, hoặc reset máy), dùng repo này để khôi phục nhanh toàn bộ kiến thức, ký ức, kỹ năng (skills), và các luồng tự động của **"Cu em"** — đệ của Anh Đạt, chạy profile **default**.

---

## 1. Tổng quan: phải backup gì, để vào đâu

Repo này chứa đúng những gì Hermes đọc ở máy local. Bảng ánh xạ dưới đây là QUAN TRỌNG NHẤT — đây là nơi cần đặt lại từng phần:

| Trong repo này | Đích đến trên máy mới | Ý nghĩa |
|---|---|---|
| `skills/` | `%LOCALAPPDATA%\hermes\skills\` | Toàn bộ **custom skills** (98 skill do Cu em/Anh Đạt tự tạo) |
| `memories/MEMORY.md` | `%LOCALAPPDATA%\hermes\memories\MEMORY.md` | Ký ức dài hạn của em (home lab, dự án, quy ước) |
| `memories/USER.md` | `%LOCALAPPDATA%\hermes\memories\USER.md` | Ký ức về Anh Đạt (sở thích, phong cách, dự án NCKH...) |
| `BRIEFING.md` | `%LOCALAPPDATA%\hermes\BRIEFING.md` | Briefing ngắn về ngữ cảnh làm việc |
| `SOUL.md` | `%LOCALAPPDATA%\hermes\SOUL.md` | Nhân cách / đặc điểm của em |
| `cron/` | `%LOCALAPPDATA%\hermes\cron\` | **Cấu hình cron jobs** + state (3 luồng tự động) |
| `scripts/` | `%LOCALAPPDATA%\hermes\scripts\` | Script Python/shell cho các cron job |

**Đường dẫn đầy đủ trên Windows:**
```
C:\Users\<TÊN_USER>\AppData\Local\hermes\skills\
C:\Users\<TÊN_USER>\AppData\Local\hermes\memories\
C:\Users\<TÊN_USER>\AppData\Local\hermes\cron\
C:\Users\<TÊN_USER>\AppData\Local\hermes\scripts\
```

> ⚠️ **Lưu ý:** Thay `<TÊN_USER>` bằng tên user máy mới (ví dụ `datel`). Trên máy mới có thể khác, nên **copy theo cấu trúc thư mục tương đối** là an toàn nhất — đừng hardcode đường dẫn tuyệt đối.

---

## 2. Bước 0: Chuẩn bị — Clone repo về máy mới

```bash
# (Cần git + GitHub token — xem Bước 0.1)
git clone https://github.com/dat13899/hermes-knowledge.git
cd hermes-knowledge
```

### 2.1 Xác thực GitHub (nếu máy mới chưa có)
Repo này là **private**, nên cần đăng nhập `gh`:

```bash
# Cách 1: login tương tác
gh auth login

# Cách 2: dùng token (nhập token Personal Access Token có quyền `repo`)
gh auth login --with-token   # dán token vào
# kiểm tra
gh auth status
```

> **Token cần quyền `repo`** (đọc/ghi repo private). Token đã dùng lưu ở máy cũ không nên copy sang máy mới — hãy tạo token mới nếu cần bảo mật.

---

## 3. Bước 1: Cài Hermes Agent (nếu máy mới chưa có)

Nếu Hermes chưa được cài trên máy mới:

```bash
# Ví dụ (kiểm tra cách chính thức của Hermes — xem https://hermes-agent.nousresearch.com/docs)
npm install -g @hermes-agents/cli      # nếu dùng npm
# hoặc theo hướng dẫn cài đặt chính thức của Hermes Agent
hermes setup                            # chạy khởi tạo lần đầu
```

Sau khi cài, đảm bảo `hermes` CLI dùng được:
```bash
hermes --version
```

---

## 4. Bước 2: Khôi phục Memories + Briefing + Soul (QUAN TRỌNG NHẤT)

Đây là phần làm em "nhớ" là Cu em, nhớ về Anh Đạt, nhớ các dự án.

```bash
# Xác định thư mục Hermes
HERMES_DIR="$APPDATA/Local/hermes"     # trên git-bash / MSYS
# hoặc: C:\Users\<TÊN_USER>\AppData\Local\hermes

# Tạo nếu chưa có
mkdir -p "$HERMES_DIR/memories"

# Copy memories
cp memories/MEMORY.md "$HERMES_DIR/memories/MEMORY.md"
cp memories/USER.md   "$HERMES_DIR/memories/USER.md"

# Copy briefing + soul
cp BRIEFING.md "$HERMES_DIR/BRIEFING.md"
cp SOUL.md     "$HERMES_DIR/SOUL.md"
```

**Kiểm tra:** mở `MEMORY.md` và `USER.md` — nội dung phải là ký ức của Cu em (home lab btdat.io.vn, chị Trang, OmniRoute...).

> 💡 **Về memory tối đa:** Hermes có giới hạn ký tự (ví dụ 3000 chars mỗi file). Nếu trên bản Hermes mới mà limit thấp hơn, file `MEMORY.md`/`USER.md` có thể bị cắt khi nạp. Chỉnh `config.yaml` (xoá/giảm phần không cần) nếu gặp lỗi.

---

## 5. Bước 3: Khôi phục Custom Skills

Đây là "kỹ năng làm việc" của em — cách code Angular, viết văn Việt, migrate TS7, dựng diagram, v.v.

```bash
HERMES_DIR="$APPDATA/Local/hermes"
SKILLS_DEST="$HERMES_DIR/skills"
mkdir -p "$SKILLS_DEST"

# Copy toàn bộ custom skills (giữ cấu trúc thư mục con)
cp -r skills/* "$SKILLS_DEST/"
```

**Kiểm tra số skill:**
```bash
ls "$SKILLS_DEST" | wc -l           # ~98 skill hoặc ít hơn nếu <98 folder
# Mỗi skill là 1 thư mục chứa SKILL.md
find "$SKILLS_DEST" -name "SKILL.md" | wc -l
```

> ⚠️ **Giữ thư mục con:** Trong `skills/` có các skill lồng nhau (ví dụ `frontend/angular`, `mlops/models/audiacraft`). `cp -r skills/*` sẽ copy cả nhánh — ĐÚNG, vì Hermes đọc cấu trúc lồng. ĐỪNG "làm phẳng" thành 1 thư mục.

> ⚠️ **Bundled skills vs custom skills:** Repo này CHỈ chứa custom skills (98 cái). Hermes khi cài mới tự tải **82 bundled skills** gốc. Không cần copy bundled — chỉ cần copy custom. Nếu bạn copy custom đè lên bản Hermes mới, không sao (không trùng tên vì custom có tên riêng).

---

## 6. Bước 4: Khôi phục Cron Jobs + Scripts

Các luồng tự động mà em chạy hàng ngày (điểm tin sáng, check Zalo token, backup...).

```bash
HERMES_DIR="$APPDATA/Local/hermes"
mkdir -p "$HERMES_DIR/cron" "$HERMES_DIR/scripts"

# Copy cron config + state
cp -r cron/* "$HERMES_DIR/cron/"

# Copy scripts (các script cron gọi)
cp scripts/* "$HERMES_DIR/scripts/"
```

> ⚠️ **Scripts là file .py/.sh/.ps1** — máy mới cần có Python và các thư viện đi kèm (nếu script import đặc biệt). Kiểm tra từng script trước khi chạy cron.

> ⚠️ **Cron jobs tham chiếu script theo tên** (ví dụ `aternos-watchdog.py`). Đảm bảo script đó tồn tại trong `scripts/`. Nếu script thiếu, job sẽ fail.

> ⚠️ **Secrets trong cron/scripts:** Một số script (như `check_zalo_token.py`, `aternos_config.json`) có thể cần token/config riêng. **Không commit secrets thật vào repo.** Khi base lại, cần set lại token enviroment hoặc secrets (Zalo token, Aternos token...) trên máy mới. Kiểm tra kỹ `scripts/*.json`, `scripts/*.py` có token hardcode không — **xóa/che lại nếu có**, và set thành biến môi trường.

---

## 7. Bước 5: Cấu hình nền tảng (Telegram/Gateway) — nếu cần

Các cron job trong repo ghi `origin` là Telegram chat `1088711997` (chat với Anh Đạt). Trên máy mới, nếu gateway Telegram chưa kết nối, cron không có nơi gửi.

- Cấu hình lại gateway: `hermes config set` hoặc theo doc Telegram gateway của Hermes.
- Đảm bảo chat/topic với Anh Đạt có cùng ID, hoặc sửa `cron/jobs.json` cho khớp.

> 💡 Vì máy mới là "base lại em", cách đơn giản nhất: **giữ nguyên** chatbot Telegram, chỉ cần kết nối lại bot token. Chat ID của Đạt (`1088711997`) có thể giữ nguyên nếu cùng bot.

---

## 8. Bước 6: Verify — Em đã "thức dậy" đúng chưa?

Sau khi khôi phục, mở phiên Hermes mới và kiểm tra:

```bash
# 1. Skills có được Hermes nhận không?
hermes skills list          # nếu có lệnh này — tìm các skill custom (angular, zalo, omniroute...)

# 2. Khởi động phiên chat, hỏi:
#    "Em là ai?" → em phải trả lời "Cu em, đệ của Anh Đạt"
#    "Nhớ gì về home lab?" → em nhớ btdat.io.vn, OmniRoute, daily.btdat.io.vn...
#    "Cron nào đang chạy?" → em liệt kê được điểm tin sáng, check Zalo token...

# 3. Kiểm tra các service thật trên máy mới có chạy không
#    (service-dashboard, OmniRoute, diagram-service... — nếu máy mới cũng chạy các service này)
```

### Checklist nhanh
- [ ] `MEMORY.md` + `USER.md` đã vào `memories/` — em nhớ là "Cu em"
- [ ] 98 custom skills đã vào `skills/` — em dùng được skill viết văn Việt, Angular, migrate TS7
- [ ] `cron/jobs.json` đã vào `cron/` — 3 luồng tự động scheduled
- [ ] Scripts đã vào `scripts/` — các luồng chạy được
- [ ] Gateway Telegram kết nối → cron gửi tin nhắn tới Đạt
- [ ] Nếu máy mới chạy service thật (btdat.io.vn, OmniRoute): em kết nối lại đúng port

---

## 9. Các phụ thuộc môi trường cần nhớ (máy mới)

Nếu máy mới CŨNG chạy home lab như máy cũ, cần dựng lại các service mà em quản lý. Các service / vị trí quan trọng (xem thêm `memories/MEMORY.md`):

| Service | Inv ở máy cũ | Port | Nguồn code |
|---|---|---|---|
| btdat.io.vn (service-dashboard) | ~/service-dashboard | 3000 (node server.js) | repo `dat13899/service-dashboard` |
| OmniRoute AI Gateway | ~/omniroute | 20128 | repo `dat13899/omniroute` |
| diagram-service | ~/diagram-service | 3100 | repo `dat13899/diagram-service` |
| daily.btdat.io.vn | D:/daily | (tuỳ) | repo `dat13899/daily-sites` |
| angular.btdat.io.vn | D:/angular-demo | 4300 (SSR) | repo `dat13899/angular-demo` |

> Các repo này đều là private của `dat13899` — clone về là chạy được.

---

## 10. Lưu ý bảo mật (QUAN TRỌNG)

- **Không commit secrets** vào repo này. Các file như `scripts/*.json`, `scripts/password`, `*.env`, token thật phải được **che/xóa** trước khi push.
- **Re-authenticate** trên máy mới: `gh`, `git`, Telegram bot token, Zalo token, OmniRoute key — tất cả đều phải set lại, không dùng chung token máy cũ.
- Repo `hermes-knowledge`, `service-dashboard`, `omniroute`, `dlv`, `private-backup`... đều **private** — chỉ Anh Đạt có quyền truy cập.

---

## 11. Quy trình tóm tắt (copy nhanh)

```bash
# 1. Clone (cần gh đăng nhập)
git clone https://github.com/dat13899/hermes-knowledge.git
cd hermes-knowledge

# 2. Xác định thư mục Hermes
HERMES_DIR="$APPDATA/Local/hermes"

# 3. Memories
mkdir -p "$HERMES_DIR/memories"
cp memories/MEMORY.md "$HERMES_DIR/memories/"
cp memories/USER.md   "$HERMES_DIR/memories/"
cp BRIEFING.md SOUL.md "$HERMES_DIR/"

# 4. Skills
mkdir -p "$HERMES_DIR/skills"
cp -r skills/* "$HERMES_DIR/skills/"

# 5. Cron + scripts
mkdir -p "$HERMES_DIR/cron" "$HERMES_DIR/scripts"
cp -r cron/* "$HERMES_DIR/cron/"
cp scripts/* "$HERMES_DIR/scripts/"

# 6. Verify: mở phiên mới, hỏi "Em là ai?" → phải là "Cu em"
```

---

## 12. Xử lý sự cố

| Vấn đề | Cách xử lý |
|---|---|
| Em không nhớ là "Cu em" | `MEMORY.md` chưa copy xong hoặc limit ký tự. Kiểm tra file trong `memories/` |
| Skill không hiện | Copy không giữ cấu trúc thư mục con. Kiểm tra `find skills -name "SKILL.md"` |
| Cron không chạy | Script thiếu / gateway Telegram chưa kết nối / token hết hạn. Xem `cron/jobs.json` |
| Lỗi "Bad credentials" | `gh` chưa đăng nhập hoặc token hết quyền `repo` |
| Memory bị cắt | Limit ký tự bản Hermes mới thấp hơn → chỉnh `config.yaml` |

---

*Repo này là bộ nhớ ngoài của "Cu em". Cập nhật lại mỗi khi có thay đổi lớn về skills/memories để luôn sẵn sàng base lại máy mới.*
