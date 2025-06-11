"""
Application configuration settings.
"""

from functools import lru_cache
from typing import List, Optional, Union
from pydantic import Field, field_validator
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
    ALLOWED_HOSTS: Union[List[str], str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # CORS settings
    CORS_ORIGINS: Optional[str] = Field(
        default="http://localhost:3000,http://localhost:5173,*",
        env="CORS_ORIGINS",
        description="Comma-separated list of CORS origins"
    )
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Cosmos DB settings
    COSMOS_DB_ENABLED: bool = Field(default=False, env="COSMOS_DB_ENABLED")
    COSMOS_DB_URL: str = Field(default="", env="COSMOS_DB_URL")
    COSMOS_DB_KEY: str = Field(default="", env="COSMOS_DB_KEY")
    COSMOS_DB_DATABASE: str = Field(default="pathfinder", env="COSMOS_DB_DATABASE")
    COSMOS_DB_CONTAINER_ITINERARIES: str = Field(default="itineraries", env="COSMOS_DB_CONTAINER_ITINERARIES")
    COSMOS_DB_CONTAINER_MESSAGES: str = Field(default="messages", env="COSMOS_DB_CONTAINER_MESSAGES")
    COSMOS_DB_CONTAINER_PREFERENCES: str = Field(default="preferences", env="COSMOS_DB_CONTAINER_PREFERENCES")
    
    # Cache settings (Redis-free alternatives for cost optimization)
    USE_REDIS_CACHE: bool = Field(default=False, env="USE_REDIS_CACHE")  # Disabled by default
    REDIS_URL: str = Field(default="", env="REDIS_URL")  # Optional Redis URL
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour default TTL
    CACHE_MAX_SIZE: int = Field(default=2000, env="CACHE_MAX_SIZE")  # Memory cache size
    CACHE_TYPE: str = Field(default="memory", env="CACHE_TYPE")  # "memory" or "sqlite"
    CACHE_DB_PATH: str = Field(default="data/cache.db", env="CACHE_DB_PATH")
    
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
    
    # Email settings (SendGrid)
    SENDGRID_API_KEY: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    FROM_EMAIL: str = Field(default="noreply@pathfinder.com", env="FROM_EMAIL")
    FROM_NAME: str = Field(default="Pathfinder", env="FROM_NAME")
    
    # Email settings (SMTP fallback)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    
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
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
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
    
    # LLM Orchestration Service settings
    LLM_ORCHESTRATION_URL: Optional[str] = Field(default=None, env="LLM_ORCHESTRATION_URL")
    LLM_ORCHESTRATION_ENABLED: bool = Field(default=False, env="LLM_ORCHESTRATION_ENABLED")
    LLM_ORCHESTRATION_TIMEOUT: int = Field(default=60, env="LLM_ORCHESTRATION_TIMEOUT")
    LLM_ORCHESTRATION_API_KEY: Optional[str] = Field(default=None, env="LLM_ORCHESTRATION_API_KEY")
    
    # Security context validation
    ENABLE_CONTEXT_VALIDATION: bool = Field(default=False, env="ENABLE_CONTEXT_VALIDATION")
    MAX_RISK_THRESHOLD: float = Field(default=0.7, env="MAX_RISK_THRESHOLD")
    MFA_TRIGGER_THRESHOLD: float = Field(default=0.5, env="MFA_TRIGGER_THRESHOLD")
    TRUSTED_LOCATIONS: List[str] = Field(default=[], env="TRUSTED_LOCATIONS")
    TRUSTED_NETWORKS: List[str] = Field(default=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"], env="TRUSTED_NETWORKS")
    WORKING_HOURS_START: int = Field(default=8, env="WORKING_HOURS_START")
    WORKING_HOURS_END: int = Field(default=18, env="WORKING_HOURS_END")
    WORKING_HOURS_TIMEZONE: str = Field(default="UTC", env="WORKING_HOURS_TIMEZONE")
    USER_PATTERNS_FILE: str = Field(default="user_access_patterns.json", env="USER_PATTERNS_FILE")
    
    # Performance monitoring
    SLOW_REQUEST_THRESHOLD: float = Field(default=1.0, env="SLOW_REQUEST_THRESHOLD")
    SLOW_QUERY_THRESHOLD: float = Field(default=0.5, env="SLOW_QUERY_THRESHOLD") 
    SLOW_FUNCTION_THRESHOLD: float = Field(default=0.5, env="SLOW_FUNCTION_THRESHOLD")
    METRICS_ROLLUP_INTERVAL: int = Field(default=300, env="METRICS_ROLLUP_INTERVAL")
    
    @field_validator("AUTH0_ISSUER", mode="before")
    @classmethod
    def set_auth0_issuer(cls, v, info):
        """Set Auth0 issuer from domain if not provided."""
        if v is None and hasattr(info, 'data') and "AUTH0_DOMAIN" in info.data:
            return f"https://{info.data['AUTH0_DOMAIN']}/"
        return v
    
    @property
    def database_url_sqlalchemy(self) -> str:
        """Convert SQL Server connection string to SQLAlchemy format if needed."""
        if self.DATABASE_URL.startswith("Server="):
            # For production, fall back to SQLite if SQL Server drivers aren't available
            # This is a temporary measure for ultra-cost-optimized deployment
            if self.ENVIRONMENT == "production":
                # Use SQLite as fallback for cost optimization
                import os
                db_path = "/app/data/pathfinder.db"
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                return f"sqlite+aiosqlite:///{db_path}"
            
            # Parse SQL Server connection string for development/full environments
            parts = {}
            for part in self.DATABASE_URL.split(";"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    parts[key.strip()] = value.strip()
            
            # Extract components
            server_port = parts.get("Server", "").replace("tcp:", "")
            database = parts.get("Initial Catalog", "")
            username = parts.get("User ID", "")
            password = parts.get("Password", "")
            
            # Build SQLAlchemy URL for SQL Server with aioodbc (async)
            return f"mssql+aioodbc://{username}:{password}@{server_port}/{database}?driver=ODBC+Driver+17+for+SQL+Server&encrypt=yes&trustServerCertificate=no"
        
        return self.DATABASE_URL

    @property
    def database_config(self) -> dict:
        """Database configuration for SQLAlchemy."""
        # SQLite doesn't support connection pooling parameters
        db_url = self.database_url_sqlalchemy
        if "sqlite" in db_url.lower():
            return {
                "pool_pre_ping": True,
            }
        
        # For PostgreSQL, MySQL, SQL Server and other databases that support pooling
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
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://localhost:5173", "*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list."""
        if isinstance(self.ALLOWED_HOSTS, str):
            return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
        return self.ALLOWED_HOSTS
    
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