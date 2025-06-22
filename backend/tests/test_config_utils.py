"""
Tests for app.core.config utility functions.
These are simple utility functions that should be easy to test and improve coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.config import (
    reload_settings,
    is_feature_enabled,
    get_settings
)


class TestConfigUtilities:
    """Test config utility functions."""

    def test_is_feature_enabled_cosmos_db(self):
        """Test feature flag for cosmos_db."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.COSMOS_DB_ENABLED = True
            assert is_feature_enabled("cosmos_db") is True
            
            mock_settings.COSMOS_DB_ENABLED = False
            assert is_feature_enabled("cosmos_db") is False

    def test_is_feature_enabled_redis_cache(self):
        """Test feature flag for redis_cache."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.USE_REDIS_CACHE = True
            assert is_feature_enabled("redis_cache") is True
            
            mock_settings.USE_REDIS_CACHE = False
            assert is_feature_enabled("redis_cache") is False

    def test_is_feature_enabled_context_validation(self):
        """Test feature flag for context_validation."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.ENABLE_CONTEXT_VALIDATION = True
            assert is_feature_enabled("context_validation") is True
            
            mock_settings.ENABLE_CONTEXT_VALIDATION = False
            assert is_feature_enabled("context_validation") is False

    def test_is_feature_enabled_cost_tracking(self):
        """Test feature flag for cost_tracking."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.AI_COST_TRACKING_ENABLED = True
            assert is_feature_enabled("cost_tracking") is True
            
            mock_settings.AI_COST_TRACKING_ENABLED = False
            assert is_feature_enabled("cost_tracking") is False

    def test_is_feature_enabled_llm_orchestration(self):
        """Test feature flag for llm_orchestration."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.LLM_ORCHESTRATION_ENABLED = True
            assert is_feature_enabled("llm_orchestration") is True
            
            mock_settings.LLM_ORCHESTRATION_ENABLED = False
            assert is_feature_enabled("llm_orchestration") is False

    def test_is_feature_enabled_cache(self):
        """Test feature flag for cache."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = True
            assert is_feature_enabled("cache") is True
            
            mock_settings.CACHE_ENABLED = False
            assert is_feature_enabled("cache") is False

    def test_is_feature_enabled_debug(self):
        """Test feature flag for debug."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.DEBUG = True
            assert is_feature_enabled("debug") is True
            
            mock_settings.DEBUG = False
            assert is_feature_enabled("debug") is False

    def test_is_feature_enabled_unknown_feature(self):
        """Test feature flag for unknown feature returns False."""
        assert is_feature_enabled("unknown_feature") is False
        assert is_feature_enabled("nonexistent") is False

    @patch('app.core.config.get_settings')
    def test_reload_settings(self, mock_get_settings):
        """Test that reload_settings clears cache and returns new settings."""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Mock the cache_clear method
        mock_get_settings.cache_clear = MagicMock()
        
        result = reload_settings()
        
        # Verify cache_clear was called
        mock_get_settings.cache_clear.assert_called_once()
        
        # Verify get_settings was called after cache clear
        mock_get_settings.assert_called()
        assert result == mock_settings

    def test_feature_enabled_with_actual_settings(self):
        """Test feature enabled function with actual settings object."""
        # This tests the integration with real settings
        # The result will depend on actual configuration but should not raise errors
        result = is_feature_enabled("debug")
        assert isinstance(result, bool)
        
        result = is_feature_enabled("cache")
        assert isinstance(result, bool)

class TestSettingsIntegration:
    """Test settings integration."""

    def test_get_settings_returns_object(self):
        """Test that get_settings returns a settings object."""
        settings = get_settings()
        assert settings is not None
        
        # Should have common attributes
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'ENVIRONMENT')

    def test_settings_is_cached(self):
        """Test that settings object is cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same object due to lru_cache
        assert settings1 is settings2 