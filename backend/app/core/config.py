"""
Application configuration settings.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "Pathfinder API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Cosmos DB settings
    COSMOS_DB_URL: str = Field(..., env="COSMOS_DB_URL")
    COSMOS_DB_KEY: str = Field(..., env="COSMOS_DB_KEY")
    COSMOS_DB_DATABASE: str = Field(default="pathfinder", env="COSMOS_DB_DATABASE")
    COSMOS_DB_CONTAINER: str = Field(default="trips", env="COSMOS_DB_CONTAINER")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")  # 1 hour
    
    # Auth0 settings
    AUTH0_DOMAIN: str = Field(..., env="AUTH0_DOMAIN")
    AUTH0_AUDIENCE: str = Field(..., env="AUTH0_AUDIENCE")
    AUTH0_CLIENT_ID: str = Field(..., env="AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET: str = Field(..., env="AUTH0_CLIENT_SECRET")
    AUTH0_ISSUER: Optional[str] = Field(default=None, env="AUTH0_ISSUER")
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL_PRIMARY: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL_PRIMARY")
    OPENAI_MODEL_FALLBACK: str = Field(default="gpt-4o", env="OPENAI_MODEL_FALLBACK")
    OPENAI_MAX_TOKENS: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    OPENAI_TIMEOUT: int = Field(default=60, env="OPENAI_TIMEOUT")
    
    # Google Maps settings
    GOOGLE_MAPS_API_KEY: str = Field(..., env="GOOGLE_MAPS_API_KEY")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "application/pdf"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Azure settings
    AZURE_STORAGE_ACCOUNT: Optional[str] = Field(default=None, env="AZURE_STORAGE_ACCOUNT")
    AZURE_STORAGE_KEY: Optional[str] = Field(default=None, env="AZURE_STORAGE_KEY")
    AZURE_STORAGE_CONTAINER: str = Field(default="uploads", env="AZURE_STORAGE_CONTAINER")
    
    # Application Insights
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = Field(
        default=None, env="APPINSIGHTS_CONNECTION_STRING"
    )
    
    # WebSocket settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=1000, env="WEBSOCKET_MAX_CONNECTIONS")
    
    # AI cost tracking
    AI_COST_TRACKING_ENABLED: bool = Field(default=True, env="AI_COST_TRACKING_ENABLED")
    AI_DAILY_BUDGET_LIMIT: float = Field(default=50.0, env="AI_DAILY_BUDGET_LIMIT")  # USD
    
    @validator("AUTH0_ISSUER", pre=True, always=True)
    def set_auth0_issuer(cls, v, values):
        """Set Auth0 issuer from domain if not provided."""
        if v is None and "AUTH0_DOMAIN" in values:
            return f"https://{values['AUTH0_DOMAIN']}/"
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @property
    def database_config(self) -> dict:
        """Database configuration for SQLAlchemy."""
        # SQLite doesn't support connection pooling parameters
        if "sqlite" in self.DATABASE_URL.lower():
            return {
                "pool_pre_ping": True,
            }
        
        # For PostgreSQL, MySQL, and other databases that support pooling
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        }
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()