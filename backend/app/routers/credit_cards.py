"""
Credit Cards API Router
Endpoints for credit card data from stealer logs
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import CreditCard, Device

router = APIRouter()


@router.get("/credit-cards")
async def get_credit_cards(
    device_id: Optional[str] = None,
    card_brand: Optional[str] = None,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get credit cards from stealer logs
    
    Query Parameters:
    - device_id: Filter by device ID
    - card_brand: Filter by card brand (Visa, Mastercard, etc.)
    - limit: Number of results to return
    - offset: Number of results to skip
    """
    query = db.query(CreditCard)
    
    if device_id:
        query = query.filter(CreditCard.device_id == device_id)
    
    if card_brand:
        query = query.filter(CreditCard.card_brand == card_brand)
    
    total = query.count()
    cards = query.order_by(CreditCard.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "results": [
            {
                "id": card.id,
                "device_id": card.device_id,
                "card_number_masked": card.card_number_masked,
                "expiration": card.expiration,
                "cardholder_name": card.cardholder_name,
                "card_brand": card.card_brand,
                "created_at": card.created_at.isoformat() if card.created_at else None
            }
            for card in cards
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/credit-cards/{card_id}")
async def get_credit_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific credit card"""
    card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    
    if not card:
        return {"error": "Credit card not found"}, 404
    
    return {
        "id": card.id,
        "device_id": card.device_id,
        "card_number_masked": card.card_number_masked,
        "expiration": card.expiration,
        "cardholder_name": card.cardholder_name,
        "card_brand": card.card_brand,
        "source_file": card.source_file,
        "created_at": card.created_at.isoformat() if card.created_at else None
    }


@router.get("/devices/{device_id}/credit-cards")
async def get_device_credit_cards(
    device_id: str,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all credit cards associated with a specific device"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    if not device:
        return {"error": "Device not found"}, 404
    
    query = db.query(CreditCard).filter(CreditCard.device_id == device_id)
    total = query.count()
    cards = query.order_by(CreditCard.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "device_id": device_id,
        "results": [
            {
                "id": card.id,
                "card_number_masked": card.card_number_masked,
                "expiration": card.expiration,
                "cardholder_name": card.cardholder_name,
                "card_brand": card.card_brand,
                "created_at": card.created_at.isoformat() if card.created_at else None
            }
            for card in cards
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats/credit-cards")
async def get_credit_card_stats(db: Session = Depends(get_db)):
    """Get statistics about credit cards"""
    total_cards = db.query(func.count(CreditCard.id)).scalar()
    
    # Count by brand
    brand_stats = db.query(
        CreditCard.card_brand,
        func.count(CreditCard.id).label('count')
    ).group_by(CreditCard.card_brand).all()
    
    # Devices with credit cards
    devices_with_cc = db.query(func.count(func.distinct(CreditCard.device_id))).scalar()
    
    return {
        "total_credit_cards": total_cards,
        "devices_with_cards": devices_with_cc,
        "by_brand": [
            {"brand": brand, "count": count}
            for brand, count in brand_stats
        ]
    }


@router.get("/stats/credit-card-brands")
async def get_credit_card_brands(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get credit card statistics by brand"""
    brands = db.query(
        CreditCard.card_brand,
        func.count(CreditCard.id).label('count')
    ).group_by(
        CreditCard.card_brand
    ).order_by(
        func.count(CreditCard.id).desc()
    ).limit(limit).all()
    
    return [
        {"brand": brand, "count": count}
        for brand, count in brands
    ]
