import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

def format_precise_number(value):
    """Format numbers with full precision, only removing trailing zeros"""
    if value is None or value == 0:
        return "0"
    
    try:
        num = float(value)
        # Use reasonable precision formatting (8 decimal places for financial data)
        formatted = f"{num:.8f}"
        
        # Remove trailing zeros and decimal point if needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    except (ValueError, TypeError):
        return str(value)

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use environment variable or default
            db_path = os.getenv('DATABASE_PATH', 'bot_database.db')
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                free_messages_used INTEGER DEFAULT 0,
                free_text_messages_used INTEGER DEFAULT 0,
                free_image_messages_used INTEGER DEFAULT 0,
                free_video_messages_used INTEGER DEFAULT 0,
                text_messages_left INTEGER DEFAULT 0,
                image_messages_left INTEGER DEFAULT 0,
                video_messages_left INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0.0
            )
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN free_text_messages_used INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN free_image_messages_used INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN free_video_messages_used INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Packages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                text_count INTEGER DEFAULT 0,
                image_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                price_stars INTEGER DEFAULT 0,
                price_ton REAL DEFAULT 0.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_id INTEGER,
                payment_method TEXT, -- 'stars' or 'ton'
                amount REAL,
                status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'failed'
                transaction_hash TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (package_id) REFERENCES packages (id)
            )
        ''')
        
        # Message history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_type TEXT, -- 'text', 'image', 'video'
                user_message TEXT,
                bot_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Add new columns for conversation context if they don't exist
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN ai_model TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN tokens_used INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN cost REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN context_length INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Venice API response metadata columns
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN completion_tokens INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN prompt_tokens INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN total_tokens INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN response_id TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN finish_reason TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN response_created INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN venice_parameters TEXT')  # JSON string
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN full_response_json TEXT')  # Complete response for audit
        except sqlite3.OperationalError:
            pass
        
        # Admin settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referee_id INTEGER NOT NULL,
                referral_code TEXT,
                status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'expired'
                text_reward INTEGER DEFAULT 0,
                image_reward INTEGER DEFAULT 0,
                video_reward INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_date TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referee_id) REFERENCES users (user_id),
                UNIQUE(referee_id) -- Each user can only be referred once
            )
        ''')
        
        # User referral codes table (for tracking unique referral codes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_referral_codes (
                user_id INTEGER PRIMARY KEY,
                referral_code TEXT UNIQUE NOT NULL,
                total_referrals INTEGER DEFAULT 0,
                successful_referrals INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Bot statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                revenue_stars INTEGER DEFAULT 0,
                revenue_ton REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default packages
        self.insert_default_packages()
        self.insert_default_settings()
    
    def insert_default_packages(self):
        """Insert default packages if none exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM packages")
        if cursor.fetchone()[0] == 0:
            default_packages = [
                ("Starter Pack", "Perfect for beginners", 10, 2, 1, 50, 0.5),
                ("Standard Pack", "Most popular choice", 25, 5, 3, 100, 1.0),
                ("Premium Pack", "For heavy users", 50, 15, 10, 200, 2.0),
                ("Ultimate Pack", "Unlimited experience", 100, 30, 20, 350, 3.5)
            ]
            
            cursor.executemany('''
                INSERT INTO packages (name, description, text_count, image_count, 
                                    video_count, price_stars, price_ton)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', default_packages)
        
        conn.commit()
        conn.close()
    
    def insert_default_settings(self):
        """Insert default admin settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        default_settings = [
            ("bot_running", "true"),
            ("simulation_mode", "false"),
            ("free_messages", "1"),
            ("openrouter_model", "openai/gpt-3.5-turbo"),
            ("payment_stars_enabled", "true"),
            ("payment_ton_enabled", "true"),
            # Token pricing settings (Venice AI default pricing)
            ("input_token_price_per_1m", "0.50"),    # $0.50 per 1M input tokens
            ("output_token_price_per_1m", "1.50"),   # $1.50 per 1M output tokens
            # Referral system settings
            ("referral_system_enabled", "true"),
            ("referral_text_reward", "3"),
            ("referral_image_reward", "1"),
            ("referral_video_reward", "1")
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO admin_settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    # User management methods
    def create_user(self, user_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None):
        """Create a new user or update existing user info"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_activity = ? WHERE user_id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def use_message_credit(self, user_id: int, message_type: str) -> bool:
        """Use a message credit and return True if successful"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        user = self.get_user(user_id)
        if not user:
            conn.close()
            return False
        
        # Get free message settings from database
        free_settings = self.get_free_message_settings()
        
        # Check if user has free messages left for this specific type
        free_field = f"free_{message_type}_messages_used"
        free_limit_key = f"free_{message_type}_messages"
        free_limit = free_settings.get(free_limit_key, 0)
        
        current_free_used = user.get(free_field, 0)
        
        if current_free_used < free_limit:
            # Use free message
            cursor.execute(f'''
                UPDATE users SET {free_field} = {free_field} + 1
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
            return True
        
        # Check paid message credits
        credit_field = f"{message_type}_messages_left"
        if user.get(credit_field, 0) > 0:
            cursor.execute(f'''
                UPDATE users SET {credit_field} = {credit_field} - 1
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def add_message_credits(self, user_id: int, text_count: int = 0, 
                           image_count: int = 0, video_count: int = 0):
        """Add message credits to user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET 
                text_messages_left = text_messages_left + ?,
                image_messages_left = image_messages_left + ?,
                video_messages_left = video_messages_left + ?
            WHERE user_id = ?
        ''', (text_count, image_count, video_count, user_id))
        
        conn.commit()
        conn.close()
    
    # Package management methods
    def get_packages(self, active_only: bool = True) -> List[Dict]:
        """Get all packages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM packages"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY price_stars ASC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'description', 'text_count', 'image_count', 
                  'video_count', 'price_stars', 'price_ton', 'is_active', 'created_date']
        return [dict(zip(columns, row)) for row in rows]
    
    def get_package(self, package_id: int) -> Optional[Dict]:
        """Get a specific package"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM packages WHERE id = ?", (package_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'name', 'description', 'text_count', 'image_count', 
                      'video_count', 'price_stars', 'price_ton', 'is_active', 'created_date']
            return dict(zip(columns, row))
        return None
    
    def create_package(self, name: str, description: str, text_count: int,
                      image_count: int, video_count: int, price_stars: int, price_ton: float):
        """Create a new package"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO packages (name, description, text_count, image_count,
                                video_count, price_stars, price_ton)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, text_count, image_count, video_count, price_stars, price_ton))
        
        package_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return package_id
    
    # Transaction management methods
    def create_transaction(self, user_id: int, package_id: int, 
                          payment_method: str, amount: float) -> int:
        """Create a new transaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, package_id, payment_method, amount)
            VALUES (?, ?, ?, ?)
        ''', (user_id, package_id, payment_method, amount))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return transaction_id
    
    def complete_transaction(self, transaction_id: int, transaction_hash: str = None):
        """Mark transaction as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transactions SET 
                status = 'completed',
                completed_date = ?,
                transaction_hash = ?
            WHERE id = ?
        ''', (datetime.now(), transaction_hash, transaction_id))
        
        conn.commit()
        conn.close()
    
    # Message history methods
    def add_message_history(self, user_id: int, message_type: str, 
                           user_message: str, bot_response: str, venice_metadata: dict = None):
        """Add message to history with Venice API metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if venice_metadata:
            # Extract Venice API metadata
            usage = venice_metadata.get('usage', {})
            choice = venice_metadata.get('choices', [{}])[0] if venice_metadata.get('choices') else {}
            venice_params = venice_metadata.get('venice_parameters', {})
            
            cursor.execute('''
                INSERT INTO message_history (
                    user_id, message_type, user_message, bot_response,
                    ai_model, completion_tokens, prompt_tokens, total_tokens,
                    response_id, finish_reason, response_created,
                    venice_parameters, full_response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, message_type, user_message, bot_response,
                venice_metadata.get('model'),
                usage.get('completion_tokens', 0),
                usage.get('prompt_tokens', 0), 
                usage.get('total_tokens', 0),
                venice_metadata.get('id'),
                choice.get('finish_reason'),
                venice_metadata.get('created', 0),
                json.dumps(venice_params),
                json.dumps(venice_metadata)
            ))
        else:
            # Fallback for non-Venice responses
            cursor.execute('''
                INSERT INTO message_history (user_id, message_type, user_message, bot_response)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message_type, user_message, bot_response))
        
        conn.commit()
        conn.close()
    
    # Settings management methods
    def get_setting(self, key: str, default: str = None) -> str:
        """Get admin setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set admin setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO admin_settings (key, value, updated_date)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now()))
        
        conn.commit()
        conn.close()
    
    # Alias for compatibility with admin dashboard
    def update_setting(self, key: str, value: str):
        """Alias for set_setting for compatibility"""
        return self.set_setting(key, value)
    
    # Statistics methods
    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_activity > datetime('now', '-7 days')
        ''')
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message_history")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE status = 'completed' AND payment_method = 'stars'
        ''')
        revenue_stars = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE status = 'completed' AND payment_method = 'ton'
        ''')
        revenue_ton = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_messages': total_messages,
            'revenue_stars': revenue_stars,
            'revenue_ton': revenue_ton
        }
    
    def get_all_users(self) -> List[Dict]:
        """Get all users for admin dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY registration_date DESC")
        rows = cursor.fetchall()
        conn.close()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_total_revenue(self):
        """Get total revenue from completed transactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(amount) as total FROM transactions 
            WHERE status = 'completed'
        ''')
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 0.0

    def get_payment_statistics(self):
        """Get detailed payment statistics with currency-aware totals"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total revenue by payment method (currency-aware)
        cursor.execute('''
            SELECT 
                payment_method,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM transactions 
            WHERE status = 'completed'
            GROUP BY payment_method
        ''')
        
        payment_methods_rows = cursor.fetchall()
        payment_methods = []
        total_ton = 0.0
        total_stars = 0.0
        
        for row in payment_methods_rows:
            payment_method = row['payment_method']
            total_amount = row['total_amount']
            
            # Track totals by currency
            if payment_method == 'ton':
                total_ton += total_amount
            elif payment_method == 'stars':
                total_stars += total_amount
                
            payment_methods.append({
                'payment_method': payment_method,
                'transaction_count': row['transaction_count'],
                'total_amount': total_amount,
                'avg_amount': row['avg_amount'],
                'currency_symbol': '💎 TON' if payment_method == 'ton' else '⭐ Stars'
            })
        
        # Recent payments
        cursor.execute('''
            SELECT t.*, u.username, p.name as package_name
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN packages p ON t.package_id = p.id
            WHERE t.status = 'completed'
            ORDER BY t.created_date DESC
            LIMIT 10
        ''')
        
        recent_payments_rows = cursor.fetchall()
        recent_payments = []
        for row in recent_payments_rows:
            recent_payments.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'] if 'username' in row.keys() else None,
                'package_name': row['package_name'] if 'package_name' in row.keys() else None,
                'amount': row['amount'],
                'payment_method': row['payment_method'],
                'created_date': row['created_date']
            })
        
        # Total counts
        cursor.execute('''
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_revenue,
                COUNT(DISTINCT user_id) as paying_users
            FROM transactions 
            WHERE status = 'completed'
        ''')
        
        totals = cursor.fetchone()
        
        # Recent payments with currency symbols
        for payment in recent_payments:
            payment_method = payment['payment_method']
            if payment_method == 'ton':
                payment['currency_symbol'] = '💎 TON'
                payment['display_amount'] = f"{payment['amount']} TON"
            elif payment_method == 'telegram_stars':
                payment['currency_symbol'] = '⭐ Stars'
                payment['display_amount'] = f"{payment['amount']} ⭐"
            else:
                payment['currency_symbol'] = '$'
                payment['display_amount'] = f"${payment['amount']}"
        
        # Total counts (no longer mixed currency)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(DISTINCT user_id) as paying_users
            FROM transactions 
            WHERE status = 'completed'
        ''')
        
        totals = cursor.fetchone()
        
        conn.close()
        
        return {
            'payment_methods': payment_methods,
            'recent_payments': recent_payments,
            'total_transactions': totals[0] if totals else 0,
            'total_ton': total_ton,
            'total_stars': total_stars,
            'total_revenue': total_ton + total_stars,  # Keep for backward compatibility
            'paying_users': totals[1] if totals else 0
        }

    def get_user_count(self):
        """Get total number of users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_users_paginated(self, page, per_page):
        """Get users with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, credits, 
                   total_spent, created_date, last_active 
            FROM users 
            ORDER BY created_date DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        users = cursor.fetchall()
        conn.close()
        return users

    def get_transaction_count(self):
        """Get total number of transactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "completed"')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_total_revenue(self):
        """Get total revenue from completed transactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(
                CASE 
                    WHEN payment_method = 'ton' THEN amount * 2.5 
                    WHEN payment_method = 'stars' THEN amount * 0.01 
                    ELSE 0 
                END
            ) as total_revenue 
            FROM transactions 
            WHERE status = "completed"
        ''')
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0

    def get_recent_users(self, limit=10):
        """Get recent users"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users 
            ORDER BY registration_date DESC 
            LIMIT ?
        ''', (limit,))
        
        users = cursor.fetchall()
        conn.close()
        return users

    def get_recent_transactions(self, limit=10):
        """Get recent transactions with user info"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, u.username 
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            ORDER BY t.created_date DESC 
            LIMIT ?
        ''', (limit,))
        
        transactions = cursor.fetchall()
        conn.close()
        return transactions

    def get_users_paginated(self, page, per_page):
        """Get users with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT * FROM users 
            ORDER BY registration_date DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        users = cursor.fetchall()
        conn.close()
        return users

    def get_transactions_paginated(self, page, per_page):
        """Get transactions with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT t.*, u.username, p.name as package_name 
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN packages p ON t.package_id = p.id
            ORDER BY t.created_date DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        transactions = cursor.fetchall()
        conn.close()
        return transactions

    def get_active_package_count(self):
        """Get number of active packages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM packages WHERE is_active = 1')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_package_by_id(self, package_id):
        """Get package by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM packages WHERE id = ?', (package_id,))
        package = cursor.fetchone()
        conn.close()
        return package

    def update_package(self, package_id, name, description, text_count, image_count, video_count, price_ton, price_stars, is_active=True):
        """Update an existing package"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE packages 
            SET name = ?, description = ?, text_count = ?, image_count = ?, 
                video_count = ?, price_ton = ?, price_stars = ?, is_active = ?
            WHERE id = ?
        ''', (name, description, text_count, image_count, video_count, price_ton, price_stars, is_active, package_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def delete_package(self, package_id):
        """Delete a package"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM packages WHERE id = ?', (package_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def get_user_transactions(self, user_id):
        """Get all transactions for a specific user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, p.name as package_name 
            FROM transactions t
            LEFT JOIN packages p ON t.package_id = p.id
            WHERE t.user_id = ? 
            ORDER BY t.created_date DESC
        ''', (user_id,))
        
        transactions = cursor.fetchall()
        conn.close()
        return transactions

    def get_user_usage_history(self, user_id, limit=50):
        """Get user's usage history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get actual message usage history from message_history table
        cursor.execute('''
            SELECT message_type, user_message, bot_response, timestamp as created_date,
                   NULL as ai_model, NULL as tokens_used, NULL as cost
            FROM message_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        usage = cursor.fetchall()
        conn.close()
        return usage

    def get_conversation_history(self, user_id, limit=10):
        """Get recent conversation history for AI context"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, bot_response, message_type, timestamp
            FROM message_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        # Return in chronological order (oldest first)
        return list(reversed(history))

    def calculate_message_cost(self, prompt_tokens, completion_tokens):
        """Calculate the USD cost of a message based on token usage and pricing settings"""
        try:
            # Get token pricing from database settings
            input_price_per_1m = float(self.get_setting('input_token_price_per_1m', '0.50'))
            output_price_per_1m = float(self.get_setting('output_token_price_per_1m', '1.50'))
            
            # Calculate costs (price is per 1 million tokens)
            input_cost = (prompt_tokens / 1_000_000) * input_price_per_1m
            output_cost = (completion_tokens / 1_000_000) * output_price_per_1m
            total_cost = input_cost + output_cost
            
            return {
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': total_cost,
                'input_tokens': prompt_tokens,
                'output_tokens': completion_tokens
            }
        except (ValueError, TypeError) as e:
            print(f"Error calculating message cost: {e}")
            return {
                'input_cost': 0.0,
                'output_cost': 0.0,
                'total_cost': 0.0,
                'input_tokens': prompt_tokens or 0,
                'output_tokens': completion_tokens or 0
            }

    def save_message_history(self, user_id, message_type, user_message, bot_response, ai_model=None, tokens_used=0, cost=0.0, context_length=0, venice_metadata=None):
        """Save message and response to history with optional Venice metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if venice_metadata:
            # Extract Venice API metadata
            usage = venice_metadata.get('usage', {})
            choice = venice_metadata.get('choices', [{}])[0] if venice_metadata.get('choices') else {}
            venice_params = venice_metadata.get('venice_parameters', {})
            
            # Extract token counts
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            # Calculate cost based on token usage
            cost_info = self.calculate_message_cost(prompt_tokens, completion_tokens)
            calculated_cost = cost_info['total_cost']
            
            print(f"💰 Message Cost Calculation:")
            print(f"   Input Tokens: {prompt_tokens:,} = ${format_precise_number(cost_info['input_cost'])}")
            print(f"   Output Tokens: {completion_tokens:,} = ${format_precise_number(cost_info['output_cost'])}")
            print(f"   Total Cost: ${format_precise_number(calculated_cost)}")
            
            cursor.execute('''
                INSERT INTO message_history 
                (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length,
                 completion_tokens, prompt_tokens, total_tokens, response_id, finish_reason, response_created,
                 venice_parameters, full_response_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id, message_type, user_message, bot_response, ai_model, tokens_used, calculated_cost, context_length,
                completion_tokens,
                prompt_tokens,
                total_tokens,
                venice_metadata.get('id'),
                choice.get('finish_reason'),
                venice_metadata.get('created', 0),
                json.dumps(venice_params),
                json.dumps(venice_metadata)
            ))
        else:
            # Fallback for non-Venice responses
            cursor.execute('''
                INSERT INTO message_history 
                (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length))
        
        conn.commit()
        conn.close()

    def clear_conversation_history(self, user_id):
        """Clear conversation history for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM message_history 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()
        
        return rows_deleted

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def get_all_settings(self):
        """Get all admin settings as a dictionary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM admin_settings')
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for row in rows:
            settings[row[0]] = row[1]
        
        return settings

    def get_all_packages(self):
        """Get all packages (alias for get_packages with active_only=False)"""
        return self.get_packages(active_only=False)
    
    def update_setting(self, key: str, value: str):
        """Update an admin setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO admin_settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def update_free_message_settings(self, free_text=None, free_image=None, free_video=None):
        """Update free message settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        settings = []
        if free_text is not None:
            settings.append(('free_text_messages', str(free_text)))
        if free_image is not None:
            settings.append(('free_image_messages', str(free_image)))
        if free_video is not None:
            settings.append(('free_video_messages', str(free_video)))
        
        for key, value in settings:
            cursor.execute('''
                INSERT OR REPLACE INTO admin_settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_free_message_settings(self):
        """Get free message settings from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value FROM admin_settings 
            WHERE key IN ('free_text_messages', 'free_image_messages', 'free_video_messages')
        ''')
        
        settings = {}
        for row in cursor.fetchall():
            key, value = row
            try:
                settings[key] = int(value)
            except (ValueError, TypeError):
                # Default values if conversion fails
                if key == 'free_text_messages':
                    settings[key] = 5
                elif key == 'free_image_messages':
                    settings[key] = 2
                elif key == 'free_video_messages':
                    settings[key] = 1
        
        # Set defaults if not found in database
        if 'free_text_messages' not in settings:
            settings['free_text_messages'] = 5
        if 'free_image_messages' not in settings:
            settings['free_image_messages'] = 2
        if 'free_video_messages' not in settings:
            settings['free_video_messages'] = 1
        
        conn.close()
        return settings

    def execute_query(self, query: str, params: tuple = None):
        """Execute a raw SQL query and return results"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            conn.close()
            logging.error(f"Database query error: {e}")
            return []
    
    def get_total_users(self):
        """Alias for get_user_count for compatibility"""
        return self.get_user_count()
    
    def get_total_transactions(self):
        """Alias for get_transaction_count for compatibility"""
        return self.get_transaction_count()
    
    # Referral System Methods
    
    def generate_referral_code(self, user_id: int) -> str:
        """Generate a unique referral code for a user"""
        import random
        import string
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if user already has a referral code
        cursor.execute('SELECT referral_code FROM user_referral_codes WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        # Generate a unique code
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            cursor.execute('SELECT user_id FROM user_referral_codes WHERE referral_code = ?', (code,))
            if not cursor.fetchone():
                break
        
        # Insert the new code
        cursor.execute('''
            INSERT INTO user_referral_codes (user_id, referral_code)
            VALUES (?, ?)
        ''', (user_id, code))
        
        conn.commit()
        conn.close()
        return code
    
    def get_user_referral_code(self, user_id: int) -> Optional[str]:
        """Get user's referral code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT referral_code FROM user_referral_codes WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def process_referral(self, referee_id: int, referral_code: str) -> bool:
        """Process a referral when a new user joins with a referral code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Find the referrer by code
            cursor.execute('SELECT user_id FROM user_referral_codes WHERE referral_code = ?', (referral_code,))
            referrer_result = cursor.fetchone()
            
            if not referrer_result:
                conn.close()
                return False
            
            referrer_id = referrer_result[0]
            
            # Check if this user was already referred
            cursor.execute('SELECT id FROM referrals WHERE referee_id = ?', (referee_id,))
            if cursor.fetchone():
                conn.close()
                return False  # Already referred
            
            # Get referral rewards from settings
            settings = self.get_all_settings()
            text_reward = int(settings.get('referral_text_reward', 3))
            image_reward = int(settings.get('referral_image_reward', 1))
            video_reward = int(settings.get('referral_video_reward', 1))
            
            # Create referral record
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referee_id, referral_code, status, 
                                     text_reward, image_reward, video_reward, completed_date)
                VALUES (?, ?, ?, 'completed', ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (referrer_id, referee_id, referral_code, text_reward, image_reward, video_reward))
            
            # Add credits to both users
            # Referrer gets the rewards
            cursor.execute('''
                UPDATE users 
                SET text_messages_left = text_messages_left + ?,
                    image_messages_left = image_messages_left + ?,
                    video_messages_left = video_messages_left + ?
                WHERE user_id = ?
            ''', (text_reward, image_reward, video_reward, referrer_id))
            
            # Referee gets the rewards too
            cursor.execute('''
                UPDATE users 
                SET text_messages_left = text_messages_left + ?,
                    image_messages_left = image_messages_left + ?,
                    video_messages_left = video_messages_left + ?
                WHERE user_id = ?
            ''', (text_reward, image_reward, video_reward, referee_id))
            
            # Update referrer's statistics
            cursor.execute('''
                UPDATE user_referral_codes 
                SET total_referrals = total_referrals + 1,
                    successful_referrals = successful_referrals + 1
                WHERE user_id = ?
            ''', (referrer_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            conn.rollback()
            conn.close()
            logging.error(f"Error processing referral: {e}")
            return False
    
    def get_user_referrals(self, user_id: int) -> Dict:
        """Get referral statistics for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get referral code info
        cursor.execute('''
            SELECT referral_code, total_referrals, successful_referrals 
            FROM user_referral_codes WHERE user_id = ?
        ''', (user_id,))
        code_info = cursor.fetchone()
        
        # Get successful referrals
        cursor.execute('''
            SELECT r.*, u.username, u.first_name 
            FROM referrals r
            LEFT JOIN users u ON r.referee_id = u.user_id
            WHERE r.referrer_id = ? AND r.status = 'completed'
            ORDER BY r.completed_date DESC
        ''', (user_id,))
        referrals = cursor.fetchall()
        
        conn.close()
        
        result = {
            'referral_code': code_info[0] if code_info else None,
            'total_referrals': code_info[1] if code_info else 0,
            'successful_referrals': code_info[2] if code_info else 0,
            'referrals': [dict(zip([col[0] for col in cursor.description], row)) for row in referrals] if referrals else []
        }
        
        return result
    
    def validate_referral_code(self, referral_code: str) -> bool:
        """Check if a referral code is valid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM user_referral_codes WHERE referral_code = ?', (referral_code,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None