import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from database import Database

class FinancialAnalytics:
    """
    Financial Analytics Service for calculating:
    - Total AI spending (from message costs)
    - Total revenue (from payments)
    - Net profit (revenue - spending)
    - Financial trends and analytics
    """
    
    def __init__(self, database: Database):
        self.db = database
    
    def get_total_ai_spending(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate total AI spending from all message costs
        
        Args:
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            
        Returns:
            Dict with total spending, token counts, and breakdown
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build date filter
            date_filter = ""
            params = []
            if start_date and end_date:
                date_filter = "WHERE DATE(timestamp) BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif start_date:
                date_filter = "WHERE DATE(timestamp) >= ?"
                params = [start_date]
            elif end_date:
                date_filter = "WHERE DATE(timestamp) <= ?"
                params = [end_date]
            
            # Get total spending and token usage
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(cost) as total_cost_usd,
                    SUM(prompt_tokens) as total_input_tokens,
                    SUM(completion_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens_sum,
                    AVG(cost) as avg_cost_per_message
                FROM message_history 
                {date_filter}
                AND cost > 0
            ''', params)
            
            result = cursor.fetchone()
            
            # Get spending by message type
            cursor.execute(f'''
                SELECT 
                    message_type,
                    COUNT(*) as message_count,
                    SUM(cost) as type_cost,
                    SUM(total_tokens) as type_tokens
                FROM message_history 
                {date_filter}
                AND cost > 0
                GROUP BY message_type
            ''', params)
            
            spending_by_type = {}
            for row in cursor.fetchall():
                spending_by_type[row[0]] = {
                    'message_count': row[1],
                    'total_cost': float(row[2]) if row[2] else 0.0,
                    'total_tokens': row[3] if row[3] else 0
                }
            
            # Get daily spending for trends
            cursor.execute(f'''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as daily_messages,
                    SUM(cost) as daily_cost,
                    SUM(total_tokens) as daily_tokens
                FROM message_history 
                {date_filter}
                AND cost > 0
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 30
            ''', params)
            
            daily_trends = []
            for row in cursor.fetchall():
                daily_trends.append({
                    'date': row[0],
                    'messages': row[1],
                    'cost': float(row[2]) if row[2] else 0.0,
                    'tokens': row[3] if row[3] else 0
                })
            
            conn.close()
            
            return {
                'total_messages': result[0] if result[0] else 0,
                'total_cost_usd': float(result[1]) if result[1] else 0.0,
                'total_input_tokens': result[2] if result[2] else 0,
                'total_output_tokens': result[3] if result[3] else 0,
                'total_tokens': result[4] if result[4] else 0,
                'avg_cost_per_message': float(result[5]) if result[5] else 0.0,
                'spending_by_type': spending_by_type,
                'daily_trends': daily_trends
            }
            
        except Exception as e:
            print(f"Error calculating AI spending: {e}")
            return {
                'total_messages': 0,
                'total_cost_usd': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_tokens': 0,
                'avg_cost_per_message': 0.0,
                'spending_by_type': {},
                'daily_trends': []
            }
    
    def get_total_revenue(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate total revenue from all payments (TON + Stars) converted to USD
        
        Args:
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            
        Returns:
            Dict with total revenue, payment breakdowns, and trends
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build date filter
            date_filter = ""
            params = []
            if start_date and end_date:
                date_filter = "WHERE DATE(created_date) BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif start_date:
                date_filter = "WHERE DATE(created_date) >= ?"
                params = [start_date]
            elif end_date:
                date_filter = "WHERE DATE(created_date) <= ?"
                params = [end_date]
            
            # Get currency exchange rates from settings
            cursor.execute("SELECT key, value FROM admin_settings WHERE key IN ('ton_price_usd', 'stars_price_usd')")
            exchange_rates = {}
            for row in cursor.fetchall():
                exchange_rates[row[0]] = float(row[1])
            
            ton_rate = exchange_rates.get('ton_price_usd', 5.50)
            stars_rate = exchange_rates.get('stars_price_usd', 0.013)
            
            # Get total revenue converted to USD using exchange rates
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_payments,
                    SUM(CASE 
                        WHEN payment_method = 'ton' THEN amount * {ton_rate}
                        WHEN payment_method = 'stars' THEN amount * {stars_rate}
                        ELSE amount 
                    END) as total_revenue_usd,
                    AVG(CASE 
                        WHEN payment_method = 'ton' THEN amount * {ton_rate}
                        WHEN payment_method = 'stars' THEN amount * {stars_rate}
                        ELSE amount 
                    END) as avg_payment_usd
                FROM transactions 
                {date_filter}
                AND status = 'completed'
            ''', params)
            
            result = cursor.fetchone()
            
            # Get revenue by payment method with USD conversion
            cursor.execute(f'''
                SELECT 
                    payment_method,
                    COUNT(*) as payment_count,
                    SUM(amount) as original_amount,
                    SUM(CASE 
                        WHEN payment_method = 'ton' THEN amount * {ton_rate}
                        WHEN payment_method = 'stars' THEN amount * {stars_rate}
                        ELSE amount 
                    END) as method_revenue_usd
                FROM transactions 
                {date_filter}
                AND status = 'completed'
                GROUP BY payment_method
            ''', params)
            
            revenue_by_method = {}
            for row in cursor.fetchall():
                method = row[0]
                original_amount = float(row[2]) if row[2] else 0.0
                usd_amount = float(row[3]) if row[3] else 0.0
                
                revenue_by_method[method] = {
                    'payment_count': row[1],
                    'original_amount': original_amount,
                    'total_revenue_usd': usd_amount,
                    'exchange_rate': ton_rate if method == 'ton' else (stars_rate if method == 'stars' else 1.0),
                    'currency': 'TON' if method == 'ton' else ('Stars' if method == 'stars' else 'USD')
                }
            
            # Get daily revenue trends with USD conversion
            cursor.execute(f'''
                SELECT 
                    DATE(created_date) as date,
                    COUNT(*) as daily_payments,
                    SUM(CASE 
                        WHEN payment_method = 'ton' THEN amount * {ton_rate}
                        WHEN payment_method = 'stars' THEN amount * {stars_rate}
                        ELSE amount 
                    END) as daily_revenue_usd
                FROM transactions 
                {date_filter}
                AND status = 'completed'
                GROUP BY DATE(created_date)
                ORDER BY date DESC
                LIMIT 30
            ''', params)
            
            daily_trends = []
            for row in cursor.fetchall():
                daily_trends.append({
                    'date': row[0],
                    'payments': row[1],
                    'revenue': float(row[2]) if row[2] else 0.0
                })
            
            conn.close()
            
            return {
                'total_payments': result[0] if result[0] else 0,
                'total_revenue_usd': float(result[1]) if result[1] else 0.0,
                'avg_payment_usd': float(result[2]) if result[2] else 0.0,
                'revenue_by_method': revenue_by_method,
                'daily_trends': daily_trends
            }
            
        except Exception as e:
            print(f"Error calculating revenue: {e}")
            return {
                'total_payments': 0,
                'total_revenue_usd': 0.0,
                'avg_payment_usd': 0.0,
                'revenue_by_method': {},
                'daily_trends': []
            }
    
    def get_net_profit_analysis(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive profit analysis (Revenue - Spending = Net Profit)
        
        Args:
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            
        Returns:
            Dict with complete financial analysis
        """
        try:
            # Get spending and revenue data
            spending_data = self.get_total_ai_spending(start_date, end_date)
            revenue_data = self.get_total_revenue(start_date, end_date)
            
            # Calculate profit metrics
            total_revenue = revenue_data['total_revenue_usd']
            total_spending = spending_data['total_cost_usd']
            net_profit = total_revenue - total_spending
            
            # Calculate profit margin (avoid division by zero)
            profit_margin_percent = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Calculate ROI (Return on Investment)
            roi_percent = (net_profit / total_spending * 100) if total_spending > 0 else 0
            
            # Combine daily trends for profit analysis
            daily_profit_trends = []
            revenue_by_date = {item['date']: item['revenue'] for item in revenue_data['daily_trends']}
            spending_by_date = {item['date']: item['cost'] for item in spending_data['daily_trends']}
            
            # Get all unique dates
            all_dates = set(revenue_by_date.keys()) | set(spending_by_date.keys())
            
            for date in sorted(all_dates, reverse=True):
                daily_revenue = revenue_by_date.get(date, 0.0)
                daily_spending = spending_by_date.get(date, 0.0)
                daily_profit = daily_revenue - daily_spending
                
                daily_profit_trends.append({
                    'date': date,
                    'revenue': daily_revenue,
                    'spending': daily_spending,
                    'profit': daily_profit,
                    'margin': (daily_profit / daily_revenue * 100) if daily_revenue > 0 else 0
                })
            
            return {
                'financial_summary': {
                    'total_revenue_usd': total_revenue,
                    'total_spending_usd': total_spending,
                    'net_profit_usd': net_profit,
                    'profit_margin_percent': profit_margin_percent,
                    'roi_percent': roi_percent,
                    'is_profitable': net_profit > 0
                },
                'revenue_data': revenue_data,
                'spending_data': spending_data,
                'daily_profit_trends': daily_profit_trends[:30],  # Last 30 days
                'analysis_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'period_type': 'custom' if start_date or end_date else 'all_time'
                }
            }
            
        except Exception as e:
            print(f"Error calculating profit analysis: {e}")
            return {
                'financial_summary': {
                    'total_revenue_usd': 0.0,
                    'total_spending_usd': 0.0,
                    'net_profit_usd': 0.0,
                    'profit_margin_percent': 0.0,
                    'roi_percent': 0.0,
                    'is_profitable': False
                },
                'revenue_data': {},
                'spending_data': {},
                'daily_profit_trends': [],
                'analysis_period': {}
            }
    
    def get_financial_kpis(self) -> Dict[str, Any]:
        """
        Get key financial performance indicators for dashboard
        
        Returns:
            Dict with essential KPIs
        """
        try:
            # Get overall analysis
            overall = self.get_net_profit_analysis()
            
            # Get this month's data
            today = datetime.now()
            month_start = today.replace(day=1).strftime('%Y-%m-%d')
            month_data = self.get_net_profit_analysis(month_start)
            
            # Get last month for comparison
            if today.month == 1:
                last_month_start = today.replace(year=today.year-1, month=12, day=1)
            else:
                last_month_start = today.replace(month=today.month-1, day=1)
            
            if today.month == 1:
                last_month_end = today.replace(year=today.year-1, month=12, day=31)
            else:
                # Last day of previous month
                last_month_end = today.replace(day=1) - timedelta(days=1)
            
            last_month_data = self.get_net_profit_analysis(
                last_month_start.strftime('%Y-%m-%d'),
                last_month_end.strftime('%Y-%m-%d')
            )
            
            # Calculate growth rates
            revenue_growth = 0
            profit_growth = 0
            
            if last_month_data['financial_summary']['total_revenue_usd'] > 0:
                revenue_growth = ((month_data['financial_summary']['total_revenue_usd'] - 
                                 last_month_data['financial_summary']['total_revenue_usd']) /
                                last_month_data['financial_summary']['total_revenue_usd'] * 100)
            
            if last_month_data['financial_summary']['net_profit_usd'] != 0:
                profit_growth = ((month_data['financial_summary']['net_profit_usd'] - 
                                last_month_data['financial_summary']['net_profit_usd']) /
                               abs(last_month_data['financial_summary']['net_profit_usd']) * 100)
            
            return {
                'overall': overall['financial_summary'],
                'this_month': month_data['financial_summary'],
                'last_month': last_month_data['financial_summary'],
                'growth_metrics': {
                    'revenue_growth_percent': revenue_growth,
                    'profit_growth_percent': profit_growth,
                    'spending_trend': 'increasing' if month_data['financial_summary']['total_spending_usd'] > last_month_data['financial_summary']['total_spending_usd'] else 'decreasing'
                }
            }
            
        except Exception as e:
            print(f"Error calculating financial KPIs: {e}")
            return {
                'overall': {},
                'this_month': {},
                'last_month': {},
                'growth_metrics': {}
            }