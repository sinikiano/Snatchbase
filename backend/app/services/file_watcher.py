"""
File watcher service - monitors directory for new ZIP files and processes them automatically
"""
import time
import logging
from pathlib import Path
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.zip_ingestion import ZipIngestionService


class ZipFileHandler(FileSystemEventHandler):
    """Handler for ZIP file events"""
    
    def __init__(self, ingestion_service: ZipIngestionService, logger: logging.Logger):
        self.ingestion_service = ingestion_service
        self.logger = logger
        self.processing_files: Set[str] = set()
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process ZIP files
        if file_path.suffix.lower() != '.zip':
            return
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processing_files:
            return
        
        self.logger.info(f"📦 New ZIP file detected: {file_path}")
        
        # Wait a bit to ensure file is fully written
        time.sleep(2)
        
        # Mark as processing
        self.processing_files.add(str(file_path))
        
        try:
            # Process the ZIP file
            db = SessionLocal()
            try:
                result = self.ingestion_service.process_zip_file(file_path, db)
                self.logger.info(f"✅ Successfully processed: {file_path}")
                self.logger.info(f"   - Devices processed: {result['devices_processed']}")
                self.logger.info(f"   - Credentials: {result['total_credentials']}")
                self.logger.info(f"   - Files: {result['total_files']}")
                
                # Delete ZIP file after successful processing to save disk space
                try:
                    file_path.unlink()
                    self.logger.info(f"🗑️ Deleted processed file: {file_path}")
                except Exception as del_err:
                    self.logger.warning(f"⚠️ Could not delete file {file_path}: {del_err}")
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"❌ Error processing {file_path}: {e}", exc_info=True)
        finally:
            # Remove from processing set
            self.processing_files.discard(str(file_path))


class FileWatcherService:
    """Service for watching directory and auto-processing ZIP files"""
    
    def __init__(self, watch_dir: Path, logger: Optional[logging.Logger] = None):
        self.watch_dir = watch_dir
        self.logger = logger or logging.getLogger(__name__)
        self.ingestion_service = ZipIngestionService(logger=self.logger)
        self.observer: Optional[Observer] = None
    
    def start(self):
        """Start watching directory"""
        # Create watch directory if it doesn't exist
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"👀 Starting file watcher on: {self.watch_dir}")
        
        # Process any existing ZIP files first
        self._process_existing_files()
        
        # Set up file system observer
        event_handler = ZipFileHandler(self.ingestion_service, self.logger)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        
        self.logger.info("✅ File watcher started")
    
    def stop(self):
        """Stop watching directory"""
        if self.observer:
            self.logger.info("🛑 Stopping file watcher")
            self.observer.stop()
            self.observer.join()
            self.logger.info("✅ File watcher stopped")
    
    def _process_existing_files(self):
        """Process any existing ZIP files in the watch directory"""
        zip_files = list(self.watch_dir.glob("*.zip"))
        
        if not zip_files:
            self.logger.info("ℹ️ No existing ZIP files to process")
            return
        
        self.logger.info(f"📦 Found {len(zip_files)} existing ZIP files to process")
        
        for zip_path in zip_files:
            try:
                self.logger.info(f"🚀 Processing existing file: {zip_path}")
                db = SessionLocal()
                try:
                    result = self.ingestion_service.process_zip_file(zip_path, db)
                    self.logger.info(f"✅ Successfully processed: {zip_path}")
                    self.logger.info(f"   - Devices processed: {result['devices_processed']}")
                    self.logger.info(f"   - Credentials: {result['total_credentials']}")
                    
                    # Delete ZIP file after successful processing to save disk space
                    try:
                        zip_path.unlink()
                        self.logger.info(f"🗑️ Deleted processed file: {zip_path}")
                    except Exception as del_err:
                        self.logger.warning(f"⚠️ Could not delete file {zip_path}: {del_err}")
                finally:
                    db.close()
            except Exception as e:
                self.logger.error(f"❌ Error processing {zip_path}: {e}", exc_info=True)
                continue
