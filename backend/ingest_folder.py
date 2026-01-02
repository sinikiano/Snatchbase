#!/usr/bin/env python3
"""
Ingest extracted stealer log folder into Snatchbase database
This script processes folders that were extracted from RAR/ZIP archives
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from hashlib import sha256
import logging

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models import Device, Credential, File, PasswordStat, Software, Upload, Wallet
from app.services.zip_processor import compute_device_hash
from app.services.password_parser import PasswordFileParser
from app.services.software_parser import SoftwareFileParser
from app.services.system_parser import SystemFileParser
from app.services.wallet_parser import WalletParser


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_text(text):
    """Remove NULL bytes and other problematic characters from text"""
    if not text:
        return text
    return text.replace("\0", "")


def read_file_content(file_path: Path) -> str:
    """Read file content with encoding detection"""
    try:
        return file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return ""


def process_device_folder(device_dir: Path, upload_batch: str, db) -> dict:
    """Process a single device folder"""
    device_name = device_dir.name
    device_hash = compute_device_hash(device_name)
    device_id = f"dev_{device_hash}"
    
    # Initialize parsers
    password_parser = PasswordFileParser()
    software_parser = SoftwareFileParser()
    system_parser = SystemFileParser()
    wallet_parser = WalletParser()
    
    # Check if device already exists
    existing = db.query(Device).filter(Device.device_name_hash == device_hash).first()
    if existing:
        return {"status": "skipped", "reason": "duplicate"}
    
    # Initialize device info
    stealer_name = None
    hostname = None
    ip_address = None
    country = None
    language = None
    os_version = None
    username = None
    infection_date = None
    antivirus = None
    hwid = None
    
    # Find and parse system files
    system_files = list(device_dir.glob("**/[Ss]ystem*.txt")) + \
                   list(device_dir.glob("**/[Ii]nformation.txt"))
    
    if system_files:
        try:
            content = read_file_content(system_files[0])
            if content:
                system_info = system_parser.parse(content)
                stealer_name = system_info.get('stealer_name')
                hostname = system_info.get('hostname')
                ip_address = system_info.get('ip_address')
                country = system_info.get('country')
                language = system_info.get('language')
                os_version = system_info.get('os_version')
                username = system_info.get('username')
                infection_date = system_info.get('infection_time')
                antivirus = system_info.get('antivirus')
                hwid = system_info.get('hwid')
        except Exception as e:
            logger.error(f"Error parsing system file: {e}")
    
    # Find password files
    password_files = []
    for pattern in ["**/[Pp]assword*.txt", "**/[Aa]uto[Ff]ill*.txt", "**/[Ll]ogin*.txt", 
                    "**/[Cc]ookies*.txt", "**/[Bb]rowser*.txt", "**/[Cc]redentials*.txt"]:
        password_files.extend(device_dir.glob(pattern))
    
    # Parse credentials
    all_credentials = []
    password_counts = defaultdict(int)
    domain_count = 0
    url_count = 0
    
    for pw_file in password_files:
        if not pw_file.is_file():
            continue
        try:
            content = read_file_content(pw_file)
            if not content or len(content) < 10:
                continue
                
            # Check if this looks like a password file
            if not password_parser.is_password_file(pw_file.name):
                continue
                
            stats = password_parser.parse_password_file(content)
            
            for cred in stats.credentials:
                all_credentials.append({
                    "url": cred.url,
                    "domain": cred.domain,
                    "tld": cred.tld,
                    "username": cred.username,
                    "password": cred.password,
                    "browser": cred.browser,
                    "stealer_name": stealer_name,
                    "file_path": str(pw_file.relative_to(device_dir)),
                })
            
            for password, count in stats.password_counts.items():
                password_counts[password] += count
            
            domain_count += stats.domain_count
            url_count += stats.url_count
            
        except Exception as e:
            logger.error(f"Error parsing password file {pw_file}: {e}")
    
    # Find software files
    software_files = list(device_dir.glob("**/[Ii]nstalled*.txt")) + \
                     list(device_dir.glob("**/[Ss]oftware*.txt"))
    
    all_software = []
    for sw_file in software_files:
        if not sw_file.is_file():
            continue
        try:
            content = read_file_content(sw_file)
            if not content:
                continue
            software_entries = software_parser.parse_software_file(content)
            for sw in software_entries:
                all_software.append({
                    "software_name": sw.software_name,
                    "version": sw.version,
                    "source_file": sw_file.name,
                })
        except Exception as e:
            logger.error(f"Error parsing software file {sw_file}: {e}")
    
    # Find wallet files
    wallet_files = list(device_dir.glob("**/[Ww]allet*.txt")) + \
                   list(device_dir.glob("**/[Ss]eed*.txt")) + \
                   list(device_dir.glob("**/[Cc]rypto*.txt"))
    
    all_wallets = []
    for wallet_file in wallet_files:
        if not wallet_file.is_file():
            continue
        try:
            content = read_file_content(wallet_file)
            if not content:
                continue
            wallets = wallet_parser.parse_wallet_file(content, wallet_file.name)
            for wallet in wallets:
                mnemonic_hash = sha256(wallet.mnemonic.encode()).hexdigest() if wallet.mnemonic else None
                private_key_hash = sha256(wallet.private_key.encode()).hexdigest() if wallet.private_key else None
                all_wallets.append({
                    "wallet_type": wallet.wallet_type,
                    "address": wallet.address,
                    "mnemonic_hash": mnemonic_hash,
                    "private_key_hash": private_key_hash,
                    "password": wallet.password,
                    "path": wallet.path or str(wallet_file.relative_to(device_dir)),
                    "source_file": wallet.source_file or wallet_file.name,
                })
        except Exception as e:
            logger.error(f"Error parsing wallet file {wallet_file}: {e}")
    
    # Count total files
    total_files = sum(1 for _ in device_dir.rglob("*") if _.is_file())
    
    # Create device record
    device = Device(
        device_id=device_id,
        device_name=device_name,
        device_name_hash=device_hash,
        hostname=hostname,
        ip_address=ip_address,
        country=country,
        language=language,
        os_version=os_version,
        username=username,
        infection_date=infection_date,
        antivirus=antivirus,
        hwid=hwid,
        upload_batch=upload_batch,
        total_files=total_files,
        total_credentials=len(all_credentials),
        total_domains=domain_count,
        total_urls=url_count,
    )
    db.add(device)
    db.flush()
    
    # Save credentials
    cred_count = 0
    for cred_data in all_credentials:
        try:
            domain = sanitize_text(cred_data["domain"])
            domain = domain[:500] if domain else None
            
            tld = sanitize_text(cred_data["tld"])
            tld = tld[:50] if tld else None
            
            username = sanitize_text(cred_data["username"])
            username = username[:500] if username else None
            
            browser = sanitize_text(cred_data["browser"])
            browser = browser[:200] if browser else None
            
            stealer = sanitize_text(cred_data.get("stealer_name"))
            stealer = stealer[:200] if stealer else None
            
            credential = Credential(
                device_id=device_id,
                url=sanitize_text(cred_data["url"]),
                domain=domain,
                tld=tld,
                username=username,
                password=sanitize_text(cred_data["password"]),
                browser=browser,
                stealer_name=stealer,
                file_path=sanitize_text(cred_data["file_path"]),
            )
            db.add(credential)
            cred_count += 1
        except Exception as e:
            logger.error(f"Error saving credential: {e}")
    
    # Save password stats
    for password, count in password_counts.items():
        try:
            stat = PasswordStat(
                device_id=device_id,
                password=sanitize_text(password),
                count=count,
            )
            db.add(stat)
        except Exception as e:
            logger.error(f"Error saving password stat: {e}")
    
    # Save software
    for sw_data in all_software:
        try:
            software = Software(
                device_id=device_id,
                software_name=sanitize_text(sw_data["software_name"]),
                version=sanitize_text(sw_data["version"]),
                source_file=sanitize_text(sw_data["source_file"]),
            )
            db.add(software)
        except Exception as e:
            logger.error(f"Error saving software: {e}")
    
    # Save wallets
    for wallet_data in all_wallets:
        try:
            wallet = Wallet(
                device_id=device_id,
                wallet_type=sanitize_text(wallet_data["wallet_type"]),
                address=sanitize_text(wallet_data["address"]),
                mnemonic_hash=wallet_data["mnemonic_hash"],
                private_key_hash=wallet_data["private_key_hash"],
                password=sanitize_text(wallet_data.get("password")),
                path=sanitize_text(wallet_data.get("path")),
                source_file=sanitize_text(wallet_data.get("source_file")),
            )
            db.add(wallet)
        except Exception as e:
            logger.error(f"Error saving wallet: {e}")
    
    return {
        "status": "processed",
        "credentials": cred_count,
        "software": len(all_software),
        "wallets": len(all_wallets),
        "files": total_files,
    }


def ingest_folder(folder_path: Path, filename: str = None):
    """Ingest all devices from an extracted folder"""
    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        return
    
    # Get all device folders
    device_folders = [d for d in folder_path.iterdir() if d.is_dir()]
    
    if not device_folders:
        logger.error(f"No device folders found in {folder_path}")
        return
    
    logger.info(f"🚀 Starting ingestion of {len(device_folders)} devices from {folder_path}")
    
    # Generate upload batch ID
    upload_batch = f"batch_{int(datetime.now().timestamp())}_{folder_path.name}"
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create upload record
        upload = Upload(
            upload_id=upload_batch,
            filename=filename or folder_path.name,
            status="processing"
        )
        db.add(upload)
        db.commit()
        
        # Process each device
        processed = 0
        skipped = 0
        total_creds = 0
        total_files = 0
        total_wallets = 0
        
        for i, device_dir in enumerate(device_folders, 1):
            try:
                result = process_device_folder(device_dir, upload_batch, db)
                
                if result["status"] == "skipped":
                    skipped += 1
                else:
                    processed += 1
                    total_creds += result.get("credentials", 0)
                    total_files += result.get("files", 0)
                    total_wallets += result.get("wallets", 0)
                
                # Commit every 10 devices
                if i % 10 == 0:
                    db.commit()
                    logger.info(f"  Progress: {i}/{len(device_folders)} devices ({processed} processed, {skipped} skipped)")
                    
            except Exception as e:
                logger.error(f"Error processing device {device_dir.name}: {e}")
                db.rollback()
                continue
        
        # Final commit
        db.commit()
        
        # Update upload record
        upload.status = "completed"
        upload.devices_found = len(device_folders)
        upload.devices_processed = processed
        upload.devices_skipped = skipped
        upload.total_credentials = total_creds
        upload.total_files = total_files
        upload.completed_at = datetime.now()
        db.commit()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ INGESTION COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"   Total devices found: {len(device_folders)}")
        logger.info(f"   Devices processed:   {processed}")
        logger.info(f"   Devices skipped:     {skipped}")
        logger.info(f"   Total credentials:   {total_creds}")
        logger.info(f"   Total wallets:       {total_wallets}")
        logger.info(f"   Total files:         {total_files}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_folder.py <folder_path> [original_filename]")
        print("Example: python ingest_folder.py data/incoming/uploads/extracted_hubhead '16.08 @HUBHEAD 450PCS.rar'")
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    ingest_folder(folder_path, filename)
