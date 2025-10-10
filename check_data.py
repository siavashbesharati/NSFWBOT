#!/usr/bin/env python3

from database import Database

def check_database():
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()

    print("=== Database Analysis ===")
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nAvailable tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Count records in each table
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"    Records: {count}")
        except Exception as e:
            print(f"    Error counting: {e}")

    # Check message_history data specifically
    print(f"\n=== Message History Analysis ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM message_history")
        total_messages = cursor.fetchone()[0]
        print(f"Total messages: {total_messages}")
        
        cursor.execute("SELECT COUNT(*) FROM message_history WHERE cost > 0")
        messages_with_cost = cursor.fetchone()[0]
        print(f"Messages with cost: {messages_with_cost}")
        
        cursor.execute("SELECT COUNT(*) FROM message_history WHERE prompt_tokens > 0 OR completion_tokens > 0")
        messages_with_tokens = cursor.fetchone()[0]
        print(f"Messages with token data: {messages_with_tokens}")
        
        # Show sample message data
        cursor.execute("SELECT user_id, prompt_tokens, completion_tokens, cost, created_date FROM message_history ORDER BY id DESC LIMIT 5")
        recent_messages = cursor.fetchall()
        print(f"\nRecent messages sample:")
        for msg in recent_messages:
            print(f"  User: {msg[0]}, Prompt: {msg[1]}, Completion: {msg[2]}, Cost: ${msg[3]}, Date: {msg[4]}")
            
    except Exception as e:
        print(f"Error checking message_history: {e}")

    # Check if payment_transactions table exists
    print(f"\n=== Payment Analysis ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM payment_transactions WHERE status='completed'")
        completed_payments = cursor.fetchone()[0]
        print(f"Completed payments: {completed_payments}")
        
        cursor.execute("SELECT SUM(usd_amount) FROM payment_transactions WHERE status='completed'")
        total_revenue = cursor.fetchone()[0] or 0
        print(f"Total revenue: ${total_revenue}")
        
        # Show sample payment data
        cursor.execute("SELECT user_id, amount, currency, usd_amount, status, created_at FROM payment_transactions ORDER BY id DESC LIMIT 5")
        recent_payments = cursor.fetchall()
        print(f"\nRecent payments sample:")
        for payment in recent_payments:
            print(f"  User: {payment[0]}, Amount: {payment[1]} {payment[2]}, USD: ${payment[3]}, Status: {payment[4]}, Date: {payment[5]}")
            
    except Exception as e:
        print(f"Error checking payment_transactions: {e}")
        
        # Try payments table instead
        try:
            cursor.execute("SELECT COUNT(*) FROM payments WHERE status='completed'")
            completed_payments = cursor.fetchone()[0]
            print(f"Completed payments (payments table): {completed_payments}")
            
            cursor.execute("SELECT SUM(usd_amount) FROM payments WHERE status='completed'")
            total_revenue = cursor.fetchone()[0] or 0
            print(f"Total revenue (payments table): ${total_revenue}")
            
        except Exception as e2:
            print(f"Error checking payments table: {e2}")

    conn.close()

if __name__ == "__main__":
    check_database()