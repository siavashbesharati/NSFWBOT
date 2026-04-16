# Referral System Documentation

## Overview

The referral system allows users to earn free messages by inviting friends to use the bot. Both the referrer and the new user receive message credits when a successful referral occurs.

## Features

### 🎯 Core Functionality
- **Unique Referral Codes**: Each user gets a unique 8-character alphanumeric referral code
- **Automatic Processing**: Referrals are processed automatically when new users join with a referral link
- **Manual Code Entry**: Users can also enter referral codes manually using the `/enterreferral` command
- **Duplicate Prevention**: Each user can only be referred once
- **Reward Distribution**: Both referrer and referee receive the same rewards

### 🎁 Rewards System
- **Text Messages**: Configurable number of text message credits
- **Image Messages**: Configurable number of image generation credits  
- **Video Messages**: Configurable number of video generation credits
- **Equal Rewards**: Both parties receive the same amount of credits

### 🔧 Admin Configuration
Administrators can configure the referral system through the admin dashboard at `/settings`:

- **Enable/Disable**: Toggle the entire referral system on/off
- **Text Message Reward**: Number of text messages both users receive (default: 3)
- **Image Message Reward**: Number of image generations both users receive (default: 1)
- **Video Message Reward**: Number of video generations both users receive (default: 1)

## How It Works

### For Users

#### Getting Your Referral Link
1. Send `/referral` to the bot
2. Bot will show your unique referral link and code
3. Share the link with friends

#### Using a Referral Code
**Method 1: Referral Link (Recommended)**
1. Friend clicks your referral link
2. Starts the bot with your code automatically
3. Rewards are applied immediately

**Method 2: Manual Code Entry**
1. Friend starts the bot normally with `/start`
2. Friend uses `/enterreferral YOUR_CODE` command
3. Rewards are applied if valid

#### Checking Referral Stats
- Use `/referral` to see your referral code, link, and statistics
- View successful referrals and earned rewards

### For Administrators

#### Database Tables
The system creates two new tables:

**`referrals`**
- Tracks all referral relationships
- Stores reward amounts and completion status
- Ensures one-time referral per user

**`user_referral_codes`**
- Maps users to their unique referral codes
- Tracks referral statistics per user

#### Admin Dashboard Features
- **Settings Configuration**: Adjust reward amounts and enable/disable system
- **User Details**: View referral information for each user
- **Statistics Tracking**: Monitor referral success rates

## Bot Commands

### User Commands
- `/referral` - Get your referral link and view statistics
- `/enterreferral CODE` - Enter a referral code manually
- `/start CODE` - Start bot with referral code (automatic)

### Bot Responses
The bot provides helpful feedback for:
- ✅ Successful referral applications
- ❌ Invalid or expired codes
- ℹ️ Already referred users
- 🚫 Disabled referral system

## Technical Implementation

### Database Schema

```sql
-- Referrals tracking table
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referee_id INTEGER NOT NULL,
    referral_code TEXT,
    status TEXT DEFAULT 'pending',
    text_reward INTEGER DEFAULT 0,
    image_reward INTEGER DEFAULT 0,
    video_reward INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    UNIQUE(referee_id) -- Each user can only be referred once
);

-- User referral codes table
CREATE TABLE user_referral_codes (
    user_id INTEGER PRIMARY KEY,
    referral_code TEXT UNIQUE NOT NULL,
    total_referrals INTEGER DEFAULT 0,
    successful_referrals INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Methods

#### Database Methods
- `generate_referral_code(user_id)` - Creates unique referral code
- `validate_referral_code(code)` - Checks if code exists and is valid
- `process_referral(referee_id, code)` - Applies referral and awards credits
- `get_user_referrals(user_id)` - Gets referral statistics for user

#### Bot Methods
- `start_command()` - Modified to handle referral codes in arguments
- `referral_command()` - Shows user's referral information
- `enter_referral_command()` - Allows manual code entry

## Configuration Settings

### Admin Settings (Database)
- `referral_system_enabled`: "true"/"false" - Enable/disable system
- `referral_text_reward`: Number (default: 3) - Text message rewards
- `referral_image_reward`: Number (default: 1) - Image message rewards  
- `referral_video_reward`: Number (default: 1) - Video message rewards

### Default Values
```python
{
    "referral_system_enabled": "true",
    "referral_text_reward": "3",
    "referral_image_reward": "1", 
    "referral_video_reward": "1"
}
```

## Security Features

### Validation & Prevention
- **Unique Codes**: 8-character alphanumeric codes prevent conflicts
- **One-Time Use**: Each user can only be referred once
- **Self-Referral Prevention**: Users cannot refer themselves
- **Database Constraints**: UNIQUE constraints prevent duplicate referrals
- **Input Validation**: Codes are validated before processing

### Error Handling
- Invalid codes return user-friendly error messages
- Database errors are logged and handled gracefully
- Failed referrals don't affect user experience

## Usage Examples

### Typical User Flow
1. **User A** joins bot, gets 5 free messages
2. **User A** runs `/referral` → gets code "ABC12345"
3. **User A** shares link: `https://t.me/yourbot?start=ABC12345`
4. **User B** clicks link → automatically starts with `/start ABC12345`
5. **Both users** receive 3 text + 1 image + 1 video messages
6. **User A** can check stats with `/referral`

### Manual Code Entry Flow
1. **User B** joins bot normally with `/start`
2. **User A** shares code: "ABC12345"
3. **User B** runs `/enterreferral ABC12345`
4. **Both users** receive referral rewards

## Monitoring & Analytics

### Admin Dashboard
- View referral statistics per user
- Monitor system-wide referral success rates
- Track reward distribution
- User detail pages show referral information

### Database Queries
```sql
-- Top referrers
SELECT u.username, urc.successful_referrals 
FROM user_referral_codes urc
JOIN users u ON urc.user_id = u.user_id
ORDER BY urc.successful_referrals DESC;

-- Recent referrals
SELECT r.*, u1.username as referrer, u2.username as referee
FROM referrals r
JOIN users u1 ON r.referrer_id = u1.user_id
JOIN users u2 ON r.referee_id = u2.user_id
ORDER BY r.completed_date DESC;
```

## Testing

The system includes a comprehensive test suite (`test_referral_system.py`) that validates:
- ✅ Referral code generation
- ✅ Code validation
- ✅ Referral processing
- ✅ Credit distribution
- ✅ Duplicate prevention
- ✅ Error handling

Run tests with: `python test_referral_system.py`

## Troubleshooting

### Common Issues

**Referral not working**
- Check if referral system is enabled in admin settings
- Verify referral code is valid
- Ensure user hasn't been referred before

**Credits not added**
- Check database for referral record
- Verify settings for reward amounts
- Check user's current credit balance

**Invalid code errors**
- Ensure code is entered correctly (case-insensitive)
- Check if code exists in database
- Verify bot has database access

### Logging
All referral operations are logged for debugging:
- Successful referrals
- Failed attempts
- Database errors
- Invalid code attempts

## Future Enhancements

### Potential Features
- **Referral Tiers**: Different rewards based on referrer level
- **Time-Limited Codes**: Expiring referral codes
- **Referral Contests**: Leaderboards and competitions
- **Custom Rewards**: Different rewards for different user types
- **Referral Analytics**: Detailed tracking and reporting
- **Bulk Operations**: Admin tools for bulk referral management