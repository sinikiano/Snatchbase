#!/usr/bin/env python3
"""
Manual ZIP processing script for testing wallet extraction
"""
from pathlib import Path
from app.database import SessionLocal
from app.services.zip_ingestion import ZipIngestionService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ManualZipProcessor")

# Process ZIP file
zip_path = Path("data/incoming/uploads/test_wallets.zip")

if not zip_path.exists():
    logger.error(f"ZIP file not found: {zip_path}")
    exit(1)

logger.info(f"Processing ZIP: {zip_path}")

db = SessionLocal()
try:
    ingestion_service = ZipIngestionService(logger=logger)
    result = ingestion_service.process_zip_file(zip_path, db)
    
    logger.info("=" * 80)
    logger.info("PROCESSING RESULTS:")
    logger.info(f"  Success: {result['success']}")
    logger.info(f"  Devices found: {result['devices_found']}")
    logger.info(f"  Devices processed: {result['devices_processed']}")
    logger.info(f"  Total credentials: {result['total_credentials']}")
    logger.info(f"  Total files: {result['total_files']}")
    if 'wallets' in result:
        logger.info(f"  Total wallets: {result.get('wallets', 0)}")
    logger.info("=" * 80)
    
except Exception as e:
    logger.error(f"Error processing ZIP: {e}", exc_info=True)
finally:
    db.close()
