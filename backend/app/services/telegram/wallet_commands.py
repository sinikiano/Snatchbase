"""
Wallet balance checker commands for Telegram bot
"""
from telegram import Update
from telegram.ext import ContextTypes
from app.services.wallet_checker import get_balance_checker
from app.database import SessionLocal
from app.models import Wallet
from sqlalchemy import func, desc
from decimal import Decimal
import asyncio
from .config import logger, ALLOWED_USER_ID
from .utils import get_back_button


async def wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /wallets command - show wallet statistics and top wallets
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    await update.message.reply_text("💰 Loading wallet statistics...\n⏳ Please wait...")
    
    checker = get_balance_checker()
    
    try:
        # Get statistics
        stats = await checker.get_wallet_statistics()
        
        # Build message
        message = "💰 *WALLET STATISTICS*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += "📊 *OVERVIEW*\n"
        message += f"🔢 Total Wallets: `{stats['total_wallets']:,}`\n"
        message += f"📍 With Addresses: `{stats['wallets_with_address']:,}`\n"
        message += f"✅ Checked: `{stats['checked_wallets']:,}`\n"
        message += f"⏳ Unchecked: `{stats['unchecked_wallets']:,}`\n"
        message += f"💎 With Balance: `{stats['wallets_with_balance']:,}`\n"
        message += f"💵 Total Value: `${stats['total_value_usd']:,.2f}` USD\n\n"
        
        # Breakdown by type
        if stats['breakdown_by_type']:
            message += "🪙 *BREAKDOWN BY TYPE*\n"
            for wallet_type, data in sorted(stats['breakdown_by_type'].items()):
                count = data['count']
                total_usd = data['total_usd']
                message += f"• `{wallet_type}`: {count:,} wallets"
                if total_usd > 0:
                    message += f" (${total_usd:,.2f})"
                message += "\n"
            message += "\n"
        
        # Get top wallets
        db = SessionLocal()
        try:
            top_wallets = db.query(Wallet).filter(
                Wallet.balance_usd.isnot(None),
                Wallet.balance_usd > 0
            ).order_by(
                desc(Wallet.balance_usd)
            ).limit(10).all()
            
            if top_wallets:
                message += "🏆 *TOP 10 WALLETS BY VALUE*\n"
                for i, wallet in enumerate(top_wallets, 1):
                    address_short = f"{wallet.address[:8]}...{wallet.address[-6:]}" if len(wallet.address) > 20 else wallet.address
                    balance_usd = float(wallet.balance_usd) if wallet.balance_usd else 0
                    balance = float(wallet.balance) if wallet.balance else 0
                    message += f"{i}. `{wallet.wallet_type}` - ${balance_usd:,.2f}\n"
                    message += f"   {address_short} ({balance:.6f} {wallet.wallet_type})\n"
        finally:
            db.close()
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "💡 *COMMANDS*\n"
        message += "`/checkwallets` - Check unchecked wallets\n"
        message += "`/checkbalances` - Re-check all balances\n"
        message += "`/highvalue` - Show wallets >$100"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        
        logger.info(f"Wallets command executed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in wallets command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error loading wallet statistics: {str(e)}",
            reply_markup=get_back_button()
        )


async def checkwallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /checkwallets command - check unchecked wallet balances
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    # Parse limit from arguments
    limit = 50
    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
            limit = min(max(limit, 1), 200)  # Limit between 1-200
        except ValueError:
            pass
    
    status_msg = await update.message.reply_text(
        f"🔍 Checking up to {limit} unchecked wallets...\n"
        f"⏳ This may take a few minutes...\n\n"
        f"💡 Rate limiting is enabled to avoid API blocks"
    )
    
    checker = get_balance_checker()
    
    try:
        # Check unchecked wallets
        results = await checker.check_unchecked_wallets(limit=limit, batch_size=5)
        
        # Build result message
        message = "✅ *WALLET CHECK COMPLETE*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += "📊 *RESULTS*\n"
        message += f"🔢 Total Checked: `{results['checked']}`\n"
        message += f"✅ Successful: `{results['success']}`\n"
        message += f"❌ Failed: `{results['failed']}`\n"
        message += f"💎 With Balance: `{results['with_balance']}`\n"
        
        if results['with_balance'] > 0:
            total_value = float(results['total_value_usd'])
            message += f"💵 Total Found: `${total_value:,.2f}` USD\n\n"
            
            # Show wallets with balance
            message += "💰 *WALLETS WITH BALANCE*\n"
            count = 0
            for result in results['results']:
                if result.get('has_balance') and result.get('balance_usd'):
                    count += 1
                    if count <= 10:  # Show top 10
                        addr = result['address']
                        addr_short = f"{addr[:8]}...{addr[-6:]}" if len(addr) > 20 else addr
                        balance = result['balance']
                        balance_usd = result['balance_usd']
                        wallet_type = result['wallet_type']
                        message += f"• `{wallet_type}`: ${balance_usd:,.2f}\n"
                        message += f"  {addr_short} ({balance:.6f})\n"
            
            if count > 10:
                message += f"\n_... and {count - 10} more with balance_\n"
        else:
            message += "\n😔 No wallets with balance found\n"
        
        await status_msg.edit_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        
        logger.info(f"Check wallets command: {results['with_balance']} wallets with balance found")
        
    except Exception as e:
        logger.error(f"Error checking wallets: {str(e)}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Error checking wallets: {str(e)}",
            reply_markup=get_back_button()
        )


async def highvalue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /highvalue command - show high value wallets
    Usage: /highvalue [min_value] (default: 100)
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    # Parse minimum value
    min_value = 100.0
    if context.args and len(context.args) > 0:
        try:
            min_value = float(context.args[0])
        except ValueError:
            pass
    
    db = SessionLocal()
    try:
        # Get high value wallets
        high_value_wallets = db.query(Wallet).filter(
            Wallet.balance_usd >= min_value
        ).order_by(
            desc(Wallet.balance_usd)
        ).limit(50).all()
        
        if not high_value_wallets:
            await update.message.reply_text(
                f"💰 No wallets found with value >= ${min_value:,.2f}",
                reply_markup=get_back_button()
            )
            return
        
        # Calculate total
        total_value = sum(float(w.balance_usd) for w in high_value_wallets if w.balance_usd)
        
        # Build message
        message = f"💎 *HIGH VALUE WALLETS (>= ${min_value:,.2f})*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += f"📊 Found: `{len(high_value_wallets)}` wallets\n"
        message += f"💵 Total: `${total_value:,.2f}` USD\n\n"
        
        # Group by type
        by_type = {}
        for wallet in high_value_wallets:
            wtype = wallet.wallet_type
            if wtype not in by_type:
                by_type[wtype] = []
            by_type[wtype].append(wallet)
        
        message += "🪙 *BY TYPE*\n"
        for wtype, wallets in sorted(by_type.items()):
            type_total = sum(float(w.balance_usd) for w in wallets if w.balance_usd)
            message += f"• `{wtype}`: {len(wallets)} (${type_total:,.2f})\n"
        
        message += "\n🏆 *TOP 15 WALLETS*\n"
        for i, wallet in enumerate(high_value_wallets[:15], 1):
            addr = wallet.address
            addr_short = f"{addr[:8]}...{addr[-6:]}" if len(addr) > 20 else addr
            balance = float(wallet.balance) if wallet.balance else 0
            balance_usd = float(wallet.balance_usd) if wallet.balance_usd else 0
            
            message += f"{i}. `{wallet.wallet_type}` - ${balance_usd:,.2f}\n"
            message += f"   {addr_short}\n"
            message += f"   {balance:.6f} {wallet.wallet_type}\n"
        
        if len(high_value_wallets) > 15:
            message += f"\n_... and {len(high_value_wallets) - 15} more_\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "💡 *TIP:* Use `/highvalue 1000` for wallets >$1000"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        
        logger.info(f"High value command: {len(high_value_wallets)} wallets >= ${min_value}")
        
    except Exception as e:
        logger.error(f"Error in highvalue command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error loading high value wallets: {str(e)}",
            reply_markup=get_back_button()
        )
    finally:
        db.close()


async def checkbalances_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /checkbalances - re-check wallets with balance
    """
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    limit = 30
    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
            limit = min(max(limit, 1), 100)
        except ValueError:
            pass
    
    status_msg = await update.message.reply_text(
        f"🔄 Re-checking {limit} wallets with balance...\n"
        f"⏳ Please wait..."
    )
    
    checker = get_balance_checker()
    
    try:
        results = await checker.check_wallets_with_balance(limit=limit, batch_size=5)
        
        message = "✅ *BALANCE RE-CHECK COMPLETE*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += f"🔢 Checked: `{results['checked']}`\n"
        message += f"✅ Success: `{results['success']}`\n"
        message += f"💎 Still Have Balance: `{results['with_balance']}`\n"
        message += f"💵 Total Value: `${float(results['total_value_usd']):,.2f}` USD\n"
        
        await status_msg.edit_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_back_button()
        )
        
    except Exception as e:
        logger.error(f"Error re-checking balances: {str(e)}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Error re-checking balances: {str(e)}",
            reply_markup=get_back_button()
        )
