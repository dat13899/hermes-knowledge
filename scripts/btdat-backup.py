import os, shutil, glob
from datetime import datetime

home = os.environ['USERPROFILE']
backup_dir = os.path.join(home, '.btdat-backup', datetime.now().strftime('%Y%m%d_%H%M'))
os.makedirs(backup_dir, exist_ok=True)

files = [
    'service-dashboard/server.js',
    'service-dashboard/services.json',
    'service-dashboard/public/index.html',
    'service-dashboard/public/dashboard.html',
    '.cloudflared/config.yml',
    '.cloudflared/credentials.json',
]
for f in files:
    src = os.path.join(home, f)
    if os.path.exists(src):
        shutil.copy2(src, backup_dir)

# keep 30 newest
all_dirs = sorted(glob.glob(os.path.join(home, '.btdat-backup', '*')), reverse=True)
for d in all_dirs[30:]:
    shutil.rmtree(d, ignore_errors=True)

count = len(os.listdir(backup_dir))
print(f'Backup OK: {backup_dir} ({count} files)')
