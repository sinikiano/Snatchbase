"""
Search command handler for Telegram bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import or_
from app.database import SessionLocal
from app.models import Credential, Device
from .config import logger, ALLOWED_USER_ID
from .utils import get_back_button


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command to search credentials"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    # Check if search query is provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "🔍 *Search Credentials*\n\n"
            "Usage: `/search <query>`\n\n"
            "Examples:\n"
            "• `/search gmail.com` - Search by domain\n"
            "• `/search john@example.com` - Search by username/email\n"
            "• `/search password123` - Search by password\n"
            "• `/search 192.168.1.1` - Search by IP address\n\n"
            "The search will look in:\n"
            "✓ Domains\n"
            "✓ Usernames/Emails\n"
            "✓ URLs\n"
            "✓ IP Addresses",
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        return
    
    # Join all arguments as search query
    search_query = ' '.join(context.args)
    
    await update.message.reply_text(
        f"🔍 Searching for: `{search_query}`\n"
        f"⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    db = SessionLocal()
    try:
        # Search in credentials
        search_pattern = f"%{search_query}%"
        credentials = db.query(Credential).filter(
            or_(
                Credential.domain.ilike(search_pattern),
                Credential.username.ilike(search_pattern),
                Credential.url.ilike(search_pattern)
            )
        ).limit(100).all()
        
        if not credentials:
            await update.message.reply_text(
                f"❌ No results found for: `{search_query}`",
                parse_mode='Markdown',
                reply_markup=get_back_button()
            )
            return
        
        # Group results by domain
        domain_results = {}
        for cred in credentials:
            domain = cred.domain or "Unknown"
            if domain not in domain_results:
                domain_results[domain] = []
            domain_results[domain].append(cred)
        
        # Build result message
        total_found = len(credentials)
        total_domains = len(domain_results)
        
        if total_found > 50:
            # Too many results, show summary and create file
            import tempfile
            from datetime import datetime
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
            temp_path = temp_file.name
            
            temp_file.write(f"Search Results for: {search_query}\n")
            temp_file.write(f"=" * 60 + "\n\n")
            
            for domain, creds in sorted(domain_results.items(), key=lambda x: len(x[1]), reverse=True):
                temp_file.write(f"\n{domain} ({len(creds)} credentials)\n")
                temp_file.write("-" * 60 + "\n")
                for cred in creds:
                    temp_file.write(f"{cred.username}:{cred.password}\n")
            
            temp_file.close()
            
            # Send summary
            summary = f"✅ *Search Results*\n\n"
            summary += f"🔍 Query: `{search_query}`\n"
            summary += f"📊 Found: {total_found:,} credentials\n"
            summary += f"🌐 Domains: {total_domains}\n\n"
            summary += f"*Top domains:*\n"
            
            # Show top 10 domains
            sorted_domains = sorted(domain_results.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            for domain, creds in sorted_domains:
                summary += f"• {domain}: {len(creds):,}\n"
            
            await update.message.reply_text(summary, parse_mode='Markdown', reply_markup=get_back_button())
            
            # Send the file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_{search_query.replace(' ', '_')}_{timestamp}.txt"
            
            with open(temp_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📁 {total_found:,} results for '{search_query}'"
                )
            
            # Clean up temp file
            import os
            os.unlink(temp_path)
            
        else:
            # Small result set, show in message
            message = f"✅ *Search Results*\n\n"
            message += f"🔍 Query: `{search_query}`\n"
            message += f"📊 Found: {total_found:,} credentials\n"
            message += f"🌐 Domains: {total_domains}\n\n"
            
            # Show all results grouped by domain
            for domain, creds in sorted(domain_results.items(), key=lambda x: len(x[1]), reverse=True):
                message += f"\n*{domain}* ({len(creds)})\n"
                for cred in creds[:5]:  # Show max 5 per domain in message
                    username = cred.username[:40] if cred.username else "N/A"
                    password = cred.password[:30] if cred.password else "N/A"
                    message += f"`{username}:{password}`\n"
                
                if len(creds) > 5:
                    message += f"_... and {len(creds) - 5} more_\n"
                
                # Check message length
                if len(message) > 3500:
                    message += f"\n_Results truncated. Total: {total_found} credentials_"
                    break
            
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_back_button())
        
        logger.info(f"Search query '{search_query}' returned {total_found} results for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error during search: {str(e)}",
            reply_markup=get_back_button()
        )
    finally:
        db.close()
