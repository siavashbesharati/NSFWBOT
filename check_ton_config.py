#!/usr/bin/env python3
"""
Check database settings for TON configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database

def check_ton_settings():
    """Check TON-related settings in database"""
    print("🔍 Checking TON Configuration in Database")
    print("=" * 50)
    
    db = Database()
    
    # Check all TON-related settings
    settings_to_check = [
        'ton_network_mode',
        'ton_api_key', 
        'ton_mainnet_wallet_address',
        'ton_testnet_wallet_address'
    ]
    
    for setting in settings_to_check:
        value = db.get_setting(setting, 'NOT_SET')
        if setting == 'ton_api_key' and value != 'NOT_SET':
            # Mask the API key for security
            masked_value = value[:8] + '...' + value[-8:] if len(value) > 16 else value
            print(f"   {setting}: {masked_value}")
        else:
            print(f"   {setting}: {value}")
    
    print(f"\n🌐 Current Network Mode Analysis:")
    network_mode = db.get_setting('ton_network_mode', 'sandbox')
    is_testnet = network_mode == 'sandbox'
    
    print(f"   - Network Mode: {network_mode}")
    print(f"   - Is Testnet: {is_testnet}")
    print(f"   - API Endpoint: {'https://testnet.toncenter.com/api/v2/' if is_testnet else 'https://toncenter.com/api/v2/'}")
    
    wallet_address = db.get_setting('ton_testnet_wallet_address' if is_testnet else 'ton_mainnet_wallet_address', 'NOT_SET')
    print(f"   - Active Wallet: {wallet_address}")
    
    print(f"\n💡 Possible Issues:")
    api_key = db.get_setting('ton_api_key', '')
    
    if not api_key:
        print("   ❌ No API key configured")
    else:
        print("   ✅ API key is configured")
        
    if wallet_address == 'NOT_SET':
        print(f"   ❌ No wallet address configured for {network_mode} mode")
    else:
        print(f"   ✅ Wallet address configured for {network_mode} mode")
        
    if is_testnet:
        print("   ℹ️ Using TESTNET - make sure API key supports testnet")
    else:
        print("   ℹ️ Using MAINNET - make sure API key supports mainnet")

if __name__ == "__main__":
    check_ton_settings()