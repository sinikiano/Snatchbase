#!/usr/bin/env python3
"""
Telegram Scraper Runner
Runs the auto-scraper service as a standalone process
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/scraper.log')
    ]
)

from app.services.telegram_scraper import TelegramScraperService


async def send_bot_notification(message: str):
    """Send notification via Telegram bot"""
    import aiohttp
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    user_id = os.getenv('TELEGRAM_ALLOWED_USER_ID')
    
    if not bot_token or not user_id:
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'Markdown'
            }) as response:
                if response.status != 200:
                    logging.error(f"Failed to send notification: {await response.text()}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")


async def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 Telegram Auto-Scraper Service")
    print("=" * 60)
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Create and start scraper
    scraper = TelegramScraperService(bot_notifier=send_bot_notification)
    
    # Make scraper available to commands module
    from app.services.telegram import commands
    commands.scraper_service = scraper
    
    try:
        await scraper.start()
    except KeyboardInterrupt:
        print("\n⛔ Stopping scraper...")
        await scraper.stop()
    except Exception as e:
        logging.error(f"Scraper error: {e}")
        await send_bot_notification(f"❌ *Scraper Error*\n`{e}`")


if __name__ == "__main__":
    asyncio.run(main())
