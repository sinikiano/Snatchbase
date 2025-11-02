#!/usr/bin/env python3
"""
Telegram Bot Main Entry Point
Modular architecture for better maintainability
"""
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from .config import logger, TELEGRAM_BOT_TOKEN, ALLOWED_USER_ID, UPLOAD_DIR
from .commands import start_command, status_command, top100_command
from .extractdomains import extractdomains_command
from .handlers import handle_document, handle_message
from .callbacks import button_callback
from .search import search_command
from .analytics import stats_command, recent_command
from .wallet_commands import wallets_command, checkwallets_command, highvalue_command, checkbalances_command


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    if not ALLOWED_USER_ID:
        logger.error("TELEGRAM_ALLOWED_USER_ID environment variable not set!")
        return
    
    logger.info(f"Starting Telegram bot...")
    logger.info(f"Authorized user ID: {ALLOWED_USER_ID}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("recent", recent_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("wallets", wallets_command))
    application.add_handler(CommandHandler("checkwallets", checkwallets_command))
    application.add_handler(CommandHandler("checkbalances", checkbalances_command))
    application.add_handler(CommandHandler("highvalue", highvalue_command))
    application.add_handler(CommandHandler("top100", top100_command))
    application.add_handler(CommandHandler("topdomains", top100_command))  # Alias for top100
    application.add_handler(CommandHandler("extractdomains", extractdomains_command))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("✅ Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
