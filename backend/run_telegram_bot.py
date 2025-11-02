#!/usr/bin/env python3
"""
Start the Telegram bot for file uploads
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.telegram_bot import main

if __name__ == "__main__":
    main()
