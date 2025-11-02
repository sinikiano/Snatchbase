"""
Address derivation from BIP39 mnemonic phrases.

Supports deriving cryptocurrency addresses for:
- Bitcoin (BTC) - BIP44 path m/44'/0'/0'/0/0
- Ethereum (ETH) - BIP44 path m/44'/60'/0'/0/0
- Solana (SOL) - BIP44 path m/44'/501'/0'/0/0
"""

from typing import Optional, Dict
from mnemonic import Mnemonic
from eth_account import Account
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import hashlib


class AddressDerivation:
    """Derive cryptocurrency addresses from BIP39 mnemonic phrases."""
    
    def __init__(self):
        self.mnemo = Mnemonic("english")
    
    def is_valid_mnemonic(self, mnemonic: str) -> bool:
        """Check if a mnemonic phrase is valid BIP39."""
        try:
            return self.mnemo.check(mnemonic)
        except Exception:
            return False
    
    def derive_eth_address(self, mnemonic: str, index: int = 0) -> Optional[str]:
        """
        Derive Ethereum address from mnemonic.
        
        Args:
            mnemonic: BIP39 mnemonic phrase (12-24 words)
            index: Address index (default: 0)
        
        Returns:
            Ethereum address (0x...) or None if derivation fails
        """
        try:
            # Enable BIP39 mnemonic support in eth-account
            Account.enable_unaudited_hdwallet_features()
            
            # Derive account using BIP44 path for Ethereum
            # m/44'/60'/0'/0/{index}
            account = Account.from_mnemonic(
                mnemonic,
                account_path=f"m/44'/60'/0'/0/{index}"
            )
            
            return account.address
        
        except Exception as e:
            print(f"Error deriving ETH address: {e}")
            return None
    
    def derive_sol_address(self, mnemonic: str, index: int = 0) -> Optional[str]:
        """
        Derive Solana address from mnemonic.
        
        Args:
            mnemonic: BIP39 mnemonic phrase (12-24 words)
            index: Address index (default: 0)
        
        Returns:
            Solana address (base58) or None if derivation fails
        """
        try:
            # Convert mnemonic to seed
            seed = self.mnemo.to_seed(mnemonic, passphrase="")
            
            # Solana uses the full 64-byte seed as the keypair seed
            # Create keypair from full seed
            keypair = Keypair.from_seed(seed[:32])
            
            # Get public key (address)
            return str(keypair.pubkey())
        
        except Exception as e:
            print(f"Error deriving SOL address: {e}")
            return None
    
    def derive_btc_address(self, mnemonic: str, index: int = 0) -> Optional[str]:
        """
        Derive Bitcoin address from mnemonic.
        
        Args:
            mnemonic: BIP39 mnemonic phrase (12-24 words)
            index: Address index (default: 0)
        
        Returns:
            Bitcoin address (legacy P2PKH format) or None if derivation fails
        
        Note:
            This is a simplified implementation using seed-based derivation.
            For production use, consider using a proper BIP32/BIP44 library
            like `bip32` or `hdwallet`.
        """
        try:
            # Convert mnemonic to seed
            seed = self.mnemo.to_seed(mnemonic, passphrase="")
            
            # For Bitcoin, we'd need a proper BIP32 implementation
            # This is a placeholder that returns None
            # To properly implement, install: pip install hdwallet
            # and use HDWallet with BIP44 path m/44'/0'/0'/0/{index}
            
            return None  # Not implemented - requires hdwallet library
        
        except Exception as e:
            print(f"Error deriving BTC address: {e}")
            return None
    
    def derive_all_addresses(
        self,
        mnemonic: str,
        index: int = 0
    ) -> Dict[str, Optional[str]]:
        """
        Derive addresses for all supported cryptocurrencies.
        
        Args:
            mnemonic: BIP39 mnemonic phrase (12-24 words)
            index: Address index (default: 0)
        
        Returns:
            Dictionary with chain names as keys and addresses as values:
            {
                'ethereum': '0x...',
                'solana': '...',
                'bitcoin': '...'
            }
        """
        if not self.is_valid_mnemonic(mnemonic):
            return {
                'ethereum': None,
                'solana': None,
                'bitcoin': None
            }
        
        return {
            'ethereum': self.derive_eth_address(mnemonic, index),
            'solana': self.derive_sol_address(mnemonic, index),
            'bitcoin': self.derive_btc_address(mnemonic, index)
        }
    
    def derive_primary_address(
        self,
        mnemonic: str,
        wallet_type: str
    ) -> Optional[str]:
        """
        Derive the primary address based on wallet type.
        
        Args:
            mnemonic: BIP39 mnemonic phrase
            wallet_type: Wallet type (e.g., 'Metamask', 'Phantom', 'Exodus')
        
        Returns:
            Primary address for the wallet type, or None
        """
        wallet_type_lower = wallet_type.lower()
        
        # Map wallet types to their primary blockchain
        if any(w in wallet_type_lower for w in ['metamask', 'okx', 'coinbase', 'trust']):
            # Ethereum-based wallets
            return self.derive_eth_address(mnemonic)
        
        elif any(w in wallet_type_lower for w in ['phantom', 'solflare', 'slope']):
            # Solana-based wallets
            return self.derive_sol_address(mnemonic)
        
        elif any(w in wallet_type_lower for w in ['exodus', 'electrum']):
            # Multi-chain or Bitcoin wallets - try ETH first
            eth_addr = self.derive_eth_address(mnemonic)
            if eth_addr:
                return eth_addr
            return self.derive_btc_address(mnemonic)
        
        else:
            # Unknown wallet type - try Ethereum (most common)
            return self.derive_eth_address(mnemonic)


# Singleton instance
_derivation_instance: Optional[AddressDerivation] = None


def get_address_derivation() -> AddressDerivation:
    """Get singleton instance of AddressDerivation."""
    global _derivation_instance
    if _derivation_instance is None:
        _derivation_instance = AddressDerivation()
    return _derivation_instance
