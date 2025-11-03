#!/usr/bin/env python3
"""
Telegram Bot Service Launcher
Runs the Telegram bot independently
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from launcher.config import ServiceConfig

# Configure logging
ServiceConfig.ensure_directories()
logging.basicConfig(
    level=getattr(logging, ServiceConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ServiceConfig.LOG_DIR / "telegram_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot service"""
    if not ServiceConfig.TELEGRAM_ENABLED:
        logger.warning("⚠️  Telegram bot is disabled in configuration")
        sys.exit(0)
    
    if not ServiceConfig.is_telegram_configured():
        logger.error("❌ Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID")
        sys.exit(1)
    
    logger.info("🤖 Starting Telegram Bot Service")
    logger.info(f"👤 Allowed User ID: {ServiceConfig.TELEGRAM_ALLOWED_USER_ID}")
    
    try:
        from app.services.telegram.bot import main as bot_main
        bot_main()
    except Exception as e:
        logger.error(f"❌ Telegram bot service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
