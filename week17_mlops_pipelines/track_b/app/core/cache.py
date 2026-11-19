"""Response and prompt caching module with TTL and hash-based keying."""

import hashlib
import json
import time
from typing import Optional, Dict, Any
from app.config import settings


class ResponseCache:
    """Thread-safe In-Memory Response Cache with TTL support."""

    def __init__(self, ttl_seconds: int = settings.CACHE_TTL_SECONDS, enabled: bool = settings.CACHE_ENABLED):
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

    def _generate_key(self, prompt: str, system_prompt: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        """Create a deterministic hash key from prompt, system prompt, and generation parameters."""
        raw_key_data = {
            "prompt": prompt.strip().lower(),
            "system_prompt": (system_prompt or "").strip().lower(),
            "params": params or {}
        }
        serialized = json.dumps(raw_key_data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, prompt: str, system_prompt: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a cached response if valid and not expired."""
        if not self.enabled:
            return None

        key = self._generate_key(prompt, system_prompt, params)
        entry = self._cache.get(key)

        if not entry:
            self.misses += 1
            return None

        # Check expiration
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return entry["response"]

    def set(self, prompt: str, response: Dict[str, Any], system_prompt: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        """Store response in cache with expiration timestamp."""
        if not self.enabled:
            return

        key = self._generate_key(prompt, system_prompt, params)
        self._cache[key] = {
            "response": response,
            "created_at": time.time(),
            "expires_at": time.time() + self.ttl_seconds
        }

    def clear(self):
        """Clear all entries in the cache."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
        return {
            "enabled": self.enabled,
            "total_entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds
        }


# Global cache instance
cache = ResponseCache()
