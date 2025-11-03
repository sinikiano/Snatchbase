"""
Service Configuration
Central configuration for all Snatchbase services
"""
import os
from pathlib import Path

class ServiceConfig:
    """Base configuration for all services"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    INCOMING_DIR = DATA_DIR / "incoming" / "uploads"
    PROCESSED_DIR = DATA_DIR / "processed"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://snatchbase:snatchbase@localhost/snatchbase")
    
    # API Service
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
    API_WORKERS = int(os.getenv("API_WORKERS", "1"))
    
    # Telegram Bot
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    
    # File Watcher Service
    FILE_WATCHER_ENABLED = os.getenv("FILE_WATCHER_ENABLED", "true").lower() == "true"
    FILE_WATCHER_INTERVAL = int(os.getenv("FILE_WATCHER_INTERVAL", "5"))  # seconds
    
    # Wallet Balance Checker
    WALLET_CHECKER_ENABLED = os.getenv("WALLET_CHECKER_ENABLED", "false").lower() == "true"
    WALLET_CHECKER_INTERVAL = int(os.getenv("WALLET_CHECKER_INTERVAL", "3600"))  # seconds
    WALLET_CHECK_BATCH_SIZE = int(os.getenv("WALLET_CHECK_BATCH_SIZE", "100"))
    
    # Health Check
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # seconds
    SERVICE_RESTART_DELAY = int(os.getenv("SERVICE_RESTART_DELAY", "5"))  # seconds
    MAX_RESTART_ATTEMPTS = int(os.getenv("MAX_RESTART_ATTEMPTS", "3"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = BASE_DIR / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.INCOMING_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_telegram_configured(cls) -> bool:
        """Check if Telegram bot is properly configured"""
        return bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_ALLOWED_USER_ID)
