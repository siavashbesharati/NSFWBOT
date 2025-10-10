#!/usr/bin/env python3
"""
Quick script to add sample data for testing the statistics page.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
import random
from datetime import datetime, timedelta

def add_sample_data():
    """Add sample users and transactions for testing statistics"""
    print("📊 Adding sample data for statistics testing...")
    
    db = Database()
    
    # Add some sample users
    sample_users = [
        (12345, "test_user1"),
        (23456, "test_user2"), 
        (34567, "test_user3"),
        (45678, "test_user4"),
        (56789, "test_user5"),
    ]
    
    print("👥 Adding sample users...")
    for user_id, username in sample_users:
        try:
            db.create_user(user_id, username)
            print(f"   ✅ Added user: {username} ({user_id})")
        except Exception as e:
            print(f"   ⚠️  User {username} might already exist: {e}")
    
    # Create a sample package
    print("\n📦 Creating sample package...")
    try:
        package_id = db.create_package(
            name="Premium Package",
            description="Sample premium package for testing",
            text_count=100,
            image_count=50,
            video_count=20,
            ton_price=5.0,
            stars_price=500,
            active=True
        )
        print(f"   ✅ Created package with ID: {package_id}")
    except Exception as e:
        print(f"   ⚠️  Package might already exist: {e}")
        package_id = 1  # Use existing package
    
    # Add some sample transactions
    print("\n💳 Adding sample transactions...")
    
    # Generate transactions over the last 30 days
    for i in range(20):
        user_id = random.choice([u[0] for u in sample_users])
        payment_method = random.choice(['ton', 'stars'])
        
        if payment_method == 'ton':
            amount = round(random.uniform(1.0, 10.0), 2)
        else:
            amount = random.randint(100, 1000)
        
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        transaction_date = datetime.now() - timedelta(days=days_ago)
        
        try:
            transaction_id = db.create_transaction(
                user_id=user_id,
                package_id=package_id,
                payment_method=payment_method,
                amount=amount
            )
            
            # Complete the transaction
            db.complete_transaction(transaction_id, f"test_hash_{i}")
            
            print(f"   ✅ Added {payment_method} transaction: {amount} ({user_id})")
            
        except Exception as e:
            print(f"   ❌ Error adding transaction: {e}")
    
    print("\n🎉 Sample data added successfully!")
    print("📈 You can now view the statistics page with sample data.")

if __name__ == "__main__":
    add_sample_data()