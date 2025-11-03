"""
Blockchain API integrations for wallet balance checking
Supports multiple chains: BTC, ETH, MATIC, BNB, etc.
"""
import os
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class BlockchainAPI:
    """Base class for blockchain API integrations"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get balance for address - must be implemented by subclasses"""
        raise NotImplementedError


class BitcoinAPI(BlockchainAPI):
    """Bitcoin balance checker using blockchain.info API"""
    
    BASE_URL = "https://blockchain.info"
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get Bitcoin balance"""
        try:
            session = await self.get_session()
            url = f"{self.BASE_URL}/q/addressbalance/{address}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    # Returns balance in satoshis
                    satoshis = int(await response.text())
                    btc_balance = Decimal(satoshis) / Decimal(100_000_000)
                    
                    return {
                        "success": True,
                        "balance": btc_balance,
                        "currency": "BTC",
                        "raw_balance": satoshis,
                        "address": address
                    }
                else:
                    return {
                        "success": False,
                        "balance": Decimal(0),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error checking BTC balance for {address}: {str(e)}")
            return {
                "success": False,
                "balance": Decimal(0),
                "error": str(e)
            }


class EthereumAPI(BlockchainAPI):
    """Ethereum balance checker using Etherscan API"""
    
    BASE_URL = "https://api.etherscan.io/api"
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('ETHERSCAN_API_KEY')
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get Ethereum balance"""
        try:
            session = await self.get_session()
            
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest"
            }
            
            if self.api_key:
                params["apikey"] = self.api_key
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "1":
                        # Returns balance in wei
                        wei_balance = int(data.get("result", "0"))
                        eth_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return {
                            "success": True,
                            "balance": eth_balance,
                            "currency": "ETH",
                            "raw_balance": wei_balance,
                            "address": address
                        }
                    else:
                        return {
                            "success": False,
                            "balance": Decimal(0),
                            "error": data.get("message", "Unknown error")
                        }
                else:
                    return {
                        "success": False,
                        "balance": Decimal(0),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error checking ETH balance for {address}: {str(e)}")
            return {
                "success": False,
                "balance": Decimal(0),
                "error": str(e)
            }
    
    async def get_token_balances(self, address: str) -> Dict[str, Any]:
        """Get ERC-20 token balances"""
        try:
            session = await self.get_session()
            
            params = {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "sort": "desc"
            }
            
            if self.api_key:
                params["apikey"] = self.api_key
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "1":
                        return {
                            "success": True,
                            "tokens": data.get("result", []),
                            "address": address
                        }
                    else:
                        return {
                            "success": False,
                            "tokens": [],
                            "error": data.get("message", "Unknown error")
                        }
                else:
                    return {
                        "success": False,
                        "tokens": [],
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error checking ETH tokens for {address}: {str(e)}")
            return {
                "success": False,
                "tokens": [],
                "error": str(e)
            }


class PolygonAPI(BlockchainAPI):
    """Polygon (MATIC) balance checker using Polygonscan API"""
    
    BASE_URL = "https://api.polygonscan.com/api"
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('POLYGONSCAN_API_KEY')
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get Polygon MATIC balance"""
        try:
            session = await self.get_session()
            
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest"
            }
            
            if self.api_key:
                params["apikey"] = self.api_key
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "1":
                        # Returns balance in wei
                        wei_balance = int(data.get("result", "0"))
                        matic_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return {
                            "success": True,
                            "balance": matic_balance,
                            "currency": "MATIC",
                            "raw_balance": wei_balance,
                            "address": address
                        }
                    else:
                        return {
                            "success": False,
                            "balance": Decimal(0),
                            "error": data.get("message", "Unknown error")
                        }
                else:
                    return {
                        "success": False,
                        "balance": Decimal(0),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error checking MATIC balance for {address}: {str(e)}")
            return {
                "success": False,
                "balance": Decimal(0),
                "error": str(e)
            }


class BinanceSmartChainAPI(BlockchainAPI):
    """Binance Smart Chain (BNB) balance checker using BscScan API"""
    
    BASE_URL = "https://api.bscscan.com/api"
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('BSCSCAN_API_KEY')
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get BNB balance"""
        try:
            session = await self.get_session()
            
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest"
            }
            
            if self.api_key:
                params["apikey"] = self.api_key
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "1":
                        # Returns balance in wei
                        wei_balance = int(data.get("result", "0"))
                        bnb_balance = Decimal(wei_balance) / Decimal(10**18)
                        
                        return {
                            "success": True,
                            "balance": bnb_balance,
                            "currency": "BNB",
                            "raw_balance": wei_balance,
                            "address": address
                        }
                    else:
                        return {
                            "success": False,
                            "balance": Decimal(0),
                            "error": data.get("message", "Unknown error")
                        }
                else:
                    return {
                        "success": False,
                        "balance": Decimal(0),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"Error checking BNB balance for {address}: {str(e)}")
            return {
                "success": False,
                "balance": Decimal(0),
                "error": str(e)
            }


class CryptoCompareAPI:
    """CryptoCompare API for price data"""
    
    BASE_URL = "https://min-api.cryptocompare.com/data"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_price(self, from_symbol: str, to_symbol: str = "USD") -> Optional[Decimal]:
        """Get current price for cryptocurrency"""
        try:
            session = await self.get_session()
            
            params = {
                "fsym": from_symbol.upper(),
                "tsyms": to_symbol.upper()
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with session.get(f"{self.BASE_URL}/price", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data.get(to_symbol.upper())
                    
                    if price:
                        return Decimal(str(price))
                    else:
                        return None
                else:
                    return None
        except Exception as e:
            logger.error(f"Error getting price for {from_symbol}: {str(e)}")
            return None
    
    async def get_multiple_prices(self, symbols: list, to_symbol: str = "USD") -> Dict[str, Decimal]:
        """Get prices for multiple cryptocurrencies"""
        try:
            session = await self.get_session()
            
            params = {
                "fsyms": ",".join([s.upper() for s in symbols]),
                "tsyms": to_symbol.upper()
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with session.get(f"{self.BASE_URL}/pricemulti", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    prices = {}
                    for symbol in symbols:
                        price_data = data.get(symbol.upper(), {})
                        price = price_data.get(to_symbol.upper())
                        if price:
                            prices[symbol.upper()] = Decimal(str(price))
                    
                    return prices
                else:
                    return {}
        except Exception as e:
            logger.error(f"Error getting multiple prices: {str(e)}")
            return {}
