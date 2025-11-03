"""
Demo script to test the credit card parser integration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.cc_integration import process_stealer_logs
from app.services.cc_parser import parse_cc_from_directory
from app.services.enhanced_password_parser import parse_passwords_from_directory


def test_parser(directory_path: str):
    """Test the parser on a directory"""
    print(f"\n{'='*60}")
    print(f"Testing Stealer Log Parser")
    print(f"Directory: {directory_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Test CC parser
    print("🔍 Parsing Credit Cards...")
    cards = parse_cc_from_directory(directory_path)
    print(f"✅ Found {len(cards)} credit cards\n")
    
    if cards:
        print("Sample Credit Cards:")
        for i, card in enumerate(cards[:5], 1):
            print(f"  {i}. {card.holder}")
            print(f"     Card: ****{card.number[-4:]}")
            print(f"     Exp: {card.expiration}")
            print()
    
    # Test Password parser
    print("🔍 Parsing Passwords/Credentials...")
    creds = parse_passwords_from_directory(directory_path)
    print(f"✅ Found {len(creds)} credentials\n")
    
    if creds:
        print("Sample Credentials:")
        for i, cred in enumerate(creds[:5], 1):
            print(f"  {i}. {cred.domain}")
            print(f"     User: {cred.username}")
            print(f"     URL: {cred.url}")
            print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Credit Cards: {len(cards)}")
    print(f"  Credentials: {len(creds)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cc_parser.py <path_to_stealer_logs>")
        print("\nExample:")
        print("  python test_cc_parser.py /path/to/logs")
        sys.exit(1)
    
    directory = sys.argv[1]
    test_parser(directory)
