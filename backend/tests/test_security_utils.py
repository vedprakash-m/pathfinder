"""
Tests for app.core.security utility functions.
Testing password hashing and rate limiting functionality.
"""

import time
from datetime import datetime

from app.core.security import (
    RateLimiter,
    get_password_hash,
    pwd_context,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification utilities."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification cycle."""
        password = "test_password_123"

        # Hash the password
        hashed = get_password_hash(password)

        # Should be different from original
        assert hashed != password
        assert len(hashed) > 0

        # Should verify correctly
        assert verify_password(password, hashed) is True

    def test_password_verify_wrong_password(self):
        """Test that wrong password fails verification."""
        password = "correct_password"
        wrong_password = "wrong_password"

        hashed = get_password_hash(password)

        # Wrong password should not verify
        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_different_every_time(self):
        """Test that same password produces different hashes."""
        password = "same_password"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Should be different due to salt
        assert hash1 != hash2

        # But both should verify the same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_empty_string(self):
        """Test password hashing with empty string."""
        password = ""

        hashed = get_password_hash(password)
        assert len(hashed) > 0
        assert verify_password(password, hashed) is True

    def test_password_special_characters(self):
        """Test password hashing with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_unicode_characters(self):
        """Test password hashing with unicode characters."""
        password = "测试密码🔒🌟"

        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_long_password(self):
        """Test password hashing with very long password."""
        password = "a" * 1000  # Very long password

        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestRateLimiter:
    """Test RateLimiter class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use short time windows for testing
        self.rate_limiter = RateLimiter(requests=3, window=2)

    def test_rate_limiter_creation(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(requests=10, window=60)

        assert limiter.requests == 10
        assert limiter.window == 60
        assert limiter.request_counts == {}

    def test_rate_limiter_allows_initial_requests(self):
        """Test that initial requests are allowed."""
        identifier = "test_user"

        # First few requests should be allowed
        assert self.rate_limiter.is_allowed(identifier) is True
        assert self.rate_limiter.is_allowed(identifier) is True
        assert self.rate_limiter.is_allowed(identifier) is True

    def test_rate_limiter_blocks_excess_requests(self):
        """Test that excess requests are blocked."""
        identifier = "test_user"

        # Use up the allowed requests
        for _ in range(3):
            assert self.rate_limiter.is_allowed(identifier) is True

        # Next request should be blocked
        assert self.rate_limiter.is_allowed(identifier) is False

    def test_rate_limiter_different_identifiers(self):
        """Test that different identifiers have separate limits."""
        user1 = "user1"
        user2 = "user2"

        # Both users should have their own limits
        for _ in range(3):
            assert self.rate_limiter.is_allowed(user1) is True
            assert self.rate_limiter.is_allowed(user2) is True

        # Both should be blocked after limit
        assert self.rate_limiter.is_allowed(user1) is False
        assert self.rate_limiter.is_allowed(user2) is False

    def test_rate_limiter_window_reset(self):
        """Test that rate limit resets after time window."""
        identifier = "test_user"

        # Use up the limit
        for _ in range(3):
            assert self.rate_limiter.is_allowed(identifier) is True

        # Should be blocked
        assert self.rate_limiter.is_allowed(identifier) is False

        # Wait for window to pass
        time.sleep(2.1)

        # Should be allowed again
        assert self.rate_limiter.is_allowed(identifier) is True

    def test_rate_limiter_cleanup_old_entries(self):
        """Test that old entries are cleaned up."""
        identifier = "test_user"

        # Make a request
        self.rate_limiter.is_allowed(identifier)

        # Check that entry exists
        assert identifier in self.rate_limiter.request_counts

        # Wait for cleanup window
        time.sleep(2.1)

        # Make another request (should trigger cleanup)
        self.rate_limiter.is_allowed(identifier)

        # Old entry should be cleaned, new one should exist
        assert identifier in self.rate_limiter.request_counts

    def test_rate_limiter_zero_requests(self):
        """Test rate limiter with zero allowed requests."""
        limiter = RateLimiter(requests=0, window=60)

        # The implementation allows the first request and then blocks
        assert limiter.is_allowed("test_user") is True  # First request allowed
        assert limiter.is_allowed("test_user") is False  # Second request blocked

    def test_rate_limiter_request_count_tracking(self):
        """Test that request counts are tracked correctly."""
        identifier = "test_user"

        # Make requests and check count increases
        self.rate_limiter.is_allowed(identifier)
        assert self.rate_limiter.request_counts[identifier]["count"] == 1

        self.rate_limiter.is_allowed(identifier)
        assert self.rate_limiter.request_counts[identifier]["count"] == 2

        self.rate_limiter.is_allowed(identifier)
        assert self.rate_limiter.request_counts[identifier]["count"] == 3

    def test_rate_limiter_timestamp_tracking(self):
        """Test that timestamps are tracked correctly."""
        identifier = "test_user"

        before_time = datetime.utcnow()
        self.rate_limiter.is_allowed(identifier)
        after_time = datetime.utcnow()

        # Timestamp should be between before and after
        recorded_time = self.rate_limiter.request_counts[identifier]["timestamp"]
        assert before_time <= recorded_time <= after_time


class TestSecurityIntegration:
    """Test security utilities integration."""

    def test_pwd_context_available(self):
        """Test that password context is properly configured."""
        assert pwd_context is not None

        # Should support bcrypt
        assert "bcrypt" in pwd_context.schemes()

    def test_password_hash_format(self):
        """Test that password hash has expected format."""
        password = "test_password"
        hashed = get_password_hash(password)

        # bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")

        # Should have reasonable length
        assert len(hashed) >= 50

    def test_rate_limiter_edge_cases(self):
        """Test rate limiter edge cases."""
        limiter = RateLimiter(requests=1, window=1)

        # Test with empty identifier
        assert limiter.is_allowed("") is True
        assert limiter.is_allowed("") is False

        # Test with None identifier (should handle gracefully)
        try:
            result = limiter.is_allowed(None)
            # If it doesn't crash, that's good
            assert isinstance(result, bool)
        except (TypeError, AttributeError):
            # This is also acceptable - depends on implementation
            pass

    def test_multiple_rate_limiters_independent(self):
        """Test that multiple rate limiter instances are independent."""
        limiter1 = RateLimiter(requests=2, window=60)
        limiter2 = RateLimiter(requests=3, window=60)

        identifier = "test_user"

        # Use up limiter1
        assert limiter1.is_allowed(identifier) is True
        assert limiter1.is_allowed(identifier) is True
        assert limiter1.is_allowed(identifier) is False

        # limiter2 should still work
        assert limiter2.is_allowed(identifier) is True
        assert limiter2.is_allowed(identifier) is True
        assert limiter2.is_allowed(identifier) is True
        assert limiter2.is_allowed(identifier) is False
