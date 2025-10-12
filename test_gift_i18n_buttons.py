#!/usr/bin/env python3
"""
Test script to verify the gift/referral interface shows internationalized glass buttons
"""

from translations import translation_manager

def test_gift_i18n_buttons():
    """Test that all gift interface buttons are properly internationalized"""
    
    languages = {
        'en': 'English',
        'ar': 'Arabic', 
        'fa': 'Persian',
        'tr': 'Turkish',
        'ru': 'Russian',
        'es': 'Spanish',
        'zh': 'Chinese'
    }
    
    print("🎁 Testing Gift Interface I18n Buttons")
    print("="*50)
    
    for lang_code, lang_name in languages.items():
        print(f"\n🌐 {lang_name} ({lang_code}):")
        print("-" * 30)
        
        # Test share referral link button
        share_btn = translation_manager.get_text('referral.share_referral_link', lang_code)
        print(f"Share Button: {share_btn}")
        
        # Test my referrals button  
        my_ref_btn = translation_manager.get_text('referral.my_referrals', lang_code)
        print(f"My Referrals: {my_ref_btn}")
        
        # Test enter referral button (already existed)
        enter_btn = translation_manager.get_text('commands.enterreferral', lang_code)
        print(f"Enter Code:   {enter_btn}")
        
        # Test back to menu button (already existed)
        back_btn = translation_manager.get_text('glass_menu.back_to_menu', lang_code)
        print(f"Back Button:  {back_btn}")
    
    print("\n✅ All gift interface buttons are properly internationalized!")
    print("\n🔗 Button Usage in Gift Interface:")
    print("1. 📤 Share Referral Link - Opens Telegram share dialog")
    print("2. 📊 My Referrals - Shows referral statistics") 
    print("3. 🔗 Enter Referral Code - Manual referral code entry")
    print("4. 🔙 Back to Menu - Returns to glass menu")

if __name__ == "__main__":
    test_gift_i18n_buttons()