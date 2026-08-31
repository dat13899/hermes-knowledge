---
name: windows-cli
description: "Windows CLI/git-bash/MSYS2 workflows: native EXE calling, path conversion, archive extraction, package management. Gotchas and workarounds for running Hermes on Windows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
---

# Windows CLI Workflows

Hermes on Windows runs under git-bash (MSYS2/MINGW64). Most POSIX tools
work, but calling **native Windows executables** (.exe, .msi, .bat from
cmd.exe) triggers MSYS2's automatic path conversion — which frequently
breaks paths the native tool can't understand.

This skill covers the patterns and workarounds.

## References

- `references/disk-cleanup-powershell.md` — disk cleanup & app removal on
  Windows: PowerShell size-scanning (du hangs on Windows trees), the
  "Device or resource busy" directory-lock hunt (background du / bash CWD
  holding handles), silent NSIS/Inno uninstall quirks, safe-deletion list.
- `references/hermes-windows-selflock-update.md` — `hermes update` deferring
  forever on Windows (venv self-locks its own `cryptography .pyd`) → run the
  updater via a UV-managed independent Python interpreter so `_rust` never
  enters `sys.modules`; also `.config set` dotted-key gotcha + `--version`
  vs `version` after big refactors.

### Heredoc nuốt backslash — luôn viết file script bằng tool write_file

`cat > file << 'EOF'` trong terminal (git-bash) **nuốt backslash** của Windows
path → executable path vỡ thành `C:UsersdatelAppDataLocal...`. Đã dính 2 lần
trong 1 session khi viết playwright script có `exe = 'C:\\Users\\...'`.

Rule: script có Windows path (node/playwright/python) → **luôn dùng tool
`write_file`** (hoặc `patch`), KHÔNG dùng heredoc trong terminal. File viết
bằng write_file chạy đúng ngay cả khi lint hiển thị lỗi giả
(`Cannot find module 'C:\c\Users\...'` — chỉ là MSYS check path, bỏ qua).

### MSYS `//` flag mangling (taskkill, ipconfig)

Git-bash đổi `//F` thành đường dẫn gốc → `taskkill //F //PID` lỗi "Invalid
argument/option". Dùng cờ `-` cho taskkill:

```bash
taskkill -F -PID 1234        # OK
```

`ipconfig //flushdns` cũng lỗi kiểu này → bọc qua cmd:
`cmd //c "ipconfig /flushdns"`.

### MSYS biến dạng `$_` trong powershell -Command inline

Khi cwd là thư mục "path-like" (vd `/d/daily`), `$_` bên trong
`powershell -Command "... $_.ProcessId ..."` bị MSYS đổi thành
`/d/daily.ProcessId` → parse error. Escape không đáng tin → **viết script
.ps1 ra file rồi chạy bằng -File**:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File check.ps1
```

### Node: path MSYS `/d/...` bị đổi thành `D:\d\...`

`node /d/daily/server.js` → node nhận `D:\d\daily\server.js` → MODULE_NOT_FOUND.
Dùng workdir + relative path:
```bash
node server.js    # với workdir=D:\daily
```
Khi chạy script check ở `C:\Users\datel` mà cwd là `/d/daily`:
```bash
cd /c/Users/datel && node "C:\Users\datel\check.js"   # path tuyệt đối Windows-style
```
 /d/daily/server.js` → MSYS đổi thành `D:\d\daily\server.js` →
MODULE_NOT_FOUND. Cách chạy an toàn:

```bash
cd /d/daily && node server.js     # workdir + relative path (chuẩn nhất)
node "D:/daily/server.js"          # Windows path dạng forward-slash cũng OK
```

Lưu ý: `write_file` tự chạy lint bằng node; nếu cwd là thư mục D: drive,
lint báo sai "Cannot find module 'C:\c\...'" — ignore, verify bằng
`cd /c/Users/... && node file.js`.


## Key Pattern: MSYS2 Path Conversion Bypass

MSYS2 translates POSIX-style paths (`/c/Users/...`) to Windows paths
(`C:\Users\...`) when it sees arguments it thinks are paths — but it
often mangles them, especially for native Windows EXEs.

### Best: `cygpath -w` + `MSYS2_ARG_CONV_EXCL`

```bash
export MSYS2_ARG_CONV_EXCL="*"
"/path/to/native.exe" arg1 "$(cygpath -w '/c/Users/me/some path/file.rar')" "$(cygpath -w '/c/Users/me/output/')"
```

- `MSYS2_ARG_CONV_EXCL="*"` — tells MSYS2 to skip ALL automatic path conversion
- `cygpath -w` — converts a POSIX path to a Windows-native path for the tool
- Use `cygpath -w` for any argument that is a file path

### Pitfall: native curl.exe silently writes 0 bytes to MSYS `/tmp/` paths

Windows-native `curl.exe` (the one in PATH on this host) does NOT understand
MSYS paths like `/tmp/out.js`. Running `curl -o /tmp/out.js URL` reports
`size_download: 0` and creates NO file, while `curl -v` proves the server sent
full data. The response is indistinguishable from a broken server (200 OK,
`Transfer-Encoding: chunked`, empty body) and can burn 10+ minutes of
debugging a perfectly healthy server.

- **Rule:** when a native Windows tool takes an output path as an ARGUMENT
  from git-bash, pass an explicit Windows path: `-o "C:/Users/<user>/AppData/Local/Temp/out.js"`,
  or convert: `-o "$(cygpath -w /tmp/out.js)"`.
- **Verify with `wc -c` on the exact path you passed** — MSYS `wc` reads `/tmp/`
  fine, so curl and wc live in different path universes; that mismatch is the tell.
- Shell redirection (`> /tmp/x`) is handled by bash and is fine — only
  in-argument paths (like `-o`, `--output`, `--data-binary @file`) break.
- The same applies to any native EXE with output-file arguments (`unrar x ... dest/`,
  `7z e ... -o...`).

### When Needed

Any native Windows EXE called from git-bash that takes file/directory
arguments:
- `unrar.exe`, `rar.exe`, `7z.exe` — archive tools
- `winget.exe` — package manager
- `cmd.exe /c ...` — when passing paths inside the command string
- Any `.exe` compiled for Win32 (not MSYS2)

### When NOT Needed

MSYS2-aware tools (compiled for MSYS2/MINGW, found in `/mingw64/bin/`,\
not affected. Most POSIX tools (grep, sed, awk, node via MSYS2) work
without escaping.

## Pitfall: `path.resolve()` with absolute paths on Windows

When writing Node.js server code that resolves request paths against a
base directory (e.g. a public/ or dist/ folder), **never pass a
pathname that starts with `/` as the second argument to `path.resolve()`**
— on Windows it treats it as an absolute path and silently strips the
base:

```js
const PUBLIC_DIR = path.join(__dirname, 'public');

// BAD — /stream resolves to C:\stream, dropping PUBLIC_DIR entirely
path.resolve(PUBLIC_DIR, '/stream');
// → 'C:\\stream'

// GOOD — path.join handles leading slashes safely
path.join(PUBLIC_DIR, '/stream');
// → 'C:\\...\\public\\stream'
```

The `isSafePath()` helper that uses `path.resolve()` is unsafe for
SPA-style catch-all routes (`/stream`, `/docs/...`) on Windows.
Replace with a `path.join()` + `startsWith()` check instead:

```js
if (!filePath.startsWith(PUBLIC_DIR)) { /* 403 Forbidden */ }
```

Also ensure `serveStatic()` itself skips the base-directory check when
serving the SPA fallback `index.html` from a different directory
(e.g. `dist/` vs `public/`).
- `grep`, `sed`, `awk`, `find`, `ls` — MSYS2 ports, no conversion issues

## Archive Extraction (RAR, ZIP, 7z, etc.)

### Install a Tool if Missing

```bash
# WinRAR/unrar (handles RAR v5)
winget install --id RARLab.WinRAR

# 7-Zip (handles RAR, ZIP, 7z, hundreds of formats)
winget install --id 7zip.7zip
```

### Extract RAR

```bash
rar_path="/c/Users/me/file.rar"
out_dir="/c/Users/me/output/"
mkdir -p "$out_dir"

export MSYS2_ARG_CONV_EXCL="*"
"/c/Program Files/WinRAR/unrar.exe" x -y "$(cygpath -w "$rar_path")" "$(cygpath -w "$out_dir")"
```

## Running .bat or .cmd Files

Native batch files need `cmd.exe /c`:

```bash
cd /c/Users/me/project
export MSYS2_ARG_CONV_EXCL="*"
cmd.exe /c start.bat
```

The `export MSYS2_ARG_CONV_EXCL` is essential here — without it,
paths the .bat file passes to its own child processes get mangled.

For long-running bots/servers, pair with `background=true` +
`notify_on_complete=true` in terminal().

## npm Install with Script Approval

Some npm packages need install scripts (esbuild, native modules):

```bash
cd /c/Users/me/project
npm i
npm approve-scripts <pkg1> <pkg2>  # approve specific packages
# or: npm approve-scripts --allow-scripts-pending
```

## Pitfalls

- **Trailing backslash in bash strings**: In double-quoted bash strings,
  `"path\\"` escapes the closing quote. Use forward slashes or avoid
  trailing `\` after the directory path.
- **`export` MSYS2_ARG_CONV_EXCL before, not as prefix**: One-shot
  `MSYS2_ARG_CONV_EXCL="*" cmd ...` can fail in nested shell contexts.
  Always `export MSYS2_ARG_CONV_EXCL="*"` on its own line first.
- **winpty not for non-interactive**: `winpty` requires a TTY. For
  non-interactive native EXEs, use `MSYS2_ARG_CONV_EXCL` + `cygpath -w`
  instead.
- **`winget` path format**: winget accepts `--id` package identifiers
  (e.g., `RARLab.WinRAR`, `7zip.7zip`) — no path conversion needed.
- **npm deprecation warnings**: `npm i` often shows deprecation and
  vulnerability warnings for transitive deps. These are normal for
  legacy projects; audit only when the user asks.
- **`taskkill /f /im node.exe` kills ALL node processes**: On Anh Đạt's
  machine, 9Router (port 20128) runs as a separate Next.js node.exe
  process and must NEVER be killed. Use `scripts/kill-node.sh` instead
  — it kills **only the PID listening on port 3000**.

  **CRITICAL — 4 versions before correct (2026-07-23):**
  - V1 (naive): `taskkill /f /im node.exe` — killed everything ❌
  - V2 (tasklist filter): List all `node.exe`, compare against 20128
    PID. But Next.js spawns multiple worker PIDs under same image name.
    Workers got killed → crashed parent 20128 ❌
  - V3 (PID file): Save 20128 PID to file. But 20128 restarts to new
    PID, file holds stale PID → killed the new PID ❌
  - V4 (final, correct): Kill ONLY the PID listening on port **3000**
    via `netstat | grep ":3000 " | grep LISTENING`. Zero awareness of
    other processes. If port 3000 not LISTENING → abort, zero kills ✅

  **DO NOT revert to any earlier approach.** Listing node.exe by image
  name is inherently dangerous: Next.js runs multiple processes under
  the same name. Port-based targeting (`:3000`) is the only safe method.

## Python Toolchain (uv on Windows)

Anh Đạt's Windows Hermes uses **uv** as the Python package manager (not system pip). Key differences from standard Python on Linux:

### `python3` vs `python`

**`python3` opens Microsoft Store** on Windows (App Execution alias). Use `python` only:
```bash
python --version                   # good → Python 3.11.15
python3 --version                  # bad → opens MS Store
python3 -c "print(1)"              # bad → opens MS Store
python -c "print(1)"               # good
```
For piped Python one-liners in terminal, always use `python -c` not `python3 -c`.

### uv-installed packages NOT in PATH

Packages installed via `uv pip install` are placed in uv's internal environment at `~/AppData/Roaming/uv/python/...`. They are **not added to Windows PATH** even if they install CLI entry points.

**Wrong** — FileNotFoundError:
```python
subprocess.run(["yt-dlp", ...])     # FileNotFoundError
```

**Right** — invoke via python module:
```python
import sys, subprocess
subprocess.run([sys.executable, "-m", "yt_dlp", ...])  # works
```

This applies to any uv-installed package called from subprocess: `yt-dlp`, `black`, `ruff`, `pytest`, etc.

### Install commands

```bash
uv pip install yt-dlp    # ✓ correct
pip install yt-dlp       # ✗ may use wrong python
```

## When to Use This Skill

- User asks to extract an archive (esp. RAR) on Windows
- A native Windows EXE fails with "Unknown option" or garbled paths
- Setting up a Node.js project that needs native module compilation
- Any task that mixes MSYS2 tools with native Win32 executables
