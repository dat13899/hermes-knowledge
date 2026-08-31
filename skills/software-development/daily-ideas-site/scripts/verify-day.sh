#!/bin/bash
# Verify 1 ngày trên daily.btdat.io.vn — dùng trước khi báo "xong" cho cron Daily Idea.
# Usage: bash verify-day.sh <MMDDYYYY>   (vd: bash verify-day.sh 08082026)
set -u
DAY="${1:?thiếu mã ngày MMDDYYYY}"
PORT="${PORT:-3050}"
BASE="http://localhost:${PORT}"

# Chromium headless shell — glob version mới nhất (Playwright update đổi version dir)
SHELL_DIR="$(ls -d "$LOCALAPPDATA"/ms-playwright/chromium_headless_shell-* 2>/dev/null | sort -V | tail -1)"
if [ -z "$SHELL_DIR" ]; then
  echo "❌ Không tìm thấy chromium_headless_shell trong $LOCALAPPDATA/ms-playwright"
  exit 2
fi
SHELL="$(find "$SHELL_DIR" -maxdepth 3 -iname '*headless*.exe' 2>/dev/null | head -1)"
[ -z "$SHELL" ] && SHELL="$(find "$SHELL_DIR" -maxdepth 3 -iname 'chrome.exe' 2>/dev/null | head -1)"
echo "→ shell: $SHELL"
echo "→ ngày:  $DAY"
echo

FAIL=0

# 1) HTTP status
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$BASE/$DAY/")
echo "1) HTTP GET /$DAY/ → $CODE"
[ "$CODE" = "200" ] || { echo "   ❌ không phải 200"; FAIL=1; }

# 2) DOM render + JS errors
DUMP=$("$SHELL" --headless --disable-gpu --no-sandbox --virtual-time-budget=2500 \
  --enable-logging=stderr --v=0 "$BASE/$DAY/" 2>&1 || true)
JS_ERRS=$(printf '%s\n' "$DUMP" | grep -iE 'Uncaught|TypeError|ReferenceError|SyntaxError|CONSOLE.*error' | head -5)
if [ -n "$JS_ERRS" ]; then
  echo "2) JS errors ❌:"
  printf '%s\n' "$JS_ERRS" | head -5
  FAIL=1
else
  echo "2) JS errors → sạch ✅ (DOM dump $(printf '%s' "$DUMP" | wc -c) bytes)"
fi

# 3) Screenshots mobile + desktop
SHOTS="${SHOTS_DIR:-$PWD/verify-shots}"
mkdir -p "$SHOTS"
for spec in "375x667:mobile" "1280x800:desktop"; do
  SIZE="${spec%%:*}"; NAME="${spec##*:}"
  OUT="$SHOTS/$DAY-$NAME.png"
  "$SHELL" --headless --disable-gpu --no-sandbox --window-size="$SIZE" --hide-scrollbars \
    --screenshot="$OUT" --virtual-time-budget=2000 "$BASE/$DAY/" >/dev/null 2>&1
  [ -f "$OUT" ] && echo "3) screenshot $NAME → $OUT ($(stat -c%s "$OUT") bytes)" || { echo "   ❌ $NAME fail"; FAIL=1; }
done

echo
[ "$FAIL" = "0" ] && echo "✅ VERIFY PASS — xem 2 screenshot bằng vision_analyze trước khi báo xong" || echo "❌ VERIFY FAIL"
exit $FAIL
