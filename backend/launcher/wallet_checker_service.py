#!/usr/bin/env python3
"""
Wallet Checker Service Launcher
Periodically checks wallet balances for discovered wallets
"""
import sys
import logging
import asyncio
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
        logging.FileHandler(ServiceConfig.LOG_DIR / "wallet_checker.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def run_wallet_checker():
    """Run wallet balance checker periodically"""
    from app.services.wallet_balance_checker import WalletBalanceChecker
    from app.database import SessionLocal
    
    checker = WalletBalanceChecker()
    
    while True:
        try:
            logger.info("🔍 Starting wallet balance check...")
            db = SessionLocal()
            try:
                await checker.check_all_wallets(
                    db=db,
                    batch_size=ServiceConfig.WALLET_CHECK_BATCH_SIZE
                )
                logger.info("✅ Wallet balance check completed")
            finally:
                db.close()
            
            # Wait for next check
            logger.info(f"⏱️  Next check in {ServiceConfig.WALLET_CHECKER_INTERVAL} seconds")
            await asyncio.sleep(ServiceConfig.WALLET_CHECKER_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ Wallet check failed: {e}", exc_info=True)
            await asyncio.sleep(60)  # Wait a minute before retrying


def main():
    """Start the wallet checker service"""
    if not ServiceConfig.WALLET_CHECKER_ENABLED:
        logger.warning("⚠️  Wallet checker is disabled in configuration")
        sys.exit(0)
    
    logger.info("💰 Starting Wallet Checker Service")
    logger.info(f"📦 Batch size: {ServiceConfig.WALLET_CHECK_BATCH_SIZE}")
    logger.info(f"⏱️  Check interval: {ServiceConfig.WALLET_CHECKER_INTERVAL}s")
    
    try:
        asyncio.run(run_wallet_checker())
    except KeyboardInterrupt:
        logger.info("🛑 Wallet checker service stopped")
    except Exception as e:
        logger.error(f"❌ Wallet checker service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
