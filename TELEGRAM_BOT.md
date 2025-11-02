# Telegram Bot - Usage Guide

## Overview
The Snatchbase Telegram Bot (@ermachook_bot) allows you to upload stealer logs directly to your Snatchbase instance for automatic processing.

## Features

### 1. Direct File Upload
- Send ZIP files containing stealer logs directly through Telegram
- Files are automatically saved to `backend/data/incoming/uploads/`
- Auto-processing extracts credentials and system information
- ZIP files are automatically deleted after successful processing

### 2. Mega.nz Link Download ⭐ NEW
- Paste Mega.nz download links directly in the chat
- Bot automatically detects and downloads files
- Downloaded files are processed automatically
- Supports nested ZIP files (ZIP containing multiple ZIPs)

### 3. Statistics and Monitoring
- View total credentials, systems, and uploads
- See top domains with credential counts
- Monitor pending files in upload queue
- Check bot status and health

## Commands

### `/start`
Shows comprehensive statistics including:
- Total credentials in database
- Total systems processed
- Total file uploads
- Unique domains count
- Top 20 domains with counts
- Available commands

### `/status`
Quick bot health check showing:
- Bot operational status
- Upload directory location

### `/top100`
View top 100 domains sorted by credential count

### `/extractdomains`
Extract credentials from 200+ targeted domains including:
- Social media (Facebook, Instagram, Twitter, TikTok, etc.)
- Email services (Gmail, Outlook, Yahoo, etc.)
- Gaming platforms (Steam, Epic Games, Battle.net, etc.)
- Financial services (PayPal, Coinbase, Binance, etc.)
- Developer platforms (GitHub, GitLab, AWS, etc.)

Results are exported as a CSV file and sent back to you.

## Usage Examples

### Example 1: Upload ZIP File
1. Open Telegram and find @ermachook_bot
2. Drag and drop or send a ZIP file containing stealer logs
3. Bot will confirm receipt and processing
4. File is automatically processed and deleted

### Example 2: Download from Mega.nz
1. Copy a Mega.nz download link (e.g., `https://mega.nz/file/xxxxx#xxxxx`)
2. Paste the link in chat with @ermachook_bot
3. Bot detects the link and starts downloading
4. Progress updates are sent during download
5. Downloaded file is automatically processed

### Example 3: Check Statistics
1. Send `/start` to see current database statistics
2. View top 20 domains with credential counts
3. Check pending files in upload queue

### Example 4: Extract Specific Domains
1. Send `/extractdomains` command
2. Bot extracts credentials from 200+ target domains
3. Receive CSV file with extracted data

## Technical Details

### Supported File Types
- ZIP archives (`.zip`)
- Nested ZIP files (ZIP containing ZIPs)
- Password-protected archives with common passwords

### Password File Detection
The bot automatically detects password files containing:
- Filenames: `passwords.txt`, `logins.txt`, `creds.txt`, `accounts.txt`
- Keywords: `password`, `pass`, `login`, `cred`, `account` in filename

### Nested ZIP Processing
- Automatically extracts and processes nested ZIP files
- No depth limit - processes all levels of nesting
- Temp files are cleaned up after processing

### Auto-Processing
- File watcher monitors upload directory every 10 seconds
- New files trigger automatic ingestion pipeline
- Credentials extracted and saved to PostgreSQL database
- ZIP files deleted after successful processing

### Mega.nz Downloads
- Uses system `megatools` package for downloads
- Downloads directly to upload directory
- Original filename is preserved
- Progress updates sent to user
- Error handling for failed downloads

## Security

### Authorization
- Bot only responds to authorized user ID: `839078943`
- All other users receive "Unauthorized access denied" message

### Data Privacy
- Files are processed locally on your server
- No data sent to third parties
- ZIP files deleted after processing
- Database secured with PostgreSQL authentication

## Environment Variables

Required variables in `backend/.env`:
```bash
TELEGRAM_BOT_TOKEN=8385294414:AAFQqDbiqrZ5TZZ7Q8fKURpeLITd-CHNmH0
TELEGRAM_ALLOWED_USER_ID=839078943
```

## Installation Requirements

### Python Packages
```bash
pip install python-telegram-bot>=21.0
```

### System Packages
```bash
sudo apt install megatools
```

## Running the Bot

### Manual Start
```bash
cd /workspaces/Snatchbase/backend
source venv/bin/activate
python -m app.services.telegram_bot
```

### Background Start
```bash
cd /workspaces/Snatchbase/backend
source venv/bin/activate
nohup python -m app.services.telegram_bot > telegram_bot.log 2>&1 &
```

### Using Startup Script
```bash
./start_snatchbase.sh
```

The startup script automatically starts:
- PostgreSQL database
- FastAPI backend server
- Vite frontend server
- Telegram bot

## Monitoring

### Check Bot Status
```bash
# View real-time logs
tail -f /workspaces/Snatchbase/backend/telegram_bot.log

# Check if bot is running
ps aux | grep telegram_bot | grep -v grep

# Use health check script
./check_health.sh
```

### Common Issues

**Multiple bot instances running:**
```bash
# Kill all instances
pkill -f "python.*telegram_bot.py"

# Start fresh instance
cd backend && source venv/bin/activate
nohup python -m app.services.telegram_bot > telegram_bot.log 2>&1 &
```

**Mega.nz download fails:**
- Check internet connection
- Verify `megatools` is installed: `which megadl`
- Check link is valid and public
- Review logs: `tail -f backend/telegram_bot.log`

**Files not processing:**
- Check auto-ingest service is running
- Verify upload directory permissions
- Check database connection
- Review backend logs: `tail -f backend/backend.log`

## Support

For issues or questions:
1. Check logs: `tail -f backend/telegram_bot.log`
2. Run health check: `./check_health.sh`
3. Review README.md for general setup

## Changelog

### Version 2.0 (2025-11-02)
- ✨ Added Mega.nz link parser for automatic downloads
- ✨ Updated /start command to mention Mega.nz support
- 🐛 Fixed message handler to detect mega.nz URLs
- 📝 Added download progress updates
- 🔧 Improved error handling for failed downloads

### Version 1.1 (2025-11-01)
- ✨ Added duplicate credential detection
- ✨ Implemented /extractdomains command
- 🐛 Fixed nested ZIP processing
- 📝 Extended password file detection patterns

### Version 1.0 (2025-11-01)
- 🎉 Initial release
- ✨ File upload support
- ✨ Auto-processing and ZIP deletion
- ✨ Statistics in /start command
- ✨ /top100 domains command
