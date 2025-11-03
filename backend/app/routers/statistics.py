"""
Statistics Router
Handles all statistical and analytics endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics"""
    return search_service.get_statistics(db)


@router.get("/stats/domains")
async def get_domain_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get top domains statistics"""
    return search_service.get_domain_statistics(db, limit)


@router.get("/stats/countries")
async def get_country_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get country statistics"""
    return search_service.get_country_statistics(db, limit)


@router.get("/stats/stealers")
async def get_stealer_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get stealer statistics"""
    return search_service.get_stealer_statistics(db, limit)


@router.get("/stats/browsers")
async def get_browser_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get browser statistics"""
    return search_service.get_browser_statistics(db, limit)


@router.get("/stats/tlds")
async def get_tld_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get TLD statistics"""
    return search_service.get_tld_statistics(db, limit)


@router.get("/stats/passwords")
async def get_password_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get top passwords statistics"""
    return search_service.get_password_statistics(db, limit)


@router.get("/stats/software")
async def get_software_stats(limit: int = 20, db: Session = Depends(get_db)):
    """Get software statistics"""
    return search_service.get_software_statistics(db, limit)
