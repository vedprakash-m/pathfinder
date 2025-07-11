"""
Unit tests for the audit module.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from app.core.audit import AuditLog, AuditLogger, audit_logger


class TestAuditLog:
    """Test cases for AuditLog class."""

    def test_audit_log_initialization(self):
        """Test audit log can be initialized with minimal parameters."""
        log = AuditLog(event_type="test_event")

        assert log.event_type == "test_event"
        assert log.event_id is not None
        assert log.timestamp is not None
        assert log.status == "success"
        assert log.details == {}
        assert log.ip_address == "unknown"
        assert log.user_agent == "unknown"
        assert log.path is None
        assert log.method is None

    def test_audit_log_with_all_parameters(self):
        """Test audit log with all parameters."""
        details = {"key": "value", "count": 123}
        log = AuditLog(
            event_type="data_access",
            user_id="user123",
            resource_type="trip",
            resource_id="trip456",
            action="read",
            status="success",
            details=details,
        )

        assert log.event_type == "data_access"
        assert log.user_id == "user123"
        assert log.resource_type == "trip"
        assert log.resource_id == "trip456"
        assert log.action == "read"
        assert log.status == "success"
        assert log.details == details

    def test_audit_log_with_request(self):
        """Test audit log with request object."""
        # Mock request object
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0 Test Browser"
        mock_request.url.path = "/api/v1/trips"
        mock_request.method = "GET"

        log = AuditLog(event_type="access", user_id="user123", request=mock_request)

        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0 Test Browser"
        assert log.path == "/api/v1/trips"
        assert log.method == "GET"

    def test_audit_log_with_request_no_client(self):
        """Test audit log with request object that has no client."""
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers.get.return_value = "Test Browser"
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "POST"

        log = AuditLog(event_type="test", request=mock_request)

        assert log.ip_address == "unknown"
        assert log.user_agent == "Test Browser"
        assert log.path == "/api/v1/test"
        assert log.method == "POST"

    def test_audit_log_to_dict(self):
        """Test converting audit log to dictionary."""
        log = AuditLog(event_type="auth", user_id="user123", action="login")

        result = log.to_dict()

        assert isinstance(result, dict)
        assert result["event_type"] == "auth"
        assert result["user_id"] == "user123"
        assert result["action"] == "login"
        assert result["event_id"] == log.event_id
        assert result["timestamp"] == log.timestamp
        assert "environment" in result

    def test_audit_log_to_json(self):
        """Test converting audit log to JSON string."""
        log = AuditLog(event_type="security", details={"severity": "high"})

        json_str = log.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "security"
        assert parsed["details"]["severity"] == "high"


class TestAuditLogger:
    """Test cases for AuditLogger class."""

    @pytest.fixture
    def logger(self):
        """Create audit logger instance."""
        return AuditLogger()

    def test_audit_logger_initialization(self, logger):
        """Test audit logger initialization."""
        assert logger.enable_console is True
        assert logger.enable_db is False  # Default for non-production

    @patch("app.core.audit.settings.ENVIRONMENT", "production")
    def test_audit_logger_production_mode(self):
        """Test audit logger in production mode."""
        with patch("app.core.audit.get_settings") as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "production"
            logger = AuditLogger()
            assert logger.enable_db is True

    @pytest.mark.asyncio
    async def test_log_event_basic(self, logger):
        """Test basic event logging."""
        with patch("app.core.audit.logger") as mock_logger:
            event_id = await logger.log_event(event_type="test", user_id="user123")

            assert event_id is not None
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_failure_status(self, logger):
        """Test logging event with failure status."""
        with patch("app.core.audit.logger") as mock_logger:
            await logger.log_event(event_type="test", status="failure")

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_auth_event(self, logger):
        """Test logging authentication event."""
        with patch("app.core.audit.logger") as mock_logger:
            event_id = await logger.log_auth_event(
                event="login", user_id="user123", details={"method": "password"}
            )

            assert event_id is not None
            mock_logger.info.assert_called_once()

            # Check that the logged message contains expected data
            call_args = mock_logger.info.call_args[0][0]
            assert "auth" in call_args
            assert "user123" in call_args
            assert "login" in call_args

    @pytest.mark.asyncio
    async def test_log_access_event(self, logger):
        """Test logging access event."""
        with patch("app.core.audit.logger") as mock_logger:
            event_id = await logger.log_access_event(
                user_id="user456",
                resource_type="trip",
                resource_id="trip789",
                action="read",
            )

            assert event_id is not None
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_data_change(self, logger):
        """Test logging data change event."""
        before_data = {"status": "draft"}
        after_data = {"status": "published"}

        with patch("app.core.audit.logger") as mock_logger:
            event_id = await logger.log_data_change(
                user_id="user789",
                resource_type="trip",
                resource_id="trip101",
                action="update",
                before=before_data,
                after=after_data,
            )

            assert event_id is not None
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_security_event(self, logger):
        """Test logging security event."""
        with patch("app.core.audit.logger") as mock_logger:
            event_id = await logger.log_security_event(
                event="suspicious_activity",
                user_id="user999",
                details={"threat_level": "medium"},
            )

            assert event_id is not None
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_console_logging_disabled(self, logger):
        """Test when console logging is disabled."""
        logger.enable_console = False

        with patch("app.core.audit.logger") as mock_logger:
            await logger.log_event(event_type="test")

            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_logging_enabled(self, logger):
        """Test when database logging is enabled."""
        logger.enable_db = True

        # Since DB logging is just a pass statement, we test that it doesn't error
        event_id = await logger.log_event(event_type="test")
        assert event_id is not None


class TestGlobalAuditLogger:
    """Test the global audit logger instance."""

    def test_global_audit_logger_exists(self):
        """Test that global audit logger instance exists."""
        assert audit_logger is not None
        assert isinstance(audit_logger, AuditLogger)

    @pytest.mark.asyncio
    async def test_global_audit_logger_usage(self):
        """Test using the global audit logger."""
        with patch("app.core.audit.logger") as mock_logger:
            event_id = await audit_logger.log_event(
                event_type="global_test", user_id="global_user"
            )

            assert event_id is not None
            mock_logger.info.assert_called_once()
