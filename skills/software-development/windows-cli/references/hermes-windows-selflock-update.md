# Cập nhật Hermes trên Windows gặp self-lock `.pyd` (defer vô hạn) — recipe

## Triệu chứng
`hermes update` luôn thoát với:
```
✗ This updater process has already loaded native venv modules that
  the dependency sync must replace:
    cryptography (_rust.pyd)
  On Windows a mapped extension cannot be replaced by the process holding it.
  The update has been deferred: the next `hermes` launch will complete it...
```
Và version cứ kẹt mãi (vd v0.20.1), dù chạy `hermes update` nhiều lần, cả từ Terminal ngoài Hermes hay `--force-venv`.

## Nguyên nhân gốc
- Máy **chỉ có 1 Python duy nhất là venv Hermes** (`venv/Scripts/python.exe`). Không có Python hệ thống riêng (`python3` WindowsApps là stub Store).
- `hermes` là launcher **trong venv** (`hermes` trỏ `venv/Scripts/hermes`) nên *mọi* cách chạy `hermes update` đều dùng venv → load `cryptography.hazmat.bindings._rust` vào `sys.modules` → Windows không cho thay `.pyd` đang mapped → tự defer.
- Guard trong `hermes_cli/update_cmd.py` (`_detect_self_loaded_native_modules`, `_SELF_LOCKING_NATIVE_MODULES`) chỉ kiểm tra `"cryptography.hazmat.bindings._rust" in sys.modules`.

## Giải pháp đã kiểm chứng (2026-08-22)
Chạy updater bằng **UV-managed Python độc lập** (không dính venv Hermes), để `_rust` không bao giờ vào `sys.modules`:

1. Xác nhận UV python độc lập có sẵn:
   ```bash
   uv python list | grep -E '3\.11|3\.12'
   # → C:\Users\<user>\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe
   ```
2. Kiểm tra guard sẽ pass:
   ```bash
   U="C:/Users/<user>/AppData/Roaming/uv/python/cpython-3.11-windows-x86_64-none/python.exe"
   "$U" -c "from hermes_cli.update_cmd import _detect_self_loaded_native_modules; print(_detect_self_loaded_native_modules())" 
   # → []  (rỗng = pass, update sẽ chạy thật)
   ```
3. Gọi thẳng `_cmd_update_impl` với argparse Namespace giả lập `update --yes --force --force-venv`:
   ```python
   # wrapper.py (đặt trong ~/.hermes/hermes-agent/)
   import sys, argparse
   assert "cryptography.hazmat.bindings._rust" not in sys.modules
   from hermes_cli.update_cmd import _cmd_update_impl
   ns = argparse.Namespace(gateway=False, check=False, no_backup=False, backup=False,
                           yes=True, branch=None, force=True, force_venv=True)
   rc = _cmd_update_impl(ns, gateway_mode=False)
   ```
   Chạy: `"$U" wrapper.py` (background, notify_on_complete).
4. **Cảnh báo**: cuối log wrapper có thể hiện `ImportError: bounded_probe_run` — vô hại, xảy ra sau khi update đã xong (wrapper dùng code cũ). Kiểm tra kết quả bằng `hermes --version` (không phải `hermes version`).

## Xác minh thành công
```bash
hermes --version   # → Hermes Agent v0.20.5 (2026.8.19) ... (tăng version)
cd ~/AppData/Local/hermes/hermes-agent && git rev-list --count HEAD..origin/main  # → 0
```
Lưu ý: `hermes version` subcommand in ra usage (CLI refactor) — dùng `hermes --version`.

## Pitfall
- `hermes config set model.default <v>` chạy đúng nhưng `hermes config set model <v>` thì báo `unrecognized arguments` — key lồng phải chấm (`model.default`, `model.base_url`, `providers.omniroute.base_url`).
- Sau update lớn, CLI subcommands có thể đổi (thêm `bots`, `profile`...); vài `hermes X` cũ thành `unrecognized`. Dùng `hermes <sub> --help` để xác nhận.
- Pre-update backup (`hermes update --backup`) tạo zip ~390MB trong `~/AppData/Local/hermes/backups/` — kiểm tra disk trống trước (cần vài trăm MB).
