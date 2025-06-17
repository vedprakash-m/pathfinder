# CI/CD Troubleshooting Guide

This document contains solutions for common CI/CD failures in the Pathfinder project.

## Backend Quality Failures

### Python 3.12 Compilation Issues

**Symptom**: CI/CD fails with compilation errors for `dependency-injector` package:
```
error: command '/usr/bin/gcc' failed with exit code 1
ERROR: Failed building wheel for dependency-injector
```

**Root Cause**: The `dependency-injector` package (version 4.41.0) has compatibility issues with Python 3.12+ due to internal CPython API changes.

**Solution**: 
1. Keep Python version pinned to 3.11 in CI/CD workflows
2. Already configured in `.github/workflows/ci-cd-pipeline.yml`:
   ```yaml
   - name: Set up Python 3.11
     uses: actions/setup-python@v5
     with:
       python-version: '3.11'
   ```

**Prevention**: 
- Run local validation with `DOCKER_REQUIRED=false ./scripts/validate-e2e-setup.sh`
- This will warn about Python 3.12+ compatibility issues

## Dependency Vulnerability Scan Failures

### Missing Poetry Configuration

**Symptom**: Snyk scan fails with:
```
Either [project.name] or [tool.poetry.name] is required in package mode.
Either [project.version] or [tool.poetry.version] is required in package mode.
```

**Solution**: Ensure `pyproject.toml` has project metadata:
```toml
[project]
name = "pathfinder"
version = "1.0.0"
description = "AI-Powered Group Trip Planner"
# ... other fields
```

**Prevention**: Local validation script checks for these fields.

### Missing Package Installation

**Symptom**: Snyk scan fails with:
```
Required packages missing: fastapi, uvicorn, python-multipart, ...
Please run `pip install -r backend/requirements.txt`.
```

**Solution**: Add package installation step before Snyk scan:
```yaml
- name: Install dependencies
  run: |
    cd backend
    pip install -r requirements.txt
```

## Infrastructure Deployment Failures

### Missing Data Layer Resources

**Symptom**: Deployment fails with:
```
Could not find SQL server in data layer
```

**Root Cause**: The data layer (pathfinder-db-rg) resources haven't been deployed.

**Solution**: Deploy data layer first:
```bash
./scripts/deploy-data-layer.sh
```

**Resources Required in Data Layer**:
- SQL Server
- Cosmos DB account  
- Storage account
- Key Vault

**Prevention**: 
- Run local validation to check Azure resources
- Validation script checks for all required data layer components

### Missing Azure Credentials

**Symptom**: Azure CLI commands fail in CI/CD.

**Solution**: Ensure GitHub Secrets are configured:
- `AZURE_CREDENTIALS`: Service principal JSON
- `SQL_ADMIN_USERNAME`: Database admin username
- `SQL_ADMIN_PASSWORD`: Database admin password

## Container Security Scan Issues

### CodeQL Upload Permissions

**Symptom**: 
```
Warning: Resource not accessible by integration
Error: Resource not accessible by integration
```

**Root Cause**: GitHub token permissions insufficient for CodeQL uploads.

**Solution**: Ensure workflow has proper permissions:
```yaml
permissions:
  security-events: write
  contents: read
```

## General Prevention

### Use Enhanced Local Validation

Run comprehensive validation before pushing:
```bash
# Full validation (requires Docker)
./scripts/validate-e2e-setup.sh

# CI/CD validation (no Docker required)  
DOCKER_REQUIRED=false ./scripts/validate-e2e-setup.sh
```

This will catch:
- Python version compatibility issues
- Missing Poetry configuration
- Backend dependency problems
- Azure resource prerequisites
- Security scan requirements

### Environment Consistency

1. **Python Version**: Keep 3.11 across all environments
2. **Dependencies**: Test installation locally
3. **Azure Resources**: Validate data layer before compute deployment
4. **Secrets**: Ensure all required environment variables are set

### Monitoring

- Check GitHub Actions logs for specific error patterns
- Use validation script output to identify root causes
- Monitor dependency security advisories

## Quick Fixes

Common one-liner fixes:

```bash
# Fix pyproject.toml (already done)
# See pyproject.toml [project] section

# Fix Python version in CI/CD (already done)  
# See .github/workflows/ci-cd-pipeline.yml

# Check Azure resources
az resource list --resource-group pathfinder-db-rg --output table

# Test backend dependencies
./scripts/test-backend-deps.sh

# Full validation
DOCKER_REQUIRED=false ./scripts/validate-e2e-setup.sh
```
