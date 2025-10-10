#!/usr/bin/env python3
"""
Automated Database Reset Script
Resets all user data, transactions, messages, etc. while preserving admin settings
"""

from database import Database
import os
import shutil
from datetime import datetime

def backup_settings():
    """Backup current admin settings"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("📥 Backing up admin settings...")
    
    # Get all admin settings
    cursor.execute("SELECT key, value FROM admin_settings")
    settings = cursor.fetchall()
    
    print(f"Found {len(settings)} admin settings to preserve")
    
    conn.close()
    return settings

def reset_database_tables(preserved_settings):
    """Reset all tables except preserve admin settings"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("🗑️ Resetting database tables...")
    
    # List of tables to clear (preserve admin_settings)
    tables_to_clear = [
        'users',
        'transactions', 
        'message_history',
        'bot_stats'
    ]
    
    # Clear each table
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  ✅ Cleared {table} table")
        except Exception as e:
            print(f"  ⚠️ Could not clear {table}: {e}")
    
    # Reset auto-increment sequences
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'transactions', 'message_history', 'bot_stats')")
        print("  ✅ Reset auto-increment sequences")
    except Exception as e:
        print(f"  ⚠️ Could not reset sequences: {e}")
    
    # Clear admin_settings and restore preserved ones
    cursor.execute("DELETE FROM admin_settings")
    print("  ✅ Cleared admin_settings table")
    
    # Restore preserved settings
    print("📤 Restoring admin settings...")
    for key, value in preserved_settings:
        cursor.execute("INSERT INTO admin_settings (key, value, updated_date) VALUES (?, ?, ?)", 
                      (key, value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print(f"  ✅ Restored setting: {key}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database reset complete! Preserved {len(preserved_settings)} admin settings")

def show_reset_summary():
    """Show summary after reset"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("\n📊 Reset Summary:")
    
    # Count records in each table
    tables = ['users', 'packages', 'transactions', 'message_history', 'admin_settings', 'bot_stats']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")
    
    # Show preserved settings
    print(f"\n🔧 Preserved Admin Settings:")
    cursor.execute("SELECT key, value FROM admin_settings ORDER BY key")
    settings = cursor.fetchall()
    
    for key, value in settings:
        # Truncate long values for display
        display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"  {key}: {display_value}")
    
    conn.close()

def create_backup():
    """Create a backup of the current database before reset"""
    db_file = "bot_database.db"
    if os.path.exists(db_file):
        backup_filename = f"bot_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_file, backup_filename)
        print(f"💾 Created backup: {backup_filename}")
        return backup_filename
    return None

def main():
    """Main reset function"""
    print("🔄 Database Reset Tool - AUTO MODE")
    print("=" * 50)
    
    try:
        # Create backup
        backup_file = create_backup()
        
        # Backup settings
        settings = backup_settings()
        
        # Reset database
        reset_database_tables(settings)
        
        # Show summary
        show_reset_summary()
        
        print(f"\n✅ Database reset completed successfully!")
        if backup_file:
            print(f"💾 Backup saved as: {backup_file}")
        print(f"🔧 Preserved {len(settings)} admin settings")
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        print("💾 Your original database should be safe")

if __name__ == "__main__":
    main()