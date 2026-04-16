import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path


def _default_db_path() -> str:
    """Determine default database path relative to the application location."""
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).resolve().parent / 'bot_database.db')
    return str(Path(__file__).resolve().parent / 'bot_database.db')

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
            # Use environment variable or default relative to application
            env_path = os.getenv('DATABASE_PATH')
            db_path = env_path if env_path else _default_db_path()
        else:
            db_path = str(Path(db_path).expanduser().resolve())
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.connection_pool = []
        self.pool_size = 5  # Keep 5 connections ready
        self.init_database()
    
    def get_connection(self):
        """Get database connection with optimized settings for production"""
        import threading
        
        # Simple connection pooling for better performance
        if self.connection_pool and len(self.connection_pool) > 0:
            try:
                conn = self.connection_pool.pop()
                # Test if connection is still valid
                conn.execute('SELECT 1')
                return conn
            except:
                # Connection is dead, create new one
                pass
        
        # Create new connection with optimized settings
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        
        # Enable WAL mode for better concurrency and reliability
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')  # Good balance of speed vs safety
        conn.execute('PRAGMA cache_size=-64000')   # 64MB cache
        conn.execute('PRAGMA temp_store=MEMORY')    # Store temp tables in memory
        conn.execute('PRAGMA mmap_size=268435456')  # 256MB memory map
        
        # Enable foreign keys
        conn.execute('PRAGMA foreign_keys=ON')
        
        return conn
    
    def return_connection(self, conn):
        """Return connection to pool if pool not full"""
        if len(self.connection_pool) < self.pool_size:
            try:
                # Test connection before returning to pool
                conn.execute('SELECT 1')
                self.connection_pool.append(conn)
            except:
                # Connection is bad, don't return to pool
                conn.close()
        else:
            conn.close()
    
    def health_check(self):
        """Check database health and connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM message_history')
                message_count = cursor.fetchone()[0]
                return {
                    'status': 'healthy',
                    'user_count': user_count,
                    'message_count': message_count,
                    'pool_size': len(self.connection_pool)
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_db_connection(self):
        """Context manager for database connections with automatic pooling"""
        from contextlib import contextmanager
        
        @contextmanager
        def connection_manager():
            conn = self.get_connection()
            try:
                yield conn
            finally:
                self.return_connection(conn)
        
        return connection_manager()
    
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
        
        # Add language preference column
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "en"')
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

        # Track conversation memory per selected character
        try:
            cursor.execute('ALTER TABLE message_history ADD COLUMN character_id INTEGER')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_history_user_character_time ON message_history(user_id, character_id, timestamp DESC)')
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
        
        # User activity logs table (for tracking user interactions)
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS user_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL, -- 'command', 'menu', 'button', 'callback', etc.
                activity_data TEXT NOT NULL, -- JSON data about the activity
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster activity log queries
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id_timestamp ON user_activity_logs(user_id, timestamp DESC)')
        except sqlite3.OperationalError:
            pass
        
        # Characters table (AI personality/role)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                instruction TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add character_id column to users table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN character_id INTEGER REFERENCES characters(id)')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()        # Insert default packages
        self.insert_default_packages()
        self.insert_default_settings()
        self.insert_default_characters()
    
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
            ("bot_token", ""),
            ("admin_chat_id", "0"),
            ("admin_username", "admin"),
            ("admin_password", "admin123"),
            ("secret_key", "change-this-secret-key-in-production"),
            ("bot_running", "true"),
            ("bot_active", "false"),
            ("simulation_mode", "true"),
            ("log_level", "INFO"),
            ("ai_api_key", ""),
            ("ai_model", "venice-uncensored"),
            ("ai_base_url", "https://api.venice.ai/api/v1"),
            ("venice_inference_key", ""),
            ("telegram_stars_enabled", "true"),
            ("ton_enabled", "true"),
            ("ton_api_key", ""),
            ("ton_mainnet_wallet_address", ""),
            ("ton_testnet_wallet_address", ""),
            ("ton_network_mode", "sandbox"),
            ("webhook_url", ""),
            ("dashboard_host", "127.0.0.1"),
            ("dashboard_port", "5000"),
            ("free_messages", "1"),
            ("free_text_messages", "5"),
            ("free_image_messages", "2"),
            ("free_video_messages", "1"),
            ("referral_system_enabled", "true"),
            ("referral_text_reward", "3"),
            ("referral_image_reward", "1"),
            ("referral_video_reward", "1"),
            ("max_requests_per_minute", "20"),
            ("max_requests_per_hour", "100"),
            ("max_image_size", "10"),
            ("max_video_size", "50"),
            ("ai_response_timeout", "30"),
            ("conversation_history_length", "10"),
            ("context_window_hours", "24"),
            ("enable_conversation_memory", "true"),
            ("activity_logging_enabled", "true"),
            ("input_token_price_per_1m", "0.50"),
            ("output_token_price_per_1m", "1.50"),
            ("ton_price_usd", "5.50"),
            ("stars_price_usd", "0.013"),
            ("payment_stars_enabled", "true"),
            ("payment_ton_enabled", "true"),
            ("ton_testnet_mode", "true"),
            ("support_telegram_username", "")
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO admin_settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def insert_default_characters(self):
        """Insert default characters if none exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM characters")
        if cursor.fetchone()[0] == 0:
            default_characters = [
                (
                    "Friendly Assistant",
                    "A helpful and friendly AI companion",
                    "You are a friendly, helpful, and respectful AI assistant. You provide clear, informative responses while maintaining a warm and approachable tone."
                ),
                (
                    "Professional Expert",
                    "A knowledgeable professional consultant",
                    "You are a professional expert with deep knowledge across various domains. You provide detailed, well-researched answers with a formal and authoritative tone."
                ),
                (
                    "Creative Writer",
                    "An imaginative storyteller and creative mind",
                    "You are a creative writer with a vivid imagination. You craft engaging stories, provide creative solutions, and think outside the box while maintaining artistic flair."
                ),
                (
                    "Casual Friend",
                    "A laid-back conversational companion",
                    "You are a casual, friendly companion who chats in a relaxed, conversational style. You use everyday language and emojis occasionally to keep things fun and engaging."
                ),
            ]
            
            cursor.executemany('''
                INSERT INTO characters (name, description, instruction)
                VALUES (?, ?, ?)
            ''', default_characters)
        
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
    
    def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET language = ? WHERE user_id = ?
        ''', (language, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        user = self.get_user(user_id)
        if user and 'language' in user and user['language']:
            return user['language']
        return 'en'  # Default to English
    
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
        """Get users with pagination metadata."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        if total_users == 0:
            conn.close()
            return {
                'items': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_index': 0,
                'end_index': 0
            }

        total_pages = (total_users + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        offset = (page - 1) * per_page

        cursor.execute('''
            SELECT * FROM users 
            ORDER BY registration_date DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        users = cursor.fetchall()
        conn.close()

        start_index = offset + 1
        end_index = min(offset + per_page, total_users)

        return {
            'items': users,
            'total': total_users,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'start_index': start_index,
            'end_index': end_index
        }

    def get_user_conversation(self, user_id: int, limit: Optional[int] = None):
        """Return message history for a user ordered by timestamp."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
            SELECT mh.*, u.username, u.first_name, u.last_name
            FROM message_history mh
            LEFT JOIN users u ON mh.user_id = u.user_id
            WHERE mh.user_id = ?
            ORDER BY mh.timestamp ASC
        '''

        if limit:
            query += ' LIMIT ?'
            cursor.execute(query, (user_id, limit))
        else:
            cursor.execute(query, (user_id,))

        messages = cursor.fetchall()
        conn.close()
        return messages

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

    def get_conversation_history(self, user_id, character_id=None, limit=10):
        """Get recent conversation history for AI context (per user + character)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if character_id is not None:
            cursor.execute('''
                SELECT user_message, bot_response, message_type, timestamp
                FROM message_history
                WHERE user_id = ? AND character_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, character_id, limit))
        else:
            # Backward compatibility for rows created before character-aware memory.
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

    def save_message_history(self, user_id, message_type, user_message, bot_response, ai_model=None, tokens_used=0, cost=0.0, context_length=0, venice_metadata=None, character_id=None):
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
                 completion_tokens, prompt_tokens, total_tokens, character_id, response_id, finish_reason, response_created,
                 venice_parameters, full_response_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id, message_type, user_message, bot_response, ai_model, tokens_used, calculated_cost, context_length,
                completion_tokens,
                prompt_tokens,
                total_tokens,
                character_id,
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
                (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length, character_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, message_type, user_message, bot_response, ai_model, tokens_used, cost, context_length, character_id))

        # Keep only the latest 50 history rows for each (user_id, character_id).
        if character_id is not None:
            cursor.execute('''
                DELETE FROM message_history
                WHERE user_id = ? AND character_id = ? AND id NOT IN (
                    SELECT id FROM message_history
                    WHERE user_id = ? AND character_id = ?
                    ORDER BY timestamp DESC, id DESC
                    LIMIT 50
                )
            ''', (user_id, character_id, user_id, character_id))
        
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
    
    # Character Management Methods
    def get_characters(self, active_only: bool = True) -> List[Dict]:
        """Get all characters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM characters"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY created_date ASC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def get_character(self, character_id: int) -> Optional[Dict]:
        """Get a specific character by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def create_character(self, name: str, description: str, instruction: str, is_active: bool = True) -> int:
        """Create a new character and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO characters (name, description, instruction, is_active)
            VALUES (?, ?, ?, ?)
        ''', (name, description, instruction, is_active))
        
        character_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return character_id
    
    def update_character(self, character_id: int, name: str = None, description: str = None, 
                        instruction: str = None, is_active: bool = None) -> bool:
        """Update an existing character"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if instruction is not None:
            updates.append("instruction = ?")
            params.append(instruction)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_date = ?")
        params.append(datetime.now())
        params.append(character_id)
        
        query = f"UPDATE characters SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_character(self, character_id: int) -> bool:
        """Delete a character (or set as inactive)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if any users are using this character
        cursor.execute("SELECT COUNT(*) FROM users WHERE character_id = ?", (character_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Don't delete, just deactivate
            cursor.execute("UPDATE characters SET is_active = 0 WHERE id = ?", (character_id,))
        else:
            # Safe to delete
            cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def set_user_character(self, user_id: int, character_id: int) -> bool:
        """Set a user's selected character"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET character_id = ? WHERE user_id = ?
        ''', (character_id, user_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_user_character(self, user_id: int) -> Optional[Dict]:
        """Get the character selected by a user"""
        user = self.get_user(user_id)
        if not user or not user.get('character_id'):
            return None
        
        return self.get_character(user['character_id'])
    
    # Activity Logging Methods
    def log_user_activity(self, user_id: int, activity_type: str, activity_data: dict):
        """Log user activity if activity logging is enabled"""
        if not self.get_setting('activity_logging_enabled', 'true').lower() == 'true':
            return  # Activity logging is disabled
        
        import json
        from datetime import datetime
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Add timestamp to activity data
        activity_data['timestamp'] = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO user_activity_logs (user_id, activity_type, activity_data)
            VALUES (?, ?, ?)
        ''', (user_id, activity_type, json.dumps(activity_data, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
    
    def get_user_activity_logs(self, user_id: int, limit: int = 100) -> list:
        """Get user activity logs (most recent first)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT activity_type, activity_data, timestamp
            FROM user_activity_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        logs = []
        for row in cursor.fetchall():
            import json
            try:
                activity_data = json.loads(row[1])
                logs.append({
                    'type': row[0],
                    'data': activity_data,
                    'timestamp': row[2]
                })
            except json.JSONDecodeError:
                # Skip corrupted JSON data
                continue
        
        conn.close()
        return logs
    
    def get_user_activity_count(self, user_id: int) -> int:
        """Get total count of user activity logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_activity_logs WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def clear_user_activity_logs(self, user_id: int, days_old: int = 30):
        """Clear old activity logs for a user (older than specified days)"""
        from datetime import datetime, timedelta
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        cursor.execute('''
            DELETE FROM user_activity_logs 
            WHERE user_id = ? AND timestamp < ?
        ''', (user_id, cutoff_date.isoformat()))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count