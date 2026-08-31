# React Component Prop Mismatch — Silent Crash Pattern

## When to suspect this

- ErrorBoundary chung chung ("Có lỗi xảy ra") — không stack trace rõ ràng
- API vẫn 200, data vẫn trả về OK
- `localStorage`, `useMemo`, `useCallback` — tất cả nghi ngờ khác đều OK
- Fix từng bug nhỏ (như `docsCtrl.allTags`) vẫn không hết lỗi
- Component con đã được rewrite gần đây nhưng cha chưa cập nhật

## Root cause

Component con được rewrite với API props mới, nhưng component cha vẫn gọi nó với props kiểu cũ → props undefined → TypeError hoặc callback không gọi được → ErrorBoundary.

## Cách debug

### 1. So sánh signature với call site

Đọc signature component con:
```jsx
function DocSidebar({ docs, currentDoc, onSelectDoc, searchQuery, setSearchQuery, ... })
```

Đọc JSX gọi nó ở cha:
```jsx
<DocSidebar
  docs={docsCtrl.docs}
  activeId={docsCtrl.currentDoc?.id}  // ❌ tên cũ
  onSelect={handleSelect}              // ❌ tên cũ
  onDelete={...}                       // ❌ không tồn tại
/>
```

Map từng prop cha → con:
- `activeId` → không có trong signature → bỏ qua, nhưng `currentDoc` = undefined
- `onSelect` → không bằng `onSelectDoc` → `onSelectDoc` = undefined → click crash
- `onDelete` → không tồn tại trong signature → bỏ qua

### 2. Build bundle check

```bash
npm run build
python -c "
js=open('dist/assets/DocumentsPage-XXXXXX.js').read()
print('onSelectDoc' in js, 'onSelect' in js)
print('currentDoc' in js, 'activeId' in js)
"
```

Nếu chỉ thấy tên cũ (`onSelect`, `activeId`) mà không thấy tên mới (`onSelectDoc`, `currentDoc`) → props truyền sai.

### 3. Browser console (nếu có CDP)

Errors điển hình:
- `Cannot read properties of undefined (reading 'trim')` → `searchQuery` = undefined
- `X is not a function` → callback prop sai tên
- `Cannot read properties of undefined (reading 'length')` → array/string prop undefined

## Cách fix đúng

1. **Không chỉ thêm default values** — props sai tên thì default values cũng không giúp được. `onSelectDoc = () => {}` chỉ tránh crash, component vẫn không hoạt động vì không có handler thật.

2. **Viết lại toàn bộ section gọi component con** với đúng API props mới.

3. **Kéo state lên cha nếu cần** — nếu component con mới dùng internal state mà cần chia sẻ với cha (vd: `searchQuery`, `sortBy`, `draftOnly`).

### Ví dụ cụ thể từ service-dashboard DocumentsPage

**Cũ (cha truyền props sai):**
```jsx
<DocSidebar
  docs={docsCtrl.docs}
  activeId={docsCtrl.currentDoc?.id}      // ❌ → currentDoc
  onSelect={handleSelect}                  // ❌ → onSelectDoc
  onDelete={(doc) => setDeleteTarget(doc)} // ❌ không dùng
  onUpload={docsCtrl.uploadDoc}            // ❌ → onUploadDoc
  // thiếu: searchQuery, setSearchQuery, sortBy, setSortBy, 
  //        draftOnly, setDraftOnly, selectedIds, setSelectedIds,
  //        onCacheClear, visible, isMobile
/>
```

**Mới (đúng API):**
```jsx
<DocSidebar
  docs={docsCtrl.docs}
  loading={docsCtrl.loading}
  currentDoc={docsCtrl.currentDoc}
  selectedTags={selectedTags}
  setSelectedTags={setSelectedTags}
  searchQuery={searchQuery}
  setSearchQuery={setSearchQuery}
  onSelectDoc={handleSelect}
  onCreateDoc={openNewModal}
  onUploadDoc={docsCtrl.uploadDoc}
  visible={showSidebar}
  isMobile={isMobile}
  sortBy={sortBy}
  setSortBy={setSortBy}
  draftOnly={draftOnly}
  setDraftOnly={setDraftOnly}
  selectedIds={selectedIds}
  setSelectedIds={setSelectedIds}
  onCacheClear={handleCacheClear}
/>
```

## Pitfall: "Đã fix rồi mà vẫn lỗi"

Sau khi fix 1 bug (vd `docsCtrl.allTags` undefined) mà vẫn crash → **có bug thứ 2**. Pattern phổ biến trong React app có nhiều component phụ thuộc lẫn nhau:

1. Bug #1 đã được xác nhận fix (chunk có `useMemo`, `allTags` sau build)
2. Vẫn crash → mở rộng phạm vi: kiểm tra **props**, imports, API calls
3. Sau khi fix cả 2: build mới (hash mới) + restart server + verify cả local và CDN

## Deployment checklist sau fix

- [ ] `npm run build` — hash mới khác hash cũ
- [ ] Kill server cũ, start server mới
- [ ] `curl localhost:3000/documents` → 200
- [ ] `curl https://btdat.io.vn/documents` → 200
- [ ] Hash local và CDN khớp
- [ ] `git add -A && git commit -m "..." && git push`
