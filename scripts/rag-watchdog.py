#!/usr/bin/env python
"""Watchdog: auto-restart 9Router on port 20128 if it dies."""
import os, socket, subprocess, time, sys

PROJECT_DIR = os.path.expanduser("~")
PID_FILE = os.path.expanduser("~/AppData/Local/hermes/scripts/.rag-pid")
CMD = ["npx", "next", "start", "-p", "20128"]
CHECK_INTERVAL = 15

def is_alive(pid):
    try:
        return subprocess.run(["tasklist", "/fi", f"pid eq {pid}", "/nh"],
                              capture_output=True, timeout=5).stdout.decode().strip() != ""
    except:
        return False

def port_open(port):
    with socket.socket() as s:
        try:
            s.settimeout(2)
            s.connect(("127.0.0.1", port))
            return True
        except:
            return False

def start():
    print(f"[watchdog] Starting 9Router on port 20128...")
    proc = subprocess.Popen(CMD, cwd=PROJECT_DIR, shell=True, 
                            creationflags=subprocess.CREATE_NO_WINDOW)
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    return proc.pid

if __name__ == "__main__":
    pid = None
    if os.path.exists(PID_FILE):
        try:
            pid = int(open(PID_FILE).read().strip())
        except:
            pass
    if pid and is_alive(pid) and port_open(20128):
        print(f"[watchdog] 9Router already running (PID {pid})")
    else:
        pid = start()

    while True:
        time.sleep(CHECK_INTERVAL)
        if not is_alive(pid) or not port_open(20128):
            print(f"[watchdog] 9Router down (PID {pid}), restarting...")
            pid = start()
