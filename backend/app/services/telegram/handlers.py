"""
File upload and message handlers for Telegram bot
"""
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.services.zip_ingestion import ZipIngestionService
from app.services.password_archive_manager import password_manager
from .config import logger, ALLOWED_USER_ID, UPLOAD_DIR
from .utils import get_back_button
from .mega_download import download_mega_file


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
    
    # Accept ZIP and RAR files
    if not (file_name.lower().endswith('.zip') or file_name.lower().endswith('.rar')):
        await update.message.reply_text(
            "❌ Only ZIP and RAR files are accepted!\n"
            "Please send a ZIP/RAR file containing stealer logs.",
            reply_markup=get_back_button()
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
        
        # Check if file is password protected
        if password_manager.is_password_protected(file_path):
            await processing_msg.edit_text(
                f"🔐 `{file_name}` is password protected!\n\n"
                f"⏳ Trying common passwords...",
                parse_mode='Markdown'
            )
            
            # Try common passwords
            password = password_manager.try_common_passwords(file_path)
            
            if password:
                await processing_msg.edit_text(
                    f"🔓 Found password: `{password}`\n"
                    f"⏳ Extracting `{file_name}`...",
                    parse_mode='Markdown'
                )
                # Continue with extraction below
            else:
                # Add to pending archives
                file_hash = password_manager.add_pending_archive(
                    file_path=str(file_path),
                    source=f"Telegram: {user_id}"
                )
                
                await processing_msg.edit_text(
                    f"🔐 *Password Required*\n\n"
                    f"📦 File: `{file_name}`\n"
                    f"🔢 Hash: `{file_hash}`\n\n"
                    f"None of the common passwords worked.\n"
                    f"Please provide the password:\n"
                    f"`/unlock {file_hash} <password>`\n\n"
                    f"Or check `/pending` to see all waiting archives.",
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
                )
                return
        
        # Update message
        await processing_msg.edit_text(
            f"✅ Downloaded `{file_name}`\n"
            f"⏳ Processing archive...",
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
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
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
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
                )
                logger.error(f"Failed to process {file_name}")
                
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}", exc_info=True)
            await processing_msg.edit_text(
                f"❌ *Error Processing File*\n\n"
                f"File: `{file_name}`\n"
                f"Error: {str(e)}",
                parse_mode='Markdown',
                reply_markup=get_back_button()
            )
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling document: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error downloading file: {str(e)}",
            reply_markup=get_back_button()
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages, including Mega.nz links"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        return
    
    message_text = update.message.text
    
    # Check if message contains a Mega.nz link
    mega_pattern = r'https?://mega\.nz/[^\s]+'
    mega_links = re.findall(mega_pattern, message_text)
    
    if mega_links:
        for link in mega_links:
            await download_mega_file(update, link)
    else:
        await update.message.reply_text(
            "📎 Please send me a ZIP file containing stealer logs or a Mega.nz link.\n"
            "Use /status to check the bot status.",
            reply_markup=get_back_button()
        )
