"""
Wallet Balance Checker Service
Automatically checks cryptocurrency wallet balances
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.database import SessionLocal
from app.models import Wallet
from app.services.blockchain_api import (
    BitcoinAPI,
    EthereumAPI,
    PolygonAPI,
    BinanceSmartChainAPI,
    CryptoCompareAPI
)

logger = logging.getLogger(__name__)


class WalletBalanceChecker:
    """Service for checking cryptocurrency wallet balances"""
    
    def __init__(self):
        self.btc_api = BitcoinAPI()
        self.eth_api = EthereumAPI()
        self.matic_api = PolygonAPI()
        self.bnb_api = BinanceSmartChainAPI()
        self.price_api = CryptoCompareAPI()
        
        # API keys (optional - set via environment variables)
        self.etherscan_key = None
        self.polygonscan_key = None
        self.bscscan_key = None
    
    async def check_wallet_balance(self, wallet_id: int) -> Dict[str, Any]:
        """
        Check balance for a single wallet by ID
        Returns dict with balance information
        """
        db = SessionLocal()
        try:
            # Get wallet from database
            wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
            
            if not wallet:
                return {
                    "success": False,
                    "error": "Wallet not found",
                    "wallet_id": wallet_id
                }
            
            if not wallet.address:
                return {
                    "success": False,
                    "error": "No address available",
                    "wallet_id": wallet.id
                }
            
            wallet_type = wallet.wallet_type.upper()
            
            # Get balance based on wallet type
            if wallet_type in ["BTC", "BITCOIN"]:
                result = await self.btc_api.get_balance(wallet.address)
            elif wallet_type in ["ETH", "ETHEREUM"]:
                result = await self.eth_api.get_balance(wallet.address, self.etherscan_key)
            elif wallet_type in ["MATIC", "POLYGON"]:
                result = await self.matic_api.get_balance(wallet.address, self.polygonscan_key)
            elif wallet_type in ["BNB", "BSC", "BINANCE"]:
                result = await self.bnb_api.get_balance(wallet.address, self.bscscan_key)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported wallet type: {wallet_type}",
                    "wallet_id": wallet.id
                }
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "wallet_id": wallet.id
                }
            
            balance = result.get("balance", Decimal(0))
            currency = result.get("currency", wallet_type)
            
            # Get USD price
            usd_price = await self.price_api.get_price(currency, "USD")
            balance_usd = None
            
            if usd_price and balance > 0:
                balance_usd = balance * usd_price
            
            # Update wallet in database
            wallet.balance = balance
            wallet.balance_usd = balance_usd
            wallet.has_balance = balance > 0
            wallet.last_checked = datetime.now()
            
            db.commit()
            
            return {
                "success": True,
                "wallet_id": wallet.id,
                "address": wallet.address,
                "wallet_type": wallet_type,
                "balance": float(balance),
                "balance_usd": float(balance_usd) if balance_usd else None,
                "has_balance": balance > 0
            }
            
        except Exception as e:
            logger.error(f"Error checking wallet {wallet_id}: {str(e)}", exc_info=True)
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "wallet_id": wallet_id
            }
        finally:
            db.close()
    
    async def check_multiple_wallets(
        self,
        wallet_ids: List[int],
        batch_size: int = 10,
        delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Check balances for multiple wallets with rate limiting
        
        Args:
            wallet_ids: List of wallet IDs to check
            batch_size: Number of concurrent requests
            delay: Delay between batches in seconds
        """
        results = {
            "total": len(wallet_ids),
            "checked": 0,
            "success": 0,
            "failed": 0,
            "with_balance": 0,
            "total_value_usd": Decimal(0),
            "results": []
        }
        
        try:
            # Process in batches
            for i in range(0, len(wallet_ids), batch_size):
                batch = wallet_ids[i:i + batch_size]
                
                # Check balances concurrently
                tasks = [self.check_wallet_balance(wallet_id) for wallet_id in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["failed"] += 1
                        logger.error(f"Exception in wallet check: {str(result)}")
                    elif result.get("success"):
                        results["success"] += 1
                        if result.get("has_balance"):
                            results["with_balance"] += 1
                            if result.get("balance_usd"):
                                results["total_value_usd"] += Decimal(str(result["balance_usd"]))
                        results["results"].append(result)
                    else:
                        results["failed"] += 1
                        results["results"].append(result)
                    
                    results["checked"] += 1
                
                # Rate limiting delay
                if i + batch_size < len(wallet_ids):
                    await asyncio.sleep(delay)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in check_multiple_wallets: {str(e)}", exc_info=True)
            return results
    
    async def check_unchecked_wallets(
        self,
        limit: int = 100,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Check wallets that have never been checked
        """
        db = SessionLocal()
        
        try:
            # Get wallets with no last_checked date
            wallets = db.query(Wallet).filter(
                and_(
                    Wallet.address.isnot(None),
                    Wallet.last_checked.is_(None)
                )
            ).limit(limit).all()
            
            wallet_ids = [w.id for w in wallets]
            
            if not wallet_ids:
                return {
                    "total": 0,
                    "checked": 0,
                    "success": 0,
                    "failed": 0,
                    "with_balance": 0,
                    "total_value_usd": Decimal(0),
                    "results": [],
                    "message": "No unchecked wallets found"
                }
            
            return await self.check_multiple_wallets(wallet_ids, batch_size)
            
        finally:
            db.close()
    
    async def check_stale_wallets(
        self,
        hours: int = 24,
        limit: int = 100,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Check wallets that haven't been checked in X hours
        """
        db = SessionLocal()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get stale wallets
            wallets = db.query(Wallet).filter(
                and_(
                    Wallet.address.isnot(None),
                    Wallet.last_checked < cutoff_time
                )
            ).limit(limit).all()
            
            wallet_ids = [w.id for w in wallets]
            
            if not wallet_ids:
                return {
                    "total": 0,
                    "checked": 0,
                    "success": 0,
                    "failed": 0,
                    "with_balance": 0,
                    "total_value_usd": Decimal(0),
                    "results": [],
                    "message": f"No wallets older than {hours} hours found"
                }
            
            return await self.check_multiple_wallets(wallet_ids, batch_size)
            
        finally:
            db.close()
    
    async def check_wallets_with_balance(
        self,
        limit: int = 50,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Re-check wallets that previously had balance
        """
        db = SessionLocal()
        
        try:
            # Get wallets with balance
            wallets = db.query(Wallet).filter(
                and_(
                    Wallet.address.isnot(None),
                    Wallet.has_balance == True
                )
            ).limit(limit).all()
            
            wallet_ids = [w.id for w in wallets]
            
            if not wallet_ids:
                return {
                    "total": 0,
                    "checked": 0,
                    "success": 0,
                    "failed": 0,
                    "with_balance": 0,
                    "total_value_usd": Decimal(0),
                    "results": [],
                    "message": "No wallets with balance found"
                }
            
            return await self.check_multiple_wallets(wallet_ids, batch_size)
            
        finally:
            db.close()
    
    async def get_wallet_statistics(self) -> Dict[str, Any]:
        """Get statistics about wallets in database"""
        db = SessionLocal()
        
        try:
            from sqlalchemy import func
            
            # Total wallets
            total_wallets = db.query(func.count(Wallet.id)).scalar() or 0
            
            # Wallets with addresses
            wallets_with_address = db.query(func.count(Wallet.id)).filter(
                Wallet.address.isnot(None)
            ).scalar() or 0
            
            # Checked wallets
            checked_wallets = db.query(func.count(Wallet.id)).filter(
                Wallet.last_checked.isnot(None)
            ).scalar() or 0
            
            # Wallets with balance
            wallets_with_balance = db.query(func.count(Wallet.id)).filter(
                Wallet.has_balance == True
            ).scalar() or 0
            
            # Total value
            total_value_usd = db.query(func.sum(Wallet.balance_usd)).filter(
                Wallet.balance_usd.isnot(None)
            ).scalar() or Decimal(0)
            
            # Breakdown by type
            type_breakdown = db.query(
                Wallet.wallet_type,
                func.count(Wallet.id).label('count'),
                func.sum(Wallet.balance_usd).label('total_usd')
            ).filter(
                Wallet.address.isnot(None)
            ).group_by(
                Wallet.wallet_type
            ).all()
            
            breakdown = {}
            for wallet_type, count, total_usd in type_breakdown:
                breakdown[wallet_type] = {
                    "count": count,
                    "total_usd": float(total_usd) if total_usd else 0.0
                }
            
            return {
                "total_wallets": total_wallets,
                "wallets_with_address": wallets_with_address,
                "checked_wallets": checked_wallets,
                "unchecked_wallets": wallets_with_address - checked_wallets,
                "wallets_with_balance": wallets_with_balance,
                "total_value_usd": float(total_value_usd),
                "breakdown_by_type": breakdown
            }
            
        finally:
            db.close()
    
    async def close(self):
        """Close all API sessions"""
        await self.btc_api.close()
        await self.eth_api.close()
        await self.matic_api.close()
        await self.bnb_api.close()
        await self.price_api.close()


# Singleton instance
_checker_instance: Optional[WalletBalanceChecker] = None


def get_balance_checker() -> WalletBalanceChecker:
    """Get or create the wallet balance checker singleton"""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = WalletBalanceChecker()
    return _checker_instance
