import translators as ts
import asyncio
import time
from typing import Tuple, Optional

class TranslationMiddleware:
    """
    Translation middleware using Bing translator
    Auto-detects source language and translates to/from English
    """
    
    def __init__(self):
        """Initialize the translation middleware"""
        self.translator = 'bing'
        self._initialized = False
    
    async def initialize(self):
        """Initialize the translator - simplified for Bing only"""
        if not self._initialized:
            try:
                # Simple initialization - no preacceleration needed for Bing
                self._initialized = True
                print("✅ Bing translator initialized successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not initialize translator: {e}")
                self._initialized = True
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection - let Bing handle auto-detection
        Returns 'auto' to let Bing detect, or 'en' if likely English
        """
        try:
            # Simple heuristic to check if text is likely English
            if self._is_likely_english(text):
                return 'en'
            else:
                return 'auto'  # Let Bing handle auto-detection
            
        except Exception as e:
            print(f"⚠️ Language detection error: {e}")
            return 'auto'  # Fallback to auto-detection
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity calculation between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def translate_to_english(self, text: str, source_language: str = 'auto') -> Tuple[str, str]:
        """
        Translate text to English using Bing only
        Returns (translated_text, detected_language)
        """
        try:
            # Check if already English (simple check)
            if source_language == 'en' or self._is_likely_english(text):
                return text, 'en'
            
            print(f"🌐 Translating to English using Bing (from {source_language})...")
            start_time = time.time()
            
            # Run translation in thread to avoid blocking - BING ONLY
            loop = asyncio.get_event_loop()
            translated_text = await loop.run_in_executor(
                None,
                lambda: ts.translate_text(
                    query_text=text,
                    translator='bing',  # Force Bing only
                    from_language=source_language,
                    to_language='en',
                    if_show_time_stat=False
                )
            )
            
            translation_time = time.time() - start_time
            print(f"✅ Bing translated to English in {translation_time:.2f}s")
            
            return translated_text, source_language
            
        except Exception as e:
            print(f"❌ Bing translation to English failed: {e}")
            # Return original text if translation fails
            return text, 'unknown'
    
    async def translate_from_english(self, text: str, target_language: str) -> str:
        """
        Translate text from English to target language using Bing only
        """
        try:
            # If target is English, return as-is
            if target_language == 'en':
                return text
            
            print(f"🌐 Translating from English to {target_language} using Bing...")
            start_time = time.time()
            
            # Run translation in thread to avoid blocking - BING ONLY
            loop = asyncio.get_event_loop()
            translated_text = await loop.run_in_executor(
                None,
                lambda: ts.translate_text(
                    query_text=text,
                    translator='bing',  # Force Bing only
                    from_language='en',
                    to_language=target_language,
                    if_show_time_stat=False
                )
            )
            
            translation_time = time.time() - start_time
            print(f"✅ Bing translated to {target_language} in {translation_time:.2f}s")
            
            return translated_text
            
        except Exception as e:
            print(f"❌ Bing translation from English failed: {e}")
            # Return original text if translation fails
            return text
    
    def _is_likely_english(self, text: str) -> bool:
        """
        Simple heuristic to check if text is likely English
        """
        if not text:
            return True
        
        # Check for common English words
        english_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'this', 'that', 'these', 'those', 'what', 'where', 'when', 'why', 'how'
        }
        
        words = text.lower().split()
        if not words:
            return True
        
        english_word_count = sum(1 for word in words[:20] if word.strip('.,!?;:') in english_words)
        
        # If more than 30% are common English words, likely English
        return english_word_count / min(len(words), 20) > 0.3
    
    def get_language_code_for_user(self, user_lang: str) -> str:
        """
        Convert user language code to translator language code
        """
        # Map common language codes
        lang_map = {
            'en': 'en',  # English
            'fa': 'fa',  # Persian/Farsi
            'ar': 'ar',  # Arabic
            'es': 'es',  # Spanish
            'ru': 'ru',  # Russian
            'tr': 'tr',  # Turkish
            'zh': 'zh',  # Chinese
            'fr': 'fr',  # French
            'de': 'de',  # German
            'it': 'it',  # Italian
            'pt': 'pt',  # Portuguese
            'ja': 'ja',  # Japanese
            'ko': 'ko',  # Korean
            'hi': 'hi',  # Hindi
            'ur': 'ur',  # Urdu
        }
        
        return lang_map.get(user_lang, 'en')  # Default to English if not found

# Global instance
translation_middleware = TranslationMiddleware()

async def translate_user_input(text: str, user_language: str) -> Tuple[str, str]:
    """
    Translate user input to English
    Returns (english_text, detected_language)
    """
    target_lang_code = translation_middleware.get_language_code_for_user(user_language)
    return await translation_middleware.translate_to_english(text, 'auto')

async def translate_ai_response(text: str, target_language: str) -> str:
    """
    Translate AI response from English to target language
    """
    target_lang_code = translation_middleware.get_language_code_for_user(target_language)
    return await translation_middleware.translate_from_english(text, target_lang_code)