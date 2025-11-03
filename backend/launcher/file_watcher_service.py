#!/usr/bin/env python3
"""
File Watcher Service Launcher
Monitors incoming directory for ZIP files and auto-ingests them
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
        logging.FileHandler(ServiceConfig.LOG_DIR / "file_watcher.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start the file watcher service"""
    if not ServiceConfig.FILE_WATCHER_ENABLED:
        logger.warning("⚠️  File watcher is disabled in configuration")
        sys.exit(0)
    
    logger.info("📂 Starting File Watcher Service")
    logger.info(f"📁 Watch directory: {ServiceConfig.INCOMING_DIR.absolute()}")
    logger.info(f"⏱️  Check interval: {ServiceConfig.FILE_WATCHER_INTERVAL}s")
    
    try:
        from app.services.file_watcher import FileWatcherService
        
        watcher = FileWatcherService(
            watch_dir=ServiceConfig.INCOMING_DIR,
            logger=logger
        )
        watcher.start()
        
        # Keep running
        import signal
        import time
        
        def signal_handler(sig, frame):
            logger.info("🛑 Stopping file watcher...")
            watcher.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("✅ File watcher service started successfully")
        logger.info("💡 Drop ZIP files into the watch directory for automatic processing")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ File watcher service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
