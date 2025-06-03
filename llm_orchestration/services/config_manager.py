"""
Admin Configuration Manager - Loads, validates, and manages system configuration
Handles tenant-specific overrides and configuration hot-reloading
"""
import yaml
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import structlog
from core.types import LLMProvider, LLMConfigurationError

logger = structlog.get_logger(__name__)


class ModelDefinition(BaseModel):
    """Model definition from configuration"""
    id: str
    provider: LLMProvider
    name: str
    cost_per_1k_tokens: Dict[str, float]  # {"input": 0.005, "output": 0.015}
    max_tokens: int
    capabilities: List[str]
    active: bool = True


class RoutingRule(BaseModel):
    """Routing rule for model selection"""
    condition: str  # e.g., "task_type == 'simple_qa'"
    models: List[str]  # Ordered list of model IDs to try


class RoutingStrategy(BaseModel):
    """Complete routing strategy definition"""
    description: str
    rules: List[RoutingRule]


class BudgetConfig(BaseModel):
    """Budget configuration"""
    daily_limit: float
    monthly_limit: float
    alert_thresholds: List[int] = Field(default_factory=lambda: [80, 95])
    auto_disable_at: Optional[int] = None


class PerformanceConfig(BaseModel):
    """Performance and reliability configuration"""
    caching: Dict[str, Any]
    rate_limiting: Dict[str, Any] 
    circuit_breaker: Dict[str, Any]
    retry_policy: Dict[str, Any]


class TenantOverride(BaseModel):
    """Tenant-specific configuration overrides"""
    budget: Optional[BudgetConfig] = None
    routing_strategy: Optional[str] = None
    models: Optional[Dict[str, Any]] = None


class AdminConfig(BaseModel):
    """Complete admin configuration model"""
    version: str
    last_updated: datetime
    admin_contact: str
    
    # Key Vault configuration
    key_vault: Dict[str, Any]
    
    # Model configuration
    models: Dict[str, Any]
    
    # Budget configuration
    budget: Dict[str, Any]
    
    # Performance configuration
    performance: Dict[str, Any]
    
    # Provider-specific configuration
    providers: Dict[str, Dict[str, Any]]
    
    # Logging and analytics
    logging: Dict[str, Any]
    analytics: Dict[str, Any]
    
    # Tenant overrides
    tenant_overrides: Dict[str, TenantOverride] = Field(default_factory=dict)
    
    @validator('version')
    def validate_version(cls, v):
        if not v or not v.strip():
            raise ValueError("Version cannot be empty")
        return v


class AdminConfigManager:
    """
    Manages admin configuration with validation, caching, and tenant overrides
    Supports hot-reloading and configuration validation
    """
    
    def __init__(self, config_path: str = "config/admin_config.yaml"):
        self.config_path = config_path
        self._config: Optional[AdminConfig] = None
        self._last_modified: Optional[float] = None
        self._tenant_configs: Dict[str, Dict[str, Any]] = {}
        
    async def load_config(self, force_reload: bool = False) -> AdminConfig:
        """
        Load configuration from file with caching and validation
        
        Args:
            force_reload: Force reload even if file hasn't changed
            
        Returns:
            AdminConfig: Validated configuration object
        """
        try:
            # Check if file has been modified
            if not force_reload and self._config is not None:
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime == self._last_modified:
                    logger.debug("Using cached configuration")
                    return self._config
            
            # Load and parse YAML
            logger.info("Loading admin configuration", config_path=self.config_path)
            
            with open(self.config_path, 'r') as file:
                raw_config = yaml.safe_load(file)
            
            # Substitute environment variables
            raw_config = self._substitute_env_vars(raw_config)
            
            # Validate configuration
            self._config = AdminConfig(**raw_config)
            self._last_modified = os.path.getmtime(self.config_path)
            
            # Pre-process tenant configurations
            self._process_tenant_overrides()
            
            logger.info(
                "Configuration loaded successfully",
                version=self._config.version,
                models_count=len(self._config.models.get("definitions", [])),
                tenants_count=len(self._config.tenant_overrides)
            )
            
            return self._config
            
        except FileNotFoundError:
            raise LLMConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise LLMConfigurationError(f"Invalid YAML in configuration: {str(e)}")
        except Exception as e:
            raise LLMConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in configuration"""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, config)  # Return original if env var not found
        else:
            return config
    
    def _process_tenant_overrides(self):
        """Pre-process tenant-specific configurations"""
        if not self._config:
            return
            
        for tenant_id, override in self._config.tenant_overrides.items():
            # Merge tenant overrides with base configuration
            tenant_config = self._merge_tenant_config(tenant_id, override)
            self._tenant_configs[tenant_id] = tenant_config
            
            logger.debug("Processed tenant configuration", tenant_id=tenant_id)
    
    def _merge_tenant_config(self, tenant_id: str, override: TenantOverride) -> Dict[str, Any]:
        """Merge tenant overrides with base configuration"""
        base_config = self._config.dict() if self._config else {}
        tenant_config = base_config.copy()
        
        # Apply budget overrides
        if override.budget:
            tenant_config["budget"] = tenant_config.get("budget", {}).copy()
            tenant_config["budget"].update(override.budget.dict())
        
        # Apply routing strategy overrides
        if override.routing_strategy:
            tenant_config["models"]["routing_strategy"]["default_strategy"] = override.routing_strategy
        
        # Apply model overrides
        if override.models:
            tenant_config["models"] = tenant_config.get("models", {}).copy()
            tenant_config["models"].update(override.models)
        
        return tenant_config
    
    async def get_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration, optionally with tenant-specific overrides
        
        Args:
            tenant_id: Optional tenant ID for tenant-specific config
            
        Returns:
            Dict: Complete configuration with any tenant overrides applied
        """
        # Ensure config is loaded
        if self._config is None:
            await self.load_config()
        
        # Return tenant-specific config if available
        if tenant_id and tenant_id in self._tenant_configs:
            logger.debug("Returning tenant-specific configuration", tenant_id=tenant_id)
            return self._tenant_configs[tenant_id]
        
        # Return base configuration
        return self._config.dict()
    
    async def get_model_definitions(self, tenant_id: Optional[str] = None) -> List[ModelDefinition]:
        """Get model definitions with tenant overrides"""
        config = await self.get_config(tenant_id)
        model_defs = config.get("models", {}).get("definitions", [])
        
        return [ModelDefinition(**model_def) for model_def in model_defs]
    
    async def get_routing_strategies(self, tenant_id: Optional[str] = None) -> Dict[str, RoutingStrategy]:
        """Get routing strategies with tenant overrides"""
        config = await self.get_config(tenant_id)
        strategies_config = config.get("models", {}).get("routing_strategy", {}).get("strategies", {})
        
        strategies = {}
        for name, strategy_config in strategies_config.items():
            strategies[name] = RoutingStrategy(**strategy_config)
        
        return strategies
    
    async def get_budget_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get budget configuration with tenant overrides"""
        config = await self.get_config(tenant_id)
        return config.get("budget", {})
    
    async def get_key_vault_config(self) -> Dict[str, Any]:
        """Get Key Vault configuration (no tenant overrides for security)"""
        if self._config is None:
            await self.load_config()
        return self._config.key_vault
    
    async def get_provider_config(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        config = await self.get_config()
        providers = config.get("providers", {})
        
        if provider.value not in providers:
            raise LLMConfigurationError(f"No configuration found for provider: {provider.value}")
        
        return providers[provider.value]
    
    async def get_performance_config(self) -> Dict[str, Any]:
        """Get performance and reliability configuration"""
        config = await self.get_config()
        return config.get("performance", {})
    
    async def validate_config(self) -> List[str]:
        """
        Validate current configuration and return any issues
        
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            config = await self.get_config()
            
            # Validate model definitions
            model_defs = await self.get_model_definitions()
            if not model_defs:
                issues.append("No model definitions found")
            
            # Validate Key Vault configuration
            kv_config = await self.get_key_vault_config()
            if not kv_config.get("vault_name"):
                issues.append("Key Vault name not configured")
            
            # Validate provider configurations
            for model_def in model_defs:
                try:
                    await self.get_provider_config(model_def.provider)
                except LLMConfigurationError as e:
                    issues.append(f"Provider config issue: {str(e)}")
            
            # Validate routing strategies
            strategies = await self.get_routing_strategies()
            if not strategies:
                issues.append("No routing strategies defined")
            
            logger.info("Configuration validation completed", issues_count=len(issues))
            
        except Exception as e:
            issues.append(f"Configuration validation error: {str(e)}")
        
        return issues
    
    async def reload_config(self) -> AdminConfig:
        """Force reload configuration from file"""
        logger.info("Force reloading configuration")
        return await self.load_config(force_reload=True)


# Global configuration manager instance
config_manager: Optional[AdminConfigManager] = None


def get_config_manager() -> AdminConfigManager:
    """Get the global configuration manager instance"""
    global config_manager
    if config_manager is None:
        config_manager = AdminConfigManager()
    return config_manager


async def initialize_config_manager(config_path: Optional[str] = None) -> AdminConfigManager:
    """Initialize and load the global configuration manager"""
    global config_manager
    
    if config_path:
        config_manager = AdminConfigManager(config_path)
    else:
        config_manager = AdminConfigManager()
    
    # Load configuration to validate it
    await config_manager.load_config()
    
    logger.info("Configuration manager initialized", config_path=config_manager.config_path)
    return config_manager
