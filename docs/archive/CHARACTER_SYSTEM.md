# Character System Implementation

## Overview
The character system allows users to select AI personalities that define how the bot responds. Each character has a unique instruction (system prompt) that guides the AI's behavior.

## Features Implemented

### 1. Database Schema
- **characters table**: Stores character definitions
  - `id`: Primary key
  - `name`: Character name
  - `description`: Short description
  - `instruction`: System prompt for AI
  - `is_active`: Visibility flag
  - `created_date`, `updated_date`: Timestamps

- **users table**: Added `character_id` column to track user's selected character

### 2. Admin Dashboard
**New Pages:**
- `/characters` - List all characters
- `/characters/create` - Create new character
- `/characters/edit/<id>` - Edit existing character
- `/characters/delete/<id>` - Delete/deactivate character

**Features:**
- CRUD operations for characters
- Live preview when creating/editing
- Automatic deactivation if users are using the character
- Glass-style UI matching existing design

### 3. Bot Integration

**User Flow:**
1. User runs `/start`
2. Selects language
3. **NEW**: Chooses AI character with glass buttons
4. Bot stores selection and shows welcome message

**Character Selection:**
- Displays all active characters in 2-column grid
- Shows character name with 🎭 emoji
- After selection, confirms with character details

**Message Handling:**
- Before processing any message, checks if user has selected a character
- If no character: Shows prompt to select one
- If character selected: Passes character's instruction as system prompt to AI
- Logs character usage in activity tracking

**Character Command:**
- `/character` or menu button shows current character
- Allows changing character anytime
- Available in main glass menu

### 4. AI Handler Updates
Modified `generate_text_response()` to accept `system_instruction` parameter:
- Venice AI: Adds system message at start of conversation
- Standard OpenAI: Also supports system messages
- Character instruction sent with every AI request

### 5. Internationalization
Added translations in all 7 languages (en, es, fa, ar, ru, tr, zh):
```json
{
  "character": {
    "select_title": "🎭 Choose Your AI Character",
    "select_subtitle": "Select a character that matches your style:",
    "selected": "✅ You selected: **{name}**\n\n{description}...",
    "change_character": "🎭 Change Character",
    "no_character_selected": "⚠️ **Please select a character first!**...",
    "current_character": "🎭 **Current Character:**\n**{name}**..."
  }
}
```

### 6. Default Characters
Four default characters created on first database initialization:
1. **Friendly Assistant** - Helpful and warm
2. **Professional Expert** - Formal and authoritative
3. **Creative Writer** - Imaginative storyteller
4. **Casual Friend** - Relaxed conversational style

## Database Methods Added

```python
# Character CRUD
db.get_characters(active_only=True)
db.get_character(character_id)
db.create_character(name, description, instruction, is_active)
db.update_character(character_id, ...)
db.delete_character(character_id)

# User-Character relationship
db.set_user_character(user_id, character_id)
db.get_user_character(user_id)
```

## Files Modified

1. **database.py**
   - Added characters table schema
   - Added character_id to users table
   - Created character management methods
   - Added default characters insertion

2. **admin_dashboard.py**
   - Added character routes (list, create, edit, delete)
   - Integrated with existing admin authentication

3. **templates/**
   - `base.html` - Added Characters menu item
   - `characters.html` - Character list view
   - `create_character.html` - Character creation form
   - `edit_character.html` - Character editing form

4. **telegram_bot.py**
   - Modified language selection flow to show character selection
   - Added character selection handler
   - Created character command
   - Added character check in message handling
   - Updated glass menu with character button
   - Added character to menu callback map

5. **ai_handler.py**
   - Updated `generate_text_response()` with system_instruction param
   - Modified Venice and standard OpenAI requests to use system messages

6. **languages/*.json**
   - Added character section to all 7 language files

## Usage

### Admin
1. Go to admin dashboard → Characters
2. Create new characters with custom instructions
3. Edit/deactivate characters as needed
4. Characters with active users can't be deleted (only deactivated)

### Users
1. Start bot and select language
2. Choose preferred character from list
3. All AI responses follow that character's personality
4. Change character anytime via menu or `/character` command
5. Can't send messages without selecting a character

## Technical Notes

- Character instructions are system prompts sent to AI with every request
- Character selection is mandatory before using the bot
- Activity logging tracks which character users interact with
- Glass-style buttons maintain UI consistency
- Full i18n support across all languages
- Database migrations handle existing installations

## Testing Checklist

- [ ] Create character in admin dashboard
- [ ] Edit character instruction
- [ ] Deactivate/activate character
- [ ] New user selects character after language
- [ ] User sends message (uses character instruction)
- [ ] User changes character via menu
- [ ] Attempt to send message without character
- [ ] Check activity logs include character info
- [ ] Test in all supported languages
- [ ] Verify character deleted if users assigned (should deactivate)
