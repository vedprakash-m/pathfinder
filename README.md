# Pathfinder – AI-Powered Group Trip Planner

[![CI/CD Pipeline](https://github.com/vedprakash-m/pathfinder/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![Infrastructure Management](https://github.com/vedprakash-m/pathfinder/actions/workflows/infrastructure-management.yml/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

> **🔧 Latest Update**: Enhanced CI/CD reliability with environment-aware configuration system. The pipeline now automatically handles test vs. production environment differences, ensuring consistent deployments.

**Pathfinder** is a production-ready, AI-powered platform that transforms the chaotic process of planning multi-family group trips into a streamlined, collaborative experience. By centralizing communication, gathering preferences intelligently, and generating AI-powered itineraries, Pathfinder eliminates the typical frustrations of group travel planning.

---
## 🎯 Table of Contents
1. [Why Pathfinder?](#-why-pathfinder)
2. [Key Features](#-key-features)  
3. [Architecture Overview](#-architecture-overview)  
4. [Quick Start (Local)](#-quick-start-local-development)  
5. [Cloud Deployment (Azure)](#-cloud-deployment-azure)  
6. [Development Workflow](#-development-workflow)  
7. [Testing](#-testing)  
8. [Cost Optimization](#-cost-optimization)  
9. [License](#-license)

---
## 🚀 Why Pathfinder?

**For Families & Groups:**
- **Eliminate Decision Paralysis:** AI-powered itinerary generation with multiple options
- **Streamline Communication:** Real-time chat, polls, and collaborative planning
- **Budget Transparency:** Shared expense tracking with automatic settlement suggestions
- **Mobile-First Experience:** Progressive Web App works seamlessly across all devices

**For Developers & Organizations:**
- **Production-Ready:** Enterprise-grade security with Auth0 and comprehensive monitoring
- **Cost-Optimized:** Innovative pause/resume architecture saves 70% on idle infrastructure
- **Modern Stack:** React 18, FastAPI, Azure Container Apps with Bicep IaC
- **Comprehensive Testing:** Full E2E test suite with Playwright and automated CI/CD

---
## ✨ Key Features
### 🤖 AI-Powered Planning
- **Multi-Provider LLM Orchestration:** OpenAI, Gemini, and Claude integration with intelligent fallbacks
- **Context-Aware Recommendations:** AI understands group preferences, budgets, and constraints
- **Cost-Controlled AI:** Budget limits and usage tracking prevent runaway costs

### 🏠 Multi-Family Coordination  
- **Role-Based Access Control:** Family Admin, Trip Organizer, and Member roles
- **Smart Invitation System:** Email-based family invitation workflow with permissions
- **Consensus Building:** Interactive polls and decision-making tools

### 💬 Real-Time Collaboration
- **Live Chat & Presence:** Socket.IO-powered real-time communication
- **Smart Polls:** Gather preferences and make group decisions efficiently
- **Activity Feeds:** Stay updated on trip planning progress

### 💰 Financial Management
- **Shared Budget Tracking:** Transparent expense management across families
- **Settlement Suggestions:** Automated calculations for cost splitting
- **Spending Analytics:** Track expenses by category and family

### 🔐 Enterprise Security
- **Zero-Trust Architecture:** Microsoft Entra External ID integration with comprehensive RBAC
- **Data Protection:** CSRF/CORS protection, input validation, audit logging
- **Secrets Management:** Azure Key Vault integration with automatic rotation

---
## 🏗️ Architecture Overview

Pathfinder employs a cost-optimized two-layer architecture designed for scalability and efficiency. Complete technical documentation is available in [`docs/metadata.md`](docs/metadata.md).

### 🔄 Two-Layer Azure Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENT DATA LAYER                        │
│                      (pathfinder-db-rg)                        │
│  💾 Azure SQL Database     🗄️  Cosmos DB (Serverless)          │
│  📁 Storage Account        🔐 Key Vault (Secrets)              │
│  ├─ Never deleted for data preservation                        │
│  └─ $15-25/month baseline cost                                 │
└─────────────────────────────────────────────────────────────────┘
                                    ⬆️
                             Data persistence
                                    ⬇️
┌─────────────────────────────────────────────────────────────────┐
│                   EPHEMERAL COMPUTE LAYER                      │
│                       (pathfinder-rg)                          │
│  🚀 Container Apps Env     📦 Container Registry               │
│  🖥️  Backend API Service   🌐 Frontend Web App                │
│  📊 Application Insights   ⚖️  Auto-scaling (0-N instances)   │
│  ├─ Safe to delete for 70% cost reduction                      │
│  └─ $35-50/month when active, $0 when paused                  │
└─────────────────────────────────────────────────────────────────┘
```

### ⚡ Cost Optimization Benefits
- **Active State:** Full functionality, $50-75/month
- **Paused State:** Data preserved, compute deleted, $15-25/month  
- **Resume Time:** 5-10 minutes via automated CI/CD
- **Savings:** Up to 70% cost reduction during idle periods

### 🛠️ Technology Stack
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Fluent UI v9 + PWA
- **Backend:** FastAPI + Python 3.11 + Pydantic v2 + SQLAlchemy + Alembic
- **Real-time:** Socket.IO for chat and live presence
- **AI Services:** Custom LLM orchestration with cost tracking and fallbacks
- **Data:** Azure SQL (relational) + Cosmos DB (documents) + SQLite (local dev)
- **Caching:** Redis for session management and performance optimization
- **Infrastructure:** Docker + Bicep IaC + Azure Container Apps + Azure Key Vault
- **CI/CD:** GitHub Actions with optimized workflows (71% reduction in complexity)
- **Authentication:** Microsoft Entra External ID with zero-trust security model
- **Testing:** Playwright E2E + Pytest with comprehensive coverage

---
## 🚀 Quick Start (Local Development)

### Prerequisites
- **Node.js 18+** and **Python 3.11+** 
- **Docker** and **Docker Compose**
- At least **4GB RAM** available

### Setup & Launch
```bash
# Clone the repository
git clone https://github.com/vedprakashmishra/pathfinder.git
cd pathfinder

# Configure backend environment (copy from template)
cp backend/.env.test backend/.env

# Configure frontend environment (copy from template)
cp frontend/.env.template frontend/.env.local

# Launch the full stack
docker compose up -d

# Access the applications
open http://localhost:3000        # React PWA (Frontend)
open http://localhost:8000/docs   # FastAPI Documentation (Backend)
```

### Local Development with Validation
```bash
# Quick validation before commits (recommended)
./scripts/local-validation.sh --quick

# Full validation with auto-fix
./scripts/local-validation.sh --fix

# Run comprehensive E2E tests
./scripts/run-e2e-tests.sh
```

**What's Included:**
- ✅ **Backend API** with FastAPI and auto-generated documentation at `/docs`
- ✅ **Frontend PWA** with hot-reload and modern development tools  
- ✅ **Database** with SQLite for local development and Cosmos DB emulator
- ✅ **Real-time features** via Socket.IO
- ✅ **Caching** with Redis for optimal performance
- ✅ **AI integration** with mock services for local testing

---
## ☁️ Cloud Deployment (Azure)

Pathfinder uses **Bicep Infrastructure as Code** for reliable, repeatable deployments to Azure. The platform is designed for Azure-first deployment with cost optimization built-in.

### 🔐 Prerequisites
1. **Azure Subscription** with appropriate permissions
2. **GitHub Repository Secrets** configured:
   - `AZURE_CREDENTIALS` (Service Principal JSON)
   - `SQL_ADMIN_USERNAME` (Database admin username)  
   - `SQL_ADMIN_PASSWORD` (Database admin password)
   - `OPENAI_API_KEY` (Optional - for AI features)
   - `ENTRA_TENANT_ID` (Microsoft Entra External ID tenant)
   - `ENTRA_CLIENT_ID` (Microsoft Entra External ID client ID)

### 🏗️ Deployment Process

#### 1. One-Time Data Layer Setup
```bash
# Deploy persistent data layer (SQL, Cosmos DB, Storage, Key Vault)
./scripts/deploy-data-layer.sh

# Or use GitHub Actions workflow: "Deploy Infrastructure"
```

#### 2. Deploy/Resume Compute Layer  
```bash
# Deploy or resume the complete application
./scripts/resume-environment.sh

# Or simply push to main branch - CI/CD will auto-deploy
git push origin main
```

#### 3. Cost Optimization (Pause)
```bash
# Pause compute layer to save 70% on costs
./scripts/pause-environment.sh

# Data layer remains active for immediate resume
```

### 🔄 Automated CI/CD Pipeline
Our optimized CI/CD system provides:
- ✅ **Quality Gates:** Code formatting, linting, security scanning
- ✅ **Comprehensive Testing:** Unit tests, integration tests, E2E validation  
- ✅ **Performance Monitoring:** Load testing and response time tracking
- ✅ **Security Scanning:** Dependency vulnerabilities and container scanning
- ✅ **Cost Monitoring:** Azure resource usage alerts and optimization
- ✅ **Zero-Downtime Deployment:** Container-based rolling updates

**Recent Optimizations:**
- **71% reduction** in workflow complexity (7 → 2 workflows)
- **40-60% faster** execution via parallel jobs and intelligent caching
- **Enhanced error reporting** with actionable guidance

---
## 🛠️ Development Workflow

### Local Validation System
Before pushing changes to CI/CD, use our comprehensive local validation system with enhanced dependency checking:

```bash
# Quick validation (recommended before every commit)
cd backend && python3 local_validation.py

# Check for undeclared dependencies
cd backend && python3 local_validation.py --dependency-check

# Full project validation
./scripts/local-validation.sh --fix
```

### What Gets Validated
- ✅ **Dependencies:** Undeclared dependencies, requirements.txt completeness, package conflicts
- ✅ **CI/CD Parity:** Test collection validation, environment consistency
- ✅ **Code Quality:** Formatting, linting, type checking, imports
- ✅ **Build Compatibility:** Docker build validation
- ✅ **Git Status:** Branch awareness and uncommitted changes
- ✅ **Infrastructure:** GitHub Actions and Azure prerequisites

### Dependency Validation Features
- 🔍 **Undeclared Dependency Detection:** Scans imports vs requirements.txt
- 📚 **Standard Library Filtering:** Avoids false positives for built-in modules
- 🔀 **Import Name Mapping:** Handles cases like `jwt` → `python-jose`
- 🎯 **CI/CD Environment Simulation:** Ensures local matches CI/CD exactly

### Benefits
- 🚀 **40-60% faster feedback** than waiting for CI/CD
- 🔧 **Auto-fix mode** resolves common issues automatically  
- 🛡️ **Prevents CI/CD failures** by catching dependency issues locally
- 📊 **Comprehensive reporting** with actionable guidance

### CI/CD Pipeline
Our streamlined pipeline includes:

1. **Quality Checks** - Code formatting, linting, type checking
2. **Security Scanning** - Dependency vulnerabilities and container scanning  
3. **Build & Test** - Docker builds and automated testing
4. **Performance Testing** - Load testing and performance benchmarks
5. **Cost Monitoring** - Azure resource usage and optimization alerts
6. **Deployment** - Automated deployment with rollback capabilities

**Key Optimizations:**
- ✅ **Consolidated workflows** - 71% reduction (7 → 2 workflows)
- ✅ **Parallel execution** - 40-60% faster builds
- ✅ **Smart caching** - 40% reduction in build times
- ✅ **Enhanced debugging** - Comprehensive error reporting

---
## 🧪 Testing

Pathfinder includes a comprehensive testing strategy covering unit tests, integration tests, and end-to-end validation.

### Unit & Integration Tests
```bash
# Backend tests with coverage reporting
cd backend && pytest -v --cov

# Frontend tests with component validation  
cd frontend && npm test
```

### End-to-End Testing Suite
**Comprehensive E2E validation** using Docker Compose + Playwright:

```bash
# Run complete E2E test suite (single command)
./scripts/run-e2e-tests.sh

# Validate E2E setup and prerequisites
./scripts/validate-e2e-setup.sh
```

### E2E Testing Features
- **Multi-Browser Testing:** Chrome, Firefox, Safari, Mobile simulation
- **Complete Isolation:** Dedicated MongoDB + Redis for each test run  
- **Comprehensive Coverage:** Authentication, CRUD operations, API integration, user workflows
- **Mock Services:** Authentication and external service mocking
- **Automated Orchestration:** Single command execution with cleanup
- **Performance Testing:** Load testing and response time validation

### Test Categories
1. **Authentication Flows** - Login, logout, session management
2. **Core CRUD Operations** - Trip and family management  
3. **API Integration** - Complete backend endpoint validation
4. **User Workflows** - End-to-end journey testing
5. **Error Scenarios** - Error handling and edge cases
6. **Performance Testing** - Load and response time testing

### Debugging & Development
```bash
# Run tests with visible browser (debugging)
cd tests/e2e && npx playwright test --debug

# Run specific test suites
npx playwright test auth          # Authentication tests
npx playwright test trips         # Trip management tests  
npx playwright test api           # API integration tests
```

**Test Reports:** Generated in HTML format with screenshots, videos, and comprehensive debugging information.

---
## 💰 Cost Optimization

Pathfinder's innovative two-layer architecture provides significant cost savings without compromising functionality.

### 💡 Smart Cost Management
- **Active State:** Full functionality - $50-75/month
- **Paused State:** Data preserved, compute deleted - $15-25/month  
- **Savings:** Up to **70% cost reduction** during idle periods
- **Resume Time:** **5-10 minutes** via automated CI/CD

### 🔄 Pause/Resume Operations
```bash
# Pause compute layer (immediate cost savings)
./scripts/pause-environment.sh   

# Resume full functionality (5-10 minutes)
./scripts/resume-environment.sh  

# Check current infrastructure status
az resource list --resource-group pathfinder-rg --output table
```

### 📊 Cost Breakdown
| Component | Persistent Data Layer | Ephemeral Compute Layer | 
|-----------|----------------------|-------------------------|
| **Always Active** | Azure SQL, Cosmos DB, Storage, Key Vault | - |
| **When Active** | - | Container Apps, Registry, App Insights |
| **Monthly Cost (Active)** | $15-25 | $35-50 |
| **Monthly Cost (Paused)** | $15-25 | $0 |

### ⚡ Automation Features
- **GitHub Actions Integration:** Pause/resume via repository workflows
- **Scheduled Pausing:** Optional automated pausing during off-hours
- **Cost Monitoring:** Azure alerts for budget thresholds
- **Resource Optimization:** Auto-scaling with scale-to-zero capabilities

This architecture is ideal for:
- **Development teams** with intermittent usage patterns
- **Small organizations** requiring enterprise features on a budget  
- **Demo environments** that need occasional full functionality
- **Cost-conscious deployments** requiring production-grade capabilities

---
## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)** – see the [`LICENSE`](LICENSE) file for complete terms.

### 🔑 Key Licensing Points
- ✅ **Free Use:** Use, modify, and distribute freely
- ✅ **Commercial Use:** Permitted under AGPLv3 terms  
- ✅ **Network Services:** Source code must be available to users interacting over a network
- ✅ **Derivative Works:** Must be licensed under AGPLv3

### 💼 Commercial Licensing
For commercial use without AGPLv3 obligations, **dual licensing** options are available. Contact the maintainer for:
- Closed-source commercial deployments
- SaaS offerings without source code disclosure requirements
- Custom licensing terms for enterprise customers

### 📞 Contact & Support
- **Maintainer:** Ved Prakash
- **Repository:** [github.com/vedprakash-m/pathfinder](https://github.com/vedprakash-m/pathfinder)
- **Issues:** Report bugs and feature requests via GitHub Issues
- **Security:** Follow responsible disclosure guidelines in [`docs/metadata.md`](docs/metadata.md)

### 🤝 Contributing
We welcome contributions! Please see:
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for contribution guidelines
- [`docs/User_Experience.md`](docs/User_Experience.md) for UX principles  
- [`docs/metadata.md`](docs/metadata.md) for comprehensive technical documentation
- [`docs/Tech_Spec_Pathfinder.md`](docs/Tech_Spec_Pathfinder.md) for detailed technical specifications

---
**© Pathfinder 2025** – Empowering seamless group travel planning with AI-powered intelligence and cost-optimized cloud architecture.
