"""
Cryptocurrency Wallet Parser and Balance Checker
Parses wallet mnemonics, private keys, and checks balances
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class WalletInfo:
    """Wallet information extracted from files"""
    wallet_type: str  # BTC, ETH, etc.
    mnemonic: Optional[str] = None
    private_key: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    path: Optional[str] = None
    source_file: Optional[str] = None


class WalletParser:
    """Parser for cryptocurrency wallet files"""
    
    # Common wallet file names
    WALLET_FILE_NAMES = {
        "mnemonic.txt",
        "seed.txt",
        "wallet.txt",
        "metamask.txt",
        "exodus.txt",
        "electrum.txt",
        "wallet_cracked.txt",
        "walletaddress.txt",
        "privatekey.txt",
    }
    
    # Regex patterns for different wallet types
    PATTERNS = {
        # BTC address patterns
        'btc_legacy': re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),
        'btc_segwit': re.compile(r'\bbc1[a-z0-9]{39,59}\b'),
        
        # ETH address pattern
        'eth_address': re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
        
        # Mnemonic phrase (12, 15, 18, 21, 24 words)
        'mnemonic': re.compile(r'\b([a-z]+\s+){11,23}[a-z]+\b', re.IGNORECASE),
        
        # Private key patterns
        'private_key_hex': re.compile(r'\b[a-fA-F0-9]{64}\b'),
        'private_key_wif': re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
        
        # Solana address
        'solana': re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'),
    }
    
    def is_wallet_file(self, filename: str) -> bool:
        """Check if filename is a wallet file"""
        return filename.lower() in self.WALLET_FILE_NAMES or \
               any(keyword in filename.lower() for keyword in ['wallet', 'mnemonic', 'seed', 'private'])
    
    def parse_wallet_file(self, content: str, filename: str = "") -> List[WalletInfo]:
        """Parse wallet file content and extract wallet information"""
        wallets = []
        
        if not content or not content.strip():
            return wallets
        
        lines = content.split('\n')
        
        # Try to detect structured format first
        structured_wallets = self._parse_structured_format(lines, filename)
        if structured_wallets:
            return structured_wallets
        
        # Fallback to pattern matching
        wallets.extend(self._parse_by_patterns(content, filename))
        
        return wallets
    
    def _parse_structured_format(self, lines: List[str], filename: str) -> List[WalletInfo]:
        """Parse structured wallet format (key: value pairs)"""
        wallets = []
        current_wallet = {}
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and separators
            if not line or set(line).issubset({'=', '_', '-', '|', ' '}):
                if current_wallet:
                    wallet = self._create_wallet_from_dict(current_wallet, filename)
                    if wallet:
                        wallets.append(wallet)
                    current_wallet = {}
                continue
            
            # Parse key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if any(k in key for k in ['mnemonic', 'seed', 'phrase']):
                    current_wallet['mnemonic'] = value
                elif any(k in key for k in ['private', 'key']):
                    current_wallet['private_key'] = value
                elif 'password' in key or 'pass' in key:
                    current_wallet['password'] = value
                elif 'address' in key or 'wallet' in key:
                    current_wallet['address'] = value
                elif 'type' in key:
                    current_wallet['wallet_type'] = value
                elif 'path' in key or 'derivation' in key:
                    current_wallet['path'] = value
            else:
                # Try to detect mnemonic phrase
                if self._is_mnemonic(line):
                    current_wallet['mnemonic'] = line
        
        # Add last wallet if exists
        if current_wallet:
            wallet = self._create_wallet_from_dict(current_wallet, filename)
            if wallet:
                wallets.append(wallet)
        
        return wallets
    
    def _parse_by_patterns(self, content: str, filename: str) -> List[WalletInfo]:
        """Parse wallet information using regex patterns"""
        wallets = []
        
        # Extract mnemonics
        mnemonic_matches = self.PATTERNS['mnemonic'].findall(content)
        for match in mnemonic_matches:
            mnemonic = match.strip() if isinstance(match, str) else ' '.join(match).strip()
            if self._is_mnemonic(mnemonic):
                wallets.append(WalletInfo(
                    wallet_type='multi',
                    mnemonic=mnemonic,
                    source_file=filename
                ))
        
        # Extract Ethereum addresses
        eth_addresses = self.PATTERNS['eth_address'].findall(content)
        for addr in set(eth_addresses):
            wallets.append(WalletInfo(
                wallet_type='ETH',
                address=addr,
                source_file=filename
            ))
        
        # Extract Bitcoin addresses
        btc_legacy = self.PATTERNS['btc_legacy'].findall(content)
        for addr in set(btc_legacy):
            wallets.append(WalletInfo(
                wallet_type='BTC',
                address=addr,
                source_file=filename
            ))
        
        btc_segwit = self.PATTERNS['btc_segwit'].findall(content)
        for addr in set(btc_segwit):
            wallets.append(WalletInfo(
                wallet_type='BTC',
                address=addr,
                source_file=filename
            ))
        
        # Extract private keys
        private_keys = self.PATTERNS['private_key_hex'].findall(content)
        for key in set(private_keys):
            wallets.append(WalletInfo(
                wallet_type='multi',
                private_key=key,
                source_file=filename
            ))
        
        return wallets
    
    def _is_mnemonic(self, text: str) -> bool:
        """Check if text is a valid BIP39 mnemonic phrase"""
        words = text.strip().split()
        # Valid mnemonic lengths: 12, 15, 18, 21, 24 words
        return len(words) in [12, 15, 18, 21, 24] and all(word.isalpha() for word in words)
    
    def _create_wallet_from_dict(self, data: Dict, filename: str) -> Optional[WalletInfo]:
        """Create WalletInfo from parsed dictionary"""
        if not data:
            return None
        
        # Determine wallet type
        wallet_type = data.get('wallet_type', 'unknown')
        
        # Auto-detect type from address
        if 'address' in data:
            addr = data['address']
            if addr.startswith('0x'):
                wallet_type = 'ETH'
            elif addr.startswith('bc1'):
                wallet_type = 'BTC'
            elif addr.startswith(('1', '3')):
                wallet_type = 'BTC'
        
        # Auto-detect from mnemonic
        if 'mnemonic' in data and wallet_type == 'unknown':
            wallet_type = 'multi'
        
        return WalletInfo(
            wallet_type=wallet_type,
            mnemonic=data.get('mnemonic'),
            private_key=data.get('private_key'),
            password=data.get('password'),
            address=data.get('address'),
            path=data.get('path'),
            source_file=filename
        )


def parse_wallet_files(file_paths: List[Path]) -> List[WalletInfo]:
    """
    Parse multiple wallet files and extract all wallet information
    
    Args:
        file_paths: List of paths to wallet files
    
    Returns:
        List of WalletInfo objects
    """
    parser = WalletParser()
    all_wallets = []
    
    for file_path in file_paths:
        try:
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            wallets = parser.parse_wallet_file(content, file_path.name)
            all_wallets.extend(wallets)
            
        except Exception as e:
            logger.error(f"Error parsing wallet file {file_path}: {e}")
    
    return all_wallets


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python wallet_parser.py <wallet_file>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    wallets = parse_wallet_files([file_path])
    
    print(f"Found {len(wallets)} wallets:")
    for i, wallet in enumerate(wallets, 1):
        print(f"\n{i}. {wallet.wallet_type}")
        if wallet.mnemonic:
            print(f"   Mnemonic: {wallet.mnemonic[:50]}...")
        if wallet.address:
            print(f"   Address: {wallet.address}")
        if wallet.private_key:
            print(f"   Private Key: {wallet.private_key[:16]}...")
        if wallet.password:
            print(f"   Password: {wallet.password}")
