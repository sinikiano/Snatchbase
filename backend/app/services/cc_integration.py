"""
Credit Card Integration Service
Integrates CC parsing into the ZIP ingestion process
"""
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

from app.services.cc_parser import parse_cc_from_directory, parse_cc_from_file, CreditCard
from app.services.enhanced_password_parser import parse_passwords_from_directory, Credential
from app.database import SessionLocal
from app.models import CreditCard as CreditCardModel, Credential as CredentialModel

logger = logging.getLogger(__name__)


def detect_card_brand(card_number: str) -> str:
    """
    Detect credit card brand from card number
    
    Args:
        card_number: Credit card number
        
    Returns:
        Brand name (Visa, Mastercard, Amex, Discover, etc.)
    """
    # Remove spaces and dashes
    clean_number = card_number.replace(' ', '').replace('-', '')
    
    if not clean_number.isdigit():
        return "Unknown"
    
    # Visa: starts with 4
    if clean_number[0] == '4':
        return "Visa"
    
    # Mastercard: starts with 51-55 or 2221-2720
    if clean_number[:2] in ['51', '52', '53', '54', '55']:
        return "Mastercard"
    if len(clean_number) >= 4 and 2221 <= int(clean_number[:4]) <= 2720:
        return "Mastercard"
    
    # American Express: starts with 34 or 37
    if clean_number[:2] in ['34', '37']:
        return "American Express"
    
    # Discover: starts with 6011, 622126-622925, 644-649, 65
    if clean_number[:4] == '6011':
        return "Discover"
    if len(clean_number) >= 6 and 622126 <= int(clean_number[:6]) <= 622925:
        return "Discover"
    if len(clean_number) >= 3 and 644 <= int(clean_number[:3]) <= 649:
        return "Discover"
    if clean_number[:2] == '65':
        return "Discover"
    
    # JCB: starts with 3528-3589
    if len(clean_number) >= 4 and 3528 <= int(clean_number[:4]) <= 3589:
        return "JCB"
    
    # Diners Club: starts with 300-305, 36, 38
    if len(clean_number) >= 3 and 300 <= int(clean_number[:3]) <= 305:
        return "Diners Club"
    if clean_number[:2] in ['36', '38']:
        return "Diners Club"
    
    return "Unknown"


def mask_card_number(card_number: str) -> str:
    """
    Mask credit card number showing only last 4 digits
    
    Args:
        card_number: Credit card number
        
    Returns:
        Masked card number (e.g., ****1234)
    """
    clean_number = card_number.replace(' ', '').replace('-', '')
    if len(clean_number) >= 4:
        return f"****{clean_number[-4:]}"
    return "****"


def process_credit_cards_for_device(
    directory_path: str,
    device_id: str,
    db_session=None
) -> List[Dict]:
    """
    Process credit cards from a device directory and save to database
    
    Args:
        directory_path: Path to the device directory
        device_id: Device ID to associate credit cards with
        db_session: Database session (optional)
        
    Returns:
        List of processed credit card dicts
    """
    cards = parse_cc_from_directory(directory_path)
    
    if not cards:
        logger.info(f"No credit cards found for device {device_id}")
        return []
    
    logger.info(f"Found {len(cards)} credit cards for device {device_id}")
    
    # Convert to database models
    db_cards = []
    close_session = False
    
    try:
        if db_session is None:
            db_session = SessionLocal()
            close_session = True
        
        for card in cards:
            # Detect brand
            brand = detect_card_brand(card.number)
            masked = mask_card_number(card.number)
            
            cc_model = CreditCardModel(
                device_id=device_id,
                card_number=card.number,
                card_number_masked=masked,
                expiration=card.expiration,
                cardholder_name=card.holder,
                card_brand=brand,
                source_file=getattr(card, 'source_file', '')
            )
            
            db_session.add(cc_model)
            db_cards.append({
                'number': card.number,
                'masked': masked,
                'expiration': card.expiration,
                'holder': card.holder,
                'brand': brand
            })
        
        db_session.commit()
        logger.info(f"Saved {len(db_cards)} credit cards to database for device {device_id}")
        
    except Exception as e:
        logger.error(f"Error processing credit cards for device {device_id}: {e}")
        if db_session:
            db_session.rollback()
    finally:
        if close_session and db_session:
            db_session.close()
    
    return db_cards


def process_enhanced_passwords_for_device(
    directory_path: str,
    device_id: str,
    browser: str = "Unknown",
    stealer_name: str = "Unknown",
    db_session=None
) -> List[Dict]:
    """
    Process passwords using enhanced parser and save to database
    
    Args:
        directory_path: Path to the device directory
        device_id: Device ID to associate credentials with
        browser: Browser name
        stealer_name: Stealer malware name
        db_session: Database session (optional)
        
    Returns:
        List of processed credential dicts
    """
    credentials = parse_passwords_from_directory(directory_path)
    
    if not credentials:
        logger.info(f"No credentials found for device {device_id}")
        return []
    
    logger.info(f"Found {len(credentials)} credentials for device {device_id}")
    
    db_creds = []
    close_session = False
    
    try:
        if db_session is None:
            db_session = SessionLocal()
            close_session = True
        
        for cred in credentials:
            # Extract TLD from domain
            tld = ""
            if cred.domain:
                parts = cred.domain.split('.')
                if len(parts) > 1:
                    tld = parts[-1]
            
            cred_model = CredentialModel(
                device_id=device_id,
                url=cred.url,
                domain=cred.domain,
                tld=tld,
                username=cred.username,
                password=cred.password,
                browser=browser,
                stealer_name=stealer_name,
                file_path=cred.source_file
            )
            
            db_session.add(cred_model)
            db_creds.append(cred.to_dict())
        
        db_session.commit()
        logger.info(f"Saved {len(db_creds)} credentials to database for device {device_id}")
        
    except Exception as e:
        logger.error(f"Error processing credentials for device {device_id}: {e}")
        if db_session:
            db_session.rollback()
    finally:
        if close_session and db_session:
            db_session.close()
    
    return db_creds


def process_stealer_logs(
    directory_path: str,
    device_id: str,
    browser: str = "Chrome",
    stealer_name: str = "Unknown",
    include_cc: bool = True,
    include_passwords: bool = True,
    db_session=None
) -> Dict:
    """
    Process both credit cards and passwords from stealer logs
    
    Args:
        directory_path: Path to the device directory
        device_id: Device ID
        browser: Browser name
        stealer_name: Stealer malware name
        include_cc: Process credit cards
        include_passwords: Process passwords
        db_session: Database session (optional)
        
    Returns:
        Dictionary with processing results
    """
    results = {
        'credit_cards': [],
        'credentials': [],
        'stats': {
            'cc_count': 0,
            'credential_count': 0
        }
    }
    
    try:
        if include_cc:
            results['credit_cards'] = process_credit_cards_for_device(
                directory_path, device_id, db_session
            )
            results['stats']['cc_count'] = len(results['credit_cards'])
        
        if include_passwords:
            results['credentials'] = process_enhanced_passwords_for_device(
                directory_path, device_id, browser, stealer_name, db_session
            )
            results['stats']['credential_count'] = len(results['credentials'])
        
        logger.info(
            f"Processed device {device_id}: "
            f"{results['stats']['cc_count']} CCs, "
            f"{results['stats']['credential_count']} credentials"
        )
        
    except Exception as e:
        logger.error(f"Error processing stealer logs for device {device_id}: {e}")
    
    return results
