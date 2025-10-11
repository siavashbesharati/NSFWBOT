#!/usr/bin/env python3
"""
Test script to manually verify a TON payment and see detailed logs
"""

import asyncio
import logging
from database import Database
from payment_handler import PaymentHandler

# Configure logging to see all details
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def test_payment_verification():
    """Test payment verification with detailed logging"""
    print("🧪 Testing TON Payment Verification")
    print("=" * 50)
    
    # Initialize components
    db = Database()
    payment_handler = PaymentHandler(db)
    
    # Get the most recent pending transaction
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, package_id, amount, created_date, status 
        FROM transactions 
        WHERE payment_method = 'ton' 
        ORDER BY created_date DESC 
        LIMIT 5
    ''')
    
    transactions = cursor.fetchall()
    conn.close()
    
    if not transactions:
        print("❌ No TON transactions found in database")
        return
    
    print(f"📋 Found {len(transactions)} recent TON transactions:")
    for i, (tx_id, user_id, package_id, amount, created_date, status) in enumerate(transactions):
        print(f"   {i+1}. ID: {tx_id}, User: {user_id}, Amount: {amount} TON, Status: {status}, Date: {created_date}")
    
    # Test with the most recent transaction
    transaction_id, user_id, package_id, amount, created_date, status = transactions[0]
    
    print(f"\n🔍 Testing verification for transaction {transaction_id}")
    print(f"   - User ID: {user_id}")
    print(f"   - Amount: {amount} TON")
    print(f"   - Status: {status}")
    print(f"   - Created: {created_date}")
    
    if status != 'pending':
        print(f"⚠️ Transaction is not pending (status: {status})")
        print("Let's check it anyway to see the logs...")
    
    print(f"\n🚀 Starting verification process...")
    print("=" * 50)
    
    # Run verification
    result = await payment_handler.verify_ton_payment(transaction_id)
    
    print("=" * 50)
    print(f"📊 Verification Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Check network settings
    print(f"\n🌐 Network Configuration:")
    print(f"   - Network Mode: {payment_handler.ton_network_mode}")
    print(f"   - Using Testnet: {payment_handler.ton_testnet}")
    print(f"   - API Endpoint: {payment_handler.ton_api_endpoint}")
    print(f"   - Wallet Address: {payment_handler.get_ton_wallet_address()}")
    print(f"   - API Key Set: {'Yes' if payment_handler.ton_api_key else 'No'}")

if __name__ == "__main__":
    asyncio.run(test_payment_verification())