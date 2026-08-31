# Port → Process → CommandLine audit on Windows (git-bash)

Use when the user asks "what's running on port X / what services are up" or you
need the command lines of listening processes. `wmic` is deprecated/quiet on
modern Windows; `tasklist` shows names but no command lines.

## Working recipe (write the .ps1 via write_file tool)

`tasklist` maps PID → image name (parse with `tasklist > /tmp/tl.txt`, then grep
the PID column). But for command lines / working dirs you need PowerShell:

```powershell
$conn = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conn) {
  $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
  if ($p) {
    $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$($c.OwningProcess)" -ErrorAction SilentlyContinue).CommandLine
    if (-not $cl) { $cl = '' }
    if ($cl.Length -gt 180) { $cl = $cl.Substring(0,180) + '...' }
    Write-Output ("{0,-8} {1,-10} {2,-12} {3}" -f $c.LocalAddress, $c.LocalPort, $p.ProcessName, $cl)
  }
}
```

Run from git-bash:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\datel\tmp\ports.ps1"
```

## Key facts learned

- `wmic process where "ProcessId=N" get CommandLine` returned EMPTY for node /
  cloudflared on this machine — do not rely on it. `Get-CimInstance
  Win32_Process` via a .ps1 file works.
- Write the script with the `write_file` TOOL, never a heredoc — heredocs in
  git-bash swallow backslashes in Windows paths (same rule as playwright
  scripts; see main SKILL.md).
- `tasklist //FI "PID eq N"` under git-bash: `//` gets mangled to a path; the
  CSV output `cut -d',' -f1` works, but writing the full tasklist to a file and
  grepping is simpler.
- Getting a process CWD: `(Get-Process -Id N).MainModule.FileName` gives the
  EXE path, NOT cwd. To distinguish two `server.js` node processes (e.g.
  port 3000 vs 3050), cross-reference the port (netstat → PID) with known
  project `server.js` PORT constants — grep `const PORT` in each project dir.
- Filter out system noise: svchost/services/lsass/wininit ports (49xxx range,
  135, 445, 3389, 5357) are OS, not user services.

## Example output

```
::       3050       node         "C:\Program Files\nodejs\node.exe" server.js
0.0.0.0  20128      node         node --max-old-space-size=4096 ...omniroute\dist\server-ws.mjs
127.0.0.1 20241     cloudflared  ...\cloudflared.exe tunnel --url http://127.0.0.1:20128
```

Distinguishes the named tunnel (config.yml) from the quick tunnel — memory note:
never kill the OmniRoute quick tunnel; identify cloudflared by CommandLine since
PID changes each boot.
