#!/usr/bin/env python3
"""
Test script for the translation middleware functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translation_middleware import translate_user_input, translate_ai_response

async def test_translation():
    """Test the translation middleware"""
    print("🧪 Testing Translation Middleware")
    print("=" * 50)
    
    # Test cases: [text, expected_language, target_language]
    test_cases = [
        ("Hello, how are you?", "en", "fa"),  # English to Farsi
        ("سلام، چطوری؟", "fa", "en"),           # Farsi to English  
        ("Hola, ¿cómo estás?", "es", "en"),   # Spanish to English
        ("Привет, как дела?", "ru", "en"),    # Russian to English
        ("مرحبا، كيف حالك؟", "ar", "en"),       # Arabic to English
    ]
    
    for i, (text, source_lang, target_lang) in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"   Original: {text}")
        print(f"   Expected source: {source_lang}")
        print(f"   Target: {target_lang}")
        print("-" * 30)
        
        try:
            # Test user input translation (to English)
            english_text, detected_lang = await translate_user_input(text, target_lang)
            print(f"✅ To English: {english_text}")
            print(f"🔍 Detected: {detected_lang}")
            
            # Test AI response translation (from English back to target)
            if target_lang != 'en' and english_text:
                translated_back = await translate_ai_response(english_text, source_lang)
                print(f"🔄 Back to {source_lang}: {translated_back}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Translation test completed!")

async def test_simple_translation():
    """Simple test with one example"""
    print("🌍 Simple Translation Test")
    print("-" * 30)
    
    # Test English to Farsi
    test_text = "Hello! How can I help you today?"
    print(f"Original English: {test_text}")
    
    try:
        # Translate to Farsi
        farsi_response = await translate_ai_response(test_text, "fa")
        print(f"Farsi Translation: {farsi_response}")
        
        # Test detection and back-translation
        english_back, detected = await translate_user_input(farsi_response, "fa")
        print(f"Back to English: {english_back}")
        print(f"Detected Language: {detected}")
        
    except Exception as e:
        print(f"❌ Error in simple test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Translation Tests...")
    
    # Run simple test first
    asyncio.run(test_simple_translation())
    
    print("\n" + "=" * 60 + "\n")
    
    # Run full test suite
    asyncio.run(test_translation())