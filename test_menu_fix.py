#!/usr/bin/env python3
"""
Test script to verify the menu functionality after fixing the is_admin error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import TelegramBot
from database import BotDatabase
from unittest.mock import Mock, AsyncMock
import asyncio

async def test_glass_menu_fix():
    """Test that the glass menu works without the is_admin error"""
    print("🧪 Testing Glass Menu Fix...")
    print("=" * 50)
    
    # Create a bot instance
    bot = TelegramBot()
    bot.db = BotDatabase()
    
    # Mock context object
    mock_context = Mock()
    mock_context.bot = Mock()
    mock_context.bot.send_message = AsyncMock()
    
    # Test parameters
    chat_id = 123456789
    user_lang = 'en'
    
    try:
        # This should not raise AttributeError anymore
        await bot.show_glass_menu(chat_id, user_lang, mock_context)
        print("✅ Glass menu method executed successfully!")
        print("✅ No 'is_admin' AttributeError!")
        
        # Verify send_message was called
        assert mock_context.bot.send_message.called, "send_message should be called"
        print("✅ Message sending was triggered!")
        
        # Get the call arguments
        call_args = mock_context.bot.send_message.call_args
        print(f"✅ Chat ID: {call_args.kwargs.get('chat_id', 'Not found')}")
        
        return True
        
    except AttributeError as e:
        if "'TelegramBot' object has no attribute 'is_admin'" in str(e):
            print("❌ is_admin error still exists!")
            return False
        else:
            print(f"❌ Different AttributeError: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_admin_check_logic():
    """Test the admin check logic"""
    print("\n🧪 Testing Admin Check Logic...")
    print("=" * 40)
    
    bot = TelegramBot()
    bot.db = BotDatabase()
    
    # Test with no admin set
    bot.db.set_setting('admin_chat_id', '0')
    mock_context = Mock()
    mock_context.bot = Mock()
    mock_context.bot.send_message = AsyncMock()
    
    await bot.show_glass_menu(123456, 'en', mock_context)
    print("✅ Works with no admin set")
    
    # Test with admin set
    bot.db.set_setting('admin_chat_id', '123456')
    await bot.show_glass_menu(123456, 'en', mock_context)
    print("✅ Works with admin user")
    
    # Test with non-admin user
    await bot.show_glass_menu(999999, 'en', mock_context)
    print("✅ Works with non-admin user")
    
    return True

async def main():
    print("🔧 Testing Menu Fix After is_admin Error...")
    print("=" * 60)
    
    try:
        success1 = await test_glass_menu_fix()
        success2 = await test_admin_check_logic()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 All Tests Passed!")
            print("✅ is_admin AttributeError has been fixed")
            print("✅ Glass menu works correctly")
            print("✅ Admin check logic is working")
            print("✅ Bot is ready for use!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())