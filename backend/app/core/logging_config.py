"""
Logging configuration for the application.
"""

import json
import logging
import logging.config
import sys
from datetime import datetime, timezone
from typing import Dict, Any

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            } and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data, default=str)


def setup_logging():
    """Setup application logging configuration."""
    import os

    # Determine log level
    log_level = "DEBUG" if settings.DEBUG else "INFO"

    # Console handler
    console_handler = {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "json" if settings.is_production else "standard",
        "level": log_level,
    }

    # File handler for production (only if not in container)
    handlers = {"console": console_handler}

    # Only add file handler if we're in production AND not in a container
    # Container environments should use console logging only
    is_container = (
        os.getenv("CONTAINER_MODE", "false").lower() == "true"
        or os.path.exists("/.dockerenv")
        or os.getenv("KUBERNETES_SERVICE_HOST") is not None
    )

    if settings.is_production and not is_container:
        try:
            # Ensure log directory exists
            log_dir = "/var/log/pathfinder"
            os.makedirs(log_dir, exist_ok=True)

            file_handler = {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/var/log/pathfinder/app.log",
                "maxBytes": 50 * 1024 * 1024,  # 50MB
                "backupCount": 5,
                "formatter": "json",
                "level": "INFO",
            }
            handlers["file"] = file_handler
        except (OSError, PermissionError) as e:
            # If we can't create the log file, fall back to console only
            print(
                f"Warning: Could not set up file logging: {e}. Using console logging only.",
                file=sys.stderr,
            )

    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
        },
        "handlers": handlers,
        "loggers": {
            "app": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": list(handlers.keys()),
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "handlers": list(handlers.keys()),
            "level": "WARNING",
        },
    }

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Create application logger
    logger = logging.getLogger("app")
    logger.info(f"Logging configured for {settings.ENVIRONMENT} environment")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with application prefix."""
    return logging.getLogger(f"app.{name}")


class StructuredLogger:
    """Structured logger with correlation ID support."""

    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.correlation_id = None

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking."""
        self.correlation_id = correlation_id

    def _log(self, level: str, message: str, **kwargs: Any):
        """Internal log method with correlation ID."""
        extra: Dict[str, Any] = kwargs.copy()
        if self.correlation_id:
            extra["correlation_id"] = self.correlation_id

        getattr(self.logger, level.lower())(message, extra=extra)

    def debug(self, message: str, **kwargs: Any):
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any):
        """Log info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any):
        """Log warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any):
        """Log error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any):
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)


def create_logger(name: str) -> StructuredLogger:
    """Create a structured logger instance."""
    return StructuredLogger(name)
