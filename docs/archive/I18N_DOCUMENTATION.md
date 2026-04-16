# Internationalization (i18n) System Documentation

## Overview

The bot now supports internationalization (i18n) with the following languages:
- **English** (en) - Default
- **Arabic** (ar) - العربية  
- **Farsi/Persian** (fa) - فارسی
- **Turkish** (tr) - Türkçe
- **Russian** (ru) - Русский
- **Spanish** (es) - Español
- **Chinese** (zh) - 中文

## Files Structure

```
NSFWBOT/
├── translations.py          # Main translation manager
├── languages/              # Translation files directory
│   ├── en.json             # English translations (base)
│   ├── ar.json             # Arabic translations
│   ├── fa.json             # Farsi translations
│   ├── tr.json             # Turkish translations
│   ├── ru.json             # Russian translations
│   ├── es.json             # Spanish translations
│   └── zh.json             # Chinese translations
└── test_i18n_system.py    # Test script
```

## User Commands

### Language Selection
- `/language` - Shows language selection menu
- Users can select their preferred language from an inline keyboard
- Language preference is stored in the database per user

### Supported Commands (All Translated)
- `/start` - Welcome message with referral support
- `/help` - Command help and bot information  
- `/dashboard` - User statistics and usage
- `/packages` - Available message packages
- `/balance` - Remaining credits
- `/referral` - Referral system information
- `/reset` - Reset conversation history
- `/language` - Change language preference

## For Developers

### Using Translations in Code

```python
from translations import get_text, get_user_language

# Get user's language preference
user_lang = get_user_language(user_id, database)

# Get translated text
message = get_text('welcome.title', user_lang, first_name=user.first_name)

# With variable substitution
message = get_text('welcome.free_messages', user_lang, 
                  free_text=10, free_image=5, free_video=3)
```

### Adding New Translations

1. **Add to English first** (`languages/en.json`):
```json
{
  "new_section": {
    "new_key": "Hello {name}!"
  }
}
```

2. **Add to all other language files** with appropriate translations

3. **Use in code**:
```python
text = get_text('new_section.new_key', user_lang, name="John")
```

### Translation Key Structure

Translations use dot notation for nested keys:
```json
{
  "commands": {
    "start": "🚀 Start the bot"
  },
  "welcome": {
    "title": "🤖 Welcome to the AI Bot, {first_name}!"
  }
}
```

Access with: `get_text('commands.start', lang)` or `get_text('welcome.title', lang, first_name='John')`

## Database Schema

### Users Table Addition
- Added `language` column (TEXT, DEFAULT "en")
- Stores user's preferred language code

### Database Methods
```python
# Set user language
database.set_user_language(user_id, 'es')

# Get user language (returns 'en' if not set)
lang = database.get_user_language(user_id)
```

## Features

### ✅ Implemented Features
- Complete bot command translations
- User language preference storage
- Inline keyboard language selector  
- Fallback system (missing key → key name, missing language → English)
- Variable substitution in translations
- RTL language support (Arabic, Farsi)
- Database integration
- Comprehensive test suite

### 🔄 Fallback System
1. **Missing Translation**: Returns the key name itself
2. **Missing Language**: Falls back to English translation
3. **Missing Variables**: Handles gracefully without crashing

### 🧪 Testing
Run the test suite:
```bash
python test_i18n_system.py
```

Tests include:
- Translation loading
- Database integration  
- Fallback mechanisms
- Variable formatting
- Language completeness

## Usage Examples

### For Users
1. Start the bot: `/start`
2. Change language: `/language`
3. Select preferred language from the menu
4. All subsequent messages will be in the selected language

### For Admins
- Admin commands (`/testapi`) show messages in the admin's selected language
- Admin dashboard remains in English (primarily for technical users)

## Adding New Languages

1. **Create new language file**: `languages/xx.json` (where xx is language code)
2. **Copy structure from** `languages/en.json`
3. **Translate all strings** maintaining the same JSON structure
4. **Add to supported languages** in `translations.py`:
```python
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'xx': 'New Language Name',
    # ... other languages
}
```
5. **Test thoroughly** with `test_i18n_system.py`

## Technical Notes

- **Encoding**: All files use UTF-8 encoding for proper international character support
- **Performance**: Translations are loaded once at startup and cached in memory
- **Thread Safety**: Translation manager is thread-safe for read operations
- **Memory Usage**: Minimal - all translations loaded into a single dictionary structure

## Maintenance

### Regular Tasks
1. **Add new translations** when adding new bot features
2. **Test language completeness** using the test script
3. **Update documentation** when adding new languages
4. **Review translations** for accuracy and cultural appropriateness

### Monitoring
- Monitor user language preferences in database
- Check for missing translation keys in logs
- Verify fallback system is working for edge cases

## Troubleshooting

### Common Issues
1. **"nonexistent.key" appears**: Translation key missing, add to language files
2. **English appears instead of selected language**: Language file missing or corrupted
3. **Variables not replaced**: Check variable names match exactly in translation and code

### Debug Steps
1. Run `python test_i18n_system.py` to verify system health
2. Check language files are valid JSON
3. Verify database has language column and user preferences are set
4. Check logs for translation errors