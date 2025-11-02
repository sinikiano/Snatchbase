"""
API endpoints for wallet management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import Wallet, Device
from app.schemas import WalletResponse, WalletStats

router = APIRouter()


@router.get("/devices/{device_id}/wallets", response_model=List[WalletResponse])
async def get_device_wallets(
    device_id: int,
    wallet_type: Optional[str] = None,
    has_balance: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all wallets for a specific device"""
    query = db.query(Wallet).filter(Wallet.device_id == device_id)
    
    if wallet_type:
        query = query.filter(Wallet.wallet_type == wallet_type.upper())
    
    if has_balance is not None:
        query = query.filter(Wallet.has_balance == has_balance)
    
    wallets = query.order_by(Wallet.balance.desc()).all()
    return wallets


@router.get("/wallets", response_model=List[WalletResponse])
async def search_wallets(
    wallet_type: Optional[str] = None,
    has_balance: Optional[bool] = None,
    min_balance: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search wallets with filters"""
    query = db.query(Wallet)
    
    if wallet_type:
        query = query.filter(Wallet.wallet_type == wallet_type.upper())
    
    if has_balance is not None:
        query = query.filter(Wallet.has_balance == has_balance)
    
    if min_balance is not None:
        query = query.filter(Wallet.balance >= Decimal(str(min_balance)))
    
    total = query.count()
    wallets = query.order_by(Wallet.balance.desc()).offset(skip).limit(limit).all()
    
    return wallets


@router.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific wallet by ID"""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return wallet


@router.get("/stats/wallets", response_model=WalletStats)
async def get_wallet_stats(db: Session = Depends(get_db)):
    """Get wallet statistics"""
    from sqlalchemy import func
    
    # Total wallets
    total_wallets = db.query(func.count(Wallet.id)).scalar()
    
    # Wallets with balance
    wallets_with_balance = db.query(func.count(Wallet.id)).filter(Wallet.has_balance == True).scalar()
    
    # Total value in USD
    total_value_usd = db.query(func.sum(Wallet.balance_usd)).filter(Wallet.balance_usd.isnot(None)).scalar() or Decimal(0)
    
    # Breakdown by wallet type
    wallet_type_breakdown = db.query(
        Wallet.wallet_type,
        func.count(Wallet.id).label('count'),
        func.sum(Wallet.balance_usd).label('total_usd')
    ).group_by(Wallet.wallet_type).all()
    
    breakdown = {}
    for wallet_type, count, total_usd in wallet_type_breakdown:
        breakdown[wallet_type] = {
            'count': count,
            'total_usd': float(total_usd or 0)
        }
    
    # Top wallets by balance
    top_wallets = db.query(Wallet).filter(Wallet.has_balance == True).order_by(Wallet.balance_usd.desc()).limit(10).all()
    
    return {
        'total_wallets': total_wallets,
        'wallets_with_balance': wallets_with_balance,
        'total_value_usd': float(total_value_usd),
        'breakdown_by_type': breakdown,
        'top_wallets': [
            {
                'id': w.id,
                'wallet_type': w.wallet_type,
                'address': w.address,
                'balance': float(w.balance),
                'balance_usd': float(w.balance_usd or 0)
            }
            for w in top_wallets
        ]
    }


@router.post("/wallets/check-balance")
async def trigger_balance_check(
    wallet_ids: Optional[List[int]] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger balance check for wallets
    This is a background task in production
    """
    from app.services.wallet_balance_checker import WalletBalanceChecker
    from app.services.wallet_parser import WalletInfo
    import asyncio
    from hashlib import sha256
    
    query = db.query(Wallet)
    
    if wallet_ids:
        query = query.filter(Wallet.id.in_(wallet_ids))
    elif device_id:
        query = query.filter(Wallet.device_id == device_id)
    else:
        # Check only wallets that haven't been checked recently
        query = query.filter(
            (Wallet.last_checked.is_(None)) |
            (Wallet.last_checked < datetime.utcnow())
        ).limit(100)
    
    wallets = query.all()
    
    if not wallets:
        return {"message": "No wallets to check"}
    
    # Convert to WalletInfo objects
    wallet_infos = [
        WalletInfo(
            wallet_type=w.wallet_type,
            address=w.address,
            path=w.path
        )
        for w in wallets if w.address
    ]
    
    # Check balances
    async with WalletBalanceChecker() as checker:
        balances = await checker.check_multiple_balances(wallet_infos)
    
    # Update database
    updated_count = 0
    for balance in balances:
        wallet = db.query(Wallet).filter(Wallet.address == balance.address).first()
        if wallet:
            wallet.balance = balance.balance
            wallet.balance_usd = balance.balance_usd
            wallet.last_checked = datetime.utcnow()
            wallet.has_balance = balance.balance > 0
            updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Checked {len(balances)} wallets",
        "updated": updated_count,
        "total_requested": len(wallets)
    }
