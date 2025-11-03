#!/usr/bin/env python3
"""
API Service Launcher
Runs the FastAPI application server independently
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from launcher.config import ServiceConfig
import uvicorn

# Configure logging
ServiceConfig.ensure_directories()
logging.basicConfig(
    level=getattr(logging, ServiceConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ServiceConfig.LOG_DIR / "api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start the API service"""
    logger.info("🚀 Starting Snatchbase API Service")
    logger.info(f"📡 Host: {ServiceConfig.API_HOST}")
    logger.info(f"🔌 Port: {ServiceConfig.API_PORT}")
    logger.info(f"🔄 Auto-reload: {ServiceConfig.API_RELOAD}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=ServiceConfig.API_HOST,
            port=ServiceConfig.API_PORT,
            reload=ServiceConfig.API_RELOAD,
            workers=ServiceConfig.API_WORKERS,
            log_level=ServiceConfig.LOG_LEVEL.lower()
        )
    except Exception as e:
        logger.error(f"❌ API service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
