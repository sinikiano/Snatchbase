#!/usr/bin/env python3
"""
Telegram Bot for receiving and processing stealer log files
This is the main entry point - actual implementation is in telegram/ package
"""
from app.services.telegram.bot import main

if __name__ == "__main__":
    main()
