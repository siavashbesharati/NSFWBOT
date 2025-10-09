import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
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
        
        # Admin settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            ("payment_ton_enabled", "true")
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
                           user_message: str, bot_response: str):
        """Add message to history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        """Get detailed payment statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total revenue by payment method
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
        for row in payment_methods_rows:
            payment_methods.append({
                'payment_method': row['payment_method'],
                'transaction_count': row['transaction_count'],
                'total_amount': row['total_amount'],
                'avg_amount': row['avg_amount']
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
        
        conn.close()
        
        return {
            'payment_methods': payment_methods,
            'recent_payments': recent_payments,
            'total_transactions': totals[0] if totals else 0,
            'total_revenue': totals[1] if totals else 0.0,
            'paying_users': totals[2] if totals else 0
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

    def save_message_history(self, user_id, message_type, user_message, bot_response, ai_model=None, tokens_used=0, cost=0.0, context_length=0):
        """Save message and response to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO message_history 
            (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length))
        
        conn.commit()
        conn.close()

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