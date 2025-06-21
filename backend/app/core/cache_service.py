"""
Cache Service - Redis-free implementation for cost optimization.
Provides unified caching interface using in-memory and SQLite alternatives.
"""

import json
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from .cache_alternatives import memory_cache, persistent_cache, cache_manager, cache_decorator
from .config import settings


class CacheService:
    """
    Unified cache service that abstracts away Redis dependency.
    Provides same interface as Redis but uses cost-effective alternatives.
    """

    def __init__(self):
        # Initialize based on configuration
        self.use_memory = settings.CACHE_TYPE == "memory"
        self.use_redis = settings.USE_REDIS_CACHE and settings.REDIS_URL
        self.ttl = settings.CACHE_TTL

        # Set up cache backend
        if self.use_redis:
            # Redis is available and enabled - use it
            import redis.asyncio as redis

            self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
            self.backend = "redis"
        elif self.use_memory:
            # Use in-memory cache
            self.cache = memory_cache
            self.backend = "memory"
        else:
            # Use SQLite persistent cache
            self.cache = persistent_cache
            self.backend = "sqlite"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.use_redis:
                cached = await self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
                return None
            else:
                return self.cache.get(key)
        except Exception as e:
            # Cache failures should not break the application
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or self.ttl

            if self.use_redis:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                await self.redis_client.setex(key, ttl, serialized)
                return True
            else:
                self.cache.set(key, value, ttl)
                return True
        except Exception as e:
            # Cache failures should not break the application
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.use_redis:
                result = await self.redis_client.delete(key)
                return result > 0
            else:
                return self.cache.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            if self.use_redis:
                await self.redis_client.flushdb()
                return True
            else:
                if hasattr(self.cache, "clear"):
                    self.cache.clear()
                    return True
        except Exception as e:
            print(f"Cache clear error: {e}")
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.use_redis:
                return await self.redis_client.exists(key) > 0
            else:
                return self.cache.get(key) is not None
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = {
                "backend": self.backend,
                "ttl_default": self.ttl,
            }

            if self.use_redis:
                info = await self.redis_client.info("memory")
                stats.update(
                    {
                        "memory_used": info.get("used_memory_human", "unknown"),
                        "connected": True,
                    }
                )
            else:
                if hasattr(self.cache, "stats"):
                    stats.update(self.cache.stats())

            return stats
        except Exception as e:
            return {"backend": self.backend, "error": str(e), "connected": False}

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate standardized cache key."""
        return cache_manager.cache_key(prefix, *args, **kwargs)

    async def close(self):
        """Close cache connections."""
        if self.use_redis and hasattr(self, "redis_client"):
            await self.redis_client.close()


# AI-specific cache methods for backward compatibility
class AICacheService(CacheService):
    """
    AI-specific cache service with methods optimized for LLM responses.
    Provides same interface as the old Redis-based AI cache.
    """

    def generate_cache_key(self, prompt: str, model: str = "default", **kwargs) -> str:
        """Generate cache key for AI responses."""
        import hashlib

        # Include relevant parameters in cache key
        key_data = {"prompt": prompt, "model": model, **kwargs}

        # Create hash for long prompts
        key_str = json.dumps(key_data, sort_keys=True)
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"ai:{model}:{key_hash}"
        else:
            return f"ai:{model}:{hashlib.md5(key_str.encode()).hexdigest()[:16]}"

    async def get_ai_response(
        self, prompt: str, model: str = "default", **kwargs
    ) -> Optional[Dict]:
        """Get cached AI response."""
        cache_key = self.generate_cache_key(prompt, model, **kwargs)
        cached = await self.get(cache_key)

        if cached and isinstance(cached, dict):
            # Check if cache entry has timestamp and is not too old
            if "timestamp" in cached:
                cache_age = datetime.now().timestamp() - cached["timestamp"]
                if cache_age > self.ttl:
                    await self.delete(cache_key)
                    return None
            return cached
        return None

    async def set_ai_response(
        self, prompt: str, response: Dict, model: str = "default", **kwargs
    ) -> bool:
        """Cache AI response with metadata."""
        cache_key = self.generate_cache_key(prompt, model, **kwargs)

        # Add metadata
        cache_entry = {
            "response": response,
            "timestamp": datetime.now().timestamp(),
            "model": model,
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()[:16],
        }

        return await self.set(cache_key, cache_entry, self.ttl)


# Global cache instances
cache_service = CacheService()
ai_cache_service = AICacheService()


# Decorator for function-level caching
def cached_function(ttl: int = 3600, key_prefix: str = "func"):
    """
    Decorator for caching function results.
    Uses the new cache alternatives instead of Redis.
    """
    return cache_decorator(ttl=ttl)


# Export for backward compatibility
__all__ = ["CacheService", "AICacheService", "cache_service", "ai_cache_service", "cached_function"]
