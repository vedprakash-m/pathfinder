"""
Unified configuration management system for Pathfinder application.
Implements standardized environment variable handling, validation, and defaults.
"""

import logging
import os
import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class UnifiedSettings(BaseSettings):
    """
    Unified application settings with comprehensive validation and standardized patterns.
    Implements the configuration management standards from the tech debt remediation plan.
    """

    # ==================== CORE APPLICATION SETTINGS ====================
    APP_NAME: str = Field(default="Pathfinder API", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Application secret key",
    )

    # ==================== SERVER CONFIGURATION ====================
    HOST: str = Field(default="0.0.0.0", description="Server host address")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")
    ALLOWED_HOSTS: Union[List[str], str] = Field(
        default=["localhost", "127.0.0.1"], description="Allowed host headers"
    )

    # ==================== CORS CONFIGURATION ====================
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated List[Any] of CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow CORS credentials")
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods",
    )
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed CORS headers")

    # ==================== DATABASE CONFIGURATION ====================
    DATABASE_URL: str = Field(
        default_factory=lambda: (
            "sqlite+aiosqlite:///:memory:"
            if os.getenv("ENVIRONMENT", "").lower() in ["test", "testing"]
            else "sqlite+aiosqlite:///pathfinder.db"
        ),
        description="Primary database connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(
        default=10, ge=1, le=50, description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=20, ge=0, le=100, description="Database max overflow connections"
    )
    DATABASE_TIMEOUT: int = Field(
        default=30, ge=5, le=300, description="Database connection timeout in seconds"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Enable database query logging")

    # ==================== COSMOS DB CONFIGURATION ====================
    # Unified Cosmos DB approach per Tech Spec
    COSMOS_DB_ENABLED: bool = Field(
        default=False,  # Simplified: disabled by default for cost optimization
        description="Enable unified Cosmos DB integration",
    )
    COSMOS_DB_URL: Optional[str] = Field(default=None, description="Cosmos DB endpoint URL")
    COSMOS_DB_KEY: Optional[str] = Field(default=None, description="Cosmos DB primary key")
    COSMOS_DB_DATABASE: str = Field(default="pathfinder", description="Cosmos DB database name")
    COSMOS_DB_CONTAINER: str = Field(
        default="entities", description="Unified entities container name"
    )

    # Legacy SQL Database (to be deprecated)
    USE_SQL_DATABASE: bool = Field(default=False, description="Use SQL database (legacy)")

    # Legacy container names (deprecated - will be removed after migration)
    COSMOS_DB_CONTAINER_ITINERARIES: str = Field(
        default="itineraries", description="Legacy: Itineraries container name"
    )
    COSMOS_DB_CONTAINER_MESSAGES: str = Field(
        default="messages", description="Legacy: Messages container name"
    )
    COSMOS_DB_CONTAINER_PREFERENCES: str = Field(
        default="preferences", description="Legacy: Preferences container name"
    )

    # ==================== CACHE CONFIGURATION ====================
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching layer")
    CACHE_TYPE: str = Field(default="memory", description="Cache backend type")
    CACHE_TTL: int = Field(
        default=3600, ge=60, le=86400, description="Default cache TTL in seconds"
    )
    CACHE_MAX_SIZE: int = Field(default=2000, ge=100, le=10000, description="Maximum cache entries")
    CACHE_DB_PATH: str = Field(default="data/cache.db", description="SQLite cache database path")

    # Redis settings (optional)
    REDIS_URL: Optional[str] = Field(default=None, description="Redis connection URL")
    REDIS_TTL: int = Field(default=3600, ge=60, le=86400, description="Redis TTL in seconds")
    USE_REDIS_CACHE: bool = Field(default=False, description="Use Redis for caching")

    # ==================== AUTHENTICATION CONFIGURATION ====================
    # Microsoft Entra ID Configuration (Vedprakash Domain Standard)
    ENTRA_EXTERNAL_TENANT_ID: Optional[str] = Field(
        default="vedid.onmicrosoft.com",  # ✅ Fixed to Vedprakash domain standard
        description="Microsoft Entra ID tenant ID - Vedprakash domain standard",
    )
    ENTRA_EXTERNAL_CLIENT_ID: Optional[str] = Field(
        default=None,  # Simplified: get from env var or None
        description="Microsoft Entra ID application client ID",
    )
    ENTRA_EXTERNAL_AUTHORITY: Optional[str] = Field(
        default="https://login.microsoftonline.com/vedid.onmicrosoft.com",  # ✅ Fixed to Vedprakash domain
        description="Microsoft Entra ID authority URL - Vedprakash domain standard",
    )
    ENTRA_EXTERNAL_CLIENT_SECRET: Optional[str] = Field(
        default=None,  # Simplified: get from env var or None
        description="Microsoft Entra ID client secret (optional for public clients)",
    )
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT signing algorithm")
    JWT_EXPIRATION: int = Field(
        default=3600, ge=300, le=86400, description="JWT expiration time in seconds"
    )

    # ==================== AI SERVICES CONFIGURATION ====================
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,  # Simplified: get from env var or None
        description="OpenAI API key",
    )
    OPENAI_MODEL_PRIMARY: str = Field(default="gpt-4o-mini", description="Primary OpenAI model")
    OPENAI_MODEL_FALLBACK: str = Field(default="gpt-4o", description="Fallback OpenAI model")
    OPENAI_MAX_TOKENS: int = Field(
        default=2000, ge=100, le=8000, description="Maximum tokens per request"
    )
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    OPENAI_TIMEOUT: int = Field(default=60, ge=10, le=300, description="API request timeout")

    # ==================== EXTERNAL SERVICES ====================
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(
        default=None,  # Simplified: get from env var or None
        description="Google Maps API key",
    )

    # Email services
    SENDGRID_API_KEY: Optional[str] = Field(default=None, description="SendGrid API key")
    FROM_EMAIL: str = Field(default="noreply@pathfinder.com", description="Default sender email")
    FROM_NAME: str = Field(default="Pathfinder", description="Default sender name")

    # SMTP fallback
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server host")
    SMTP_PORT: int = Field(default=587, ge=25, le=65535, description="SMTP server port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS for SMTP")

    # ==================== SECURITY CONFIGURATION ====================
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, ge=10, le=10000, description="Rate limit requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=3600, ge=60, le=86400, description="Rate limit window in seconds"
    )

    # File upload security
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
        description="Maximum file size in bytes",
    )
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "application/pdf"],
        description="Allowed MIME types for file uploads",
    )

    # Context validation
    ENABLE_CONTEXT_VALIDATION: bool = Field(
        default=False, description="Enable security context validation"
    )
    MAX_RISK_THRESHOLD: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Maximum security risk threshold"
    )
    MFA_TRIGGER_THRESHOLD: float = Field(
        default=0.5, ge=0.0, le=1.0, description="MFA trigger threshold"
    )

    # ==================== AZURE SERVICES ====================
    AZURE_STORAGE_ACCOUNT: Optional[str] = Field(
        default=None, description="Azure Storage account name"
    )
    AZURE_STORAGE_KEY: Optional[str] = Field(default=None, description="Azure Storage account key")
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None, description="Azure Storage connection string"
    )
    AZURE_STORAGE_CONTAINER: str = Field(
        default="uploads", description="Azure Storage container name"
    )

    # Application Insights
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = Field(
        default=None, description="Application Insights connection string"
    )

    # ==================== PERFORMANCE MONITORING ====================
    SLOW_REQUEST_THRESHOLD: float = Field(
        default=1.0, ge=0.1, le=60.0, description="Slow request threshold in seconds"
    )
    SLOW_QUERY_THRESHOLD: float = Field(
        default=0.5, ge=0.1, le=30.0, description="Slow query threshold in seconds"
    )
    METRICS_ROLLUP_INTERVAL: int = Field(
        default=300, ge=60, le=3600, description="Metrics rollup interval in seconds"
    )

    # ==================== AI COST TRACKING ====================
    AI_COST_TRACKING_ENABLED: bool = Field(default=True, description="Enable AI cost tracking")
    AI_DAILY_BUDGET_LIMIT: float = Field(
        default=50.0, ge=1.0, le=1000.0, description="Daily AI budget limit in USD"
    )

    # ==================== WEBSOCKET CONFIGURATION ====================
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(
        default=30, ge=10, le=300, description="WebSocket heartbeat interval"
    )
    WEBSOCKET_MAX_CONNECTIONS: int = Field(
        default=1000, ge=10, le=10000, description="Maximum WebSocket connections"
    )

    # ==================== LLM ORCHESTRATION ====================
    LLM_ORCHESTRATION_ENABLED: bool = Field(
        default=False, description="Enable LLM orchestration service"
    )
    LLM_ORCHESTRATION_URL: Optional[str] = Field(
        default=None, description="LLM orchestration service URL"
    )
    LLM_ORCHESTRATION_API_KEY: Optional[str] = Field(
        default=None, description="LLM orchestration API key"
    )
    LLM_ORCHESTRATION_TIMEOUT: int = Field(
        default=60, ge=10, le=300, description="LLM orchestration timeout"
    )

    # ==================== LEGACY SETTINGS COMPATIBILITY ====================
    # Temporary fields for backward compatibility during migration
    TRUSTED_LOCATIONS: List[str] = Field(default=[], description="Trusted location patterns")
    TRUSTED_NETWORKS: List[str] = Field(
        default=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        description="Trusted network CIDR blocks",
    )
    WORKING_HOURS_START: int = Field(
        default=8, ge=0, le=23, description="Working hours start (24h format)"
    )
    WORKING_HOURS_END: int = Field(
        default=18, ge=0, le=23, description="Working hours end (24h format)"
    )
    WORKING_HOURS_TIMEZONE: str = Field(default="UTC", description="Working hours timezone")
    USER_PATTERNS_FILE: str = Field(
        default="user_access_patterns.json", description="User patterns storage file"
    )
    SLOW_FUNCTION_THRESHOLD: float = Field(
        default=0.5, ge=0.1, le=30.0, description="Slow function threshold"
    )

    # ==================== VALIDATION METHODS ====================

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug_mode(cls, v, info) -> None:
        """Ensure DEBUG is properly disabled in production."""
        environment = (
            info.data.get("ENVIRONMENT", "development") if hasattr(info, "data") else "development"
        )
        if environment.lower() == "production" and v is True:
            logger.warning("DEBUG mode is enabled in production environment - forcing to False")
            return False
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v, info) -> None:
        """Validate and secure allowed hosts configuration."""
        environment = (
            info.data.get("ENVIRONMENT", "development") if hasattr(info, "data") else "development"
        )

        # Convert string to List[Any] if needed
        if isinstance(v, str):
            hosts = [host.strip() for host in v.split(",") if host.strip()]
        else:
            hosts = v if isinstance(v, List[Any]) else ["localhost", "127.0.0.1"]

        # Security check for production
        if environment.lower() == "production" and "*" in hosts:
            logger.warning("Wildcard host '*' detected in production - this is a security risk")
            # Remove wildcard in production unless explicitly allowed
            hosts = [h for h in hosts if h != "*"]
            if not hosts:
                hosts = ["localhost"]

        return hosts

    @field_validator("ENTRA_EXTERNAL_AUTHORITY", mode="before")
    @classmethod
    def set_entra_authority(cls, v, info) -> None:
        """Set Entra External ID authority from tenant ID if not provided."""
        if v is None and hasattr(info, "data") and "ENTRA_EXTERNAL_TENANT_ID" in info.data:
            tenant_id = info.data["ENTRA_EXTERNAL_TENANT_ID"]
            return f"https://login.microsoftonline.com/{tenant_id}"
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v, info) -> None:
        """Validate CORS origins for security."""
        environment = (
            info.data.get("ENVIRONMENT", "development") if hasattr(info, "data") else "development"
        )

        if not v:
            return "http://localhost:3000,http://localhost:5173"

        # Check for wildcard in production
        if environment.lower() == "production" and "*" in v:
            logger.warning("CORS wildcard '*' detected in production - this is a security risk")

        return v

    @model_validator(mode="after")
    def validate_database_configuration(self) -> None:
        """Validate database configuration consistency."""
        if self.COSMOS_DB_ENABLED:
            if not self.COSMOS_DB_URL or not self.COSMOS_DB_KEY:
                # Simplified: just warn and disable rather than error
                logger.warning(
                    "Cosmos DB is enabled but URL or KEY is missing - "
                    "disabling Cosmos DB automatically"
                )
                self.COSMOS_DB_ENABLED = False

        if self.USE_REDIS_CACHE and not self.REDIS_URL:
            logger.warning(
                "Redis cache is enabled but REDIS_URL is not provided - falling back to memory cache"
            )
            self.USE_REDIS_CACHE = False

        return self

    @model_validator(mode="after")
    def validate_external_services(self) -> None:
        """Validate external service configurations."""
        # Validate email configuration
        if self.SENDGRID_API_KEY and any([self.SMTP_HOST, self.SMTP_USERNAME]):
            logger.warning(
                "Both SendGrid and SMTP configurations detected - SendGrid will take precedence"
            )

        # Validate Azure storage
        if self.AZURE_STORAGE_ACCOUNT and not (
            self.AZURE_STORAGE_KEY or self.AZURE_STORAGE_CONNECTION_STRING
        ):
            logger.warning(
                "Azure Storage account specified but no key or connection string provided"
            )

        return self

    # ==================== COMPUTED PROPERTIES ====================

    @property
    def database_url_sqlalchemy(self) -> str:
        """Convert SQL Server connection string to SQLAlchemy format with proper error handling."""
        try:
            if self.DATABASE_URL.startswith("Server="):
                # Production fallback to SQLite for cost optimization
                if self.is_production:
                    db_path = "/app/data/pathfinder.db"
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    logger.info(f"Using SQLite fallback for production: {db_path}")
                    return f"sqlite+aiosqlite:///{db_path}"

                # Parse SQL Server connection string
                parts = {}
                for part in self.DATABASE_URL.split(";"):
                    if "=" in part:
                        key, value = part.split("=", 1)
                        parts[key.strip()] = value.strip()

                server_port = parts.get("Server", "").replace("tcp:", "")
                database = parts.get("Initial Catalog", "")
                username = parts.get("User ID", "")
                password = parts.get("Password", "")

                if not all([server_port, database, username, password]):
                    raise ValueError("Incomplete SQL Server connection string")

                return f"mssql+aioodbc://{username}:{password}@{server_port}/{database}?driver=ODBC+Driver+17+for+SQL+Server&encrypt=yes&trustServerCertificate=no"

            return self.DATABASE_URL
        except Exception as e:
            logger.error(f"Error parsing database URL: {e}")
            raise ValueError(f"Invalid database configuration: {e}")

    @property
    def database_config(self) -> Dict[str, Any]:
        """Enhanced database configuration with proper validation."""
        db_url = self.database_url_sqlalchemy

        # SQLite doesn't support connection pooling
        if "sqlite" in db_url.lower():
            return {
                "connect_args": {"check_same_thread": False},
                "echo": self.DATABASE_ECHO,
            }
        else:
            return {
                "pool_pre_ping": True,
                "pool_timeout": self.DATABASE_TIMEOUT,
                "pool_recycle": 3600,
                "pool_size": self.DATABASE_POOL_SIZE,
                "max_overflow": self.DATABASE_MAX_OVERFLOW,
                "echo": self.DATABASE_ECHO,
            }

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a validated List[Any]."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://localhost:5173"]

        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        # Add default localhost if none specified
        if not origins:
            origins = ["http://localhost:3000", "http://localhost:5173"]

        return origins

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a validated List[Any]."""
        if isinstance(self.ALLOWED_HOSTS, str):
            return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
        return self.ALLOWED_HOSTS

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() in ["production", "prod"]

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() in ["testing", "test"]

    @property
    def cache_config(self) -> Dict[str, Any]:
        """Get cache configuration based on enabled backend."""
        config = {
            "enabled": self.CACHE_ENABLED,
            "ttl": self.CACHE_TTL,
            "max_size": self.CACHE_MAX_SIZE,
        }

        if self.USE_REDIS_CACHE and self.REDIS_URL:
            config.update(
                {
                    "backend": "redis",
                    "url": self.REDIS_URL,
                    "redis_ttl": self.REDIS_TTL,
                }
            )
        elif self.CACHE_TYPE == "sqlite":
            config.update(
                {
                    "backend": "sqlite",
                    "db_path": self.CACHE_DB_PATH,
                }
            )
        else:
            config.update(
                {
                    "backend": "memory",
                }
            )

        return config

    @property
    def security_config(self) -> Dict[str, Any]:
        """Get comprehensive security configuration."""
        return {
            "rate_limiting": {
                "requests": self.RATE_LIMIT_REQUESTS,
                "window": self.RATE_LIMIT_WINDOW,
            },
            "file_upload": {
                "max_size": self.MAX_FILE_SIZE,
                "allowed_types": self.ALLOWED_FILE_TYPES,
            },
            "context_validation": {
                "enabled": self.ENABLE_CONTEXT_VALIDATION,
                "max_risk_threshold": self.MAX_RISK_THRESHOLD,
                "mfa_trigger_threshold": self.MFA_TRIGGER_THRESHOLD,
            },
            "cors": {
                "origins": self.cors_origins_list,
                "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
                "allow_methods": self.CORS_ALLOW_METHODS,
                "allow_headers": self.CORS_ALLOW_HEADERS,
            },
        }

    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring and performance configuration."""
        return {
            "slow_thresholds": {
                "request": self.SLOW_REQUEST_THRESHOLD,
                "query": self.SLOW_QUERY_THRESHOLD,
            },
            "metrics": {
                "rollup_interval": self.METRICS_ROLLUP_INTERVAL,
            },
            "cost_tracking": {
                "enabled": self.AI_COST_TRACKING_ENABLED,
                "daily_budget": self.AI_DAILY_BUDGET_LIMIT,
            },
        }

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        service_configs = {
            "openai": {
                "api_key": self.OPENAI_API_KEY,
                "model_primary": self.OPENAI_MODEL_PRIMARY,
                "model_fallback": self.OPENAI_MODEL_FALLBACK,
                "max_tokens": self.OPENAI_MAX_TOKENS,
                "temperature": self.OPENAI_TEMPERATURE,
                "timeout": self.OPENAI_TIMEOUT,
            },
            "entra_external_id": {
                "tenant_id": self.ENTRA_EXTERNAL_TENANT_ID,
                "client_id": self.ENTRA_EXTERNAL_CLIENT_ID,
                "authority": self.ENTRA_EXTERNAL_AUTHORITY,
                "client_secret": self.ENTRA_EXTERNAL_CLIENT_SECRET,
                "algorithm": self.JWT_ALGORITHM,
                "expiration": self.JWT_EXPIRATION,
            },
            "cosmos_db": {
                "enabled": self.COSMOS_DB_ENABLED,
                "url": self.COSMOS_DB_URL,
                "key": self.COSMOS_DB_KEY,
                "database": self.COSMOS_DB_DATABASE,
                "containers": {
                    "itineraries": self.COSMOS_DB_CONTAINER_ITINERARIES,
                    "messages": self.COSMOS_DB_CONTAINER_MESSAGES,
                    "preferences": self.COSMOS_DB_CONTAINER_PREFERENCES,
                },
            },
            "websocket": {
                "heartbeat_interval": self.WEBSOCKET_HEARTBEAT_INTERVAL,
                "max_connections": self.WEBSOCKET_MAX_CONNECTIONS,
            },
        }

        return service_configs.get(service_name, {})

    def validate_runtime_config(self) -> Dict[str, Any]:
        """Validate configuration at runtime and return status."""
        issues = []
        warnings = []

        # Check required environment variables (simplified for single-environment deployment)
        required_vars = ["SECRET_KEY", "DATABASE_URL"]  # OPENAI_API_KEY is optional with defaults
        for var in required_vars:
            if not getattr(self, var, None):
                issues.append(f"Missing required environment variable: {var}")

        # Optional services with warnings (not errors)
        if not self.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY not set - using test defaults for AI features")

        # Check production-specific requirements
        if self.is_production:
            if self.DEBUG:
                warnings.append("DEBUG mode should be disabled in production")
            if "*" in self.allowed_hosts_list:
                issues.append("Wildcard hosts not allowed in production")
            if "*" in self.cors_origins_list:
                warnings.append("CORS wildcard detected in production")

        # Check service dependencies
        if self.COSMOS_DB_ENABLED and not all([self.COSMOS_DB_URL, self.COSMOS_DB_KEY]):
            issues.append("Cosmos DB enabled but missing URL or KEY")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
        validate_assignment = True


# ==================== LEGACY COMPATIBILITY ====================
# Maintain backward compatibility during migration
Settings = UnifiedSettings


@lru_cache()
def get_settings() -> UnifiedSettings:
    """Get cached application settings with validation."""
    settings_instance = UnifiedSettings()

    # Log configuration validation results
    validation_result = settings_instance.validate_runtime_config()
    if not validation_result["valid"]:
        logger.error(f"Configuration validation failed: {validation_result['issues']}")
        raise ValueError(f"Invalid configuration: {'; '.join(validation_result['issues'])}")

    if validation_result["warnings"]:
        for warning in validation_result["warnings"]:
            logger.warning(f"Configuration warning: {warning}")

    logger.info(
        f"Configuration loaded successfully for environment: {settings_instance.ENVIRONMENT}"
    )
    return settings_instance


# Global settings instance
settings = get_settings()


# ==================== CONFIGURATION UTILITIES ====================
def reload_settings() -> UnifiedSettings:
    """Reload settings (useful for testing)."""
    get_settings.cache_clear()
    return get_settings()


def get_database_url() -> str:
    """Get properly formatted database URL."""
    return settings.database_url_sqlalchemy


def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration."""
    return settings.cache_config


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return settings.security_config


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled based on configuration."""
    feature_flags = {
        "cosmos_db": settings.COSMOS_DB_ENABLED,
        "redis_cache": settings.USE_REDIS_CACHE,
        "context_validation": settings.ENABLE_CONTEXT_VALIDATION,
        "cost_tracking": settings.AI_COST_TRACKING_ENABLED,
        "llm_orchestration": settings.LLM_ORCHESTRATION_ENABLED,
        "cache": settings.CACHE_ENABLED,
        "debug": settings.DEBUG,
    }

    return feature_flags.get(feature_name, False)


def get_environment_info() -> Dict[str, Any]:
    """Get comprehensive environment information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "is_production": settings.is_production,
        "is_development": settings.is_development,
        "is_testing": settings.is_testing,
        "features": {
            "cosmos_db": settings.COSMOS_DB_ENABLED,
            "redis_cache": settings.USE_REDIS_CACHE,
            "context_validation": settings.ENABLE_CONTEXT_VALIDATION,
            "cost_tracking": settings.AI_COST_TRACKING_ENABLED,
        },
        "database_type": ("sqlite" if "sqlite" in settings.database_url_sqlalchemy else "external"),
        "cache_backend": settings.cache_config.get("backend", "memory"),
    }
