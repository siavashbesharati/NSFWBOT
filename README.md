# 🤖 Advanced Telegram AI Bot

A comprehensive Telegram bot with AI responses, payment processing, and admin dashboard.

## ✨ Features

### 🤖 AI Integration
- **Venice API**: AI responses through Venice chat completions
- **Dynamic Model Selection**: Admin can choose from 100+ available models
- **Multi-modal Support**: Text, image, and video processing
- **Configurable Responses**: Customizable AI behavior and prompts

### 💳 Payment System
- **TON Cryptocurrency**: Accept payments via TON blockchain
- **Telegram Stars**: Native Telegram payment integration
- **Package System**: Flexible credit-based packages
- **Simulation Mode**: Test payments without real transactions

### 📊 Admin Dashboard
- **Real-time Analytics**: User statistics, revenue tracking
- **Payment Management**: Transaction history and revenue breakdown
- **User Management**: View and manage bot users
- **Package Management**: Create and modify service packages
- **Settings Configuration**: Bot configuration and API settings

### 🔒 Security & Reliability
- **Environment Variables**: Secure configuration management
- **Database Persistence**: SQLite database for data storage
- **Error Handling**: Comprehensive error logging and recovery
- **Input Validation**: Secure handling of user inputs

### 🛠 Admin Features
- **Web Dashboard**: Manage users, packages, and settings
- **User Analytics**: View user statistics and usage patterns
- **Package Management**: Create and edit message packages
- **Payment Tracking**: Monitor transactions and revenue
- **Bot Control**: Start/stop bot, toggle simulation mode
- **Real-time Stats**: Live dashboard with auto-refreshing data

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Venice Inference Key (from venice.ai)

### 2. Installation

```bash
# Clone or download the project
cd NSFWBOT

# Install dependencies
pip install -r requirements.txt

# Setup configuration
python config_manager.py --setup
```

### 3. Configuration

Run the interactive setup:
```bash
python config_manager.py --setup
```

Or manually copy `env_example.txt` to `.env` and edit:
```bash
copy env_example.txt .env
# Edit .env with your settings
```

### 4. Start the Bot

```bash
# Start everything (bot + admin dashboard)
python start_bot.py start

# Or start components separately
python start_bot.py bot-only
python start_bot.py dashboard-only
```

### 5. Access Admin Dashboard

Open http://127.0.0.1:5000 in your browser
- Default login: `admin` / `admin123`

## 🚂 Deploy on Railway (Step-by-Step)

### 1. Prepare repository
1. Push this project to GitHub.
2. Make sure these files are present in root:
   - `Dockerfile`
   - `Procfile`
   - `requirements.txt`
   - `start_bot.py`

### 2. Create Railway project
1. Go to [railway.app](https://railway.app/) and sign in.
2. Click **New Project**.
3. Choose **Deploy from GitHub repo**.
4. Select your repository.

### 3. Configure service variables
In Railway, open your service and set these environment variables:

```env
BOT_TOKEN=your_telegram_bot_token
VENICE_INFERENCE_KEY=your_venice_inference_key
AI_API_KEY=your_venice_inference_key
AI_MODEL=venice-uncensored
AI_BASE_URL=https://api.venice.ai/api/v1
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me
SECRET_KEY=change_me_to_a_random_secret
DATABASE_PATH=/app/data/bot_database.db
```

Notes:
- Railway automatically provides `PORT`; the app now binds to it automatically.
- `AI_API_KEY` is kept for compatibility with existing DB settings.

### 4. Configure start command
- If Railway detects `Procfile`, no extra command is needed.
- Manual start command (if needed): `python start_bot.py start`

### 5. Add persistent storage (recommended)
1. Add a Railway volume and mount it to `/app/data`.
2. Keep `DATABASE_PATH=/app/data/bot_database.db`.

Without a volume, SQLite data may be lost after redeploy/restart.

### 6. Deploy
1. Trigger a deploy from Railway dashboard (or push a commit).
2. Wait for logs to show:
   - Telegram bot started
   - Admin dashboard started

### 7. Open dashboard
1. Copy your Railway service URL.
2. Open it in browser.
3. Log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

### 8. Verify Telegram bot
1. Open Telegram and send `/start` to your bot.
2. Confirm it replies.
3. In dashboard, check users/messages are updating.

### 9. Optional: production hardening
- Change default admin credentials.
- Use a strong `SECRET_KEY`.
- Disable simulation mode in dashboard.
- Consider migrating from SQLite to Postgres for higher reliability.

## 🧰 Building a Standalone Executable

1. (Optional) Activate your virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the build script: `pwsh scripts/build_executable.ps1`.
4. Collect the packaged bot from `dist/NSFWBot.exe`.

Notes:
- The script installs PyInstaller automatically if it is missing.
- The database (`bot_database.db` by default) lives next to the executable; set `DATABASE_PATH` to move it elsewhere.
- Re-run the script whenever project code or assets change to refresh the executable.

## 📖 Detailed Setup Guide

### Step 1: Get Telegram Bot Token

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the bot token

### Step 2: Get Venice Inference Key

1. Go to https://venice.ai/
2. Sign up for an account
3. Navigate to API keys / inference keys
4. Create a new inference key
5. Copy the key

### Step 3: Configuration Options

#### Required Settings
```env
BOT_TOKEN=your_bot_token_here
VENICE_INFERENCE_KEY=your_venice_inference_key_here
```

#### Payment Settings (Optional)
```env
TON_WALLET_ADDRESS=your_ton_wallet_address
TELEGRAM_STARS_ENABLED=true
TON_ENABLED=true
```

#### Admin Dashboard
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_password
SECRET_KEY=your-secret-key-here
```

#### Bot Behavior
```env
SIMULATION_MODE=false
FREE_MESSAGES=1
DEFAULT_TEXT_PRICE=1
DEFAULT_IMAGE_PRICE=2
DEFAULT_VIDEO_PRICE=3
```

## 💰 Package Management

### Creating Packages

Packages define what users can purchase:

```python
# Example package
{
    "name": "Starter Pack",
    "description": "Perfect for beginners",
    "text_count": 10,     # Number of text messages
    "image_count": 2,     # Number of image generations
    "video_count": 1,     # Number of video messages
    "price_ton": 0.5,     # Price in TON
    "price_stars": 50     # Price in Telegram Stars
}
```

### Default Packages

The system comes with 4 default packages:
1. **Starter Pack**: 10 text, 2 images, 1 video
2. **Standard Pack**: 25 text, 5 images, 3 videos
3. **Premium Pack**: 50 text, 15 images, 10 videos
4. **Ultimate Pack**: 100 text, 30 images, 20 videos

## 🎮 User Experience

### User Flow
1. User starts bot with `/start`
2. Gets 1 free message
3. After free message, sees package options
4. Selects payment method (TON or Stars)
5. Completes payment
6. Gets credits added to account
7. Can check usage with `/dashboard`

### Bot Commands
- `/start` - Start the bot and see welcome message
- `/help` - Show help information
- `/dashboard` - View remaining credits
- `/packages` - View available packages
- `/support` - Contact support

## 🔧 Admin Dashboard Guide

### Dashboard Sections

#### 1. Overview Dashboard
- Total users, transactions, revenue
- Recent user activity
- Quick actions (start/stop bot, toggle simulation)
- System status indicators

#### 2. User Management
- View all users with pagination
- Search users by name/ID
- View individual user details
- Track user usage patterns

#### 3. Package Management
- Create new packages
- Edit existing packages
- Enable/disable packages
- Real-time package preview

#### 4. Transaction Monitoring
- View all payments
- Filter by status (completed, pending, failed)
- Transaction details with payment hashes
- Revenue analytics

#### 5. Settings
- Bot configuration
- AI model selection
- Payment settings
- Advanced options

### Quick Actions
- **Start/Stop Bot**: Control bot operation
- **Simulation Mode**: Toggle test mode
- **Create Package**: Quick package creation
- **View Stats**: Real-time statistics

## 🧪 Testing & Development

### Simulation Mode

Enable simulation mode for testing:
```env
SIMULATION_MODE=true
```

In simulation mode:
- Payments are automatically approved after 5 seconds
- No real money is charged
- All features work normally
- Perfect for development and testing

### Testing Payments

1. Enable simulation mode
2. Create test packages with low prices
3. Use the bot to test the complete flow
4. Check admin dashboard for transaction records

### Development Commands

```bash
# Validate configuration
python start_bot.py --config

# Check service status
python start_bot.py status

# Start individual services
python start_bot.py bot-only
python start_bot.py dashboard-only

# Configuration management
python config_manager.py --show
python config_manager.py --validate
python config_manager.py --set KEY VALUE
```

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Passwords**
   ```env
   ADMIN_PASSWORD=strong_password_here
   SECRET_KEY=random_secret_key_here
   ```

2. **Use HTTPS**
   - Deploy behind a reverse proxy (nginx)
   - Enable SSL/TLS certificates

3. **Secure Database**
   - Regular backups
   - Proper file permissions
   - Consider encrypted database

4. **Environment Variables**
   - Never commit `.env` file
   - Use secure hosting environment variables

### Rate Limiting

The bot includes built-in rate limiting:
```env
MAX_REQUESTS_PER_MINUTE=20
MAX_REQUESTS_PER_HOUR=100
```

## 📁 Project Structure

```
NSFWBOT/
├── 📄 telegram_bot.py         # Main bot logic
├── 📄 ai_handler.py           # AI response handling
├── 📄 payment_handler.py      # Payment processing
├── 📄 database.py             # Database operations
├── 📄 config.py               # Configuration management
├── 📄 admin_dashboard.py      # Web admin interface
├── 📄 start_bot.py            # Startup script
├── 📄 config_manager.py       # Config utility
├── 📄 requirements.txt        # Python dependencies
├── 📄 env_example.txt         # Environment template
├── 📁 templates/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── packages.html
│   ├── settings.html
│   └── users.html
└── 📁 static/                # Static files (CSS, JS)
```

## 🛠 Available AI Models

| Model | Provider | Speed | Cost | Use Case |
|-------|----------|-------|------|----------|
| gpt-3.5-turbo | OpenAI | Fast | Low | General use |
| gpt-4 | OpenAI | Medium | High | Best quality |
| claude-3-haiku | Anthropic | Fast | Low | Quick responses |
| claude-3-sonnet | Anthropic | Medium | Medium | Balanced |
| gemini-pro | Google | Fast | Low | Alternative |
| mistral-7b | Mistral | Fast | Very Low | Open source |

## 🐛 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check bot status
python start_bot.py status

# Validate configuration
python start_bot.py --config

# Check logs
tail -f bot.log
```

#### Database Errors
```bash
# Reinitialize database
rm bot_database.db
python start_bot.py start
```

#### Payment Issues
1. Check simulation mode setting
2. Verify TON wallet address
3. Check Telegram Stars configuration
4. Review payment webhook setup

#### Admin Dashboard Not Loading
1. Check if port 5000 is available
2. Verify admin credentials
3. Check Flask secret key
4. Review firewall settings

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### Support

If you encounter issues:
1. Check the logs (`bot.log`)
2. Validate configuration
3. Test in simulation mode
4. Review the troubleshooting section

## 📊 Performance & Scaling

### Database Optimization
- Regular VACUUM operations
- Index optimization for large datasets
- Consider PostgreSQL for high traffic

### Rate Limiting
- Built-in request limiting
- Configurable limits per user
- Automatic cooldown periods

### Monitoring
- Real-time dashboard metrics
- Transaction monitoring
- User activity tracking
- Error logging and alerts

## 🔄 Updates & Maintenance

### Regular Tasks
1. **Database Backup**
   ```bash
   cp bot_database.db backup_$(date +%Y%m%d).db
   ```

2. **Log Rotation**
   ```bash
   # Archive old logs
   mv bot.log bot.log.old
   ```

3. **Dependency Updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

### Version Control
- Keep `.env` out of version control
- Regular code backups
- Test updates in simulation mode

## 📄 License & Credits

This project is created for educational and commercial use. Make sure to:
- Comply with Telegram's Terms of Service
- Follow Venice's usage guidelines
- Respect user privacy and data protection laws
- Implement proper security measures for production use

---

**Made with ❤️ for the Telegram community**

For support and updates, check the project documentation and admin dashboard.