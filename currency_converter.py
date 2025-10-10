import requests
import time
from typing import Optional

class CurrencyConverter:
    def __init__(self):
        self._ton_rate_cache = None
        self._stars_rate_cache = None
        self._cache_timestamp = 0
        self._cache_duration = 300  # 5 minutes cache
    
    def _is_cache_valid(self) -> bool:
        """Check if cached rates are still valid"""
        return time.time() - self._cache_timestamp < self._cache_duration
    
    def get_ton_to_usd_rate(self) -> float:
        """Get current TON to USD conversion rate"""
        if self._is_cache_valid() and self._ton_rate_cache is not None:
            return self._ton_rate_cache
        
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd",
                timeout=5
            )
            data = response.json()
            rate = data['the-open-network']['usd']
            
            # Cache the result
            self._ton_rate_cache = rate
            self._cache_timestamp = time.time()
            
            return rate
        except Exception as e:
            print(f"Error fetching TON rate: {e}")
            # Return cached value if available, otherwise fallback
            return self._ton_rate_cache if self._ton_rate_cache else 0
    
    def get_stars_to_usd_rate(self) -> float:
        """Get Telegram Stars to USD conversion rate"""
        # Telegram Stars rate: 1 Star = ~$0.013 USD (as of 2024)
        # This is a relatively stable rate set by Telegram
        if self._is_cache_valid() and self._stars_rate_cache is not None:
            return self._stars_rate_cache
        
        try:
            # For now, use the standard Telegram Stars rate
            # In the future, this could be made configurable or fetched from an API
            rate = 0.013  # $0.013 per Star
            
            # Cache the result
            self._stars_rate_cache = rate
            self._cache_timestamp = time.time()
            
            return rate
        except Exception as e:
            print(f"Error setting Stars rate: {e}")
            return self._stars_rate_cache if self._stars_rate_cache else 0.013
    
    def ton_to_usd(self, ton_amount: float) -> float:
        """Convert TON amount to USD"""
        if ton_amount <= 0:
            return 0
        rate = self.get_ton_to_usd_rate()
        return ton_amount * rate
    
    def stars_to_usd(self, stars_amount: float) -> float:
        """Convert Telegram Stars amount to USD"""
        if stars_amount <= 0:
            return 0
        rate = self.get_stars_to_usd_rate()
        return stars_amount * rate
    
    def get_total_usd_value(self, ton_amount: float, stars_amount: float) -> dict:
        """Get total USD value breakdown"""
        ton_usd = self.ton_to_usd(ton_amount)
        stars_usd = self.stars_to_usd(stars_amount)
        total_usd = ton_usd + stars_usd
        
        return {
            'ton_usd': ton_usd,
            'stars_usd': stars_usd,
            'total_usd': total_usd,
            'ton_rate': self.get_ton_to_usd_rate(),
            'stars_rate': self.get_stars_to_usd_rate()
        }
    
    def get_cache_timestamp(self) -> float:
        """Get the timestamp of when the cache was last updated"""
        return self._cache_timestamp
    
    def get_ton_usd_rate(self) -> float:
        """Alias for get_ton_to_usd_rate for compatibility"""
        return self.get_ton_to_usd_rate()

# Global instance for reuse
currency_converter = CurrencyConverter()