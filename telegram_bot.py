import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import io
import os

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    LabeledPrice, PreCheckoutQuery, InputFile, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, filters, ContextTypes
)

from database import Database
from ai_handler import OpenRouterAPI
from payment_handler import PaymentHandler
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.db = Database()
        self.ai_handler = OpenRouterAPI(database=self.db)
        self.payment_handler = PaymentHandler(self.db)
        self.app = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Create or update user in database
        self.db.create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get free message settings from database
        free_settings = self.db.get_free_message_settings()
        
        welcome_message = f"""
🤖 Welcome to the AI Bot, {user.first_name}!

I can help you with:
📝 Text conversations
🖼️ Image analysis
🎥 Video responses

🎁 Free Messages for new users:
📝 Text: {free_settings['free_text_messages']} messages
🖼️ Images: {free_settings['free_image_messages']} generations
🎥 Videos: {free_settings['free_video_messages']} generations

After using your free messages, you'll need to purchase a package to continue.

Use /packages to see available packages
Use /dashboard to check your usage
Use /help for more commands
        """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 Bot Commands:

🍔 **Use the Menu Button** next to the text input for quick access to all commands!

/start - 🚀 Start the bot
/help - ℹ️ Show this help message  
/dashboard - 📊 Check your usage stats
/packages - 💎 View available packages
/balance - 💰 Check your remaining credits
/reset - 🔄 Reset conversation history
/testapi - 🧪 Test AI API connection (Admin only)

💬 Message Types:
- Send text for AI conversation
- Send images for AI analysis  
- Send videos for AI response

💳 Payment Methods:
- Telegram Stars ⭐
- TON Coin 💎

📊 All message types are tracked for usage
        """
        
        await update.message.reply_text(help_text)
    
    async def test_api_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /testapi command - Test AI API connection"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        admin_chat_id = self.db.get_setting('admin_chat_id', '0')
        try:
            admin_id = int(admin_chat_id) if admin_chat_id else 0
        except ValueError:
            admin_id = 0
            
        if user_id != admin_id or admin_id == 0:
            await update.message.reply_text("❌ This command is only available for administrators. Please set your Telegram User ID in the admin dashboard.")
            return
        
        await update.message.reply_text("🧪 Testing AI API connection...")
        
        try:
            # Test the API
            is_working = await self.ai_handler.test_api_connection()
            
            if is_working:
                await update.message.reply_text("✅ AI API test successful! The connection is working properly.")
            else:
                await update.message.reply_text("❌ AI API test failed! Please check your API configuration in the admin dashboard.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error testing API: {str(e)}")
    
    async def venice_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /venicestatus command - Check Venice API status and account balance"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        admin_chat_id = self.db.get_setting('admin_chat_id', '0')
        try:
            admin_id = int(admin_chat_id) if admin_chat_id else 0
        except ValueError:
            admin_id = 0
            
        if user_id != admin_id or admin_id == 0:
            await update.message.reply_text("❌ This command is only available for administrators.")
            return
        
        await update.message.reply_text("📊 Checking Venice API status...")
        
        try:
            # Get Venice status
            status = await self.ai_handler.get_venice_account_status()
            formatted_status = self.ai_handler.format_venice_status(status)
            
            await update.message.reply_text(formatted_status, parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking Venice status: {str(e)}")
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command - clear conversation history"""
        try:
            user_id = update.effective_user.id
            
            # Clear conversation history for this user
            self.db.clear_conversation_history(user_id)
            
            reset_message = """
🔄 **Conversation Reset Complete!**

Your conversation history has been cleared. The AI will start fresh with no memory of previous messages.

You can now start a new conversation from scratch! 🚀
            """
            
            await update.message.reply_text(reset_message, parse_mode='Markdown')
            
        except Exception as e:
            print(f"Error in reset command: {str(e)}")
            await update.message.reply_text("Sorry, there was an error resetting your conversation. Please try again later.")
    
    async def packages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available packages"""
        packages = self.db.get_packages()
        
        if not packages:
            await update.message.reply_text("No packages available at the moment.")
            return
        
        keyboard = []
        message_text = "📦 Available Packages:\n\n"
        
        for package in packages:
            package_text = (
                f"🏷️ **{package['name']}**\n"
                f"📝 {package['text_count']} text messages\n"
                f"🖼️ {package['image_count']} image messages\n"
                f"🎥 {package['video_count']} video messages\n"
            )
            
            # Get payment settings from database
            telegram_stars_enabled = self.db.get_setting('telegram_stars_enabled', 'true') == 'true'
            ton_enabled = self.db.get_setting('ton_enabled', 'true') == 'true'
            
            if telegram_stars_enabled:
                package_text += f"⭐ {package['price_stars']} Stars"
            
            if ton_enabled:
                if telegram_stars_enabled:
                    package_text += f" or 💎 {package['price_ton']} TON"
                else:
                    package_text += f"💎 {package['price_ton']} TON"
            
            message_text += package_text + "\n\n"
            
            # Create payment buttons
            row = []
            if telegram_stars_enabled:
                row.append(InlineKeyboardButton(
                    f"⭐ Buy with Stars ({package['price_stars']})",
                    callback_data=f"buy_stars_{package['id']}"
                ))
            
            if ton_enabled:
                row.append(InlineKeyboardButton(
                    f"💎 Buy with TON ({package['price_ton']})",
                    callback_data=f"buy_ton_{package['id']}"
                ))
            
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user dashboard"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        # Get free message settings from database
        free_settings = self.db.get_free_message_settings()
        
        # Calculate remaining free messages for each type
        free_text_left = max(0, free_settings['free_text_messages'] - user_data.get('free_text_messages_used', 0))
        free_image_left = max(0, free_settings['free_image_messages'] - user_data.get('free_image_messages_used', 0))
        free_video_left = max(0, free_settings['free_video_messages'] - user_data.get('free_video_messages_used', 0))
        
        dashboard_text = f"""
📊 Your Dashboard

👤 User: {user_data['first_name']} {user_data['last_name'] or ''}
📅 Member since: {user_data['registration_date'][:10]}

🎁 Free Messages Remaining:
📝 Text: {free_text_left}/{free_settings['free_text_messages']}
🖼️ Images: {free_image_left}/{free_settings['free_image_messages']}
🎥 Videos: {free_video_left}/{free_settings['free_video_messages']}

💬 Paid Credits:
📝 Text: {user_data['text_messages_left']}
🖼️ Images: {user_data['image_messages_left']}
🎥 Videos: {user_data['video_messages_left']}

💰 Total Spent: ${user_data['total_spent']:.2f}
        """
        
        keyboard = [
            [InlineKeyboardButton("📦 Buy Packages", callback_data="show_packages")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_dashboard")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(dashboard_text, reply_markup=reply_markup)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user balance"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("Please start the bot first with /start")
            return
        
        # Get free message settings from database
        free_settings = self.db.get_free_message_settings()
        
        # Calculate remaining free messages for each type
        free_text_left = max(0, free_settings['free_text_messages'] - user_data.get('free_text_messages_used', 0))
        free_image_left = max(0, free_settings['free_image_messages'] - user_data.get('free_image_messages_used', 0))
        free_video_left = max(0, free_settings['free_video_messages'] - user_data.get('free_video_messages_used', 0))
        
        balance_text = f"""
💳 Your Balance

🎁 Free Messages:
📝 Text: {free_text_left} remaining
🖼️ Images: {free_image_left} remaining
🎥 Videos: {free_video_left} remaining

💬 Paid Credits:
📝 Text Messages: {user_data['text_messages_left']}
🖼️ Image Messages: {user_data['image_messages_left']}
🎥 Video Messages: {user_data['video_messages_left']}

Use /packages to buy more credits!
        """
        
        await update.message.reply_text(balance_text)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text("🚫 Bot is currently offline. Please try again later.")
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'text'):
            await update.message.reply_text(
                "❌ You don't have enough text message credits!\n\n"
                "Use /packages to buy more credits."
            )
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Check if conversation memory is enabled
            memory_enabled = self.db.get_setting('enable_conversation_memory', 'true') == 'true'
            conversation_history = []
            
            if memory_enabled:
                # Get configurable conversation history length
                history_length = int(self.db.get_setting('conversation_history_length', '10'))
                conversation_history = self.db.get_conversation_history(user_id, limit=history_length)
            
            # Generate AI response with context
            ai_response = await self.ai_handler.generate_text_response(
                user_message, 
                conversation_history=conversation_history
            )
            
            # Save to message history with AI model info
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'text', 
                user_message, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history)
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling text message: {str(e)}")
            await update.message.reply_text("Sorry, I encountered an error. Please try again.")
    
    async def handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages"""
        user_id = update.effective_user.id
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text("🚫 Bot is currently offline. Please try again later.")
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'image'):
            await update.message.reply_text(
                "❌ You don't have enough image message credits!\n\n"
                "Use /packages to buy more credits."
            )
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get the largest photo
            photo = update.message.photo[-1]
            
            # Download the image
            file = await context.bot.get_file(photo.file_id)
            image_data = await file.download_as_bytearray()
            
            # Get caption if any
            caption = update.message.caption or "What do you see in this image?"
            
            # Check if conversation memory is enabled
            memory_enabled = self.db.get_setting('enable_conversation_memory', 'true') == 'true'
            conversation_history = []
            
            if memory_enabled:
                # Get configurable conversation history length
                history_length = int(self.db.get_setting('conversation_history_length', '10'))
                conversation_history = self.db.get_conversation_history(user_id, limit=history_length)
            
            # Generate AI response with context
            ai_response = await self.ai_handler.generate_image_response(
                caption, 
                bytes(image_data),
                conversation_history=conversation_history
            )
            
            # Save to message history with AI model info
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'image', 
                caption, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history)
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling image message: {str(e)}")
            await update.message.reply_text("Sorry, I encountered an error processing your image. Please try again.")
    
    async def handle_video_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user_id = update.effective_user.id
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text("🚫 Bot is currently offline. Please try again later.")
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'video'):
            await update.message.reply_text(
                "❌ You don't have enough video message credits!\n\n"
                "Use /packages to buy more credits."
            )
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get caption if any
            caption = update.message.caption or "User sent a video"
            
            # Check if conversation memory is enabled
            memory_enabled = self.db.get_setting('enable_conversation_memory', 'true') == 'true'
            conversation_history = []
            
            if memory_enabled:
                # Get configurable conversation history length
                history_length = int(self.db.get_setting('conversation_history_length', '10'))
                conversation_history = self.db.get_conversation_history(user_id, limit=history_length)
            
            # Generate AI response with context
            ai_response = await self.ai_handler.generate_video_response(
                caption,
                conversation_history=conversation_history
            )
            
            # Save to message history with AI model info
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'video', 
                caption, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history)
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling video message: {str(e)}")
            await update.message.reply_text("Sorry, I encountered an error processing your video. Please try again.")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        if data.startswith("buy_stars_"):
            package_id = int(data.split("_")[2])
            await self.handle_stars_purchase(query, package_id)
        
        elif data.startswith("buy_ton_"):
            package_id = int(data.split("_")[2])
            await self.handle_ton_purchase(query, package_id)
        
        elif data == "show_packages":
            packages = self.db.get_packages()
            keyboard = []
            
            for package in packages:
                row = []
                if Config.TELEGRAM_STARS_ENABLED:
                    row.append(InlineKeyboardButton(
                        f"⭐ {package['name']} ({package['price_stars']} Stars)",
                        callback_data=f"buy_stars_{package['id']}"
                    ))
                
                if Config.TON_ENABLED:
                    row.append(InlineKeyboardButton(
                        f"💎 {package['name']} ({package['price_ton']} TON)",
                        callback_data=f"buy_ton_{package['id']}"
                    ))
                
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📦 Select a package:", reply_markup=reply_markup)
        
        elif data == "refresh_dashboard":
            # Refresh dashboard
            await self.dashboard_command(update, context)
    
    async def handle_stars_purchase(self, query, package_id: int):
        """Handle Telegram Stars purchase"""
        package = self.db.get_package(package_id)
        if not package:
            await query.edit_message_text("❌ Package not found.")
            return
        
        user_id = query.from_user.id
        amount = package['price_stars']
        
        result = await self.payment_handler.create_stars_payment(user_id, package_id, amount)
        
        if result['success']:
            # Get simulation mode from database
            simulation_mode = self.db.get_setting('simulation_mode', 'false') == 'true'
            
            if simulation_mode:
                await query.edit_message_text(result['message'])
            else:
                # Create invoice for real payment
                title = f"Package: {package['name']}"
                description = f"{package['description']}\n📝 {package['text_count']} text\n🖼️ {package['image_count']} images\n🎥 {package['video_count']} videos"
                
                prices = [LabeledPrice(package['name'], amount)]
                
                await query.message.reply_invoice(
                    title=title,
                    description=description,
                    payload=str(result['transaction_id']),
                    provider_token="",  # Empty for Telegram Stars
                    currency="XTR",
                    prices=prices
                )
        else:
            await query.edit_message_text(f"❌ {result['error']}")
    
    async def handle_ton_purchase(self, query, package_id: int):
        """Handle TON purchase"""
        package = self.db.get_package(package_id)
        if not package:
            await query.edit_message_text("❌ Package not found.")
            return
        
        user_id = query.from_user.id
        amount = package['price_ton']
        
        result = await self.payment_handler.create_ton_payment(user_id, package_id, amount)
        
        if result['success']:
            # Get simulation mode from database
            simulation_mode = self.db.get_setting('simulation_mode', 'false') == 'true'
            
            if simulation_mode:
                await query.edit_message_text(result['message'])
            else:
                message = f"""
💎 TON Payment Instructions

📦 Package: {package['name']}
💰 Amount: {amount} TON
🏦 Address: `{result['ton_address']}`
💬 Comment: `{result['comment']}`

📱 Quick Payment:
[Open in Tonkeeper]({result['payment_url']})

⏰ Your payment will be verified automatically within a few minutes.
                """
                
                keyboard = [[
                    InlineKeyboardButton("🔗 Pay with Tonkeeper", url=result['payment_url'])
                ]]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ {result['error']}")
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful Telegram Stars payment"""
        payment = update.message.successful_payment
        transaction_id = int(payment.invoice_payload)
        
        # Verify and complete payment
        success = await self.payment_handler.verify_stars_payment(
            transaction_id, 
            payment.telegram_payment_charge_id
        )
        
        if success:
            await update.message.reply_text(
                "✅ Payment successful! Your credits have been added to your account.\n\n"
                "Use /dashboard to check your updated balance."
            )
        else:
            await update.message.reply_text(
                "❌ Payment verification failed. Please contact support."
            )
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pre-checkout query for Telegram Stars"""
        query = update.pre_checkout_query
        
        # Always approve in this example
        await query.answer(ok=True)
    
    async def setup_bot_menu(self, application):
        """Set up the bot's hamburger menu with commands"""
        try:
            commands = [
                BotCommand("start", "🚀 Start the bot and get welcome message"),
                BotCommand("help", "ℹ️ Show available commands and help"),
                BotCommand("dashboard", "📊 View your usage dashboard"),
                BotCommand("packages", "💎 Browse message packages"),
                BotCommand("balance", "💰 Check your message balance"),
                BotCommand("reset", "🔄 Reset conversation history"),
                BotCommand("testapi", "🧪 Test AI connection (admin only)"),
                BotCommand("venicestatus", "📊 Check Venice API status (admin only)")
            ]
            
            await application.bot.set_my_commands(commands)
            logger.info(f"✅ Bot menu set up with {len(commands)} commands")
            
        except Exception as e:
            logger.error(f"❌ Failed to set up bot menu: {str(e)}")
    
    def run(self):
        """Run the bot"""
        try:
            # Validate configuration
            Config.validate_config()
            
            # Get bot token from database or config
            bot_token = self.db.get_setting('bot_token', Config.BOT_TOKEN)
            
            # Create application
            self.app = Application.builder().token(bot_token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            self.app.add_handler(CommandHandler("reset", self.reset_command))
            self.app.add_handler(CommandHandler("testapi", self.test_api_command))
            self.app.add_handler(CommandHandler("venicestatus", self.venice_status_command))
            self.app.add_handler(CommandHandler("packages", self.packages_command))
            self.app.add_handler(CommandHandler("dashboard", self.dashboard_command))
            self.app.add_handler(CommandHandler("balance", self.balance_command))
            
            # Message handlers
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
            self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_image_message))
            self.app.add_handler(MessageHandler(filters.VIDEO, self.handle_video_message))
            
            # Payment handlers
            self.app.add_handler(PreCheckoutQueryHandler(self.handle_pre_checkout_query))
            self.app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.handle_successful_payment))
            
            # Callback query handler
            self.app.add_handler(CallbackQueryHandler(self.handle_callback_query))
            
            # Set up bot menu after initialization
            self.app.post_init = self.setup_bot_menu
            
            logger.info("Bot starting...")
            
            # Run the bot
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()