"""
Password management commands for Telegram bot.
Allows users to:
- View pending password-protected archives
- Submit passwords for extraction
- Check extraction status
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.services.password_archive_manager import password_manager, PendingArchive
from app.database import SessionLocal
from app.services.zip_ingestion import ZipIngestionService
from .config import logger, ALLOWED_USER_ID, UPLOAD_DIR
from .utils import get_back_button
from pathlib import Path


# Conversation states
WAITING_PASSWORD = 1


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of pending password-protected archives"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    pending = password_manager.get_pending_archives()
    
    if not pending:
        await update.message.reply_text(
            "✅ No pending password-protected archives!\n\n"
            "All archives have been extracted or there are none waiting.",
            reply_markup=get_back_button()
        )
        return
    
    # Build message with list of pending archives
    message = f"🔐 *Pending Password-Protected Archives*\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"Found {len(pending)} archive(s) waiting for passwords:\n\n"
    
    keyboard = []
    
    for archive in pending:
        message += f"📦 `{archive.file_name}`\n"
        message += f"   Hash: `{archive.file_hash}`\n"
        message += f"   Source: {archive.source}\n"
        message += f"   Attempts: {archive.attempts}\n\n"
        
        # Add button for each archive
        keyboard.append([
            InlineKeyboardButton(
                f"🔑 Unlock: {archive.file_name[:20]}...",
                callback_data=f"unlock_{archive.file_hash}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Submit a password for a pending archive.
    Usage: /unlock <hash> <password>
    Or: /unlock <password> (if only one pending archive)
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    args = context.args if context.args else []
    
    pending = password_manager.get_pending_archives()
    
    if not pending:
        await update.message.reply_text(
            "✅ No pending archives to unlock!",
            reply_markup=get_back_button()
        )
        return
    
    # Parse arguments
    if len(args) == 0:
        # No arguments - show help
        await update.message.reply_text(
            "🔑 *Unlock Password-Protected Archive*\n\n"
            "Usage:\n"
            "`/unlock <password>` - If only one pending archive\n"
            "`/unlock <hash> <password>` - For specific archive\n\n"
            "Use `/pending` to see archive hashes.",
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        return
    
    elif len(args) == 1:
        # One argument - could be password for single pending archive
        if len(pending) == 1:
            file_hash = pending[0].file_hash
            password = args[0]
        else:
            await update.message.reply_text(
                f"⚠️ Multiple archives pending ({len(pending)})!\n"
                "Please specify which one:\n"
                "`/unlock <hash> <password>`\n\n"
                "Use `/pending` to see archive hashes.",
                parse_mode='Markdown'
            )
            return
    else:
        # Two arguments - hash and password
        file_hash = args[0]
        password = ' '.join(args[1:])  # Password might have spaces
    
    # Find the archive
    archive = password_manager.get_pending_archive(file_hash)
    
    if not archive:
        # Maybe they provided partial hash
        for a in pending:
            if a.file_hash.startswith(file_hash) or file_hash in a.file_name:
                archive = a
                file_hash = a.file_hash
                break
    
    if not archive:
        await update.message.reply_text(
            f"❌ Archive not found: `{file_hash}`\n"
            "Use `/pending` to see available archives.",
            parse_mode='Markdown'
        )
        return
    
    # Try to extract with the password
    status_msg = await update.message.reply_text(
        f"🔓 Trying password on `{archive.file_name}`...",
        parse_mode='Markdown'
    )
    
    result = password_manager.extract_with_password(file_hash, password)
    
    if result['success']:
        await status_msg.edit_text(
            f"✅ *Successfully Extracted!*\n\n"
            f"📦 File: `{archive.file_name}`\n"
            f"🔑 Password: `{password}`\n"
            f"📁 {result['message']}\n\n"
            f"⏳ Processing extracted files...",
            parse_mode='Markdown'
        )
        
        # Now process the extracted files
        try:
            output_dir = Path(result['output_dir'])
            
            # Find ZIP files in the extracted content
            zip_files = list(output_dir.rglob('*.zip'))
            
            if zip_files:
                # Process each ZIP file
                db = SessionLocal()
                try:
                    ingestion_service = ZipIngestionService(logger=logger)
                    total_processed = 0
                    
                    for zip_file in zip_files:
                        try:
                            process_result = ingestion_service.process_zip_file(zip_file, db)
                            if process_result.get('success'):
                                total_processed += 1
                        except Exception as e:
                            logger.error(f"Error processing {zip_file}: {e}")
                    
                    await status_msg.edit_text(
                        f"✅ *Extraction & Processing Complete!*\n\n"
                        f"📦 Archive: `{archive.file_name}`\n"
                        f"🔑 Password: `{password}`\n"
                        f"📁 Extracted: {result['message']}\n"
                        f"✨ Processed: {total_processed} ZIP file(s)\n\n"
                        f"Use /stats to see updated statistics.",
                        parse_mode='Markdown',
                        reply_markup=get_back_button()
                    )
                finally:
                    db.close()
            else:
                # No nested ZIPs, might be already extracted content
                await status_msg.edit_text(
                    f"✅ *Extraction Complete!*\n\n"
                    f"📦 Archive: `{archive.file_name}`\n"
                    f"🔑 Password: `{password}`\n"
                    f"📁 {result['message']}\n"
                    f"📂 Output: `{output_dir}`",
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
                )
                
        except Exception as e:
            logger.error(f"Error processing extracted files: {e}")
            await status_msg.edit_text(
                f"✅ Extracted but processing failed!\n\n"
                f"📦 Archive: `{archive.file_name}`\n"
                f"📁 {result['message']}\n"
                f"❌ Error: {str(e)}",
                parse_mode='Markdown'
            )
    else:
        await status_msg.edit_text(
            f"❌ *Wrong Password!*\n\n"
            f"📦 File: `{archive.file_name}`\n"
            f"🔑 Tried: `{password}`\n"
            f"❌ {result['message']}\n\n"
            f"Try another password with:\n"
            f"`/unlock {file_hash} <password>`",
            parse_mode='Markdown'
        )


async def trypasswords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Try common passwords on all pending archives.
    Usage: /trypasswords
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    pending = password_manager.get_pending_archives()
    
    if not pending:
        await update.message.reply_text(
            "✅ No pending archives to try passwords on!",
            reply_markup=get_back_button()
        )
        return
    
    status_msg = await update.message.reply_text(
        f"🔑 Trying {len(password_manager.common_passwords)} common passwords on {len(pending)} archive(s)...\n"
        "This may take a while..."
    )
    
    results = []
    
    for archive in pending:
        file_path = Path(archive.file_path)
        
        if not file_path.exists():
            results.append(f"❌ `{archive.file_name}` - File not found")
            password_manager.remove_pending(archive.file_hash)
            continue
        
        # Try common passwords
        password = password_manager.try_common_passwords(file_path)
        
        if password:
            # Extract with found password
            result = password_manager.extract_with_password(archive.file_hash, password)
            if result['success']:
                results.append(f"✅ `{archive.file_name}` - Password: `{password}`")
            else:
                results.append(f"⚠️ `{archive.file_name}` - Found password but extraction failed")
        else:
            results.append(f"❌ `{archive.file_name}` - No common password worked")
    
    # Build results message
    message = "🔑 *Password Brute Force Results*\n\n"
    message += '\n'.join(results)
    
    remaining = password_manager.get_pending_archives()
    if remaining:
        message += f"\n\n📝 {len(remaining)} archive(s) still need passwords."
        message += "\nUse `/unlock <hash> <password>` to try specific passwords."
    
    await status_msg.edit_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_back_button()
    )


async def addpassword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a password to the common passwords list.
    Usage: /addpassword <password>
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    args = context.args if context.args else []
    
    if not args:
        await update.message.reply_text(
            "Usage: `/addpassword <password>`\n\n"
            f"Current common passwords: {len(password_manager.common_passwords)}",
            parse_mode='Markdown'
        )
        return
    
    password = ' '.join(args)
    
    if password in password_manager.common_passwords:
        await update.message.reply_text(
            f"⚠️ Password `{password}` already in list!",
            parse_mode='Markdown'
        )
        return
    
    password_manager.common_passwords.append(password)
    
    await update.message.reply_text(
        f"✅ Added password: `{password}`\n"
        f"Total common passwords: {len(password_manager.common_passwords)}",
        parse_mode='Markdown'
    )


async def handle_unlock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unlock button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != ALLOWED_USER_ID:
        return
    
    data = query.data
    
    if data.startswith("unlock_"):
        file_hash = data.replace("unlock_", "")
        archive = password_manager.get_pending_archive(file_hash)
        
        if not archive:
            await query.edit_message_text(
                "❌ Archive no longer pending.",
                reply_markup=get_back_button()
            )
            return
        
        # Store the hash in context for the reply
        context.user_data['unlock_hash'] = file_hash
        
        await query.edit_message_text(
            f"🔐 *Unlock Archive*\n\n"
            f"📦 File: `{archive.file_name}`\n"
            f"📊 Size: {Path(archive.file_path).stat().st_size / 1024 / 1024:.1f}MB\n"
            f"🔢 Attempts: {archive.attempts}\n\n"
            f"Reply with the password to unlock this archive.\n"
            f"Or use: `/unlock {file_hash} <password>`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Try Common Passwords", callback_data=f"trycommon_{file_hash}")],
                [InlineKeyboardButton("🔙 Back", callback_data="pending_list")]
            ])
        )
    
    elif data.startswith("trycommon_"):
        file_hash = data.replace("trycommon_", "")
        archive = password_manager.get_pending_archive(file_hash)
        
        if not archive:
            await query.edit_message_text("❌ Archive not found.")
            return
        
        await query.edit_message_text(
            f"🔑 Trying common passwords on `{archive.file_name}`...",
            parse_mode='Markdown'
        )
        
        file_path = Path(archive.file_path)
        password = password_manager.try_common_passwords(file_path)
        
        if password:
            result = password_manager.extract_with_password(file_hash, password)
            if result['success']:
                await query.edit_message_text(
                    f"✅ *Successfully Extracted!*\n\n"
                    f"📦 File: `{archive.file_name}`\n"
                    f"🔑 Password: `{password}`\n"
                    f"📁 {result['message']}",
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
                )
            else:
                await query.edit_message_text(
                    f"⚠️ Found password but extraction failed!\n\n"
                    f"🔑 Password: `{password}`\n"
                    f"❌ {result['message']}",
                    parse_mode='Markdown',
                    reply_markup=get_back_button()
                )
        else:
            await query.edit_message_text(
                f"❌ No common password worked for `{archive.file_name}`\n\n"
                f"Please provide the password manually:\n"
                f"`/unlock {file_hash} <password>`",
                parse_mode='Markdown',
                reply_markup=get_back_button()
            )
    
    elif data == "pending_list":
        # Regenerate pending list
        pending = password_manager.get_pending_archives()
        
        if not pending:
            await query.edit_message_text(
                "✅ No pending archives!",
                reply_markup=get_back_button()
            )
            return
        
        message = f"🔐 *Pending Archives*\n\n"
        keyboard = []
        
        for archive in pending:
            message += f"📦 `{archive.file_name}`\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"🔑 {archive.file_name[:25]}...",
                    callback_data=f"unlock_{archive.file_hash}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
