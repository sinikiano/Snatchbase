"""
Enhanced Password/Credential Parser for Stealer Logs
Integrated from: https://github.com/milxss/universal_stealer_log_parser
Supports: Raccoon, StealC, RedLine, Aurora, Meta, and other stealers
"""
import os
from urllib.parse import urlsplit
from typing import List, Dict


class Credential:
    """Credential information container"""
    def __init__(self, url: str, username: str, password: str, source_file: str = ""):
        self.url = url
        self.username = username
        self.password = password
        self.source_file = source_file
        self.domain = self._extract_domain(url)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        
        try:
            if url.startswith("android"):
                # Handle Android app packages
                package_name = url.split("@")[-1]
                return package_name
            else:
                url_components = urlsplit(url)
                domain = url_components.netloc or url_components.path
                # Remove www. prefix
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain
        except:
            return url
    
    def to_dict(self):
        return {
            'url': self.url,
            'domain': self.domain,
            'username': self.username,
            'password': self.password,
            'source_file': self.source_file
        }


def extract_passwords_raccoon(file_path: str) -> List[Credential]:
    """
    Extract passwords from Raccoon stealer format
    
    Format:
        URL: <url>
        USER: <username>
        PASS: <password>
    
    Args:
        file_path: Path to passwords.txt file
        
    Returns:
        List of Credential objects
    """
    credentials = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
    except UnicodeDecodeError:
        print(f"Error: Unable to read file {file_path}. Skipping...")
        return []
    
    # Split into individual entries
    entries = contents.split("\n\n")
    
    for entry in entries:
        lines = entry.split("\n")
        url = ""
        user = ""
        password = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract URL
            if line.startswith("URL:") or line.startswith("url:") or line.startswith("Url:"):
                url = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.startswith("Host:") or line.startswith("HOSTNAME:"):
                url = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # Extract username
            elif any(line.startswith(prefix) for prefix in ["USER:", "login:", "Login:", "Username:", "USER LOGIN:"]):
                user = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # Extract password
            elif any(line.startswith(prefix) for prefix in ["PASS:", "password:", "Password:", "USER PASSWORD:"]):
                password = line.split(":", 1)[1].strip() if ":" in line else ""
        
        # Only add if we have at least a URL
        if url:
            # Normalize URL
            if url.startswith("android"):
                package_name = url.split("@")[-1]
                package_name = package_name.replace("-", "").replace("_", "").replace(".", "")
                package_name = ".".join(package_name.split("/")[::-1])
                package_name = ".".join(package_name.split(".")[::-1])
                url = f"{package_name}android.app"
            else:
                try:
                    url_components = urlsplit(url)
                    if url_components.scheme and url_components.netloc:
                        url = f"{url_components.scheme}://{url_components.netloc}"
                except:
                    pass
            
            credentials.append(Credential(url, user, password, file_path))
    
    return credentials


def extract_passwords_redline(file_path: str) -> List[Credential]:
    """
    Extract passwords from RedLine stealer format
    
    Format:
        ===============
        URL: <url>
        USER: <username>
        PASS: <password>
    
    Args:
        file_path: Path to passwords.txt file
        
    Returns:
        List of Credential objects
    """
    credentials = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
    except UnicodeDecodeError:
        print(f"Error: Unable to read file {file_path}. Skipping...")
        return []
    
    # Split by separator
    entries = contents.split("===============\n")
    
    for entry in entries:
        lines = entry.strip().split("\n")
        url = ""
        user = ""
        password = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract URL
            if any(line.startswith(prefix) for prefix in ["URL:", "url:", "Url:", "Host:", "HOSTNAME:"]):
                url = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # Extract username
            elif any(line.startswith(prefix) for prefix in ["USER:", "login:", "Login:", "Username:", "USER LOGIN:"]):
                user = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # Extract password
            elif any(line.startswith(prefix) for prefix in ["PASS:", "password:", "Password:", "USER PASSWORD"]):
                password = line.split(":", 1)[1].strip() if ":" in line else ""
        
        # Only add if we have at least a URL
        if url:
            # Normalize URL
            if url.startswith("android"):
                package_name = url.split("@")[-1]
                package_name = package_name.replace("-", "").replace("_", "").replace(".", "")
                package_name = ".".join(package_name.split("/")[::-1])
                package_name = ".".join(package_name.split(".")[::-1])
                url = f"{package_name}android.app"
            else:
                try:
                    url_components = urlsplit(url)
                    if url_components.scheme and url_components.netloc:
                        url = f"{url_components.scheme}://{url_components.netloc}"
                except:
                    pass
            
            credentials.append(Credential(url, user, password, file_path))
    
    return credentials


def parse_passwords_from_directory(directory_path: str) -> List[Credential]:
    """
    Parse all password files in a directory and its subdirectories
    Supports multiple stealer formats
    
    Args:
        directory_path: Path to the directory containing stealer logs
        
    Returns:
        List of Credential objects
    """
    all_credentials = []
    password_files = ["passwords.txt", "Password List.txt", "_AllPasswords_list.txt"]
    
    for subdir, dirs, files in os.walk(directory_path):
        for file in files:
            # Check if it's a password file
            if file.lower() in [pf.lower() for pf in password_files]:
                file_path = os.path.join(subdir, file)
                
                # Try Raccoon format first
                creds = extract_passwords_raccoon(file_path)
                
                # If no results, try RedLine format
                if not creds:
                    creds = extract_passwords_redline(file_path)
                
                all_credentials.extend(creds)
    
    return all_credentials


def parse_passwords_from_file(file_path: str) -> List[Credential]:
    """
    Parse passwords from a single file
    Automatically detects format
    
    Args:
        file_path: Path to the password file
        
    Returns:
        List of Credential objects
    """
    # Try Raccoon format first
    creds = extract_passwords_raccoon(file_path)
    
    # If no results, try RedLine format
    if not creds:
        creds = extract_passwords_redline(file_path)
    
    return creds
