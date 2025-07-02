"""
Tests for app.core.logging_config utilities.
Testing the JSONFormatter and get_logger function.
"""

import json
import logging
from datetime import datetime

from app.core.logging_config import JSONFormatter, get_logger


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = JSONFormatter()

    def test_basic_log_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)

        # Should be valid JSON
        log_data = json.loads(result)

        # Check required fields
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "path"
        assert log_data["function"] == record.funcName
        assert log_data["line"] == 42

    def test_log_with_exception(self):
        """Test log formatting with exception info."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            result = self.formatter.format(record)
            log_data = json.loads(result)

            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]
            assert "Test exception" in log_data["exception"]

    def test_log_with_extra_fields(self):
        """Test log formatting with extra fields."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.user_id = "user123"
        record.request_id = "req456"
        record.custom_field = "custom_value"

        result = self.formatter.format(record)
        log_data = json.loads(result)

        # Extra fields should be included
        assert log_data["user_id"] == "user123"
        assert log_data["request_id"] == "req456"
        assert log_data["custom_field"] == "custom_value"

    def test_log_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        log_data = json.loads(result)

        # Should be valid ISO timestamp
        timestamp = log_data["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed_time, datetime)

    def test_log_excludes_internal_fields(self):
        """Test that internal logging fields are excluded."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        log_data = json.loads(result)

        # Internal fields should not be included
        internal_fields = [
            "name",
            "msg",
            "args",
            "levelno",
            "pathname",
            "filename",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_text",
            "stack_info",
        ]

        for field in internal_fields:
            assert field not in log_data

    def test_log_with_complex_message_args(self):
        """Test log formatting with message arguments."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message with %s and %d",
            args=("string_arg", 123),
            exc_info=None,
        )

        result = self.formatter.format(record)
        log_data = json.loads(result)

        assert log_data["message"] == "Test message with string_arg and 123"


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_adds_app_prefix(self):
        """Test that get_logger adds 'app.' prefix to logger name."""
        logger = get_logger("test_module")
        assert logger.name == "app.test_module"

    def test_get_logger_different_names(self):
        """Test that different module names create different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "app.module1"
        assert logger2.name == "app.module2"
        assert logger1 is not logger2

    def test_get_logger_same_name_returns_same_logger(self):
        """Test that same module name returns the same logger instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        # Should be the same logger instance
        assert logger1 is logger2

    def test_get_logger_with_empty_name(self):
        """Test get_logger with empty module name."""
        logger = get_logger("")
        assert logger.name == "app."

    def test_get_logger_with_dotted_name(self):
        """Test get_logger with dotted module name."""
        logger = get_logger("services.auth")
        assert logger.name == "app.services.auth"


class TestLoggingIntegration:
    """Test logging configuration integration."""

    def test_json_formatter_integration(self):
        """Test JSONFormatter integration with actual logging."""
        formatter = JSONFormatter()
        logger = logging.getLogger("test_integration")

        # Create a handler with our formatter
        import io

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log a message
        logger.info("Integration test message")

        # Get the formatted output
        log_output = log_stream.getvalue().strip()

        # Should be valid JSON
        log_data = json.loads(log_output)
        assert log_data["message"] == "Integration test message"
        assert log_data["level"] == "INFO"

        # Clean up
        logger.removeHandler(handler)

    def test_logger_hierarchy(self):
        """Test that app loggers form proper hierarchy."""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        assert parent_logger.name == "app.parent"
        assert child_logger.name == "app.parent.child"

        # Child should inherit from parent in logging hierarchy
        assert (
            child_logger.parent.name.startswith("app.parent") or child_logger.parent.name == "app"
        )
