from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import Database
from currency_converter import currency_converter
import json
import os
from datetime import datetime
import subprocess
import sys
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
db = Database()

# Custom template filter for currency formatting
@app.template_filter('currency')
def format_currency(value):
    """Format currency with maximum 2 decimal places, truncating trailing zeros"""
    if value is None or value == 0:
        return "0"
    
    # Format with 2 decimal places
    formatted = "{:.2f}".format(float(value))
    
    # Remove trailing zeros and decimal point if needed
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    
    return formatted

# Custom template filter for number formatting
@app.template_filter('number_format')
def format_number(value):
    """Format numbers with thousands separators"""
    if value is None:
        return "0"
    
    try:
        return "{:,}".format(int(value))
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

def fetch_openrouter_models():
    """Fetch available models from OpenRouter API"""
    try:
        url = "https://openrouter.ai/api/v1/models"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model in data.get('data', []):
                models.append({
                    'id': model.get('id', ''),
                    'name': model.get('name', ''),
                    'description': model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': model.get('pricing', {}),
                    'input_modalities': model.get('architecture', {}).get('input_modalities', []),
                    'output_modalities': model.get('architecture', {}).get('output_modalities', [])
                })
            
            return {
                'success': True,
                'models': models,
                'total': len(models)
            }
        else:
            return {
                'success': False,
                'error': f'API returned status code: {response.status_code}'
            }
            
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }
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
    
    users_data = db.get_users_paginated(page, per_page)
    return render_template('users.html', users=users_data)

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
        ton_wallet_address = request.form['ton_wallet']
        webhook_url = request.form['webhook_url']
        simulation_mode = 'simulation_mode' in request.form
        bot_active = 'bot_active' in request.form
        
        # Payment method settings
        telegram_stars_enabled = 'telegram_stars_enabled' in request.form
        ton_enabled = 'ton_enabled' in request.form
        
        # Free messages and rate limiting settings
        free_text_messages = request.form.get('free_text_messages', '5')
        free_image_messages = request.form.get('free_image_messages', '2')
        free_video_messages = request.form.get('free_video_messages', '1')
        max_requests_per_minute = request.form.get('max_requests_per_minute', '20')
        max_requests_per_hour = request.form.get('max_requests_per_hour', '100')
        
        # Advanced settings
        max_image_size = request.form.get('max_image_size', '10')
        max_video_size = request.form.get('max_video_size', '50')
        ai_response_timeout = request.form.get('ai_response_timeout', '30')
        
        # Conversation settings
        conversation_history_length = request.form.get('conversation_history_length', '10')
        context_window_hours = request.form.get('context_window_hours', '24')
        enable_conversation_memory = request.form.get('enable_conversation_memory', 'true')
        
        # Dashboard settings
        dashboard_host = request.form.get('dashboard_host', '127.0.0.1')
        dashboard_port = request.form.get('dashboard_port', '5000')
        admin_username = request.form.get('admin_username', 'admin')
        admin_password = request.form.get('admin_password', 'admin')
        log_level = request.form.get('log_level', 'INFO')
        
        # Update in database
        settings_to_update = {
            'bot_token': bot_token,
            'admin_chat_id': admin_chat_id,
            'ai_api_key': ai_api_key,
            'ai_model': ai_model,
            'ai_base_url': ai_base_url,
            'ton_wallet_address': ton_wallet_address,
            'webhook_url': webhook_url,
            'simulation_mode': str(simulation_mode).lower(),
            'bot_active': str(bot_active).lower(),
            'telegram_stars_enabled': str(telegram_stars_enabled).lower(),
            'ton_enabled': str(ton_enabled).lower(),
            'free_text_messages': free_text_messages,
            'free_image_messages': free_image_messages,
            'free_video_messages': free_video_messages,
            'max_requests_per_minute': max_requests_per_minute,
            'max_requests_per_hour': max_requests_per_hour,
            'max_image_size': max_image_size,
            'max_video_size': max_video_size,
            'ai_response_timeout': ai_response_timeout,
            'conversation_history_length': conversation_history_length,
            'context_window_hours': context_window_hours,
            'enable_conversation_memory': enable_conversation_memory,
            'dashboard_host': dashboard_host,
            'dashboard_port': dashboard_port,
            'admin_username': admin_username,
            'admin_password': admin_password,
            'log_level': log_level
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

@app.route('/api/simulation/toggle', methods=['POST'])
@login_required
def toggle_simulation():
    current_mode = db.get_setting('simulation_mode')
    new_mode = 'false' if current_mode == 'true' else 'true'
    db.update_setting('simulation_mode', new_mode)
    
    mode_text = 'enabled' if new_mode == 'true' else 'disabled'
    return jsonify({'success': True, 'message': f'Simulation mode {mode_text}!'})

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

@app.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found!')
        return redirect(url_for('users'))
    
    user_transactions = db.get_user_transactions(user_id)
    user_usage = db.get_user_usage_history(user_id)
    
    return render_template('user_detail.html', 
                         user=user, 
                         transactions=user_transactions, 
                         usage=user_usage)

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

@app.route('/api/openrouter/models')
@login_required
def get_openrouter_models():
    """API endpoint to fetch available OpenRouter models"""
    result = fetch_openrouter_models()
    return jsonify(result)

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
                'recent_users': db.get_recent_users(10),
                'recent_transactions': db.get_recent_transactions(10)
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
        
        return render_template('statistics.html', stats=stats_data, usd_data=usd_data)
        
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}')
        return redirect(url_for('dashboard'))

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
        db.update_setting('openrouter_api_key', '')
        db.update_setting('openrouter_model', 'openai/gpt-3.5-turbo')
        db.update_setting('ton_wallet', '')
        db.update_setting('webhook_url', '')
        db.update_setting('simulation_mode', 'true')
        db.update_setting('bot_active', 'false')
    
    app.run(debug=True, host='0.0.0.0', port=5000)