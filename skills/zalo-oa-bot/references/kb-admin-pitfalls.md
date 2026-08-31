# KB (SQLite) + Admin — pitfalls gặp khi vận hành

## Bug: Sửa document trên admin báo lỗi không lưu được

- Triệu chứng: admin UI bấm Sửa → Lưu → toast lỗi / API PUT trả
  `TypeError: Provided value cannot be bound to SQLite parameter 5`.
- Nguyên nhân: form sửa không gửi field `enabled` → `updateDocument` merge `{...cur, ...d}` sinh `enabled: undefined` → `node:sqlite` không bind được undefined.
- Fix trong `src/kb.ts` `updateDocument`: chỉ merge các field được cung cấp:
```ts
const clean: Partial<{...}> = {};
for (const k of ["title","content","keywords","category","enabled"] as const) {
  if (d[k] !== undefined) clean[k] = d[k] as never;
}
const merged = { ...cur, ...clean };
```
- Lưu ý: node:sqlite trả `Record<string, SQLOutputValue>` → cast `as unknown as KbDocument[]` (TS2352 nếu cast thẳng).

## Import dữ liệu tiếng Việt vào KB

- **KHÔNG dùng `curl -X POST -d '{"title":"tiếng Việt"}'` từ git-bash** — mojibake (`?` thay dấu, `L�m th? n�o`). Luôn dùng tsx script `addDocument({...})` (UTF-8 chuẩn).
- Nếu lỡ ghi mojibake: xóa doc bằng DELETE API, tạo lại bằng script.

## Chặn cứng phạm vi trả lời (KB-only)

- Bot chỉ trả lời khi `searchDocuments` có kết quả; không khớp → trả mẫu cố định KHÔNG gọi AI (chống bịa như "Messi là ai").
- Search cần: stop-words tiếng Việt ("là","ai","có","không","gì","bao"...), từ ≥3 ký tự, ngưỡng score ≥5 (title +3, keywords +5, content +1).
- Nhớ ngữ cảnh hội thoại: lưu `userTopicStore` (doc id đang nói) + ghép history vào query search; câu chấp nối mơ hồ ("vậy phí thế nào?") dùng lại topic cũ.
- Quy tắc đăng ký/mua: prompt yêu cầu luôn hướng dẫn qua website + app MBBank khi câu hỏi về mua/đăng ký.
