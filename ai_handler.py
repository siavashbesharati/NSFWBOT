import requests
import asyncio
import aiohttp
import http.client
import json
import ssl
from typing import Optional, Dict, Any

class OpenRouterAPI:
    def __init__(self, database=None):
        self.db = database
        # Get settings from database if available, otherwise use empty defaults
        if self.db:
            self.api_key = self.db.get_setting('ai_api_key', '')
            self.model = self.db.get_setting('ai_model', 'openai/gpt-3.5-turbo')
            self.base_url = self.db.get_setting('ai_base_url', 'https://openrouter.ai/api/v1')
        else:
            # No database available, use empty defaults
            self.api_key = ''
            self.model = 'openai/gpt-3.5-turbo'
            self.base_url = 'https://openrouter.ai/api/v1'
        
        # Set basic headers - additional headers added dynamically based on provider
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TelegramBot/1.0"
        }
        
        # Store last response metadata for database auditing
        self.last_response_metadata = None
        
        # Add provider-specific headers
        self._add_provider_headers()
    
    def get_last_response_metadata(self):
        """Get the metadata from the last Venice API response"""
        return self.last_response_metadata
    
    def _add_provider_headers(self):
        """Add provider-specific headers based on base URL"""
        if 'openrouter.ai' in self.base_url:
            # OpenRouter-specific headers
            self.headers["HTTP-Referer"] = "https://telegram.org"
            self.headers["X-Title"] = "Telegram NSFW Bot"
        elif 'venice.ai' in self.base_url:
            # Venice AI - uses standard OpenAI format, no extra headers needed
            pass
        # Add other providers as needed
    
    def refresh_settings(self):
        """Refresh API settings from database"""
        if self.db:
            self.api_key = self.db.get_setting('ai_api_key', '')
            self.model = self.db.get_setting('ai_model', 'openai/gpt-3.5-turbo')
            self.base_url = self.db.get_setting('ai_base_url', 'https://openrouter.ai/api/v1')
            
            # Update headers with new API key and provider-specific headers
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "TelegramBot/1.0"
            }
            self._add_provider_headers()
    
    async def generate_text_response(self, user_message: str, user_context: str = None, conversation_history: list = None, system_instruction: str = None, character_slug: str = None, user_language: str = 'en') -> dict:
        """
        Generate AI text response with translation middleware
        Returns dict with both original English and translated responses
        """
        try:
            # Import translation middleware
            from translation_middleware import translate_user_input, translate_ai_response
            
            # Refresh settings from database
            self.refresh_settings()
            
            # Check if API key is available
            if not self.api_key:
                print("❌ AI API key not configured in database")
                return {
                    'translated_response': "Sorry, the AI service is not properly configured. Please contact the administrator.",
                    'english_response': "Sorry, the AI service is not properly configured. Please contact the administrator.",
                    'original_language': 'en',
                    'target_language': user_language
                }
            
            # Step 1: Translate user input to English (if needed)
            print(f"🌐 Starting translation workflow for user language: {user_language}")
            english_message, detected_language = await translate_user_input(user_message, user_language)
            
            print(f"📝 Translation Results:")
            print(f"   Original: {user_message[:100]}..." if len(user_message) > 100 else f"   Original: {user_message}")
            print(f"   English: {english_message[:100]}..." if len(english_message) > 100 else f"   English: {english_message}")
            print(f"   Detected Language: {detected_language}")
            
            # Debug logging
            print(f"🔍 AI API Configuration:")
            print(f"   Base URL: {self.base_url}")
            print(f"   Model: {self.model}")
            print(f"   API Key: {'*' * (len(self.api_key) - 4) + self.api_key[-4:] if len(self.api_key) > 4 else '***'}")
            print(f"   Character Instruction: {'Yes' if system_instruction else 'No'}")
            print(f"   Character Slug: {character_slug}")
            
            # Step 2: Get AI response in English
            english_response = ""
            if 'venice.ai' in self.base_url:
                english_response = await self._venice_direct_request(english_message, user_context, conversation_history, system_instruction, character_slug)
            else:
                english_response = await self._standard_openai_request(english_message, user_context, conversation_history, system_instruction)
            
            print(f"🤖 AI Response (English): {english_response[:100]}..." if len(english_response) > 100 else f"🤖 AI Response (English): {english_response}")
            
            # Step 3: Translate AI response to user's language (if needed)
            translated_response = english_response
            if user_language != 'en':
                translated_response = await translate_ai_response(english_response, user_language)
                print(f"🌐 AI Response (Translated): {translated_response[:100]}..." if len(translated_response) > 100 else f"🌐 AI Response (Translated): {translated_response}")
            
            return {
                'translated_response': translated_response,
                'english_response': english_response,
                'user_message_english': english_message,
                'original_language': detected_language,
                'target_language': user_language
            }
        
        except Exception as e:
            print(f"Error in generate_text_response: {str(e)}")
            error_msg = "Sorry, I encountered an error while generating a response. Please try again."
            return {
                'translated_response': error_msg,
                'english_response': error_msg,
                'user_message_english': user_message,
                'original_language': 'en',
                'target_language': user_language
            }
    
    async def _venice_direct_request(self, user_message: str, user_context: str = None, conversation_history: list = None, system_instruction: str = None, character_slug: str = None) -> str:
        """Direct HTTP request to Venice AI with rate limiting and header monitoring"""
        try:
            # Read from database settings (no more hardcoding)
            api_key = self.api_key
            model = self.model  
            base_url = self.base_url
            
            if not api_key:
                print("❌ Venice AI API key not configured")
                return "Sorry, the AI service is not properly configured. Please contact the administrator."
            
            # Build messages array
            messages = []
            
            # Add system instruction if provided (character instruction)
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            
            # Add conversation history if provided
            if conversation_history:
                for entry in conversation_history:
                    user_msg = entry['user_message'] if entry['user_message'] else None
                    bot_resp = entry['bot_response'] if entry['bot_response'] else None
                    
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Prepare request data using working format from database settings
            data = {
                "frequency_penalty": 0,
                "max_tokens": 4096,
                "messages": messages,
                "model": model,  # From database
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.95
            }
            
            # Add character_slug if provided
            if character_slug:
                data["venice_parameters"] = {"character_slug": character_slug}
            
            headers = {
                'Authorization': f'Bearer {api_key}',  # From database
                'Content-Type': 'application/json'
                # Removed 'Accept-Encoding': 'gzip, br' to avoid compression issues
            }
            
            print(f"🔍 Venice Direct Request (FROM DATABASE):")
            print(f"   Base URL: {base_url}")
            print(f"   Model: {model}")
            print(f"   API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 4 else '***'}")
            
            # Use requests library (works unlike http.client)
            response = requests.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Log Venice response headers for monitoring
            self._log_venice_headers(response)
            
            print(f"📡 Venice Response Status: {response.status_code}")
            print(f"📄 Venice Response Content Length: {len(response.content) if response.content else 0}")
            print(f"🔍 Response Headers: {dict(response.headers)}")
            print(f"📝 Response Encoding: {response.encoding}")
            
            if response.status_code == 200:
                try:
                    # Check if response is compressed or has encoding issues
                    raw_text = response.text
                    print(f"📄 Raw response preview: {raw_text[:100]}...")
                    
                    # Try to parse JSON
                    response_data = response.json()
                    print(f"✅ Venice Response JSON parsed successfully")
                    print(f"📊 Response structure: {list(response_data.keys()) if response_data else 'Empty'}")
                    
                    # Log token usage information for cost calculation
                    if 'usage' in response_data:
                        usage = response_data['usage']
                        print(f"🎫 Token Usage:")
                        print(f"   Prompt Tokens: {usage.get('prompt_tokens', 0):,}")
                        print(f"   Completion Tokens: {usage.get('completion_tokens', 0):,}")
                        print(f"   Total Tokens: {usage.get('total_tokens', 0):,}")
                    
                    # Store complete response for database auditing
                    self.last_response_metadata = response_data
                    
                    # Extract the AI response content
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        ai_content = response_data["choices"][0]["message"]["content"].strip()
                        print(f"✨ AI Response: {ai_content[:100]}..." if len(ai_content) > 100 else f"✨ AI Response: {ai_content}")
                        return ai_content
                    else:
                        print(f"❌ No choices found in Venice response: {response_data}")
                        return "Sorry, I received an unexpected response format from the AI service."
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Venice JSON decode error: {e}")
                    print(f"📄 Raw response: {response.text[:500]}...")
                    return "Sorry, I received a malformed response from the AI service."
                except Exception as e:
                    print(f"❌ Venice response processing error: {e}")
                    return "Sorry, I had trouble processing the AI response."
            elif response.status_code == 429:
                # Rate limit exceeded - handle with exponential backoff
                return await self._handle_rate_limit(response, user_message, user_context, conversation_history)
            elif response.status_code >= 500:
                # Server error - should retry with exponential backoff
                print(f"🔄 Venice server error {response.status_code}, implementing retry logic")
                return await self._handle_server_error(response, user_message, user_context, conversation_history)
            else:
                print(f"❌ Venice API error: {response.status_code} - {response.text}")
                return f"Sorry, I'm experiencing technical difficulties. Please try again later. (Error: {response.status_code})"
                
        except requests.exceptions.Timeout:
            print("⏰ Venice API timeout")
            return "Sorry, the AI service is taking too long to respond. Please try again."
        except requests.exceptions.RequestException as e:
            print(f"🌐 Venice API network error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service. Please try again later."
        except Exception as e:
            print(f"❌ Venice API unexpected error: {e}")
            return "Sorry, something unexpected happened. Please try again later."
    
    def _log_venice_headers(self, response):
        """Log important Venice API response headers for monitoring"""
        headers = response.headers
        
        # Request identification
        cf_ray = headers.get('CF-RAY')
        venice_version = headers.get('x-venice-version')
        
        # Rate limiting information
        limit_requests = headers.get('x-ratelimit-limit-requests')
        remaining_requests = headers.get('x-ratelimit-remaining-requests')
        reset_requests = headers.get('x-ratelimit-reset-requests')
        limit_tokens = headers.get('x-ratelimit-limit-tokens')
        remaining_tokens = headers.get('x-ratelimit-remaining-tokens')
        reset_tokens = headers.get('x-ratelimit-reset-tokens')
        
        # Account balance information
        balance_usd = headers.get('x-venice-balance-usd')
        balance_diem = headers.get('x-venice-balance-diem')
        
        # Model information
        model_id = headers.get('x-venice-model-id')
        deprecation_warning = headers.get('x-venice-model-deprecation-warning')
        
        print(f"📊 Venice API Headers:")
        print(f"   Request ID (CF-RAY): {cf_ray}")
        print(f"   Venice Version: {venice_version}")
        
        if remaining_requests and limit_requests:
            print(f"   Rate Limit (Requests): {remaining_requests}/{limit_requests}")
        if remaining_tokens and limit_tokens:
            print(f"   Rate Limit (Tokens): {remaining_tokens}/{limit_tokens}")
        
        if balance_usd:
            print(f"   USD Balance: ${balance_usd}")
        if balance_diem:
            print(f"   DIEM Balance: {balance_diem}")
            
        if model_id:
            print(f"   Model Used: {model_id}")
            
        # Warning for model deprecation
        if deprecation_warning:
            print(f"⚠️  Model Deprecation Warning: {deprecation_warning}")
        
        # Warning for low remaining requests/tokens
        if remaining_requests and int(remaining_requests) < 10:
            print(f"⚠️  Low remaining requests: {remaining_requests}")
        if remaining_tokens and int(remaining_tokens) < 1000:
            print(f"⚠️  Low remaining tokens: {remaining_tokens}")
            
        # Warning for low balance
        if balance_usd and float(balance_usd) < 1.0:
            print(f"⚠️  Low USD balance: ${balance_usd}")
    
    async def _handle_rate_limit(self, response, user_message, user_context, conversation_history, retry_count=0):
        """Handle 429 rate limit errors with exponential backoff"""
        if retry_count >= 3:
            return "Sorry, the AI service is currently overloaded. Please try again in a few minutes."
        
        headers = response.headers
        reset_requests = headers.get('x-ratelimit-reset-requests')
        remaining_requests = headers.get('x-ratelimit-remaining-requests')
        
        print(f"🚫 Venice rate limit hit. Remaining requests: {remaining_requests}")
        
        # Calculate wait time (exponential backoff: 2^retry_count seconds, min 1, max 30)
        wait_time = min(30, max(1, 2 ** retry_count))
        
        if reset_requests:
            import time
            reset_time = int(reset_requests)
            current_time = int(time.time())
            time_until_reset = max(1, reset_time - current_time)
            wait_time = min(wait_time, time_until_reset)
        
        print(f"⏰ Waiting {wait_time} seconds before retry...")
        await asyncio.sleep(wait_time)
        
        # Retry the request
        return await self._venice_direct_request(user_message, user_context, conversation_history)
    
    async def _handle_server_error(self, response, user_message, user_context, conversation_history, retry_count=0):
        """Handle 5xx server errors with exponential backoff"""
        if retry_count >= 2:  # Max 2 retries for server errors
            return "Sorry, the AI service is temporarily unavailable. Please try again later."
        
        print(f"🔄 Venice server error {response.status_code}, retry {retry_count + 1}/2")
        
        # Exponential backoff: 2^retry_count seconds
        wait_time = 2 ** retry_count
        print(f"⏰ Waiting {wait_time} seconds before retry...")
        await asyncio.sleep(wait_time)
        
        # Retry the request
        return await self._venice_direct_request(user_message, user_context, conversation_history)
    
    async def _standard_openai_request(self, user_message: str, user_context: str = None, conversation_history: list = None, system_instruction: str = None) -> str:
        """Standard OpenAI-compatible request for other providers"""
        try:
            # Build messages array
            messages = []
            
            # Add system instruction if provided (character instruction)
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            
            # Add conversation history if provided
            if conversation_history:
                for entry in conversation_history:
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
            
            print(f"🔍 Standard API Request:")
            print(f"   URL: {self.base_url}/chat/completions")
            print(f"   Headers: {list(self.headers.keys())}")
            
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
                        error_text = await response.text()
                        print(f"❌ API error: {response.status} - {error_text}")
                        return "Sorry, I'm having trouble generating a response right now. Please try again later."
        
        except Exception as e:
            print(f"Error in standard request: {str(e)}")
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
            
            # NO SYSTEM PROMPT - PURE USER MESSAGES ONLY
            messages = []
            
            # Add conversation history as user/assistant pairs only
            if conversation_history:
                for entry in conversation_history[-3:]:  # Last 3 exchanges for context
                    user_msg = entry['user_message'] if entry['user_message'] else ""
                    bot_resp = entry['bot_response'] if entry['bot_response'] else ""
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg[:100]})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp[:100]})
            
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
                        # Store complete response for database auditing
                        self.last_response_metadata = result
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
            
            # NO SYSTEM PROMPT - PURE USER MESSAGES ONLY
            messages = []
            
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
                        # Store complete response for database auditing
                        self.last_response_metadata = result
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        return "Thanks for sharing the video! I received it but I'm having some technical difficulties right now."
        
        except Exception as e:
            print(f"Error in generate_video_response: {str(e)}")
            return "Thanks for the video! I'm having some technical issues at the moment, but I appreciate you sharing it."
    
    async def test_api_connection(self) -> bool:
        """Test if the AI API is working"""
        try:
            # Refresh settings
            self.refresh_settings()
            
            if not self.api_key:
                print("❌ No API key configured")
                return False
            
            # Test Venice AI specifically
            if 'venice.ai' in self.base_url:
                print("🔍 Testing Venice AI with requests library (the one that works)...")  
                result = self._test_venice_api_requests()
                print(f"📊 Venice AI Test Result: {result}")
                return result
            else:
                return await self._test_standard_api()
                
        except Exception as e:
            print(f"API test failed: {str(e)}")
            return False
    
    async def _test_venice_api(self) -> bool:
        """Test Venice AI using exact format that works in curl"""
        try:
            # HARDCODED Venice AI credentials - MATCH WORKING CURL
            test_api_key = "af9uD9UxvcrqR3kACGqyILz4gHQ7oN839m10wKy5pm"
            test_model = "llama-3.2-3b"  # Same model as working curl
            
            headers = {
                'Authorization': f'Bearer {test_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'python-httpx/0.24.1',  # Add User-Agent like curl
                'Accept': '*/*'  # Add Accept header
            }
            
            # Test data matching your EXACT working curl
            test_data = {
                "frequency_penalty": 0,
                "max_tokens": 4096,
                "messages": [
                    {
                        "content": "Say 'Venice AI test successful!' to confirm the connection works",
                        "role": "user"
                    }
                ],
                "model": test_model,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.95
            }
            
            print(f"🧪 Testing Venice AI API (DEBUGGING 403):")
            print(f"   URL: https://api.venice.ai/api/v1/chat/completions")
            print(f"   Model: {test_model}")
            print(f"   API Key: {test_api_key[:8]}...{test_api_key[-4:]}")
            print(f"   Headers: {headers}")
            
            # Use direct HTTP connection like Venice example
            conn = http.client.HTTPSConnection("api.venice.ai")
            
            # Convert data to JSON string
            json_data = json.dumps(test_data)
            print(f"   JSON Data: {json_data}")
            
            conn.request("POST", "/api/v1/chat/completions", json_data, headers)
            res = conn.getresponse()
            data = res.read()
            
            print(f"📡 Venice API Response Status: {res.status}")
            print(f"📡 Venice API Response Headers: {dict(res.getheaders())}")
            print(f"📡 Venice API Response Body: {data.decode('utf-8')}")
            
            if res.status == 200:
                response_data = json.loads(data.decode('utf-8'))
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    message = response_data['choices'][0].get('message', {}).get('content', '')
                    print(f"✅ Venice AI Test Success! Response: {message[:100]}...")
                    return True
                else:
                    print(f"❌ Venice API Test Failed: Invalid response format")
                    return False
            else:
                print(f"❌ Venice API Test Failed: {res.status}")
                return False
                
        except Exception as e:
            print(f"Venice API test error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_venice_api_requests(self) -> bool:
        """Test Venice AI using requests library (reads from database)"""
        try:
            # Read from database settings (no more hardcoding)
            api_key = self.api_key
            model = self.model
            base_url = self.base_url
            
            if not api_key:
                print("❌ Venice AI API key not configured in database")
                return False
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Test data using database settings
            test_data = {
                "frequency_penalty": 0,
                "max_tokens": 4096,
                "messages": [
                    {
                        "content": "Say 'Venice AI test successful!' to confirm the connection works",
                        "role": "user"
                    }
                ],
                "model": model,  # From database
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.95
            }
            
            print(f"🧪 Testing Venice AI API (FROM DATABASE SETTINGS):")
            print(f"   URL: https://api.venice.ai/api/v1/chat/completions")
            print(f"   Base URL Setting: {base_url}")
            print(f"   Model: {model}")
            print(f"   API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 4 else '***'}")
            
            # Use requests library like your PowerShell curl
            response = requests.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=30
            )
            
            print(f"📡 Venice API Response Status: {response.status_code}")
            print(f"📡 Venice API Response Headers: {dict(response.headers)}")
            print(f"📡 Venice API Response Body: {response.text[:300]}...")  # Truncate for logging
            
            if response.status_code == 200:
                response_data = response.json()
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    message = response_data['choices'][0].get('message', {}).get('content', '')
                    print(f"✅ Venice AI Test Success! Response: {message[:100]}...")
                    return True
                else:
                    print(f"❌ Venice API Test Failed: Invalid response format")
                    return False
            else:
                print(f"❌ Venice API Test Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Venice API test error (requests): {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _test_standard_api(self) -> bool:
        """Test standard OpenAI-compatible API"""
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
                    print(f"📡 Standard API Test Status: {response.status}")
                    if response.status == 200:
                        print("✅ Standard API Test Success!")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Standard API Test Failed: {response.status} - {error_text}")
                        return False
        
        except Exception as e:
            print(f"Standard API test error: {str(e)}")
            return False
    
    async def get_venice_account_status(self):
        """Get Venice account balance and rate limit status"""
        try:
            if 'venice.ai' not in self.base_url:
                return {"error": "Not a Venice AI endpoint"}
            
            # Make a minimal request to get headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Minimal test data to get rate limit headers
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0
            }
            
            response = requests.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            # Extract status information from headers
            status = {
                "status_code": response.status_code,
                "request_id": response.headers.get('CF-RAY', 'N/A'),
                "venice_version": response.headers.get('x-venice-version', 'N/A'),
                "model_id": response.headers.get('x-venice-model-id', 'N/A'),
                
                # Rate limits
                "requests_limit": response.headers.get('x-ratelimit-limit-requests'),
                "requests_remaining": response.headers.get('x-ratelimit-remaining-requests'),
                "requests_reset": response.headers.get('x-ratelimit-reset-requests'),
                "tokens_limit": response.headers.get('x-ratelimit-limit-tokens'),
                "tokens_remaining": response.headers.get('x-ratelimit-remaining-tokens'),
                "tokens_reset": response.headers.get('x-ratelimit-reset-tokens'),
                
                # Balances
                "balance_usd": response.headers.get('x-venice-balance-usd'),
                "balance_diem": response.headers.get('x-venice-balance-diem'),
                
                # Warnings
                "model_deprecation_warning": response.headers.get('x-venice-model-deprecation-warning'),
                "model_deprecation_date": response.headers.get('x-venice-model-deprecation-date')
            }
            
            return status
            
        except Exception as e:
            return {"error": f"Failed to get Venice status: {str(e)}"}
    
    def format_venice_status(self, status):
        """Format Venice status for display"""
        if "error" in status:
            return f"❌ Error: {status['error']}"
        
        lines = []
        lines.append(f"🏛️ **Venice API Status**")
        lines.append(f"📡 Status: {status['status_code']}")
        lines.append(f"🆔 Request ID: {status['request_id']}")
        lines.append(f"📦 Venice Version: {status['venice_version']}")
        lines.append(f"🤖 Model: {status['model_id'] or 'N/A'}")
        
        # Rate limits
        if status['requests_remaining'] and status['requests_limit']:
            lines.append(f"📊 Requests: {status['requests_remaining']}/{status['requests_limit']}")
        
        if status['tokens_remaining'] and status['tokens_limit']:
            lines.append(f"🎫 Tokens: {status['tokens_remaining']}/{status['tokens_limit']}")
        
        # Balances
        if status['balance_usd']:
            lines.append(f"💵 USD Balance: ${status['balance_usd']}")
        if status['balance_diem']:
            lines.append(f"💎 DIEM Balance: {status['balance_diem']}")
        
        # Warnings
        if status['model_deprecation_warning']:
            lines.append(f"⚠️ Model Warning: {status['model_deprecation_warning']}")
        
        return "\n".join(lines)