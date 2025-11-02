"""
Telegram File Downloader Service
Automatically downloads files from specified Telegram groups/channels
"""
import os
import asyncio
import logging
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials (get from https://my.telegram.org)
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')  # Your phone number with country code
SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'snatchbase_session')

# Download configuration
DOWNLOAD_PATH = Path(__file__).parent.parent.parent / 'data' / 'incoming' / 'uploads'
ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz']
CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS', '').split(',')  # Comma-separated chat IDs or usernames

class TelegramDownloader:
    def __init__(self):
        if not API_ID or not API_HASH:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.download_path = DOWNLOAD_PATH
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Download path: {self.download_path}")
        logger.info(f"Monitoring chats: {CHAT_IDS}")
    
    async def start(self):
        """Start the Telegram client and set up event handlers"""
        await self.client.start(phone=PHONE)
        logger.info("Telegram client started successfully")
        
        # Get information about the connected account
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        
        # Register event handler for new messages
        @self.client.on(events.NewMessage(chats=CHAT_IDS if CHAT_IDS != [''] else None))
        async def handle_new_message(event):
            await self.handle_message(event)
        
        logger.info("Event handlers registered. Listening for new files...")
        
        # Keep the client running
        await self.client.run_until_disconnected()
    
    async def handle_message(self, event):
        """Handle incoming messages and download files if applicable"""
        message = event.message
        
        # Check if message has a document (file)
        if not message.media or not hasattr(message.media, 'document'):
            return
        
        document = message.media.document
        
        # Get filename
        filename = None
        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                filename = attr.file_name
                break
        
        if not filename:
            filename = f"file_{document.id}"
        
        # Check if file extension is allowed
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.info(f"Skipping file {filename} - unsupported extension: {file_ext}")
            return
        
        # Get chat information
        chat = await event.get_chat()
        chat_name = getattr(chat, 'title', getattr(chat, 'username', 'Unknown'))
        
        logger.info(f"📥 Downloading file: {filename} from {chat_name}")
        logger.info(f"   Size: {document.size / 1024 / 1024:.2f} MB")
        
        try:
            # Download the file
            download_path = self.download_path / filename
            
            # Check if file already exists
            if download_path.exists():
                logger.warning(f"File {filename} already exists, skipping download")
                return
            
            # Download with progress callback
            await self.client.download_media(
                message,
                file=str(download_path),
                progress_callback=self.progress_callback
            )
            
            logger.info(f"✅ Successfully downloaded: {filename}")
            logger.info(f"   Saved to: {download_path}")
            
        except Exception as e:
            logger.error(f"❌ Error downloading {filename}: {str(e)}")
    
    def progress_callback(self, current, total):
        """Progress callback for download"""
        percentage = (current / total) * 100
        if percentage % 10 < 0.1:  # Log every 10%
            logger.info(f"   Progress: {percentage:.1f}% ({current / 1024 / 1024:.2f}/{total / 1024 / 1024:.2f} MB)")
    
    async def download_history(self, chat_id, limit=10):
        """Download files from chat history (useful for initial setup)"""
        logger.info(f"Downloading history from chat: {chat_id}")
        
        try:
            async for message in self.client.iter_messages(chat_id, limit=limit):
                if message.media and hasattr(message.media, 'document'):
                    # Create a mock event to reuse the handler
                    class MockEvent:
                        def __init__(self, msg):
                            self.message = msg
                        async def get_chat(self):
                            return await self.message.get_chat()
                    
                    await self.handle_message(MockEvent(message))
                    await asyncio.sleep(1)  # Rate limiting
        
        except Exception as e:
            logger.error(f"Error downloading history: {str(e)}")
    
    def stop(self):
        """Stop the client"""
        if self.client.is_connected():
            self.client.disconnect()
            logger.info("Telegram client disconnected")


async def main():
    """Main function to run the downloader"""
    downloader = TelegramDownloader()
    
    try:
        await downloader.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        downloader.stop()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        downloader.stop()


if __name__ == '__main__':
    asyncio.run(main())
