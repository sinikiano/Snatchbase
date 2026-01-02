"""
Telegram Auto-Scraper Service
Downloads RAR/ZIP files from configured Telegram groups
Notifies user via bot for password-protected files
Converts RAR to ZIP for file watcher processing
"""
import asyncio
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from collections import deque

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename


@dataclass
class DownloadTask:
    """Represents a file download task"""
    message_id: int
    channel_id: int
    filename: str
    size_mb: float
    status: str = "pending"  # pending, downloading, password_required, converting, completed, failed
    password: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class TelegramScraperService:
    """Auto-scraper service for Telegram groups"""
    
    def __init__(self, bot_notifier=None):
        self.logger = logging.getLogger("telegram_scraper")
        self.logger.setLevel(logging.INFO)
        
        # Telegram client settings
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.phone = os.getenv("TELEGRAM_PHONE", "")
        
        # Channels to monitor (with -100 prefix for supergroups)
        self.channels = [
            -1001525224025,   # SNATCH LOGS CLOUD
            -1003583523754,   # @darkside_hub_free (darkside hub)
        ]
        
        # Directories
        self.download_dir = Path("data/incoming/uploads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.client: Optional[TelegramClient] = None
        self.bot_notifier = bot_notifier
        self.running = False
        self.processed_messages: set = set()
        self.pending_passwords: Dict[str, DownloadTask] = {}  # filename -> task
        self.download_queue: deque = deque()
        self.logs: deque = deque(maxlen=100)  # Keep last 100 log entries
        
        # Load processed messages from file
        self._load_processed_messages()
    
    def _load_processed_messages(self):
        """Load previously processed message IDs"""
        state_file = Path("data/scraper_state.txt")
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    for line in f:
                        parts = line.strip().split(":")
                        if len(parts) == 2:
                            self.processed_messages.add(f"{parts[0]}:{parts[1]}")
            except Exception as e:
                self.log(f"Error loading state: {e}", "ERROR")
    
    def _save_processed_message(self, channel_id: int, message_id: int):
        """Save processed message ID"""
        key = f"{channel_id}:{message_id}"
        self.processed_messages.add(key)
        
        state_file = Path("data/scraper_state.txt")
        try:
            with open(state_file, "a") as f:
                f.write(f"{key}\n")
        except Exception as e:
            self.log(f"Error saving state: {e}", "ERROR")
    
    def _is_processed(self, channel_id: int, message_id: int) -> bool:
        """Check if message was already processed"""
        return f"{channel_id}:{message_id}" in self.processed_messages
    
    def log(self, message: str, level: str = "INFO"):
        """Log message and store in memory"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    async def notify_bot(self, message: str):
        """Send notification via Telegram bot"""
        if self.bot_notifier:
            try:
                await self.bot_notifier(message)
            except Exception as e:
                self.log(f"Failed to send bot notification: {e}", "ERROR")
    
    async def start(self):
        """Start the scraper service"""
        if not self.api_id or not self.api_hash:
            self.log("Telegram API credentials not configured", "ERROR")
            return
        
        self.log("🚀 Starting Telegram Scraper Service")
        await self.notify_bot("🚀 *Telegram Scraper Started*\nMonitoring channels for new files...")
        
        self.running = True
        
        # Initialize Telethon client - use existing session if available
        session_name = "snatchbase_scraper"
        
        # Check if session file exists in different locations
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent
        
        session_path = backend_dir / f"{session_name}.session"
        if session_path.exists():
            session_name = str(backend_dir / session_name)
        
        self.client = TelegramClient(
            session_name,
            self.api_id,
            self.api_hash
        )
        
        await self.client.start(phone=self.phone)
        self.log("✅ Connected to Telegram")
        
        # Start daily checker as background task
        asyncio.create_task(self.run_daily_checker())
        
        # Start monitoring loop
        while self.running:
            try:
                await self._scan_channels()
                await self._process_download_queue()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.log(f"Error in scan loop: {e}", "ERROR")
                await asyncio.sleep(30)
        
        await self.client.disconnect()
    
    async def stop(self):
        """Stop the scraper service"""
        self.running = False
        self.log("🛑 Stopping Telegram Scraper Service")
        await self.notify_bot("🛑 *Telegram Scraper Stopped*")
    
    async def _scan_channels(self):
        """Scan all configured channels for new files"""
        for channel_id in self.channels:
            try:
                await self._scan_channel(channel_id)
            except Exception as e:
                self.log(f"Error scanning channel {channel_id}: {e}", "ERROR")
        
        # Send queue status notification
        await self._send_queue_status()
    
    async def _scan_channel(self, channel_id: int):
        """Scan a single channel for new files"""
        try:
            entity = await self.client.get_entity(channel_id)
            channel_name = getattr(entity, 'title', str(channel_id))
            
            async for message in self.client.iter_messages(entity, limit=20):
                if self._is_processed(channel_id, message.id):
                    continue
                
                if not message.media or not isinstance(message.media, MessageMediaDocument):
                    continue
                
                doc = message.media.document
                filename = None
                
                for attr in doc.attributes:
                    if isinstance(attr, DocumentAttributeFilename):
                        filename = attr.file_name
                        break
                
                if not filename:
                    continue
                
                # Check if it's a RAR or ZIP file
                ext = filename.lower().split(".")[-1]
                if ext not in ["rar", "zip"]:
                    continue
                
                size_mb = doc.size / 1024 / 1024
                
                # Skip files we already have
                download_path = self.download_dir / filename
                if download_path.exists():
                    self._save_processed_message(channel_id, message.id)
                    continue
                
                # Add to download queue
                task = DownloadTask(
                    message_id=message.id,
                    channel_id=channel_id,
                    filename=filename,
                    size_mb=size_mb
                )
                
                self.download_queue.append(task)
                self.log(f"📥 Queued: {filename} ({size_mb:.1f}MB) from {channel_name}")
                
                await self.notify_bot(
                    f"📥 *New File Found*\n"
                    f"📁 `{filename}`\n"
                    f"📊 Size: {size_mb:.1f}MB\n"
                    f"📺 Channel: {channel_name}\n"
                    f"⏳ Added to download queue"
                )
        
        except ValueError as e:
            if "Could not find" in str(e) or "No user has" in str(e):
                self.log(f"Channel {channel_id} not accessible - skipping", "WARNING")
            else:
                raise
        except Exception as e:
            self.log(f"Error scanning channel {channel_id}: {e}", "ERROR")
    
    async def _process_download_queue(self):
        """Process pending downloads"""
        while self.download_queue:
            task = self.download_queue.popleft()
            await self._download_file(task)
    
    async def _send_queue_status(self):
        """Send queue status notification to Telegram bot"""
        queued = len(self.download_queue)
        
        if queued == 0:
            return  # No notification if queue is empty
        
        # Calculate total size
        total_size = sum(task.size_mb for task in self.download_queue)
        
        # Build file list
        file_list = []
        for i, task in enumerate(self.download_queue, 1):
            file_list.append(f"{i}. `{task.filename}` ({task.size_mb:.1f}MB)")
        
        files_str = "\n".join(file_list[:10])  # Limit to first 10 files
        if queued > 10:
            files_str += f"\n... and {queued - 10} more files"
        
        await self.notify_bot(
            f"📋 *Download Queue Status*\n\n"
            f"📥 Files in queue: {queued}\n"
            f"💾 Total size: {total_size:.1f}MB\n\n"
            f"*Pending Downloads:*\n{files_str}"
        )
        self.log(f"📋 Queue status: {queued} files ({total_size:.1f}MB) pending")
    
    async def _download_file(self, task: DownloadTask):
        """Download a single file"""
        self.log(f"⬇️ Downloading: {task.filename}")
        await self.notify_bot(f"⬇️ *Downloading*\n`{task.filename}` ({task.size_mb:.1f}MB)")
        
        task.status = "downloading"
        
        try:
            entity = await self.client.get_entity(task.channel_id)
            message = await self.client.get_messages(entity, ids=task.message_id)
            
            if not message or not message.media:
                task.status = "failed"
                task.error = "Message not found"
                return
            
            download_path = self.download_dir / task.filename
            
            # Download with progress
            await self.client.download_media(
                message,
                file=str(download_path)
            )
            
            self._save_processed_message(task.channel_id, task.message_id)
            self.log(f"✅ Downloaded: {task.filename}")
            
            # Check if password protected
            is_protected = await self._check_password_protected(download_path)
            
            if is_protected:
                task.status = "password_required"
                self.pending_passwords[task.filename] = task
                
                await self.notify_bot(
                    f"🔒 *Password Required*\n"
                    f"📁 `{task.filename}`\n\n"
                    f"Please reply with the password using:\n"
                    f"`/password {task.filename} YOUR_PASSWORD`"
                )
                self.log(f"🔒 Password required: {task.filename}")
            else:
                # Convert RAR to ZIP if needed
                await self._process_archive(download_path, task)
                
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.log(f"❌ Download failed: {task.filename} - {e}", "ERROR")
            await self.notify_bot(f"❌ *Download Failed*\n`{task.filename}`\nError: {e}")
    
    async def _check_password_protected(self, file_path: Path) -> bool:
        """Check if archive is password protected"""
        ext = file_path.suffix.lower()
        
        try:
            if ext == ".rar":
                # Use unrar to test
                result = subprocess.run(
                    ["unrar", "t", "-p-", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                # If password error in output
                if "password" in result.stderr.lower() or result.returncode != 0:
                    if "password" in result.stderr.lower() or "encrypted" in result.stderr.lower():
                        return True
                        
            elif ext == ".zip":
                # Use 7z to test
                result = subprocess.run(
                    ["7z", "t", "-p", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if "wrong password" in result.stdout.lower() or "encrypted" in result.stdout.lower():
                    return True
                    
        except subprocess.TimeoutExpired:
            self.log(f"Timeout checking password for {file_path.name}", "WARNING")
        except Exception as e:
            self.log(f"Error checking password: {e}", "ERROR")
        
        return False
    
    async def provide_password(self, filename: str, password: str) -> str:
        """Provide password for a protected archive"""
        if filename not in self.pending_passwords:
            return f"❌ No pending password request for `{filename}`"
        
        task = self.pending_passwords[filename]
        task.password = password
        
        file_path = self.download_dir / filename
        
        if not file_path.exists():
            del self.pending_passwords[filename]
            return f"❌ File not found: `{filename}`"
        
        self.log(f"🔑 Attempting password for: {filename}")
        
        # Try to extract with password
        success = await self._extract_with_password(file_path, password)
        
        if success:
            del self.pending_passwords[filename]
            await self._process_archive(file_path, task, password)
            return f"✅ Password accepted for `{filename}`\nProcessing archive..."
        else:
            return f"❌ Wrong password for `{filename}`\nPlease try again."
    
    async def _extract_with_password(self, file_path: Path, password: str) -> bool:
        """Test if password is correct"""
        ext = file_path.suffix.lower()
        
        try:
            if ext == ".rar":
                result = subprocess.run(
                    ["unrar", "t", f"-p{password}", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
                
            elif ext == ".zip":
                result = subprocess.run(
                    ["7z", "t", f"-p{password}", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return "Everything is Ok" in result.stdout
                
        except Exception as e:
            self.log(f"Error testing password: {e}", "ERROR")
        
        return False
    
    async def _process_archive(self, file_path: Path, task: DownloadTask, password: str = None):
        """Process archive - convert RAR to ZIP if needed"""
        ext = file_path.suffix.lower()
        
        if ext == ".rar":
            task.status = "converting"
            self.log(f"🔄 Converting RAR to ZIP: {file_path.name}")
            await self.notify_bot(f"🔄 *Converting RAR to ZIP*\n`{file_path.name}`")
            
            # Convert RAR to ZIP
            zip_path = await self._convert_rar_to_zip(file_path, password)
            
            if zip_path and zip_path.exists():
                task.status = "completed"
                self.log(f"✅ Converted: {zip_path.name}")
                
                # Remove original RAR
                file_path.unlink()
                
                await self.notify_bot(
                    f"✅ *Ready for Processing*\n"
                    f"📁 `{zip_path.name}`\n"
                    f"File watcher will process automatically"
                )
            else:
                task.status = "failed"
                task.error = "Conversion failed"
                self.log(f"❌ Conversion failed: {file_path.name}", "ERROR")
                await self.notify_bot(f"❌ *Conversion Failed*\n`{file_path.name}`")
        else:
            # ZIP file - ready for processing
            task.status = "completed"
            self.log(f"✅ Ready for processing: {file_path.name}")
            await self.notify_bot(
                f"✅ *Ready for Processing*\n"
                f"📁 `{file_path.name}`\n"
                f"File watcher will process automatically"
            )
    
    async def _convert_rar_to_zip(self, rar_path: Path, password: str = None) -> Optional[Path]:
        """Convert RAR file to ZIP format"""
        temp_dir = self.download_dir / f"temp_{rar_path.stem}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Extract RAR
            cmd = ["unrar", "x", "-o+"]
            if password:
                cmd.append(f"-p{password}")
            else:
                cmd.append("-p-")
            cmd.extend([str(rar_path), str(temp_dir) + "/"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                self.log(f"RAR extraction failed: {result.stderr}", "ERROR")
                return None
            
            # Create ZIP
            zip_path = self.download_dir / f"{rar_path.stem}.zip"
            
            # Use 7z to create ZIP (faster and better compression)
            result = subprocess.run(
                ["7z", "a", "-tzip", str(zip_path), f"{temp_dir}/*"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                self.log(f"ZIP creation failed: {result.stderr}", "ERROR")
                return None
            
            return zip_path
            
        except subprocess.TimeoutExpired:
            self.log(f"Conversion timeout for {rar_path.name}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Conversion error: {e}", "ERROR")
            return None
        finally:
            # Clean up temp directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def get_status(self) -> str:
        """Get current scraper status"""
        pending = len(self.pending_passwords)
        queued = len(self.download_queue)
        
        status = f"""
📊 *Telegram Scraper Status*

🔄 Running: {'Yes' if self.running else 'No'}
📺 Channels: {len(self.channels)}
📥 Queued Downloads: {queued}
🔒 Pending Passwords: {pending}
📝 Processed Files: {len(self.processed_messages)}

"""
        
        if pending > 0:
            status += "*Files Awaiting Password:*\n"
            for filename in self.pending_passwords:
                status += f"• `{filename}`\n"
        
        return status
    
    def get_logs(self, count: int = 20) -> str:
        """Get recent logs"""
        logs = list(self.logs)[-count:]
        if not logs:
            return "📝 No logs available"
        
        return "📝 *Recent Logs*\n```\n" + "\n".join(logs) + "\n```"
    
    async def daily_check(self) -> str:
        """Check all channels for missing files (files not yet downloaded)"""
        if not self.client:
            return "❌ Client not initialized"
        
        self.log("🔍 Running daily check for missing files...")
        await self.notify_bot("🔍 *Daily File Check Started*\nScanning channels for new files...")
        
        missing_files = []
        
        for channel_id in self.channels:
            try:
                entity = await self.client.get_entity(channel_id)
                channel_name = getattr(entity, 'title', str(channel_id))
                
                # Scan last 100 messages for this check
                async for message in self.client.iter_messages(entity, limit=100):
                    if not message.media or not isinstance(message.media, MessageMediaDocument):
                        continue
                    
                    doc = message.media.document
                    filename = None
                    
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            filename = attr.file_name
                            break
                    
                    if not filename:
                        continue
                    
                    # Check if it's a RAR or ZIP file
                    ext = filename.lower().split(".")[-1]
                    if ext not in ["rar", "zip"]:
                        continue
                    
                    # Check if already downloaded
                    download_path = self.download_dir / filename
                    zip_path = self.download_dir / f"{Path(filename).stem}.zip"
                    
                    # Skip if file exists (either original or converted)
                    if download_path.exists() or zip_path.exists():
                        continue
                    
                    # Skip if already processed
                    if self._is_processed(channel_id, message.id):
                        continue
                    
                    size_mb = doc.size / 1024 / 1024
                    missing_files.append({
                        'filename': filename,
                        'size_mb': size_mb,
                        'channel': channel_name,
                        'message_id': message.id,
                        'channel_id': channel_id
                    })
                    
            except Exception as e:
                self.log(f"Error checking channel {channel_id}: {e}", "ERROR")
        
        # Report results
        if missing_files:
            self.log(f"🔍 Found {len(missing_files)} missing files")
            
            # Build report
            report = f"🔍 *Daily Check Complete*\n\n"
            report += f"📊 Found {len(missing_files)} files not yet downloaded:\n\n"
            
            total_size = sum(f['size_mb'] for f in missing_files)
            
            for i, f in enumerate(missing_files[:15], 1):
                report += f"{i}. `{f['filename']}`\n"
                report += f"   📺 {f['channel']} | 💾 {f['size_mb']:.1f}MB\n"
            
            if len(missing_files) > 15:
                report += f"\n... and {len(missing_files) - 15} more files"
            
            report += f"\n\n💾 *Total: {total_size:.1f}MB*"
            report += f"\n\n_Use /scraper to start downloading_"
            
            await self.notify_bot(report)
            
            # Add missing files to download queue
            for f in missing_files:
                task = DownloadTask(
                    message_id=f['message_id'],
                    channel_id=f['channel_id'],
                    filename=f['filename'],
                    size_mb=f['size_mb']
                )
                self.download_queue.append(task)
            
            return report
        else:
            self.log("✅ No missing files found")
            await self.notify_bot("✅ *Daily Check Complete*\nNo missing files found - all files are downloaded!")
            return "✅ No missing files found"
    
    async def run_daily_checker(self):
        """Background task that runs daily check every 24 hours"""
        self.log("📅 Daily checker started - will check for missing files every 24 hours")
        
        while self.running:
            # Wait 24 hours (check at startup, then every 24h)
            # First run after 1 hour to let initial scan complete
            await asyncio.sleep(3600)  # 1 hour
            
            if not self.running:
                break
            
            try:
                await self.daily_check()
            except Exception as e:
                self.log(f"Daily check error: {e}", "ERROR")
            
            # Wait remaining 23 hours
            for _ in range(23):
                if not self.running:
                    break
                await asyncio.sleep(3600)  # 1 hour


# Global instance
scraper_service: Optional[TelegramScraperService] = None


def get_scraper_service() -> TelegramScraperService:
    """Get or create the scraper service instance"""
    global scraper_service
    if scraper_service is None:
        scraper_service = TelegramScraperService()
    return scraper_service
