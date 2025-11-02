"""
Cryptocurrency Wallet Balance Checker
Checks balances for Bitcoin, Ethereum, and other cryptocurrencies
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass
import time

from app.services.wallet_parser import WalletInfo

logger = logging.getLogger(__name__)

@dataclass
class WalletBalance:
    """Wallet balance information"""
    address: str
    wallet_type: str
    balance: Decimal
    balance_usd: Optional[Decimal] = None
    token_balances: Optional[Dict[str, Decimal]] = None
    last_checked: Optional[float] = None
    error: Optional[str] = None


class WalletBalanceChecker:
    """Check cryptocurrency wallet balances using public APIs"""
    
    # Free API endpoints (no key required)
    API_ENDPOINTS = {
        'BTC': {
            'blockchain_info': 'https://blockchain.info/q/addressbalance/',
            'blockchair': 'https://api.blockchair.com/bitcoin/dashboards/address/',
            'blockcypher': 'https://api.blockcypher.com/v1/btc/main/addrs/',
        },
        'ETH': {
            'etherscan': 'https://api.etherscan.io/api?module=account&action=balance&address=',
            'blockchair': 'https://api.blockchair.com/ethereum/dashboards/address/',
        },
        'MATIC': {
            'polygonscan': 'https://api.polygonscan.com/api?module=account&action=balance&address=',
        },
        'BNB': {
            'bscscan': 'https://api.bscscan.com/api?module=account&action=balance&address=',
        },
    }
    
    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        """
        Initialize balance checker
        
        Args:
            use_cache: Enable caching of balance results
            cache_ttl: Cache time-to-live in seconds
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, WalletBalance] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_cached_balance(self, address: str) -> Optional[WalletBalance]:
        """Get cached balance if available and not expired"""
        if not self.use_cache:
            return None
        
        cached = self._cache.get(address)
        if cached and cached.last_checked:
            if time.time() - cached.last_checked < self.cache_ttl:
                logger.debug(f"Using cached balance for {address}")
                return cached
        
        return None
    
    def _cache_balance(self, address: str, balance: WalletBalance):
        """Cache balance result"""
        if self.use_cache:
            balance.last_checked = time.time()
            self._cache[address] = balance
    
    async def check_balance(self, wallet: WalletInfo) -> Optional[WalletBalance]:
        """
        Check balance for a single wallet
        
        Args:
            wallet: WalletInfo object
        
        Returns:
            WalletBalance or None if check failed
        """
        if not wallet.address:
            logger.warning("No address provided for balance check")
            return None
        
        # Check cache first
        cached = self._get_cached_balance(wallet.address)
        if cached:
            return cached
        
        # Determine wallet type and check balance
        if wallet.wallet_type == 'BTC':
            result = await self._check_btc_balance(wallet.address)
        elif wallet.wallet_type == 'ETH':
            result = await self._check_eth_balance(wallet.address)
        elif wallet.wallet_type == 'MATIC':
            result = await self._check_polygon_balance(wallet.address)
        elif wallet.wallet_type == 'BNB':
            result = await self._check_bnb_balance(wallet.address)
        else:
            logger.warning(f"Unsupported wallet type: {wallet.wallet_type}")
            result = None
        
        # Cache result
        if result:
            self._cache_balance(wallet.address, result)
        
        return result
    
    async def check_multiple_balances(self, wallets: List[WalletInfo]) -> List[WalletBalance]:
        """
        Check balances for multiple wallets concurrently
        
        Args:
            wallets: List of WalletInfo objects
        
        Returns:
            List of WalletBalance objects
        """
        if not self.session:
            async with self:
                return await self._check_balances_async(wallets)
        else:
            return await self._check_balances_async(wallets)
    
    async def _check_balances_async(self, wallets: List[WalletInfo]) -> List[WalletBalance]:
        """Internal method to check balances asynchronously"""
        tasks = [self.check_balance(wallet) for wallet in wallets if wallet.address]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        balances = []
        for result in results:
            if isinstance(result, WalletBalance):
                balances.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error checking balance: {result}")
        
        return balances
    
    async def _check_btc_balance(self, address: str) -> Optional[WalletBalance]:
        """Check Bitcoin balance using blockchain.info API"""
        try:
            # Try blockchain.info first (returns satoshis)
            url = f"{self.API_ENDPOINTS['BTC']['blockchain_info']}{address}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    satoshis = int(await response.text())
                    btc_balance = Decimal(satoshis) / Decimal(100_000_000)
                    
                    return WalletBalance(
                        address=address,
                        wallet_type='BTC',
                        balance=btc_balance
                    )
        except Exception as e:
            logger.error(f"Error checking BTC balance for {address}: {e}")
        
        # Fallback to blockchair
        try:
            url = f"{self.API_ENDPOINTS['BTC']['blockchair']}{address}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_satoshis = data['data'][address]['address']['balance']
                    btc_balance = Decimal(balance_satoshis) / Decimal(100_000_000)
                    
                    return WalletBalance(
                        address=address,
                        wallet_type='BTC',
                        balance=btc_balance,
                        balance_usd=data['data'][address].get('address', {}).get('balance_usd')
                    )
        except Exception as e:
            logger.error(f"Error checking BTC balance (blockchair) for {address}: {e}")
        
        return None
    
    async def _check_eth_balance(self, address: str) -> Optional[WalletBalance]:
        """Check Ethereum balance using Etherscan API"""
        try:
            # Note: Etherscan free API without key has rate limits
            url = f"{self.API_ENDPOINTS['ETH']['etherscan']}{address}&tag=latest"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        wei_balance = int(data['result'])
                        eth_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return WalletBalance(
                            address=address,
                            wallet_type='ETH',
                            balance=eth_balance
                        )
        except Exception as e:
            logger.error(f"Error checking ETH balance for {address}: {e}")
        
        # Fallback to blockchair
        try:
            url = f"{self.API_ENDPOINTS['ETH']['blockchair']}{address}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_wei = int(data['data'][address]['address']['balance'])
                    eth_balance = Decimal(balance_wei) / Decimal(10**18)
                    
                    return WalletBalance(
                        address=address,
                        wallet_type='ETH',
                        balance=eth_balance,
                        balance_usd=data['data'][address]['address'].get('balance_usd')
                    )
        except Exception as e:
            logger.error(f"Error checking ETH balance (blockchair) for {address}: {e}")
        
        return None
    
    async def _check_polygon_balance(self, address: str) -> Optional[WalletBalance]:
        """Check Polygon (MATIC) balance"""
        try:
            url = f"{self.API_ENDPOINTS['MATIC']['polygonscan']}{address}&tag=latest"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        wei_balance = int(data['result'])
                        matic_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return WalletBalance(
                            address=address,
                            wallet_type='MATIC',
                            balance=matic_balance
                        )
        except Exception as e:
            logger.error(f"Error checking MATIC balance for {address}: {e}")
        
        return None
    
    async def _check_bnb_balance(self, address: str) -> Optional[WalletBalance]:
        """Check Binance Smart Chain (BNB) balance"""
        try:
            url = f"{self.API_ENDPOINTS['BNB']['bscscan']}{address}&tag=latest"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        wei_balance = int(data['result'])
                        bnb_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return WalletBalance(
                            address=address,
                            wallet_type='BNB',
                            balance=bnb_balance
                        )
        except Exception as e:
            logger.error(f"Error checking BNB balance for {address}: {e}")
        
        return None


async def check_wallet_balances(wallets: List[WalletInfo]) -> Dict[str, WalletBalance]:
    """
    Convenience function to check balances for multiple wallets
    
    Args:
        wallets: List of WalletInfo objects
    
    Returns:
        Dict mapping address to WalletBalance
    """
    async with WalletBalanceChecker() as checker:
        balances = await checker.check_multiple_balances(wallets)
        return {b.address: b for b in balances}


if __name__ == '__main__':
    # Example usage
    import sys
    from app.services.wallet_parser import WalletInfo
    
    async def main():
        if len(sys.argv) < 3:
            print("Usage: python wallet_balance_checker.py <wallet_type> <address>")
            print("Example: python wallet_balance_checker.py ETH 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            sys.exit(1)
        
        wallet_type = sys.argv[1].upper()
        address = sys.argv[2]
        
        wallet = WalletInfo(
            wallet_type=wallet_type,
            address=address
        )
        
        async with WalletBalanceChecker() as checker:
            balance = await checker.check_balance(wallet)
            
            if balance:
                print(f"\n💰 Balance for {address}:")
                print(f"   Type: {balance.wallet_type}")
                print(f"   Balance: {balance.balance} {balance.wallet_type}")
                if balance.balance_usd:
                    print(f"   USD Value: ${balance.balance_usd:.2f}")
            else:
                print(f"\n❌ Could not check balance for {address}")
    
    asyncio.run(main())
