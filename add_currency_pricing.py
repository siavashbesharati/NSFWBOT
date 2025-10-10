#!/usr/bin/env python3
"""
Add TON and Stars USD pricing to admin settings
"""

from database import Database
from datetime import datetime

def add_currency_pricing():
    """Add TON and Stars USD pricing to admin settings"""
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("💰 Adding currency pricing to admin settings...")
    
    # Add TON price in USD (current market rate approximately $5.50)
    cursor.execute('''
        INSERT OR REPLACE INTO admin_settings (key, value, updated_date) 
        VALUES (?, ?, ?)
    ''', ('ton_price_usd', '5.50', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    print("  ✅ Added TON price: $5.50 USD")
    
    # Add Stars price in USD (Telegram Stars rate $0.013 per star)
    cursor.execute('''
        INSERT OR REPLACE INTO admin_settings (key, value, updated_date) 
        VALUES (?, ?, ?)
    ''', ('stars_price_usd', '0.013', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    print("  ✅ Added Stars price: $0.013 USD")
    
    conn.commit()
    
    # Verify the settings
    print("\n📊 Current currency pricing:")
    cursor.execute('SELECT key, value FROM admin_settings WHERE key IN ("ton_price_usd", "stars_price_usd")')
    for row in cursor.fetchall():
        print(f"  {row[0]}: ${row[1]}")
    
    conn.close()
    print("\n✅ Currency pricing settings added successfully!")

if __name__ == "__main__":
    add_currency_pricing()