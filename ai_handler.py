import requests
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any

class OpenRouterAPI:
    def __init__(self, database=None):
        self.db = database
        # Get settings from database if available, otherwise use empty defaults
        if self.db:
            self.api_key = self.db.get_setting('openrouter_api_key', '')
            self.model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.base_url = self.db.get_setting('openrouter_base_url', 'https://openrouter.ai/api/v1')
        else:
            # No database available, use empty defaults
            self.api_key = ''
            self.model = 'openai/gpt-3.5-turbo'
            self.base_url = 'https://openrouter.ai/api/v1'
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://telegram.org",
            "X-Title": "Telegram NSFW Bot"
        }
    
    def refresh_settings(self):
        """Refresh API settings from database"""
        if self.db:
            self.api_key = self.db.get_setting('openrouter_api_key', '')
            self.model = self.db.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            self.base_url = self.db.get_setting('openrouter_base_url', 'https://openrouter.ai/api/v1')
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def generate_text_response(self, user_message: str, user_context: str = None, conversation_history: list = None) -> str:
        """Generate AI text response using OpenRouter API with conversation context"""
        try:
            # Refresh settings from database
            self.refresh_settings()
            
            # Check if API key is available
            if not self.api_key:
                print("❌ OpenRouter API key not configured in database")
                return "Sorry, the AI service is not properly configured. Please contact the administrator."
            system_prompt = """You are a helpful AI assistant in a Telegram bot. 
            Respond naturally and helpfully to user messages. Keep responses concise but informative.
            You can handle various topics but maintain appropriate boundaries.
            Use the conversation history to provide contextual and coherent responses."""
            
            if user_context:
                system_prompt += f"\n\nUser context: {user_context}"
            
            # Build messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                for entry in conversation_history:
                    # Handle sqlite3.Row objects - use column names directly
                    user_msg = entry['user_message'] if entry['user_message'] else None
                    bot_resp = entry['bot_response'] if entry['bot_response'] else None
                    
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            # Log the request for debugging
            print(f"🔍 OpenRouter API Request:")
            print(f"   URL: {self.base_url}/chat/completions")
            print(f"   Model: {self.model}")
            print(f"   Messages count: {len(messages)}")
            print(f"   Request data: {data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=30
                ) as response:
                    # Log the response status
                    print(f"📡 OpenRouter API Response: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ API Success: {result}")
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        print(f"❌ OpenRouter API error: {response.status} - {error_text}")
                        return "Sorry, I'm having trouble generating a response right now. Please try again later."
        
        except asyncio.TimeoutError:
            return "Sorry, the response took too long to generate. Please try again."
        except Exception as e:
            print(f"Error in generate_text_response: {str(e)}")
            return "Sorry, I encountered an error while generating a response. Please try again."
    
    async def generate_image_response(self, user_message: str, image_data: bytes = None, conversation_history: list = None) -> str:
        """Generate AI response to an image using OpenRouter API with vision model"""
        try:
            # Refresh settings from database
            self.refresh_settings()
            
            # Check if API key is available
            if not self.api_key:
                print("❌ OpenRouter API key not configured in database")
                return "Sorry, the AI service is not properly configured. Please contact the administrator."
            # For image analysis, we'll use a vision-capable model
            vision_model = "openai/gpt-4-vision-preview"
            
            messages = [
                {
                    "role": "system", 
                    "content": "You are an AI assistant that can analyze images. Describe what you see in the image and respond helpfully to any questions about it. Use conversation history to provide contextual responses."
                }
            ]
            
            # Add conversation history (text only, as vision models typically don't support image history)
            if conversation_history:
                context_summary = "Recent conversation context: "
                for entry in conversation_history[-3:]:  # Last 3 exchanges for context
                    user_msg = entry['user_message'] if entry['user_message'] else ""
                    bot_resp = entry['bot_response'] if entry['bot_response'] else ""
                    if user_msg and bot_resp:
                        context_summary += f"User: {user_msg[:100]}... Bot: {bot_resp[:100]}... "
                messages[0]["content"] += f"\n\n{context_summary}"
            
            if image_data:
                # Convert image to base64 for API
                import base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message if user_message else "What do you see in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": f"User sent an image with message: {user_message}. Please respond appropriately."
                })
            
            data = {
                "model": vision_model,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=45
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        print(f"OpenRouter Vision API error: {response.status} - {error_text}")
                        return "I can see you sent an image! However, I'm having trouble analyzing it right now. Please try again later."
        
        except Exception as e:
            print(f"Error in generate_image_response: {str(e)}")
            return "Thanks for sharing the image! I'm having some technical difficulties analyzing it at the moment."
    
    async def generate_video_response(self, user_message: str, conversation_history: list = None) -> str:
        """Generate AI response for video content with conversation context"""
        try:
            # Refresh settings from database
            self.refresh_settings()
            
            # Check if API key is available
            if not self.api_key:
                print("❌ OpenRouter API key not configured in database")
                return "Sorry, the AI service is not properly configured. Please contact the administrator."
            
            system_prompt = """You are responding to a user who sent a video. 
            Since you cannot directly analyze video content, acknowledge the video 
            and respond based on any accompanying text message and conversation history."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history for context
            if conversation_history:
                for entry in conversation_history[-5:]:  # Last 5 exchanges for context
                    user_msg = entry['user_message'] if entry['user_message'] else None
                    bot_resp = entry['bot_response'] if entry['bot_response'] else None
                    
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})
            
            # Add current video message
            messages.append({"role": "user", "content": f"User sent a video with message: '{user_message}'. Please respond appropriately."})
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        return "Thanks for sharing the video! I received it but I'm having some technical difficulties right now."
        
        except Exception as e:
            print(f"Error in generate_video_response: {str(e)}")
            return "Thanks for the video! I'm having some technical issues at the moment, but I appreciate you sharing it."
    
    async def test_api_connection(self) -> bool:
        """Test if the OpenRouter API is working"""
        try:
            test_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=test_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        
        except Exception as e:
            print(f"API test failed: {str(e)}")
            return False