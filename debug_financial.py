#!/usr/bin/env python3
"""
Debug script to check financial analytics calculations
"""

from database import Database
from financial_analytics import FinancialAnalytics

def debug_financial_data():
    """Debug financial analytics calculations"""
    
    print("🔍 Debugging Financial Analytics")
    print("=" * 50)
    
    # Initialize
    db = Database()
    analytics = FinancialAnalytics(db)
    
    # Test basic data retrieval
    print("1. Testing AI Spending Calculation:")
    spending_data = analytics.get_total_ai_spending()
    print(f"   Total messages with cost: {spending_data['total_messages']}")
    print(f"   Total AI spending: ${spending_data['total_cost_usd']}")
    print(f"   Average cost per message: ${spending_data['avg_cost_per_message']}")
    print(f"   Spending by type: {spending_data['spending_by_type']}")
    
    print("\n2. Testing Revenue Calculation:")
    revenue_data = analytics.get_total_revenue()
    print(f"   Total payments: {revenue_data['total_payments']}")
    print(f"   Total revenue USD: ${revenue_data['total_revenue_usd']}")
    print(f"   Average payment USD: ${revenue_data['avg_payment_usd']}")
    print(f"   Revenue by method: {revenue_data['revenue_by_method']}")
    
    print("\n3. Testing Net Profit Analysis:")
    profit_data = analytics.get_net_profit_analysis()
    print(f"   Financial summary: {profit_data['financial_summary']}")
    
    print("\n4. Testing KPIs:")
    kpis = analytics.get_financial_kpis()
    print(f"   Overall KPIs: {kpis.get('overall', {})}")
    print(f"   This month KPIs: {kpis.get('this_month', {})}")
    print(f"   Growth metrics: {kpis.get('growth_metrics', {})}")
    
    # Check raw database data
    print("\n5. Raw Database Check:")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check message_history
    cursor.execute("SELECT COUNT(*), SUM(cost) FROM message_history WHERE cost > 0")
    msg_data = cursor.fetchone()
    print(f"   Messages with cost: {msg_data[0]}, Total cost: ${msg_data[1] or 0}")
    
    # Check transactions
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE status = 'completed'")
    txn_data = cursor.fetchone()
    print(f"   Completed transactions: {txn_data[0]}, Total amount: ${txn_data[1] or 0}")
    
    # Check exchange rates
    cursor.execute("SELECT key, value FROM admin_settings WHERE key IN ('ton_price_usd', 'stars_price_usd')")
    rates = cursor.fetchall()
    print(f"   Exchange rates: {dict(rates)}")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    debug_financial_data()