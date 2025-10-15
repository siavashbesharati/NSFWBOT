import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import io
import os
from urllib.parse import quote_plus

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
from translations import get_text, get_user_language, set_user_language, translation_manager

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

    def _build_welcome_message(
        self,
        first_name: Optional[str],
        user_lang: str,
        referral_bonus: Optional[Dict[str, int]] = None
    ) -> str:
        """Compose the localized welcome message."""
        display_name = first_name or get_text('general.unknown_user', user_lang)

        welcome_title = get_text('welcome.title', user_lang, first_name=display_name)
        features = get_text('welcome.features', user_lang)
        start_prompt = get_text('welcome.start_prompt', user_lang)

        referral_text = ""
        if referral_bonus:
            referral_text = get_text(
                'welcome.referral_bonus',
                user_lang,
                text_reward=referral_bonus['text'],
                image_reward=referral_bonus['image'],
                video_reward=referral_bonus['video']
            ) + "\n"

        return f"""
{welcome_title}

{referral_text}{features}

{start_prompt}
        """

    def _build_language_keyboard(self, selected_lang: str, prefix: str) -> InlineKeyboardMarkup:
        languages = translation_manager.get_available_languages()
        keyboard = []
        lang_items = list(languages.items())

        for i in range(0, len(lang_items), 2):
            row = []
            for j in range(2):
                if i + j < len(lang_items):
                    code, name = lang_items[i + j]
                    label = f"{'✅ ' if code == selected_lang else ''}{name}"
                    row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}{code}"))
            if row:
                keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Get user's language preference
        user_lang = get_user_language(user.id, self.db)
        
        # Check if this is a new user
        existing_user = self.db.get_user(user.id)
        is_new_user = existing_user is None
        
        # Create or update user in database
        self.db.create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Handle referral code if provided and user is new
        referral_bonus_info: Optional[Dict[str, int]] = None
        if is_new_user and context.args:
            referral_code = context.args[0].upper()
            
            # Check if referral system is enabled
            settings = self.db.get_all_settings()
            if settings.get('referral_system_enabled', 'true') == 'true':
                if self.db.validate_referral_code(referral_code):
                    # Process the referral
                    if self.db.process_referral(user.id, referral_code):
                        text_reward = int(settings.get('referral_text_reward', 3))
                        image_reward = int(settings.get('referral_image_reward', 1))
                        video_reward = int(settings.get('referral_video_reward', 1))
                        referral_bonus_info = {
                            'text': text_reward,
                            'image': image_reward,
                            'video': video_reward
                        }

        context.user_data['start_context'] = {
            'referral_bonus': referral_bonus_info
        }

        keyboard = self._build_language_keyboard(user_lang, "start_lang_")
        select_text = get_text('language.select', user_lang)
        current_lang = translation_manager.get_language_name(user_lang)
        current_text = get_text('language.current', user_lang, language=current_lang)
        prompt_message = f"{select_text}\n\n{current_text}"

        await update.message.reply_text(prompt_message, reply_markup=keyboard)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_lang = get_user_language(update.effective_user.id, self.db)
        
        help_title = get_text('help.title', user_lang)
        menu_tip = get_text('help.menu_tip', user_lang)
        
        # Build command list with translations
        commands_text = "\n".join([
            f"/start - {get_text('commands.start', user_lang)}",
            f"/help - {get_text('commands.help', user_lang)}",
            f"/dashboard - {get_text('commands.dashboard', user_lang)}",
            f"/packages - {get_text('commands.packages', user_lang)}",
            f"/balance - {get_text('commands.balance', user_lang)}",
            f"/referral - {get_text('commands.referral', user_lang)}",
            f"/enterreferral - {get_text('commands.enterreferral', user_lang)}",
            f"/reset - {get_text('commands.reset', user_lang)}",
            f"/language - {get_text('commands.language', user_lang)}",
            f"/testapi - {get_text('commands.testapi', user_lang)}"
        ])
        
        message_types = get_text('help.message_types', user_lang)
        payment_methods = get_text('help.payment_methods', user_lang)
        referral_info = get_text('help.referral_info', user_lang)
        tracking_info = get_text('help.tracking_info', user_lang)
        
        help_text = f"""
{help_title}

{menu_tip}

{commands_text}

{message_types}

{payment_methods}

{referral_info}

{tracking_info}
        """
        
        await update.message.reply_text(help_text)

    async def start_command_callback(self, query, context, user_lang):
        """Handle start command from glass menu callback"""
        user = query.from_user
        welcome_message = self._build_welcome_message(user.first_name, user_lang)

        await query.edit_message_text(welcome_message)

    async def help_command_callback(self, query, context, user_lang):
        """Handle help command from glass menu callback"""
        help_title = get_text('help.title', user_lang)
        menu_tip = get_text('help.menu_tip', user_lang)
        
        # Build command list with translations
        commands_text = "\n".join([
            f"/start - {get_text('commands.start', user_lang)}",
            f"/help - {get_text('commands.help', user_lang)}",
            f"/dashboard - {get_text('commands.dashboard', user_lang)}",
            f"/packages - {get_text('commands.packages', user_lang)}",
            f"/balance - {get_text('commands.balance', user_lang)}",
            f"/referral - {get_text('commands.referral', user_lang)}",
            f"/enterreferral - {get_text('commands.enterreferral', user_lang)}",
            f"/reset - {get_text('commands.reset', user_lang)}",
            f"/language - {get_text('commands.language', user_lang)}",
            f"/testapi - {get_text('commands.testapi', user_lang)}"
        ])
        
        message_types = get_text('help.message_types', user_lang)
        payment_methods = get_text('help.payment_methods', user_lang)
        referral_info = get_text('help.referral_info', user_lang)
        tracking_info = get_text('help.tracking_info', user_lang)
        
        help_text = f"""
{help_title}

{menu_tip}

{commands_text}

{message_types}

{payment_methods}

{referral_info}

{tracking_info}
        """
        
        # Add back to menu button
        keyboard = [[InlineKeyboardButton(
            get_text('glass_menu.back_to_menu', user_lang), 
            callback_data="back_to_menu"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup)

    async def dashboard_command_callback(self, query, context, user_lang):
        """Handle dashboard command from glass menu callback"""
        # Redirect to the existing dashboard logic but with proper language
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.dashboard_command(fake_update, context)

    async def packages_command_callback(self, query, context, user_lang):
        """Handle packages command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.packages_command(fake_update, context)

    async def balance_command_callback(self, query, context, user_lang):
        """Handle balance command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.balance_command(fake_update, context)

    async def referral_command_callback(self, query, context, user_lang):
        """Handle referral command from glass menu callback - shows gift menu with referral options"""
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text(get_text('general.start_bot_first', user_lang))
            return
        
        # Check if referral system is enabled
        settings = self.db.get_all_settings()
        if settings.get('referral_system_enabled', 'true') != 'true':
            await query.edit_message_text(get_text('errors.referral_system_disabled', user_lang))
            return
        
        # Get or generate referral code
        referral_code = self.db.get_user_referral_code(user_id)
        if not referral_code:
            referral_code = self.db.generate_referral_code(user_id)
        
        # Get referral statistics
        referral_stats = self.db.get_user_referrals(user_id)
        
        # Get reward amounts
        text_reward = int(settings.get('referral_text_reward', 3))
        image_reward = int(settings.get('referral_image_reward', 1))
        video_reward = int(settings.get('referral_video_reward', 1))
        
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        # Use translations for the gift/referral text
        title = get_text('referral.title', user_lang)
        your_code = get_text('referral.your_code', user_lang, code=referral_code)
        your_link = get_text('referral.your_link', user_lang, link=referral_link)
        stats = get_text('referral.stats', user_lang, count=referral_stats['successful_referrals'], rewards="")
        how_it_works = get_text('referral.how_it_works', user_lang)
        rewards_info = get_text('referral.rewards_info', user_lang, text=text_reward, image=image_reward, video=video_reward)
        
        referral_text = f"""
{title}

{your_code}

{your_link}

{rewards_info}

{stats}

{how_it_works}
        """
        
        # Create keyboard with gift options
        share_text = get_text('referral.share_referral_link', user_lang)
        share_message = get_text('referral.share_message', user_lang, referral_link=referral_link)
        share_url = f"https://t.me/share/url?url={quote_plus(referral_link)}&text={quote_plus(share_message)}"
        keyboard = [
            [InlineKeyboardButton(share_text, url=share_url)],
            [InlineKeyboardButton(get_text('referral.my_referrals', user_lang), callback_data="show_referrals")],
            [InlineKeyboardButton(get_text('commands.enterreferral', user_lang), callback_data="enter_referral_from_gift")],
            [InlineKeyboardButton(get_text('glass_menu.back_to_menu', user_lang), callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(referral_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def language_command_callback(self, query, context, user_lang):
        """Handle language command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.language_command(fake_update, context)

    async def enter_referral_command_callback(self, query, context, user_lang):
        """Handle enter referral command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.enter_referral_command(fake_update, context)

    async def test_api_command_callback(self, query, context, user_lang):
        """Handle test API command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.test_api_command(fake_update, context)

    async def venice_status_command_callback(self, query, context, user_lang):
        """Handle Venice status command from glass menu callback"""
        fake_update = type('Update', (), {
            'effective_user': query.from_user,
            'effective_chat': query.message.chat,
            'message': query.message
        })()
        await self.venice_status_command(fake_update, context)
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /language command - Show language selection"""
        user_lang = get_user_language(update.effective_user.id, self.db)
        reply_markup = self._build_language_keyboard(user_lang, "set_lang_")
        
        select_text = get_text('language.select', user_lang)
        current_lang = translation_manager.get_language_name(user_lang)
        current_text = get_text('language.current', user_lang, language=current_lang)
        
        message = f"{select_text}\n\n{current_text}"
        
        await update.message.reply_text(message, reply_markup=reply_markup)

    async def handle_start_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection during the start flow."""
        query = update.callback_query

        lang_code = query.data.replace("start_lang_", "")
        if not translation_manager.is_supported_language(lang_code):
            fallback_lang = getattr(translation_manager, 'DEFAULT_LANGUAGE', 'en')
            error_msg = get_text('language.invalid', fallback_lang)
            await query.edit_message_text(error_msg)
            return

        user_id = query.from_user.id
        self.db.set_user_language(user_id, lang_code)

        start_context = context.user_data.get('start_context', {})
        referral_bonus = start_context.get('referral_bonus')

        welcome_message = self._build_welcome_message(query.from_user.first_name, lang_code, referral_bonus)
        await query.edit_message_text(welcome_message)

        context.user_data.pop('start_context', None)

        await self.show_glass_menu(query.message.chat.id, lang_code, context)

    async def show_glass_menu(self, chat_id, user_lang, context: ContextTypes.DEFAULT_TYPE, message_text=None):
        """Helper method to show the glass-style interactive menu"""
        if message_text is None:
            message_text = f"{get_text('glass_menu.title', user_lang)}\n{get_text('glass_menu.subtitle', user_lang)}"
        
        # Create glass-style menu with emoji icons
        keyboard = []
        
        # Row 1: Dashboard & Packages
        keyboard.append([
            InlineKeyboardButton(
                get_text('commands.dashboard', user_lang), 
                callback_data="cmd_dashboard"
            ),
            InlineKeyboardButton(
                get_text('commands.packages', user_lang), 
                callback_data="cmd_packages"
            )
        ])
        
        # Row 2: Balance & Referral
        keyboard.append([
            InlineKeyboardButton(
                get_text('commands.balance', user_lang), 
                callback_data="cmd_balance"
            ),
            InlineKeyboardButton(
                get_text('commands.referral', user_lang), 
                callback_data="cmd_referral"
            )
        ])
        
        # Row 3: Help & Language
        keyboard.append([
            InlineKeyboardButton(
                get_text('commands.help', user_lang), 
                callback_data="cmd_help"
            ),
            InlineKeyboardButton(
                get_text('commands.language', user_lang), 
                callback_data="cmd_language"
            )
        ])

        # Row 4: Admin commands (only for admins)
        admin_chat_id = self.db.get_setting('admin_chat_id', '0')
        try:
            admin_id = int(admin_chat_id) if admin_chat_id else 0
        except ValueError:
            admin_id = 0
            
        if chat_id == admin_id and admin_id != 0:
            keyboard.append([
                InlineKeyboardButton(
                    get_text('commands.testapi', user_lang), 
                    callback_data="cmd_testapi"
                ),
                InlineKeyboardButton(
                    "📊 Venice Status", 
                    callback_data="cmd_venicestatus"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command - Show interactive glass-style menu"""
        user_lang = get_user_language(update.effective_user.id, self.db)
        chat_id = update.effective_chat.id
        
        await self.show_glass_menu(chat_id, user_lang, context)
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle menu command callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        user_lang = get_user_language(user_id, self.db)
        
        # Map callback commands to actual methods
        command_map = {
            "cmd_dashboard": self.dashboard_command,
            "cmd_packages": self.packages_command,
            "cmd_balance": self.balance_command,
            "cmd_referral": self.referral_command,
            "cmd_help": self.help_command,
            "cmd_language": self.language_command,
            "cmd_enterreferral": self.enter_referral_command,
            "cmd_testapi": self.test_api_command,
            "cmd_venicestatus": self.venice_status_command
        }
        
        # Handle back to menu button
        if callback_data == "back_to_menu":
            # Recreate the glass menu inline keyboard
            keyboard = []
            
            # Row 1: Dashboard & Packages
            keyboard.append([
                InlineKeyboardButton(
                    get_text('commands.dashboard', user_lang), 
                    callback_data="cmd_dashboard"
                ),
                InlineKeyboardButton(
                    get_text('commands.packages', user_lang), 
                    callback_data="cmd_packages"
                )
            ])
            
            # Row 2: Balance & Referral
            keyboard.append([
                InlineKeyboardButton(
                    get_text('commands.balance', user_lang), 
                    callback_data="cmd_balance"
                ),
                InlineKeyboardButton(
                    get_text('commands.referral', user_lang), 
                    callback_data="cmd_referral"
                )
            ])
            
            # Row 3: Help & Language
            keyboard.append([
                InlineKeyboardButton(
                    get_text('commands.help', user_lang), 
                    callback_data="cmd_help"
                ),
                InlineKeyboardButton(
                    get_text('commands.language', user_lang), 
                    callback_data="cmd_language"
                )
            ])
            
            # Row 4: Admin commands (only for admins)
            admin_chat_id = self.db.get_setting('admin_chat_id', '0')
            try:
                admin_id = int(admin_chat_id) if admin_chat_id else 0
            except ValueError:
                admin_id = 0
                
            if query.from_user.id == admin_id and admin_id != 0:
                keyboard.append([
                    InlineKeyboardButton(
                        get_text('commands.testapi', user_lang), 
                        callback_data="cmd_testapi"
                    ),
                    InlineKeyboardButton(
                        "📊 Venice Status", 
                        callback_data="cmd_venicestatus"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            menu_title = get_text('glass_menu.title', user_lang)
            menu_subtitle = get_text('glass_menu.subtitle', user_lang)
            message_text = f"{menu_title}\n{menu_subtitle}"
            
            await query.edit_message_text(message_text, reply_markup=reply_markup)
            return
        
        if callback_data in command_map:
            try:
                # For glass menu callbacks, we'll handle them differently
                # Instead of creating fake updates, we'll call special callback versions
                if callback_data == "cmd_help":
                    await self.help_command_callback(query, context, user_lang)
                elif callback_data == "cmd_dashboard":
                    await self.dashboard_command_callback(query, context, user_lang)
                elif callback_data == "cmd_packages":
                    await self.packages_command_callback(query, context, user_lang)
                elif callback_data == "cmd_balance":
                    await self.balance_command_callback(query, context, user_lang)
                elif callback_data == "cmd_referral":
                    await self.referral_command_callback(query, context, user_lang)
                elif callback_data == "cmd_language":
                    await self.language_command_callback(query, context, user_lang)
                elif callback_data == "cmd_testapi":
                    await self.test_api_command_callback(query, context, user_lang)
                elif callback_data == "cmd_venicestatus":
                    await self.venice_status_command_callback(query, context, user_lang)
                else:
                    # Fallback to original method
                    fake_update = Update(
                        update_id=query.message.message_id,
                        message=query.message
                    )
                    await command_map[callback_data](fake_update, context)
                    
                    # Edit the original message to show command was executed
                    success_msg = get_text('glass_menu.command_executed', user_lang)
                    await query.edit_message_text(f"✅ {success_msg}")
                
                # Note: start and help commands handle their own message editing
                # so we don't show "command executed" for them
                
            except Exception as e:
                error_msg = get_text('errors.command_error', user_lang, error=str(e))
                await query.edit_message_text(f"❌ {error_msg}")
        else:
            error_msg = get_text('errors.invalid_command', user_lang)
            await query.edit_message_text(f"❌ {error_msg}")
    
    async def handle_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        if callback_data.startswith("set_lang_"):
            lang_code = callback_data.replace("set_lang_", "")
            
            if translation_manager.is_supported_language(lang_code):
                # Update user's language preference
                self.db.set_user_language(user_id, lang_code)
                
                # Note: We DON'T update the global menu here because:
                # 1. Telegram bot menus are global (affect all users)
                # 2. Constantly changing menu creates poor UX
                # 3. Users should use /language command instead of menu for language switching
                
                # Get language name for confirmation
                lang_name = translation_manager.get_language_name(lang_code)
                success_msg = get_text('language.changed', lang_code, language=lang_name)
                
                # Add explanation about menu limitation
                explanation = get_text('language.menu_limitation', lang_code)
                full_message = f"{success_msg}\n\n{explanation}"
                
                await query.edit_message_text(full_message)
                
                # Show the glass menu again after language change
                await self.show_glass_menu(query.message.chat.id, lang_code, context)
            else:
                error_msg = get_text('language.invalid', lang_code)
                await query.edit_message_text(error_msg)
    
    async def test_api_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /testapi command - Test AI API connection"""
        user_id = update.effective_user.id
        user_lang = get_user_language(user_id, self.db)
        
        # Check if user is admin
        admin_chat_id = self.db.get_setting('admin_chat_id', '0')
        try:
            admin_id = int(admin_chat_id) if admin_chat_id else 0
        except ValueError:
            admin_id = 0
            
        if user_id != admin_id or admin_id == 0:
            error_msg = get_text('errors.admin_not_set', user_lang)
            await update.message.reply_text(error_msg)
            return
        
        testing_msg = get_text('status.testing_api', user_lang)
        await update.message.reply_text(testing_msg)
        
        try:
            # Test the API
            is_working = await self.ai_handler.test_api_connection()
            
            if is_working:
                success_msg = get_text('success.api_test_passed', user_lang)
                await update.message.reply_text(success_msg)
            else:
                error_msg = get_text('errors.api_test_failed', user_lang)
                await update.message.reply_text(error_msg)
                
        except Exception as e:
            error_msg = get_text('errors.api_test_error', user_lang, error=str(e))
            await update.message.reply_text(error_msg)
    
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
            user_lang = get_user_language(user_id, self.db)
            
            # Clear conversation history for this user
            self.db.clear_conversation_history(user_id)
            
            success_msg = get_text('success.conversation_reset', user_lang)
            await update.message.reply_text(success_msg)
            
        except Exception as e:
            user_lang = get_user_language(update.effective_user.id, self.db)
            error_msg = get_text('errors.reset_error', user_lang, error=str(e))
            await update.message.reply_text(error_msg)
    
    async def packages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available packages"""
        user_lang = get_user_language(update.effective_user.id, self.db)
        packages = self.db.get_packages()
        
        if not packages:
            await update.message.reply_text(get_text('packages.no_packages', user_lang))
            return
        
        keyboard = []
        message_lines = [get_text('packages.title', user_lang), ""]
        
        for package in packages:
            package_lines = [
                f"🏷️ **{package['name']}**",
                get_text('packages.text_messages', user_lang, count=package['text_count']),
                get_text('packages.image_generations', user_lang, count=package['image_count']),
                get_text('packages.video_generations', user_lang, count=package['video_count'])
            ]
            
            # Get payment settings from database
            telegram_stars_enabled = self.db.get_setting('telegram_stars_enabled', 'true') == 'true'
            ton_enabled = self.db.get_setting('ton_enabled', 'true') == 'true'
            
            if telegram_stars_enabled:
                package_lines.append(get_text('packages.price', user_lang, price=f"⭐ {package['price_stars']} Stars"))
            
            if ton_enabled:
                ton_price = get_text('packages.price', user_lang, price=f"💎 {package['price_ton']} TON")
                if telegram_stars_enabled:
                    package_lines.append(ton_price)
                else:
                    package_lines.append(ton_price)
            
            message_lines.extend(package_lines)
            message_lines.append("")
            
            # Create payment buttons
            row = []
            if telegram_stars_enabled:
                row.append(InlineKeyboardButton(
                    get_text('buttons.buy_with_stars', user_lang, price=package['price_stars']),
                    callback_data=f"buy_stars_{package['id']}"
                ))
            
            if ton_enabled:
                row.append(InlineKeyboardButton(
                    get_text('buttons.buy_with_ton', user_lang, price=package['price_ton']),
                    callback_data=f"buy_ton_{package['id']}"
                ))
            
            keyboard.append(row)
        
        message_text = "\n".join(message_lines).strip()
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user dashboard"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        user_lang = get_user_language(user_id, self.db)
        
        if not user_data:
            await update.message.reply_text(get_text('general.start_bot_first', user_lang))
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

💰 Total Spent: ${user_data['total_spent']}
        """
        
        keyboard = [
            [InlineKeyboardButton(get_text('buttons.buy_packages', user_lang), callback_data="show_packages")],
            [InlineKeyboardButton(get_text('buttons.refresh', user_lang), callback_data="refresh_dashboard")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(dashboard_text, reply_markup=reply_markup)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user balance"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        user_lang = get_user_language(user_id, self.db)
        
        if not user_data:
            await update.message.reply_text(get_text('general.start_bot_first', user_lang))
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
    
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's referral information"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        user_lang = get_user_language(user_id, self.db)
        
        if not user_data:
            await update.message.reply_text(get_text('general.start_bot_first', user_lang))
            return
        
        # Check if referral system is enabled
        settings = self.db.get_all_settings()
        if settings.get('referral_system_enabled', 'true') != 'true':
            await update.message.reply_text(get_text('errors.referral_system_disabled', user_lang))
            return
        
        # Get or generate referral code
        referral_code = self.db.get_user_referral_code(user_id)
        if not referral_code:
            referral_code = self.db.generate_referral_code(user_id)
        
        # Get referral statistics
        referral_stats = self.db.get_user_referrals(user_id)
        
        # Get reward amounts
        text_reward = int(settings.get('referral_text_reward', 3))
        image_reward = int(settings.get('referral_image_reward', 1))
        video_reward = int(settings.get('referral_video_reward', 1))
        
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        title = get_text('referral.title', user_lang)
        your_code = get_text('referral.your_code', user_lang, code=referral_code)
        your_link = get_text('referral.your_link', user_lang, link=referral_link)
        rewards_info = get_text('referral.rewards_info', user_lang, text=text_reward, image=image_reward, video=video_reward)
        stats = get_text('referral.stats', user_lang, count=referral_stats['successful_referrals'], rewards="")
        how_it_works = get_text('referral.how_it_works', user_lang)

        referral_text = f"""
{title}

{your_code}

{your_link}

{rewards_info}

{stats}

{how_it_works}
        """
        
        share_text = get_text('referral.share_referral_link', user_lang)
        share_message = get_text('referral.share_message', user_lang, referral_link=referral_link)
        share_url = f"https://t.me/share/url?url={quote_plus(referral_link)}&text={quote_plus(share_message)}"
        keyboard = [
            [InlineKeyboardButton(share_text, url=share_url)],
            [InlineKeyboardButton(get_text('referral.my_referrals', user_lang), callback_data="show_referrals")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(referral_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def enter_referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allow users to enter a referral code manually"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        user_lang = get_user_language(user_id, self.db)
        
        if not user_data:
            await update.message.reply_text(get_text('general.start_bot_first', user_lang))
            return
        
        # Check if referral system is enabled
        settings = self.db.get_all_settings()
        if settings.get('referral_system_enabled', 'true') != 'true':
            await update.message.reply_text(get_text('errors.referral_system_disabled', user_lang))
            return
        
        if context.args:
            referral_code = context.args[0].upper()
            
            # Check if user was already referred
            existing_referral = self.db.execute_query(
                "SELECT id FROM referrals WHERE referee_id = ?", (user_id,)
            )
            
            if existing_referral:
                await update.message.reply_text(get_text('errors.referral_already_used', user_lang))
                return
            
            # Validate and process referral
            if self.db.validate_referral_code(referral_code):
                if self.db.process_referral(user_id, referral_code):
                    text_reward = int(settings.get('referral_text_reward', 3))
                    image_reward = int(settings.get('referral_image_reward', 1))
                    video_reward = int(settings.get('referral_video_reward', 1))
                    await update.message.reply_text(
                        get_text('referral.applied_success', user_lang, text=text_reward, image=image_reward, video=video_reward),
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(get_text('errors.referral_apply_failed', user_lang))
            else:
                await update.message.reply_text(get_text('errors.referral_invalid_code', user_lang))
        else:
            await update.message.reply_text(
                get_text('referral.enter_command_help', user_lang),
                parse_mode='Markdown'
            )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        user_lang = get_user_language(user_id, self.db)
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text(get_text('general.bot_offline', user_lang))
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'text'):
            await update.message.reply_text(get_text('credits.not_enough_text', user_lang))
            await update.message.reply_text(get_text('credits.get_more', user_lang))
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
            
            # Get Venice API metadata for auditing
            venice_metadata = self.ai_handler.get_last_response_metadata()
            
            # Save to message history with AI model info and Venice metadata
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'text', 
                user_message, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history),
                venice_metadata=venice_metadata
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling text message: {str(e)}")
            await update.message.reply_text(get_text('errors.api_general_error', user_lang))
    
    async def handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages"""
        user_id = update.effective_user.id
        user_lang = get_user_language(user_id, self.db)
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text(get_text('general.bot_offline', user_lang))
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'image'):
            await update.message.reply_text(get_text('credits.not_enough_image', user_lang))
            await update.message.reply_text(get_text('credits.get_more', user_lang))
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
            caption = update.message.caption or get_text('media.default_image_caption', user_lang)
            
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
            
            # Get Venice API metadata for auditing
            venice_metadata = self.ai_handler.get_last_response_metadata()
            
            # Save to message history with AI model info and Venice metadata
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'image', 
                caption, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history),
                venice_metadata=venice_metadata
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling image message: {str(e)}")
            await update.message.reply_text(get_text('errors.image_processing_error', user_lang))
    
    async def handle_video_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user_id = update.effective_user.id
        user_lang = get_user_language(user_id, self.db)
        
        # Check if bot is running
        if not self.db.get_setting('bot_running', 'true') == 'true':
            await update.message.reply_text(get_text('general.bot_offline', user_lang))
            return
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Check if user has credits
        if not self.db.use_message_credit(user_id, 'video'):
            await update.message.reply_text(get_text('credits.not_enough_video', user_lang))
            await update.message.reply_text(get_text('credits.get_more', user_lang))
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get caption if any
            caption = update.message.caption or get_text('media.default_video_caption', user_lang)
            
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
            
            # Get Venice API metadata for auditing
            venice_metadata = self.ai_handler.get_last_response_metadata()
            
            # Save to message history with AI model info and Venice metadata
            ai_model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.db.save_message_history(
                user_id, 
                'video', 
                caption, 
                ai_response,
                ai_model=ai_model,
                context_length=len(conversation_history),
                venice_metadata=venice_metadata
            )
            
            # Send response
            await update.message.reply_text(ai_response)
            
        except Exception as e:
            logger.error(f"Error handling video message: {str(e)}")
            await update.message.reply_text(get_text('errors.video_processing_error', user_lang))
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = update.effective_user.id
        user_lang = get_user_language(user_id, self.db)

        if data.startswith("start_lang_"):
            await self.handle_start_language_selection(update, context)
            return

        # Handle language selection
        if data.startswith("set_lang_"):
            await self.handle_language_callback(update, context)
            return

        # Handle menu command callbacks
        if data.startswith("cmd_") or data == "back_to_menu":
            await self.handle_menu_callback(update, context)
            return

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
                telegram_stars_enabled = self.db.get_setting('telegram_stars_enabled', 'true') == 'true'
                ton_enabled = self.db.get_setting('ton_enabled', 'true') == 'true'
                
                if telegram_stars_enabled:
                    row.append(InlineKeyboardButton(
                        f"⭐ {package['name']} ({package['price_stars']} Stars)",
                        callback_data=f"buy_stars_{package['id']}"
                    ))
                
                if ton_enabled:
                    row.append(InlineKeyboardButton(
                        f"💎 {package['name']} ({package['price_ton']} TON)",
                        callback_data=f"buy_ton_{package['id']}"
                    ))
                
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(get_text('packages.select', user_lang), reply_markup=reply_markup)
        
        elif data == "refresh_dashboard":
            # Refresh dashboard for callback query
            user_id = query.from_user.id
            user_data = self.db.get_user(user_id)
            
            if not user_data:
                await query.edit_message_text(get_text('general.start_bot_first', user_lang))
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

💰 Total Spent: ${user_data['total_spent']}
            """
            
            keyboard = [
                [InlineKeyboardButton(get_text('buttons.buy_packages', user_lang), callback_data="show_packages")],
                [InlineKeyboardButton(get_text('buttons.refresh', user_lang), callback_data="refresh_dashboard")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(dashboard_text, reply_markup=reply_markup)
        
        elif data == "show_referrals":
            # Show user's referral details
            user_id = query.from_user.id
            referral_stats = self.db.get_user_referrals(user_id)
            
            if referral_stats['successful_referrals'] == 0:
                await query.edit_message_text(get_text('referral.no_referrals_message', user_lang), parse_mode='Markdown')
            else:
                referrals_text = get_text('referral.referrals_header', user_lang, count=referral_stats['successful_referrals'])
                
                for i, referral in enumerate(referral_stats['referrals'][:10], 1):  # Show last 10
                    username = referral.get('username')
                    first_name = referral.get('first_name') or get_text('general.unknown_user', user_lang)
                    display_name = username or f"{first_name}"
                    date_value = referral.get('completed_date')
                    date = date_value[:10] if date_value else get_text('general.unknown_value', user_lang)

                    referrals_text += get_text('referral.referrals_entry', user_lang, index=i, username=display_name, date=date)
                
                if len(referral_stats['referrals']) > 10:
                    remaining = len(referral_stats['referrals']) - 10
                    referrals_text += get_text('referral.referrals_more', user_lang, count=remaining)
                
                keyboard = [[InlineKeyboardButton(get_text('buttons.back_to_referrals', user_lang), callback_data="back_to_referral")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(referrals_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        elif data == "back_to_referral":
            # Go back to referral main screen
            await self.referral_command(update, context)
        
        elif data == "enter_referral_from_gift":
            # Handle enter referral code from gift menu
            await query.edit_message_text(
                get_text('referral.enter_code_instructions', user_lang),
                parse_mode='Markdown'
            )
            # Note: The actual referral code processing happens in the text message handler
        
        elif data.startswith("check_payment_"):
            # Check payment status
            transaction_id = int(data.split("_")[2])
            await self.handle_check_payment(query, transaction_id)
    
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
            message = f"""
💎 TON Payment Instructions {result.get('network', '')}

📦 Package: {package['name']}
💰 Amount: {amount} TON
🏦 Address: `{result['ton_address']}`
💬 Comment: `{result['comment']}`

📱 Quick Payment:
[Open in Tonkeeper]({result['payment_url']})

⏰ Your payment will be verified automatically within a few minutes.

{result.get('network', '🌐 MAINNET') if '🧪' not in result.get('network', '') else '🧪 Note: This is TESTNET - you will receive test TON only!'}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔗 Pay with Tonkeeper", url=result['payment_url'])],
                [InlineKeyboardButton("🔍 Check Payment Status", callback_data=f"check_payment_{result['transaction_id']}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ {result['error']}")
    
    async def handle_check_payment(self, query, transaction_id: int):
        """Check TON payment status"""
        try:
            # Get transaction details
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, payment_method, amount, created_date, user_id, package_id 
                FROM transactions 
                WHERE id = ?
            ''', (transaction_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                await query.edit_message_text("❌ Transaction not found.")
                return
            
            status, payment_method, amount, created_date, user_id, package_id = result
            
            # Check if this transaction belongs to the current user
            if user_id != query.from_user.id:
                await query.edit_message_text("❌ This transaction doesn't belong to you.")
                return
            
            if status == 'completed':
                await query.edit_message_text("✅ Payment already completed! Your credits have been added.")
                return
            
            if payment_method == 'ton':
                # Try to verify the TON payment
                await query.edit_message_text("🔍 Checking blockchain for your payment...")
                
                verification_success = await self.payment_handler.verify_ton_payment(transaction_id)
                
                if verification_success:
                    # Payment found and verified!
                    package = self.db.get_package(package_id)
                    message = f"""
✅ **Payment Verified!**

💰 Amount: {amount} TON
📦 Package: {package['name'] if package else 'Unknown'}
📅 Date: {created_date}

🎉 Your credits have been added to your account!
                    """
                    
                    # Add buttons to go back or check dashboard
                    keyboard = [
                        [InlineKeyboardButton("📊 View Dashboard", callback_data="refresh_dashboard")],
                        [InlineKeyboardButton("🛒 Buy More", callback_data="show_packages")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                    
                    # Notify admin about successful payment
                    admin_chat_id = self.db.get_setting('admin_chat_id')
                    if admin_chat_id:
                        admin_message = f"""
💰 **Payment Received!**

👤 User: {query.from_user.first_name} (@{query.from_user.username or 'no_username'})
💰 Amount: {amount} TON
📦 Package: {package['name'] if package else 'Unknown'}
🆔 Transaction: {transaction_id}
📅 Date: {created_date}
                        """
                        try:
                            await self.app.bot.send_message(admin_chat_id, admin_message, parse_mode='Markdown')
                        except Exception as e:
                            logging.error(f"Failed to notify admin: {e}")
                else:
                    # Payment not found yet
                    message = f"""
⏳ **Payment Pending**

💰 Amount: {amount} TON
📅 Created: {created_date}
🆔 Transaction ID: {transaction_id}

❌ Payment not found on blockchain yet.

**Please make sure you:**
✅ Sent exactly {amount} TON
✅ Used the correct comment: `Payment_{transaction_id}`
✅ Sent to the correct wallet address

⏰ It may take a few minutes for the transaction to appear on the blockchain.
                    """
                    
                    keyboard = [[
                        InlineKeyboardButton("🔍 Check Again", callback_data=f"check_payment_{transaction_id}")
                    ]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("ℹ️ This feature is only available for TON payments.")
                
        except Exception as e:
            logging.error(f"Error checking payment: {e}")
            await query.edit_message_text("❌ Error checking payment status. Please try again.")
    
    async def check_pending_payments_task(self, context: ContextTypes.DEFAULT_TYPE):
        """Background task to check pending payments every 2 minutes"""
        try:
            await self.payment_handler.check_pending_payments()
        except Exception as e:
            logging.error(f"Error in payment check task: {e}")
    
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
        """Set up the bot's minimalist hamburger menu with only essential commands"""
        try:
            # Use English for menu by default (most universal language)
            # This prevents constant menu changes when users switch languages
            menu_language = 'en'
            
            # Admin can override menu language via database setting
            admin_menu_lang = self.db.get_setting('menu_language', 'en')
            if translation_manager.is_supported_language(admin_menu_lang):
                menu_language = admin_menu_lang
            
            # Minimalist menu with only 2 essential commands
            commands = [
                BotCommand("menu", get_text('menu_descriptions.menu', menu_language)),
                BotCommand("reset", get_text('menu_descriptions.reset', menu_language))
            ]
            
            await application.bot.set_my_commands(commands)
            logger.info(f"✅ Minimalist bot menu set up with {len(commands)} commands in language: {menu_language}")
            
        except Exception as e:
            logger.error(f"❌ Failed to set up bot menu: {str(e)}")
    
    def get_most_common_language(self):
        """Get the most commonly used language by users"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get language usage statistics
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM users 
                WHERE language IS NOT NULL 
                GROUP BY language 
                ORDER BY count DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
            else:
                return 'en'  # Default to English
                
        except Exception as e:
            logger.error(f"Error getting most common language: {e}")
            return 'en'
    
    async def set_menu_language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to set the global menu language"""
        user_id = update.effective_user.id
        user_lang = get_user_language(user_id, self.db)
        
        # Check if user is admin
        admin_chat_id = self.db.get_setting('admin_chat_id', '0')
        try:
            admin_id = int(admin_chat_id) if admin_chat_id else 0
        except ValueError:
            admin_id = 0
            
        if user_id != admin_id or admin_id == 0:
            error_msg = get_text('errors.admin_only', user_lang)
            await update.message.reply_text(error_msg)
            return
        
        # Get language argument
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Usage: /setmenulang <language_code>\n"
                "Available: en, ar, fa, tr, ru, es, zh\n"
                "Example: /setmenulang es"
            )
            return
            
        lang_code = context.args[0].lower()
        
        if not translation_manager.is_supported_language(lang_code):
            await update.message.reply_text(f"❌ Unsupported language: {lang_code}")
            return
        
        # Update menu language setting
        self.db.set_setting('menu_language', lang_code)
        
        # Update the menu
        await self.update_bot_menu_for_language(lang_code)
        
        lang_name = translation_manager.get_language_name(lang_code)
        await update.message.reply_text(f"✅ Bot menu language set to {lang_name} ({lang_code})")
    
    async def update_bot_menu_for_language(self, lang_code):
        """Update the bot menu for a specific language"""
        try:
            # Minimalist menu with only 2 essential commands
            commands = [
                BotCommand("menu", get_text('menu_descriptions.menu', lang_code)),
                BotCommand("reset", get_text('menu_descriptions.reset', lang_code))
            ]
            
            await self.app.bot.set_my_commands(commands)
            logger.info(f"✅ Minimalist bot menu updated for language: {lang_code}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update bot menu for language {lang_code}: {str(e)}")
    
    def run(self):
        """Run the bot"""
        try:
            # Validate configuration
            Config.validate_config()
            
            # Get bot token from database or config
            bot_token = self.db.get_setting('bot_token', Config.BOT_TOKEN)
            
            # Create application with optimized HTTP client settings
            from telegram.request import HTTPXRequest
            
            # Create HTTP client with proper timeouts for production
            request = HTTPXRequest(
                connection_pool_size=20,      # Connection pool size
                read_timeout=30.0,            # Read timeout
                write_timeout=30.0,           # Write timeout
                connect_timeout=30.0,         # Connection timeout
                pool_timeout=30.0             # Pool timeout
            )
            
            self.app = Application.builder().token(bot_token).request(request).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            self.app.add_handler(CommandHandler("menu", self.menu_command))
            self.app.add_handler(CommandHandler("language", self.language_command))
            self.app.add_handler(CommandHandler("setmenulang", self.set_menu_language_command))
            self.app.add_handler(CommandHandler("reset", self.reset_command))
            self.app.add_handler(CommandHandler("testapi", self.test_api_command))
            self.app.add_handler(CommandHandler("venicestatus", self.venice_status_command))
            self.app.add_handler(CommandHandler("packages", self.packages_command))
            self.app.add_handler(CommandHandler("dashboard", self.dashboard_command))
            self.app.add_handler(CommandHandler("balance", self.balance_command))
            self.app.add_handler(CommandHandler("referral", self.referral_command))
            self.app.add_handler(CommandHandler("enterreferral", self.enter_referral_command))
            
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
            
            # Schedule background task to check pending payments every 2 minutes (if job queue is available)
            try:
                job_queue = self.app.job_queue
                if job_queue:
                    job_queue.run_repeating(self.check_pending_payments_task, interval=120, first=30)
                    logger.info("✅ Background payment checker scheduled")
                else:
                    logger.warning("⚠️ JobQueue not available. Install with: pip install 'python-telegram-bot[job-queue]'")
            except Exception as e:
                logger.warning(f"⚠️ Could not set up background payment checker: {e}")
            
            logger.info("Bot starting...")
            
            # Run the bot with optimized polling settings for production
            self.app.run_polling(
                poll_interval=1.0,                    # Check for updates every 1 second
                timeout=30,                          # Timeout for each poll request
                drop_pending_updates=True,           # Ignore old updates on restart (prevents spam)
                allowed_updates=Update.ALL_TYPES     # Accept all update types
            )
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()