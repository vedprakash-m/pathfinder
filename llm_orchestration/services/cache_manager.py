"""
Cache Manager - Redis-based response caching service
Implements intelligent caching strategies for LLM responses
"""

import hashlib
import json
from typing import Any, Dict, Optional

import redis.asyncio as redis
import structlog
from core.types import LLMConfigurationError, LLMRequest, LLMResponse

logger = structlog.get_logger(__name__)


class CacheManager:
    """
    Manages LLM response caching with Redis backend
    Implements cache invalidation, TTL management, and cache analytics
    """

    def __init__(
        self,
        redis_url: str,
        default_ttl: int = 3600,  # 1 hour default
        max_cache_size: int = 1000000,  # 1MB max per cached item
        enable_compression: bool = True,
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.enable_compression = enable_compression

        # Redis client (will be initialized in connect())
        self.redis_client: Optional[redis.Redis] = None

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "stores": 0, "errors": 0}

    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Cache manager connected to Redis", url=self.redis_url)

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise LLMConfigurationError(f"Redis connection failed: {e}")

    async def get_cached_response(self, request: LLMRequest) -> Optional[LLMResponse]:
        """
        Retrieve cached response for a request
        Returns None if not found or cache miss
        """
        if not self.redis_client:
            await self.connect()

        try:
            cache_key = self._generate_cache_key(request)

            logger.debug("Checking cache", cache_key=cache_key, request_id=request.request_id)

            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                # Parse cached response
                response_data = json.loads(cached_data)
                response = LLMResponse.parse_obj(response_data)

                # Update cache hit stats
                self.stats["hits"] += 1

                logger.debug(
                    "Cache hit",
                    cache_key=cache_key,
                    request_id=request.request_id,
                    cached_model=response.model_used,
                )

                return response

            # Cache miss
            self.stats["misses"] += 1
            logger.debug("Cache miss", cache_key=cache_key, request_id=request.request_id)
            return None

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning("Cache retrieval failed", request_id=request.request_id, error=str(e))
            return None

    async def cache_response(
        self, request: LLMRequest, response: LLMResponse, ttl: Optional[int] = None
    ) -> bool:
        """
        Cache an LLM response
        Returns True if successfully cached, False otherwise
        """
        if not self.redis_client:
            await self.connect()

        try:
            cache_key = self._generate_cache_key(request)
            cache_ttl = ttl or self._calculate_ttl(request, response)

            # Serialize response
            response_data = response.dict()
            serialized_data = json.dumps(response_data, ensure_ascii=False)

            # Check size limits
            if len(serialized_data) > self.max_cache_size:
                logger.warning(
                    "Response too large to cache",
                    request_id=request.request_id,
                    size=len(serialized_data),
                    max_size=self.max_cache_size,
                )
                return False

            # Store in cache
            await self.redis_client.setex(cache_key, cache_ttl, serialized_data)

            # Update stats
            self.stats["stores"] += 1

            logger.debug(
                "Response cached successfully",
                cache_key=cache_key,
                request_id=request.request_id,
                ttl=cache_ttl,
                size=len(serialized_data),
            )

            return True

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning("Failed to cache response", request_id=request.request_id, error=str(e))
            return False

    def _generate_cache_key(self, request: LLMRequest) -> str:
        """
        Generate deterministic cache key from request
        Includes prompt, model preferences, and key parameters
        """
        # Create a normalized representation of the request for caching
        cache_components = {
            "prompt": request.prompt,
            "model_preference": (
                request.model_preference.value if request.model_preference else None
            ),
            "task_type": request.task_type.value,
            "parameters": {
                "temperature": getattr(request.parameters, "temperature", None),
                "max_tokens": getattr(request.parameters, "max_tokens", None),
                "top_p": getattr(request.parameters, "top_p", None),
                # Add other relevant parameters that affect response
            },
            "context": request.context[:500] if request.context else None,  # Limit context for key
        }

        # Remove None values
        cache_components = {k: v for k, v in cache_components.items() if v is not None}

        # Create deterministic hash
        cache_string = json.dumps(cache_components, sort_keys=True, ensure_ascii=False)
        cache_hash = hashlib.sha256(cache_string.encode("utf-8")).hexdigest()

        return f"llm_response:{cache_hash[:16]}"

    def _calculate_ttl(self, request: LLMRequest, response: LLMResponse) -> int:
        """
        Calculate appropriate TTL based on request/response characteristics
        """
        base_ttl = self.default_ttl

        # Adjust TTL based on request type
        if request.task_type.value in ["factual_qa", "translation"]:
            # Factual content can be cached longer
            return base_ttl * 2
        elif request.task_type.value in ["creative_writing", "conversation"]:
            # Creative content should be cached for shorter periods
            return base_ttl // 2
        elif request.task_type.value == "code_generation":
            # Code can be cached moderately
            return base_ttl

        # Adjust based on response characteristics
        if response.finish_reason == "length":
            # Truncated responses shouldn't be cached as long
            return base_ttl // 2

        return base_ttl

    async def invalidate_cache(self, pattern: str = None) -> int:
        """
        Invalidate cache entries
        If pattern is provided, invalidates matching keys
        Returns number of keys deleted
        """
        if not self.redis_client:
            await self.connect()

        try:
            if pattern:
                # Find matching keys
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {deleted} cache entries", pattern=pattern)
                    return deleted
                return 0
            else:
                # Clear all cache
                await self.redis_client.flushdb()
                logger.info("All cache entries invalidated")
                return -1  # Unknown count for full flush

        except Exception as e:
            logger.error("Cache invalidation failed", error=str(e), pattern=pattern)
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and Redis info"""
        stats = self.stats.copy()

        if self.redis_client:
            try:
                # Get Redis info
                info = await self.redis_client.info("memory")
                stats.update(
                    {
                        "redis_memory_used": info.get("used_memory_human", "unknown"),
                        "redis_connected": True,
                    }
                )

                # Calculate hit rate
                total_requests = stats["hits"] + stats["misses"]
                if total_requests > 0:
                    stats["hit_rate"] = stats["hits"] / total_requests
                else:
                    stats["hit_rate"] = 0.0

            except Exception as e:
                logger.warning("Failed to get Redis stats", error=str(e))
                stats["redis_connected"] = False
        else:
            stats["redis_connected"] = False

        return stats

    async def warm_cache(self, requests_responses: list) -> int:
        """
        Pre-populate cache with common request/response pairs
        Useful for warming up cache with frequently used prompts
        """
        if not self.redis_client:
            await self.connect()

        cached_count = 0

        for request, response in requests_responses:
            try:
                if await self.cache_response(request, response):
                    cached_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to warm cache entry",
                    request_id=getattr(request, "request_id", "unknown"),
                    error=str(e),
                )

        logger.info(f"Cache warmed with {cached_count} entries")
        return cached_count

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Cache manager connection closed")
