"""Base HTTP collector with rate limiting and retry logic."""
import time
import requests
from typing import Optional, Dict, Any
from data.cache import get_cache


class BaseCollector:
    def __init__(self, base_url: str, headers: Optional[Dict] = None, rate_limit_delay: float = 0.5):
        self.base_url = base_url
        self.headers = headers or {}
        self.rate_limit_delay = rate_limit_delay
        self._last_request = 0.0
        self.cache = get_cache()

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request = time.time()

    def get(self, endpoint: str, params: Optional[Dict] = None,
            timeout: int = 10, retries: int = 3) -> Optional[Dict[str, Any]]:
        self._throttle()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:  # rate limited
                    wait = int(resp.headers.get("Retry-After", 60))
                    time.sleep(wait)
                elif resp.status_code in (401, 403):
                    return None  # Bad API key, don't retry
                elif resp.status_code >= 500:
                    time.sleep(2 ** attempt)
            except requests.RequestException:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def cached_get(self, cache_key: str, endpoint: str,
                   params: Optional[Dict] = None, ttl: int = 300) -> Optional[Dict]:
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.get(endpoint, params=params)
        if data is not None:
            self.cache.set(cache_key, data, ttl)
        return data

    @property
    def is_configured(self) -> bool:
        return True
