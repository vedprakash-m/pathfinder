"""
Unit tests for the cache service module.
"""

import pytest
from app.core.cache_service import CacheService, AICacheService


class TestCacheService:
    """Test cases for CacheService."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        return CacheService()

    def test_cache_service_initialization(self, cache_service):
        """Test cache service can be initialized."""
        assert cache_service is not None
        assert hasattr(cache_service, 'backend')
        assert hasattr(cache_service, 'ttl')

    @pytest.mark.asyncio
    async def test_get_set_cache(self, cache_service):
        """Test basic cache get/set operations."""
        test_key = "test_key"
        test_value = "test_value"
        
        # Set a value
        result = await cache_service.set(test_key, test_value)
        assert result is True
        
        # Get the value
        cached_value = await cache_service.get(test_key)
        assert cached_value == test_value

    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service):
        """Test cache delete operation."""
        test_key = "test_key_delete"
        test_value = "test_value_delete"
        
        # Set a value first
        await cache_service.set(test_key, test_value)
        
        # Delete it
        result = await cache_service.delete(test_key)
        assert result is True
        
        # Verify it's gone
        cached_value = await cache_service.get(test_key)
        assert cached_value is None

    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_service):
        """Test cache clear operation."""
        # Set some values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        
        result = await cache_service.clear()
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_cache(self, cache_service):
        """Test cache exists operation."""
        test_key = "test_exists_key"
        test_value = "test_exists_value"
        
        # Key should not exist initially
        exists_before = await cache_service.exists(test_key)
        assert exists_before is False
        
        # Set the key
        await cache_service.set(test_key, test_value)
        
        # Key should exist now
        exists_after = await cache_service.exists(test_key)
        assert exists_after is True

    def test_cache_key_generation(self, cache_service):
        """Test cache key generation."""
        key = cache_service.cache_key("prefix", "id", "suffix")
        assert isinstance(key, str)
        assert len(key) > 0

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test cache statistics."""
        result = await cache_service.get_stats()
        assert isinstance(result, dict)
        assert "backend" in result


class TestAICacheService:
    """Test cases for AICacheService."""

    @pytest.fixture
    def ai_cache_service(self):
        """Create AI cache service instance."""
        return AICacheService()

    def test_generate_cache_key(self, ai_cache_service):
        """Test AI cache key generation."""
        prompt = "Test prompt"
        model = "test-model"
        
        key = ai_cache_service.generate_cache_key(prompt, model)
        assert isinstance(key, str)
        assert "ai:" in key

    @pytest.mark.asyncio
    async def test_ai_response_caching(self, ai_cache_service):
        """Test AI response caching and retrieval."""
        prompt = "Test AI prompt"
        model = "test-model"
        response = {"response": "Test AI response", "usage": {"tokens": 100}}
        
        # Cache the response
        result = await ai_cache_service.set_ai_response(prompt, response, model)
        assert result is True
        
        # Retrieve the response
        cached_response = await ai_cache_service.get_ai_response(prompt, model)
        assert cached_response is not None
        assert cached_response["response"] == response 