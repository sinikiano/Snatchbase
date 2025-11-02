# Telegram Bot Integration Guide

## Overview
The Telegram bot allows you to upload stealer log ZIP files directly via Telegram. Files are automatically processed and the ZIP is deleted after successful ingestion.

## Bot Information
- **Bot Username**: `@ermachook_bot`
- **Authorized User ID**: `839078943`
- **Bot Token**: Configured in `.env`

## Features
✅ Upload ZIP files via Telegram
✅ Automatic processing and credential extraction
✅ Auto-deletion of ZIP files after processing
✅ Real-time status updates
✅ Secure (only authorized user can use the bot)

## Commands

### `/start`
Shows welcome message and available commands

### `/status`
Displays:
- Upload directory path
- Number of pending ZIP files
- Bot status

## Usage

1. **Start the bot** (included in `start_snatchbase.sh`)
   ```bash
   cd backend
   source venv/bin/activate
   python3 run_telegram_bot.py
   ```

2. **Send files to @ermachook_bot**
   - Open Telegram
   - Search for `@ermachook_bot`
   - Send `/start` to see available commands
   - Drop any ZIP file containing stealer logs
   
3. **Bot will automatically:**
   - Download the ZIP file to `backend/data/incoming/uploads/`
   - Process the file and extract credentials
   - Save data to database
   - Delete the ZIP file
   - Send you a status update with:
     - Number of devices processed
     - Number of credentials extracted
     - Number of files processed

## Configuration

The bot is configured via environment variables in `backend/.env`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8385294414:AAFQqDbiqrZ5TZZ7Q8fKURpeLITd-CHNmH0
TELEGRAM_ALLOWED_USER_ID=839078943
UPLOAD_DIR=data/incoming/uploads
```

## Security

- Only the user with ID `839078943` can interact with the bot
- Unauthorized users will receive "⛔ Unauthorized access denied" message
- All unauthorized attempts are logged

## Example Workflow

1. User sends ZIP file to `@ermachook_bot`
2. Bot responds: "⏳ Downloading `logs.zip`..."
3. Bot downloads and starts processing
4. Bot updates: "⏳ Processing ZIP file..."
5. Bot completes and responds:
   ```
   ✅ Processing Complete
   
   📦 File: logs.zip
   🖥️ Devices: 5
   🔑 Credentials: 150
   📄 Files: 45
   🗑️ ZIP file deleted
   ```

## Logging

Bot logs are written to `/tmp/snatchbase-telegram-bot.log`

View logs:
```bash
tail -f /tmp/snatchbase-telegram-bot.log
```

## Troubleshooting

### Bot not responding
1. Check if bot is running: `ps aux | grep telegram_bot`
2. Check logs: `tail -f /tmp/snatchbase-telegram-bot.log`
3. Verify environment variables are set

### "Unauthorized access" error
- Verify your Telegram user ID matches `TELEGRAM_ALLOWED_USER_ID`
- Get your user ID by messaging `@userinfobot` on Telegram

### File not processing
- Check backend logs: `tail -f /tmp/snatchbase-backend.log`
- Verify ZIP file format is correct
- Check upload directory permissions

## Testing

Test the bot locally:
```bash
cd backend
source venv/bin/activate
export TELEGRAM_BOT_TOKEN="8385294414:AAFQqDbiqrZ5TZZ7Q8fKURpeLITd-CHNmH0"
export TELEGRAM_ALLOWED_USER_ID="839078943"
export UPLOAD_DIR="data/incoming/uploads"
python3 run_telegram_bot.py
```

Then send a test ZIP file via Telegram.

## Integration with Snatchbase

The bot is fully integrated with the Snatchbase platform:
- Uses the same database as the web interface
- Processes files using the same ingestion service
- Files appear immediately in the web interface after processing
- All analytics and search features work with bot-uploaded data
