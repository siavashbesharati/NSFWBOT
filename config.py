import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Essential Bot Configuration (still from environment)
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    _admin_chat_id = os.getenv('ADMIN_CHAT_ID', '0')
    try:
        ADMIN_CHAT_ID = int(_admin_chat_id)
    except ValueError:
        # If it's a username, set to 0 and let the bot handle it
        ADMIN_CHAT_ID = 0
        ADMIN_USERNAME_TELEGRAM = _admin_chat_id
    
    # Database Configuration (essential for startup)
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')
    
    # Admin Dashboard Security (essential for initial setup)
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Webhook Configuration (environment-specific)
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
    
    # All other settings are now managed via database settings:
    # - Payment configuration (TON_WALLET_ADDRESS, TELEGRAM_STARS_ENABLED, TON_ENABLED)
    # - Bot behavior (SIMULATION_MODE, BOT_RUNNING, FREE_MESSAGES)
    # - Pricing (DEFAULT_TEXT_PRICE, DEFAULT_IMAGE_PRICE, DEFAULT_VIDEO_PRICE)
    # - Limits (MAX_IMAGE_SIZE, MAX_VIDEO_SIZE, AI_RESPONSE_TIMEOUT)
    # - Dashboard settings (DASHBOARD_HOST, DASHBOARD_PORT, ADMIN_USERNAME, ADMIN_PASSWORD)
    # - Rate limiting (MAX_REQUESTS_PER_MINUTE, MAX_REQUESTS_PER_HOUR)
    # - Logging (LOG_LEVEL)
    # - Webhook URL (WEBHOOK_URL)
    # - OpenRouter settings (OPENROUTER_API_KEY, OPENROUTER_MODEL)
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_vars = ['BOT_TOKEN']  # Only BOT_TOKEN is required from env
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_ai_models(cls):
        """Get list of available AI models"""
        return [
            'openai/gpt-3.5-turbo',
            'openai/gpt-4',
            'anthropic/claude-3-haiku',
            'anthropic/claude-3-sonnet',
            'google/gemini-pro',
            'mistralai/mistral-7b-instruct'
        ]