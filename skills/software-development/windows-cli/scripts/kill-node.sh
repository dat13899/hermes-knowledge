#!/bin/bash
# Kill all node.exe EXCEPT port 20128 (RAG server / 9Router)
# Uses PID file fallback if netstat temporarily misses the port

PID_FILE="$HOME/AppData/Local/hermes/scripts/.rag-pid"
NET_PID=$(netstat -ano | grep ":20128 " | grep LISTENING | head -1 | awk '{print $5}')

if [ -n "$NET_PID" ]; then
  echo "$NET_PID" > "$PID_FILE"
  PROTECTED_PID="$NET_PID"
elif [ -f "$PID_FILE" ]; then
  PROTECTED_PID=$(cat "$PID_FILE")
  echo "netstat miss — using saved PID $PROTECTED_PID"
else
  taskkill /f /im node.exe 2>/dev/null
  echo "killed all node (no 20128 info)"
  exit 0
fi

for p in $(tasklist /fi "imagename eq node.exe" /fo csv /nh 2>/dev/null | cut -d, -f2 | tr -d '"'); do
  if [ "$p" != "$PROTECTED_PID" ]; then
    taskkill /f /pid "$p" 2>/dev/null
  fi
done
echo "killed node.exe except PID $PROTECTED_PID (port 20128)"
