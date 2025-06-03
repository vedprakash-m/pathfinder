# LLM Orchestration Layer

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/your-repo/llm-orchestration)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](./docker-compose.yml)
[![Security](https://img.shields.io/badge/Security-Key%20Vault%20Integrated-yellow.svg)](./services/key_vault.py)

## 🚀 Overview

A production-ready LLM orchestration layer designed to serve **thousands of active users** with the highest possible user experience, lowest operational cost, and enterprise-grade security. This system provides intelligent routing, comprehensive analytics, fault tolerance, and multi-tenant budget management.

## ✨ Key Features

- **🔧 Multi-Provider Support**: OpenAI, Google Gemini, Claude, Cohere with unified API
- **🎯 Intelligent Routing**: Cost-optimized routing with A/B testing and performance tracking
- **💰 Budget Management**: Multi-tenant budget enforcement with real-time cost tracking
- **⚡ High Performance**: Redis caching, circuit breakers, and horizontal scaling
- **🔒 Enterprise Security**: Key Vault integration (Azure/AWS/HashiCorp) with audit trails
- **📊 Advanced Analytics**: Real-time usage metrics, cost analytics, and performance insights
- **🛡️ Fault Tolerance**: Circuit breaker pattern with automatic recovery
- **🏗️ Multi-Tenant**: Complete tenant isolation with custom configurations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Gateway                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Request Handler │  │ Authentication  │  │ Rate Limiting   │            │
│  │ & Validation    │  │ & Authorization │  │ & Throttling    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Core Gateway Engine                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Cache Manager   │  │ Circuit Breaker │  │ Usage Logger    │            │
│  │ (Redis)         │  │ Protection      │  │ & Analytics     │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Intelligent Routing Engine                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Model Selection │  │ Budget Manager  │  │ Cost Estimator  │            │
│  │ & A/B Testing   │  │ Multi-Tenant    │  │ & Optimizer     │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM Provider Adapters                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ OpenAI Adapter  │  │ Gemini Adapter  │  │ Claude Adapter  │            │
│  │ GPT-4, GPT-3.5  │  │ Gemini Pro      │  │ Claude-3        │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│  ┌─────────────────┐                                                        │
│  │ Cohere Adapter  │                                                        │
│  │ Command Models  │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Security & Infrastructure Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Key Vault       │  │ Config Manager  │  │ Monitoring      │            │
│  │ Azure/AWS/HC    │  │ Tenant Configs  │  │ Prometheus      │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Redis (for caching)
- PostgreSQL (for analytics storage)
- Key Vault access (Azure/AWS/HashiCorp)

### 1. Local Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd llm_orchestration

# Make startup script executable and run
chmod +x start_service.sh
./start_service.sh
```

### 2. Docker Setup (Recommended)

```bash
# Start complete environment with Redis, Prometheus, Grafana
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

### 3. Configuration

Update `config/admin_config.yaml` with your settings:

```yaml
key_vault:
  provider: "azure"  # or "aws", "hashicorp"
  vault_url: "your-vault-url"

providers:
  openai:
    key_vault_key: "openai-api-key"
    models: ["gpt-4", "gpt-3.5-turbo"]
  
  google:
    key_vault_key: "google-api-key"
    models: ["gemini-pro"]

cache:
  redis_url: "redis://localhost:6379"
  default_ttl: 3600

budget:
  default_monthly_limit: 1000.0
  currency: "USD"
```

## 💻 API Usage

### Basic Text Generation

```python
import httpx

# Generate text
response = httpx.post("http://localhost:8000/v1/generate", json={
    "prompt": "Explain quantum computing in simple terms",
    "user_id": "user123",
    "task_type": "explanation",
    "max_tokens": 500
})

result = response.json()
print(result["response"])
```

### Stream Generation

```python
import httpx

# Stream response
with httpx.stream("POST", "http://localhost:8000/v1/generate/stream", json={
    "prompt": "Write a long story about space exploration",
    "user_id": "user123",
    "stream": True
}) as response:
    for chunk in response.iter_text():
        print(chunk, end="")
```

### Multi-Modal Support

```python
# Image analysis
response = httpx.post("http://localhost:8000/v1/generate", json={
    "prompt": "Describe what you see in this image",
    "user_id": "user123",
    "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."],
    "model": "gpt-4-vision-preview"
})
```

## 🔧 Core Components

### 1. Gateway Engine (`core/gateway.py`)
- **Request Processing**: Validation, authentication, rate limiting
- **Intelligent Caching**: Redis-based with smart TTL calculation
- **Circuit Breaker**: Fault tolerance with automatic recovery
- **Usage Tracking**: Comprehensive logging and analytics

### 2. Provider Adapters (`services/llm_adapters.py`)
- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-vision
- **Google**: Gemini Pro, Gemini Pro Vision
- **Anthropic**: Claude-3 Opus, Sonnet, Haiku
- **Cohere**: Command, Command-R models

### 3. Routing Engine (`services/routing_engine.py`)
- **Cost Optimization**: Automatic model selection based on cost/performance
- **A/B Testing**: Built-in experimentation framework
- **Load Balancing**: Distribute load across providers
- **Performance Tracking**: Real-time latency and success rate monitoring

### 4. Budget Management (`services/budget_manager.py`)
- **Multi-Tenant**: Isolated budgets per tenant/user
- **Real-Time Tracking**: Live cost monitoring with alerts
- **Automatic Cutoffs**: Prevent budget overruns
- **Detailed Reporting**: Cost breakdown by model, user, time period

### 5. Analytics System (`services/analytics_collector.py`)
- **Usage Metrics**: Requests, tokens, latency, error rates
- **Cost Analytics**: Detailed cost tracking and optimization insights
- **Performance Monitoring**: System health and provider performance
- **Custom Dashboards**: Grafana integration with pre-built dashboards

## 📊 Monitoring & Observability

### Health Checks

```bash
# System health
curl http://localhost:8000/health

# Detailed health with provider status
curl http://localhost:8000/health/detailed
```

### Metrics Endpoints

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Usage analytics
curl http://localhost:8000/v1/analytics/usage?tenant_id=tenant1&period=daily

# Cost analytics
curl http://localhost:8000/v1/analytics/costs?user_id=user123&start_date=2024-01-01
```

### Grafana Dashboards

Access pre-configured dashboards at `http://localhost:3000`:
- **System Overview**: Request rates, latency, error rates
- **Cost Analytics**: Budget utilization, cost trends, optimization opportunities
- **Provider Performance**: Response times, success rates, circuit breaker status
- **User Analytics**: Usage patterns, top users, model preferences

## 🔒 Security Features

### Key Management
- **Multiple Providers**: Azure Key Vault, AWS Secrets Manager, HashiCorp Vault
- **Secure Access**: Managed identities and service principals
- **Key Rotation**: Automatic key rotation support
- **Audit Logging**: Complete access audit trail

### Authentication & Authorization
- **API Key Authentication**: Secure tenant identification
- **Rate Limiting**: Per-user and per-tenant limits
- **Budget Enforcement**: Automatic spending controls
- **Request Validation**: Input sanitization and validation

### Data Protection
- **No Data Storage**: Requests/responses not persisted
- **Secure Transit**: TLS encryption for all communications
- **Audit Trails**: Comprehensive logging for compliance
- **PII Detection**: Automatic detection and handling of sensitive data

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_gateway.py -v
python -m pytest tests/test_integration.py -v
```

### Integration Testing

```bash
# Full integration test with real providers
python test_integration.py
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📦 Deployment

### Production Deployment

1. **Environment Setup**:
   ```bash
   # Set environment variables
   export KEY_VAULT_URL="your-vault-url"
   export REDIS_URL="your-redis-url"
   export DATABASE_URL="your-postgres-url"
   ```

2. **Container Deployment**:
   ```bash
   # Build production image
   docker build -t llm-orchestration:latest .
   
   # Deploy with orchestrator (Kubernetes, Docker Swarm, etc.)
   ```

3. **Scaling Configuration**:
   - **Horizontal Scaling**: Multiple gateway instances behind load balancer
   - **Redis Cluster**: For cache scaling
   - **Database Scaling**: Read replicas for analytics queries

### Performance Optimization

- **Cache Hit Rate**: Target 70%+ cache hit rate
- **Response Time**: <500ms p95 latency
- **Throughput**: 1000+ requests/second per instance
- **Cost Efficiency**: 30%+ cost reduction through intelligent routing

## 📋 Configuration Reference

See `config/admin_config.yaml` for complete configuration options including:
- Provider configurations and model mappings
- Cache settings and TTL policies
- Budget limits and enforcement rules
- Routing strategies and A/B test configurations
- Security settings and key vault integration
- Analytics and monitoring configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with comprehensive tests
4. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
