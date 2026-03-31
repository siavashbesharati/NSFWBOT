from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import Database
from currency_converter import currency_converter
from ai_handler import VeniceAPI
from financial_analytics import FinancialAnalytics
import json
import os
import sqlite3
from datetime import datetime
import subprocess
import sys
import requests
import asyncio
import psutil
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
db = Database()
financial_analytics = FinancialAnalytics(db)

# Custom template filter for currency formatting
@app.template_filter('currency')
def format_currency(value):
    """Format currency preserving all precision but removing trailing zeros"""
    if value is None or value == 0:
        return "0"
    
    try:
        # Convert to float and format with reasonable precision (8 decimal places)
        num = float(value)
        # Format with enough decimal places to preserve meaningful precision
        formatted = f"{num:.8f}"
        
        # Remove trailing zeros and decimal point if needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    except (ValueError, TypeError):
        return str(value)

# Custom template filter for number formatting  
@app.template_filter('number_format')
def format_number(value):
    """Format numbers with thousands separators, preserving precision"""
    if value is None:
        return "0"
    
    try:
        # Check if it's a whole number
        num = float(value)
        if num == int(num):
            return "{:,}".format(int(num))
        else:
            # Format with reasonable precision then remove trailing zeros
            formatted = f"{num:.8f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            
            # Add thousands separators if possible
            if '.' in formatted:
                integer_part, decimal_part = formatted.split('.')
                integer_part = "{:,}".format(int(integer_part))
                return f"{integer_part}.{decimal_part}"
            else:
                return "{:,}".format(int(float(formatted)))
    except (ValueError, TypeError):
        return str(value)

# Custom template filter for precise number formatting (for financial data)
@app.template_filter('precise_number')
def format_precise_number(value):
    """Format numbers with full precision, only removing trailing zeros"""
    if value is None or value == 0:
        return "0"
    
    try:
        num = float(value)
        # Use reasonable precision formatting (8 decimal places should be enough for financial data)
        formatted = f"{num:.8f}"
        
        # Remove trailing zeros and decimal point if needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    except (ValueError, TypeError):
        return str(value)

# Custom template filter for date formatting
@app.template_filter('date_format')
def format_date(value):
    """Format datetime strings"""
    if value is None:
        return "N/A"
    
    try:
        if isinstance(value, str):
            # Parse the datetime string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError, AttributeError):
        return str(value)

# Simple admin authentication
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")  # Change this in production

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def fetch_venice_models():
    """Return a curated Venice model list for dashboard selector."""
    try:
        models = [
            {"id": "venice-uncensored", "name": "venice-uncensored", "description": "Default Venice chat model"},
            {"id": "llama-3.3-70b", "name": "llama-3.3-70b", "description": "Llama 3.3 70B"},
            {"id": "llama-3.2-3b", "name": "llama-3.2-3b", "description": "Llama 3.2 3B"},
            {"id": "qwen-2.5-72b-instruct", "name": "qwen-2.5-72b-instruct", "description": "Qwen 2.5 72B Instruct"},
            {"id": "mistral-31-24b", "name": "mistral-31-24b", "description": "Mistral 24B"},
        ]
        return {"success": True, "models": models, "total": len(models)}
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        import psutil
        import os
        from datetime import datetime
        
        # Get system stats
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Get database health
        db_health = db.health_check()
        
        # Get bot status (simplified check)
        bot_status = "unknown"
        try:
            # Check if bot token is configured
            bot_token = db.get_setting('bot_token')
            bot_status = "configured" if bot_token else "not_configured"
        except:
            bot_status = "error"
        
        health_data = {
            'status': 'healthy' if db_health['status'] == 'healthy' else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'system': {
                'memory_mb': round(memory_mb, 1),
                'cpu_percent': round(cpu_percent, 1),
                'uptime_seconds': int(time.time() - process.create_time())
            },
            'database': db_health,
            'bot': {
                'status': bot_status
            }
        }
        
        # Return appropriate HTTP status
        status_code = 200 if health_data['status'] == 'healthy' else 503
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
@login_required
def dashboard():
    # Get statistics
    total_users = db.get_user_count()
    total_transactions = db.get_transaction_count()
    payment_stats = db.get_payment_statistics()
    
    # Get USD conversions
    usd_data = currency_converter.get_total_usd_value(
        payment_stats['total_ton'], 
        payment_stats['total_stars']
    )
    
    # Get recent users (5)
    recent_users = db.get_recent_users(5)
    
    # Get recent transactions (5)
    recent_transactions = payment_stats['recent_payments'][:5]
    
    # Get system settings
    settings = db.get_all_settings()
    
    return render_template('dashboard.html', 
                         total_users=total_users,
                         total_transactions=total_transactions,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions,
                         settings=settings,
                         usd_data=usd_data)

@app.route('/users')
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pagination = db.get_users_paginated(page, per_page)
    return render_template(
        'users.html',
        users=pagination['items'],
        current_page=pagination['page'],
        total_pages=pagination['total_pages'],
        total_users=pagination['total'],
        has_prev=pagination['has_prev'],
        has_next=pagination['has_next'],
        prev_num=pagination['prev_page'],
        next_num=pagination['next_page'],
        start_index=pagination['start_index'],
        end_index=pagination['end_index'],
        per_page=pagination['per_page']
    )

@app.route('/packages')
@login_required
def packages():
    packages = db.get_all_packages()
    return render_template('packages.html', packages=packages)

@app.route('/packages/create', methods=['GET', 'POST'])
@login_required
def create_package():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        text_count = int(request.form['text_count'])
        image_count = int(request.form['image_count'])
        video_count = int(request.form['video_count'])
        price_ton = float(request.form['price_ton'])
        price_stars = int(request.form['price_stars'])
        
        success = db.create_package(name, description, text_count, image_count, video_count, price_ton, price_stars)
        
        if success:
            flash('Package created successfully!')
            return redirect(url_for('packages'))
        else:
            flash('Error creating package!')
    
    return render_template('create_package.html')

@app.route('/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@login_required
def edit_package(package_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        text_count = int(request.form['text_count'])
        image_count = int(request.form['image_count'])
        video_count = int(request.form['video_count'])
        price_ton = float(request.form['price_ton'])
        price_stars = int(request.form['price_stars'])
        is_active = 'is_active' in request.form
        
        success = db.update_package(package_id, name, description, text_count, image_count, video_count, price_ton, price_stars, is_active)
        
        if success:
            flash('Package updated successfully!')
            return redirect(url_for('packages'))
        else:
            flash('Error updating package!')
    
    package = db.get_package_by_id(package_id)
    return render_template('edit_package.html', package=package)

@app.route('/packages/delete/<int:package_id>', methods=['POST'])
@login_required
def delete_package(package_id):
    success = db.delete_package(package_id)
    if success:
        flash('Package deleted successfully!')
    else:
        flash('Error deleting package!')
    return redirect(url_for('packages'))

@app.route('/characters')
@login_required
def characters():
    """Display all characters"""
    characters = db.get_characters(active_only=False)
    return render_template('characters.html', characters=characters)

@app.route('/characters/create', methods=['GET', 'POST'])
@login_required
def create_character():
    """Create a new character"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        instruction = request.form['instruction']
        is_active = 'is_active' in request.form
        
        character_id = db.create_character(name, description, instruction, is_active)
        
        if character_id:
            flash('Character created successfully!')
            return redirect(url_for('characters'))
        else:
            flash('Error creating character!')
    
    return render_template('create_character.html')

@app.route('/characters/edit/<int:character_id>', methods=['GET', 'POST'])
@login_required
def edit_character(character_id):
    """Edit an existing character"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        instruction = request.form['instruction']
        is_active = 'is_active' in request.form
        
        success = db.update_character(character_id, name, description, instruction, is_active)
        
        if success:
            flash('Character updated successfully!')
            return redirect(url_for('characters'))
        else:
            flash('Error updating character!')
    
    character = db.get_character(character_id)
    if not character:
        flash('Character not found!')
        return redirect(url_for('characters'))
    
    return render_template('edit_character.html', character=character)

@app.route('/characters/delete/<int:character_id>', methods=['POST'])
@login_required
def delete_character(character_id):
    """Delete or deactivate a character"""
    success = db.delete_character(character_id)
    if success:
        flash('Character deleted/deactivated successfully!')
    else:
        flash('Error deleting character!')
    return redirect(url_for('characters'))

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions_data = db.get_transactions_paginated(page, per_page)
    return render_template('transactions.html', transactions=transactions_data)

@app.route('/payments')
@login_required  
def payments():
    """Detailed payments and revenue view"""
    payment_stats = db.get_payment_statistics()
    
    # Get USD conversions
    usd_data = currency_converter.get_total_usd_value(
        payment_stats['total_ton'], 
        payment_stats['total_stars']
    )
    
    return render_template('payments.html', 
                         payment_methods=payment_stats['payment_methods'],
                         recent_payments=payment_stats['recent_payments'],
                         total_transactions=payment_stats['total_transactions'],
                         total_ton=payment_stats['total_ton'],
                         total_stars=payment_stats['total_stars'],
                         total_revenue=payment_stats['total_revenue'],
                         paying_users=payment_stats['paying_users'],
                         usd_data=usd_data)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update basic settings
        bot_token = request.form['bot_token']
        admin_chat_id = request.form['admin_chat_id']
        ai_api_key = request.form['ai_api_key']
        ai_model = request.form['ai_model']
        ai_base_url = request.form['ai_base_url']
        ton_mainnet_wallet_address = request.form['ton_mainnet_wallet']
        ton_testnet_wallet_address = request.form['ton_testnet_wallet']
        ton_network_mode = request.form['ton_network_mode']
        webhook_url = request.form['webhook_url']
        bot_active = 'bot_active' in request.form
        
        # Payment method settings
        telegram_stars_enabled = 'telegram_stars_enabled' in request.form
        ton_enabled = 'ton_enabled' in request.form
        ton_api_key = request.form.get('ton_api_key', '')
        
        # Free messages and rate limiting settings
        free_text_messages = request.form.get('free_text_messages', '5')
        free_image_messages = request.form.get('free_image_messages', '2')
        free_video_messages = request.form.get('free_video_messages', '1')
        max_requests_per_minute = request.form.get('max_requests_per_minute', '20')
        max_requests_per_hour = request.form.get('max_requests_per_hour', '100')
        
        # Referral system settings
        referral_system_enabled = 'referral_system_enabled' in request.form
        referral_text_reward = request.form.get('referral_text_reward', '3')
        referral_image_reward = request.form.get('referral_image_reward', '1')
        referral_video_reward = request.form.get('referral_video_reward', '1')
        
        # Advanced settings
        max_image_size = request.form.get('max_image_size', '10')
        max_video_size = request.form.get('max_video_size', '50')
        ai_response_timeout = request.form.get('ai_response_timeout', '30')
        
        # Conversation settings
        conversation_history_length = request.form.get('conversation_history_length', '10')
        context_window_hours = request.form.get('context_window_hours', '24')
        enable_conversation_memory = request.form.get('enable_conversation_memory', 'true')
        
        # Activity logging settings
        activity_logging_enabled = 'activity_logging_enabled' in request.form
        
        # Token pricing settings
        input_token_price_per_1m = request.form.get('input_token_price_per_1m', '0.50')
        output_token_price_per_1m = request.form.get('output_token_price_per_1m', '1.50')
        
        # Currency exchange rates
        ton_price_usd = request.form.get('ton_price_usd', '5.50')
        stars_price_usd = request.form.get('stars_price_usd', '0.013')
        
        # Dashboard settings
        dashboard_host = request.form.get('dashboard_host', '127.0.0.1')
        dashboard_port = request.form.get('dashboard_port', '5000')
        admin_username = request.form.get('admin_username', 'admin')
        admin_password = request.form.get('admin_password', 'admin')
        log_level = request.form.get('log_level', 'INFO')
        
        # Support settings
        support_telegram_username = request.form.get('support_telegram_username', '')
        
        # Update in database
        settings_to_update = {
            'bot_token': bot_token,
            'admin_chat_id': admin_chat_id,
            'ai_api_key': ai_api_key,
            'ai_model': ai_model,
            'ai_base_url': ai_base_url,
            'ton_mainnet_wallet_address': ton_mainnet_wallet_address,
            'ton_testnet_wallet_address': ton_testnet_wallet_address,
            'ton_network_mode': ton_network_mode,
            'webhook_url': webhook_url,
            'bot_active': str(bot_active).lower(),
            'telegram_stars_enabled': str(telegram_stars_enabled).lower(),
            'ton_enabled': str(ton_enabled).lower(),
            'ton_api_key': ton_api_key,
            'free_text_messages': free_text_messages,
            'free_image_messages': free_image_messages,
            'free_video_messages': free_video_messages,
            'referral_system_enabled': str(referral_system_enabled).lower(),
            'referral_text_reward': referral_text_reward,
            'referral_image_reward': referral_image_reward,
            'referral_video_reward': referral_video_reward,
            'max_requests_per_minute': max_requests_per_minute,
            'max_requests_per_hour': max_requests_per_hour,
            'max_image_size': max_image_size,
            'max_video_size': max_video_size,
            'ai_response_timeout': ai_response_timeout,
            'conversation_history_length': conversation_history_length,
            'context_window_hours': context_window_hours,
            'enable_conversation_memory': enable_conversation_memory,
            'activity_logging_enabled': str(activity_logging_enabled).lower(),
            'input_token_price_per_1m': input_token_price_per_1m,
            'output_token_price_per_1m': output_token_price_per_1m,
            'ton_price_usd': ton_price_usd,
            'stars_price_usd': stars_price_usd,
            'dashboard_host': dashboard_host,
            'dashboard_port': dashboard_port,
            'admin_username': admin_username,
            'admin_password': admin_password,
            'log_level': log_level,
            'support_telegram_username': support_telegram_username
        }
        
        for key, value in settings_to_update.items():
            db.update_setting(key, value)
        
        # Also update the specific free message settings using the dedicated method
        db.update_free_message_settings(
            free_text=int(free_text_messages),
            free_image=int(free_image_messages),
            free_video=int(free_video_messages)
        )
        
        flash('Settings updated successfully!')
        return redirect(url_for('settings'))
    
    # Get current settings
    settings = db.get_all_settings()
    return render_template('settings.html', settings=settings)

@app.route('/api/bot/start', methods=['POST'])
@login_required
def start_bot():
    try:
        # Start the bot process
        subprocess.Popen([sys.executable, 'telegram_bot.py'], cwd=os.getcwd())
        db.update_setting('bot_active', 'true')
        return jsonify({'success': True, 'message': 'Bot started successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting bot: {str(e)}'})

@app.route('/api/bot/stop', methods=['POST'])
@login_required
def stop_bot():
    try:
        # This is a simple implementation - in production you'd want better process management
        os.system('taskkill /f /im python.exe')  # Windows
        # os.system('pkill -f telegram_bot.py')  # Linux/Mac
        db.update_setting('bot_active', 'false')
        return jsonify({'success': True, 'message': 'Bot stopped successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping bot: {str(e)}'})

@app.route('/api/stats')
@login_required
def get_stats():
    stats = {
        'total_users': db.get_user_count(),
        'total_transactions': db.get_transaction_count(),
        'total_revenue': db.get_total_revenue(),
        'active_packages': db.get_active_package_count()
    }
    return jsonify(stats)

@app.route('/api/ton_price/update', methods=['POST'])
@login_required
def update_ton_price():
    """Fetch current TON price from API and update the setting"""
    try:
        # Get current TON price using the currency converter
        current_price = currency_converter.get_ton_to_usd_rate()
        
        if current_price and current_price > 0:
            # Update the setting in database
            db.update_setting('ton_price_usd', str(current_price))
            
            return jsonify({
                'success': True, 
                'price': current_price,
                'message': f'TON price updated to ${format_precise_number(current_price)} USD'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to fetch TON price from API'
            })
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating TON price: {str(e)}'
        })

@app.route('/api/venice/balance')
@login_required
def get_venice_balance():
    """API endpoint to get Venice USD balance"""
    try:
        venice_status = get_venice_api_status()
        
        if venice_status.get('error'):
            return jsonify({
                'success': False,
                'balance': '0.00',
                'error': venice_status['error']
            })
        
        balance = venice_status.get('balance_usd', '0.00')
        return jsonify({
            'success': True,
            'balance': balance,
            'status': venice_status.get('status', 'unknown')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'balance': '0.00',
            'error': f'Error fetching Venice balance: {str(e)}'
        })

@app.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found!')
        return redirect(url_for('users'))
    
    user_transactions = db.get_user_transactions(user_id)
    user_usage = db.get_user_usage_history(user_id)
    
    # Get referral information
    referral_stats = db.get_user_referrals(user_id)
    
    # Check if user was referred by someone
    was_referred = len(db.execute_query(
        "SELECT id FROM referrals WHERE referee_id = ?", (user_id,)
    )) > 0
    
    # Get user activity logs
    user_activities = db.get_user_activity_logs(user_id, limit=100)
    
    return render_template('user_detail.html', 
                         user=user, 
                         transactions=user_transactions, 
                         usage=user_usage,
                         referral_stats=referral_stats,
                         was_referred=was_referred,
                         activities=user_activities)

@app.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message_to_user(user_id):
    """Send a message to a specific user via Telegram bot"""
    try:
        # Get the message content from the form
        message = request.form.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'})
        
        # Get bot token from database settings
        bot_token = db.get_setting('bot_token')
        if not bot_token:
            return jsonify({'success': False, 'error': 'Bot token not configured'})
        
        # Import here to avoid circular imports
        import requests
        
        # Send message via Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': user_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=payload)
        result = response.json()
        
        if result.get('ok'):
            # Log the message in database (optional)
            # You could add this to message_history table
            return jsonify({'success': True, 'message': 'Message sent successfully'})
        else:
            error_msg = result.get('description', 'Unknown error')
            return jsonify({'success': False, 'error': f'Failed to send message: {error_msg}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error sending message: {str(e)}'})

@app.route('/bulk_message')
@login_required
def bulk_message():
    """Bulk message sending page"""
    # Get all users for selection
    users = db.get_all_users()
    return render_template('bulk_message.html', users=users)

@app.route('/send_bulk_message', methods=['POST'])
@login_required
def send_bulk_message():
    """Send bulk messages to selected users"""
    try:
        # Get form data
        message = request.form.get('message', '').strip()
        target_type = request.form.get('target_type', 'all')  # 'all', 'premium', 'free', 'selected'
        selected_users = request.form.getlist('selected_users')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'})
        
        # Get bot token from database settings
        bot_token = db.get_setting('bot_token')
        if not bot_token:
            return jsonify({'success': False, 'error': 'Bot token not configured'})
        
        # Get target users based on selection
        if target_type == 'all':
            target_users = db.get_all_users()
        elif target_type == 'premium':
            target_users = [user for user in db.get_all_users() if user.get('is_premium')]
        elif target_type == 'free':
            target_users = [user for user in db.get_all_users() if not user.get('is_premium')]
        elif target_type == 'selected':
            if not selected_users:
                return jsonify({'success': False, 'error': 'No users selected'})
            target_users = [user for user in db.get_all_users() if str(user['user_id']) in selected_users]
        else:
            return jsonify({'success': False, 'error': 'Invalid target type'})
        
        # Import here to avoid circular imports
        import requests
        import time
        
        # Send messages to all target users
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        for user in target_users:
            try:
                payload = {
                    'chat_id': user['user_id'],
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=payload, timeout=10)
                result = response.json()
                
                if result.get('ok'):
                    sent_count += 1
                else:
                    failed_count += 1
                    failed_users.append({
                        'user_id': user['user_id'],
                        'username': user.get('username', 'N/A'),
                        'error': result.get('description', 'Unknown error')
                    })
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    'user_id': user['user_id'],
                    'username': user.get('username', 'N/A'),
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'failed_users': failed_users,
            'total_users': len(target_users)
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error sending bulk message: {str(e)}'})

@app.route('/message_history/<int:message_id>')
@login_required
def message_history_detail(message_id: int):
    """Display a single user's conversation in chat view."""
    conn = db.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mh.*, u.username, u.first_name, u.last_name
        FROM message_history mh
        LEFT JOIN users u ON mh.user_id = u.user_id
        WHERE mh.id = ?
    ''', (message_id,))

    message = cursor.fetchone()
    conn.close()

    if not message:
        flash('Message not found.')
        return redirect(url_for('message_history'))

    user_data = db.get_user(message['user_id']) or {}
    conversation = db.get_user_conversation(message['user_id'])

    return render_template(
        'message_conversation.html',
        conversation=conversation,
        focus_message_id=message_id,
        user=user_data,
        selected_message=message
    )

@app.route('/api/venice/models')
@login_required
def get_venice_models():
    """API endpoint to fetch available Venice models"""
    result = fetch_venice_models()
    return jsonify(result)

def get_venice_api_status():
    """Get Venice API status information"""
    try:
        # Initialize AI handler
        ai_handler = VeniceAPI(db)
        
        # Get Venice account status using the existing method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status = loop.run_until_complete(ai_handler.get_venice_account_status())
            return status
        finally:
            loop.close()
            
    except Exception as e:
        return {
            'error': f'Failed to get Venice API status: {str(e)}',
            'status': 'offline'
        }

@app.route('/statistics')
@login_required
def statistics():
    """Statistics page with comprehensive analytics"""
    try:
        # Get basic stats
        total_users = db.get_total_users()
        total_transactions = db.get_total_transactions()
        payment_stats = db.get_payment_statistics()
        
        # Get USD conversion data
        ton_amount = payment_stats.get('ton', 0)
        stars_amount = payment_stats.get('stars', 0)
        usd_data = currency_converter.get_total_usd_value(ton_amount, stars_amount)
        
        # Get financial overview
        financial_overview = financial_analytics.get_financial_kpis()
        
        # Get detailed analytics
        stats_data = {
            'overview': {
                'total_users': total_users,
                'total_transactions': total_transactions,
                'total_revenue_usd': usd_data['total_usd'],
                'ton_revenue_usd': usd_data['ton_usd'],
                'stars_revenue_usd': usd_data['stars_usd']
            },
            'payment_breakdown': {
                'ton_amount': payment_stats.get('ton', 0),
                'stars_amount': payment_stats.get('stars', 0),
                'ton_percentage': 0,
                'stars_percentage': 0
            },
            'recent_activity': {
                'venice_status': get_venice_api_status()
            },
            'time_based': {
                'daily_stats': get_daily_statistics(),
                'monthly_stats': get_monthly_statistics()
            },
            'exchange_rates': {
                'ton_usd_rate': currency_converter.get_ton_usd_rate(),
                'stars_usd_rate': 0.013,
                'last_updated': currency_converter.get_cache_timestamp()
            }
        }
        
        # Calculate payment method percentages
        total_payments = payment_stats.get('ton', 0) + payment_stats.get('stars', 0)
        if total_payments > 0:
            stats_data['payment_breakdown']['ton_percentage'] = (payment_stats.get('ton', 0) / total_payments) * 100
            stats_data['payment_breakdown']['stars_percentage'] = (payment_stats.get('stars', 0) / total_payments) * 100
        
        return render_template('statistics.html', stats=stats_data, usd_data=usd_data, financial_overview=financial_overview)
        
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/financial_analytics')
@login_required 
def financial_analytics_dashboard():
    """Financial Analytics Dashboard - Revenue, Spending, and Profit Analysis"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get comprehensive financial analysis
        financial_data = financial_analytics.get_net_profit_analysis(start_date, end_date)
        
        # Get KPIs for quick overview
        kpis = financial_analytics.get_financial_kpis()
        
        # Format data for templates
        financial_summary = {
            'total_revenue': financial_data['financial_summary']['total_revenue_usd'],
            'total_spending': financial_data['financial_summary']['total_spending_usd'], 
            'net_profit': financial_data['financial_summary']['net_profit_usd'],
            'profit_margin': financial_data['financial_summary']['profit_margin_percent'],
            'roi': financial_data['financial_summary']['roi_percent'],
            'is_profitable': financial_data['financial_summary']['is_profitable']
        }
        
        # Revenue breakdown
        revenue_breakdown = financial_data['revenue_data']['revenue_by_method']
        
        # Spending breakdown  
        spending_breakdown = financial_data['spending_data']['spending_by_type']
        
        # Daily trends for charts
        daily_trends = financial_data['daily_profit_trends']
        
        return render_template('financial_analytics.html',
                             financial_summary=financial_summary,
                             revenue_breakdown=revenue_breakdown,
                             spending_breakdown=spending_breakdown,
                             daily_trends=daily_trends,
                             kpis=kpis,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        flash(f'Error loading financial analytics: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/message_history')
@login_required
def message_history():
    """Message history page with Venice API metadata"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Messages per page
        
        # Get paginated message history
        offset = (page - 1) * per_page
        
        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM message_history')
        total_messages = cursor.fetchone()[0]
        
        # Get paginated messages with user info
        cursor.execute('''
            SELECT mh.*, u.username, u.first_name 
            FROM message_history mh
            LEFT JOIN users u ON mh.user_id = u.user_id
            ORDER BY mh.timestamp DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        messages = cursor.fetchall()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_messages + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Get summary statistics
        summary_stats = get_message_history_stats()
        
        start_index = offset + 1 if total_messages else 0
        end_index = min(offset + per_page, total_messages)
        return render_template(
            'message_history.html',
            messages=messages,
            current_page=page,
            total_pages=total_pages,
            total_messages=total_messages,
            has_prev=has_prev,
            has_next=has_next,
            prev_num=page - 1 if has_prev else None,
            next_num=page + 1 if has_next else None,
            stats=summary_stats,
            start_index=start_index,
            end_index=end_index,
            per_page=per_page
        )
        
    except Exception as e:
        flash(f'Error loading message history: {str(e)}')
        return redirect(url_for('dashboard'))


@app.route('/message_history/conversation/<int:user_id>')
@login_required
def message_history_conversation(user_id: int):
    """Conversation view for a specific user."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT username, first_name, last_name FROM users WHERE user_id = ?',
            (user_id,)
        )
        user_row = cursor.fetchone()

        cursor.execute(
            'SELECT COUNT(*) FROM message_history WHERE user_id = ?',
            (user_id,)
        )
        total_messages = cursor.fetchone()[0]

        cursor.execute(
            '''SELECT *
               FROM message_history
               WHERE user_id = ?
               ORDER BY timestamp ASC
               LIMIT ? OFFSET ?''',
            (user_id, per_page, offset)
        )
        messages = cursor.fetchall()

        cursor.execute(
            '''SELECT COUNT(*) AS cnt, user_message IS NOT NULL AS is_user
               FROM message_history
               WHERE user_id = ?
               GROUP BY is_user''',
            (user_id,)
        )
        role_counts = {row[1]: row[0] for row in cursor.fetchall()}

        cursor.execute(
            '''SELECT SUM(prompt_tokens) AS prompt_sum,
                      SUM(completion_tokens) AS completion_sum,
                      SUM(total_tokens) AS total_sum,
                      SUM(cost) AS total_cost
               FROM message_history
               WHERE user_id = ?''',
            (user_id,)
        )
        token_stats = cursor.fetchone() or (0, 0, 0, 0)

        conn.close()

        total_pages = (total_messages + per_page - 1) // per_page if total_messages else 0
        page = max(1, min(page, total_pages or 1))
        has_prev = page > 1
        has_next = page < (total_pages or 0)
        start_index = offset + 1 if total_messages else 0
        end_index = min(offset + per_page, total_messages)

        conversation_stats = {
            'total_messages': total_messages,
            'user_messages': role_counts.get(1, 0),
            'ai_messages': role_counts.get(0, 0),
            'prompt_tokens': token_stats[0] or 0,
            'completion_tokens': token_stats[1] or 0,
            'total_tokens': token_stats[2] or 0,
            'total_cost': token_stats[3] or 0,
        }

        user_display_name = None
        if user_row:
            name_parts = [part for part in (user_row['first_name'], user_row['last_name']) if part]
            user_display_name = ' '.join(name_parts) or user_row['username'] or str(user_id)
        else:
            user_display_name = str(user_id)

        return render_template(
            'conversation_detail.html',
            user_id=user_id,
            user_display_name=user_display_name,
            username=user_row['username'] if user_row else None,
            messages=messages,
            current_page=page,
            total_pages=total_pages,
            has_prev=has_prev,
            has_next=has_next,
            prev_num=page - 1 if has_prev else None,
            next_num=page + 1 if has_next else None,
            start_index=start_index,
            end_index=end_index,
            total_messages_count=total_messages,
            stats=conversation_stats
        )

    except Exception as e:
        flash(f'Error loading conversation history: {str(e)}')
        return redirect(url_for('message_history'))

def get_message_history_stats():
    """Get summary statistics for message history"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Total messages by type
        cursor.execute('''
            SELECT message_type, COUNT(*) as count
            FROM message_history 
            GROUP BY message_type
        ''')
        message_types = dict(cursor.fetchall())
        
        # Total tokens used and cost
        cursor.execute('''
            SELECT 
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens_sum,
                SUM(cost) as total_cost_usd
            FROM message_history 
            WHERE total_tokens > 0
        ''')
        token_stats = cursor.fetchone()
        
        # Most active users
        cursor.execute('''
            SELECT u.username, u.first_name, COUNT(*) as message_count
            FROM message_history mh
            LEFT JOIN users u ON mh.user_id = u.user_id
            GROUP BY mh.user_id
            ORDER BY message_count DESC
            LIMIT 5
        ''')
        top_users = cursor.fetchall()
        
        # Recent activity (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) as recent_count
            FROM message_history 
            WHERE timestamp >= datetime('now', '-24 hours')
        ''')
        recent_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'message_types': message_types,
            'token_stats': {
                'prompt_tokens': token_stats[0] or 0,
                'completion_tokens': token_stats[1] or 0,
                'total_tokens': token_stats[2] or 0,
                'total_cost': token_stats[3] or 0,
                'input_cost': 0,  # Could calculate separately if needed
                'output_cost': 0  # Could calculate separately if needed
            },
            'top_users': top_users,
            'recent_activity': recent_activity
        }
        
    except Exception as e:
        print(f"Error getting message history stats: {e}")
        return {
            'message_types': {},
            'token_stats': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'total_cost': 0, 'input_cost': 0, 'output_cost': 0},
            'top_users': [],
            'recent_activity': 0
        }

@app.route('/api/venice_details/<int:message_id>')
@login_required
def get_venice_details(message_id):
    """Get Venice API details for a specific message"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT venice_parameters, full_response_json
            FROM message_history 
            WHERE id = ?
        ''', (message_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            venice_params = None
            full_response = None
            
            # Parse Venice parameters
            if result[0]:
                try:
                    venice_params = json.loads(result[0])
                except json.JSONDecodeError:
                    venice_params = {"error": "Invalid JSON format"}
            
            # Parse full response
            if result[1]:
                try:
                    full_response = json.loads(result[1])
                except json.JSONDecodeError:
                    full_response = {"error": "Invalid JSON format"}
            
            return jsonify({
                'success': True,
                'venice_parameters': venice_params,
                'full_response': full_response
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_daily_statistics():
    """Get daily statistics for the last 30 days"""
    try:
        query = """
        SELECT 
            DATE(created_date) as date,
            COUNT(*) as transaction_count,
            SUM(CASE WHEN payment_method = 'ton' THEN amount ELSE 0 END) as ton_amount,
            SUM(CASE WHEN payment_method = 'stars' THEN amount ELSE 0 END) as stars_amount
        FROM transactions 
        WHERE created_date >= date('now', '-30 days')
        GROUP BY DATE(created_date)
        ORDER BY date DESC
        """
        return db.execute_query(query)
    except Exception as e:
        logging.error(f"Error getting daily statistics: {e}")
        return []

def get_monthly_statistics():
    """Get monthly statistics for the last 12 months"""
    try:
        query = """
        SELECT 
            strftime('%Y-%m', created_date) as month,
            COUNT(*) as transaction_count,
            SUM(CASE WHEN payment_method = 'ton' THEN amount ELSE 0 END) as ton_amount,
            SUM(CASE WHEN payment_method = 'stars' THEN amount ELSE 0 END) as stars_amount
        FROM transactions 
        WHERE created_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', created_date)
        ORDER BY month DESC
        """
        return db.execute_query(query)
    except Exception as e:
        logging.error(f"Error getting monthly statistics: {e}")
        return []

if __name__ == '__main__':
    # Initialize database
    db.init_database()
    
    # Create default admin settings if they don't exist
    if not db.get_setting('bot_token'):
        db.update_setting('bot_token', '')
        db.update_setting('venice_inference_key', '')
        db.update_setting('ai_model', 'venice-uncensored')
        db.update_setting('ton_wallet', '')
        db.update_setting('webhook_url', '')
        db.update_setting('bot_active', 'false')
    
    app.run(debug=True, host='0.0.0.0', port=5000)