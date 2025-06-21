"""
Redis-free caching alternatives for cost optimization.
Provides in-memory and SQLite-based caching to replace Redis.
Saves ~$40/month while maintaining performance for solo developer projects.
"""
import json
import sqlite3
import time
import asyncio
import threading
from functools import lru_cache, wraps
from typing import Any, Dict, Optional, List, Callable
from contextlib import contextmanager
from pathlib import Path
import pickle
import hashlib
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    timestamp: float
    ttl: int
    hit_count: int = 0
    last_accessed: float = 0


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.
    Good replacement for Redis caching in single-instance scenarios.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, return None if expired or not found."""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry.timestamp < entry.ttl:
                    entry.hit_count += 1
                    entry.last_accessed = time.time()
                    self._hits += 1
                    return entry.value
                else:
                    del self.cache[key]

            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            # Cleanup expired entries first
            self._cleanup_expired()

            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].last_accessed or self.cache[k].timestamp,
                )
                del self.cache[oldest_key]

            self.cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl,
                last_accessed=time.time(),
            )

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self._hits = 0
            self._misses = 0

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() if current_time - entry.timestamp >= entry.ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._cleanup_expired()
            total_requests = self._hits + self._misses
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / max(total_requests, 1),
                "total_requests": total_requests,
            }


class SQLiteCache:
    """SQLite-based persistent cache."""

    def __init__(self, db_path: str = "data/cache.db", default_ttl: int = 3600):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL,
                    ttl INTEGER
                )
            """
            )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value, timestamp, ttl FROM cache WHERE key = ?
            """,
                (key,),
            )
            row = cursor.fetchone()

            if row:
                value_blob, timestamp, ttl = row
                if time.time() - timestamp < ttl:
                    try:
                        return pickle.loads(value_blob)
                    except:
                        return json.loads(value_blob.decode())
                else:
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl

        try:
            value_blob = pickle.dumps(value)
        except:
            value_blob = json.dumps(value).encode()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache 
                (key, value, timestamp, ttl)
                VALUES (?, ?, ?, ?)
            """,
                (key, value_blob, time.time(), ttl),
            )
            conn.commit()

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0


class TaskQueue:
    """Simple database-backed task queue to replace Celery + Redis."""

    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()
        self._processors = {}

    def _init_db(self) -> None:
        """Initialize task queue database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    params TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at REAL,
                    completed_at REAL,
                    error TEXT
                )
            """
            )

    def add_task(self, task_name: str, params: Dict[str, Any] = None) -> int:
        """Add task to queue, return task ID."""
        params_json = json.dumps(params or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (name, params, created_at)
                VALUES (?, ?, ?)
            """,
                (task_name, params_json, time.time()),
            )
            conn.commit()
            return cursor.lastrowid

    def register_processor(self, task_name: str, processor_func: Callable):
        """Register a function to process tasks of given type."""
        self._processors[task_name] = processor_func


class CacheManager:
    """Unified cache manager with async interface."""

    def __init__(self, use_persistent: bool = False):
        self.memory_cache = memory_cache
        self.persistent_cache = persistent_cache
        self.default_cache = persistent_cache if use_persistent else memory_cache

    async def get(self, key: str) -> Optional[Any]:
        """Async get from cache."""
        return self.default_cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Async set to cache."""
        self.default_cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Async delete from cache."""
        return self.default_cache.delete(key)

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_data = ":".join(key_parts)
        if len(key_data) > 100:
            return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
        return key_data


# Global instances - Redis replacements
memory_cache = InMemoryCache(max_size=2000, default_ttl=3600)
persistent_cache = SQLiteCache(default_ttl=7200)
task_queue = TaskQueue()
cache_manager = CacheManager(use_persistent=False)


def cache_decorator(ttl: int = 3600):
    """Decorator for caching function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            result = memory_cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            memory_cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
