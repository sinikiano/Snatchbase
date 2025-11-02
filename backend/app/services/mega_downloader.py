"""
MEGA.nz File Downloader Service
Downloads files from MEGA links and saves them to the uploads directory
"""
import os
import logging
import subprocess
import random
from pathlib import Path
from dotenv import load_dotenv
import re

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MEGA credentials (optional - for private files or to avoid rate limits)
MEGA_EMAIL = os.getenv('MEGA_EMAIL', '')
MEGA_PASSWORD = os.getenv('MEGA_PASSWORD', '')

# Proxy configuration (to bypass download limits)
MEGA_PROXY = os.getenv('MEGA_PROXY', '')  # Format: socks5://127.0.0.1:1080 or http://proxy:port

# IPVanish SOCKS5 Proxy Pool for rotation
IPVANISH_PROXIES = [
    'kiv.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'rkv.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'cph.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'gru.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'gla.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lin.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'hkg.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'ath.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'vie.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'bog.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'sea.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'zag.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'zrh.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'sjo.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'nyc.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'iev.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'ams.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'sof.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'dub.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'vlc.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'bud.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'tlv.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'man.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'bru.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lux.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'par.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'sel.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lis.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'yul.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'otp.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'jnb.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'akl.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'mel.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'fra.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lon.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'kul.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'beg.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'dxb.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'syd.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'yvr.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'tor.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'waw.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'dal.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'prg.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'phx.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'tll.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'hel.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'bts.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'nrt.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lju.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'lax.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'iad.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'chi.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'rix.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
    'sto.socks.ipvanish.com:1080:tUa2vjkkE:6QhR1TezV',
]

# Download configuration
DOWNLOAD_PATH = Path(__file__).parent.parent.parent / 'data' / 'incoming' / 'uploads'
ALLOWED_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz', '.part1.rar']


class MegaDownloader:
    def __init__(self):
        self.download_path = DOWNLOAD_PATH
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Check if megatools is installed
        try:
            subprocess.run(['megadl', '--version'], 
                          capture_output=True, 
                          check=True)
            logger.info("✅ megatools is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ megatools not found. Install it with: sudo apt install megatools")
            raise RuntimeError("megatools is required but not installed")
    
    def get_random_proxy(self):
        """Get a random proxy from the IPVanish pool"""
        proxy_config = random.choice(IPVANISH_PROXIES)
        host, port, user, password = proxy_config.split(':')
        # Format: socks5://user:password@host:port
        proxy_url = f"socks5://{user}:{password}@{host}:{port}"
        return proxy_url
    
    def create_megarc_config(self):
        """Create .megarc config file if credentials are provided"""
        if MEGA_EMAIL and MEGA_PASSWORD:
            megarc_path = Path.home() / '.megarc'
            config_content = f"""[Login]
Username = {MEGA_EMAIL}
Password = {MEGA_PASSWORD}
"""
            try:
                with open(megarc_path, 'w') as f:
                    f.write(config_content)
                os.chmod(megarc_path, 0o600)  # Secure permissions
                logger.info("✅ MEGA credentials configured")
                return True
            except Exception as e:
                logger.warning(f"Failed to create .megarc: {str(e)}")
                return False
        return False
    
    def download_file(self, url, custom_filename=None):
        """
        Download a file from MEGA URL using megatools
        
        Args:
            url: MEGA download URL
            custom_filename: Optional custom filename (otherwise uses MEGA filename)
        
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"📥 Starting MEGA download from: {url}")
            
            # Create config if credentials available
            self.create_megarc_config()
            
            # Build command
            cmd = [
                'megadl',
                '--path', str(self.download_path),
            ]
            
            # Add proxy - use custom or random from pool
            proxy_to_use = MEGA_PROXY if MEGA_PROXY else self.get_random_proxy()
            logger.info(f"🌐 Using proxy: {proxy_to_use.split('@')[-1]}")  # Log without credentials
            cmd.extend(['--proxy', proxy_to_use])
            
            # Add --print-names to get the filename
            if not custom_filename:
                cmd.append('--print-names')
            
            cmd.append(url)
            
            logger.info(f"Downloading to: {self.download_path}")
            
            # Execute download
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Download failed: {result.stderr}")
                return None
            
            # Get filename from output or use custom
            if custom_filename:
                filename = custom_filename
            else:
                # megadl prints the filename when using --print-names
                filename = result.stdout.strip().split('\n')[-1]
            
            download_file_path = self.download_path / filename
            
            # Verify file exists
            if not download_file_path.exists():
                # Try to find the file by pattern
                files = list(self.download_path.glob('*'))
                if files:
                    # Get the most recently modified file
                    download_file_path = max(files, key=lambda p: p.stat().st_mtime)
                    filename = download_file_path.name
                else:
                    logger.error("❌ Downloaded file not found")
                    return None
            
            file_size = download_file_path.stat().st_size
            logger.info(f"✅ Successfully downloaded: {filename}")
            logger.info(f"   Size: {file_size / 1024 / 1024:.2f} MB")
            logger.info(f"   Saved to: {download_file_path}")
            
            # Check if file extension is allowed
            file_ext = Path(filename).suffix.lower()
            if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                logger.warning(f"⚠️  File extension {file_ext} not in allowed list")
                logger.info(f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}")
            
            return download_file_path
            
        except Exception as e:
            logger.error(f"❌ Error downloading from MEGA: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_multiple(self, urls):
        """
        Download multiple files from MEGA URLs
        
        Args:
            urls: List of MEGA URLs or dict with {url: custom_filename}
        
        Returns:
            List of paths to downloaded files
        """
        downloaded_files = []
        
        if isinstance(urls, dict):
            for url, filename in urls.items():
                result = self.download_file(url, filename)
                if result:
                    downloaded_files.append(result)
        else:
            for url in urls:
                result = self.download_file(url)
                if result:
                    downloaded_files.append(result)
        
        return downloaded_files


def download_from_mega(url, filename=None):
    """
    Convenience function to download a single file from MEGA
    
    Args:
        url: MEGA download URL
        filename: Optional custom filename
    
    Returns:
        Path to downloaded file or None
    """
    downloader = MegaDownloader()
    return downloader.download_file(url, filename)


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mega_downloader.py <MEGA_URL> [custom_filename]")
        print("\nExample:")
        print("  python mega_downloader.py 'https://mega.nz/file/ABC123#XYZ789'")
        print("  python mega_downloader.py 'https://mega.nz/file/ABC123#XYZ789' 'my_file.zip'")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = download_from_mega(url, filename)
    
    if result:
        print(f"\n✅ Download complete: {result}")
        sys.exit(0)
    else:
        print("\n❌ Download failed")
        sys.exit(1)
