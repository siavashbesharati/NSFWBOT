# Support Button Implementation

## Overview
Added a configurable support button to the packages view that opens a direct Telegram chat with the configured support account.

## Features Implemented

### 1. Database Configuration
- **New Setting**: `support_telegram_username`
  - Default value: empty string
  - Stored in `admin_settings` table
  - Admin can configure via dashboard

### 2. Admin Dashboard Configuration
**Location**: Settings page → Dashboard Settings section

**New Field**:
- Label: "Support Telegram Username"
- Input: Text field with `@` prefix shown
- Placeholder: "yoursupport"
- Help text: "Telegram username for customer support (without @). Users will see a support button in packages view."

**Usage**:
- Admin enters Telegram username (with or without @)
- System automatically strips @ if provided
- Leave empty to hide support button

### 3. Internationalization (i18n)
Added to all 7 language files:
```json
{
  "buttons": {
    "contact_support": "💬 Contact Support"
  }
}
```

Languages updated: en, es, fa, ar, ru, tr, zh

### 4. Bot Integration

**Support Button Display**:
- Shown at bottom of packages list
- Full-width glass-style button
- Opens Telegram chat: `https://t.me/{username}`
- Only shown if support username is configured

**Locations**:
1. `/packages` command response
2. Inline packages view (from dashboard/menu callbacks)

**Button Behavior**:
- Opens native Telegram chat interface
- URL button type (opens in Telegram app)
- Maintains glass-style design consistency

## Implementation Details

### Database
```python
# Default setting
("support_telegram_username", "")

# Usage in code
support_username = self.db.get_setting('support_telegram_username', '')
if support_username:
    support_username = support_username.lstrip('@')  # Clean up
    # Create support button
```

### Admin Dashboard (admin_dashboard.py)
```python
# Read from form
support_telegram_username = request.form.get('support_telegram_username', '')

# Save to database
settings_to_update = {
    ...
    'support_telegram_username': support_telegram_username
}
```

### Bot (telegram_bot.py)
```python
# Add support button to keyboard
support_username = self.db.get_setting('support_telegram_username', '')
if support_username:
    support_username = support_username.lstrip('@')
    keyboard.append([
        InlineKeyboardButton(
            get_text('buttons.contact_support', user_lang),
            url=f"https://t.me/{support_username}"
        )
    ])
```

## Files Modified

1. **database.py**
   - Added `support_telegram_username` to default settings

2. **admin_dashboard.py**
   - Added support username field to settings form processing
   - Added to settings_to_update dictionary

3. **templates/settings.html**
   - Added input field in Dashboard Settings section
   - Input group with @ prefix
   - Help text explaining usage

4. **telegram_bot.py**
   - Added support button to `packages_command()`
   - Added support button to callback query handler for `show_packages`
   - Conditional rendering based on configuration

5. **languages/*.json**
   - Added `contact_support` button translation to all 7 language files

## Usage Guide

### For Admins
1. Go to Admin Dashboard → Settings
2. Scroll to "Dashboard Settings" section
3. Find "Support Telegram Username" field
4. Enter your Telegram username (without @)
   - Example: `mysupport` or `@mysupport` (both work)
5. Save settings
6. Support button will now appear in packages view

### For Users
1. Run `/packages` command
2. See list of available packages
3. See "💬 Contact Support" button at bottom (if configured)
4. Click button to open Telegram chat with support

## Technical Notes

- **URL Sanitization**: System strips @ prefix automatically
- **Conditional Display**: Button only shown if username configured
- **Full-width**: Button spans entire width for better visibility
- **Glass-style**: Matches existing UI design
- **i18n Support**: Button text translated in all languages
- **Telegram Deep Link**: Uses `https://t.me/{username}` format

## Testing Checklist

- [x] Add support username in admin dashboard
- [x] Save settings successfully
- [x] Support button appears in `/packages` command
- [x] Support button appears in inline packages view
- [x] Clicking button opens Telegram chat
- [x] Button hidden when username not configured
- [x] @ prefix handled correctly
- [x] Test in all supported languages
- [x] Glass-style UI consistency maintained

## Future Enhancements (Optional)

1. **Multiple Support Contacts**
   - Add different support contacts for sales, technical, etc.
   
2. **Support Hours Display**
   - Show availability status or hours
   
3. **Auto-reply Message**
   - Configure initial message when user opens chat
   
4. **Support Request Logging**
   - Track when users click support button (analytics)

5. **Support Group**
   - Allow group chat links instead of individual usernames
