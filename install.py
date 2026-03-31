#!/usr/bin/env python3
"""
One-Click Installation Script for Telegram Bot
Handles dependencies, configuration, and initial setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print installation banner"""
    print("""
🤖 Telegram AI Bot Installer
===============================
    
This script will help you set up your Telegram bot with:
✅ AI responses (Venice AI)
✅ Payment system (TON & Stars)  
✅ Admin dashboard
✅ User management
✅ Package system

Let's get started!
""")

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required!")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again.")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("   Please install manually: pip install -r requirements.txt")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\n⚙️ Setting up environment file...")
    
    env_file = Path(".env")
    example_file = Path("env_example.txt")
    
    if env_file.exists():
        overwrite = input("📋 .env file exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("📄 Keeping existing .env file")
            return True
    
    if example_file.exists():
        try:
            # Copy example to .env
            with open(example_file, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file from template")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env_example.txt not found!")
        return False

def run_configuration():
    """Run interactive configuration"""
    print("\n🔧 Starting configuration setup...")
    
    try:
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.interactive_setup()
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_setup():
    """Test the bot setup"""
    print("\n🧪 Testing setup...")
    
    try:
        # Test configuration
        from config import Config
        Config.validate_config()
        print("✅ Configuration is valid!")
        
        # Test database
        from database import Database
        db = Database()
        db.init_db()
        print("✅ Database initialized!")
        
        return True
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def show_next_steps():
    """Show what to do next"""
    print("""
🎉 Installation Complete!

Next Steps:
===========

1. 🚀 Start the bot:
   python start_bot.py start

2. 🌐 Access admin dashboard:
   http://127.0.0.1:5000
   (Login: admin / admin123)

3. 🧪 Test in simulation mode:
   - Payments are automatically approved
   - No real money is charged
   - Perfect for testing

4. 🔧 Configure packages:
   - Use admin dashboard to create packages
   - Set prices in TON and Stars
   - Enable/disable as needed

5. 📱 Test with Telegram:
   - Find your bot on Telegram
   - Send /start command
   - Try the full user flow

Useful Commands:
================
- python start_bot.py status          # Check service status
- python start_bot.py bot-only        # Start only the bot
- python start_bot.py dashboard-only  # Start only dashboard
- python config_manager.py --show     # Show configuration
- python config_manager.py --validate # Validate settings

Documentation:
==============
- Check README.md for detailed guide
- Admin dashboard has built-in help
- Use simulation mode for testing

Support:
========
- Check logs in bot.log file
- Use admin dashboard for monitoring
- Test thoroughly before production

Happy botting! 🤖✨
""")

def main():
    """Main installation process"""
    print_banner()
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed at dependencies step")
        sys.exit(1)
    
    # Setup environment
    if not create_env_file():
        print("\n❌ Installation failed at environment setup")
        sys.exit(1)
    
    # Interactive configuration
    config_setup = input("\n🔧 Run configuration setup now? (Y/n): ").strip().lower()
    if config_setup != 'n':
        if not run_configuration():
            print("\n⚠️ Configuration incomplete - you can run it later with:")
            print("   python config_manager.py --setup")
    
    # Test setup
    test_now = input("\n🧪 Test the setup now? (Y/n): ").strip().lower()
    if test_now != 'n':
        if not test_setup():
            print("\n⚠️ Setup test failed - check configuration")
    
    # Success message
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)