"""
Configuration and constants for Telegram bot
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_ID = int(os.getenv('TELEGRAM_ALLOWED_USER_ID', '0'))
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'data/incoming/uploads'))

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
