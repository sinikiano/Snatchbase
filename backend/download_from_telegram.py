#!/usr/bin/env python3
"""Download files from Telegram channel"""
import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename

load_dotenv()

async def download_file():
    client = TelegramClient(
        'snatchbase_scraper',
        int(os.getenv('TELEGRAM_API_ID')),
        os.getenv('TELEGRAM_API_HASH')
    )
    
    await client.start(phone=os.getenv('TELEGRAM_PHONE'))
    print("Connected to Telegram!")
    
    entity = await client.get_entity(-1001525224025)
    print(f"Chat: {entity.title}")
    
    download_dir = Path('data/incoming/uploads')
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Get message 584 (smallest file - 570MB)
    msg = await client.get_messages(entity, ids=584)
    
    doc = msg.media.document
    filename = None
    for attr in doc.attributes:
        if isinstance(attr, DocumentAttributeFilename):
            filename = attr.file_name
            break
    
    path = download_dir / filename
    size_mb = doc.size / 1024 / 1024
    
    print(f"\n📥 Downloading: {filename}")
    print(f"📊 Size: {size_mb:.1f}MB")
    print(f"📁 To: {path}")
    
    start = time.time()
    last_update = [0]
    
    def progress(current, total):
        percent = int(current / total * 100)
        if percent >= last_update[0] + 10:
            elapsed = time.time() - start
            speed = current / elapsed / 1024 / 1024 if elapsed > 0 else 0
            print(f"  {percent}% - {current/1024/1024:.1f}MB / {total/1024/1024:.1f}MB ({speed:.1f}MB/s)")
            last_update[0] = percent
    
    await client.download_media(msg, file=str(path), progress_callback=progress)
    
    elapsed = time.time() - start
    print(f"\n✅ Downloaded in {elapsed:.1f}s ({size_mb/elapsed:.1f}MB/s)")
    print(f"📁 Saved to: {path}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(download_file())
