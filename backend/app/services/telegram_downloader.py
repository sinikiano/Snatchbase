"""
Telegram Group/Channel Scraper
Downloads ZIP files from Telegram groups and channels automatically.

This service uses Telethon (Telegram MTProto API) to:
- Monitor specified groups/channels for new messages
- Detect and download ZIP files automatically
- Handle password-protected archives
- Process downloaded files through the ingestion pipeline

Requirements:
- TELEGRAM_API_ID: Get from https://my.telegram.org
- TELEGRAM_API_HASH: Get from https://my.telegram.org  
- TELEGRAM_PHONE: Your phone number with country code
- TELEGRAM_CHAT_IDS: Comma-separated list of chat IDs or usernames to monitor
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Set, Callable
from datetime import datetime, timedelta

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# Import password manager for handling protected archives
try:
    from app.services.password_archive_manager import password_manager
    PASSWORD_MANAGER_AVAILABLE = True
except ImportError:
    PASSWORD_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class TelegramScraper:
    """
    Telegram scraper that monitors groups/channels and downloads ZIP files.
    
    Usage:
        scraper = TelegramScraper(
            api_id=123456,
            api_hash="your_api_hash",
            phone="+1234567890",
            download_dir=Path("data/incoming/uploads"),
            chat_ids=["@channel1", "@group2", -1001234567890]
        )
        await scraper.start()
    """
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        download_dir: Path,
        chat_ids: List[str],
        session_name: str = "snatchbase_scraper",
        file_extensions: List[str] = None,
        max_file_size_mb: int = 500,
        process_callback: Optional[callable] = None
    ):
        if not TELETHON_AVAILABLE:
            raise ImportError(
                "Telethon is required for Telegram scraping. "
                "Install with: pip install telethon"
            )
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.download_dir = Path(download_dir)
        self.chat_ids = chat_ids
        self.session_name = session_name
        self.file_extensions = file_extensions or ['.zip', '.rar', '.7z']
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.process_callback = process_callback
        
        # Track downloaded files to avoid duplicates
        self.downloaded_files: Set[str] = set()
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'bytes_downloaded': 0,
            'start_time': None,
            'last_download': None
        }
        
        # Initialize client
        self.client: Optional[TelegramClient] = None
        
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start the Telegram scraper"""
        logger.info("🚀 Starting Telegram Scraper...")
        logger.info(f"📂 Download directory: {self.download_dir}")
        logger.info(f"📱 Monitoring {len(self.chat_ids)} chats")
        
        self.stats['start_time'] = datetime.now()
        
        # Create client
        self.client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash
        )
        
        # Connect and authenticate
        await self.client.start(phone=self.phone)
        
        logger.info("✅ Connected to Telegram")
        
        # Resolve chat IDs
        resolved_chats = []
        for chat_id in self.chat_ids:
            try:
                entity = await self.client.get_entity(chat_id)
                resolved_chats.append(entity)
                logger.info(f"  ✓ Monitoring: {getattr(entity, 'title', chat_id)}")
            except Exception as e:
                logger.error(f"  ✗ Failed to resolve chat {chat_id}: {e}")
        
        if not resolved_chats:
            logger.error("No valid chats to monitor!")
            return
        
        # Register message handler
        @self.client.on(events.NewMessage(chats=resolved_chats))
        async def handle_new_message(event):
            await self._handle_message(event)
        
        logger.info("👀 Listening for new messages...")
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """Stop the scraper"""
        if self.client:
            logger.info("🛑 Stopping Telegram Scraper...")
            await self.client.disconnect()
            logger.info("✅ Scraper stopped")
    
    async def _handle_message(self, event):
        """Handle incoming messages"""
        self.stats['messages_processed'] += 1
        message = event.message
        
        # Check if message has a document
        if not message.media or not isinstance(message.media, MessageMediaDocument):
            return
        
        document = message.media.document
        
        # Get filename
        filename = None
        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                filename = attr.file_name
                break
        
        if not filename:
            return
        
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext not in self.file_extensions:
            return
        
        # Check file size
        file_size = document.size
        if file_size > self.max_file_size:
            logger.warning(
                f"⚠️ Skipping {filename}: too large "
                f"({file_size / 1024 / 1024:.1f}MB > {self.max_file_size / 1024 / 1024}MB)"
            )
            self.stats['files_skipped'] += 1
            return
        
        # Check if already downloaded (by file ID)
        file_id = str(document.id)
        if file_id in self.downloaded_files:
            logger.debug(f"Skipping duplicate: {filename}")
            return
        
        # Download the file
        await self._download_file(message, filename, file_size, file_id)
    
    async def _download_file(self, message, filename: str, file_size: int, file_id: str):
        """Download a file from a message"""
        # Generate unique filename to avoid overwrites
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        download_path = self.download_dir / safe_filename
        
        logger.info(f"📥 Downloading: {filename} ({file_size / 1024 / 1024:.1f}MB)")
        
        try:
            # Download with progress callback
            start_time = datetime.now()
            
            await self.client.download_media(
                message,
                file=str(download_path),
                progress_callback=lambda current, total: self._download_progress(
                    filename, current, total
                )
            )
            
            # Calculate download time
            download_time = (datetime.now() - start_time).total_seconds()
            speed = file_size / download_time / 1024 / 1024 if download_time > 0 else 0
            
            logger.info(
                f"✅ Downloaded: {safe_filename} "
                f"({file_size / 1024 / 1024:.1f}MB in {download_time:.1f}s, {speed:.1f}MB/s)"
            )
            
            # Update statistics
            self.downloaded_files.add(file_id)
            self.stats['files_downloaded'] += 1
            self.stats['bytes_downloaded'] += file_size
            self.stats['last_download'] = datetime.now()
            
            # Call process callback if provided
            if self.process_callback:
                try:
                    await self.process_callback(download_path)
                except Exception as e:
                    logger.error(f"Error in process callback: {e}")
            else:
                # Default processing: check for password protection
                await self._default_process_file(download_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
            self.stats['files_skipped'] += 1
    
    async def _default_process_file(self, file_path: Path):
        """Default file processing with password protection handling"""
        if not PASSWORD_MANAGER_AVAILABLE:
            logger.info(f"✅ File ready for processing: {file_path}")
            return
        
        try:
            # Check if file is password protected
            if password_manager.is_password_protected(file_path):
                logger.info(f"🔐 {file_path.name} is password protected, trying common passwords...")
                
                # Try common passwords
                password = password_manager.try_common_passwords(file_path)
                
                if password:
                    logger.info(f"🔓 Found password for {file_path.name}: {password}")
                    
                    # Add to pending first (to use extract_with_password)
                    archive = password_manager.add_pending_archive(
                        file_path=file_path,
                        source="Telegram Scraper"
                    )
                    
                    # Extract the archive
                    result = password_manager.extract_with_password(
                        file_hash=archive.file_hash,
                        password=password
                    )
                    
                    if result['success']:
                        logger.info(f"✅ Extracted {file_path.name} to {result['output_dir']}")
                    else:
                        logger.error(f"❌ Extraction failed: {result['message']}")
                else:
                    # Add to pending archives
                    archive = password_manager.add_pending_archive(
                        file_path=file_path,
                        source="Telegram Scraper"
                    )
                    logger.warning(
                        f"⚠️ {file_path.name} requires password! "
                        f"Use /unlock {archive.file_hash} <password> in Telegram bot"
                    )
            else:
                logger.info(f"✅ {file_path.name} is not password protected, ready for ingestion")
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def _download_progress(self, filename: str, current: int, total: int):
        """Log download progress"""
        if total > 0:
            percent = current / total * 100
            if percent % 25 < 1:  # Log at 25%, 50%, 75%
                logger.debug(f"  {filename}: {percent:.0f}%")
    
    async def fetch_history(self, limit: int = 100):
        """
        Fetch recent messages from monitored chats.
        Useful for catching up on messages that were sent while offline.
        """
        if not self.client or not self.client.is_connected():
            logger.error("Client not connected!")
            return
        
        logger.info(f"📜 Fetching last {limit} messages from each chat...")
        
        for chat_id in self.chat_ids:
            try:
                entity = await self.client.get_entity(chat_id)
                chat_name = getattr(entity, 'title', str(chat_id))
                
                logger.info(f"  Fetching from: {chat_name}")
                
                async for message in self.client.iter_messages(entity, limit=limit):
                    # Process as if it were a new message
                    class FakeEvent:
                        def __init__(self, msg):
                            self.message = msg
                    
                    await self._handle_message(FakeEvent(message))
                
            except Exception as e:
                logger.error(f"  Error fetching from {chat_id}: {e}")
        
        logger.info(f"✅ History fetch complete. Downloaded {self.stats['files_downloaded']} files.")
    
    def get_stats(self) -> dict:
        """Get scraper statistics"""
        runtime = None
        if self.stats['start_time']:
            runtime = str(datetime.now() - self.stats['start_time']).split('.')[0]
        
        return {
            'status': 'running' if self.client and self.client.is_connected() else 'stopped',
            'runtime': runtime,
            'messages_processed': self.stats['messages_processed'],
            'files_downloaded': self.stats['files_downloaded'],
            'files_skipped': self.stats['files_skipped'],
            'bytes_downloaded': self.stats['bytes_downloaded'],
            'bytes_downloaded_mb': round(self.stats['bytes_downloaded'] / 1024 / 1024, 2),
            'last_download': self.stats['last_download'].isoformat() if self.stats['last_download'] else None,
            'monitored_chats': len(self.chat_ids)
        }


class TelegramDownloader:
    """
    Wrapper class for TelegramScraper that reads configuration from environment.
    This is the class referenced in run_services.py
    """
    
    def __init__(self):
        self.scraper: Optional[TelegramScraper] = None
        
        # Read configuration from environment
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.session_name = os.getenv('TELEGRAM_SESSION_NAME', 'snatchbase_scraper')
        
        # Parse chat IDs
        chat_ids_str = os.getenv('TELEGRAM_CHAT_IDS', '')
        self.chat_ids = [c.strip() for c in chat_ids_str.split(',') if c.strip()]
        
        # Download directory
        base_dir = Path(__file__).parent.parent.parent
        self.download_dir = base_dir / "data" / "incoming" / "uploads"
    
    def is_configured(self) -> bool:
        """Check if Telegram scraper is properly configured"""
        return all([
            self.api_id,
            self.api_hash,
            self.phone,
            self.chat_ids
        ])
    
    async def start(self):
        """Start the Telegram downloader"""
        if not self.is_configured():
            logger.warning("⚠️ Telegram scraper not configured. Required:")
            logger.warning("   - TELEGRAM_API_ID")
            logger.warning("   - TELEGRAM_API_HASH")
            logger.warning("   - TELEGRAM_PHONE")
            logger.warning("   - TELEGRAM_CHAT_IDS")
            return
        
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon not installed. Install with: pip install telethon")
            return
        
        self.scraper = TelegramScraper(
            api_id=int(self.api_id),
            api_hash=self.api_hash,
            phone=self.phone,
            download_dir=self.download_dir,
            chat_ids=self.chat_ids,
            session_name=self.session_name
        )
        
        await self.scraper.start()
    
    async def stop(self):
        """Stop the Telegram downloader"""
        if self.scraper:
            await self.scraper.stop()
    
    def get_stats(self) -> dict:
        """Get scraper statistics"""
        if self.scraper:
            return self.scraper.get_stats()
        return {'status': 'not_started'}


# Standalone runner for testing
async def main():
    """Run the scraper standalone"""
    from dotenv import load_dotenv
    load_dotenv()
    
    downloader = TelegramDownloader()
    
    if not downloader.is_configured():
        print("Please configure environment variables:")
        print("  TELEGRAM_API_ID=your_api_id")
        print("  TELEGRAM_API_HASH=your_api_hash")
        print("  TELEGRAM_PHONE=+1234567890")
        print("  TELEGRAM_CHAT_IDS=@channel1,@group2")
        return
    
    try:
        await downloader.start()
    except KeyboardInterrupt:
        await downloader.stop()


if __name__ == '__main__':
    asyncio.run(main())
