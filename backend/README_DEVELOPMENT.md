# Backend Development & CI/CD Guide

## Overview

This document provides comprehensive guidance for backend development and CI/CD processes, based on lessons learned from CI/CD failure analysis (June 30, 2025).

## Quick Start - Local Development

### 1. Environment Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run environment fixes (if needed)
python fix_environment.py

# Run local validation before committing
python local_validation.py
```

### 2. Pre-Commit Validation

**CRITICAL**: Always run local validation before pushing to prevent CI/CD failures:

```bash
# Quick validation (focuses on critical imports and basic tests)
python local_validation.py

# Comprehensive validation (full CI/CD simulation)
python comprehensive_e2e_validation.py
```

## CI/CD Failure Prevention

### Root Cause Analysis (June 30, 2025)

**Primary Issue**: Import errors not caught locally
- `User` class not imported in `app/api/feedback.py`
- `TripCosmosRepository` not imported in `app/core/dependencies.py`

**Secondary Issues**:
- Local validation too narrow (AI-focused only)
- No comprehensive import checking
- Binary compatibility issues (pandas/numpy)

### Prevention Measures

1. **Enhanced Local Validation**: New comprehensive validation scripts
2. **Import Validation**: Systematic checking of all critical imports
3. **CI/CD Debug Workflow**: Detailed debugging capabilities
4. **Environment Fixes**: Binary compatibility issue resolution

## Local Validation Scripts

### 1. `local_validation.py` (Quick Check)
- **Purpose**: Fast validation for daily development
- **Focus**: Critical imports, basic tests, AI functionality
- **Runtime**: ~2-5 minutes
- **Usage**: Run before every commit

```bash
python local_validation.py
```

### 2. `comprehensive_e2e_validation.py` (Full Validation)
- **Purpose**: Complete CI/CD simulation
- **Focus**: All imports, architecture, quality, tests
- **Runtime**: ~10-20 minutes  
- **Usage**: Run before major pushes, releases

```bash
python comprehensive_e2e_validation.py
```

### 3. `fix_environment.py` (Environment Repair)
- **Purpose**: Fix binary compatibility issues
- **Focus**: pandas/numpy version conflicts
- **Usage**: Run when import errors occur

```bash
python fix_environment.py
```

## CI/CD Debugging

### Debug Workflow

If CI/CD fails, use the debug workflow:

```bash
# Trigger from GitHub Actions tab
gh workflow run debug-ci-cd.yml
```

**Debug Levels**:
- `basic`: Environment and import checks only
- `comprehensive`: + architecture and test validation
- `full`: + complete quality checks

### Common CI/CD Failure Patterns

#### 1. Import Errors
**Symptoms**: `NameError: name 'X' is not defined`

**Solutions**:
- Check all import statements in affected files
- Run `python local_validation.py` to catch locally
- Verify imports follow consistent patterns

#### 2. Test Collection Failures
**Symptoms**: `ConftestImportFailure`, test collection errors

**Solutions**:
- Run `pytest tests/ --collect-only` locally
- Check for missing imports in test files
- Verify test environment setup

#### 3. Binary Compatibility Issues
**Symptoms**: `numpy.dtype size changed`

**Solutions**:
- Run `python fix_environment.py`
- Reinstall pandas/numpy with compatible versions
- Check Python version compatibility

#### 4. Architecture Violations
**Symptoms**: Import-linter violations

**Solutions**:
- Review `importlinter_contracts/layers.toml`
- Follow clean architecture patterns
- Separate concerns properly

## Development Workflow Best Practices

### 1. Before Starting Work
```bash
# Update dependencies
pip install -r requirements.txt

# Check environment health
python local_validation.py
```

### 2. During Development
```bash
# Check specific imports after making changes
python -c "import app.api.your_module"

# Run related tests
pytest tests/test_your_module.py -v
```

### 3. Before Committing
```bash
# Critical: Always run local validation
python local_validation.py

# If validation fails, check specific issues
python comprehensive_e2e_validation.py
```

### 4. Before Major Push/Release
```bash
# Full validation
python comprehensive_e2e_validation.py

# Architecture check
lint-imports --config ../importlinter_contracts/layers.toml
```

## Import Management Guidelines

### Critical Import Patterns

```python
# API modules - always import User for auth
from ..models.user import User

# Services - import from appropriate layers
from app.core.repositories.your_repository import YourRepository

# Dependencies - import all required classes
from app.core.repositories.trip_cosmos_repository import TripCosmosRepository
```

### Import Validation Checklist

- [ ] All used classes are imported
- [ ] Import paths follow project structure
- [ ] No circular imports
- [ ] Relative imports use correct syntax (`..` for parent)

## Architecture Compliance

### Layer Separation Rules

1. **API Layer** (`app.api`):
   - Can import from `services`, `models`, `core`
   - Cannot directly import from `repositories`

2. **Service Layer** (`app.services`):
   - Can import from `repositories`, `models`, `core`
   - Cannot import from `api`

3. **Core Layer** (`app.core`):
   - Foundation layer
   - Minimal external dependencies

### Validation Commands

```bash
# Check architecture compliance
lint-imports --config ../importlinter_contracts/layers.toml

# Type checking
mypy app/ --ignore-missing-imports

# Code quality
flake8 . --max-line-length=88
black --check .
isort --check-only .
```

## Environment Variables

### Required for Local Development
```bash
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export ENVIRONMENT="testing"
export OPENAI_API_KEY="your-key-here"  # For AI features
```

### Required for CI/CD
- `AZURE_CREDENTIALS`
- `COSMOS_CONNECTION_STRING`
- `OPENAI_API_KEY`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

## Troubleshooting

### Common Local Issues

#### "User not defined" errors
```bash
# Check import statements
grep -r "User" app/api/your_file.py
# Add missing import
from ..models.user import User
```

#### Test collection failures
```bash
# Check test imports
pytest tests/ --collect-only -v
# Fix import paths in conftest.py or test files
```

#### Binary compatibility errors
```bash
# Fix environment
python fix_environment.py
# Or manually:
pip uninstall pandas numpy -y
pip install numpy==1.24.3 pandas==2.0.3
```

### CI/CD Issues

#### Import errors in CI but not locally
- Check Python path differences
- Verify all imports are explicit
- Run `comprehensive_e2e_validation.py` locally

#### Secrets not found
- Verify GitHub secrets configuration
- Check secret names match exactly
- Use debug workflow to validate

## Performance Optimization

### Local Validation Speed
- Run `local_validation.py` for quick checks
- Use `comprehensive_e2e_validation.py` only when needed
- Fix import errors first (cheapest to resolve)

### CI/CD Pipeline Speed  
- Parallel job execution
- Cached dependencies
- Early failure detection

## Support & Resources

### When CI/CD Fails
1. Check GitHub Actions logs
2. Run debug workflow: `gh workflow run debug-ci-cd.yml`
3. Run local validation: `python local_validation.py`
4. Check this guide for common patterns
5. Fix issues and re-run validation locally

### Development Tools
- **VS Code**: Use Python extension for import checking
- **PyCharm**: Enable import optimization
- **Command Line**: Use validation scripts regularly

### Key Files
- `local_validation.py`: Quick validation
- `comprehensive_e2e_validation.py`: Full validation  
- `fix_environment.py`: Environment fixes
- `.github/workflows/debug-ci-cd.yml`: CI/CD debugging

---

**Remember**: The goal is to catch all CI/CD issues locally before pushing. These tools and processes ensure zero CI/CD failures due to preventable issues like import errors.
