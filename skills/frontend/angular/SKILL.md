---
name: angular
description: "Use when building/reviewing Angular v22+ code."
version: 1.0.0
author: "Cu em"
license: MIT
metadata:
  tags: [angular, ssr, hydration, signals, typescript, frontend]
  related_skills: [frontend-ui-workflow, web-ui-standards, hermes-agent]
---

## When to Use

Trigger khi anh Đạt nhờ code, review, migrate, hay setup bất kỳ dự án **Angular** nào (SSR, hydration, signals, forms, components). Cũng dùng khi cần so sánh Angular với stack React hiện tại.

Nguồn chính thức: angular.dev/guide/ssr, angular.dev/ai (v22, updated 2026). Mọi rule dưới đây lấy nguyên văn từ bộ "Custom Prompts / System Instructions" mà Angular team phát hành.

## ⚠️ Thay đổi mindset quan trọng (dễ code sai nếu theo thói quen cũ)

- **LUÔN dùng standalone components** — KHÔNG dùng NgModules.
- **KHÔNG set `standalone: true`** trong decorator. Mặc định từ v20+, set lại là thừa.
- **KHÔNG set `changeDetection: ChangeDetectionStrategy.OnPush`** tường minh. **OnPush là mặc định từ v22+.**
- **KHÔNG dùng `@HostBinding` / `@HostListener`** — chuyển vào `host` object trong decorator `@Component`/`@Directive`.
- **KHÔNG dùng `ngClass` / `ngStyle`** — dùng `class` / `style` bindings.
- **KHÔNG dùng `*ngIf`, `*ngFor`, `*ngSwitch`** — dùng native control flow `@if`, `@for`, `@switch`.
- **KHÔNG dùng `@Input()`/`@Output()` decorators** — dùng `input()` / `output()` functions.
- **KHÔNG gọi `mutate()` trên signal** — dùng `update` / `set`.
- **KHÔNG dùng constructor injection** — dùng `inject()` function.
- **KHÔNG tạo service singleton bằng `@Injectable({providedIn:'root'})`** cho service mới — dùng `@Service` decorator (v22+).

## TypeScript Best Practices

- Strict type checking.
- Prefer type inference khi kiểu rõ ràng.
- Tránh `any`; dùng `unknown` khi không chắc chắn.

## Pitfalls khi deploy SSR (Angular 22 + Node + Cloudflare Tunnel) — QUAN TRỌNG

Đã đưa angular.btdat.io.vn lên live (port 4300, dist server.mjs). Các pitfall thực tế đã gặp:

1. **SSRF host check — `NG_ALLOWED_HOSTS`**: server.ts (AngularNodeAppEngine) từ chối host lạ. Khi chạy production, đặt env `NG_ALLOWED_HOSTS="angular.btdat.io.vn,localhost,127.0.0.1"` hoặc `trustProxyHeaders: true` trong `new AngularNodeAppEngine({ trustProxyHeaders: true })`. Nếu quên → HTTP 400 rỗng.

2. **Proxy headers qua Cloudflare**: tunnel gửi `x-forwarded-for`/`x-forwarded-proto`. Bật `trustProxyHeaders: true` để không warning + render đúng https.

3. **curl báo "size 0" nhưng site CHẠY**: khi `-o /tmp/...` (MSYS path) curl ghi lỗi exit 23. Luôn dùng path Windows thật `D:/...` cho `-o`. `--resolve` + IPv4 IP (Cloudflare) để bypass DNS local chậm.

4. **DNS local (mạng công ty ad.vinnet.vn) cache NXDOMAIN lâu** → máy không resolve subdomain mới dù Cloudflare đã có. Nhanh nhất: thêm dòng vào `C:\Windows\System32\drivers\etc\hosts` (`<cloudflare-ip> angular.btdat.io.vn`) rồi `ipconfig /flushdns`. Cloudflare public DNS resolve OK (`--resolve` để test).

5. **Chạy bền detached (không phụ thuộc Hermes/terminal)**: dùng `Start-Process` qua file `.ps1` với `Start-Process node.exe -ArgumentList "dist/.../server.mjs" -WorkingDirectory ... -WindowStyle Hidden -RedirectStandardOutput server.log`. Lưu ý: PS 5.1 không có `-Environment` param → set env qua `.cmd` wrapper hoặc đặt trong `$env:` trước `${Start-Process}`. Redirect giữ handle nên `-File` call bị timeout 180s — process vẫn chạy, chỉ cần check listener sau.

6. **Angular CLI 22 `ng new`**: MSYS path `/d/...` KHÔNG được dịch cho CLI native → project tạo ở `D:\d\angular-demo`. Luôn dùng path Windows `D:\angular-demo` hoặc `cd /d` + tên thư mục.

7. **serverRoutes**: `RenderMode.Prerender` → build báo "Prerendered 0 static routes" và dist không có index.html tĩnh (chỉ index.csr.html). Muốn SSR động dùng `RenderMode.Server`. Browser assets serve từ `dist/.../browser/`, server engine từ `dist/.../server/`.

8. **`@defer`/`@` trong text HTML**: viết `&#64;defer` nếu muốn hiển thị chữ thay vì bị Angular parse là control-flow error (NG5002).

## Signal Forms API (v22) — cú pháp chính xác

Import từ `@angular/forms/signals`:
- `form(modelSignal, schemaFn)` → FieldTree. `form(this.model, (schema) => { required(schema.name, {message}); email(schema.email); minLength(...); })`
- Bind trong template: `<input [formField]="myForm.name">` — KHÔNG dùng `[formField]="myForm.name()"` (bỏ `()`). `FormField` directive phải được import vào `imports: [...]` của component.
- Đọc state: `myForm.name()` (gọi FieldTree node như function) → object có `.value()`, `.errors()`, `.invalid()`, `.touched()`. Lỗi: `name().errors()[0].message`.
- Reset: KHÔNG có `.control.reset()`. Set lại model signal gốc: `this.model.set({...})`.
- Submit custom: dùng `(submit)` event handler, KHÔNG cần `formRoot` (trừ custom submit flow).
- `formRoot`/`FormRoot` là directive trên `<form>`, chỉ dùng cho custom submit binding.

## Material 22 (v22) + Tailwind v4 — pitfalls đã gặp khi nâng cấp demo

1. **Material 22 KHÔNG còn export `*Module` từ root `@angular/material`**. `MatCardModule`/`MatButtonModule`... không có trong `index.d.ts` gốc → `ng add` cài nhưng dùng module sẽ lỗi "Unknown reference". **Import standalone components từng entry point**: `import { MatCard, MatCardContent } from '@angular/material/card'`, `MatButton from '@angular/material/button'`, `MatTabGroup/MatTab from '@angular/material/tabs'`, `MatIcon from '@angular/material/icon'`, `MatProgressBar`, `MatDivider`, `MatChip`, `MatSlideToggle`, `MatSelect/MatOption`, `MatInput`, `MatFormField/MatLabel/MatError`, `MatToolbar`. Rồi liệt kê trong `imports: [...]`.

2. **`provideAnimationsAsync` cần `@angular/animations`** (`from '@angular/platform-browser/animations/async'`). Cài `npm i @angular/animations@22` (khớp version core, dùng `@22` để tránh peer conflict). Thiếu → lỗi build "Could not resolve @angular/animations/browser".

3. **Theme**: `styles.scss` dùng `@use '@angular/material' as mat;` + `@include mat.theme((color: (primary: mat.$violet-palette, tertiary: mat.$blue-palette, theme-type: dark), typography: Roboto))`. Palette có sẵn: `$azure $blue $chartreuse $cyan $green $magenta $orange $red $rose $violet $yellow`. `ng add` mặc định light azure/blue → đổi thành `theme-type: dark` + violet/blue cho hợp dark theme.

4. **Tailwind v4**: cài `npm i tailwindcss @tailwindcss/postcss postcss`, **tạo `.postcssrc.json`** (KHÔNG phải `postcss.config.js` — Angular 22 Vite builder KHÔNG đọc postcss.config.js, chỉ đọc `.postcssrc.json`):
```json
{ "plugins": { "@tailwindcss/postcss": {} } }
```
Thêm `@import 'tailwindcss';` vào `styles.scss` (**`@use` phải đứng TRƯỚC `@import`** — lỗi "@use rules must be written before any other rules"). Thêm `@source './app/**/*.html';` (để scan Angular template, sinh utilities) nếu cần. Builder `@angular/build:application` đọc `.postcssrc.json` từ project root. Tailwind v4 chỉ sinh classes được dùng (tree-shake).
**Pitfall lớn nhất:** dùng `postcss.config.js` → Tailwind im lặng KHÔNG sinh class → toàn bộ `flex/grid/gap/max-w-6xl` vô hiệu → layout vỡ (xếp dọc, tràn, chồng). Biểu hiện: css file ~24KB nhưng grep `.flex`/`.grid` = 0. Fix = đổi sang `.postcssrc.json`.

**Pitfall số 2 — layout vỡ vẫn xảy ra dù Tailwind sinh class (vars không emit):** với `.postcssrc.json`, Tailwind sinh `.max-w-6xl{max-width:var(--container-6xl)}` và `.px-6{padding-inline:calc(var(--spacing)*6)}` nhưng **`--spacing`/`--container-6xl` KHÔNG được emit** trong CSS → các utility dùng `var()` bị invalid → `max-w-6xl`/`px-6`/`py-24`/`gap-5` vô hiệu → vẫn vỡ. Fix: thêm khối `@theme { --spacing: 0.25rem; --container-6xl: 72rem; ... }` sau `@import 'tailwindcss'`. Verify: `grep -- '--spacing:' dist/*.css`.

**Pitfall số 3 — custom CSS đè Tailwind:** `* { padding: 0 }` và `.hero, section, footer { max-width: 100% }` (universal/element selector) đè override utility `.px-6`/`.max-w-6xl` vì chúng có specificity thấp hơn element+layer. Bỏ padding/max-width khỏi universal selector, chỉ giữ `box-sizing`; dùng `overflow-x: clip` thay vì `max-width:100%` cho section. Hoặc dùng custom class cứng (`.app-wrap { max-width:72rem; margin-inline:auto; padding-inline:1.5rem }`) cho container thay vì phụ thuộc Tailwind `max-w-6xl`/`px-6`.

5. **Budget warning**: bundle thêm Material → vượt budget 500kB. Đây chỉ là WARNING, không chặn build, có thể tăng budget trong angular.json.

6. **Control flow `@`/`(click)` trong template Angular v22**: native `@if`/`@for`/`@defer`. `@switch` cũng có. Tránh viết chữ `@` trong text (phải `&#64;`).

## Angular Best Practicesactices (code convention)

- Use signals cho state management.
- Lazy load feature routes.
- `NgOptimizedImage` cho mọi ảnh tĩnh.
  - ⚠️ `NgOptimizedImage` KHÔNG chạy với inline base64 images.
- Accessibility: PASS AXE checks, tuân WCAG AA (focus management, color contrast, ARIA).

### Components
- Nhỏ, một trách nhiệm duy nhất.
- `input()` / `output()` functions thay decorators.
- `model()` cho two-way binding `[(prop)]` thay cặp input+output.
- `computed()` cho derived state.
- `linkedSignal()` cho state derived từ nhiều reactive sources cần đồng bộ.
- Prefer inline templates cho component nhỏ.
- Khi dùng external template/style, dùng path **tương đối** so với file TS.

### Forms (quan trọng — đổi từ v22)
- **Prefer Signal Forms** (`@angular/forms/signals`). Stable từ v22+, signal-based state, type-safe field access, schema-based validation.
- Khi không dùng Signal Forms → prefer **Reactive forms** hơn template-driven.

### State Management
- Signals cho local component state.
- `computed()` cho derived state.
- Giữ transforms thuần & dự đoán được.
- Không `mutate` — dùng `update`/`set`.

### Templates
- Giữ template đơn giản, tránh logic phức tạp.
- Native control flow `@if`/`@for`/`@switch`.
- Async pipe cho observables.
- **Không assume** globals như `new Date()` luôn có sẵn.

### Services
- Một trách nhiệm.
- `providedIn: 'root'` cho singleton.
- `@Service` decorator cho service mới (v22+, thay `@Injectable({providedIn:'root'})`).
- `inject()` thay constructor injection.

## SSR & Hybrid Rendering

### 3 chiến lược render
| Phương thức | Tốc độ | Cách hoạt động | Phù hợp |
|---|---|---|---|
| CSR (mặc định) | Chậm nhất | Server chỉ gửi JS | Map, offline, ít server cost |
| SSR | Nhanh | Server render HTML mỗi request | SEO, data riêng từng user |
| Prerender (build-time) | Nhanh nhất | Build sẵn HTML tĩnh | Trang giống nhau mọi user (landing, blog) |

### SSR requirements
- Code render trên server **KHÔNG phụ thuộc browser API** (tránh `window`, `document` direct).
- SSR render HTML mỗi request → tốn server hosting.

### Hydration
- Tái dùng DOM server phía client thay vì tạo lại.
- **Event Replay:** click/scroll/focus trước khi hydration xong được lưu vào Event Contract rồi phát lại.
- **Constraint:** DOM server & client **phải giống hệt nhau** (kể cả whitespace & comment nodes). HTML từ SSR **KHÔNG được chỉnh sửa** giữa server ↔ client.

### Incremental Hydration (v22 feature chính) ⭐
- Bật **mặc định** khi dùng `provideClientHydration()`.
- Tự động bật Event Replay — xoá được `withEventReplay()` nếu đang có.
- Opt-out: `provideClientHydration(withNoIncrementalHydration())`.
- Gắn `hydrate` trigger vào `@defer` block: server render content chính (không placeholder → không layout shift), client defer dependency tới khi trigger fire.
- 3 loại trigger: `hydrate on` (idle|viewport|interaction|hover|timer), `hydrate when <cond>`, `hydrate never` (manual). Nhiều trigger cách `;`.

```typescript
@defer (hydrate on interaction; hydrate on idle) {
  <heavy-component />
}
```

```typescript
// app.config.ts — enable hydration (incremental auto-on)
bootstrapApplication(App, {
  providers: [provideClientHydration()],
});
```

### Server config (`app.config.server.ts`)
```typescript
import {provideServerRendering, withRoutes} from '@angular/ssr';

const serverConfig: ApplicationConfig = {
  providers: [
    provideServerRendering(
      { maxResponseBodySize: 5 * 1024 * 1024 }, // 5MB, default 1MB → lỗi NG02825 nếu vượt
      withRoutes(serverRoutes),
    ),
  ],
};
```
- `maxResponseBodySize` mặc định **1MB**; vượt → `NG02825`. Giữ càng nhỏ càng tốt (memory/DoS risk).

### HTTP Transfer Cache
- `HttpClient` chạy server -> cache -> serialize vào HTML -> browser tái dùng thay vì gọi lại lúc init. Ngừng cache khi app stable trên client.
- `withHttpTransferCacheOptions({...})`: `includeRequestsWithAuthHeaders`, `includeRequestsWithCredentials`, `includeNonCacheableRequests` — mặc định **loại trừ** request có auth/cookie/cache-control(`no-store`).
- Override per-request: `http.get(url, {transferCache: {includeHeaders: ['X-Foo']}})`.

## AI Tooling (angular.dev/ai)

### Angular CLI MCP Server
Chạy `npx @angular/cli mcp`. Config theo IDE: `.antigravity/mcp.json`, `.cursor/mcp.json`, hoặc `.vscode/mcp.json` (tất cả: `command: npx, args: ["-y", "@angular/cli", "mcp"]`).

**Tools có sẵn:**
- `ai_tutor` — khởi động Angular AI tutor tương tác.
- `devserver.start` / `devserver.stop` / `devserver.wait_for_build` — quản lý `ng serve`.
- `get_best_practices` — lấy Best Practices Guide (standalone, typed forms, ...).
- `list_projects` — đọc `angular.json`, liệt kê apps/libs.
- `onpush_zoneless_migration` — phân tích & lập kế hoạch migrate sang OnPush/zoneless.
- `run_target` — chạy build/test/lint/e2e/deploy.
- `search_documentation` — tra docs angular.dev.

**Workflow chuẩn (agent tự động):**
1. *Performance tuning:* `list_projects` → migrate signals → `onpush_zoneless_migration` lặp tới khi xong → `run_target test`.
2. *Feature + TDD:* `search_documentation` → `get_best_practices` → `devserver.start` → `wait_for_build` → viết test → `run_target`.

### Agent Skills (tương tự skill Hermes)
Repo chính thức `github.com/angular/skills`. Cài:
```
npx skills add https://github.com/angular/skills
```
Skills:
- **angular-developer** — code + architecture guidance (signals, linkedSignal, resource, forms, DI, routing, SSR, ARIA, animations, testing, CLI).
- **angular-new-app** — tạo app CLI + cấu trúc hiện đại.

### Rules files (đưa context vào IDE/LLM)
- Antigravity → `GEMINI.md`; Copilot → `.github/copilot-instructions.md`; Cursor → `cursor.md`/`.cursorrules`; JetBrains → `guidelines.md`; VS Code → `.instructions.md`; Windsurf → `guidelines.md`.
- `llms.txt` / `llms-full.txt` — index + compiled docs để LLM tra cứu.

### 3 stack xây AI app trong Angular
| Stack | Vị trí | Phù hợp |
|---|---|---|
| Genkit | Full-stack (cần server) | Agentic workflows, recommendation |
| Firebase AI Logic | Client-side only | Chatbot, real-time text analysis |
| Gemini API | Full-stack | Direct model control (image gen, data processing) |

Starter kits (repo Angular chính thức): `genkit-angular-starter-kit`, `genkit-angular-story-generator`, `firebase-ai-logic-angular-example`, `ai-text-editor`, `ai-chatbot`.

## Stack khuyến nghị cho Angular (đã thống nhất với anh Đạt)

**"B" = Angular Material + SCSS thuần + design tokens** (BỎ Tailwind). Đây là lựa chọn ổn định nhất, ít xung đột, hợp làm giao diện premium Linear/Stripe.

- **Ui components**: Angular Material 22 (standalone imports, không dùng `*Module`)
- **Styling**: SCSS thuần + design tokens (`:root` vars: --bg, --surface, --accent, --radius, --container=1152px...) — KHÔNG dùng Tailwind
- **Forms/State**: signal forms (`form()` + `formField` + `schema()`) + signals (có sẵn v22)
- **Layout container**: custom class `.app-wrap { max-width: 72rem; margin-inline: auto; padding-inline: 24px }` thay `max-w-6xl mx-auto px-6`

**Lý do bỏ Tailwind**: v4 có nhiều pitfall (config `.postcssrc.json`, `@theme` emit vars, custom CSS đè specificity) — dùng SCSS thuần tránh hết. Material + SCSS = chuẩn framework, ổn định, không "bleeding edge" đau đầu.

**Quy trình làm Angular UI (để không vỡ layout như lần trước)**:
1. Viết template bằng **class SCSS semantic có nghĩa** (`.hero-copy`, `.feature-card`, `.dash-grid`, `.nav-links`) — không dùng utility class.
2. Viết SCSS tương ứng cho từng class.
3. Build → **verify bằng mắt trên Chrome/browser thật (chụp màn hình + vision)**, KHÔNG chỉ tin đo đạc headless.
4. Đặc biệt kiểm tra: tràn ngang (`scrollWidth>innerWidth`), grid cột, code không bị cắt `...`, form hiển thị đủ.

**Pitfall riêng**: Material `mat-tab-group` content có `mat-mdc-tab-body-content` transform off-screen (không phải lỗi). Card grid dùng `grid-template-columns: repeat(auto-fit, minmax(300px,1fr))` + bỏ `height:100%` để code không bị cắt (để `margin-top:auto` trên result đẩy xuống đáy).

**Theme toggle (light/dark) — view encapsulation là bẫy lớn**: các override `html.light .appbar`/`.dash-card` đặt trong `app.scss` (component style) KHÔNG áp cho element vì App có `ViewEncapsulation.Emulated` — selector scope theo template, `html`/element ngoài scope không match. **Phải đặt override `html.light ...` trong `styles.scss` global** (unscoped). Đồng thời `--bg`/`--text`/Material `--mat-sys-surface` cho light theme cũng phải override trong `styles.scss` (biến global), KHÔNG trong app.scss. Cách test nhanh: `getComputedStyle(document.body).backgroundColor` đổi `rgb(10,10,15)` → `rgb(247,248,252)` là light áp. **Escape `@` trong text HTML**: viết `&#64;defer` (không escape → lỗi NG5002 "Incomplete block").

## Pitfalls đã gặp

- **`standalone: true` + `OnPush` explicit** — AI hay code theo thói quen cũ, gây review noise. Nhắc: mặc định từ v20+/v22+.
- **`@Input`/`@Output` decorator** — code cũ vẫn dùng, phải đổi sang `input()`/`output()`.
- **`new Date()` / globals trong template** — không giả định có sẵn trên server (SSR).
- **Inline base64 images + `NgOptimizedImage`** — không chạy, đổi sang URL.
- **Server & client DOM mismatch** — khi hydration, HTML server không được chỉnh gì giữa đường.

## Verify

- `ng build` pass, `ng serve` chạy, hydration không log mismatch errors.
- `ng lint` + `ng test` pass.
- SSR: mở source page → thấy HTML đã render (không phải empty root).
- AI code: pass AXE checks.
