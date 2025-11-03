"""
Credentials Router
Handles credential search, filtering, and export endpoints
"""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()


@router.get("/search/credentials")
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


@router.get("/search/export")
async def export_credentials(
    q: Optional[str] = None,
    domain: Optional[str] = None,
    username: Optional[str] = None,
    browser: Optional[str] = None,
    tld: Optional[str] = None,
    stealer_name: Optional[str] = None,
    limit: int = 10000,
    db: Session = Depends(get_db)
):
    """Export credentials as email:password text file"""
    
    results, total = search_service.search_credentials_with_count(
        db=db,
        query=q,
        domain=domain,
        username=username,
        browser=browser,
        tld=tld,
        stealer_name=stealer_name,
        limit=limit,
        offset=0
    )
    
    # Format as email:password (results are Pydantic objects)
    lines = []
    for cred in results:
        if cred.username and cred.password:
            lines.append(f"{cred.username}:{cred.password}")
    
    content = "\n".join(lines)
    
    return PlainTextResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename=credentials_export.txt"
        }
    )


@router.post("/credentials/remove-duplicates")
async def remove_duplicates(
    device_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Remove duplicate credentials (keep oldest, remove newer ones)"""
    from sqlalchemy import func, and_
    from app.models import Credential
    
    try:
        # Build base query
        if device_id:
            duplicates_query = db.query(
                Credential.device_id,
                Credential.username,
                Credential.password,
                func.count(Credential.id).label('count'),
                func.min(Credential.id).label('keep_id')
            ).filter(
                Credential.device_id == device_id
            ).group_by(
                Credential.device_id,
                Credential.username,
                Credential.password
            ).having(func.count(Credential.id) > 1)
        else:
            duplicates_query = db.query(
                Credential.device_id,
                Credential.username,
                Credential.password,
                func.count(Credential.id).label('count'),
                func.min(Credential.id).label('keep_id')
            ).group_by(
                Credential.device_id,
                Credential.username,
                Credential.password
            ).having(func.count(Credential.id) > 1)
        
        duplicates = duplicates_query.all()
        
        total_removed = 0
        for dup in duplicates:
            # Find all credentials with this username+password in this device
            all_creds = db.query(Credential).filter(
                and_(
                    Credential.device_id == dup.device_id,
                    Credential.username == dup.username,
                    Credential.password == dup.password
                )
            ).all()
            
            # Delete all except the oldest (keep_id)
            for cred in all_creds:
                if cred.id != dup.keep_id:
                    db.delete(cred)
                    total_removed += 1
        
        db.commit()
        
        return {
            "success": True,
            "duplicate_groups_found": len(duplicates),
            "credentials_removed": total_removed,
            "message": f"Removed {total_removed} duplicate credentials from {len(duplicates)} groups"
        }
        
    except Exception as e:
        db.rollback()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
