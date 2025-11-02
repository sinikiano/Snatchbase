# Telegram Auto-Download Setup

This guide explains how to set up automatic file downloading from Telegram groups/channels.

## Prerequisites

1. A Telegram account
2. Access to the Telegram groups/channels you want to monitor

## Setup Steps

### 1. Get Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application:
   - App title: `Snatchbase`
   - Short name: `snatchbase`
   - Platform: `Other`
5. You will receive:
   - `api_id` (numeric)
   - `api_hash` (alphanumeric string)

### 2. Configure Environment Variables

Edit `backend/.env` and update these values:

```bash
TELEGRAM_API_ID=12345678  # Your API ID from step 1
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890  # Your API hash from step 1
TELEGRAM_PHONE=+1234567890  # Your phone number with country code
TELEGRAM_SESSION_NAME=snatchbase_session  # Session file name (can leave as is)
TELEGRAM_CHAT_IDS=@channel_username,@group_username  # Comma-separated list
```

#### Finding Chat IDs/Usernames:

- **Public channels**: Use the username (e.g., `@channelname`)
- **Public groups**: Use the username (e.g., `@groupname`)
- **Private groups**: Use the numeric chat ID (get it from a bot like @userinfobot)
- **Leave empty** to monitor ALL chats (not recommended)

### 3. First-Time Authentication

The first time you run the service, you'll need to authenticate:

```bash
cd backend
source venv/bin/activate
python app/services/telegram_downloader.py
```

You will be prompted to:
1. Enter your phone number (if not in .env)
2. Enter the code sent to your Telegram app
3. Enter your 2FA password (if enabled)

This creates a session file that will be reused for future runs.

### 4. Running the Service

#### Option A: Run Telegram downloader only
```bash
cd backend
source venv/bin/activate
python app/services/telegram_downloader.py
```

#### Option B: Run both Telegram downloader AND auto-ingestion
```bash
cd backend
source venv/bin/activate
python app/services/run_services.py
```

#### Option C: Run as background service
```bash
cd backend
source venv/bin/activate
nohup python app/services/run_services.py > logs/telegram.log 2>&1 &
```

## Features

- ✅ Automatically downloads files from specified Telegram chats
- ✅ Supports: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tar.gz`
- ✅ Skips duplicate files
- ✅ Shows download progress
- ✅ Integrates with existing auto-ingestion pipeline
- ✅ Works with channels and groups
- ✅ Monitors new messages in real-time

## File Flow

```
Telegram Group/Channel
    ↓
Telegram Downloader Service
    ↓
backend/data/incoming/uploads/
    ↓
Auto-Ingestion Service (file_watcher.py)
    ↓
ZIP Processor
    ↓
Database
```

## Troubleshooting

### "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"
- Make sure you've added the credentials to `.env`
- Make sure the `.env` file is in the `backend/` directory

### "Could not find the input entity for..."
- The chat ID/username is incorrect
- You're not a member of that group/channel
- For private groups, use numeric chat ID instead of username

### "Phone number is not registered"
- Make sure the phone number includes country code (e.g., `+1234567890`)
- The Telegram account must already exist

### Session issues
- Delete the session file: `rm snatchbase_session.session*`
- Re-run and authenticate again

## Advanced Usage

### Download History

To download recent files from a chat (useful for initial setup):

```python
from app.services.telegram_downloader import TelegramDownloader
import asyncio

async def download_history():
    downloader = TelegramDownloader()
    await downloader.client.start(phone=PHONE)
    await downloader.download_history('@channelname', limit=50)  # Last 50 files
    await downloader.client.disconnect()

asyncio.run(download_history())
```

### Monitor Multiple Chats

Add multiple chat IDs/usernames to `TELEGRAM_CHAT_IDS`:

```bash
TELEGRAM_CHAT_IDS=@channel1,@channel2,@group1,-1001234567890
```

### Custom File Extensions

Edit `telegram_downloader.py` and modify the `ALLOWED_EXTENSIONS` list:

```python
ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz', '.custom']
```

## Security Notes

- ⚠️ Keep your `api_id` and `api_hash` secret
- ⚠️ Session files contain authentication tokens - keep them secure
- ⚠️ Be careful with `TELEGRAM_CHAT_IDS` - leaving it empty monitors ALL chats
- ⚠️ Only download files from trusted sources

## Resources

- [Telegram API Documentation](https://core.telegram.org/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Get API Credentials](https://my.telegram.org)
