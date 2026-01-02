#!/usr/bin/env python3
"""
Telegram Scraper Service Launcher
Runs the Telegram group/channel scraper as a standalone service
"""
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from launcher.config import ServiceConfig

# Configure logging
ServiceConfig.ensure_directories()
logging.basicConfig(
    level=getattr(logging, ServiceConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ServiceConfig.LOG_DIR / "telegram_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for Telegram scraper service"""
    logger.info("=" * 60)
    logger.info("  Snatchbase Telegram Scraper Service")
    logger.info("=" * 60)
    
    try:
        from app.services.telegram_downloader import TelegramDownloader
    except ImportError as e:
        logger.error(f"Failed to import TelegramDownloader: {e}")
        logger.error("Make sure telethon is installed: pip install telethon")
        return
    
    downloader = TelegramDownloader()
    
    if not downloader.is_configured():
        logger.error("Telegram scraper not configured!")
        logger.info("")
        logger.info("To configure, set these environment variables in .env:")
        logger.info("  TELEGRAM_API_ID=your_api_id")
        logger.info("  TELEGRAM_API_HASH=your_api_hash")
        logger.info("  TELEGRAM_PHONE=+1234567890")
        logger.info("  TELEGRAM_CHAT_IDS=@channel1,@group2,-1001234567890")
        logger.info("")
        logger.info("Get API credentials from: https://my.telegram.org")
        return
    
    try:
        await downloader.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await downloader.stop()
    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info=True)
        await downloader.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped")
