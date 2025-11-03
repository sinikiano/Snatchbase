"""
Files Router  
Handles file and system search endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.search_service import SearchService
from app.models import File

router = APIRouter()
search_service = SearchService()


@router.get("/search/systems")
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


@router.get("/files/{file_id}")
async def get_file_content(file_id: int, db: Session = Depends(get_db)):
    """Get file content by file ID"""
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
