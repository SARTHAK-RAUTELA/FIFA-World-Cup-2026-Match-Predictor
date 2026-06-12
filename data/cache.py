"""Thread-safe in-memory cache with TTL expiry."""
import time
import threading
import json
import os
from typing import Any, Optional


class CacheEntry:
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


class DataCache:
    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._disk_path = os.path.join(os.path.dirname(__file__), ".cache_state.json")

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        with self._lock:
            self._store[key] = CacheEntry(value, ttl)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                return None
            return entry.value

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear_expired(self) -> int:
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired()]
            for k in expired:
                del self._store[k]
            return len(expired)

    def stats(self) -> dict:
        with self._lock:
            total = len(self._store)
            expired = sum(1 for v in self._store.values() if v.is_expired())
            return {
                "total_entries": total,
                "active_entries": total - expired,
                "expired_entries": expired,
            }

    def get_or_fetch(self, key: str, fetch_fn, ttl: int = 300) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = fetch_fn()
        if value is not None:
            self.set(key, value, ttl)
        return value


# Singleton
_cache_instance: Optional[DataCache] = None

def get_cache() -> DataCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataCache()
    return _cache_instance
