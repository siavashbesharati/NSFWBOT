#!/usr/bin/env python3
"""
Test script to fetch and display OpenRouter models
This demonstrates the API request and response format
"""

import requests
import json
from datetime import datetime

def format_precise_number(value):
    """Format numbers with full precision, only removing trailing zeros"""
    if value is None or value == 0:
        return "0"
    
    try:
        num = float(value)
        # Use reasonable precision formatting (8 decimal places)
        formatted = f"{num:.8f}"
        
        # Remove trailing zeros and decimal point if needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    except (ValueError, TypeError):
        return str(value)

def fetch_openrouter_models():
    """
    Fetch available models from OpenRouter API
    
    Request: GET https://openrouter.ai/api/v1/models
    Response: JSON with 'data' array containing model objects
    """
    
    print("🔍 Fetching OpenRouter models...")
    print("📡 Request: GET https://openrouter.ai/api/v1/models")
    print("-" * 60)
    
    try:
        url = "https://openrouter.ai/api/v1/models"
        response = requests.get(url, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds()}s")
        print("-" * 60)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Successfully fetched models!")
            print(f"📈 Total models available: {len(data.get('data', []))}")
            print("-" * 60)
            
            # Display first 5 models as examples
            models = data.get('data', [])[:5]
            
            print("🤖 Sample Models (first 5):")
            for i, model in enumerate(models, 1):
                print(f"\n{i}. Model ID: {model.get('id', 'N/A')}")
                print(f"   Name: {model.get('name', 'N/A')}")
                print(f"   Description: {model.get('description', 'N/A')[:100]}...")
                print(f"   Context Length: {model.get('context_length', 'N/A'):,} tokens")
                
                # Pricing info
                pricing = model.get('pricing', {})
                prompt_price = float(pricing.get('prompt', 0)) * 1000  # Per 1K tokens
                completion_price = float(pricing.get('completion', 0)) * 1000
                
                print(f"   Pricing: ${format_precise_number(prompt_price)} prompt / ${format_precise_number(completion_price)} completion (per 1K tokens)")
                
                # Input modalities
                modalities = model.get('architecture', {}).get('input_modalities', [])
                print(f"   Input Types: {', '.join(modalities)}")
            
            print("-" * 60)
            
            # Group by provider
            providers = {}
            for model in data.get('data', []):
                provider = model.get('id', '').split('/')[0]
                if provider:
                    providers[provider] = providers.get(provider, 0) + 1
            
            print("🏢 Models by Provider:")
            for provider, count in sorted(providers.items()):
                print(f"   {provider}: {count} models")
            
            print("-" * 60)
            print(f"📅 Fetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Save full response to file for inspection
            with open('openrouter_models_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("💾 Full response saved to: openrouter_models_response.json")
            
            return data
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def show_response_structure():
    """Display the expected response structure"""
    
    print("\n" + "="*60)
    print("📋 OpenRouter API Response Structure")
    print("="*60)
    
    example_response = {
        "data": [
            {
                "id": "string",
                "name": "string", 
                "created": 1741818122,
                "description": "string",
                "architecture": {
                    "input_modalities": ["text", "image"],
                    "output_modalities": ["text"],
                    "tokenizer": "GPT",
                    "instruct_type": "string"
                },
                "top_provider": {
                    "is_moderated": True,
                    "context_length": 128000,
                    "max_completion_tokens": 16384
                },
                "pricing": {
                    "prompt": "0.0000007",
                    "completion": "0.0000007", 
                    "image": "0",
                    "request": "0",
                    "web_search": "0",
                    "internal_reasoning": "0",
                    "input_cache_read": "0",
                    "input_cache_write": "0"
                },
                "canonical_slug": "string",
                "context_length": 128000,
                "hugging_face_id": "string",
                "per_request_limits": {},
                "supported_parameters": ["string"],
                "default_parameters": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0
                }
            }
        ]
    }
    
    print("📝 Expected JSON Structure:")
    print(json.dumps(example_response, indent=2))

if __name__ == "__main__":
    print("🚀 OpenRouter Models Test Script")
    print("="*60)
    
    # Show expected response structure
    show_response_structure()
    
    # Fetch actual models
    result = fetch_openrouter_models()
    
    if result:
        print("\n✅ Test completed successfully!")
        print("Check the admin dashboard at http://127.0.0.1:5000/settings")
        print("The models dropdown should now be populated dynamically!")
    else:
        print("\n❌ Test failed!")