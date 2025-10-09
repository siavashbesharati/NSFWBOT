#!/usr/bin/env python3
"""
Telegram Bot Startup Script
Manages bot startup, configuration validation, and service management
"""

import os
import sys
import asyncio
import logging
import subprocess
import signal
from pathlib import Path
from typing import Optional
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database import Database
from telegram_bot import TelegramBot
from admin_dashboard import app as dashboard_app

class BotManager:
    def __init__(self):
        self.bot_thread = None
        self.dashboard_thread = None
        self.db = Database()
        
    def validate_environment(self):
        """Validate that all required environment variables are set"""
        print("🔍 Validating configuration...")
        
        try:
            Config.validate_config()
            print("✅ Configuration is valid!")
            return True
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("\n💡 Run 'python config_manager.py --setup' to configure the bot")
            return False
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level_str = self.db.get_setting('log_level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('bot.log')
            ]
        )
        
        print(f"📝 Logging configured at {log_level_str} level")
    
    def initialize_database(self):
        """Initialize the database"""
        print("🗄️ Initializing database...")
        try:
            self.db.init_database()
            print("✅ Database initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    def start_telegram_bot(self):
        """Start the Telegram bot"""
        print("🤖 Starting Telegram bot...")
        try:
            # Import and run the bot directly
            from telegram_bot import TelegramBot
            
            # Run in a separate thread instead of process
            import threading
            import asyncio
            
            def run_bot():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    bot = TelegramBot()
                    bot.run()
                except Exception as e:
                    print(f"Bot error: {e}")
            
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            print(f"✅ Telegram bot started")
            return bot_thread
            
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            return None
    
    def start_admin_dashboard(self):
        """Start the admin dashboard"""
        print("🌐 Starting admin dashboard...")
        try:
            # Import and run dashboard in a thread
            import threading
            def run_dashboard():
                try:
                    dashboard_host = self.db.get_setting('dashboard_host', '127.0.0.1')
                    dashboard_port = int(self.db.get_setting('dashboard_port', '5000'))
                    dashboard_app.run(
                        host=dashboard_host,
                        port=dashboard_port,
                        debug=False,
                        use_reloader=False
                    )
                except Exception as e:
                    print(f"Dashboard error: {e}")
            
            dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
            dashboard_thread.start()
            
            dashboard_host = self.db.get_setting('dashboard_host', '127.0.0.1')
            dashboard_port = self.db.get_setting('dashboard_port', '5000')
            admin_username = self.db.get_setting('admin_username', 'admin')
            admin_password = self.db.get_setting('admin_password', 'admin')
            print(f"✅ Admin dashboard started at http://{dashboard_host}:{dashboard_port}")
            print(f"   Login: {admin_username} / {admin_password}")
            return dashboard_thread
            
        except Exception as e:
            print(f"❌ Failed to start dashboard: {e}")
            return None
    
    def stop_services(self):
        """Stop all services"""
        print("\n🛑 Stopping services...")
        
        # For threads, we just print info since daemon threads will stop with main process
        if self.bot_thread and self.bot_thread.is_alive():
            print("  Telegram bot will stop with main process...")
        
        if self.dashboard_thread and self.dashboard_thread.is_alive():
            print("  Admin dashboard will stop with main process...")
        
        print("✅ All services stopped")
    
    def start_full_stack(self):
        """Start both bot and dashboard"""
        if not self.validate_environment():
            return False
        
        self.setup_logging()
        
        if not self.initialize_database():
            return False
        
        # Start services
        self.bot_thread = self.start_telegram_bot()
        self.dashboard_thread = self.start_admin_dashboard()
        
        return True
    
    def status(self):
        """Show status of all services"""
        print("📊 Service Status:")
        print("=" * 30)
        
        # Bot status
        if self.bot_thread and self.bot_thread.is_alive():
            print(f"🤖 Telegram Bot: ✅ Running")
        else:
            print("🤖 Telegram Bot: ❌ Stopped")
        
        # Dashboard status
        if self.dashboard_thread and self.dashboard_thread.is_alive():
            dashboard_host = self.db.get_setting('dashboard_host', '127.0.0.1')
            dashboard_port = self.db.get_setting('dashboard_port', '5000')
            print(f"🌐 Admin Dashboard: ✅ Running")
            print(f"   URL: http://{dashboard_host}:{dashboard_port}")
        else:
            print("🌐 Admin Dashboard: ❌ Stopped")
        
        # Database status
        try:
            stats = self.db.get_stats()
            print(f"🗄️ Database: ✅ Connected")
            print(f"   Users: {stats.get('total_users', 0)}")
            print(f"   Messages: {stats.get('total_messages', 0)}")
        except Exception:
            print("🗄️ Database: ❌ Error")
        
        # Configuration
        simulation_mode = self.db.get_setting('simulation_mode', 'true').lower() == 'true'
        print(f"⚙️ Mode: {'🧪 Simulation' if simulation_mode else '🚀 Production'}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n📡 Received signal {signum}")
    if hasattr(signal_handler, 'bot_manager'):
        signal_handler.bot_manager.stop_services()
    sys.exit(0)

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Bot Manager")
    parser.add_argument('command', nargs='?', choices=['start', 'stop', 'restart', 'status', 'bot-only', 'dashboard-only'], 
                       default='start', help='Command to execute')
    parser.add_argument('--config', action='store_true', help='Validate configuration before starting')
    parser.add_argument('--setup', action='store_true', help='Run configuration setup')
    
    args = parser.parse_args()
    
    bot_manager = BotManager()
    signal_handler.bot_manager = bot_manager
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.setup:
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.interactive_setup()
        return
    
    if args.config:
        if not bot_manager.validate_environment():
            sys.exit(1)
        return
    
    try:
        if args.command == 'start':
            print("🚀 Starting Telegram Bot Stack...")
            if bot_manager.start_full_stack():
                print("\n✅ All services started successfully!")
                print("Press Ctrl+C to stop")
                
                # Keep main process alive
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                print("❌ Failed to start services")
                sys.exit(1)
        
        elif args.command == 'bot-only':
            print("🤖 Starting Telegram Bot only...")
            if bot_manager.validate_environment() and bot_manager.initialize_database():
                bot_manager.bot_thread = bot_manager.start_telegram_bot()
                print("Press Ctrl+C to stop")
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        
        elif args.command == 'dashboard-only':
            print("🌐 Starting Admin Dashboard only...")
            if bot_manager.validate_environment() and bot_manager.initialize_database():
                bot_manager.dashboard_thread = bot_manager.start_admin_dashboard()
                print("Press Ctrl+C to stop")
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        
        elif args.command == 'status':
            bot_manager.status()
        
        elif args.command == 'stop':
            bot_manager.stop_services()
        
        elif args.command == 'restart':
            bot_manager.stop_services()
            import time
            time.sleep(2)
            if bot_manager.start_full_stack():
                print("✅ Services restarted successfully!")
            else:
                print("❌ Failed to restart services")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        bot_manager.stop_services()
        sys.exit(1)
    
    finally:
        bot_manager.stop_services()

if __name__ == "__main__":
    main()