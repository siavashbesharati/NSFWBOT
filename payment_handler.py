import asyncio
import logging
from typing import Optional, Dict, Any
import json
import aiohttp
import time
from config import Config
from database import Database

class PaymentHandler:
    def __init__(self, db: Database):
        self.db = db
        self.ton_network_mode = self.db.get_setting('ton_network_mode', 'sandbox')
        self.ton_testnet = self.ton_network_mode == 'sandbox'
        
        # TON API endpoints
        self.ton_api_endpoint = "https://testnet.toncenter.com/api/v2/" if self.ton_testnet else "https://toncenter.com/api/v2/"
        self.ton_api_key = self.db.get_setting('ton_api_key', '')  # Optional API key for higher limits
        
    def get_ton_wallet_address(self) -> str:
        """Get appropriate TON wallet address based on network mode"""
        if self.ton_network_mode == 'sandbox':
            return self.db.get_setting('ton_testnet_wallet_address', '')
        else:
            return self.db.get_setting('ton_mainnet_wallet_address', '')
        
    async def create_stars_payment(self, user_id: int, package_id: int, amount: int) -> Dict[str, Any]:
        """Create Telegram Stars payment"""
        try:
            package = self.db.get_package(package_id)
            if not package:
                return {"success": False, "error": "Package not found"}
            
            # Real Telegram Stars payment
            transaction_id = self.db.create_transaction(
                user_id, package_id, "stars", amount
            )
            
            # Create payment invoice (this would integrate with Telegram's payment API)
            payment_data = {
                "provider_token": "",  # Empty for Telegram Stars
                "currency": "XTR",  # Telegram Stars currency code
                "prices": [{"label": package['name'], "amount": amount}],
                "title": f"Package: {package['name']}",
                "description": f"{package['description']}\n" +
                              f"📝 {package['text_count']} text messages\n" +
                              f"🖼️ {package['image_count']} image messages\n" +
                              f"🎥 {package['video_count']} video messages",
                "payload": json.dumps({
                    "transaction_id": transaction_id,
                    "package_id": package_id,
                    "user_id": user_id
                }),
                "need_email": False,
                "need_phone_number": False,
                "is_flexible": False
            }
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "payment_data": payment_data,
                "message": f"💫 Payment created for {amount} Telegram Stars"
            }
            
        except Exception as e:
            logging.error(f"Error creating Stars payment: {str(e)}")
            return {"success": False, "error": "Failed to create payment"}
    
    async def create_ton_payment(self, user_id: int, package_id: int, amount: float) -> Dict[str, Any]:
        """Create TON payment"""
        try:
            package = self.db.get_package(package_id)
            if not package:
                return {"success": False, "error": "Package not found"}
            
            # Create TON payment transaction
            transaction_id = self.db.create_transaction(
                user_id, package_id, "ton", amount
            )
            
            # Generate TON payment URL
            payment_comment = f"Payment_{transaction_id}_{user_id}"
            ton_wallet_address = self.get_ton_wallet_address()
            
            # Convert TON to nanoTON for the payment URL (1 TON = 1,000,000,000 nanoTON)
            ton_amount_nanotone = int(amount * 1000000000)
            
            # Create payment URL (TON network is detected automatically by address)
            payment_url = (
                f"https://app.tonkeeper.com/transfer/"
                f"{ton_wallet_address}?"
                f"amount={ton_amount_nanotone}&"
                f"text={payment_comment}"
            )
            
            # Network info for display
            network_info = "🧪 TESTNET" if self.ton_testnet else "🌐 MAINNET"
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "payment_url": payment_url,
                "ton_address": ton_wallet_address,
                "amount": amount,
                "comment": payment_comment,
                "network": network_info,
                "message": f"💎 TON payment created for {amount} TON ({network_info})"
            }
            
        except Exception as e:
            logging.error(f"Error creating TON payment: {str(e)}")
            return {"success": False, "error": "Failed to create payment"}
    
    async def verify_stars_payment(self, transaction_id: int, telegram_payment_id: str) -> bool:
        """Verify Telegram Stars payment"""
        try:
            # In a real implementation, you would verify with Telegram's API
            # For now, we'll mark as completed when called
            self.db.complete_transaction(transaction_id, telegram_payment_id)
            
            # Add credits to user
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, package_id FROM transactions WHERE id = ?
            ''', (transaction_id,))
            
            result = cursor.fetchone()
            if result:
                user_id, package_id = result
                package = self.db.get_package(package_id)
                if package:
                    self.db.add_message_credits(
                        user_id,
                        package['text_count'],
                        package['image_count'],
                        package['video_count']
                    )
            
            conn.close()
            return True
            
        except Exception as e:
            logging.error(f"Error verifying Stars payment: {str(e)}")
            return False
    
    async def verify_ton_payment(self, transaction_id: int) -> bool:
        """Verify TON payment by checking blockchain"""
        try:
            logging.info(f"🔍 Starting TON payment verification for transaction {transaction_id}")
            
            # Get transaction details
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, package_id, amount, created_date FROM transactions 
                WHERE id = ? AND status = 'pending'
            ''', (transaction_id,))
            
            result = cursor.fetchone()
            if not result:
                logging.warning(f"❌ Transaction {transaction_id} not found or not pending")
                conn.close()
                return False
            
            user_id, package_id, expected_amount, created_date = result
            conn.close()
            
            logging.info(f"📋 Transaction details: user_id={user_id}, package_id={package_id}, amount={expected_amount} TON, created={created_date}")
            
            # Verify payment using TON API
            payment_comment = f"Payment_{transaction_id}_{user_id}"
            ton_wallet_address = self.get_ton_wallet_address()
            
            logging.info(f"🔍 Checking blockchain for payment:")
            logging.info(f"   - Wallet: {ton_wallet_address}")
            logging.info(f"   - Expected amount: {expected_amount} TON")
            logging.info(f"   - Expected comment: {payment_comment}")
            logging.info(f"   - Network: {'TESTNET' if self.ton_testnet else 'MAINNET'}")
            
            if await self._check_ton_transaction(ton_wallet_address, expected_amount, payment_comment, created_date):
                # Payment verified, complete transaction
                logging.info(f"✅ Payment verified! Completing transaction {transaction_id}")
                self.db.complete_transaction(transaction_id, f"ton_verified_{int(time.time())}")
                
                # Add credits to user
                package = self.db.get_package(package_id)
                if package:
                    logging.info(f"💰 Adding credits to user {user_id}: {package['text_count']} text, {package['image_count']} image, {package['video_count']} video")
                    self.db.add_message_credits(
                        user_id,
                        package['text_count'],
                        package['image_count'],
                        package['video_count']
                    )
                
                logging.info(f"🎉 TON payment verified and completed for transaction {transaction_id}")
                return True
            else:
                logging.warning(f"❌ Payment not found on blockchain for transaction {transaction_id}")
            
            return False
            
        except Exception as e:
            logging.error(f"💥 Error verifying TON payment {transaction_id}: {str(e)}")
            return False
    
    async def _check_ton_transaction(self, wallet_address: str, expected_amount: float, expected_comment: str, since_timestamp: str) -> bool:
        """Check TON blockchain for specific transaction"""
        try:
            # Convert timestamp to Unix time for API
            import datetime
            since_dt = datetime.datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
            since_unix = int(since_dt.timestamp())
            
            logging.info(f"🌐 Checking TON API for transactions since {since_timestamp} (unix: {since_unix})")
            
            # Build API request URL
            url = f"{self.ton_api_endpoint}getTransactions"
            params = {
                'address': wallet_address,
                'limit': 100,  # Check last 100 transactions
                'to_lt': 0,
                'archival': 'true'  # String instead of boolean
            }
            
            if self.ton_api_key and not self.ton_testnet:
                # Only use API key for mainnet (testnet API key may cause "Network not allowed")
                params['api_key'] = self.ton_api_key
                logging.info(f"🔑 Using API key for TON requests (mainnet)")
            else:
                if self.ton_testnet:
                    logging.info(f"⚠️ Not using API key for testnet (may cause network restrictions)")
                else:
                    logging.info(f"⚠️ No API key configured - using default limits")
            
            logging.info(f"📡 API Request: {url}")
            logging.info(f"📡 Parameters: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    logging.info(f"📡 API Response Status: {response.status}")
                    
                    if response.status != 200:
                        logging.error(f"❌ TON API error: {response.status}")
                        response_text = await response.text()
                        logging.error(f"❌ Response body: {response_text}")
                        return False
                    
                    data = await response.json()
                    logging.info(f"📡 API Response OK: {data.get('ok', False)}")
                    
                    if not data.get('ok'):
                        logging.error(f"❌ TON API response not ok: {data}")
                        return False
                    
                    transactions = data.get('result', [])
                    logging.info(f"📊 Found {len(transactions)} transactions to check")
                    
                    # Check each transaction
                    for i, tx in enumerate(transactions):
                        tx_time = tx.get('utime', 0)
                        logging.info(f"🔍 Checking transaction {i+1}/{len(transactions)} (time: {tx_time}, since: {since_unix})")
                        
                        # Skip if transaction is older than our payment
                        if tx_time < since_unix:
                            logging.info(f"⏭️ Skipping old transaction: {tx_time} < {since_unix}")
                            continue
                        
                        logging.info(f"⏰ Transaction is recent enough: {tx_time} >= {since_unix}")
                        
                        # Check incoming messages
                        in_msg = tx.get('in_msg', {})
                        if not in_msg:
                            logging.info(f"⏭️ No incoming message in this transaction")
                            continue
                        
                        logging.info(f"📨 Found incoming message in transaction")
                        
                        # Check amount (convert from nanoTON)
                        value = int(in_msg.get('value', 0))
                        amount_ton = value / 1000000000
                        
                        logging.info(f"💰 Transaction amount: {value} nanoTON = {amount_ton} TON")
                        logging.info(f"💰 Expected amount: {expected_amount} TON")
                        logging.info(f"💰 Difference: {abs(amount_ton - expected_amount)} (tolerance: 0.001)")
                        
                        # Check if amount matches (with small tolerance for fees)
                        if abs(amount_ton - expected_amount) < 0.001:
                            logging.info(f"✅ Amount matches! {amount_ton} ≈ {expected_amount}")
                            
                            # Check comment/message
                            message = in_msg.get('message', '')
                            logging.info(f"💬 Transaction message: '{message}'")
                            logging.info(f"💬 Expected comment: '{expected_comment}'")
                            
                            if expected_comment in message:
                                logging.info(f"🎉 PAYMENT FOUND! Amount: {amount_ton} TON, Comment: '{message}'")
                                return True
                            else:
                                logging.warning(f"❌ Comment doesn't match: '{message}' does not contain '{expected_comment}'")
                        else:
                            logging.info(f"❌ Amount doesn't match: {amount_ton} vs {expected_amount} (diff: {abs(amount_ton - expected_amount)})")
            
            logging.warning(f"❌ No matching transaction found after checking {len(transactions)} transactions")
            return False
            
        except Exception as e:
            logging.error(f"💥 Error checking TON transaction: {str(e)}")
            import traceback
            logging.error(f"💥 Full traceback: {traceback.format_exc()}")
            return False
    
    async def check_pending_payments(self):
        """Background task to check pending payments"""
        try:
            logging.info(f"🔄 Starting background check for pending payments")
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get pending TON transactions older than 5 minutes
            cursor.execute('''
                SELECT id, user_id, package_id, amount FROM transactions 
                WHERE status = 'pending' 
                AND payment_method = 'ton' 
                AND created_date < datetime('now', '-5 minutes')
            ''')
            
            pending_transactions = cursor.fetchall()
            conn.close()
            
            logging.info(f"📋 Found {len(pending_transactions)} pending TON transactions to check")
            
            for transaction in pending_transactions:
                transaction_id, user_id, package_id, amount = transaction
                logging.info(f"🔍 Checking pending transaction {transaction_id} for user {user_id} ({amount} TON)")
                
                if await self.verify_ton_payment(transaction_id):
                    logging.info(f"✅ TON payment verified for transaction {transaction_id}")
                else:
                    logging.info(f"⏳ TON payment still pending for transaction {transaction_id}")
            
            logging.info(f"🔄 Background payment check completed")
            
        except Exception as e:
            logging.error(f"💥 Error checking pending payments: {str(e)}")
            import traceback
            logging.error(f"💥 Full traceback: {traceback.format_exc()}")
    
    def get_payment_status(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get payment status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, payment_method, amount, created_date, completed_date 
                FROM transactions WHERE id = ?
            ''', (transaction_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status, payment_method, amount, created_date, completed_date = result
                return {
                    "status": status,
                    "payment_method": payment_method,
                    "amount": amount,
                    "created_date": created_date,
                    "completed_date": completed_date
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting payment status: {str(e)}")
            return None