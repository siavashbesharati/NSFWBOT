import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import io
import os

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    LabeledPrice, PreCheckoutQuery, InputFile
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
        self.ai_handler = OpenRouterAPI()
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

/start - Start the bot
/help - Show this help message
/packages - View available packages
/dashboard - Check your usage stats
/balance - Check your remaining credits

💬 Message Types:
- Send text for AI conversation
- Send images for AI analysis
- Send videos for AI response

💳 Payment:
- Telegram Stars ⭐
- TON Coin 💎

📊 Usage tracking for all message types
        """
        
        await update.message.reply_text(help_text)
    
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
            
            if Config.TELEGRAM_STARS_ENABLED:
                package_text += f"⭐ {package['price_stars']} Stars"
            
            if Config.TON_ENABLED:
                if Config.TELEGRAM_STARS_ENABLED:
                    package_text += f" or 💎 {package['price_ton']} TON"
                else:
                    package_text += f"💎 {package['price_ton']} TON"
            
            message_text += package_text + "\n\n"
            
            # Create payment buttons
            row = []
            if Config.TELEGRAM_STARS_ENABLED:
                row.append(InlineKeyboardButton(
                    f"⭐ Buy with Stars ({package['price_stars']})",
                    callback_data=f"buy_stars_{package['id']}"
                ))
            
            if Config.TON_ENABLED:
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
            # Generate AI response
            ai_response = await self.ai_handler.generate_text_response(user_message)
            
            # Save to message history
            self.db.add_message_history(user_id, 'text', user_message, ai_response)
            
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
            
            # Generate AI response
            ai_response = await self.ai_handler.generate_image_response(caption, bytes(image_data))
            
            # Save to message history
            self.db.add_message_history(user_id, 'image', caption, ai_response)
            
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
            
            # Generate AI response
            ai_response = await self.ai_handler.generate_video_response(caption)
            
            # Save to message history
            self.db.add_message_history(user_id, 'video', caption, ai_response)
            
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
            if Config.SIMULATION_MODE:
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
            if Config.SIMULATION_MODE:
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
    
    def run(self):
        """Run the bot"""
        try:
            # Validate configuration
            Config.validate_config()
            
            # Create application
            self.app = Application.builder().token(Config.BOT_TOKEN).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
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
            
            logger.info("Bot starting...")
            
            # Run the bot
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()