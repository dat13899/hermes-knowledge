# GitHub Trending & Repo Research — Recipe

Hỏi "repo AI agent nào đang hot" / "cái gì đang trend trên GitHub" / profile 1 repo cụ thể.

## 1. Scrape trending page

```bash
mkdir -p ~/tmp && cd ~/tmp
curl -sSL -A "Mozilla/5.0" "https://github.com/trending?since=weekly" > trending-weekly.html
# since=weekly | daily | monthly
wc -c trending-weekly.html   # ~650KB khi OK
```

**Gotcha (Windows/MSYS):** `/tmp` KHÔNG tồn tại trong git-bash → `curl -o /tmp/x` lỗi
`curl: (23) client returned ERROR on write` (CURLE_WRITE_ERROR). Luôn dùng `~/tmp`.
Nếu lỗi 23 vẫn xảy ra với `-o`, chuyển sang redirect `> file` (đã fix trong session 10/08/2026).

## 2. Lấy danh sách repo slugs — grep, đừng regex HTML

Cấu trúc HTML `<article class="Box-row">` của GitHub trending **hay đổi** — regex parse
từng khớp 0 kết quả (đã dính: pattern `<article class="Box-row">...` → `TOTAL: 0`).
Grep link là đủ bền:

```bash
grep -oE 'href="/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"' trending-weekly.html \
  | grep -vE '/(trending|topics|collections|sponsors|login|signup|features|enterprise|pricing|about|marketplace|settings|notifications|new|orgs|apps|search|explore|pulls|issues|codespaces|security|site|customer-stories|readme|assets|avatars|github|events|contact|team|press)' \
  | sort -u | sed 's|href="/||;s|"||'
```

## 3. Enrich metadata qua GitHub API (không auth)

~60 requests/h cho unauthenticated — đủ cho 18-25 repo, đừng gọi lại repo trùng.

```bash
for repo in "owner/repo1" "owner/repo2"; do
  curl -s "https://api.github.com/repos/$repo" | python -c "
import json,sys
d=json.load(sys.stdin)
print(f\"{d.get('full_name','?')} | ⭐{d.get('stargazers_count',0)} | {d.get('language','?')} | {(d.get('description') or '')[:100]}\")
"
done
```

Field hữu ích: `stargazers_count`, `forks_count`, `language`, `description`,
`topics` (list), `created_at`, `updated_at` (cập nhật gần = đang được maintain),
`homepage`.

## 4. Discovery repo mới / star tăng nhanh (GitHub Search API)

```bash
curl -s "https://api.github.com/search/repositories?q=ai+agent+created:%3E2026-01-01&sort=stars&order=desc&per_page=15"
```

- `created:>YYYY-MM-DD` lọc repo mới; `pushed:>YYYY-MM-DD` lọc repo đang active
- `sort=stars` cho repo nổi bật; `sort=updated` cho repo đang được phát triển
- `per_page` max 100; unauthenticated search ~10 req/min
- Response: `items[]` với full_name, stargazers_count, language, created_at, description

## 5. Trình bày

- Nhóm theo chủ đề (framework / skills / infrastructure / browser-automation / media...)
- Mỗi repo: ⭐ + ngôn ngữ + 1 dòng vì sao đáng chú ý, **map sang stack user đang dùng**
  (vd user xài DeepSeek → nhắc DeepSeek-native agent; xài Hermes skills → nhắc google/skills, addyosmani/agent-skills)
- Kết: đề nghị đào sâu 1-2 repo (clone/đọc README/chạy thử) — KHÔNG tự ý clone hàng loạt
- Nếu repo quá nhiều, ưu tiên giới thiệu 5-8 cái đáng giá nhất + nêu rõ lý do

## Python trong heredoc trên Windows

```bash
cd ~/tmp && python - << 'EOF'
... 
EOF
```

- Dùng `python`, KHÔNG `python3` — host này chỉ có `python` (python3 alias không tồn tại → "Python was not found; run without arguments to install from the Microsoft Store")
- Heredoc được auto-approve (đã thấy "flagged (script execution via heredoc) and auto-approved")
