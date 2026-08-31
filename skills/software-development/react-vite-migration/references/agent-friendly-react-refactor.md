# Agent-Friendly React Refactoring Plan (July 2026)

Plan tái cấu trúc toàn bộ React app từ inline-styles monolithic → component-driven, mobile-first, agent-friendly architecture.

## Root Cause Analysis

Sau khi đọc toàn bộ 49 file source code của `btdat.io.vn`, các vấn đề kiến trúc gốc:

| # | Vấn đề | Tác động đến agent |
|---|---|---|
| 1 | **Mỗi page tự import Navbar + BlobBackground** — không có `<Layout>` wrapper | Sửa layout = sửa 6 file, dễ bỏ sót |
| 2 | **CSS nằm trong `public/assets/global.css`** — không qua Vite build pipeline | CSS lỗi không báo build, agent không trace được |
| 3 | **100% inline styles** — mỗi page define `const s = {...}` style object khổng lồ | Code dài gấp 3 lần, agent mất context đọc 200 dòng style mới thấy logic |
| 4 | **Không mobile-first** — base style = desktop, override cho mobile qua `max-width` | Ngược chuẩn hiện đại, mobile user tải code desktop trước |
| 5 | **File quá lớn** — DashboardPage 661 dòng, DocumentsPage 681 dòng, HomePage 478 dòng | Agent không đọc hết 1 turn, bug ẩn trong inline style |
| 6 | **WidgetPage hardcoded** — thêm widget phải sửa 3 file (data.js + WidgetPage.jsx + tạo component) | Agent dễ bỏ sót 1 trong 3 |
| 7 | **Không error boundary** — 1 component crash = white screen toàn site | Không có fallback UI |
| 8 | **Không page transition** — navigate cắt ngang | UX thô |

## 5 Nguyên Tắc Thiết Kế Mới

```
1. MOBILE-FIRST: base style = mobile, @media (min-width:) = desktop
2. COMPONENT-DRIVEN: mỗi UI element có 1 file riêng, tên rõ ràng
3. SEPARATION OF CONCERNS: layout ≠ page ≠ component ≠ hook ≠ util
4. CSS QUA VITE: style qua CSS modules hoặc utility class, không inline
5. MAX 150 DÒNG/FILE: file >150 dòng bắt buộc split
6. PREDICTABLE STRUCTURE: folder structure giống nhau cho mọi tính năng
```

## Cấu Trúc Thư Mục Mới

```
frontend/src/
├── layouts/
│   ├── AppLayout.jsx          ← wrapper duy nhất cho mọi page
│   └── PageTransition.jsx     ← animated route transitions
├── styles/
│   ├── tokens.css             ← all CSS variables, design tokens
│   ├── reset.css              ← modern CSS reset
│   ├── utilities.css          ← .flex, .grid, .gap-*, .p-*, .text-*
│   ├── breakpoints.css        ← mobile-first responsive grid
│   └── components.css         ← .btn, .card, .badge, .input, .glass
├── components/
│   ├── ui/                    ← design system
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Badge.jsx
│   │   ├── Input.jsx
│   │   ├── GlassPanel.jsx
│   │   ├── Skeleton.jsx
│   │   ├── Spinner.jsx
│   │   └── EmptyState.jsx
│   ├── layout/
│   │   ├── Navbar.jsx
│   │   ├── Footer.jsx
│   │   └── BottomTab.jsx      ← mobile bottom navigation
│   └── shared/
│       ├── BlobBackground.jsx
│       ├── ConfirmModal.jsx
│       ├── ErrorBoundary.jsx
│       └── Toast.jsx
├── hooks/
│   ├── useTheme.js
│   ├── useToast.jsx
│   ├── useDocuments.js
│   ├── useMediaQuery.js       ← responsive hook
│   └── useScrollspy.js
└── pages/
    ├── home/                  ← mỗi page là 1 folder
    │   ├── HomePage.jsx       ← ≤80 dòng: layout + hooks
    │   ├── HomeHero.jsx
    │   ├── HomeServices.jsx
    │   ├── HomeStack.jsx
    │   ├── HomeContact.jsx
    │   └── index.js           ← export { default } from './HomePage'
    ├── dashboard/
    │   ├── DashboardPage.jsx
    │   ├── ServiceList.jsx
    │   ├── ServiceCard.jsx
    │   ├── ResourcePanel.jsx
    │   ├── PortPanel.jsx
    │   ├── AddServiceModal.jsx
    │   └── index.js
    ├── documents/
    │   ├── DocumentsPage.jsx
    │   ├── DocSidebar.jsx
    │   ├── DocReader.jsx
    │   ├── DocEditor.jsx
    │   ├── NewDocModal.jsx
    │   └── index.js
    └── widgets/
        ├── WidgetPage.jsx     ← ≤60 dòng
        ├── WidgetGrid.jsx     ← auto-import via import.meta.glob
        ├── WidgetCard.jsx
        ├── data.js
        ├── components/        ← auto-discovered
        └── index.js
```

## Auto-Discovery Widget Pattern

Thay vì hardcode 31 dòng `lazy(() => import(...))`:

```js
// WidgetGrid.jsx - tự động import từ thư mục components/
const widgets = import.meta.glob('./components/*.jsx');
// widget key = tên file (bỏ .jsx, lowercase)
// Mỗi file export default component
```

## Mobile Breakpoint System

| Name | Min-width | Target |
|---|---|---|
| `mobile` | 0px (base) | Phone portrait |
| `tablet` | 640px | Phone landscape / small tablet |
| `desktop` | 1024px | Laptop |
| `wide` | 1280px | Desktop monitor |

```css
/* Mobile-first grid */
.grid { display: grid; gap: 1rem; grid-template-columns: 1fr; }
@media (min-width: 640px)  { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 1280px) { .grid { grid-template-columns: repeat(4, 1fr); } }
```

## Agent-Friendly Rules

1. **Index barrel files** — `pages/home/index.js` để agent import `'../pages/home'` thay vì `'../pages/home/HomePage'`
2. **JSDoc mỗi component** — `/** @param {{ title: string, onDelete: () => void }} */`
3. **Error boundary mọi page** — agent biết chính xác component nào crash
4. **Debug mode** — `?debug=1` trên URL hiện component name ở góc mỗi section
5. **Tên biến rõ ràng** — `isLoading` không phải `l`, `handleDelete` không phải `hd`
6. **README cho folder** — `pages/README.md` mô tả cấu trúc, agent đọc 1 file hiểu cả system
