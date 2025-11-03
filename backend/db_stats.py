#!/usr/bin/env python3
"""Quick database statistics script"""

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    tables = ['devices', 'credentials', 'credit_cards', 'wallets', 'files', 'software']
    
    print("=== Snatchbase Database Statistics ===")
    for table in tables:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f"{table.capitalize()}: {count:,}")
        except Exception as e:
            print(f"{table.capitalize()}: Error - {e}")
