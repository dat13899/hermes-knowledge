---
name: telegram-gateway
description: "Configure, verify, and troubleshoot Telegram bot connectivity in Hermes gateway. Covers token setup, bot identity verification, gateway restart workflow, and common failure modes."
category: software-development
version: 1.0.0
author: Cu em
platforms: [windows, linux, macos]
---

# Telegram Gateway

Hermes connects to Telegram via the gateway platform adapter. This skill covers setting up a Telegram bot, verifying it's connected properly, and debugging when messages aren't getting through.

## Setup

1. Create bot via @BotFather on Telegram → `/newbot` → copy API token
2. Set token in the Hermes `.env`:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=1088711997             # comma-separated Telegram user IDs
TELEGRAM_HOME_CHANNEL=1088711997              # default chat for cron delivery
```

3. Restart gateway: `hermes gateway restart`

## Verify Bot Connection

### Check gateway status
```bash
hermes gateway status
# → shows "Gateway process running (PID: ...)"
# → "Scheduled Task registered: Hermes_Gateway"
```

### Check gateway logs
```bash
grep -i 'telegram' ~/AppData/Local/hermes/logs/gateway.log | tail -10
# → "[Telegram] Connected to Telegram (polling mode)"
# → "✓ telegram connected"
```

### Verify bot identity (which bot is Hermes talking to?)
```python
import urllib.request, json
# Read token from .env manually, then:
url = f'https://api.telegram.org/bot{TOKEN}/getMe'
resp = json.loads(urllib.request.urlopen(url).read())
print(f"Username: @{resp['result']['username']}")
print(f"ID: {resp['result']['id']}")
```

Compare the returned username with the bot the user is messaging. If they differ, the wrong token is set.

## Debugging: Bot Not Responding

Follow this checklist:

### 1. Gateway Process Alive?
```bash
hermes gateway status
```
If no process, start it: `hermes gateway start`

### 2. Telegram Connection in Logs?
```bash
grep -i 'telegram.*connected' ~/AppData/Local/hermes/logs/gateway.log 
```
Look for `"Connected to Telegram (polling mode)"`. If see `"attempt N/8"` repeatedly, network issue.

### 3. Correct Bot?
Call `getMe` API (see Verify Bot Identity above). If username doesn't match @YourBot, the `.env` has the wrong token.

### 4. ALLOWED_USERS Includes You?
Check `.env`:
```
TELEGRAM_ALLOWED_USERS=1088711997,8934984983
```
Your Telegram user ID must be in this list. Get your ID from @userinfobot on Telegram.

### 5. Wrong .env File?
Hermes has **two** `.env` locations on Windows:
- `~/.hermes/.env` — may have stale/partial config
- `~/AppData/Local/hermes/.env` — the real one used by gateway

Check both. The real `TELEGRAM_BOT_TOKEN` must be in the second one.

### 6. Restart After Config Change?
Any `.env` change → `hermes gateway restart`. Verify with logs after restart.

## Common Pitfalls

- **Messaging old bot**: If you created a new bot via @BotFather but didn't update `TELEGRAM_BOT_TOKEN`, Hermes still talks to the old one. `/getMe` confirms which.
- **Multiple `.env` files**: On Windows, `~/.hermes/.env` exists alongside `~/AppData/Local/hermes/.env`. Editing the wrong one does nothing. `hermes config env-path` shows the active path.
- **ALLOWED_USERS mismatch**: Gateway silently drops messages from non-allowed users — no error in logs, no response sent.
- **Token redacted in terminal output**: `cat` of `.env` shows `TELEGRAM_BOT_TOKEN=8877924103:***` due to Hermes secret redaction. Use `python -c` to read the file safely instead.
- **Gateway restart required**: Config/env changes only take effect after `hermes gateway restart`. No automatic reload.
