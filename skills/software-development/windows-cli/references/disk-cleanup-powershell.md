# Disk Cleanup & App Removal on Windows (from git-bash)

Worked recipe from a real cleanup session on this host (C: drive 71% full →
61% full, ~10GB freed).

## 1. Size analysis: PowerShell beats `du` (always)

`du -sh` / `du -h --max-depth=1` over Windows trees (node_modules, AppData,
Downloads) HANGS for minutes — it walks the whole NTFS tree through MSYS and
often times out. Use PowerShell directly:

```bash
# Top-level dirs under a base, sorted by size (GB)
powershell.exe -NoProfile -Command "Get-ChildItem -Directory <BASE> -Force -ErrorAction SilentlyContinue | ForEach-Object { \$size = (Get-ChildItem -Path \$_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Name=\$_.Name; GB=[math]::Round(\$size/1GB,2)} } | Sort-Object GB -Descending | Select-Object -First 20 | Format-Table -AutoSize"

# Mixed files+dirs (e.g. Downloads): fold in \$_.Length for files
# Per-subdir of AppData\Local\hermes, or C:\ top-level, same pattern.
```

Useful bases to scan: `$env:USERPROFILE`, `$env:LOCALAPPDATA`,
`C:\ProgramData`, `C:\` root. Escape `$_` as `\$_` inside the bash string.

## 2. "Device or resource busy" on `rm -rf` — the directory-lock hunt

When `rm -rf` fails with `Device or resource busy` and the folder is EMPTY
(sizes already dropped to ~0), a process holds a handle on the directory
itself. Two usual culprits on this host:

1. **A background `du`/scan process** you launched earlier is still walking
   that tree — it keeps CWD/handles inside the folder.
2. **A hermes terminal bash process whose CWD is inside the folder** (from a
   previous `cd` into it). You can see it: `Get-CimInstance Win32_Process`
   shows `bash.exe` command lines containing `cd -- .../<folder>`.

Fix sequence (in order):
```bash
# 1. kill background scan jobs via process tool (action=kill), then:
powershell.exe -NoProfile -Command "Stop-Process -Id <PID1>,<PID2> -Force -ErrorAction SilentlyContinue"
# 2. cd OUT of the folder first:
cd ~
# 3. retry
rm -rf "/c/Users/<user>/AppData/Local/Programs/<App>"
```

Do NOT use `taskkill //F //PID` from git-bash — the `//F` gets mangled by
MSYS path conversion and fails with "Invalid argument/option". Use
`powershell Stop-Process -Id` instead.

## 3. Silent app removal (NSIS/Inno uninstaller)

- Find the uninstaller via registry, not by guessing:
  ```bash
  powershell.exe -NoProfile -Command "Get-ChildItem 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Get-ItemProperty -ErrorAction SilentlyContinue | Where-Object { \$_.DisplayName -like '*<App>*' } | Select-Object DisplayName, UninstallString, InstallLocation | Format-List"
  ```
- Inno Setup: `./unins000.exe /VERYSILENT /NORESTART /SUPPRESSMSGBOXES`.
- **Pitfall:** the uninstaller can exit 0 while the install folder REMAINS
  (3.1GB in our case) and no unins process is left running. Check the
  remaining folder size afterwards; if still large, kill any leftover app
  processes (`Get-Process | Where Name -match '<app>' | Stop-Process -Force`)
  then `rm -rf` the folder manually (section 2 applies).
- After manual removal, clean residue: `~/.<app>` config dir, Start Menu
  shortcuts (`$HOME/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/`),
  and the registry Uninstall entry if it still resolves.
- `cleanmgr /sagerun:NNNNN` does NOTHING unless that sagerun number was
  preconfigured via the GUI — it exits silently without freeing space. Don't
  rely on it headlessly.

## 4. Safe deletion checklist (for user machines)

- Cache dirs safe to purge: `AppData/Local/npm-cache` (npm cache clean
  --force), `AppData/Local/uv` (uv cache clean), pip cache, `Temp`,
  `obsidian-updater`.
- `ProgramData/Microsoft` and global npm (`AppData/Roaming/npm/node_modules`)
  can be huge but often hold running services (codegraph MCP, OmniRoute) —
  check `Get-CimInstance Win32_Process` for node command lines before
  touching global npm.
- Always report per-category sizes and get user confirmation before deleting
  Downloads / project folders; confirm the folder isn't the live copy of
  something referenced from `~/` (e.g. `~/dlv/dlv.py` exists while
  `~/Downloads/dlv` was just a video dump).
