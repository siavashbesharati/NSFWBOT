import json
import os
from typing import Dict, Any, Optional, List

class TranslationManager:
    """
    Manages translations for the Telegram bot supporting multiple languages.
    Supported languages: English, Arabic, Farsi, Turkish, Russian, Spanish, Chinese
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ar': 'العربية',
        'fa': 'فارسی', 
        'tr': 'Türkçe',
        'ru': 'Русский',
        'es': 'Español',
        'zh': '中文'
    }
    
    DEFAULT_LANGUAGE = 'en'
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files from the languages directory"""
        languages_dir = os.path.join(os.path.dirname(__file__), 'languages')
        
        if not os.path.exists(languages_dir):
            os.makedirs(languages_dir, exist_ok=True)
        
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            translation_file = os.path.join(languages_dir, f'{lang_code}.json')
            
            if os.path.exists(translation_file):
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Error loading translation file {translation_file}: {e}")
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}
    
    def get_text(self, key: str, lang_code: str = None, **kwargs) -> str:
        """
        Get translated text by key for the specified language.
        
        Args:
            key: Translation key (e.g., 'welcome_message')
            lang_code: Language code (e.g., 'en', 'ar', 'fa')
            **kwargs: Variables to format into the translation string
        
        Returns:
            Translated text or fallback to English/key if not found
        """
        if lang_code is None:
            lang_code = self.DEFAULT_LANGUAGE
        
        # Get translation from specified language
        translation = self._get_nested_translation(self.translations.get(lang_code, {}), key)
        
        # Fallback to English if not found
        if translation is None and lang_code != self.DEFAULT_LANGUAGE:
            translation = self._get_nested_translation(self.translations.get(self.DEFAULT_LANGUAGE, {}), key)
        
        # Final fallback to key itself
        if translation is None:
            translation = key
        
        # Format with provided variables
        try:
            return translation.format(**kwargs) if kwargs else translation
        except (KeyError, ValueError):
            return translation
    
    def _get_nested_translation(self, translations: Dict, key: str) -> Optional[str]:
        """Get translation value from nested dictionary using dot notation"""
        keys = key.split('.')
        value = translations
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value if isinstance(value, str) else None
    
    def get_language_name(self, lang_code: str) -> str:
        """Get the display name of a language"""
        return self.SUPPORTED_LANGUAGES.get(lang_code, lang_code)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get all available languages"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def is_supported_language(self, lang_code: str) -> bool:
        """Check if a language code is supported"""
        return lang_code in self.SUPPORTED_LANGUAGES

    def get_characters(self, lang_code: str = None) -> List[Dict[str, Any]]:
        """Return list of character definitions for the given language."""
        if lang_code is None:
            lang_code = self.DEFAULT_LANGUAGE

        characters = self._get_character_section(lang_code)
        if not characters and lang_code != self.DEFAULT_LANGUAGE:
            characters = self._get_character_section(self.DEFAULT_LANGUAGE)

        result: List[Dict[str, Any]] = []
        if isinstance(characters, dict):
            for key, value in characters.items():
                if isinstance(value, dict):
                    item = {
                        'key': key,
                        'slug': value.get('slug') or key,
                        'name': value.get('name', ''),
                        'description': value.get('description', ''),
                        'instruction': value.get('instruction') or value.get('description', '')
                    }
                    result.append(item)
        elif isinstance(characters, list):
            for entry in characters:
                if isinstance(entry, dict):
                    item = {
                        'key': entry.get('key') or entry.get('slug'),
                        'slug': entry.get('slug') or entry.get('key'),
                        'name': entry.get('name', ''),
                        'description': entry.get('description', ''),
                        'instruction': entry.get('instruction') or entry.get('description', '')
                    }
                    result.append(item)
        return result

    def get_character_by_slug(self, slug: str, lang_code: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific character by slug for the given language."""
        if not slug:
            return None

        lang_code = lang_code or self.DEFAULT_LANGUAGE
        for character in self.get_characters(lang_code):
            if character.get('slug') == slug:
                return character

        if lang_code != self.DEFAULT_LANGUAGE:
            for character in self.get_characters(self.DEFAULT_LANGUAGE):
                if character.get('slug') == slug:
                    return character
        return None

    def _get_character_section(self, lang_code: str) -> Any:
        """Internal helper to fetch raw character section for a language."""
        translations = self.translations.get(lang_code, {})
        return translations.get('characters') if isinstance(translations, dict) else None
    
    def get_language_selection_keyboard_data(self) -> list:
        """Get keyboard data for language selection"""
        keyboard_data = []
        for code, name in self.SUPPORTED_LANGUAGES.items():
            keyboard_data.append({
                'text': f"{name}",
                'callback_data': f"set_lang_{code}"
            })
        return keyboard_data

# Global translation manager instance
translation_manager = TranslationManager()

def get_text(key: str, lang_code: str = None, **kwargs) -> str:
    """Convenience function to get translated text"""
    return translation_manager.get_text(key, lang_code, **kwargs)

def get_user_language(user_id: int, database) -> str:
    """Get user's preferred language from database"""
    try:
        user_data = database.get_user(user_id)
        if user_data and 'language' in user_data:
            return user_data['language']
    except:
        pass
    return TranslationManager.DEFAULT_LANGUAGE

def set_user_language(user_id: int, lang_code: str, database) -> bool:
    """Set user's preferred language in database"""
    try:
        if translation_manager.is_supported_language(lang_code):
            database.set_user_language(user_id, lang_code)
            return True
    except:
        pass
    return False