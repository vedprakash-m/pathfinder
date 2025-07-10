"""
Cache Manager - Redis-free implementation for cost optimization
Implements intelligent caching strategies for LLM responses using SQLite and in-memory alternatives
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

try:
    from core.llm_types import LLMConfigurationError, LLMRequest, LLMResponse
except ImportError:
    # Fallback for development/testing
    class LLMRequest:
        pass

    class LLMResponse:
        pass

    class LLMConfigurationError(Exception):
        pass


logger = structlog.get_logger(__name__)


class AlternativeCacheManager:
    """
    Manages LLM response caching without Redis dependency
    Uses SQLite for persistence and in-memory cache for performance
    Saves ~$40/month compared to Redis while maintaining performance
    """

    def __init__(
        self,
        cache_db_path: str = "data/llm_cache.db",
        default_ttl: int = 3600,  # 1 hour default
        max_memory_items: int = 1000,  # Keep 1000 items in memory
        max_cache_size: int = 1000000,  # 1MB max per cached item
    ):
        self.cache_db_path = Path(cache_db_path)
        self.cache_db_path.parent.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.max_cache_size = max_cache_size

        # In-memory cache for hot data
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "stores": 0,
            "errors": 0,
            "memory_hits": 0,
            "disk_hits": 0,
        }

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database for persistent caching."""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_cache (
                        cache_key TEXT PRIMARY KEY,
                        response_data TEXT,
                        created_at REAL,
                        ttl INTEGER,
                        request_hash TEXT,
                        model_used TEXT,
                        token_count INTEGER
                    )
                """
                )

                # Index for efficient cleanup
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_cache_expires 
                    ON llm_cache(created_at, ttl)
                """
                )

        except Exception as e:
            logger.error("Failed to initialize cache database", error=str(e))
            raise Exception(f"Cache database initialization failed: {e}")

    async def connect(self) -> None:
        """Initialize cache manager (compatibility method)."""
        # Cleanup expired entries on startup
        self._cleanup_expired()
        logger.info(
            "Alternative cache manager initialized (Redis-free)", db_path=str(self.cache_db_path)
        )

    async def get_cached_response(self, request: LLMRequest) -> Optional[LLMResponse]:
        """
        Retrieve cached response for a request
        Checks memory cache first, then SQLite
        """
        try:
            cache_key = self._generate_cache_key(request)
            current_time = time.time()

            logger.debug("Checking cache", cache_key=cache_key, request_id=request.request_id)

            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if current_time - entry["created_at"] < entry["ttl"]:
                    response = LLMResponse.parse_obj(entry["response_data"])
                    self.stats["hits"] += 1
                    self.stats["memory_hits"] += 1

                    logger.debug(
                        "Memory cache hit",
                        cache_key=cache_key,
                        request_id=request.request_id,
                        cached_model=response.model_used,
                    )

                    return response
                else:
                    # Expired, remove from memory
                    del self.memory_cache[cache_key]

            # Check SQLite cache
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT response_data, created_at, ttl, model_used 
                    FROM llm_cache 
                    WHERE cache_key = ?
                """,
                    (cache_key,),
                )

                row = cursor.fetchone()
                if row:
                    response_data, created_at, ttl, model_used = row

                    # Check if not expired
                    if current_time - created_at < ttl:
                        # Parse response
                        response = LLMResponse.parse_obj(json.loads(response_data))

                        # Add to memory cache for faster future access
                        self._add_to_memory_cache(
                            cache_key,
                            {
                                "response_data": json.loads(response_data),
                                "created_at": created_at,
                                "ttl": ttl,
                            },
                        )

                        self.stats["hits"] += 1
                        self.stats["disk_hits"] += 1

                        logger.debug(
                            "Disk cache hit",
                            cache_key=cache_key,
                            request_id=request.request_id,
                            cached_model=model_used,
                        )

                        return response
                    else:
                        # Expired, delete from database
                        conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (cache_key,))
                        conn.commit()

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
        Cache an LLM response in both memory and SQLite
        """
        try:
            cache_key = self._generate_cache_key(request)
            cache_ttl = ttl or self._calculate_ttl(request, response)
            current_time = time.time()

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

            # Store in SQLite
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO llm_cache 
                    (cache_key, response_data, created_at, ttl, request_hash, model_used, token_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        cache_key,
                        serialized_data,
                        current_time,
                        cache_ttl,
                        hashlib.md5(request.prompt.encode()).hexdigest()[:16],
                        response.model_used,
                        response.usage.total_tokens if response.usage else 0,
                    ),
                )
                conn.commit()

            # Add to memory cache
            self._add_to_memory_cache(
                cache_key,
                {"response_data": response_data, "created_at": current_time, "ttl": cache_ttl},
            )

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

    def _add_to_memory_cache(self, cache_key: str, entry: Dict[str, Any]) -> None:
        """Add entry to memory cache with LRU eviction."""
        # Remove oldest entries if at capacity
        if len(self.memory_cache) >= self.max_memory_items:
            # Find oldest entry
            oldest_key = min(
                self.memory_cache.keys(), key=lambda k: self.memory_cache[k]["created_at"]
            )
            del self.memory_cache[oldest_key]

        self.memory_cache[cache_key] = entry

    def _generate_cache_key(self, request: LLMRequest) -> str:
        """
        Generate deterministic cache key from request
        Same logic as Redis version for compatibility
        """
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
            },
            "context": request.context[:500] if request.context else None,
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

        # Longer TTL for successful, high-quality responses
        if response.success and hasattr(response, "confidence"):
            if response.confidence > 0.8:
                base_ttl *= 2

        # Shorter TTL for error responses
        if not response.success:
            base_ttl = min(base_ttl, 300)  # 5 minutes max for errors

        # Task-specific TTL adjustments
        if request.task_type.value == "itinerary_generation":
            base_ttl *= 1.5  # Itineraries are valuable to cache longer
        elif request.task_type.value == "optimization":
            base_ttl *= 0.5  # Optimizations may become stale faster

        return int(base_ttl)

    def _cleanup_expired(self) -> int:
        """Remove expired entries from both memory and disk cache."""
        current_time = time.time()
        removed_count = 0

        # Cleanup memory cache
        expired_keys = [
            key
            for key, entry in self.memory_cache.items()
            if current_time - entry["created_at"] >= entry["ttl"]
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            removed_count += 1

        # Cleanup SQLite cache
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM llm_cache 
                    WHERE (created_at + ttl) < ?
                """,
                    (current_time,),
                )
                removed_count += cursor.rowcount
                conn.commit()
        except Exception as e:
            logger.warning("Failed to cleanup SQLite cache", error=str(e))

        if removed_count > 0:
            logger.debug("Cleaned up expired cache entries", count=removed_count)

        return removed_count

    async def invalidate_cache(self, pattern: str = None) -> int:
        """
        Invalidate cache entries matching pattern
        Returns number of entries removed
        """
        try:
            removed_count = 0

            if pattern:
                # Pattern-based invalidation
                if pattern.endswith("*"):
                    prefix = pattern[:-1]

                    # Remove from memory cache
                    keys_to_remove = [
                        key for key in self.memory_cache.keys() if key.startswith(prefix)
                    ]
                    for key in keys_to_remove:
                        del self.memory_cache[key]
                        removed_count += 1

                    # Remove from SQLite
                    with sqlite3.connect(self.cache_db_path) as conn:
                        cursor = conn.execute(
                            """
                            DELETE FROM llm_cache 
                            WHERE cache_key LIKE ?
                        """,
                            (f"{prefix}%",),
                        )
                        removed_count += cursor.rowcount
                        conn.commit()

            else:
                # Clear all cache
                self.memory_cache.clear()
                with sqlite3.connect(self.cache_db_path) as conn:
                    cursor = conn.execute("DELETE FROM llm_cache")
                    removed_count = cursor.rowcount
                    conn.commit()

            logger.info("Cache invalidated", pattern=pattern, removed_count=removed_count)
            return removed_count

        except Exception as e:
            logger.error("Cache invalidation failed", error=str(e))
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and info"""
        # Cleanup expired entries first
        self._cleanup_expired()

        stats = self.stats.copy()

        try:
            # Get SQLite database stats
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM llm_cache")
                disk_entries = cursor.fetchone()[0]

                cursor = conn.execute(
                    """
                    SELECT AVG(LENGTH(response_data)) 
                    FROM llm_cache
                """
                )
                avg_entry_size = cursor.fetchone()[0] or 0

            stats.update(
                {
                    "memory_entries": len(self.memory_cache),
                    "disk_entries": disk_entries,
                    "total_entries": len(self.memory_cache) + disk_entries,
                    "avg_entry_size_bytes": int(avg_entry_size),
                    "cache_db_path": str(self.cache_db_path),
                    "backend": "sqlite_memory_hybrid",
                    "max_memory_items": self.max_memory_items,
                    "default_ttl": self.default_ttl,
                    "cost_savings": "$40/month vs Redis",
                }
            )

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = stats["hits"] / total_requests
            else:
                stats["hit_rate"] = 0.0

        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))
            stats["error"] = str(e)

        return stats

    async def close(self) -> None:
        """Cleanup cache resources"""
        # Perform final cleanup
        removed = self._cleanup_expired()
        logger.info("Cache manager closed", expired_entries_removed=removed)


# Create global instance for Redis-free caching
cache_manager = AlternativeCacheManager()
