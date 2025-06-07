# Pathfinder CI/CD Pipeline Documentation

## Overview

This document describes the comprehensive CI/CD pipeline for Pathfinder, designed to automate testing, building, and deployment to Azure Container Apps.

## Pipeline Architecture

The pipeline consists of 7 main jobs that run sequentially:

1. **Backend Quality Checks** - Linting, formatting, type checking, and testing
2. **Frontend Quality Checks** - Linting, type checking, and testing  
3. **Build Backend Image** - Docker build and push to GitHub Container Registry
4. **Build Frontend Image** - Docker build and push to GitHub Container Registry
5. **Deploy Infrastructure** - Azure resource provisioning via Bicep templates
6. **Deploy Applications** - Container App deployment with latest images
7. **Post-Deployment Checks** - Health checks and deployment summary

## Required GitHub Secrets

### Azure Authentication
```
AZURE_CREDENTIALS - Azure service principal credentials (JSON format)
AZURE_SUBSCRIPTION_ID - Azure subscription ID
```

### Database Credentials
```
SQL_ADMIN_LOGIN - Azure SQL Database administrator username
SQL_ADMIN_PASSWORD - Azure SQL Database administrator password
```

### External Service APIs
```
OPENAI_API_KEY - OpenAI API key for AI generation
```

### Auth0 Configuration
```
AUTH0_DOMAIN - Auth0 domain (e.g., dev-jwnud3v8ghqnyygr.us.auth0.com)
AUTH0_AUDIENCE - Auth0 API audience identifier
AUTH0_CLIENT_ID - Auth0 client ID for frontend
```

### Azure Resource Connection Strings (Auto-generated)
```
AZURE_COSMOS_ENDPOINT - Cosmos DB endpoint URL
AZURE_COSMOS_KEY - Cosmos DB primary key
SQL_CONNECTION_STRING - Complete SQL connection string
```

## Setup Instructions

### 1. Azure Service Principal Setup

Create a service principal for GitHub Actions:

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "pathfinder-github-actions" \
  --role "Contributor" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID" \
  --sdk-auth

# Copy the JSON output to AZURE_CREDENTIALS secret
```

### 2. GitHub Secrets Configuration

In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

```yaml
# Required secrets for pipeline
AZURE_CREDENTIALS: |
  {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret", 
    "subscriptionId": "your-subscription-id",
    "tenantId": "your-tenant-id"
  }

AZURE_SUBSCRIPTION_ID: "your-subscription-id"
SQL_ADMIN_LOGIN: "your-sql-admin-username"
SQL_ADMIN_PASSWORD: "your-strong-password"
OPENAI_API_KEY: "sk-your-openai-key"
AUTH0_DOMAIN: "your-auth0-domain.auth0.com"
AUTH0_AUDIENCE: "your-api-audience"
AUTH0_CLIENT_ID: "your-auth0-client-id"
```

### 3. Pipeline Triggers

The pipeline triggers on:
- **Push to main**: Full deployment to production
- **Push to develop**: Quality checks and building (no deployment)
- **Pull requests**: Quality checks only

## Quality Checks

### Backend Quality Checks
- **Linting**: flake8 with line length 88, excluding E203,W503
- **Formatting**: black code formatter check
- **Import Sorting**: isort compatibility check
- **Type Checking**: mypy static type analysis
- **Testing**: pytest with coverage reporting

### Frontend Quality Checks  
- **Type Checking**: TypeScript compiler check
- **Linting**: ESLint with React-specific rules
- **Testing**: Vitest unit tests with coverage

## Build Process

### Backend Build
- Uses multi-stage Docker build from `./backend/Dockerfile`
- Tagged with both `latest` and commit SHA
- Pushed to GitHub Container Registry

### Frontend Build
- Uses multi-stage Docker build from `./frontend/Dockerfile`
- Tagged with both `latest` and commit SHA
- Pushed to GitHub Container Registry

## Deployment Strategy

### Infrastructure Deployment
- **Resource Group**: `rg-pathfinder-prod` in East US
- **Bicep Template**: `./infrastructure/bicep/main.bicep`
- **Resources Created**:
  - Container Apps Environment
  - Azure SQL Database
  - Cosmos DB
  - Redis Cache
  - Application Insights
  - Log Analytics Workspace
  - Key Vault
  - Storage Account

### Application Deployment
- **Backend**: Container App with environment variables
- **Frontend**: Container App with build-time environment variables
- **Health Checks**: Automated post-deployment verification

## Environment Variables

### Backend Environment Variables
```
AZURE_COSMOS_ENDPOINT - Cosmos DB connection
AZURE_COSMOS_KEY - Cosmos DB authentication
SQL_CONNECTION_STRING - Azure SQL connection
OPENAI_API_KEY - AI service integration
AUTH0_DOMAIN - Authentication service
AUTH0_AUDIENCE - API audience validation
```

### Frontend Environment Variables
```
VITE_API_BASE_URL - Backend API endpoint
VITE_AUTH0_DOMAIN - Auth0 domain for frontend
VITE_AUTH0_CLIENT_ID - Auth0 client configuration
VITE_AUTH0_AUDIENCE - Auth0 API audience
```

## Monitoring and Observability

### Health Checks
- **Backend**: `GET /health` endpoint verification
- **Frontend**: HTTP 200 response check
- **Failure Handling**: Pipeline marked as failed if health checks fail

### Deployment Summary
- **GitHub Step Summary**: Automatic deployment report
- **URLs**: Live application endpoints
- **Commit**: Deployed commit SHA
- **Status**: Success/failure indication

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify AZURE_CREDENTIALS JSON format
   - Check service principal permissions
   - Validate subscription ID

2. **Build Failures**
   - Check Dockerfile syntax
   - Verify dependency versions
   - Review build logs for specific errors

3. **Deployment Failures**
   - Validate Bicep template syntax
   - Check resource naming conflicts
   - Verify required secrets are set

4. **Health Check Failures**
   - Check application startup logs
   - Verify environment variable configuration
   - Test endpoints manually

### Pipeline Logs
- All jobs provide detailed logging
- Failed steps include error context
- Artifact uploads preserve build outputs

## Performance Optimizations

### Caching Strategy
- **pip dependencies**: Cached based on requirements.txt hash
- **npm dependencies**: Cached based on package-lock.json hash
- **Docker layers**: Optimized multi-stage builds

### Parallel Execution
- Backend and frontend quality checks run in parallel
- Build jobs run in parallel after quality checks pass
- Deployment is sequential for consistency

## Security Considerations

### Secret Management
- All sensitive data stored in GitHub Secrets
- No hardcoded credentials in repository
- Secrets rotated according to security policy

### Access Control
- Pipeline only runs on authorized branches
- Deployment requires successful quality checks
- Container registry access controlled by GitHub tokens

### Compliance
- Automated security scanning with CodeQL
- Dependency vulnerability checks
- Code quality enforcement before deployment

## Next Steps: Enhanced Pipeline

The current simple pipeline will be evolved to include:

1. **Multi-Environment Support** (dev, staging, prod)
2. **Feature Branch Deployments** (preview environments)
3. **Advanced Rollback Strategies** (blue/green deployments)
4. **Integration with Azure Key Vault** (enhanced secret management)
5. **Performance Testing** (automated load testing)
6. **Slack/Teams Notifications** (deployment status alerts)

## Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Bicep Template Reference](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure DevOps Integration](https://docs.microsoft.com/azure/devops/) 