# Telegram Delivery — Video Download Delivery Status

## Bot API limit: 50 MB

Hermes connects to Telegram via **Bot API**, which caps outgoing files at **50 MB** regardless of account tier. This is a hard platform limit, not configurable.

## Desktop / Mobile app limit: 2 GB

The native Telegram apps (Desktop, iOS, Android) support **2 GB** file transfers via **Saved Messages** or direct DMs. This is the recommended fallback for files > 50 MB.

## MEDIA: convention

When the agent includes `MEDIA:/absolute/path/to/file` in a response, Hermes delivers the file natively. For video under 50 MB this means an inline video player in chat. For files > 50 MB this **fails silently** — the message is sent but the file is dropped.

## MEDIA: is NOT file-type-dependent

Telegram treats the MEDIA: file the same whether the extension suggests "video" or "document" — the 50 MB limit applies universally.

## Upload host status

Tested 2026-07-10 from this Windows machine (git-bash/MSYS2):

| Host | Result | Failure reason |
|---|---|---|
| [catbox.moe](https://catbox.moe) | ❌ 412 Invalid uploader | Blocks requests without browser-like user-agent / auth |
| [0x0.st](https://0x0.st) | ❌ uploads disabled | "uploads disabled — it's been almost nothing but AI botnet spam" |
| [tmpfiles.org](https://tmpfiles.org) | ❌ 413 Payload Too Large | Cloudflare limit via their API |
| [gofile.io](https://gofile.io) | ❌ auth required | Requires account token for upload API |
| [pixeldrain.com](https://pixeldrain.com) | ❌ auth required | Requires API key in HTTP Basic Auth |

**Bottom line**: there is no reliable free upload host accessible from this env. Do not attempt upload delivery for large files — save to disk and tell the user.

## Format picking for Telegram delivery

When user wants a file sent via MEDIA: (< 50 MB):

1. Download with `-S "res:1080,codec:h264,ext:mp4"` (h264 codec for quality)
2. Check actual file size after download (metadata `filesize` is unreliable — YouTube estimated values are often wrong)
3. If ≤ 48 MB (buffer for overhead) → send MEDIA:
4. If > 48 MB → report path + recommend Telegram Desktop

## User preference (Anh Đạt)

- Ưu tiên chất lượng: 1080p > 720p > 480p > ...
- Không upload host, không gửi file > 50MB qua bot
- File > 50MB: chỉ tải về thư mục `C:\Users\datel\Downloads\dlv\`, báo path
- File < 50MB: gửi thẳng qua MEDIA:
