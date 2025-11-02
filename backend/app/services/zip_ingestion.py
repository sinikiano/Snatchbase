"""
ZIP ingestion service - orchestrates the complete ZIP processing pipeline
"""
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from collections import defaultdict

from app.models import Device, Credential, File, PasswordStat, Software, Upload, Wallet
from app.services.zip_processor import (
    ZipStructureAnalyzer, 
    ZipFileGrouper, 
    compute_device_hash,
    is_likely_text_file
)
from app.services.password_parser import PasswordFileParser, escape_password
from app.services.software_parser import SoftwareFileParser
from app.services.system_parser import SystemFileParser
from app.services.wallet_parser import WalletParser


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Remove NULL bytes and other problematic characters from text"""
    if not text:
        return text
    # Remove NULL bytes that PostgreSQL can't handle
    return text.replace("\0", "")


def extract_stealer_name(zip_filename: str) -> Optional[str]:
    """Extract stealer name from ZIP filename"""
    # Common stealer patterns in filenames
    stealer_patterns = {
        'redline': 'RedLine',
        'raccoon': 'Raccoon',
        'vidar': 'Vidar',
        'mars': 'Mars',
        'azorult': 'Azorult',
        'lumma': 'Lumma',
        'meta': 'Meta',
        'rhadamanthys': 'Rhadamanthys',
        'stealc': 'StealC',
        'titan': 'Titan',
        'scorpion': 'Scorpion',
        'aurora': 'Aurora',
        'oski': 'Oski',
        'formbook': 'FormBook',
        'agentTesla': 'Agent Tesla',
    }
    
    filename_lower = zip_filename.lower()
    for pattern, name in stealer_patterns.items():
        if pattern in filename_lower:
            return name
    
    return None


class ZipIngestionService:
    """Service for ingesting ZIP files containing stealer logs"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.analyzer = ZipStructureAnalyzer()
        self.grouper = ZipFileGrouper(self.analyzer)
        self.password_parser = PasswordFileParser()
        self.software_parser = SoftwareFileParser()
        self.system_parser = SystemFileParser()
        self.wallet_parser = WalletParser()
    
    def process_zip_file(self, zip_path: Path, db: Session) -> Dict:
        """Process a ZIP file and ingest all data"""
        self.logger.info(f"🚀 Processing ZIP file: {zip_path}")
        
        # Generate upload batch ID
        upload_batch = f"batch_{int(datetime.now().timestamp())}_{zip_path.stem}"
        
        # Create upload record
        upload = Upload(
            upload_id=upload_batch,
            filename=zip_path.name,
            status="processing"
        )
        db.add(upload)
        db.commit()
        
        try:
            # Open ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Group files by device
                device_map, structure_info = self.grouper.group_by_device(zip_file)
                
                self.logger.info(f"📊 Found {len(device_map)} devices in ZIP")
                
                # Check for existing devices
                existing_hashes = self._get_existing_device_hashes(db, device_map.keys())
                
                # Process each device
                devices_processed = 0
                devices_skipped = 0
                total_credentials = 0
                total_files = 0
                
                for device_name, files in device_map.items():
                    device_hash = compute_device_hash(device_name)
                    
                    # Skip if device already exists
                    if device_hash in existing_hashes:
                        self.logger.info(f"⏭️ Skipping duplicate device: {device_name}")
                        devices_skipped += 1
                        continue
                    
                    self.logger.info(f"🖥️ Processing device: {device_name} ({len(files)} files)")
                    
                    # Process device
                    device_stats = self._process_device(
                        db=db,
                        device_name=device_name,
                        device_hash=device_hash,
                        files=files,
                        upload_batch=upload_batch,
                        zip_file=zip_file
                    )
                    
                    devices_processed += 1
                    total_credentials += device_stats["credentials"]
                    total_files += device_stats["files"]
                    
                    # Commit after each device to avoid losing progress
                    db.commit()
                    self.logger.info(f"✅ Device processed: {device_name}")
                
                # Update upload record
                upload.status = "completed"
                upload.devices_found = len(device_map)
                upload.devices_processed = devices_processed
                upload.devices_skipped = devices_skipped
                upload.total_credentials = total_credentials
                upload.total_files = total_files
                upload.completed_at = datetime.now()
                db.commit()
                
                result = {
                    "success": True,
                    "upload_batch": upload_batch,
                    "devices_found": len(device_map),
                    "devices_processed": devices_processed,
                    "devices_skipped": devices_skipped,
                    "total_credentials": total_credentials,
                    "total_files": total_files,
                    "structure_type": structure_info.structure_type,
                }
                
                self.logger.info(f"✅ ZIP processing completed: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error processing ZIP: {e}", exc_info=True)
            upload.status = "failed"
            upload.error_message = str(e)
            db.commit()
            raise
    
    def _get_existing_device_hashes(self, db: Session, device_names: List[str]) -> set:
        """Get hashes of existing devices to avoid duplicates"""
        if not device_names:
            return set()
        
        hashes = [compute_device_hash(name) for name in device_names]
        existing = db.query(Device.device_name_hash).filter(
            Device.device_name_hash.in_(hashes)
        ).all()
        
        return {row.device_name_hash for row in existing}
    
    def _process_device(
        self, 
        db: Session,
        device_name: str,
        device_hash: str,
        files: List,
        upload_batch: str,
        zip_file: zipfile.ZipFile
    ) -> Dict:
        """Process a single device"""
        # Generate unique device ID using device hash to ensure uniqueness
        # Use only hash to keep it short and avoid varchar limits
        device_id = f"dev_{device_hash}"
        
        # Extract system info from System.txt
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
        
        system_files = [
            (path, entry) for path, entry in files
            if Path(path).name.lower() in ['system.txt', 'systeminfo.txt', 'information.txt'] and not entry.is_dir()
        ]
        
        if system_files:
            try:
                path, entry = system_files[0]
                content = zip_file.read(entry).decode('utf-8', errors='ignore')
                system_info = self.system_parser.parse(content)
                stealer_name = system_info.get('stealer_name')
                hostname = system_info.get('hostname')
                ip_address = system_info.get('ip_address')
                country = system_info.get('country')
                language = system_info.get('language')
                os_version = system_info.get('os_version')
                username = system_info.get('username')
                infection_date = system_info.get('infection_time')  # Use "Time:" field, not "Local Date"
                antivirus = system_info.get('antivirus')
                hwid = system_info.get('hwid')
                
                if stealer_name:
                    self.logger.info(f"🎯 Detected stealer: {stealer_name}")
                if hostname:
                    self.logger.info(f"💻 Hostname: {hostname}")
                if ip_address:
                    self.logger.info(f"🌐 IP: {ip_address}")
                if country:
                    self.logger.info(f"🌍 Country: {country}")
                if infection_date:
                    self.logger.info(f"⏰ Infection Time: {infection_date}")
                else:
                    self.logger.warning(f"⚠️ No infection time found in System.txt")
            except Exception as e:
                self.logger.error(f"❌ Error parsing system file: {e}")
        
        # Debug: Log all .txt files in the device
        txt_files = [(path, Path(path).name) for path, entry in files if Path(path).name.lower().endswith('.txt') and not entry.is_dir()]
        if txt_files:
            self.logger.info(f"📄 Found {len(txt_files)} .txt files in device: {[name for _, name in txt_files[:10]]}")
        
        # Find password files
        password_files = [
            (path, entry) for path, entry in files
            if self.password_parser.is_password_file(Path(path).name) and not entry.is_dir()
        ]
        
        if password_files:
            self.logger.info(f"🔍 Found {len(password_files)} password files: {[Path(p).name for p, _ in password_files]}")
        else:
            self.logger.info(f"🔍 Found {len(password_files)} password files")
        
        # Parse credentials
        all_credentials = []
        password_counts = defaultdict(int)
        domain_count = 0
        url_count = 0
        
        for path, entry in password_files:
            try:
                content = zip_file.read(entry).decode('utf-8', errors='ignore')
                stats = self.password_parser.parse_password_file(content)
                
                # Collect credentials
                for cred in stats.credentials:
                    all_credentials.append({
                        "url": cred.url,
                        "domain": cred.domain,
                        "tld": cred.tld,
                        "username": cred.username,
                        "password": cred.password,
                        "browser": cred.browser,
                        "stealer_name": stealer_name,
                        "file_path": path,
                    })
                
                # Merge password counts
                for password, count in stats.password_counts.items():
                    password_counts[password] += count
                
                domain_count += stats.domain_count
                url_count += stats.url_count
                
            except Exception as e:
                self.logger.error(f"❌ Error parsing password file {path}: {e}")
                continue
        
        # Find software files
        software_files = [
            (path, entry) for path, entry in files
            if self.software_parser.is_software_file(Path(path).name) and not entry.is_dir()
        ]
        
        self.logger.info(f"🔍 Found {len(software_files)} software files")
        
        # Parse software
        all_software = []
        for path, entry in software_files:
            try:
                content = zip_file.read(entry).decode('utf-8', errors='ignore')
                software_entries = self.software_parser.parse_software_file(content)
                
                for sw in software_entries:
                    all_software.append({
                        "software_name": sw.software_name,
                        "version": sw.version,
                        "source_file": Path(path).name,
                    })
                
            except Exception as e:
                self.logger.error(f"❌ Error parsing software file {path}: {e}")
                continue
        
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
            total_files=len(files),
            total_credentials=len(all_credentials),
            total_domains=domain_count,
            total_urls=url_count,
        )
        db.add(device)
        db.flush()  # Get device ID
        
        # Save credentials
        self.logger.info(f"💾 Saving {len(all_credentials)} credentials")
        for cred_data in all_credentials:
            try:
                # Truncate fields to fit VARCHAR limits
                domain = sanitize_text(cred_data["domain"])
                domain = domain[:500] if domain else None
                
                tld = sanitize_text(cred_data["tld"])
                tld = tld[:50] if tld else None
                
                username = sanitize_text(cred_data["username"])
                username = username[:500] if username else None
                
                browser = sanitize_text(cred_data["browser"])
                browser = browser[:200] if browser else None
                
                stealer_name = sanitize_text(cred_data.get("stealer_name"))
                stealer_name = stealer_name[:200] if stealer_name else None
                
                credential = Credential(
                    device_id=device_id,
                    url=sanitize_text(cred_data["url"]),
                    domain=domain,
                    tld=tld,
                    username=username,
                    password=sanitize_text(cred_data["password"]),
                    browser=browser,
                    stealer_name=stealer_name,
                    file_path=sanitize_text(cred_data["file_path"]),
                )
                db.add(credential)
            except Exception as e:
                self.logger.error(f"❌ Error saving credential: {e}")
                continue
        
        # Save password stats
        self.logger.info(f"💾 Saving {len(password_counts)} password stats")
        for password, count in password_counts.items():
            try:
                stat = PasswordStat(
                    device_id=device_id,
                    password=sanitize_text(password),
                    count=count,
                )
                db.add(stat)
            except Exception as e:
                self.logger.error(f"❌ Error saving password stat: {e}")
                continue
        
        # Save software
        self.logger.info(f"💾 Saving {len(all_software)} software entries")
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
                self.logger.error(f"❌ Error saving software: {e}")
                continue
        
        # Parse and save wallets
        self.logger.info(f"🔍 Searching for wallet files")
        wallet_files = [
            (path, entry) for path, entry in files
            if self.wallet_parser.is_wallet_file(Path(path).name) and not entry.is_dir()
        ]
        
        self.logger.info(f"💰 Found {len(wallet_files)} wallet files")
        all_wallets = []
        
        for path, entry in wallet_files:
            try:
                content = zip_file.read(entry).decode('utf-8', errors='ignore')
                wallets = self.wallet_parser.parse_wallet_file(content, Path(path).name)
                
                for wallet in wallets:
                    # Hash sensitive data
                    from hashlib import sha256
                    mnemonic_hash = sha256(wallet.mnemonic.encode()).hexdigest() if wallet.mnemonic else None
                    private_key_hash = sha256(wallet.private_key.encode()).hexdigest() if wallet.private_key else None
                    
                    all_wallets.append({
                        "wallet_type": wallet.wallet_type,
                        "address": wallet.address,
                        "mnemonic_hash": mnemonic_hash,
                        "private_key_hash": private_key_hash,
                        "password": wallet.password,
                        "path": wallet.path or path,
                        "source_file": wallet.source_file or Path(path).name,
                    })
                
            except Exception as e:
                self.logger.error(f"❌ Error parsing wallet file {path}: {e}")
                continue
        
        self.logger.info(f"💾 Saving {len(all_wallets)} wallets")
        for wallet_data in all_wallets:
            try:
                wallet = Wallet(
                    device_id=device.id,  # Use device.id (integer PK) not device_id (string)
                    wallet_type=sanitize_text(wallet_data["wallet_type"]),
                    address=sanitize_text(wallet_data.get("address")),
                    mnemonic_hash=wallet_data.get("mnemonic_hash"),
                    private_key_hash=wallet_data.get("private_key_hash"),
                    password=sanitize_text(wallet_data.get("password")),
                    path=sanitize_text(wallet_data.get("path")),
                    source_file=sanitize_text(wallet_data.get("source_file")),
                )
                db.add(wallet)
            except Exception as e:
                self.logger.error(f"❌ Error saving wallet: {e}")
                continue
        
        # Save file tree (text files only)
        self.logger.info(f"💾 Saving file tree ({len(files)} entries)")
        file_count = 0
        for path, entry in files:
            try:
                filename = Path(path).name
                parent_path = str(Path(path).parent)
                
                # Only store text file content
                content = None
                size = 0
                
                if not entry.is_dir():
                    if is_likely_text_file(filename):
                        try:
                            content = zip_file.read(entry).decode('utf-8', errors='ignore')
                            size = len(content)
                        except:
                            size = entry.file_size
                    else:
                        size = entry.file_size
                
                file_record = File(
                    device_id=device_id,
                    file_path=sanitize_text(path),
                    file_name=sanitize_text(filename),
                    parent_path=sanitize_text(parent_path),
                    is_directory=entry.is_dir(),
                    file_size=size,
                    content=sanitize_text(content),
                )
                db.add(file_record)
                
                if not entry.is_dir():
                    file_count += 1
                
            except Exception as e:
                self.logger.error(f"❌ Error saving file {path}: {e}")
                continue
        
        return {
            "credentials": len(all_credentials),
            "files": file_count,
            "software": len(all_software),
            "wallets": len(all_wallets),
        }
