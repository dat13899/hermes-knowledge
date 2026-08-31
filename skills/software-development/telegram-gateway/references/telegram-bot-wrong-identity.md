# Reproduction: Telegram Bot Not Responding

## Scenario

User messages Telegram bot @dat1389_cuem_bot — no response.

## Investigation Trace

1. Check gateway process:
   ```
   hermes gateway status
   PS C:\Users\datel> gateway status
   ✓ Scheduled Task registered: Hermes_Gateway
   Status: Ready
   ✓ Gateway process running (PID: 29948)
   ```

2. Check gateway logs for errors:
   ```
   grep -i 'telegram.*error\|fail' ~/AppData/Local/hermes/logs/gateway.log | tail -20
   ```
   No errors found. Bot connected in polling mode.

3. Check which bot is actually configured (crucial step):
   ```python
   # Read TELEGRAM_BOT_TOKEN from ~/AppData/Local/hermes/.env
   url = f'https://api.telegram.org/bot{TOKEN}/getMe'
   # Response: {"username": "hermes_fnkyjzxant4plhrb_bot", "id": 8877924103}
   ```
   **Username = @hermes_fnkyjzxant4plhrb_bot, NOT @dat1389_cuem_bot!**

4. Verify: user messaging @dat1389_cuem_bot, Hermes running @hermes_fnkyjzxant4plhrb_bot.
   Cause: user created new bot but didn't update TELEGRAM_BOT_TOKEN.

## Root Cause

User created a new Telegram bot @dat1389_cuem_bot via @BotFather but did not update the `TELEGRAM_BOT_TOKEN` in `~/AppData/Local/hermes/.env`. Hermes was still using the old bot's token (8877924103:... → @hermes_fnkyjzxant4plhrb_bot).

## Fix

1. Get new bot's token from @BotFather → /mybots → @dat1389_cuem_bot → API Token
2. Update `.env`:
   ```
   TELEGRAM_BOT_TOKEN=<new_token>
   ```
3. Restart gateway:
   ```
   hermes gateway restart
   ```
4. Verify: re-run `getMe` → returns @dat1389_cuem_bot

## Key Details

- **Config location confusion**: On Windows, Hermes lives at `~/AppData/Local/hermes/` — that's where the real `.env` is. `~/.hermes/.env` is a secondary file that may have stale/partial config (e.g., only ALLOWED_USERS, no BOT_TOKEN).
- **Secret redaction**: `cat .env` shows `8877924103:***` — the real token is hidden by Hermes redaction. Use Python to read the file programmatically.
- **ALLOWED_USERS mismatch**: The `~/.hermes/.env` had `TELEGRAM_ALLOWED_USERS=1088711997,8934984983` (2 users), but `~/AppData/Local/hermes/.env` had only `1088711997` (1 user). Always check the REAL .env.
