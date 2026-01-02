#!/usr/bin/env python3
"""
Test script for Telegram Scraper
This will authenticate with Telegram and test downloading from the configured group.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_scraper():
    """Test the Telegram scraper connection"""
    
    # Check configuration
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    chat_ids = os.getenv('TELEGRAM_CHAT_IDS', '')
    
    print("=" * 60)
    print("Telegram Scraper Configuration Test")
    print("=" * 60)
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}..." if api_hash else "API Hash: NOT SET")
    print(f"Phone: {phone if phone else 'NOT SET ⚠️'}")
    print(f"Chat IDs: {chat_ids}")
    print("=" * 60)
    
    if not phone:
        print("\n⚠️  TELEGRAM_PHONE is not set!")
        print("Please add your phone number (with country code) to .env:")
        print("  TELEGRAM_PHONE=+1234567890")
        return
    
    try:
        from telethon import TelegramClient
        from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename
    except ImportError:
        print("\n❌ Telethon not installed!")
        print("Install with: pip install telethon")
        return
    
    # Create client
    session_name = os.getenv('TELEGRAM_SESSION_NAME', 'snatchbase_scraper')
    client = TelegramClient(session_name, int(api_id), api_hash)
    
    print("\n🔐 Connecting to Telegram...")
    print("   (You may need to enter a verification code)")
    
    await client.start(phone=phone)
    
    print("✅ Connected to Telegram!")
    
    # Get user info
    me = await client.get_me()
    print(f"👤 Logged in as: {me.first_name} (@{me.username})")
    
    # Try to access the chat
    chat_id = chat_ids.split(',')[0].strip() if chat_ids else None
    
    if chat_id:
        print(f"\n📱 Trying to access chat: {chat_id}")
        try:
            # Convert to int if it's a numeric ID
            try:
                chat_id = int(chat_id)
            except ValueError:
                pass
            
            entity = await client.get_entity(chat_id)
            chat_name = getattr(entity, 'title', str(chat_id))
            print(f"✅ Successfully accessed: {chat_name}")
            
            # Get recent messages with files
            print(f"\n📜 Fetching recent messages with files...")
            
            file_count = 0
            async for message in client.iter_messages(entity, limit=50):
                if message.media and isinstance(message.media, MessageMediaDocument):
                    doc = message.media.document
                    filename = None
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            filename = attr.file_name
                            break
                    
                    if filename:
                        ext = Path(filename).suffix.lower()
                        if ext in ['.zip', '.rar', '.7z']:
                            size_mb = doc.size / 1024 / 1024
                            print(f"  📦 {filename} ({size_mb:.1f}MB)")
                            file_count += 1
            
            if file_count == 0:
                print("  No ZIP/RAR files found in recent messages")
            else:
                print(f"\n✅ Found {file_count} archive files")
                print("\nTo start downloading, run:")
                print("  python -m app.services.telegram_downloader")
                
        except Exception as e:
            print(f"❌ Could not access chat: {e}")
            print("\nPossible issues:")
            print("  - You are not a member of this group/channel")
            print("  - The chat ID is incorrect")
            print("  - The group/channel is private and you need an invite")
    
    await client.disconnect()
    print("\n✅ Test complete!")


if __name__ == '__main__':
    asyncio.run(test_scraper())
