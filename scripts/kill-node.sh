#!/bin/bash
# Kill only server on port 3000. Never touch other node.exe.
PID=$(netstat -ano | grep ":3000 " | grep LISTENING | head -1 | awk '{print $5}')
[ -z "$PID" ] && echo "port 3000 not listening — nothing to kill" && exit 0
taskkill /f /pid "$PID" 2>/dev/null
echo "killed port 3000 (PID $PID)"
