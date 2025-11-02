"""
Download existing files from Telegram channel history
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv()

from app.services.telegram_downloader import TelegramDownloader

async def download_history():
    """Download recent files from the channel"""
    downloader = TelegramDownloader()
    
    try:
        # Get phone from environment
        phone = os.getenv('TELEGRAM_PHONE')
        await downloader.client.start(phone=phone)
        print("✅ Connected to Telegram")
        
        # Download last 20 files from the channel
        chat_id = '@RTX5090CLOUD'
        print(f"📥 Downloading recent files from {chat_id}...")
        
        await downloader.download_history(chat_id, limit=20)
        
        print("✅ Download history complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await downloader.client.disconnect()

if __name__ == '__main__':
    asyncio.run(download_history())
