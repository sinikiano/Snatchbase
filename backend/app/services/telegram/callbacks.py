"""
Callback query handlers for inline buttons
"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Credential, Device, Upload
from .config import logger, ALLOWED_USER_ID, UPLOAD_DIR


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_main":
        # Show main menu by editing the message
        user_id = query.from_user.id
        
        if user_id != ALLOWED_USER_ID:
            await query.edit_message_text("⛔ Unauthorized access denied.")
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
            
            await query.edit_message_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            await query.edit_message_text(
                "🤖 *Snatchbase Log Processor Bot*\n\n"
                "Send me ZIP files or Mega.nz links!",
                parse_mode='Markdown'
            )
        finally:
            db.close()
