#!/usr/bin/env python3
"""
Test TON API access with and without API key
"""

import asyncio
import aiohttp
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database

async def test_ton_api():
    """Test TON API access"""
    print("🧪 Testing TON API Access")
    print("=" * 50)
    
    db = Database()
    
    # Test both with and without API key
    testnet_endpoint = "https://testnet.toncenter.com/api/v2/"
    mainnet_endpoint = "https://toncenter.com/api/v2/"
    wallet_address = "kQBwmbT0oTZvljngHQT7QXX2ewHz5Ya21O24Ct573_H3yBp2"
    api_key = db.get_setting('ton_api_key', '')
    
    tests = [
        ("Testnet WITHOUT API key", testnet_endpoint, None),
        ("Testnet WITH API key", testnet_endpoint, api_key),
        ("Mainnet WITHOUT API key", mainnet_endpoint, None),
        ("Mainnet WITH API key", mainnet_endpoint, api_key),
    ]
    
    for test_name, endpoint, key in tests:
        print(f"\n🔍 Testing: {test_name}")
        print(f"   Endpoint: {endpoint}")
        print(f"   API Key: {'Yes' if key else 'No'}")
        
        url = f"{endpoint}getTransactions"
        params = {
            'address': wallet_address,
            'limit': 10,
            'to_lt': 0,
            'archival': 'true'
        }
        
        if key:
            params['api_key'] = key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            transactions = data.get('result', [])
                            print(f"   ✅ SUCCESS: Found {len(transactions)} transactions")
                        else:
                            print(f"   ❌ API Error: {data}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ HTTP Error: {error_text}")
                        
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
    
    print(f"\n📋 Summary:")
    print(f"   - Your testnet wallet: {wallet_address}")
    print(f"   - Expected transaction: Payment_26_328410861 for 0.5 TON")
    print(f"   - Check your transaction manually at:")
    print(f"     https://testnet.tonviewer.com/{wallet_address}")

if __name__ == "__main__":
    asyncio.run(test_ton_api())