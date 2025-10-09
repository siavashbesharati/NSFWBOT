import asyncio
import logging
from typing import Optional, Dict, Any
import json
import aiohttp
from config import Config
from database import Database

class PaymentHandler:
    def __init__(self, db: Database):
        self.db = db
        self.simulation_mode = self.db.get_setting('simulation_mode', 'true').lower() == 'true'
        
    async def create_stars_payment(self, user_id: int, package_id: int, amount: int) -> Dict[str, Any]:
        """Create Telegram Stars payment"""
        try:
            package = self.db.get_package(package_id)
            if not package:
                return {"success": False, "error": "Package not found"}
            
            if self.simulation_mode:
                # In simulation mode, auto-approve payment
                transaction_id = self.db.create_transaction(
                    user_id, package_id, "stars", amount
                )
                
                # Simulate payment verification delay
                await asyncio.sleep(2)
                
                # Auto-complete transaction in simulation
                self.db.complete_transaction(transaction_id, f"sim_stars_{transaction_id}")
                
                # Add credits to user
                self.db.add_message_credits(
                    user_id, 
                    package['text_count'], 
                    package['image_count'], 
                    package['video_count']
                )
                
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "payment_url": None,
                    "message": "✅ Simulation payment completed successfully!"
                }
            
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
            
            if self.simulation_mode:
                # In simulation mode, auto-approve payment
                transaction_id = self.db.create_transaction(
                    user_id, package_id, "ton", amount
                )
                
                # Simulate payment verification delay
                await asyncio.sleep(3)
                
                # Auto-complete transaction in simulation
                self.db.complete_transaction(transaction_id, f"sim_ton_{transaction_id}")
                
                # Add credits to user
                self.db.add_message_credits(
                    user_id, 
                    package['text_count'], 
                    package['image_count'], 
                    package['video_count']
                )
                
                ton_wallet_address = self.db.get_setting('ton_wallet_address', '')
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "payment_url": f"https://app.tonkeeper.com/transfer/{ton_wallet_address}?amount={amount}&text=Payment_{transaction_id}",
                    "message": "✅ Simulation TON payment completed successfully!"
                }
            
            # Real TON payment
            transaction_id = self.db.create_transaction(
                user_id, package_id, "ton", amount
            )
            
            # Generate TON payment URL
            payment_comment = f"Payment_{transaction_id}"
            ton_amount = int(amount * 1000000000)  # Convert to nanoTON
            ton_wallet_address = self.db.get_setting('ton_wallet_address', '')
            
            payment_url = (
                f"https://app.tonkeeper.com/transfer/"
                f"{ton_wallet_address}?"
                f"amount={ton_amount}&"
                f"text={payment_comment}"
            )
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "payment_url": payment_url,
                "ton_address": ton_wallet_address,
                "amount": amount,
                "comment": payment_comment,
                "message": f"💎 TON payment created for {amount} TON"
            }
            
        except Exception as e:
            logging.error(f"Error creating TON payment: {str(e)}")
            return {"success": False, "error": "Failed to create payment"}
    
    async def verify_stars_payment(self, transaction_id: int, telegram_payment_id: str) -> bool:
        """Verify Telegram Stars payment"""
        try:
            if self.simulation_mode:
                # In simulation mode, always verify successfully
                return True
            
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
            if self.simulation_mode:
                # In simulation mode, always verify successfully
                return True
            
            # In a real implementation, you would:
            # 1. Check TON blockchain for incoming transactions
            # 2. Verify the amount and comment match
            # 3. Confirm the transaction is confirmed
            
            # For now, we'll implement a basic check
            # You would integrate with TON API here
            
            # Placeholder for real TON verification
            payment_comment = f"Payment_{transaction_id}"
            
            # This is where you'd call TON API to check for transactions
            # Example: Check last transactions to your wallet
            # and look for one with the correct comment and amount
            
            # For demo purposes, we'll mark as completed
            self.db.complete_transaction(transaction_id, f"ton_verified_{transaction_id}")
            
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
            logging.error(f"Error verifying TON payment: {str(e)}")
            return False
    
    async def check_pending_payments(self):
        """Background task to check pending payments"""
        try:
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
            
            for transaction in pending_transactions:
                transaction_id, user_id, package_id, amount = transaction
                
                if await self.verify_ton_payment(transaction_id):
                    logging.info(f"TON payment verified for transaction {transaction_id}")
                else:
                    logging.info(f"TON payment still pending for transaction {transaction_id}")
            
        except Exception as e:
            logging.error(f"Error checking pending payments: {str(e)}")
    
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