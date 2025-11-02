"""
Mega.nz file download functionality
"""
import os
import subprocess
import asyncio
import time
from telegram import Update
from .config import logger, UPLOAD_DIR
from .utils import get_back_button


async def download_mega_file(update: Update, mega_url: str):
    """Download file from Mega.nz link with real-time progress updates"""
    try:
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔗 Detected Mega.nz link!\n"
            f"⏬ Starting download..."
        )
        
        # Download using megatools with progress
        logger.info(f"Downloading from Mega.nz: {mega_url}")
        
        # Start megadl process with progress enabled
        process = subprocess.Popen(
            ['megadl', '--path', str(UPLOAD_DIR), '--print-names', mega_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Track download progress
        start_time = time.time()
        last_update = 0
        filename = None
        
        # Monitor download progress
        while process.poll() is None:
            current_time = time.time()
            
            # Update every 10 seconds
            if current_time - last_update >= 10:
                # Find the newest file being downloaded
                files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
                
                if files:
                    # Get the most recently modified file
                    newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(UPLOAD_DIR, f)))
                    file_path = os.path.join(UPLOAD_DIR, newest_file)
                    
                    # Check if file was modified recently (within last 15 seconds)
                    file_mtime = os.path.getmtime(file_path)
                    if current_time - file_mtime < 15:
                        current_size = os.path.getsize(file_path)
                        current_size_mb = current_size / (1024 * 1024)
                        elapsed = int(current_time - start_time)
                        
                        # Calculate download speed
                        speed_mbps = current_size_mb / elapsed if elapsed > 0 else 0
                        
                        # Create progress bar
                        progress_bar = "▓" * min(20, int(current_size_mb / 10)) + "░" * max(0, 20 - int(current_size_mb / 10))
                        
                        # Update message
                        try:
                            await status_msg.edit_text(
                                f"🔗 Downloading from Mega.nz\n\n"
                                f"📁 File: {newest_file}\n"
                                f"📊 Downloaded: {current_size_mb:.2f} MB\n"
                                f"⚡ Speed: {speed_mbps:.2f} MB/s\n"
                                f"⏱️ Time: {elapsed}s\n\n"
                                f"[{progress_bar}]\n\n"
                                f"⏳ Download in progress..."
                            )
                            filename = newest_file
                        except Exception as e:
                            # Ignore errors during message edit (rate limit, etc.)
                            logger.debug(f"Error updating progress: {str(e)}")
                        
                        last_update = current_time
            
            # Sleep briefly to avoid busy waiting
            await asyncio.sleep(1)
        
        # Get process output
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.strip() if stderr else "Unknown error"
            logger.error(f"Mega download failed: {error_msg}")
            await status_msg.edit_text(
                f"❌ Download failed!\n"
                f"Error: {error_msg}",
                reply_markup=get_back_button()
            )
            return
        
        # Find the downloaded file
        files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        if not files:
            await status_msg.edit_text("❌ Download failed! No file found.", reply_markup=get_back_button())
            return
        
        # Get the most recently modified file
        newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(UPLOAD_DIR, f)))
        file_path = os.path.join(UPLOAD_DIR, newest_file)
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        total_time = int(time.time() - start_time)
        avg_speed = file_size_mb / total_time if total_time > 0 else 0
        
        logger.info(f"Downloaded: {newest_file} ({file_size_mb:.2f} MB)")
        
        # Update final status message
        await status_msg.edit_text(
            f"✅ Download complete!\n\n"
            f"📁 File: {newest_file}\n"
            f"📊 Size: {file_size_mb:.2f} MB\n"
            f"⚡ Avg Speed: {avg_speed:.2f} MB/s\n"
            f"⏱️ Total Time: {total_time}s\n\n"
            f"🔄 The file will be automatically processed by the ingestion service.\n"
            f"⏳ Processing time depends on file size.",
            reply_markup=get_back_button()
        )
        
        logger.info(f"Mega.nz file downloaded successfully: {newest_file}")
        
    except Exception as e:
        logger.error(f"Error downloading Mega.nz file: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error downloading file:\n{str(e)}",
            reply_markup=get_back_button()
        )
