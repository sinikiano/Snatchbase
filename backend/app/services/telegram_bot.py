#!/usr/bin/env python3
"""
Telegram Bot for receiving and processing stealer log files
"""
import os
import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.database import SessionLocal
from app.services.zip_ingestion import ZipIngestionService

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_ID = int(os.getenv('TELEGRAM_ALLOWED_USER_ID', '0'))
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'backend/data/incoming/uploads'))

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        logger.warning(f"Unauthorized access attempt from user {user_id}")
        return
    
    await update.message.reply_text(
        "🤖 *Snatchbase Log Processor Bot*\n\n"
        "Send me ZIP files containing stealer logs and I'll:\n"
        "✅ Save them to the upload directory\n"
        "✅ Process and extract credentials\n"
        "✅ Delete the ZIP files after processing\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/status - Check bot status",
        parse_mode='Markdown'
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    # Count files in upload directory
    zip_files = list(UPLOAD_DIR.glob("*.zip"))
    
    await update.message.reply_text(
        f"✅ *Bot Status*\n\n"
        f"📁 Upload Directory: `{UPLOAD_DIR}`\n"
        f"📦 ZIP Files Pending: {len(zip_files)}\n"
        f"🤖 Status: Active",
        parse_mode='Markdown'
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads"""
    user_id = update.effective_user.id
    
    # Check authorization
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        logger.warning(f"Unauthorized file upload attempt from user {user_id}")
        return
    
    document = update.message.document
    file_name = document.file_name
    
    # Only accept ZIP files
    if not file_name.lower().endswith('.zip'):
        await update.message.reply_text(
            "❌ Only ZIP files are accepted!\n"
            "Please send a ZIP file containing stealer logs."
        )
        return
    
    try:
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"⏳ Downloading `{file_name}`...",
            parse_mode='Markdown'
        )
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_path = UPLOAD_DIR / file_name
        await file.download_to_drive(file_path)
        
        logger.info(f"Downloaded file: {file_name} ({document.file_size} bytes)")
        
        # Update message
        await processing_msg.edit_text(
            f"✅ Downloaded `{file_name}`\n"
            f"⏳ Processing ZIP file...",
            parse_mode='Markdown'
        )
        
        # Process the ZIP file
        db = SessionLocal()
        try:
            ingestion_service = ZipIngestionService(logger=logger)
            result = ingestion_service.process_zip_file(file_path, db)
            
            if result['success']:
                # Delete ZIP file after successful processing
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted processed ZIP file: {file_name}")
                
                # Send success message
                await processing_msg.edit_text(
                    f"✅ *Processing Complete*\n\n"
                    f"📦 File: `{file_name}`\n"
                    f"🖥️ Devices: {result['devices_processed']}\n"
                    f"🔑 Credentials: {result['total_credentials']}\n"
                    f"📄 Files: {result['total_files']}\n"
                    f"🗑️ ZIP file deleted",
                    parse_mode='Markdown'
                )
                
                logger.info(
                    f"Successfully processed {file_name}: "
                    f"{result['devices_processed']} devices, "
                    f"{result['total_credentials']} credentials"
                )
            else:
                await processing_msg.edit_text(
                    f"❌ *Processing Failed*\n\n"
                    f"File: `{file_name}`\n"
                    f"Error: Processing unsuccessful",
                    parse_mode='Markdown'
                )
                logger.error(f"Failed to process {file_name}")
                
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}", exc_info=True)
            await processing_msg.edit_text(
                f"❌ *Error Processing File*\n\n"
                f"File: `{file_name}`\n"
                f"Error: {str(e)}",
                parse_mode='Markdown'
            )
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling document: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error downloading file: {str(e)}"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        return
    
    await update.message.reply_text(
        "📎 Please send me a ZIP file containing stealer logs.\n"
        "Use /status to check the bot status."
    )


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
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("✅ Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
