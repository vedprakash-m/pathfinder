"""
Configuration Management

Loads settings from environment variables with sensible defaults.
Uses Pydantic for validation and type safety.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = Field(default="production", description="Runtime environment")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Cosmos DB
    COSMOS_DB_URL: str = Field(..., description="Cosmos DB endpoint URL")
    COSMOS_DB_KEY: str = Field(..., description="Cosmos DB primary key")
    COSMOS_DB_DATABASE: str = Field(default="pathfinder", description="Database name")
    COSMOS_DB_CONTAINER: str = Field(default="entities", description="Container name")

    # SignalR
    SIGNALR_CONNECTION_STRING: str = Field(..., description="Azure SignalR connection string")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-5-mini", description="OpenAI model name")
    OPENAI_MAX_TOKENS: int = Field(default=2000, description="Max tokens per request")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="Model temperature")

    # Microsoft Entra ID
    ENTRA_TENANT_ID: str = Field(default="vedid.onmicrosoft.com", description="Entra ID tenant")
    ENTRA_CLIENT_ID: str = Field(..., description="Entra ID client/application ID")
    ENTRA_AUTHORITY: str = Field(
        default="https://login.microsoftonline.com/vedid.onmicrosoft.com", description="Entra ID authority URL"
    )

    # Application Insights
    APPINSIGHTS_INSTRUMENTATIONKEY: str = Field(default="", description="Application Insights instrumentation key")
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(default="", description="Application Insights connection string")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,https://pf-swa.azurestaticapps.net",
        description="Comma-separated list of allowed origins",
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # AI Cost Management
    AI_DAILY_BUDGET_USD: float = Field(default=10.0, description="Daily AI spending limit")
    AI_REQUEST_TIMEOUT: int = Field(default=30, description="AI request timeout in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_settings_uncached() -> Settings:
    """Get fresh settings instance (for testing)."""
    return Settings()
