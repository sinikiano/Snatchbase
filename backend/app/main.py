"""
Snatchbase - Stealer Log Aggregator API
A modern stealer log search engine and aggregator
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import logging

from app.database import get_db, engine
from app.models import Base
from app.schemas import CredentialResponse, SystemResponse
from app.services.search_service import SearchService
from app.services.file_watcher import FileWatcherService
from app.routers import wallets

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Snatchbase API",
    description="Stealer Log Aggregator and Search Engine",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wallets.router, prefix="/api", tags=["wallets"])

search_service = SearchService()

# Global file watcher instance
file_watcher: Optional[FileWatcherService] = None

@app.on_event("startup")
async def startup_event():
    """Startup event - initialize file watcher for automated ZIP ingestion"""
    global file_watcher
    
    # Set up logging
    logger = logging.getLogger("ZipIngestion")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Set up file watcher for automated ingestion
    watch_dir = Path("data/incoming/uploads")
    logger.info(f"🚀 Starting automated ZIP ingestion service")
    logger.info(f"📁 Watch directory: {watch_dir.absolute()}")
    
    try:
        file_watcher = FileWatcherService(watch_dir=watch_dir, logger=logger)
        file_watcher.start()
        logger.info("✅ ZIP ingestion service started successfully")
        logger.info("💡 Drop ZIP files into the watch directory for automatic processing")
    except Exception as e:
        logger.error(f"❌ Failed to start ZIP ingestion service: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - stop file watcher"""
    global file_watcher
    if file_watcher:
        file_watcher.stop()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Snatchbase API - Stealer Log Aggregator"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "snatchbase-api"}


@app.get("/search/credentials")
async def search_credentials(
    q: Optional[str] = None,
    domain: Optional[str] = None,
    username: Optional[str] = None,
    browser: Optional[str] = None,
    tld: Optional[str] = None,
    stealer_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Search credentials with filters (enhanced with browser, TLD, and stealer)"""
    
    results, total = search_service.search_credentials_with_count(
        db=db,
        query=q,
        domain=domain,
        username=username,
        browser=browser,
        tld=tld,
        stealer_name=stealer_name,
        limit=limit,
        offset=offset
    )
    
    return {
        "results": results,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/search/systems")
async def search_systems(
    q: Optional[str] = None,
    country: Optional[str] = None,
    ip_address: Optional[str] = None,
    computer_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Search systems with filters"""
    
    results, total = search_service.search_systems_with_count(
        db=db,
        query=q,
        country=country,
        ip_address=ip_address,
        computer_name=computer_name,
        limit=limit,
        offset=offset
    )
    
    return {
        "results": results,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics"""
    return search_service.get_statistics(db)

@app.get("/stats/stealers")
async def get_stealer_statistics(limit: int = 20, db: Session = Depends(get_db)):
    """Get stealer statistics"""
    return search_service.get_stealer_statistics(db, limit)

@app.get("/stats/domains")
async def get_domain_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get top domains statistics"""
    return search_service.get_domain_statistics(db, limit)

@app.get("/stats/countries")
async def get_country_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get country statistics"""
    return search_service.get_country_statistics(db, limit)

@app.get("/stats/stealers")
async def get_stealer_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get stealer statistics"""
    return search_service.get_stealer_statistics(db, limit)

# New endpoints for enhanced functionality

@app.get("/devices")
async def list_devices(
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all devices with optional search"""
    devices, total = search_service.search_devices(db, query=q, limit=limit, offset=offset)
    
    return {
        "results": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "device_name": d.device_name,
                "hostname": d.hostname,
                "ip_address": d.ip_address,
                "country": d.country,
                "antivirus": d.antivirus,
                "infection_date": d.infection_date,
                "upload_batch": d.upload_batch,
                "total_files": d.total_files,
                "total_credentials": d.total_credentials,
                "total_domains": d.total_domains,
                "total_urls": d.total_urls,
                "created_at": d.created_at,
            }
            for d in devices
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/devices/{device_id}")
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get device details by numeric ID"""
    from app.models import Device
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "id": device.id,
        "device_id": device.device_id,
        "device_name": device.device_name,
        "hostname": device.hostname,
        "ip_address": device.ip_address,
        "country": device.country,
        "language": device.language,
        "os_version": device.os_version,
        "username": device.username,
        "infection_date": device.infection_date,
        "antivirus": device.antivirus,
        "hwid": device.hwid,
        "upload_batch": device.upload_batch,
        "total_files": device.total_files,
        "total_credentials": device.total_credentials,
        "total_domains": device.total_domains,
        "total_urls": device.total_urls,
        "upload_date": device.upload_date,
        "created_at": device.created_at,
    }

@app.get("/devices/{device_id}/credentials")
async def get_device_credentials(
    device_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get credentials for a specific device by numeric ID"""
    from app.models import Credential, Device
    
    # Check if device exists and get its device_id string
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get credentials using the device_id string
    query = db.query(Credential).filter(Credential.device_id == device.device_id)
    total = query.count()
    credentials = query.order_by(Credential.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "results": [CredentialResponse.from_orm(c) for c in credentials],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/devices/{device_id}/files")
async def get_device_files(
    device_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get file tree for a specific device by numeric ID"""
    from app.models import File, Device
    
    # Check if device exists and get its device_id string
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get files using the device_id string
    query = db.query(File).filter(File.device_id == device.device_id)
    total = query.count()
    files = query.offset(offset).limit(limit).all()
    
    return {
        "results": [
            {
                "id": f.id,
                "file_path": f.file_path,
                "file_name": f.file_name,
                "parent_path": f.parent_path,
                "is_directory": f.is_directory,
                "file_size": f.file_size,
                "has_content": f.content is not None,
            }
            for f in files
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/files/{file_id}")
async def get_file_content(file_id: int, db: Session = Depends(get_db)):
    """Get file content by file ID"""
    from app.models import File
    
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "id": file.id,
        "file_path": file.file_path,
        "file_name": file.file_name,
        "file_size": file.file_size,
        "is_directory": file.is_directory,
        "content": file.content,
    }

@app.get("/devices/{device_id}/software")
async def get_device_software(
    device_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get installed software for a specific device"""
    from app.models import Software
    
    # Check if device exists
    device = search_service.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get software
    query = db.query(Software).filter(Software.device_id == device_id)
    total = query.count()
    software = query.offset(offset).limit(limit).all()
    
    return {
        "results": [
            {
                "id": s.id,
                "software_name": s.software_name,
                "version": s.version,
                "source_file": s.source_file,
            }
            for s in software
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats/browsers")
async def get_browser_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get browser statistics"""
    return search_service.get_browser_statistics(db, limit)

@app.get("/stats/tlds")
async def get_tld_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get TLD statistics"""
    return search_service.get_tld_statistics(db, limit)

@app.get("/stats/passwords")
async def get_password_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get top passwords statistics"""
    return search_service.get_password_statistics(db, limit)

@app.get("/stats/software")
async def get_software_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get software statistics"""
    return search_service.get_software_statistics(db, limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
