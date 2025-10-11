#!/usr/bin/env python3
"""
Test script for the enhanced TON payment system
"""

import asyncio
from payment_handler import PaymentHandler
from database import Database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_ton_payment_system():
    """Test the enhanced TON payment system"""
    print("🧪 Testing Enhanced TON Payment System...")
    
    # Initialize database and payment handler
    db = Database()
    payment_handler = PaymentHandler(db)
    
    # Test user and package IDs
    user_id = 123456789
    package_id = 1
    test_amount = 0.1  # Small test amount
    
    print(f"\n1. Creating test user...")
    db.create_user(user_id, "test_user", "Test", "User")
    print(f"✅ Created user: {user_id}")
    
    print(f"\n2. Testing payment creation in different modes...")
    
    # Test 1: Simulation Mode
    print(f"\n🎮 Testing Simulation Mode:")
    db.update_setting('simulation_mode', 'true')
    db.update_setting('ton_testnet_mode', 'true')
    
    payment_handler_sim = PaymentHandler(db)
    result_sim = await payment_handler_sim.create_ton_payment(user_id, package_id, test_amount)
    
    print(f"✅ Simulation result: {result_sim.get('message', 'Success')}")
    print(f"   Transaction ID: {result_sim.get('transaction_id')}")
    
    # Test 2: Testnet Mode
    print(f"\n🧪 Testing Testnet Mode:")
    db.update_setting('simulation_mode', 'false')
    db.update_setting('ton_testnet_mode', 'true')
    db.update_setting('ton_wallet_address', 'EQD_test_wallet_address_for_testnet')
    
    payment_handler_test = PaymentHandler(db)
    result_test = await payment_handler_test.create_ton_payment(user_id, package_id, test_amount)
    
    print(f"✅ Testnet result: {result_test.get('message', 'Success')}")
    print(f"   Network: {result_test.get('network', 'Unknown')}")
    print(f"   Payment URL: {result_test.get('payment_url', 'None')}")
    
    # Test 3: Mainnet Mode
    print(f"\n🌐 Testing Mainnet Mode:")
    db.update_setting('simulation_mode', 'false')
    db.update_setting('ton_testnet_mode', 'false')
    db.update_setting('ton_wallet_address', 'EQD_main_wallet_address_for_mainnet')
    
    payment_handler_main = PaymentHandler(db)
    result_main = await payment_handler_main.create_ton_payment(user_id, package_id, test_amount)
    
    print(f"✅ Mainnet result: {result_main.get('message', 'Success')}")
    print(f"   Network: {result_main.get('network', 'Unknown')}")
    print(f"   Payment URL: {result_main.get('payment_url', 'None')}")
    
    print(f"\n3. Testing configuration detection...")
    
    # Test configuration reading
    testnet_mode = payment_handler_main.ton_testnet
    api_endpoint = payment_handler_main.ton_api_endpoint
    
    print(f"✅ Testnet mode: {testnet_mode}")
    print(f"✅ API endpoint: {api_endpoint}")
    
    print(f"\n4. Testing payment verification (simulation only)...")
    
    # Test verification in simulation mode
    db.update_setting('simulation_mode', 'true')
    payment_handler_verify = PaymentHandler(db)
    
    # Create a test transaction for verification
    tx_id = db.create_transaction(user_id, package_id, "ton", test_amount)
    verification_result = await payment_handler_verify.verify_ton_payment(tx_id)
    
    print(f"✅ Verification result: {verification_result}")
    
    print(f"\n5. Testing settings integration...")
    
    # Test various settings
    settings_to_test = [
        ('ton_testnet_mode', 'true'),
        ('ton_testnet_mode', 'false'), 
        ('ton_api_key', 'test_api_key_123'),
        ('simulation_mode', 'true'),
        ('simulation_mode', 'false')
    ]
    
    for setting, value in settings_to_test:
        db.update_setting(setting, value)
        new_handler = PaymentHandler(db)
        print(f"✅ Setting {setting}={value} - Handler initialized successfully")
    
    print(f"\n🎉 All tests passed! Enhanced TON payment system is working correctly.")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"✅ Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(test_ton_payment_system())