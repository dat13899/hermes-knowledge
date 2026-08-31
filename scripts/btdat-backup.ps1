$backupDir = "$env:USERPROFILE\.btdat-backup\" + (Get-Date -Format "yyyyMMdd_HHmm")
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Copy-Item "$env:USERPROFILE\service-dashboard\server.js" "$backupDir\"
Copy-Item "$env:USERPROFILE\service-dashboard\services.json" "$backupDir\"
Copy-Item "$env:USERPROFILE\service-dashboard\public\index.html" "$backupDir\"
Copy-Item "$env:USERPROFILE\service-dashboard\public\dashboard.html" "$backupDir\"
Copy-Item "$env:USERPROFILE\.cloudflared\config.yml" "$backupDir\"
Copy-Item "$env:USERPROFILE\.cloudflared\credentials.json" "$backupDir\"

# Keep only last 30 backups
Get-ChildItem "$env:USERPROFILE\.btdat-backup" -Directory | Sort-Object Name -Descending | Select-Object -Skip 30 | Remove-Item -Recurse -Force

Write-Output "Backup OK: $backupDir ($(Get-ChildItem $backupDir | Measure-Object).Count files)"
