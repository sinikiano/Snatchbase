"""
Upload Router
Handles ZIP file uploads for processing stealer logs
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.database import get_db
from app.services.zip_ingestion import ZipIngestionService

router = APIRouter()

# Get upload directory from environment or use default
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/incoming/uploads"))


def process_upload_background(zip_path: Path):
    """Background task to process uploaded ZIP file"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = ZipIngestionService()
        result = service.process_zip_file(zip_path, db)
        
        # Optionally move processed file to a processed folder
        processed_dir = zip_path.parent.parent / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(zip_path), str(processed_dir / zip_path.name))
        
        return result
    except Exception as e:
        print(f"Error processing upload: {e}")
        raise
    finally:
        db.close()


@router.post("/upload")
async def upload_zip_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_now: bool = True
):
    """
    Upload a ZIP file containing stealer logs for processing.
    
    The file will be saved to the uploads directory and optionally
    processed immediately in the background.
    
    Parameters:
    - file: The ZIP file to upload
    - process_now: If True, process the file immediately in the background
    
    Returns upload info and processing status.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=400, 
            detail="Only ZIP files are allowed"
        )
    
    # Create upload directory if it doesn't exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to avoid collisions
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        response = {
            "message": "File uploaded successfully",
            "filename": safe_filename,
            "original_filename": file.filename,
            "size_bytes": file_path.stat().st_size,
            "path": str(file_path),
            "status": "uploaded"
        }
        
        # Process in background if requested
        if process_now:
            background_tasks.add_task(process_upload_background, file_path)
            response["status"] = "processing"
            response["message"] = "File uploaded and processing started"
        
        return response
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


@router.get("/uploads")
async def list_uploads(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all upload records.
    
    Parameters:
    - status: Filter by status (processing, completed, failed)
    - limit: Number of results to return
    - offset: Number of results to skip
    """
    from app.models import Upload
    from sqlalchemy import desc
    
    query = db.query(Upload)
    
    if status:
        query = query.filter(Upload.status == status)
    
    total = query.count()
    uploads = query.order_by(desc(Upload.created_at)).offset(offset).limit(limit).all()
    
    return {
        "results": [
            {
                "id": u.id,
                "upload_id": u.upload_id,
                "filename": u.filename,
                "status": u.status,
                "devices_found": u.devices_found,
                "devices_processed": u.devices_processed,
                "devices_skipped": u.devices_skipped,
                "total_credentials": u.total_credentials,
                "total_files": u.total_files,
                "error_message": u.error_message,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "completed_at": u.completed_at.isoformat() if u.completed_at else None
            }
            for u in uploads
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/uploads/{upload_id}")
async def get_upload(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific upload"""
    from app.models import Upload
    
    upload = db.query(Upload).filter(Upload.upload_id == upload_id).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return {
        "id": upload.id,
        "upload_id": upload.upload_id,
        "filename": upload.filename,
        "status": upload.status,
        "devices_found": upload.devices_found,
        "devices_processed": upload.devices_processed,
        "devices_skipped": upload.devices_skipped,
        "total_credentials": upload.total_credentials,
        "total_files": upload.total_files,
        "error_message": upload.error_message,
        "created_at": upload.created_at.isoformat() if upload.created_at else None,
        "completed_at": upload.completed_at.isoformat() if upload.completed_at else None
    }
