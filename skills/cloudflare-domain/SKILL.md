---
name: cloudflare-domain
description: Setup domain (kể cả .vn, .io.vn) với Cloudflare DNS — mua ở registrar VN, trỏ NS về Cloudflare
---

# Cloudflare Domain Setup

## Khi nào dùng

- User mua domain ở registrar VN (Nhân Hòa, P.A VN, Mắt Bão, Tenten…)
- Muốn dùng Cloudflare DNS free (CDN, SSL, proxy, firewall)
- Domain là `.vn`, `.com.vn`, `.io.vn`, `.id.vn`, `.ai.vn` (VNNIC)

## Lưu ý về .vn domains

- `.io.vn`, `.id.vn`, `.ai.vn` là ccSLD do VNNIC quản lý
- Đã được thêm vào Public Suffix List (PSL) từ 06/2023
- **Cloudflare hỗ trợ từ giữa 2023** — có thể add bình thường
- Nếu Cloudflare từ chối: thử lại sau vài ngày, hoặc dùng **CNAME setup (partial)** — xem link dưới

## Các bước

### 1. Add domain vào Cloudflare

```
https://dash.cloudflare.com → Add a domain → nhập domain
```

Chọn gói **Free**. Cloudflare sẽ quét DNS records tự động.

### 2. Cập nhật bản ghi DNS

Check lại các bản ghi DNS trên Cloudflare khớp với records hiện tại (từ registrar hoặc zonedns.vn). Quan trọng: A/AAAA/CNAME records trỏ đúng IP service.

### 3. Đổi nameserver ở registrar

Cloudflare cấp 2 nameserver (vd: `niki.ns.cloudflare.com`, `sima.ns.cloudflare.com`).

Vào **registrar (Nhân Hòa / P.A VN / ...)** → Quản lý tên miền → Change Nameserver → thay bằng NS của Cloudflare.

Registrar VN nào hỗ trợ:
| Registrar | Đổi NS được? | Ghi chú |
|---|---|---|
| Nhân Hòa | ✅ | Hướng dẫn: wiki.nhanhoa.com/kb/tro-ten-mien-ve-cloudflare |
| P.A VN | ✅ | |
| Mắt Bão | ✅ | |
| Tenten | ✅ | |

### 4. Đợi propagation

DNS propagation: vài phút → 24h. Cloudflare sẽ báo "Active" khi hoàn tất.

### 5. SSL/TLS

Vào Cloudflare → SSL/TLS → chọn **Full (strict)** nếu có SSL gốc, hoặc **Flexible** nếu ko.

## CNAME setup (partial) — khi Cloudflare ko chấp nhận NS change

Nếu Cloudflare ko cho add domain (VD: .vn chưa được hỗ trợ đầy đủ), dùng partial (CNAME) setup:

https://developers.cloudflare.com/dns/zone-setups/partial-setup/

## Pitfalls

- **zonedns.vn**: nếu đang dùng zonedns.vn quản lý DNS, cần backup records trước khi đổi NS — sau khi đổi NS sang Cloudflare, zonedns.vn hết tác dụng
- **.io.vn**: trước 06/2023 ko được Cloudflare hỗ trợ. Từ 06/2023+ đã OK
- **Propagation lâu** với .vn domain: có thể lâu hơn .com do VNNIC cache