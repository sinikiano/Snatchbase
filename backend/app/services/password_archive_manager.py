"""
Password-Protected Archive Handler

This module handles password-protected ZIP/RAR files by:
1. Detecting password protection when extraction fails
2. Storing pending archives that need passwords
3. Providing interface for Telegram bot to submit passwords
4. Retrying extraction with provided passwords
"""
import os
import json
import zipfile
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Union
from dataclasses import dataclass, asdict
from threading import Lock
import hashlib

logger = logging.getLogger(__name__)

# Storage file for pending archives
PENDING_ARCHIVES_FILE = Path(__file__).parent.parent.parent / "data" / "pending_archives.json"


@dataclass
class PendingArchive:
    """Represents an archive waiting for a password"""
    file_path: str
    file_name: str
    file_hash: str
    detected_at: str
    source: str  # 'telegram_scraper', 'upload', 'file_watcher'
    chat_id: Optional[int] = None  # Telegram chat to notify
    message_id: Optional[int] = None  # Message ID to reply to
    attempts: int = 0
    last_attempt: Optional[str] = None
    status: str = 'pending'  # pending, processing, extracted, failed


class PasswordArchiveManager:
    """
    Manages password-protected archives.
    
    This singleton class keeps track of archives that need passwords
    and provides methods for the Telegram bot to interact with them.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.pending_archives: Dict[str, PendingArchive] = {}
        self.common_passwords: List[str] = []
        self.on_password_needed: Optional[Callable] = None
        self.on_extraction_complete: Optional[Callable] = None
        
        # Load pending archives from storage
        self._load_pending_archives()
        
        # Load common passwords
        self._load_common_passwords()
    
    def _load_pending_archives(self):
        """Load pending archives from JSON file"""
        try:
            if PENDING_ARCHIVES_FILE.exists():
                with open(PENDING_ARCHIVES_FILE, 'r') as f:
                    data = json.load(f)
                    for file_hash, archive_data in data.items():
                        self.pending_archives[file_hash] = PendingArchive(**archive_data)
                logger.info(f"Loaded {len(self.pending_archives)} pending archives")
        except Exception as e:
            logger.error(f"Error loading pending archives: {e}")
    
    def _save_pending_archives(self):
        """Save pending archives to JSON file"""
        try:
            PENDING_ARCHIVES_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {k: asdict(v) for k, v in self.pending_archives.items()}
            with open(PENDING_ARCHIVES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending archives: {e}")
    
    def _load_common_passwords(self):
        """Load common stealer log passwords"""
        self.common_passwords = [
            # Common stealer passwords
            "infected",
            "123",
            "1234",
            "12345",
            "123456",
            "password",
            "logs",
            "stealer",
            "cloud",
            "redline",
            "raccoon",
            "vidar",
            "meta",
            "lumma",
            "mars",
            "azorult",
            "ficker",
            "aurora",
            "rhadamanthys",
            "stealc",
            "risepro",
            "mystic",
            # Common variations
            "111",
            "222",
            "333",
            "666",
            "777",
            "888",
            "999",
            "000",
            "qwerty",
            "admin",
            "root",
            "test",
            "demo",
        ]
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of first 1MB of file for identification"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read(1024 * 1024))  # First 1MB
        return hasher.hexdigest()[:16]
    
    def is_password_protected(self, file_path: Path) -> bool:
        """Check if a ZIP/RAR file is password protected"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext == '.zip':
            return self._is_zip_password_protected(file_path)
        elif ext in ['.rar', '.7z']:
            return self._is_rar_password_protected(file_path)
        
        return False
    
    def _is_zip_password_protected(self, file_path: Path) -> bool:
        """Check if ZIP file is password protected"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Try to read the first file
                for info in zf.infolist():
                    if not info.is_dir():
                        try:
                            zf.read(info.filename)
                            return False  # Successfully read, not encrypted
                        except RuntimeError as e:
                            if 'encrypted' in str(e).lower() or 'password' in str(e).lower():
                                return True
                        except Exception:
                            pass
                return False
        except zipfile.BadZipFile:
            return False
        except Exception as e:
            logger.error(f"Error checking ZIP: {e}")
            return False
    
    def _is_rar_password_protected(self, file_path: Path) -> bool:
        """Check if RAR/7z file is password protected using unrar/7z"""
        try:
            # Try unrar first
            result = subprocess.run(
                ['unrar', 't', '-p-', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if 'encrypted' in result.stderr.lower() or result.returncode != 0:
                return True
            return False
        except FileNotFoundError:
            # unrar not installed, try 7z
            try:
                result = subprocess.run(
                    ['7z', 't', '-p', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if 'wrong password' in result.stderr.lower() or result.returncode != 0:
                    return True
                return False
            except FileNotFoundError:
                logger.warning("Neither unrar nor 7z installed for RAR extraction")
                return False
        except Exception as e:
            logger.error(f"Error checking RAR: {e}")
            return False
    
    def try_common_passwords(self, file_path: Path) -> Optional[str]:
        """Try common passwords on an archive"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        logger.info(f"Trying {len(self.common_passwords)} common passwords on {file_path.name}")
        
        for password in self.common_passwords:
            if ext == '.zip':
                if self._try_zip_password(file_path, password):
                    logger.info(f"✅ Found password: {password}")
                    return password
            elif ext in ['.rar', '.7z']:
                if self._try_rar_password(file_path, password):
                    logger.info(f"✅ Found password: {password}")
                    return password
        
        return None
    
    def _try_zip_password(self, file_path: Path, password: str) -> bool:
        """Try a password on a ZIP file"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for info in zf.infolist():
                    if not info.is_dir():
                        try:
                            zf.read(info.filename, pwd=password.encode())
                            return True
                        except:
                            return False
        except:
            return False
        return False
    
    def _try_rar_password(self, file_path: Path, password: str) -> bool:
        """Try a password on a RAR/7z file"""
        try:
            result = subprocess.run(
                ['unrar', 't', f'-p{password}', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ['7z', 't', f'-p{password}', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.returncode == 0
            except:
                return False
        except:
            return False
    
    def add_pending_archive(
        self,
        file_path: Union[Path, str],
        source: str,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None
    ) -> PendingArchive:
        """Add a password-protected archive to the pending list"""
        file_path = Path(file_path)
        file_hash = self._get_file_hash(file_path)
        
        archive = PendingArchive(
            file_path=str(file_path),
            file_name=file_path.name,
            file_hash=file_hash,
            detected_at=datetime.now().isoformat(),
            source=source,
            chat_id=chat_id,
            message_id=message_id
        )
        
        self.pending_archives[file_hash] = archive
        self._save_pending_archives()
        
        logger.info(f"Added pending archive: {file_path.name} (hash: {file_hash})")
        
        # Trigger callback if set
        if self.on_password_needed:
            asyncio.create_task(self.on_password_needed(archive))
        
        return archive
    
    def get_pending_archives(self) -> List[PendingArchive]:
        """Get all pending archives"""
        return list(self.pending_archives.values())
    
    def get_pending_archive(self, file_hash: str) -> Optional[PendingArchive]:
        """Get a specific pending archive by hash"""
        return self.pending_archives.get(file_hash)
    
    def extract_with_password(
        self,
        file_hash: str,
        password: str,
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        Try to extract an archive with the provided password.
        
        Returns dict with:
        - success: bool
        - message: str
        - extracted_files: list (if successful)
        """
        archive = self.pending_archives.get(file_hash)
        if not archive:
            return {'success': False, 'message': 'Archive not found'}
        
        file_path = Path(archive.file_path)
        if not file_path.exists():
            self.pending_archives.pop(file_hash, None)
            self._save_pending_archives()
            return {'success': False, 'message': 'Archive file no longer exists'}
        
        # Update attempt count
        archive.attempts += 1
        archive.last_attempt = datetime.now().isoformat()
        archive.status = 'processing'
        self._save_pending_archives()
        
        # Determine output directory
        if output_dir is None:
            output_dir = file_path.parent / f"extracted_{file_path.stem}"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ext = file_path.suffix.lower()
        
        try:
            if ext == '.zip':
                result = self._extract_zip(file_path, password, output_dir)
            elif ext in ['.rar', '.7z']:
                result = self._extract_rar(file_path, password, output_dir)
            else:
                result = {'success': False, 'message': f'Unsupported format: {ext}'}
            
            if result['success']:
                archive.status = 'extracted'
                self.pending_archives.pop(file_hash, None)
                self._save_pending_archives()
                
                # Add password to common list if it's new
                if password not in self.common_passwords:
                    self.common_passwords.append(password)
                
                # Trigger callback
                if self.on_extraction_complete:
                    asyncio.create_task(self.on_extraction_complete(archive, result))
            else:
                archive.status = 'pending'
                self._save_pending_archives()
            
            return result
            
        except Exception as e:
            archive.status = 'pending'
            self._save_pending_archives()
            return {'success': False, 'message': str(e)}
    
    def _extract_zip(self, file_path: Path, password: str, output_dir: Path) -> Dict:
        """Extract ZIP file with password"""
        extracted_files = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for info in zf.infolist():
                    try:
                        zf.extract(info, output_dir, pwd=password.encode())
                        extracted_files.append(info.filename)
                    except RuntimeError as e:
                        if 'password' in str(e).lower() or 'encrypted' in str(e).lower():
                            return {'success': False, 'message': 'Wrong password'}
                        raise
            
            return {
                'success': True,
                'message': f'Extracted {len(extracted_files)} files',
                'extracted_files': extracted_files,
                'output_dir': str(output_dir)
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _extract_rar(self, file_path: Path, password: str, output_dir: Path) -> Dict:
        """Extract RAR/7z file with password"""
        try:
            # Try unrar first
            result = subprocess.run(
                ['unrar', 'x', '-y', f'-p{password}', str(file_path), str(output_dir) + '/'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Count extracted files
                extracted_files = list(output_dir.rglob('*'))
                return {
                    'success': True,
                    'message': f'Extracted {len(extracted_files)} files',
                    'extracted_files': [str(f) for f in extracted_files],
                    'output_dir': str(output_dir)
                }
            elif 'wrong password' in result.stderr.lower():
                return {'success': False, 'message': 'Wrong password'}
            else:
                return {'success': False, 'message': result.stderr or 'Extraction failed'}
                
        except FileNotFoundError:
            # Try 7z
            try:
                result = subprocess.run(
                    ['7z', 'x', f'-p{password}', '-y', f'-o{output_dir}', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    extracted_files = list(output_dir.rglob('*'))
                    return {
                        'success': True,
                        'message': f'Extracted {len(extracted_files)} files',
                        'extracted_files': [str(f) for f in extracted_files],
                        'output_dir': str(output_dir)
                    }
                else:
                    return {'success': False, 'message': result.stderr or 'Extraction failed'}
            except FileNotFoundError:
                return {'success': False, 'message': 'No RAR/7z extractor installed'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def remove_pending(self, file_hash: str):
        """Remove an archive from pending list"""
        if file_hash in self.pending_archives:
            del self.pending_archives[file_hash]
            self._save_pending_archives()
    
    def cleanup_old_pending(self, max_age_days: int = 7):
        """Remove pending archives older than max_age_days"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        to_remove = []
        
        for file_hash, archive in self.pending_archives.items():
            detected_at = datetime.fromisoformat(archive.detected_at)
            if detected_at < cutoff:
                to_remove.append(file_hash)
        
        for file_hash in to_remove:
            del self.pending_archives[file_hash]
        
        if to_remove:
            self._save_pending_archives()
            logger.info(f"Cleaned up {len(to_remove)} old pending archives")


# Global instance
password_manager = PasswordArchiveManager()
