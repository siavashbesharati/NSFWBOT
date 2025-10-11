#!/usr/bin/env python3
"""
Test script for the referral system
"""

from database import Database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_referral_system():
    """Test the referral system functionality"""
    print("🧪 Testing Referral System...")
    
    # Initialize database
    db = Database()
    
    # Test user IDs
    referrer_id = 123456789
    referee_id = 987654321
    
    print(f"\n1. Creating test users...")
    # Create test users
    db.create_user(referrer_id, "test_referrer", "Test", "Referrer")
    db.create_user(referee_id, "test_referee", "Test", "Referee")
    
    print(f"✅ Created users: {referrer_id} and {referee_id}")
    
    print(f"\n2. Generating referral code for user {referrer_id}...")
    # Generate referral code for referrer
    referral_code = db.generate_referral_code(referrer_id)
    print(f"✅ Generated referral code: {referral_code}")
    
    print(f"\n3. Getting referral code for user {referrer_id}...")
    # Test getting existing referral code
    existing_code = db.get_user_referral_code(referrer_id)
    print(f"✅ Retrieved existing code: {existing_code}")
    assert referral_code == existing_code, "Referral codes should match"
    
    print(f"\n4. Validating referral code...")
    # Test code validation
    is_valid = db.validate_referral_code(referral_code)
    print(f"✅ Code validation result: {is_valid}")
    assert is_valid, "Referral code should be valid"
    
    print(f"\n5. Processing referral...")
    # Test referral processing
    success = db.process_referral(referee_id, referral_code)
    print(f"✅ Referral processing result: {success}")
    assert success, "Referral processing should succeed"
    
    print(f"\n6. Getting referral statistics...")
    # Test referral stats
    stats = db.get_user_referrals(referrer_id)
    print(f"✅ Referral stats: {stats}")
    assert stats['successful_referrals'] == 1, "Should have 1 successful referral"
    
    print(f"\n7. Checking user credits...")
    # Check if credits were added
    referrer_data = db.get_user(referrer_id)
    referee_data = db.get_user(referee_id)
    
    print(f"Referrer credits: Text={referrer_data['text_messages_left']}, Image={referrer_data['image_messages_left']}, Video={referrer_data['video_messages_left']}")
    print(f"Referee credits: Text={referee_data['text_messages_left']}, Image={referee_data['image_messages_left']}, Video={referee_data['video_messages_left']}")
    
    # Get default rewards
    settings = db.get_all_settings()
    expected_text = int(settings.get('referral_text_reward', 3))
    expected_image = int(settings.get('referral_image_reward', 1))
    expected_video = int(settings.get('referral_video_reward', 1))
    
    assert referrer_data['text_messages_left'] >= expected_text, f"Referrer should have at least {expected_text} text messages"
    assert referee_data['text_messages_left'] >= expected_text, f"Referee should have at least {expected_text} text messages"
    
    print(f"\n8. Testing duplicate referral (should fail)...")
    # Test duplicate referral (should fail)
    duplicate_success = db.process_referral(referee_id, referral_code)
    print(f"✅ Duplicate referral result: {duplicate_success}")
    assert not duplicate_success, "Duplicate referral should fail"
    
    print(f"\n9. Testing invalid code...")
    # Test invalid code
    invalid_valid = db.validate_referral_code("INVALID123")
    print(f"✅ Invalid code validation: {invalid_valid}")
    assert not invalid_valid, "Invalid code should not be valid"
    
    print(f"\n🎉 All tests passed! Referral system is working correctly.")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id IN (?, ?)", (referrer_id, referee_id))
    cursor.execute("DELETE FROM referrals WHERE referrer_id IN (?, ?) OR referee_id IN (?, ?)", 
                  (referrer_id, referee_id, referrer_id, referee_id))
    cursor.execute("DELETE FROM user_referral_codes WHERE user_id IN (?, ?)", (referrer_id, referee_id))
    conn.commit()
    conn.close()
    print(f"✅ Cleanup completed.")

if __name__ == "__main__":
    test_referral_system()