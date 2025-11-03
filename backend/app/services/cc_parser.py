"""
Credit Card Parser for Stealer Logs
Integrated from: https://github.com/milxss/universal_stealer_log_parser
"""
import os
from typing import List, Tuple, Optional


class CreditCard:
    """Credit card information container"""
    def __init__(self, number: str, expiration: str, holder: str):
        self.number = number
        self.expiration = expiration
        self.holder = holder
    
    def to_dict(self):
        return {
            'number': self.number,
            'expiration': self.expiration,
            'holder': self.holder
        }


def extract_cc_info(file_path: str) -> List[Tuple[str, str, str]]:
    """
    Extract credit card information from a file (Raccoon format)
    
    Args:
        file_path: Path to the CC file
        
    Returns:
        List of tuples (cc_number, expiration, card_holder)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contents = f.read()
    except UnicodeDecodeError:
        print(f"Cannot read file '{file_path}' with encoding 'utf-8'. Skipping file...")
        return []
    
    cc_info_list = contents.split('\n\n')
    cc_info = []
    
    for info in cc_info_list:
        if info.strip() == '':
            continue
        
        cc_number = None
        if 'CC NUMBER: ' in info:
            cc_number = info.split('CC NUMBER: ')[1].split('\n')[0]
        elif 'Card: ' in info:
            cc_number = info.split('Card: ')[1].split('\n')[0]
        
        if cc_number:
            month = None
            year = None
            if 'EXPIRATION: ' in info:
                expiration_str = info.split('EXPIRATION: ')[1].split('\n')[0]
                month, year = expiration_str.split("/")
            elif 'Month: ' in info and 'Year: ' in info:
                month_str = info.split('Month: ')[1].split('\n')[0]
                year_str = info.split('Year: ')[1].split('\n')[0]
                month = month_str.strip()
                year = year_str.strip()
            
            if year is None:
                continue
            
            card_holder = None
            if 'CARD HOLDER: ' in info:
                card_holder = info.split('CARD HOLDER: ')[1].split('\n')[0]
            elif 'Name: ' in info:
                card_holder = info.split('Name: ')[1].split('\n')[0]
            
            if card_holder:
                cc_info.append((cc_number, f"{month}/{year}", card_holder))
    
    return cc_info


def extract_cc_info_v2(file_path: str) -> List[Tuple[str, str, str]]:
    """
    Extract credit card information from a file (RedLine format)
    
    Args:
        file_path: Path to the CC file
        
    Returns:
        List of tuples (cc_number, expiration, card_holder)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contents = f.read()
    except UnicodeDecodeError:
        print(f"Cannot read file '{file_path}' with encoding 'utf-8'. Skipping file...")
        return []
    
    cc_info_list = []
    if 'Card: ' in contents:
        cc_number = contents.split('Card: ')[1].split('\n')[0]
        if 'Expire: ' in contents:
            exp_str = contents.split('Expire: ')[1].split('\n')[0]
            exp_month, exp_year = exp_str.split('/')
            if 'Holder: ' in contents:
                card_holder = contents.split('Holder: ')[1].split('\n')[0]
                cc_info_list.append((cc_number, f"{exp_month}/{exp_year}", card_holder))
    
    return cc_info_list


def parse_cc_from_directory(directory_path: str) -> List[CreditCard]:
    """
    Parse all credit card files in a directory and its subdirectories
    
    Args:
        directory_path: Path to the directory containing stealer logs
        
    Returns:
        List of CreditCard objects
    """
    all_cards = []
    
    for dirpath, dirnames, filenames in os.walk(directory_path):
        # Check for CC directories
        cc_dirs = [d for d in dirnames if "CC" in d.upper() or "CREDITCARDS" in d.upper()]
        
        for cc_dir in cc_dirs:
            cc_dir_path = os.path.join(dirpath, cc_dir)
            for filename in os.listdir(cc_dir_path):
                if filename.lower().endswith('.txt'):
                    file_path = os.path.join(cc_dir_path, filename)
                    
                    # Try both formats
                    cc_info_list = extract_cc_info(file_path)
                    if not cc_info_list:
                        cc_info_list = extract_cc_info_v2(file_path)
                    
                    for cc_number, expiration, card_holder in cc_info_list:
                        all_cards.append(CreditCard(cc_number, expiration, card_holder))
        
        # Process any CC.txt files in the current directory
        for filename in filenames:
            if filename.lower() == 'cc.txt' or (filename.lower().endswith('.txt') and 'cc' in filename.lower()):
                file_path = os.path.join(dirpath, filename)
                
                # Try both formats
                cc_info_list = extract_cc_info(file_path)
                if not cc_info_list:
                    cc_info_list = extract_cc_info_v2(file_path)
                
                for cc_number, expiration, card_holder in cc_info_list:
                    all_cards.append(CreditCard(cc_number, expiration, card_holder))
    
    return all_cards


def parse_cc_from_file(file_path: str) -> List[CreditCard]:
    """
    Parse credit cards from a single file
    
    Args:
        file_path: Path to the CC file
        
    Returns:
        List of CreditCard objects
    """
    cards = []
    
    # Try both formats
    cc_info_list = extract_cc_info(file_path)
    if not cc_info_list:
        cc_info_list = extract_cc_info_v2(file_path)
    
    for cc_number, expiration, card_holder in cc_info_list:
        cards.append(CreditCard(cc_number, expiration, card_holder))
    
    return cards
