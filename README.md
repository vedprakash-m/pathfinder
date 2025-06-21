# Pathfinder – AI-Powered Group Trip Planner

[![CI / CD](https://github.com/vedprakash-m/pathfinder/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![Pause / Resume](https://github.com/vedprakash-m/pathfinder/actions/workflows/pause-resume.yml/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

Pathfinder eliminates the chaos of planning **multi-family group trips** by centralising communication, preference gathering and AI-generated itineraries – all secured by Auth0 and deployed cost-efficiently on Azure.

---
## Table of Contents
1. Key Features  
2. Architecture Overview  
3. Quick Start (Local)  
4. Cloud Deployment (Azure)  
5. Development Workflow  
6. Testing  
7. Cost Optimisation & Pause/Resume  
8. License

---
## 1. Key Features
• **AI Itinerary Generation** – Multi-provider LLM orchestration (OpenAI / Gemini / Claude).  
• **Real-Time Collaboration** – Socket.IO chat, live presence and smart polls.  
• **Budget & Expense Tracking** – Shared cost breakdowns and settlement suggestions.  
• **Enterprise-grade Security** – Auth0 zero-trust model and Key Vault- backed secrets.  
• **Hybrid Storage** – Azure SQL (relational) + Cosmos DB (documents) + Storage Account (files).  
• **Cost-Aware Architecture** – Two-layer pause/resume model provides ± 70 % savings when idle.

---
## 2. Architecture Overview
A full description lives in [`docs/metadata.md`](docs/metadata.md) (single source of truth).  
High-level summary:

```
Persistent Layer (pathfinder-db-rg)   Ephemeral Layer (pathfinder-rg)
┌──────────────────────────────┐     ┌──────────────────────────────┐
│  • Azure SQL & Cosmos DB     │     │  • Azure Container Apps      │
│  • Storage Account (files)   │◄───►│  • Backend & Frontend        │
│  • Key Vault (secrets)       │     │  • Container Registry        │
└──────────────────────────────┘     │  • Application Insights      │
                                     └──────────────────────────────┘
```
Resume in 5-10 minutes; delete compute layer anytime for immediate savings.

---
## 3. Quick Start (Local Development)
Prerequisites: **Node 18+**, **Python 3.12+**, **Docker**
```bash
# Clone & prepare
git clone https://github.com/vedprakashmishra/pathfinder.git
cd pathfinder

# Back-end
cp backend/.env.example backend/.env

# Front-end
cp frontend/.env.example frontend/.env.local

# Launch full stack
docker compose up -d
open http://localhost:3000        # React PWA
open http://localhost:8000/docs   # FastAPI docs
```

---
## 4. Cloud Deployment (Azure)
Infrastructure is defined with **Bicep** in `infrastructure/bicep/` and automated by GitHub Actions.

1. **Secrets** – Add `AZURE_CREDENTIALS`, `SQL_ADMIN_USERNAME`, `SQL_ADMIN_PASSWORD`, (optional) `OPENAI_API_KEY` to your repository.  
2. **Deploy Data Layer (one-time)**
   ```bash
   ./scripts/deploy-data-layer.sh   # or run the "Deploy Infrastructure" workflow
   ```
3. **Resume / Deploy Compute Layer**
   ```bash
   ./scripts/resume-environment.sh  # or commit/push to trigger CI/CD
   ```
4. **Pause to Save Cost**  
   ```bash
   ./scripts/pause-environment.sh
   ```

For advanced options, see the **Pause / Resume** workflow or the scripts in `scripts/`.

---
## 5. Development Workflow

### Local Validation System

Before pushing changes to CI/CD, run our comprehensive local validation:

```bash
# Quick validation (recommended before every commit)
./scripts/local-validation.sh --quick

# Full validation with auto-fix
./scripts/local-validation.sh --fix

# Full validation (check-only mode)
./scripts/local-validation.sh
```

**What it validates:**
- ✅ Requirements.txt syntax and package conflicts
- ✅ Frontend package.json and dependencies
- ✅ Backend code quality (formatting, linting, imports)
- ✅ Docker build compatibility
- ✅ Git status and branch awareness

**Benefits:**
- 🚀 **40-60% faster feedback** than waiting for CI/CD
- 🔧 **Auto-fix mode** resolves common issues automatically
- 🛡️ **Prevents CI/CD failures** by catching issues locally
- 📊 **Comprehensive reporting** with actionable guidance
- 🔍 **GitHub Actions validation** catches missing action references
- 🏗️ **Infrastructure prerequisite checking** prevents deployment failures

### CI/CD Pipeline Status

Our streamlined CI/CD system runs the same validations plus deployment:

1. **Quality Checks** - Code formatting, linting, type checking
2. **Security Scanning** - Dependency vulnerabilities and container scanning  
3. **Build & Test** - Docker builds and automated testing
4. **Performance Testing** - Load testing and performance benchmarks
5. **Cost Monitoring** - Azure resource usage and optimization alerts
6. **Deployment** - Automated deployment with rollback capabilities

**Recent Optimizations:**
- ✅ Consolidated 7 workflows → 2 efficient workflows (71% reduction)
- ✅ 40-60% faster execution via parallel jobs
- ✅ Smart caching reduces build times by 40%
- ✅ Enhanced error reporting and debugging

Continuous integration executes the full test suite and, on main, builds & deploys containers to Azure Container Apps.

---
## 6. Testing

### Unit and Integration Tests
```bash
# Back-end tests
cd backend && pytest -v

# Front-end tests  
cd frontend && npm test
```

### End-to-End Testing
Pathfinder includes a comprehensive E2E testing suite using Docker Compose and Playwright for complete workflow validation:

```bash
# Run full E2E test suite
./scripts/run-e2e-tests.sh
```

The E2E suite tests:
- User authentication flows
- Trip management (CRUD operations)
- Family management and invitations
- API integration and error handling
- Complete user workflows across multiple features

For detailed E2E testing documentation, setup instructions, and debugging guides, see [`E2E_TESTING.md`](E2E_TESTING.md).

---
## 7. Cost Optimisation
• **Active**: ≈ $50–75 / month  
• **Paused (compute deleted)**: ≈ $15–25 / month  
Save ≈ 70 % with one command:
```bash
./scripts/pause-environment.sh   # Pause
./scripts/resume-environment.sh  # Resume
```

---
## 8. License
This project is licensed under the **GNU Affero General Public License v3.0** – see [`LICENSE`](LICENSE).  
Commercial or closed-source usage is available via dual-licensing; contact the maintainer for details.
