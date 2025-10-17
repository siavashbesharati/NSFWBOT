# Character System Implementation

## Overview
The character system lets every user pick an AI persona that defines the bot's tone and behavior. Character metadata now lives entirely in the translation files, keeping localization and personality content in a single place.

## Key Concepts

### Translation-Driven Characters
- Characters are defined under the `characters` section inside each `languages/<code>.json` file.
- Every entry contains:
   - `slug`: Stable identifier stored in the database
   - `name`: Display name (localized)
   - `description`: Short blurb shown to the user (localized)
   - `instruction`: System prompt fed to the AI (authored in English for consistency)
- Example (`languages/en.json`):

```json
"characters": {
   "damon": {
      "slug": "damon",
      "name": "Damon Black",
      "description": "Damon is the reckless bad boy—cocky, daring, and always ready to drag you deeper into the fire.",
      "instruction": "You are Damon Black, the user's dangerous bad boy fantasy..."
   }
}
```

### Database Storage
- Only the selected `character_slug` is stored per user (`users.character_slug`).
- No character tables remain in the database, simplifying migrations and edits.

### Admin Dashboard
- `/characters` now renders a read-only matrix of characters and their translations.
- Create/Edit/Delete routes redirect with guidance to update the JSON files directly.

### Bot Flow
1. User runs `/start` and picks a language.
2. Character choices are pulled from the selected language (defaulting to English if missing).
3. Selected slug is written to the `users` table.
4. For each AI request, the bot loads the English instruction for that slug and passes it as the system prompt.

### AI Handler
- `generate_text_response()` continues to accept `system_instruction`.
- The Telegram bot retrieves the instruction from the translation manager (English fallback) and forwards it unchanged.

## Default Characters
| Slug     | Name         | Persona Snapshot |
|----------|--------------|------------------|
| damon  | Damon Black  | Reckless bad boy with seductive bravado |
| lucy-4  | Lucy Ember   | Magnetic bad girl who owns every interaction |

## Code Touchpoints
- **translations.py**: Provides `get_characters()` and `get_character_by_slug()` helpers that surface localized metadata plus English instructions.
- **telegram_bot.py**: Uses translation manager for selection menus, stores slugs, and injects instructions into AI calls.
- **database.py**: Adds `character_slug` column plus getter/setter helpers.
- **admin_dashboard.py** & `templates/characters.html`: Read-only preview of translation-managed characters.

## Editing Workflow
1. Update every `languages/<code>.json` file with matching `slug` entries.
2. Keep `instruction` authored in English so the AI receives a consistent system prompt.
3. Restart the bot (or reload translations) to pick up changes.

## Testing Checklist
- [ ] Start flow: language selection followed by character selection.
- [ ] Character confirmation message shows localized name/description.
- [ ] Sending text uses the expected system instruction (verify via AI response or logs).
- [ ] `/character` menu reflects stored slug and description.
- [ ] Admin `/characters` view lists both Damon and Lucy across languages.
- [ ] Updating a translation file changes the bot output after reload.
