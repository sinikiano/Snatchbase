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
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Credential, System, Upload
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
    """Handle /start command with comprehensive statistics"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        logger.warning(f"Unauthorized access attempt from user {user_id}")
        return
    
    # Get database statistics
    db = SessionLocal()
    try:
        # Get total counts
        total_credentials = db.query(func.count(Credential.id)).scalar() or 0
        total_systems = db.query(func.count(System.device_id)).scalar() or 0
        total_uploads = db.query(func.count(Upload.upload_id)).scalar() or 0
        
        # Get unique domains count
        unique_domains = db.query(func.count(func.distinct(Credential.domain))).scalar() or 0
        
        # Get top 100 domains
        top_domains = db.query(
            Credential.domain,
            func.count(Credential.id).label('count')
        ).group_by(
            Credential.domain
        ).order_by(
            func.count(Credential.id).desc()
        ).limit(100).all()
        
        # Format top domains list
        top_domains_text = ""
        for i, (domain, count) in enumerate(top_domains[:20], 1):  # Show top 20 in message
            top_domains_text += f"{i}. {domain} - {count:,}\n"
        
        if len(top_domains) > 20:
            top_domains_text += f"\n... and {len(top_domains) - 20} more domains"
        
        # Count pending ZIP files
        zip_files = list(UPLOAD_DIR.glob("*.zip"))
        
        # Build comprehensive message
        message = (
            "🤖 *Snatchbase Log Processor Bot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            "📊 *DATABASE STATISTICS*\n"
            f"🔑 Total Credentials: {total_credentials:,}\n"
            f"🖥️ Total Systems: {total_systems:,}\n"
            f"📦 Total Uploads: {total_uploads:,}\n"
            f"🌐 Unique Domains: {unique_domains:,}\n"
            f"📁 Pending Files: {len(zip_files)}\n\n"
            
            "📈 *TOP 20 DOMAINS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{top_domains_text}\n"
            
            "⚙️ *COMMANDS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "/start - Show statistics\n"
            "/status - Check bot status\n"
            "/top100 - Show top 100 domains\n\n"
            
            "📤 *SEND FILES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Send me ZIP files containing stealer logs and I'll:\n"
            "✅ Process and extract credentials\n"
            "✅ Save to database\n"
            "✅ Delete the ZIP file automatically\n"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
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
    finally:
        db.close()


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


async def top100_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /top100 command to show top 100 domains"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    db = SessionLocal()
    try:
        # Get top 100 domains
        top_domains = db.query(
            Credential.domain,
            func.count(Credential.id).label('count')
        ).group_by(
            Credential.domain
        ).order_by(
            func.count(Credential.id).desc()
        ).limit(100).all()
        
        if not top_domains:
            await update.message.reply_text("No domains found in database.")
            return
        
        # Split into multiple messages (Telegram has message length limit)
        message_parts = []
        current_message = "📊 *TOP 100 DOMAINS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, (domain, count) in enumerate(top_domains, 1):
            line = f"{i}. {domain} - {count:,}\n"
            
            # If message gets too long, start a new one
            if len(current_message + line) > 4000:
                message_parts.append(current_message)
                current_message = f"*TOP 100 DOMAINS (continued)*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{line}"
            else:
                current_message += line
        
        # Add the last part
        if current_message:
            message_parts.append(current_message)
        
        # Send all message parts
        for part in message_parts:
            await update.message.reply_text(part, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error getting top domains: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ Error retrieving top domains: {str(e)}")
    finally:
        db.close()


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
    application.add_handler(CommandHandler("top100", top100_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("✅ Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
