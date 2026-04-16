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
import time
import gc
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database import Database
from telegram_bot import TelegramBot
from admin_dashboard import app as dashboard_app


def get_app_root() -> Path:
    """Return the directory where the application should read/write runtime files."""
    if getattr(sys, 'frozen', False):  # Running inside PyInstaller bundle
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class BotManager:
    def __init__(self):
        self.bot_thread = None
        self.dashboard_thread = None
        self.db = Database()

    def validate_environment(self, require_bot_token: bool = True):
        """Validate configuration; optionally require bot token."""
        print("Validating configuration...")
        try:
            if require_bot_token:
                Config.validate_config()
            print("Configuration is valid.")
            return True
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("Set BOT_TOKEN in dashboard settings (database) and restart.")
            return False

    def has_bot_token(self) -> bool:
        """Return True when bot token is available from database settings."""
        token = Config.get_bot_token()
        return bool(token and token.strip())
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level_str = self.db.get_setting('log_level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)

        log_path = get_app_root() / 'bot.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(str(log_path), encoding='utf-8')
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
        """Start the Telegram bot with auto-restart capability"""
        print("🤖 Starting Telegram bot with auto-restart...")
        try:
            # Import and run the bot directly
            from telegram_bot import TelegramBot
            import time
            import gc
            import psutil
            import os
            
            # Run in a separate thread instead of process
            import threading
            import asyncio
            
            def run_bot():
                restart_count = 0
                max_restarts = 10  # Prevent infinite restart loops
                
                while restart_count < max_restarts:
                    try:
                        print(f"🤖 Starting bot instance #{restart_count + 1}")
                        
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        bot = TelegramBot()
                        bot.run()
                        
                        # If we reach here, bot exited normally
                        print("🤖 Bot exited normally")
                        break
                        
                    except Exception as e:
                        restart_count += 1
                        print(f"❌ Bot crashed (attempt {restart_count}/{max_restarts}): {e}")
                        
                        # Memory cleanup
                        gc.collect()
                        
                        # Check memory usage
                        try:
                            process = psutil.Process(os.getpid())
                            memory_mb = process.memory_info().rss / 1024 / 1024
                            print(f"📊 Memory usage: {memory_mb:.1f}MB")
                            
                            if memory_mb > 800:  # If over 800MB
                                print("⚠️ High memory usage detected, forcing cleanup")
                                gc.collect()
                        except:
                            pass
                        
                        if restart_count < max_restarts:
                            print(f"🔄 Restarting bot in 30 seconds...")
                            time.sleep(30)
                        else:
                            print("❌ Maximum restart attempts reached. Bot stopped.")
                            break
            
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            print(f"✅ Telegram bot started with auto-restart capability")
            return bot_thread
            
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            return None
    
    def start_admin_dashboard(self):
        """Start the admin dashboard"""
        print("🌐 Starting admin dashboard...")
        try:
            dashboard_host, dashboard_port = self._resolve_dashboard_binding()
            # Import and run dashboard in a thread
            import threading
            def run_dashboard():
                try:
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
        """Start dashboard always; start bot only if BOT_TOKEN exists."""
        self.setup_logging()
        
        if not self.initialize_database():
            return False
        
        # Start dashboard first so hosted setup is always reachable
        self.dashboard_thread = self.start_admin_dashboard()

        # Start bot only when token is configured
        if self.has_bot_token():
            self.bot_thread = self.start_telegram_bot()
        else:
            print("BOT_TOKEN not configured. Dashboard is running; set token in dashboard then restart.")

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
            dashboard_host, dashboard_port = self._resolve_dashboard_binding()
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

    def _resolve_dashboard_binding(self):
        """
        Resolve dashboard host/port with hosted-platform overrides.
        Railway/Render/Heroku-like envs require binding to 0.0.0.0:$PORT.
        """
        hosted_port = os.getenv('PORT')
        if hosted_port:
            return '0.0.0.0', int(hosted_port)

        dashboard_host = self.db.get_setting('dashboard_host', '127.0.0.1')
        dashboard_port = int(self.db.get_setting('dashboard_port', '5000'))
        return dashboard_host, dashboard_port

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