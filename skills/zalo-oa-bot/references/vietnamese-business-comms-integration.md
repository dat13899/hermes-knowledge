# Vietnamese Business Comms — tích hợp vào Zalo OA Bot (2026-08-25)

Nguồn: `trussary/vietnamese-language-skill` → skill `vietnamese-business-comms` (register `consult` cho chat tư vấn BHViet).

## Vì sao cần
LLM mặc định viết tiếng Việt kiểu dịch máy: `Chào bạn` trong tư vấn B2B, CTA `Học thêm`, `2,500,000 VND`, superlative `tốt nhất số 1` (vi phạm Luật QC Đ8 K11). Skill này bắt đúng 3 nhóm lỗi: xưng hô, calque/CTA, luật + format.

## Cài đặt skill (npx skills — không phải hermes skills install)
```bash
npx skills add trussary/vietnamese-language-skill -l          # xem 5 skills trước
npx skills add trussary/vietnamese-language-skill -y          # project (~/zalo-oa-bot/.agents/skills)
npx skills add trussary/vietnamese-language-skill -g -y       # global → symlink AppData/Local/hermes/skills
npx skills list          # project
npx skills list -g       # global
hermes skills list       # verify 5 skills enabled (vietnamese-business-comms ...)
```
Repo MIT, 732KB, validator `validate_copy.py` (stdlib, Python 3.9+, không pip). Score skills.sh: 4 Safe + 1 Med Risk, 0 Socket alert.

> Lưu ý: `npx skills add ... -g` báo `Failed to install 5 → PromptScript does not support global` là expected — vẫn symlink đủ sang `~/.agents/skills` và `AppData/Local/hermes/skills` (check `ls -l`).

## Tích hợp đã làm trong ~/zalo-oa-bot (2026-08-25)

### 1. Prompt-level (register consult)
`src/vietnameseValidator.ts` export `VI_BUSINESS_PROMPT_SUFFIX` — 8 rule cốt lõi (consult: khách `anh/chị`, mình `em`, cấm `bạn/mình`, CTA `Đăng ký tư vấn/Nhận báo giá`, cấm superlative, VND `2.500.000 ₫`, date `dd/MM/yyyy`, phone bỏ 0 sau +84). `src/ai.ts` append vào `KB_ONLY_SYSTEM_PROMPT`:
```ts
import { VI_BUSINESS_PROMPT_SUFFIX } from "./vietnameseValidator.js";
const KB_ONLY_SYSTEM_PROMPT = `... ${VI_BUSINESS_PROMPT_SUFFIX}`;
```

### 2. Runtime validator (JS thuần, không spawn Python trong hot path)
`src/vietnameseValidator.ts`:
- `lintVietnamese(text)` → LAW001 (superlative), CAL001 (trích dẫn→báo giá, học thêm→Xem ngay...), NUM001 (dấu phẩy VND), PHONE001 (+84 0912), SALES001 (bạn trong consult)
- `fixVietnamese(text)` → fix calque + VND `2,500,000 → 2.500.000` + phone + `Chào bạn → Chào anh/chị` (đầu câu)

`src/ai.ts` sau `cleanMarkdown()`:
```ts
let clean = cleanMarkdown(content);
const findings = lintVietnamese(clean);
if (findings.length) {
  console.warn("[VI] findings:", findings.map(f=>`${f.rule} ${f.message}`).join(" | "));
  const fixed = fixVietnamese(clean);
  if (fixed !== clean) { console.log("[VI] auto-fixed"); clean = fixed; }
}
```
Không block tin — LAW001 chỉ warn (đúng tinh thần skill: superlative warn, cần `<!-- proof: ... -->` mới suppress).

### 3. Full validator Python (khi cần audit KB)
```bash
python .agents/skills/vietnamese-business-comms/scripts/validate_copy.py src/ai.ts --register consult --json
python .agents/skills/vietnamese-business-comms/scripts/validate_copy.py /tmp/kb.md --register consult
python .agents/skills/vietnamese-business-comms/scripts/validate_copy.py --list-rules
```
Gating: `--register consult|zns|b2b|saas` bật PRO002, `--doctype zns|cold-outreach|bao-gia|dunning|bulk-message` bật rule cấu trúc (ZNS 400 ký tự, MARKET, SPAM...).

## Verify
```bash
npx tsc -p tsconfig.json --noEmit   # PASS
npx tsx -e "import {lintVietnamese,fixVietnamese} from './src/vietnameseValidator.ts'; console.log(lintVietnamese('Chào bạn ... tốt nhất số 1 2,500,000 VND Học thêm'))"
# → LAW001 + CAL001 + NUM001 + SALES001, FIX → "Chào anh/chị ... 2.500.000 VND Xem ngay"
```
`handleEvent` đã async (trả 200 trước), thêm validator không ảnh hưởng 2s timeout Zalo. Log `[VI]` xuất hiện trong `webhook.log` + console.

## Pitfalls đã gặp
- `npx skills add -l` clone repo và hiện 5 skills — phải chạy thêm `-y` mới cài thật.
- Global install báo fail PromptScript nhưng vẫn symlink đủ — đừng retry mù.
- Skill folder là symlink `AppData/Local/hermes/skills/vietnamese-* → ~/.agents/skills/...` — xóa 1 nơi mất cả 2.
