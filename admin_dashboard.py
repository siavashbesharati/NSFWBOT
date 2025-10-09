from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import Database
import json
import os
from datetime import datetime
import subprocess
import sys
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
db = Database()

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
    total_revenue = db.get_total_revenue()
    
    # Get recent users
    recent_users = db.get_recent_users(10)
    
    # Get system settings
    settings = db.get_all_settings()
    
    return render_template('dashboard.html', 
                         total_users=total_users,
                         total_transactions=total_transactions,
                         total_revenue=total_revenue,
                         recent_users=recent_users,
                         settings=settings)

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
    
    return render_template('payments.html', 
                         payment_methods=payment_stats['payment_methods'],
                         recent_payments=payment_stats['recent_payments'],
                         total_transactions=payment_stats['total_transactions'],
                         total_revenue=payment_stats['total_revenue'],
                         paying_users=payment_stats['paying_users'])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update basic settings
        bot_token = request.form['bot_token']
        openrouter_api_key = request.form['openrouter_api_key']
        openrouter_model = request.form['openrouter_model']
        ton_wallet = request.form['ton_wallet']
        webhook_url = request.form['webhook_url']
        simulation_mode = 'simulation_mode' in request.form
        bot_active = 'bot_active' in request.form
        
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
        
        # Update in database
        settings_to_update = {
            'bot_token': bot_token,
            'openrouter_api_key': openrouter_api_key,
            'openrouter_model': openrouter_model,
            'ton_wallet': ton_wallet,
            'webhook_url': webhook_url,
            'simulation_mode': str(simulation_mode).lower(),
            'bot_active': str(bot_active).lower(),
            'free_text_messages': free_text_messages,
            'free_image_messages': free_image_messages,
            'free_video_messages': free_video_messages,
            'max_requests_per_minute': max_requests_per_minute,
            'max_requests_per_hour': max_requests_per_hour,
            'max_image_size': max_image_size,
            'max_video_size': max_video_size,
            'ai_response_timeout': ai_response_timeout
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

@app.route('/api/openrouter/models')
@login_required
def get_openrouter_models():
    """API endpoint to fetch available OpenRouter models"""
    result = fetch_openrouter_models()
    return jsonify(result)

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    
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