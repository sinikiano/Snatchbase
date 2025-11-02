"""
Password file parser - extracts credentials from stealer log password files
Ported from bron-vault's TypeScript implementation
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Credential:
    """Parsed credential"""
    url: str
    domain: Optional[str]
    tld: Optional[str]
    username: str
    password: str
    browser: Optional[str]


@dataclass
class PasswordFileStats:
    """Statistics from parsing a password file"""
    credential_count: int
    domain_count: int
    url_count: int
    password_counts: Dict[str, int]
    credentials: List[Credential]


class PasswordFileParser:
    """Parser for stealer log password files"""
    
    # Common password file names
    PASSWORD_FILE_NAMES = {
        "all passwords.txt",
        "all_passwords.txt",
        "passwords.txt",
        "allpasswords_list.txt",
        "_allpasswords_list",
        "password.txt",
        "pass.txt",
        "all_pass.txt",
        "all pass.txt",
        "password_list.txt",
        "passlist.txt",
        "creds.txt",
        "credentials.txt",
        "logins.txt",
        "login.txt",
        "accounts.txt",
    }
    
    def is_password_file(self, filename: str) -> bool:
        """Check if filename is a password file"""
        filename_lower = filename.lower()
        # Check exact match first
        if filename_lower in self.PASSWORD_FILE_NAMES:
            return True
        # Check if filename contains common password keywords
        password_keywords = ["password", "pass", "login", "cred", "account"]
        return any(keyword in filename_lower for keyword in password_keywords) and filename_lower.endswith('.txt')
    
    def parse_password_file(self, content: str) -> PasswordFileStats:
        """Parse password file content and extract credentials"""
        result = PasswordFileStats(
            credential_count=0,
            domain_count=0,
            url_count=0,
            password_counts=defaultdict(int),
            credentials=[],
        )
        
        if not content or not content.strip():
            return result
        
        lines = content.split("\n")
        
        # First pass: count credentials, URLs, and passwords
        for line in lines:
            trimmed_line = line.strip()
            if not trimmed_line:
                continue
            
            lower_line = trimmed_line.lower()
            
            # Count credentials by looking for "password:" or "pass:"
            if "password:" in lower_line or "pass:" in lower_line:
                password = self._extract_value(trimmed_line)
                if password:
                    result.credential_count += 1
                    result.password_counts[password] += 1
            
            # Count URLs and domains
            if any(keyword in lower_line for keyword in ["url:", "host:", "hostname:"]):
                url = self._extract_value(trimmed_line)
                if url:
                    result.url_count += 1
                    
                    # Check if it's not an IP address for domain count
                    if not self._is_ip_address(url):
                        result.domain_count += 1
        
        # Second pass: parse complete credentials
        current_credential = {}
        
        for line in lines:
            trimmed_line = line.strip()
            
            # Empty line or separator (=====, _____, -----) signals end of credential block
            if not trimmed_line or (len(set(trimmed_line)) == 1 and trimmed_line[0] in "=_-|"):
                if self._is_valid_credential(current_credential):
                    url_info = self._extract_url_info(current_credential["url"])
                    result.credentials.append(
                        Credential(
                            url=current_credential["url"],
                            domain=url_info["domain"],
                            tld=url_info["tld"],
                            username=current_credential["username"],
                            password=current_credential["password"],
                            browser=current_credential.get("browser"),
                        )
                    )
                current_credential = {}
                continue
            
            lower_line = trimmed_line.lower()
            
            # Parse credential fields
            if any(keyword in lower_line for keyword in ["url:", "host:", "hostname:"]):
                current_credential["url"] = self._extract_value(trimmed_line)
            elif any(keyword in lower_line for keyword in ["username:", "user:", "login:"]):
                current_credential["username"] = self._extract_value(trimmed_line)
            elif "password:" in lower_line or "pass:" in lower_line:
                current_credential["password"] = self._extract_value(trimmed_line)
            elif any(keyword in lower_line for keyword in ["browser:", "soft:", "application:"]):
                current_credential["browser"] = self._extract_value(trimmed_line)
        
        # Add the last credential if valid
        if self._is_valid_credential(current_credential):
            url_info = self._extract_url_info(current_credential["url"])
            result.credentials.append(
                Credential(
                    url=current_credential["url"],
                    domain=url_info["domain"],
                    tld=url_info["tld"],
                    username=current_credential["username"],
                    password=current_credential["password"],
                    browser=current_credential.get("browser"),
                )
            )
        
        return result
    
    def _extract_value(self, line: str) -> str:
        """Extract value after colon in a line"""
        colon_index = line.find(":")
        if colon_index != -1:
            return line[colon_index + 1:].strip()
        return line.strip()
    
    def _is_valid_credential(self, credential: Dict) -> bool:
        """Check if credential has required fields"""
        return bool(
            credential.get("url") and 
            credential.get("username") and 
            credential.get("password")
        )
    
    def _is_ip_address(self, url: str) -> bool:
        """Check if URL is an IP address"""
        try:
            hostname = url.strip()
            hostname = re.sub(r"^https?://", "", hostname)
            hostname = hostname.split("/")[0]
            hostname = hostname.split(":")[0]
            
            # Simple IPv4 regex
            ip_regex = r"^(\d{1,3}\.){3}\d{1,3}$"
            return bool(re.match(ip_regex, hostname))
        except:
            return False
    
    def _extract_url_info(self, url: str) -> Dict[str, Optional[str]]:
        """Extract domain and TLD from URL"""
        try:
            if not url or not url.strip():
                return {"domain": None, "tld": None}
            
            clean_url = url.strip()
            clean_url = re.sub(r"^https?://", "", clean_url)
            clean_url = re.sub(r"^www\.", "", clean_url)
            
            hostname = clean_url.split("/")[0].split(":")[0].lower()
            
            # Check if it's an IP address
            if self._is_ip_address(url):
                return {"domain": hostname, "tld": None}
            
            # Extract domain and TLD
            parts = hostname.split(".")
            if len(parts) >= 2:
                tld = parts[-1]
                domain = ".".join(parts[-2:]) if len(parts) > 2 else hostname
                return {"domain": domain, "tld": tld}
            
            return {"domain": hostname, "tld": None}
        except:
            return {"domain": None, "tld": None}


def escape_password(password: str) -> str:
    """Escape special characters in password for safe storage"""
    if not password:
        return password
    
    # Remove NULL bytes (0x00) - PostgreSQL cannot store them
    password = password.replace("\0", "")
    
    # Escape special characters that could cause parsing issues
    return (password
        .replace("\\", "\\\\")  # Escape backslash first
        .replace("'", "\\'")    # Escape single quotes
        .replace('"', '\\"')    # Escape double quotes
        .replace("\n", "\\n")   # Escape newlines
        .replace("\r", "\\r")   # Escape carriage returns
        .replace("\t", "\\t"))  # Escape tabs


def has_special_characters(password: str) -> bool:
    """Check if password contains special characters"""
    if not password:
        return False
    
    special_chars = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]"
    return bool(re.search(special_chars, password))
