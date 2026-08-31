# KB-scoped AI + UI pitfalls (2026-08-20, ~/zalo-oa-bot)

## Bot chỉ trả lời trong phạm vi dữ liệu admin — CHẶN CỨNG ở code

User yêu cầu "giới hạn phạm vi trong /admin". Bài học: **đừng chỉ dựa prompt AI "từ chối"** — model vẫn tự bịa. Test thật: hỏi "Messi là ai?" vẫn được trả lời vì search match nhầm từ "bảo hiểm" xuất hiện trong nhiều Q&A.

Giải pháp đúng (2 lớp):

1. **Search KB nghiêm ngặt** (`src/kb.ts` searchDocuments):
   - Tách query thành từ: **≥3 ký tự**, loại **từ dừng tiếng Việt**: `["là","ai","có","không","gì","nào","bao","như","và","của","để","cho","theo","với","hay","hoặc","tôi","em","mình","bạn","anh","chị","được","thì","mà","đã","sẽ","đang","nếu","từ","ra","vào","lên","xuống","ở","tại","về"]`
   - Score: keywords match +5, title +3, content +1; title khớp cả query +10, keywords +8
   - **Ngưỡng tối thiểu score ≥5** — nếu không, "Messi là ai" match 3 docs chỉ nhờ "là"/"ai"
2. **Không gọi AI khi không khớp** (`src/ai.ts` askAi):
   ```ts
   const kbContext = buildKbContext(userText);
   if (!kbContext) {
     return "Xin lỗi, em chỉ hỗ trợ các câu hỏi về ... nhé! 😊"; // template cố định, KHÔNG gọi LLM
   }
   ```

Kết quả chuẩn: "Messi là ai" → từ chối; "phí bao nhiêu" → trả lời từ KB; "mua bảo hiểm ở đâu" (chủ đề gần nhưng không có data) → từ chối nhờ ngưỡng score.

## Import Q&A hàng loạt — regex chặn mục con

- Đúng: `text.split(/\n(?=\d{1,2}\s*[.、]\s*[^\n]*\?)/)` — chỉ tách block khi dòng **kết thúc bằng `?`** (câu hỏi thật).
- Sai: tách theo mọi số đầu dòng → câu trả lời dài (hồ sơ bồi thường có mục 1.,2.,3...) bị tách nhầm → 18 documents thay vì 10.
- Fix khi seed nhầm: `kb.db` bị server giữ lock → kill server, xóa file, restart (hoặc DELETE từng id qua API `/api/kb/:id`).

## node:sqlite (Node 24 built-in)

- `import { DatabaseSync } from "node:sqlite"` — không cần cài sqlite3/better-sqlite3.
- TS cast: `.all() as unknown as KbDocument[]` — `Record<string, SQLOutputValue>` không overlap interface.
- tsx watch + sqlite: sửa file liên tục → 2 instance đụng DB → `ERR_SQLITE_ERROR: database is locked`. **Kill sạch process cũ trước khi start lại** (đừng để tsx watch tự restart chồng).

## Inline `<script>` trong Express template literal — script bị cắt rỗng

Triệu chứng: trang log treo "chờ kết nối", `typeof load === 'undefined'`, `script.textContent.length === 0` dù HTML nhìn đầy đủ; fetch `/api/log` vẫn OK.

Nguyên nhân: regex `s.replace(/</g,'&lt;')` trong inline JS → chuỗi `</` khiến HTML parser tưởng **đóng thẻ `<script>` sớm** → phần còn lại bị coi là HTML text.

Fix: **tách JS ra file tĩnh** — `public/log.js` + `app.use(express.static('.../public'))` + `<script src="/log.js?v=N">` (thêm `?v=` để bust cache Cloudflare). Trong JS riêng, escape bằng `\u003C`/`\u003E` nếu cần. Không bao giờ nhúng inline script lớn chứa `</` vào template literal.

## UI log/admin theo chuẩn (đo trước, sửa sau)

- Đo bằng CDP: `document.querySelectorAll('button,a').forEach(el => el.getBoundingClientRect())` — tìm nút <40px, font <11px.
- Fix đã áp dụng: nút cao **40px** (không 28px), font stats **12px** (không 10.5px), avatar **44px**, `white-space: nowrap` cho nút có icon, gom nút hành động **cạnh nhau bên phải** (không rải 2 mép — gây lệch mắt), label text bên trái cân đối.
- `innerText` hiện `\n` giữa icon và chữ dù `nowrap` — đó là artifact của innerText, không phải lỗi UI thật.
- Ghi log vào **file** (stdout background bị buffer) → đọc qua API `/api/log`; trang log user → danh sách người dùng → bấm vào xem thread chat (bubble user phải / bot trái), nút làm mới thủ công thay vì auto-refresh 3s (user yêu cầu).
