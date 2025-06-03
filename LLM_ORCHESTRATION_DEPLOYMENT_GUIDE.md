# 🚀 LLM Orchestration Service - Azure Deployment Guide

## 📋 Deployment Status Summary

### ✅ Completed Components
- **Auth0 Configuration**: Hardcoded configuration with domain `dev-jwnud3v8ghqnyygr.us.auth0.com`
- **Frontend Application**: Deployed to Azure Container Apps
- **Backend Application**: Deployed to Azure Container Apps
- **LLM Orchestration Service**: Code complete, ready for deployment

### 🎯 Current Task: Deploy LLM Orchestration Service

## 🏗️ LLM Orchestration Service Architecture

### Core Components
```
llm_orchestration/
├── app_production.py          # Production FastAPI application
├── Dockerfile.production      # Optimized container build
├── requirements-production.txt # Minimal dependencies
├── core/                      # Core orchestration logic
│   ├── gateway.py            # Main LLM gateway
│   ├── types.py              # Type definitions
│   └── ...
├── services/                  # Service modules
│   ├── routing_engine.py     # Intelligent model routing
│   ├── budget_manager.py     # Cost management
│   ├── cache_manager.py      # Redis caching
│   ├── circuit_breaker.py    # Reliability patterns
│   └── ...
└── config/                   # Configuration files
```

### Key Features
- **Multi-Provider Support**: OpenAI, Gemini, Anthropic
- **Intelligent Routing**: Cost and performance optimization
- **Budget Management**: Real-time cost tracking and limits
- **Caching Layer**: Redis-based response caching
- **Circuit Breaker**: Fault tolerance and resilience
- **Analytics**: Usage tracking and performance metrics

## 🚀 Deployment Options

### Option 1: Quick Deployment (Azure Container Instances)
**Fastest deployment for testing and demos**

```bash
cd /Users/vedprakashmishra/pathfinder/llm_orchestration
./deploy-ultra-simple.sh
```

**What it does:**
- Creates resource group `llm-orchestration-demo`
- Deploys single container instance with public IP
- No external dependencies (Redis, Key Vault)
- Mock responses for testing

**Expected outcome:**
- Service URL: `http://[CONTAINER_IP]:8000`
- API Documentation: `http://[CONTAINER_IP]:8000/docs`
- Health endpoint: `http://[CONTAINER_IP]:8000/health`

### Option 2: Production Deployment (Azure Container Apps)
**Full production setup with infrastructure**

```bash
cd /Users/vedprakashmishra/pathfinder/llm_orchestration
./deploy-azure.sh
```

**What it creates:**
- Resource group `llm-orchestration-rg`
- Azure Key Vault for secrets
- Redis Cache for caching
- Storage Account for logs
- Container Apps environment
- Production-ready LLM service

### Option 3: Manual Azure CLI Deployment
**Step-by-step manual deployment**

```bash
# 1. Create resource group
az group create \
  --name llm-orchestration-rg \
  --location eastus

# 2. Deploy container instance
az container create \
  --resource-group llm-orchestration-rg \
  --name llm-orchestration-service \
  --image python:3.9-slim \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --ip-address Public \
  --environment-variables \
    ENVIRONMENT=azure \
    LOG_LEVEL=INFO \
  --command-line "sh -c 'pip install fastapi uvicorn && uvicorn app:app --host 0.0.0.0 --port 8000'"

# 3. Get service IP
az container show \
  --name llm-orchestration-service \
  --resource-group llm-orchestration-rg \
  --query ipAddress.ip \
  --output tsv
```

## 🧪 Testing the Deployment

### Health Check
```bash
# Replace [SERVICE_IP] with actual IP from deployment
curl http://[SERVICE_IP]:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": 1700000000.0,
  "version": "1.0.0",
  "environment": "azure",
  "services": {
    "gateway": "operational",
    "providers": "available"
  }
}
```

### API Testing
```bash
# Test LLM generation endpoint
curl -X POST http://[SERVICE_IP]:8000/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the benefits of cloud computing",
    "user_id": "test-user",
    "tenant_id": "pathfinder",
    "max_tokens": 100
  }'
```

**Expected response:**
```json
{
  "content": "Cloud computing offers several key benefits...",
  "model_used": "gpt-3.5-turbo",
  "estimated_cost": 0.002,
  "request_id": "req_123456",
  "processing_time": 0.15
}
```

### Metrics Endpoint
```bash
curl http://[SERVICE_IP]:8000/metrics
```

## 🔗 Integration with Pathfinder

### Environment Variables for Integration
Once deployed, update the Pathfinder backend with:

```bash
az containerapp update \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --set-env-vars \
    "LLM_ORCHESTRATION_URL=http://[SERVICE_IP]:8000" \
    "LLM_SERVICE_ENABLED=true"
```

### API Integration Code
Add to Pathfinder backend:

```python
import httpx

class LLMOrchestrationClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def generate_content(self, prompt: str, user_id: str) -> str:
        response = await self.client.post(
            f"{self.base_url}/v1/generate",
            json={
                "prompt": prompt,
                "user_id": user_id,
                "tenant_id": "pathfinder"
            }
        )
        response.raise_for_status()
        return response.json()["content"]
```

## ⚠️ Production Considerations

### Security
- [ ] Configure CORS origins properly
- [ ] Add authentication middleware
- [ ] Set up API keys for provider access
- [ ] Enable HTTPS with SSL certificates

### Monitoring
- [ ] Set up Azure Application Insights
- [ ] Configure log aggregation
- [ ] Set up alerting for errors and budget limits
- [ ] Monitor response times and costs

### Scaling
- [ ] Configure auto-scaling rules
- [ ] Set up load balancing
- [ ] Monitor resource usage
- [ ] Optimize container resource allocation

## 🔧 Troubleshooting

### Common Issues
1. **Container fails to start**: Check logs with `az container logs`
2. **API not responding**: Verify port 8000 is accessible
3. **Authentication errors**: Check API key configuration
4. **High costs**: Review budget manager settings

### Debug Commands
```bash
# Check container status
az container show --name llm-orchestration-service --resource-group llm-orchestration-rg

# View logs
az container logs --name llm-orchestration-service --resource-group llm-orchestration-rg

# Monitor in real-time
az container logs --name llm-orchestration-service --resource-group llm-orchestration-rg --follow
```

## ✅ Success Criteria

The deployment is successful when:
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] API documentation is accessible at `/docs`
- [ ] LLM generation endpoint processes test requests
- [ ] Metrics endpoint shows operational data
- [ ] Service integrates with Pathfinder backend

## 📞 Next Steps

1. **Deploy the service** using one of the three options above
2. **Test all endpoints** with provided curl commands
3. **Integrate with Pathfinder** by updating backend environment variables
4. **Configure production settings** (API keys, CORS, monitoring)
5. **Set up monitoring and alerting** for production readiness

---

**Ready to deploy? Choose your deployment option above and follow the commands!** 🚀
