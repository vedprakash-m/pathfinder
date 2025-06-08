"""
LLM Orchestration Client Service
Provides interface to the deployed LLM Orchestration Service for enhanced AI capabilities
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from app.core.config import get_settings
from app.core.logging_config import create_logger

settings = get_settings()
logger = create_logger(__name__)


class LLMOrchestrationClient:
    """Client for communicating with the LLM Orchestration Service."""
    
    def __init__(self):
        self.base_url = settings.LLM_ORCHESTRATION_URL
        self.enabled = settings.LLM_ORCHESTRATION_ENABLED and self.base_url is not None
        self.timeout = settings.LLM_ORCHESTRATION_TIMEOUT
        self.api_key = settings.LLM_ORCHESTRATION_API_KEY
        
        # HTTP client with timeout and retry configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_headers(),
            follow_redirects=True
        )
        
        if self.enabled:
            logger.info(f"LLM Orchestration client enabled, service URL: {self.base_url}")
        else:
            logger.info("LLM Orchestration client disabled - using fallback OpenAI service")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Pathfinder-Backend/1.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    async def is_healthy(self) -> bool:
        """Check if the LLM orchestration service is healthy."""
        if not self.enabled:
            return False
            
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM Orchestration health check failed: {e}")
            return False
    
    async def generate_text(
        self,
        prompt: str,
        task_type: str = "general",
        user_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using the LLM orchestration service."""
        
        if not self.enabled:
            raise ValueError("LLM Orchestration service is not enabled")
        
        try:
            # Build request payload
            request_data = {
                "request": {
                    "prompt": prompt,
                    "task_type": task_type,
                    "max_tokens": max_tokens or 2000,
                    "temperature": temperature or 0.7,
                    "model_preference": model_preference,
                    "metadata": {
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "pathfinder-backend"
                    }
                },
                "tenant_id": "pathfinder-main"  # Default tenant for Pathfinder
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/api/v1/llm/process",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    # Extract response data
                    llm_response = result.get("response", {})
                    
                    return {
                        "text": llm_response.get("content", ""),
                        "model_used": llm_response.get("model_used"),
                        "tokens_used": llm_response.get("tokens_used"),
                        "cost": result.get("cost", 0.0),
                        "processing_time": result.get("processing_time", 0.0),
                        "provider": llm_response.get("provider"),
                        "metadata": llm_response.get("metadata", {})
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"LLM Orchestration API error: {error_msg}")
                    raise Exception(f"LLM API error: {error_msg}")
            else:
                logger.error(f"LLM Orchestration HTTP error: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except httpx.TimeoutException:
            logger.error("LLM Orchestration request timeout")
            raise Exception("LLM request timeout")
        except httpx.RequestError as e:
            logger.error(f"LLM Orchestration request error: {e}")
            raise Exception(f"LLM request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in LLM Orchestration: {e}")
            raise
    
    async def get_budget_status(self, tenant_id: str = "pathfinder-main") -> Dict[str, Any]:
        """Get current budget status from the orchestration service."""
        if not self.enabled:
            return {"error": "LLM Orchestration service not enabled"}
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/budget/status/{tenant_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get budget status: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting budget status: {e}")
            return {"error": str(e)}
    
    async def get_analytics(self, tenant_id: str = "pathfinder-main", hours: int = 24) -> Dict[str, Any]:
        """Get analytics data from the orchestration service."""
        if not self.enabled:
            return {"error": "LLM Orchestration service not enabled"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/analytics/tenant/{tenant_id}",
                params={"hours": hours}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get analytics: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global client instance
llm_orchestration_client = LLMOrchestrationClient()


async def get_llm_orchestration_client() -> LLMOrchestrationClient:
    """Dependency injection for LLM orchestration client."""
    return llm_orchestration_client 