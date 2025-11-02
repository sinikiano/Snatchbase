"""
Integrated Service Runner
Runs both Telegram downloader and auto-ingestion services
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.telegram_downloader import TelegramDownloader
from app.services.auto_ingest import AutoIngestService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_services():
    """Run both services concurrently"""
    logger.info("🚀 Starting Snatchbase services...")
    
    # Check if Telegram is configured
    telegram_configured = all([
        os.getenv('TELEGRAM_API_ID'),
        os.getenv('TELEGRAM_API_HASH'),
        os.getenv('TELEGRAM_PHONE')
    ])
    
    tasks = []
    
    # Start auto-ingestion service
    logger.info("📂 Starting auto-ingestion service...")
    auto_ingest = AutoIngestService()
    auto_ingest_task = asyncio.create_task(
        asyncio.to_thread(auto_ingest.start)
    )
    tasks.append(auto_ingest_task)
    
    # Start Telegram downloader if configured
    if telegram_configured:
        logger.info("📱 Starting Telegram downloader...")
        telegram_downloader = TelegramDownloader()
        telegram_task = asyncio.create_task(telegram_downloader.start())
        tasks.append(telegram_task)
    else:
        logger.warning("⚠️  Telegram not configured. Skipping Telegram downloader.")
        logger.info("   To enable: Set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE in .env")
    
    # Wait for all tasks
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        for task in tasks:
            task.cancel()


if __name__ == '__main__':
    try:
        asyncio.run(run_services())
    except KeyboardInterrupt:
        logger.info("Services stopped")
