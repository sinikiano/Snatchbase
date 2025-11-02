#!/usr/bin/env python3
"""
Demo Wallet Balance Checker Test

This script tests the wallet balance checker with known addresses
that have real balances on various blockchains.
"""
import os
import sys
import asyncio
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Wallet, Device
from app.services.wallet_checker import WalletBalanceChecker


async def test_with_demo_addresses():
    """Test wallet checker with known addresses that have balances"""
    
    print("\n" + "="*60)
    print("🧪 WALLET BALANCE CHECKER DEMO TEST")
    print("="*60)
    
    db = SessionLocal()
    checker = WalletBalanceChecker()
    
    try:
        # Get or create test device
        device = db.query(Device).first()
        if not device:
            print("\n📱 Creating test device...")
            device = Device(
                device_id="demo_wallet_test",
                device_name="Demo Wallet Test",
                device_name_hash="demo_hash",
                upload_batch="demo_test"
            )
            db.add(device)
            db.commit()
            db.refresh(device)
        
        # Known addresses with balances (public blockchain explorers)
        demo_wallets = [
            {
                "type": "ETH",
                "address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",  # Ethereum Foundation
                "description": "Ethereum Foundation (Known ETH holder)"
            },
            {
                "type": "ETH",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Vitalik's address
                "description": "Vitalik Buterin (Known ETH holder)"
            },
            {
                "type": "BTC",
                "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block
                "description": "Bitcoin Genesis Address"
            },
            {
                "type": "BTC", 
                "address": "3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS",  # Known holder
                "description": "Known BTC Address"
            },
        ]
        
        print(f"\n📝 Creating {len(demo_wallets)} demo wallet records...")
        
        wallet_ids = []
        for wallet_info in demo_wallets:
            # Check if already exists
            existing = db.query(Wallet).filter(
                Wallet.address == wallet_info["address"]
            ).first()
            
            if existing:
                print(f"   ♻️  Using existing: {wallet_info['type']} - {wallet_info['description']}")
                wallet_ids.append(existing.id)
            else:
                wallet = Wallet(
                    device_id=device.id,
                    wallet_type=wallet_info["type"],
                    address=wallet_info["address"],
                    path=f"demo/{wallet_info['type']}/test.txt"
                )
                db.add(wallet)
                db.flush()
                print(f"   ✅ Created: {wallet_info['type']} - {wallet_info['description']}")
                wallet_ids.append(wallet.id)
        
        db.commit()
        
        print(f"\n💰 Testing balance checker on {len(wallet_ids)} wallets...")
        print("   This may take 30-60 seconds due to API rate limits...")
        print("   Please wait...\n")
        
        # Test the balance checker
        results = await checker.check_multiple_wallets(
            wallet_ids=wallet_ids,
            batch_size=2,  # Small batches to respect rate limits
            delay=3.0  # 3 second delay between batches
        )
        
        print("\n" + "="*60)
        print("📊 BALANCE CHECK RESULTS")
        print("="*60)
        print(f"\n✅ Summary:")
        print(f"   Total Checked: {results['checked']}")
        print(f"   Successful: {results['success']}")
        print(f"   Failed: {results['failed']}")
        print(f"   With Balance: {results['with_balance']}")
        print(f"   Total Value: ${results['total_value_usd']:.2f} USD")
        
        print(f"\n💎 Detailed Results:")
        print("-" * 60)
        
        for i, result in enumerate(results['results'], 1):
            status = "✅" if result.get('success') else "❌"
            wallet_type = result.get('wallet_type', 'Unknown')
            address = result.get('address', result.get('wallet_id', 'N/A'))
            
            print(f"\n{i}. {status} {wallet_type} Wallet")
            print(f"   Address: {address}")
            
            if result.get('success'):
                balance = result.get('balance', 0)
                balance_usd = result.get('balance_usd', 0)
                has_balance = result.get('has_balance', False)
                
                if has_balance:
                    print(f"   💰 Balance: {balance} {wallet_type}")
                    print(f"   💵 USD Value: ${balance_usd:.2f}")
                    
                    # Show token balances if available
                    if result.get('token_balance'):
                        print(f"   🪙 Token Balance: {result['token_balance']}")
                else:
                    print(f"   ⚪ Balance: 0 (Empty)")
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ❌ Error: {error}")
        
        print("\n" + "="*60)
        
        # Show updated database stats
        print(f"\n📊 Updated Database Statistics:")
        total_wallets = db.query(Wallet).count()
        with_addresses = db.query(Wallet).filter(Wallet.address.isnot(None)).count()
        checked = db.query(Wallet).filter(Wallet.last_checked.isnot(None)).count()
        with_balance = db.query(Wallet).filter(Wallet.has_balance == True).count()
        
        print(f"   Total Wallets: {total_wallets}")
        print(f"   With Addresses: {with_addresses}")
        print(f"   Checked: {checked}")
        print(f"   With Balance: {with_balance}")
        
        # Test statistics function
        print(f"\n📈 Wallet Statistics from Service:")
        stats = await checker.get_wallet_statistics()
        print(f"   Total Wallets: {stats['total_wallets']}")
        print(f"   With Addresses: {stats['wallets_with_address']}")
        print(f"   Checked: {stats['checked_wallets']}")
        print(f"   Unchecked: {stats['unchecked_wallets']}")
        print(f"   With Balance: {stats['wallets_with_balance']}")
        if stats.get('total_value_usd', 0) > 0:
            print(f"   Total Portfolio: ${stats['total_value_usd']:.2f} USD")
        
        print("\n" + "="*60)
        print("✅ Demo test completed successfully!")
        print("="*60 + "\n")
        
        # Show how to use via Telegram
        print("💡 To use via Telegram bot:")
        print("   /wallets - View wallet statistics")
        print("   /checkwallets - Check unchecked wallets")
        print("   /checkbalances - Re-check known wallets")
        print("   /highvalue 100 - Show wallets with >$100")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup API sessions
        print("\n🧹 Cleaning up...")
        await checker.btc_api.close()
        await checker.eth_api.close()
        await checker.matic_api.close()
        await checker.bnb_api.close()
        await checker.price_api.close()
        db.close()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_with_demo_addresses())
