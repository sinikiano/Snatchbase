#!/usr/bin/env python3
"""
Test wallet balance checking functionality
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.wallet_parser import WalletParser, WalletInfo
from app.services.wallet_balance_checker import WalletBalanceChecker


async def test_wallet_parsing():
    """Test parsing wallet files"""
    print("=" * 60)
    print("💰 Wallet Parser Test")
    print("=" * 60)
    
    # Sample wallet data (example from common stealer logs)
    sample_mnemonic_file = """
Wallet Type: Metamask
Path: Wallet/Extension/Metamask/C-Chrome-88ba39cc/Default
Password: newkamerachi1
Mnemonic: cute interest toddler elder very dinner become guilt canal weasel fossil promote
"""
    
    sample_bitcoin_file = """
Bitcoin Wallet
Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
Private Key: 5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ
"""
    
    sample_ethereum_file = """
Type: Ethereum
Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Private Key: ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
"""
    
    parser = WalletParser()
    
    # Test 1: Mnemonic wallet
    print("\n📝 Test 1: Mnemonic Wallet")
    print("-" * 60)
    wallets = parser.parse_wallet_file(sample_mnemonic_file, "metamask.txt")
    for wallet in wallets:
        print(f"  Type: {wallet.wallet_type}")
        print(f"  Mnemonic: {wallet.mnemonic[:50]}...")
        print(f"  Password: {wallet.password}")
        print(f"  Path: {wallet.path}")
    
    # Test 2: Bitcoin wallet
    print("\n📝 Test 2: Bitcoin Wallet")
    print("-" * 60)
    wallets = parser.parse_wallet_file(sample_bitcoin_file, "bitcoin.txt")
    for wallet in wallets:
        print(f"  Type: {wallet.wallet_type}")
        print(f"  Address: {wallet.address}")
        print(f"  Has Private Key: {'Yes' if wallet.private_key else 'No'}")
    
    # Test 3: Ethereum wallet
    print("\n📝 Test 3: Ethereum Wallet")
    print("-" * 60)
    wallets = parser.parse_wallet_file(sample_ethereum_file, "ethereum.txt")
    for wallet in wallets:
        print(f"  Type: {wallet.wallet_type}")
        print(f"  Address: {wallet.address}")
        print(f"  Has Private Key: {'Yes' if wallet.private_key else 'No'}")


async def test_balance_checking():
    """Test balance checking with real blockchain APIs"""
    print("\n" + "=" * 60)
    print("🔗 Blockchain Balance Checker Test")
    print("=" * 60)
    print("⚠️  Note: This uses public APIs with rate limits")
    print("-" * 60)
    
    # Test wallets (these are public example addresses)
    test_wallets = [
        WalletInfo(
            wallet_type='BTC',
            address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',  # Satoshi's first BTC address
            path='Test/Bitcoin'
        ),
        WalletInfo(
            wallet_type='ETH',
            address='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # Vitalik's address
            path='Test/Ethereum'
        ),
    ]
    
    async with WalletBalanceChecker() as checker:
        print("\n🔍 Checking wallet balances...")
        print("-" * 60)
        
        for wallet in test_wallets:
            print(f"\n📍 {wallet.wallet_type} Address: {wallet.address[:20]}...")
            balance = await checker.check_balance(wallet)
            
            if balance:
                print(f"   ✅ Balance: {balance.balance} {balance.wallet_type}")
                if balance.balance_usd:
                    print(f"   💵 USD Value: ${balance.balance_usd:.2f}")
                if balance.balance > 0:
                    print(f"   💰 HAS FUNDS!")
            else:
                print(f"   ❌ Could not check balance")
            
            # Rate limiting delay
            await asyncio.sleep(2)


async def main():
    """Main test function"""
    print("\n🚀 Snatchbase Wallet Feature Tests")
    print("=" * 60)
    
    # Run parsing tests
    await test_wallet_parsing()
    
    # Ask user if they want to test balance checking
    print("\n" + "=" * 60)
    print("⚠️  Balance checking will query public blockchain APIs")
    print("   This may take a few seconds and has rate limits")
    response = input("\nDo you want to test balance checking? (y/N): ")
    
    if response.lower() == 'y':
        await test_balance_checking()
    else:
        print("\n⏭️  Skipping balance checking test")
    
    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)
    print("\n📚 Integration Status:")
    print("   ✅ Wallet parser implemented")
    print("   ✅ Balance checker implemented")
    print("   ✅ Database model created")
    print("   ✅ API endpoints created")
    print("   ✅ ZIP ingestion integration added")
    print("\n💡 Next Steps:")
    print("   1. Restart backend server to load new code")
    print("   2. Process ZIP files with wallet data")
    print("   3. Check balances via API: POST /api/wallets/check-balance")
    print("   4. View wallet stats: GET /api/stats/wallets")
    print("   5. Build frontend components to display wallet data")
    print()


if __name__ == '__main__':
    asyncio.run(main())
