"""
Tests for app.core.cache_alternatives utilities.
Testing the simple cache implementations and utilities.
"""

import pytest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock

from app.core.cache_alternatives import (
    InMemoryCache,
    cache_decorator,
    memory_cache,
    CacheEntry
)


class TestCacheEntry:
    """Test CacheEntry helper class."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation with basic values."""
        entry = CacheEntry(
            value="test_value",
            timestamp=time.time(),
            ttl=10
        )
        
        assert entry.value == "test_value"
        assert entry.ttl == 10
        assert entry.hit_count == 0
        assert entry.last_accessed == 0

    def test_cache_entry_with_metadata(self):
        """Test CacheEntry with hit count and last accessed."""
        current_time = time.time()
        entry = CacheEntry(
            value="test_value",
            timestamp=current_time,
            ttl=10,
            hit_count=5,
            last_accessed=current_time
        )
        
        assert entry.hit_count == 5
        assert entry.last_accessed == current_time


class TestInMemoryCache:
    """Test InMemoryCache implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = InMemoryCache(max_size=10, default_ttl=10)

    def test_cache_creation(self):
        """Test cache initialization."""
        cache = InMemoryCache()
        assert cache.cache == {}
        assert cache.max_size == 1000  # default
        assert cache.default_ttl == 3600  # default
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value, ttl=10)
        retrieved = self.cache.get(key)
        assert retrieved == value

    def test_cache_get_miss(self):
        """Test cache get with missing key."""
        result = self.cache.get("nonexistent_key")
        assert result is None

    def test_cache_expiry(self):
        """Test that cached items expire correctly."""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value, ttl=1)
        
        # Immediately should be available
        assert self.cache.get(key) == value
        
        # After expiry should be None
        time.sleep(1.1)
        assert self.cache.get(key) is None

    def test_cache_delete(self):
        """Test cache delete operation."""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value, ttl=10)
        assert self.cache.get(key) == value
        
        result = self.cache.delete(key)
        assert result is True
        assert self.cache.get(key) is None

    def test_cache_delete_nonexistent(self):
        """Test deleting non-existent key."""
        result = self.cache.delete("nonexistent_key")
        assert result is False

    def test_cache_clear(self):
        """Test cache clear operation."""
        self.cache.set("key1", "value1", ttl=10)
        self.cache.set("key2", "value2", ttl=10)
        
        assert self.cache.get("key1") == "value1"
        assert self.cache.get("key2") == "value2"
        
        self.cache.clear()
        
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None

    def test_cache_hit_count_tracking(self):
        """Test that hit counts are tracked correctly."""
        key = "test_key"
        value = "test_value"
        
        self.cache.set(key, value, ttl=10)
        
        # Multiple gets should increase hit count
        self.cache.get(key)
        self.cache.get(key)
        self.cache.get(key)
        
        entry = self.cache.cache[key]
        assert entry.hit_count == 3

    def test_cache_stats(self):
        """Test cache statistics."""
        # Initially empty
        stats = self.cache.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Add some data and access it
        self.cache.set("key1", "value1", ttl=10)
        self.cache.get("key1")  # hit
        self.cache.get("key2")  # miss
        
        stats = self.cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_max_size_eviction(self):
        """Test that cache evicts oldest items when max size reached."""
        small_cache = InMemoryCache(max_size=2, default_ttl=10)
        
        # Fill cache to capacity
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        
        # Access key1 to make it more recently accessed
        small_cache.get("key1")
        
        # Add another item - should evict key2 (least recently accessed)
        small_cache.set("key3", "value3")
        
        assert small_cache.get("key1") == "value1"  # Should still be there
        assert small_cache.get("key2") is None       # Should be evicted
        assert small_cache.get("key3") == "value3"  # Should be there

    def test_cache_cleanup_expired(self):
        """Test automatic cleanup of expired items."""
        self.cache.set("short_ttl", "value1", ttl=1)
        self.cache.set("long_ttl", "value2", ttl=10)
        
        # Both should be available initially
        assert self.cache.get("short_ttl") == "value1"
        assert self.cache.get("long_ttl") == "value2"
        
        # Wait for short TTL to expire
        time.sleep(1.1)
        
        # Access should trigger cleanup
        assert self.cache.get("short_ttl") is None  # Expired
        assert self.cache.get("long_ttl") == "value2"  # Still valid

    def test_cache_default_ttl(self):
        """Test cache uses default TTL when none specified."""
        cache = InMemoryCache(default_ttl=5)
        cache.set("test_key", "test_value")  # No TTL specified
        
        entry = cache.cache["test_key"]
        assert entry.ttl == 5


class TestCacheDecorator:
    """Test cache_decorator function."""

    def test_cache_decorator_basic(self):
        """Test basic cache decorator functionality."""
        call_count = 0
        
        @cache_decorator(ttl=10)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call with same args should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Different args should execute function again
        result3 = test_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cache_decorator_with_kwargs(self):
        """Test cache decorator with keyword arguments."""
        call_count = 0
        
        @cache_decorator(ttl=10)
        def test_function(x, multiplier=2):
            nonlocal call_count
            call_count += 1
            return x * multiplier
        
        # Test with kwargs
        result1 = test_function(5, multiplier=3)
        assert result1 == 15
        assert call_count == 1
        
        # Same call should use cache
        result2 = test_function(5, multiplier=3)
        assert result2 == 15
        assert call_count == 1
        
        # Different kwargs should execute again
        result3 = test_function(5, multiplier=4)
        assert result3 == 20
        assert call_count == 2

    def test_cache_decorator_default_ttl(self):
        """Test cache decorator with default TTL."""
        @cache_decorator()  # No TTL specified
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10

    def test_cache_decorator_different_functions(self):
        """Test that different functions have separate cache spaces."""
        @cache_decorator(ttl=10)
        def function1(x):
            return x * 2
        
        @cache_decorator(ttl=10)
        def function2(x):
            return x * 3
        
        result1 = function1(5)
        result2 = function2(5)
        
        assert result1 == 10
        assert result2 == 15


class TestGlobalCacheInstances:
    """Test global cache instances."""

    def test_memory_cache_instance(self):
        """Test that memory_cache is properly initialized."""
        assert memory_cache is not None
        assert isinstance(memory_cache, InMemoryCache)

    def test_memory_cache_functionality(self):
        """Test that global memory_cache works correctly."""
        key = "global_test_key"
        value = "global_test_value"
        
        # Use the global instance
        memory_cache.set(key, value, ttl=10)
        result = memory_cache.get(key)
        
        assert result == value
        
        # Clean up
        memory_cache.delete(key)

    def test_cache_instances_are_different(self):
        """Test that different cache instances are separate."""
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        
        cache1.set("test_key", "value1", ttl=10)
        cache2.set("test_key", "value2", ttl=10)
        
        assert cache1.get("test_key") == "value1"
        assert cache2.get("test_key") == "value2"


class TestCacheIntegration:
    """Test cache integration and edge cases."""

    def test_cache_with_complex_values(self):
        """Test caching complex data types."""
        cache = InMemoryCache()
        
        # Test with different data types
        test_data = {
            "string": "test_value",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "bool": True,
            "none": None
        }
        
        for key, value in test_data.items():
            cache.set(key, value, ttl=10)
            retrieved = cache.get(key)
            assert retrieved == value

    def test_cache_key_collision_handling(self):
        """Test that different keys don't collide."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1", ttl=10)
        cache.set("key2", "value2", ttl=10)
        cache.set("key11", "value11", ttl=10)  # Similar but different
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key11") == "value11"

    def test_cache_thread_safety_basic(self):
        """Test basic thread safety of cache operations."""
        import threading
        
        cache = InMemoryCache()
        results = []
        
        def cache_operations():
            cache.set("thread_key", "thread_value", ttl=5)
            result = cache.get("thread_key")
            results.append(result)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_operations)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should have succeeded
        assert len(results) == 5
        assert all(result == "thread_value" for result in results) 