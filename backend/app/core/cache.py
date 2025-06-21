"""
Caching service implementation for performance optimization.

This module provides both in-memory caching and Redis-based caching capabilities.
The system defaults to in-memory caching but can use Redis if configured.
"""

import json
import logging
import pickle
import threading
import time
from functools import wraps
from typing import Any, Dict, List, Optional, TypeVar, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheItem:
    """Represents a single item in the cache with expiry time."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expiry = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if this cache item has expired."""
        return time.time() > self.expiry


class InMemoryCache:
    """
    Simple in-memory cache implementation with TTL support.
    Thread-safe using a lock for cache operations.
    """

    def __init__(self, cleanup_interval: int = 60):
        """Initialize the in-memory cache."""
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        logger.info("In-memory cache service initialized")

    def _cleanup_expired(self):
        """Remove expired items from cache."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            with self._lock:
                # Find keys to remove
                expired_keys = [key for key, item in self._cache.items() if item.is_expired()]

                # Remove expired keys
                for key in expired_keys:
                    del self._cache[key]

                self._last_cleanup = now

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        self._cleanup_expired()

        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if not item.is_expired():
                    logger.debug(f"Cache hit: {key}")
                    return item.value
                else:
                    # Remove expired item
                    del self._cache[key]

        logger.debug(f"Cache miss: {key}")
        return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        if ttl is None:
            ttl = (
                getattr(settings, "REDIS_TTL", None) or settings.CACHE_TTL
            )  # Use CACHE_TTL as fallback

        with self._lock:
            self._cache[key] = CacheItem(value, ttl)

        logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
        return True

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache key: {key}")
                return True

        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        self._cleanup_expired()

        with self._lock:
            return key in self._cache and not self._cache[key].is_expired()

    async def clear(self) -> bool:
        """Clear all values from cache."""
        with self._lock:
            self._cache.clear()

        logger.info("Cache cleared")
        return True

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        self._cleanup_expired()

        result = {}
        with self._lock:
            for key in keys:
                if key in self._cache and not self._cache[key].is_expired():
                    result[key] = self._cache[key].value

        return result

    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        if ttl is None:
            ttl = (
                getattr(settings, "REDIS_TTL", None) or settings.CACHE_TTL
            )  # Use CACHE_TTL as fallback

        with self._lock:
            for key, value in mapping.items():
                self._cache[key] = CacheItem(value, ttl)

        logger.debug(f"Cached {len(mapping)} values (TTL: {ttl}s)")
        return True

    async def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from cache."""
        with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]

        logger.debug(f"Deleted {len(keys)} cache keys")
        return True


class RedisCache:
    """
    Redis cache implementation with fallback to in-memory cache.
    """

    def __init__(self):
        """Initialize Redis connection with fallback to in-memory cache."""
        self.in_memory = InMemoryCache()

        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using in-memory cache only")
            self.redis = None
            return

        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # We need binary for pickle support
            )
            logger.info("Redis cache service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self.redis = None

    async def _check_connection(self) -> bool:
        """Check if Redis connection is working."""
        if not self.redis:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception:
            logger.warning("Redis connection failed")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache, trying Redis first then falling back to in-memory."""
        # First check in memory for performance
        value = await self.in_memory.get(key)
        if value is not None:
            return value

        # Then try Redis if available
        if self.redis and await self._check_connection():
            try:
                value = await self.redis.get(key)
                if value is not None:
                    try:
                        # Try to deserialize as pickle first (for complex objects)
                        deserialized = pickle.loads(value)
                        # Cache in memory for faster subsequent access
                        await self.in_memory.set(key, deserialized)
                        return deserialized
                    except Exception:
                        try:
                            # Try as JSON next
                            deserialized = json.loads(value)
                            await self.in_memory.set(key, deserialized)
                            return deserialized
                        except Exception:
                            # Return as-is if not serialized
                            await self.in_memory.set(key, value)
                            return value
            except Exception as e:
                logger.error(f"Redis get error: {str(e)}")

        return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False) -> bool:
        """Set a value in cache."""
        if ttl is None:
            ttl = getattr(settings, "REDIS_TTL", None) or settings.CACHE_TTL

        # Always set in memory cache first
        await self.in_memory.set(key, value, ttl)

        # Try Redis if available
        if self.redis and await self._check_connection():
            try:
                # Try to serialize as JSON first for better interoperability
                try:
                    serialized = json.dumps(value)
                except (TypeError, OverflowError):
                    # Fall back to pickle for complex objects
                    serialized = pickle.dumps(value)

                # Set in Redis with TTL
                if nx:
                    success = await self.redis.set(key, serialized, ex=ttl, nx=True)
                else:
                    success = await self.redis.set(key, serialized, ex=ttl)

                if not success and not nx:
                    logger.warning(f"Failed to set cache key in Redis: {key}")

                return bool(success)
            except Exception as e:
                logger.error(f"Redis set error: {str(e)}")

        # Return True if set in memory, even if Redis failed
        return True

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        # Delete from memory first
        memory_success = await self.in_memory.delete(key)

        # Try Redis if available
        if self.redis and await self._check_connection():
            try:
                redis_success = bool(await self.redis.delete(key))
                return memory_success or redis_success
            except Exception as e:
                logger.error(f"Redis delete error: {str(e)}")

        return memory_success

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        # Check memory first
        if await self.in_memory.exists(key):
            return True

        # Try Redis if memory check failed
        if self.redis and await self._check_connection():
            try:
                return bool(await self.redis.exists(key))
            except Exception as e:
                logger.error(f"Redis exists error: {str(e)}")

        return False

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        # Set TTL in memory
        # Note: The in-memory cache will need to get the value again
        value = await self.in_memory.get(key)
        if value is not None:
            await self.in_memory.set(key, value, ttl)

        # Try Redis if available
        if self.redis and await self._check_connection():
            try:
                success = await self.redis.expire(key, ttl)
                return bool(success)
            except Exception as e:
                logger.error(f"Redis expire error: {str(e)}")

        return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        # Memory cache doesn't easily support increment operations
        # First try to get the current value
        current = await self.get(key, 0)
        if not isinstance(current, (int, float)):
            current = 0

        # Increment locally
        new_value = current + amount

        # Update both caches
        await self.set(key, new_value)

        # Use Redis native increment if available
        if self.redis and await self._check_connection():
            try:
                return await self.redis.incrby(key, amount)
            except Exception as e:
                logger.error(f"Redis increment error: {str(e)}")

        return new_value

    async def clear(self) -> bool:
        """Clear all cache values."""
        # Clear memory cache
        memory_success = await self.in_memory.clear()

        # Try Redis if available
        redis_success = False
        if self.redis and await self._check_connection():
            try:
                redis_success = await self.redis.flushdb()
            except Exception as e:
                logger.error(f"Redis flush error: {str(e)}")

        return memory_success or redis_success

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        result = {}

        # First check memory cache
        memory_results = await self.in_memory.get_many(keys)
        result.update(memory_results)

        # If we got all keys from memory, we're done
        if len(result) == len(keys):
            return result

        # For missing keys, try Redis
        missing_keys = [key for key in keys if key not in result]
        if self.redis and missing_keys and await self._check_connection():
            try:
                # Redis doesn't have a direct async equivalent for mget in redis.asyncio
                # We'll pipeline the requests
                pipe = self.redis.pipeline()
                for key in missing_keys:
                    pipe.get(key)

                values = await pipe.execute()

                # Process each value
                for i, key in enumerate(missing_keys):
                    value = values[i]
                    if value is not None:
                        try:
                            # Try to deserialize
                            result[key] = pickle.loads(value)
                        except Exception:
                            try:
                                result[key] = json.loads(value)
                            except Exception:
                                result[key] = value

                        # Cache in memory for future requests
                        await self.in_memory.set(key, result[key])
            except Exception as e:
                logger.error(f"Redis mget error: {str(e)}")

        return result

    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        if ttl is None:
            ttl = getattr(settings, "REDIS_TTL", None) or settings.CACHE_TTL

        # Set all in memory cache
        await self.in_memory.set_many(mapping, ttl)

        # Try Redis if available
        if self.redis and await self._check_connection():
            try:
                pipe = self.redis.pipeline()
                for key, value in mapping.items():
                    try:
                        # Try JSON first
                        serialized = json.dumps(value)
                    except (TypeError, OverflowError):
                        # Fall back to pickle
                        serialized = pickle.dumps(value)

                    pipe.set(key, serialized, ex=ttl)

                results = await pipe.execute()
                return all(results)
            except Exception as e:
                logger.error(f"Redis mset error: {str(e)}")

        # Return True since memory cache succeeded
        return True


# Decide which implementation to use based on settings
def get_cache() -> Union[RedisCache, InMemoryCache]:
    """Get the appropriate cache implementation based on settings."""
    use_redis = hasattr(settings, "USE_REDIS_CACHE") and settings.USE_REDIS_CACHE

    if use_redis and REDIS_AVAILABLE:
        return RedisCache()
    else:
        return InMemoryCache()


# Create a singleton cache instance
cache = get_cache()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds. Defaults to settings.CACHE_TTL.
        key_prefix: Prefix for the cache key. Defaults to "".

    Example:
        @cached(ttl=60)
        async def get_user_by_id(user_id: str) -> User:
            # This result will be cached for 60 seconds
            return await db.query(User).filter(User.id == user_id).first()
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a key based on function name, args and kwargs
            key_parts = [key_prefix, func.__module__, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = ":".join(key_parts)

            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call the function if not cached
            result = await func(*args, **kwargs)

            # Cache the result
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
