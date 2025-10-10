#!/usr/bin/env python3
"""
Test script for Venice AI integration with rate limiting and monitoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_handler import OpenRouterAPI
import asyncio

async def test_venice_integration():
    """Test the enhanced Venice AI integration."""
    print("🧪 Testing Venice AI Integration...")
    
    # Initialize AI handler
    ai_handler = OpenRouterAPI()
    
    # Test 1: Basic Venice API request
    print("\n1️⃣ Testing basic Venice API request...")
    try:
        response = await ai_handler.generate_text_response("Hello, this is a test message.")
        print(f"✅ Response received: {response[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Venice account status
    print("\n2️⃣ Testing Venice account status...")
    try:
        status = await ai_handler.get_venice_account_status()
        print(f"✅ Account status: {status}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Rate limiting test (multiple requests)
    print("\n3️⃣ Testing rate limiting with multiple requests...")
    for i in range(3):
        try:
            print(f"   Request {i+1}/3...")
            response = await ai_handler.generate_text_response(f"Test message {i+1}")
            print(f"   ✅ Response {i+1}: {len(response)} characters")
        except Exception as e:
            print(f"   ❌ Request {i+1} failed: {e}")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    print("\n🎉 Venice integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_venice_integration())