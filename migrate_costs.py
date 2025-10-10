#!/usr/bin/env python3
"""
Migration script to calculate costs for existing message_history records
and ensure all financial data is properly populated
"""

from database import Database
import json

def migrate_message_costs():
    """Calculate costs for existing messages that don't have cost data"""
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("=== Message Cost Migration ===")
    
    # Get token pricing settings
    cursor.execute("SELECT key, value FROM admin_settings WHERE key LIKE '%token_price%'")
    settings = {}
    for row in cursor.fetchall():
        settings[row[0]] = float(row[1])
    
    input_price = settings.get('input_token_price_per_1m', 0.0) / 1_000_000  # Price per token
    output_price = settings.get('output_token_price_per_1m', 0.0) / 1_000_000  # Price per token
    
    print(f"Input token price: ${input_price:.8f} per token")
    print(f"Output token price: ${output_price:.8f} per token")
    
    # Find messages without cost calculation
    cursor.execute("""
        SELECT id, prompt_tokens, completion_tokens, total_tokens, cost 
        FROM message_history 
        WHERE (prompt_tokens > 0 OR completion_tokens > 0) 
        AND (cost IS NULL OR cost = 0)
    """)
    
    messages_to_update = cursor.fetchall()
    print(f"Found {len(messages_to_update)} messages without cost calculation")
    
    updated_count = 0
    for message in messages_to_update:
        msg_id, prompt_tokens, completion_tokens, total_tokens, current_cost = message
        
        # Calculate cost
        prompt_tokens = prompt_tokens or 0
        completion_tokens = completion_tokens or 0
        
        cost = (prompt_tokens * input_price) + (completion_tokens * output_price)
        
        if cost > 0:
            cursor.execute("""
                UPDATE message_history 
                SET cost = ? 
                WHERE id = ?
            """, (cost, msg_id))
            
            updated_count += 1
            print(f"  Updated message {msg_id}: {prompt_tokens} + {completion_tokens} tokens = ${cost:.6f}")
    
    conn.commit()
    print(f"Updated {updated_count} messages with cost calculations")
    
    # Show summary
    cursor.execute("SELECT COUNT(*) FROM message_history WHERE cost > 0")
    messages_with_cost = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(cost) FROM message_history WHERE cost > 0")
    total_spending = cursor.fetchone()[0] or 0
    
    print(f"\nFinal summary:")
    print(f"  Messages with cost: {messages_with_cost}")
    print(f"  Total AI spending: ${total_spending:.6f}")
    
    conn.close()

def show_financial_summary():
    """Show current financial data summary"""
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("\n=== Financial Summary ===")
    
    # AI Spending
    cursor.execute("SELECT COUNT(*), SUM(cost) FROM message_history WHERE cost > 0")
    spending_data = cursor.fetchone()
    total_messages = spending_data[0] or 0
    total_spending = spending_data[1] or 0.0
    
    print(f"AI Spending:")
    print(f"  Messages with cost: {total_messages}")
    print(f"  Total spending: ${total_spending:.6f}")
    
    # Revenue
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE status = 'completed'")
    revenue_data = cursor.fetchone()
    total_payments = revenue_data[0] or 0
    total_revenue = revenue_data[1] or 0.0
    
    print(f"\nRevenue:")
    print(f"  Completed payments: {total_payments}")
    print(f"  Total revenue: ${total_revenue:.2f}")
    
    # Net Profit
    net_profit = total_revenue - total_spending
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    print(f"\nProfit Analysis:")
    print(f"  Net profit: ${net_profit:.6f}")
    print(f"  Profit margin: {profit_margin:.2f}%")
    
    # Payment methods breakdown
    cursor.execute("""
        SELECT payment_method, COUNT(*), SUM(amount) 
        FROM transactions 
        WHERE status = 'completed' 
        GROUP BY payment_method
    """)
    
    print(f"\nRevenue by payment method:")
    for row in cursor.fetchall():
        method, count, amount = row
        print(f"  {method}: {count} payments, ${amount:.2f}")
    
    conn.close()

if __name__ == "__main__":
    migrate_message_costs()
    show_financial_summary()