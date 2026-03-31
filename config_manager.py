#!/usr/bin/env python3
"""Configuration Management Utility that stores settings in the database."""

import argparse
from typing import Dict, Optional

from database import Database
from config import Config


class ConfigManager:
    """Helper for reading and updating admin settings."""

    KEY_MAP: Dict[str, str] = {
        'BOT_TOKEN': 'bot_token',
        'ADMIN_CHAT_ID': 'admin_chat_id',
        'ADMIN_USERNAME': 'admin_username',
        'ADMIN_PASSWORD': 'admin_password',
        'SECRET_KEY': 'secret_key',
        'SIMULATION_MODE': 'simulation_mode',
        'FREE_MESSAGES': 'free_messages',
        'FREE_TEXT_MESSAGES': 'free_text_messages',
        'FREE_IMAGE_MESSAGES': 'free_image_messages',
        'FREE_VIDEO_MESSAGES': 'free_video_messages',
        'TELEGRAM_STARS_ENABLED': 'telegram_stars_enabled',
        'TON_ENABLED': 'ton_enabled',
        'TON_API_KEY': 'ton_api_key',
        'TON_WALLET_ADDRESS': 'ton_mainnet_wallet_address',
        'TON_MAINNET_WALLET_ADDRESS': 'ton_mainnet_wallet_address',
        'TON_TESTNET_WALLET_ADDRESS': 'ton_testnet_wallet_address',
        'TON_NETWORK_MODE': 'ton_network_mode',
        'WEBHOOK_URL': 'webhook_url',
        'AI_API_KEY': 'ai_api_key',
        'VENICE_INFERENCE_KEY': 'venice_inference_key',
        'AI_MODEL': 'ai_model',
        'AI_BASE_URL': 'ai_base_url',
        'DASHBOARD_HOST': 'dashboard_host',
        'DASHBOARD_PORT': 'dashboard_port',
        'LOG_LEVEL': 'log_level',
        'BOT_RUNNING': 'bot_running',
        'BOT_ACTIVE': 'bot_active',
        'ACTIVITY_LOGGING_ENABLED': 'activity_logging_enabled',
        'MAX_IMAGE_SIZE': 'max_image_size',
        'MAX_VIDEO_SIZE': 'max_video_size',
        'AI_RESPONSE_TIMEOUT': 'ai_response_timeout',
        'MAX_REQUESTS_PER_MINUTE': 'max_requests_per_minute',
        'MAX_REQUESTS_PER_HOUR': 'max_requests_per_hour',
        'CONVERSATION_HISTORY_LENGTH': 'conversation_history_length',
        'CONTEXT_WINDOW_HOURS': 'context_window_hours',
        'INPUT_TOKEN_PRICE_PER_1M': 'input_token_price_per_1m',
        'OUTPUT_TOKEN_PRICE_PER_1M': 'output_token_price_per_1m',
        'TON_PRICE_USD': 'ton_price_usd',
        'STARS_PRICE_USD': 'stars_price_usd',
    }

    SENSITIVE_KEYS = {
        'bot_token',
        'ai_api_key',
        'venice_inference_key',
        'admin_password',
        'secret_key',
        'ton_api_key',
    }

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db = Database(db_path)
        self.load_config()

    def load_config(self) -> None:
        """Refresh settings from the database."""
        self.config = self.db.get_all_settings()

    def _resolve_key(self, key: str) -> str:
        return self.KEY_MAP.get(key.upper(), key)

    def set_config(self, key: str, value) -> None:
        """Persist a configuration value."""
        db_key = self._resolve_key(key)
        normalized = 'true' if value is True else 'false' if value is False else str(value)
        self.db.update_setting(db_key, normalized)
        self.config[db_key] = normalized
        print(f"✅ Set {db_key} = {normalized}")

    def get_config(self, key: str) -> str:
        db_key = self._resolve_key(key)
        return self.config.get(db_key, '')

    def interactive_setup(self) -> None:
        """Interactive wizard for first-time configuration."""
        print("🤖 Telegram Bot Configuration Setup")
        print("=" * 50)

        bot_token = input("Enter your Telegram Bot Token (from @BotFather): ").strip()
        if bot_token:
            self.set_config('BOT_TOKEN', bot_token)

        admin_id = input("Enter your Telegram User ID (admin): ").strip() or '0'
        self.set_config('ADMIN_CHAT_ID', admin_id)

        print("\n🧠 AI Configuration")
        api_key = input("Enter your Venice Inference Key: ").strip()
        if api_key:
            self.set_config('AI_API_KEY', api_key)
            self.set_config('VENICE_INFERENCE_KEY', api_key)

        models = Config.get_ai_models()
        print("\nAvailable AI Models:")
        for idx, model in enumerate(models, 1):
            print(f" {idx}. {model}")
        choice = input(f"Choose AI model (1-{len(models)}, default 1): ").strip()
        try:
            selected_model = models[int(choice) - 1]
        except (ValueError, IndexError):
            selected_model = models[0]
        self.set_config('AI_MODEL', selected_model)

        base_url = input("API Base URL (default https://api.venice.ai/api/v1): ").strip() or 'https://api.venice.ai/api/v1'
        self.set_config('AI_BASE_URL', base_url)

        print("\n💰 Payment Configuration")
        ton_wallet = input("TON mainnet wallet address (optional): ").strip()
        if ton_wallet:
            self.set_config('TON_MAINNET_WALLET_ADDRESS', ton_wallet)

        ton_test_wallet = input("TON testnet wallet address (optional): ").strip()
        if ton_test_wallet:
            self.set_config('TON_TESTNET_WALLET_ADDRESS', ton_test_wallet)

        print("\n🔧 Admin Dashboard Credentials")
        admin_user = input("Admin username (default admin): ").strip() or 'admin'
        admin_pass = input("Admin password (default admin123): ").strip() or 'admin123'
        self.set_config('ADMIN_USERNAME', admin_user)
        self.set_config('ADMIN_PASSWORD', admin_pass)

        secret_key = input("Flask secret key (blank to keep default): ").strip()
        if secret_key:
            self.set_config('SECRET_KEY', secret_key)

        print("\n⚙️ Basic Settings")
        sim_mode = input("Enable simulation mode for testing? (y/N): ").strip().lower() == 'y'
        self.set_config('SIMULATION_MODE', 'true' if sim_mode else 'false')
        self.set_config('BOT_RUNNING', 'true')
        self.set_config('BOT_ACTIVE', 'true')

        free_msgs = input("Number of free text messages (default 5): ").strip() or '5'
        free_img = input("Number of free image messages (default 2): ").strip() or '2'
        free_vid = input("Number of free video messages (default 1): ").strip() or '1'
        self.set_config('FREE_TEXT_MESSAGES', free_msgs)
        self.set_config('FREE_IMAGE_MESSAGES', free_img)
        self.set_config('FREE_VIDEO_MESSAGES', free_vid)
        self.set_config('FREE_MESSAGES', free_msgs)

        print("\n✅ Configuration saved to database.")

    def validate_config(self) -> bool:
        """Validate required configuration values exist."""
        self.load_config()
        errors = []
        if not self.config.get('bot_token'):
            errors.append('bot_token is missing')
        if not self.config.get('ai_api_key') and not self.config.get('venice_inference_key'):
            errors.append('Venice inference key is missing')

        if errors:
            print("❌ Configuration Errors:")
            for err in errors:
                print(f"  - {err}")
            return False

        print("✅ Configuration is valid!")
        return True

    def show_config(self) -> None:
        """Print the current configuration (masking sensitive values)."""
        self.load_config()
        print("📋 Current Configuration")
        print("=" * 50)
        for key in sorted(self.config.keys()):
            value = self.config[key]
            if key in self.SENSITIVE_KEYS and value:
                display = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display = value
            print(f"{key:<30} = {display}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram Bot Configuration Manager")
    parser.add_argument('--database', metavar='PATH', help='Path to bot_database.db (defaults to repository location)')
    parser.add_argument('--setup', action='store_true', help='Interactive setup')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='Set configuration value')
    parser.add_argument('--get', metavar='KEY', help='Get configuration value')

    args = parser.parse_args()
    manager = ConfigManager(db_path=args.database)

    if args.setup:
        manager.interactive_setup()
    elif args.validate:
        manager.validate_config()
    elif args.show:
        manager.show_config()
    elif args.set:
        key, value = args.set
        manager.set_config(key, value)
    elif args.get:
        value = manager.get_config(args.get)
        print(f"{args.get} = {value}")
    else:
        print("🤖 Telegram Bot Configuration Manager")
        print("Use --help for available options")
        print("\nQuick start: python config_manager.py --setup")


if __name__ == '__main__':
    main()
