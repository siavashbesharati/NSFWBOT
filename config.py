import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from database import Database


def _get_app_root() -> Path:
    """Return directory containing the application files."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _get_database() -> Database:
    """Return a shared Database instance for configuration access."""
    return Database()


class Config:
    """Database-backed configuration helpers."""

    REQUIRED_KEYS = ('bot_token',)

    @classmethod
    def get_setting(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch a configuration value from the database with optional env fallback."""
        value = _get_database().get_setting(key)
        if value is None or value == '':
            env_value = os.getenv(key.upper())
            return env_value if env_value not in ('', None) else default
        return value

    @classmethod
    def get_bot_token(cls) -> str:
        """Convenience accessor for the Telegram bot token."""
        return (cls.get_setting('bot_token', '') or '').strip()

    @classmethod
    def get_database_path(cls) -> str:
        """Expose the resolved database path."""
        return _get_database().db_path

    @classmethod
    def validate_config(cls) -> bool:
        """Ensure required configuration keys are present before startup."""
        missing = []
        for key in cls.REQUIRED_KEYS:
            if not cls.get_setting(key, '').strip():
                missing.append(key)
        if missing:
            raise ValueError(
                "Missing required configuration: " + ", ".join(missing)
            )
        return True
    
    @classmethod
    def get_ai_models(cls):
        """Get list of available AI models"""
        return [
            'venice-uncensored',
            'llama-3.3-70b',
            'llama-3.2-3b',
            'qwen-2.5-72b-instruct',
            'mistral-31-24b'
        ]