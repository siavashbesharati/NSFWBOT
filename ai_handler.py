import asyncio
from typing import Optional

import requests


class VeniceAPI:
    """Venice-only AI client."""

    VENICE_BASE_URL = "https://api.venice.ai/api/v1"

    def __init__(self, database=None):
        self.db = database
        self.api_key = ""
        self.model = "venice-uncensored"
        self.base_url = self.VENICE_BASE_URL
        self.last_response_metadata = None
        self.refresh_settings()

    def get_last_response_metadata(self):
        return self.last_response_metadata

    def refresh_settings(self):
        """Load key/model from DB only; always force Venice endpoint."""
        db_key = ""
        db_model = "venice-uncensored"
        if self.db:
            db_key = self.db.get_setting("venice_inference_key", "") or self.db.get_setting("ai_api_key", "")
            db_model = self.db.get_setting("ai_model", "venice-uncensored")

        self.api_key = db_key or ""
        self.model = db_model or "venice-uncensored"
        self.base_url = self.VENICE_BASE_URL

    async def generate_text_response(
        self,
        user_message: str,
        user_context: str = None,
        conversation_history: list = None,
        system_instruction: str = None,
    ) -> str:
        try:
            self.refresh_settings()
            if not self.api_key:
                return "Sorry, the AI service is not properly configured. Please contact the administrator."
            return await self._venice_direct_request(
                user_message, user_context, conversation_history, system_instruction
            )
        except Exception as e:
            print(f"Error in generate_text_response: {str(e)}")
            return "Sorry, I encountered an error while generating a response. Please try again."

    async def _venice_direct_request(
        self,
        user_message: str,
        user_context: str = None,
        conversation_history: list = None,
        system_instruction: str = None,
    ) -> str:
        try:
            if not self.api_key:
                return "Sorry, the AI service is not properly configured. Please contact the administrator."

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            if conversation_history:
                for entry in conversation_history:
                    user_msg = entry["user_message"] if entry["user_message"] else None
                    bot_resp = entry["bot_response"] if entry["bot_response"] else None
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})

            messages.append({"role": "user", "content": user_message})

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "frequency_penalty": 0,
                "stream": False,
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            self._log_venice_headers(response)
            if response.status_code == 200:
                data = response.json()
                self.last_response_metadata = data
                if data.get("choices"):
                    return data["choices"][0]["message"]["content"].strip()
                return "Sorry, I received an unexpected response format from the AI service."
            if response.status_code == 429:
                return await self._handle_rate_limit(response, user_message, user_context, conversation_history)
            if response.status_code >= 500:
                return await self._handle_server_error(response, user_message, user_context, conversation_history)
            return f"Sorry, I'm experiencing technical difficulties. Please try again later. (Error: {response.status_code})"
        except requests.exceptions.Timeout:
            return "Sorry, the AI service is taking too long to respond. Please try again."
        except requests.exceptions.RequestException:
            return "Sorry, I'm having trouble connecting to the AI service. Please try again later."
        except Exception as e:
            print(f"Venice API error: {e}")
            return "Sorry, something unexpected happened. Please try again later."

    def _log_venice_headers(self, response):
        headers = response.headers
        print(
            "Venice headers:",
            headers.get("CF-RAY"),
            headers.get("x-venice-version"),
            headers.get("x-venice-model-id"),
            headers.get("x-ratelimit-remaining-requests"),
            headers.get("x-ratelimit-limit-requests"),
        )

    async def _handle_rate_limit(self, response, user_message, user_context, conversation_history, retry_count=0):
        if retry_count >= 3:
            return "Sorry, the AI service is currently overloaded. Please try again in a few minutes."
        wait_time = min(30, max(1, 2 ** retry_count))
        reset_requests = response.headers.get("x-ratelimit-reset-requests")
        if reset_requests:
            import time

            wait_time = min(wait_time, max(1, int(reset_requests) - int(time.time())))
        await asyncio.sleep(wait_time)
        return await self._venice_direct_request(user_message, user_context, conversation_history)

    async def _handle_server_error(self, response, user_message, user_context, conversation_history, retry_count=0):
        if retry_count >= 2:
            return "Sorry, the AI service is temporarily unavailable. Please try again later."
        await asyncio.sleep(2 ** retry_count)
        return await self._venice_direct_request(user_message, user_context, conversation_history)

    async def generate_image_response(
        self,
        user_message: str,
        image_data: bytes = None,
        conversation_history: list = None,
    ) -> str:
        try:
            self.refresh_settings()
            if not self.api_key:
                return "Sorry, the AI service is not properly configured. Please contact the administrator."

            messages = []
            if conversation_history:
                for entry in conversation_history[-3:]:
                    user_msg = entry["user_message"] if entry["user_message"] else ""
                    bot_resp = entry["bot_response"] if entry["bot_response"] else ""
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg[:100]})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp[:100]})

            if image_data:
                import base64

                image_base64 = base64.b64encode(image_data).decode("utf-8")
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message if user_message else "What do you see in this image?"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        ],
                    }
                )
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": f"User sent an image with message: {user_message}. Please respond appropriately.",
                    }
                )

            return await self._venice_messages_request(messages, max_tokens=300, timeout=45)
        except Exception as e:
            print(f"Error in generate_image_response: {str(e)}")
            return "Thanks for sharing the image! I'm having some technical difficulties analyzing it at the moment."

    async def generate_video_response(self, user_message: str, conversation_history: list = None) -> str:
        try:
            self.refresh_settings()
            if not self.api_key:
                return "Sorry, the AI service is not properly configured. Please contact the administrator."

            messages = []
            if conversation_history:
                for entry in conversation_history[-5:]:
                    user_msg = entry["user_message"] if entry["user_message"] else None
                    bot_resp = entry["bot_response"] if entry["bot_response"] else None
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})

            messages.append(
                {
                    "role": "user",
                    "content": f"User sent a video with message: '{user_message}'. Please respond appropriately.",
                }
            )
            return await self._venice_messages_request(messages, max_tokens=300, timeout=30)
        except Exception as e:
            print(f"Error in generate_video_response: {str(e)}")
            return "Thanks for the video! I'm having some technical issues at the moment, but I appreciate you sharing it."

    async def _venice_messages_request(self, messages: list, max_tokens: int = 300, timeout: int = 30) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if response.status_code != 200:
            return "Thanks for sharing. I'm having technical difficulties right now."
        result = response.json()
        self.last_response_metadata = result
        return result["choices"][0]["message"]["content"].strip()

    async def test_api_connection(self) -> bool:
        try:
            self.refresh_settings()
            if not self.api_key:
                return False
            return self._test_venice_api_requests()
        except Exception as e:
            print(f"API test failed: {str(e)}")
            return False

    def _test_venice_api_requests(self) -> bool:
        try:
            if not self.api_key:
                return False
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Say: Venice API test successful"}],
                    "max_tokens": 64,
                    "stream": False,
                },
                timeout=30,
            )
            if response.status_code != 200:
                return False
            data = response.json()
            return bool(data.get("choices"))
        except Exception as e:
            print(f"Venice API test error: {str(e)}")
            return False

    async def get_venice_account_status(self):
        try:
            self.refresh_settings()
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                    "temperature": 0,
                },
                timeout=10,
            )
            return {
                "status_code": response.status_code,
                "request_id": response.headers.get("CF-RAY", "N/A"),
                "venice_version": response.headers.get("x-venice-version", "N/A"),
                "model_id": response.headers.get("x-venice-model-id", "N/A"),
                "requests_limit": response.headers.get("x-ratelimit-limit-requests"),
                "requests_remaining": response.headers.get("x-ratelimit-remaining-requests"),
                "requests_reset": response.headers.get("x-ratelimit-reset-requests"),
                "tokens_limit": response.headers.get("x-ratelimit-limit-tokens"),
                "tokens_remaining": response.headers.get("x-ratelimit-remaining-tokens"),
                "tokens_reset": response.headers.get("x-ratelimit-reset-tokens"),
                "balance_usd": response.headers.get("x-venice-balance-usd"),
                "balance_diem": response.headers.get("x-venice-balance-diem"),
                "model_deprecation_warning": response.headers.get("x-venice-model-deprecation-warning"),
                "model_deprecation_date": response.headers.get("x-venice-model-deprecation-date"),
            }
        except Exception as e:
            return {"error": f"Failed to get Venice status: {str(e)}"}

    def format_venice_status(self, status):
        if "error" in status:
            return f"❌ Error: {status['error']}"
        lines = [
            "🏛️ **Venice API Status**",
            f"📡 Status: {status['status_code']}",
            f"🆔 Request ID: {status['request_id']}",
            f"📦 Venice Version: {status['venice_version']}",
            f"🤖 Model: {status['model_id'] or 'N/A'}",
        ]
        if status["requests_remaining"] and status["requests_limit"]:
            lines.append(f"📊 Requests: {status['requests_remaining']}/{status['requests_limit']}")
        if status["tokens_remaining"] and status["tokens_limit"]:
            lines.append(f"🎫 Tokens: {status['tokens_remaining']}/{status['tokens_limit']}")
        if status["balance_usd"]:
            lines.append(f"💵 USD Balance: ${status['balance_usd']}")
        if status["balance_diem"]:
            lines.append(f"💎 DIEM Balance: {status['balance_diem']}")
        if status["model_deprecation_warning"]:
            lines.append(f"⚠️ Model Warning: {status['model_deprecation_warning']}")
        return "\n".join(lines)
