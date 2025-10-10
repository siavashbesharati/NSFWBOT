#!/usr/bin/env python3
"""
Test script to verify TON price update functionality
"""

import requests
import json

def test_ton_price_api():
    """Test the TON price update API endpoint"""
    print("🧪 Testing TON Price Update API")
    print("=" * 40)
    
    # API endpoint
    url = "http://127.0.0.1:5000/api/ton_price/update"
    
    try:
        # Make request to update TON price
        response = requests.post(url, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"📊 Success: {data.get('success')}")
            print(f"💰 TON Price: ${data.get('price', 'N/A')}")
            print(f"📝 Message: {data.get('message', 'N/A')}")
        else:
            print(f"❌ API Response: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_currency_converter_directly():
    """Test the currency converter directly"""
    print("\n🔄 Testing Currency Converter Directly")
    print("=" * 40)
    
    try:
        from currency_converter import CurrencyConverter
        converter = CurrencyConverter()
        
        print("📡 Fetching TON price from CoinGecko...")
        ton_price = converter.get_ton_to_usd_rate()
        
        if ton_price and ton_price > 0:
            print(f"✅ TON Price: ${ton_price:.4f} USD")
        else:
            print(f"❌ Failed to fetch TON price: {ton_price}")
            
    except Exception as e:
        print(f"❌ Error testing currency converter: {e}")

if __name__ == "__main__":
    test_currency_converter_directly()
    test_ton_price_api()