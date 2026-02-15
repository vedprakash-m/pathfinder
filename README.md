# Pathfinder – AI-Powered Group Trip Planner

[![CI/CD](https://github.com/vedprakash-m/pathfinder/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions/workflows/ci-cd.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

**Pathfinder** is an AI-powered platform that transforms multi-family group trip planning into a streamlined, collaborative experience. By centralizing communication, gathering preferences intelligently, and generating AI-powered itineraries, Pathfinder eliminates the typical frustrations of group travel planning.

---

## 🎯 Table of Contents

1. [Why Pathfinder?](#-why-pathfinder)
2. [Key Features](#-key-features)
3. [Architecture](#-architecture)
4. [Quick Start](#-quick-start)
5. [Deployment](#-deployment)
6. [Development](#-development)
7. [Testing](#-testing)
8. [Cost](#-cost)
9. [License](#-license)

---

## 🚀 Why Pathfinder?

**For Families & Groups:**
- **Eliminate Decision Paralysis:** AI-powered itinerary generation with multiple options
- **Streamline Communication:** Real-time messaging, polls, and collaborative planning
- **Budget Transparency:** Shared expense tracking with automatic settlement suggestions
- **Mobile-First Experience:** Progressive Web App works seamlessly across all devices

**For Developers:**
- **Cost-Optimized:** Serverless architecture for 70-80% lower costs vs traditional hosting
- **Modern Stack:** React 18, Azure Functions, Cosmos DB Serverless
- **Enterprise Security:** Microsoft Entra ID with zero-trust architecture
- **Infrastructure as Code:** Bicep templates for reproducible deployments

---

## ✨ Key Features

### 🤖 AI-Powered Planning
- **Smart Itinerary Generation:** GPT-powered trip planning with context awareness
- **Preference Aggregation:** AI understands group preferences, budgets, and constraints
- **Interactive Assistant:** Natural language chat for trip suggestions and modifications

### 🏠 Multi-Family Coordination
- **Family Management:** Create families and invite members via email
- **Role-Based Access:** Family Admin, Trip Organizer, and Member permissions
- **Consensus Building:** Interactive polls and voting for group decisions

### 💬 Real-Time Collaboration
- **Live Updates:** SignalR-powered real-time notifications
- **Smart Polls:** Gather preferences and make group decisions efficiently
- **Activity Feeds:** Stay updated on trip planning progress

### 🔐 Enterprise Security
- **Microsoft Entra ID:** Modern identity management with MSAL
- **Zero-Trust Architecture:** JWT validation on every request
- **Secrets Management:** Azure Key Vault for secure credential storage

---

## 🏗️ Architecture

Pathfinder uses a modern serverless architecture optimized for cost and scalability.

```
┌─────────────────────────────────────────────────────────────────┐
│                      pathfinder-rg (West US 2)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │  Static Web App  │────▶│     Azure Functions (Flex)       │  │
│  │  (React + Vite)  │     │     (Python 3.13)                │  │
│  │     [FREE]       │     │                                  │  │
│  └──────────────────┘     │  ┌────────────┐ ┌────────────┐  │  │
│                           │  │ HTTP APIs  │ │ Queue Funcs│  │  │
│                           │  └────────────┘ └────────────┘  │  │
│                           │  ┌────────────┐ ┌────────────┐  │  │
│                           │  │Timer Tasks │ │ SignalR Hub│  │  │
│                           │  └────────────┘ └────────────┘  │  │
│                           └───────────┬──────────────────────┘  │
│                                       │                          │
│  ┌─────────────────┐  ┌───────────────┴───────┐  ┌───────────┐  │
│  │   Cosmos DB     │  │     Key Vault         │  │  SignalR  │  │
│  │  (Serverless)   │  │  (Secrets Store)      │  │  [FREE]   │  │
│  └─────────────────┘  └───────────────────────┘  └───────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌───────────────────────┐                 │
│  │ Storage Account │  │  Application Insights │                 │
│  │ (Queue Storage) │  │   (Monitoring)        │                 │
│  └─────────────────┘  └───────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Fluent UI v9 |
| Backend | Azure Functions v2 (Python 3.13), Blueprint-based |
| Database | Azure Cosmos DB (Serverless, NoSQL API — single `entities` container) |
| Real-time | Azure SignalR Service (Free tier) |
| Auth | Microsoft Entra ID, MSAL.js, PyJWT + JWKS |
| AI | OpenAI GPT-4o |
| Queues | Azure Storage Queues (itinerary generation, notifications) |
| Infrastructure | Bicep IaC, GitHub Actions CI/CD |

### Backend Architecture

The backend follows **clean architecture** with domain-driven design:

```
function_app.py          ← Azure Functions entry point (registers blueprints)
├── functions/http/      ← HTTP triggers (thin controllers, no business logic)
├── functions/queue/     ← Queue triggers (async itinerary generation, notifications)
├── functions/timer/     ← Timer triggers (cleanup expired data, close polls)
├── services/            ← Business logic layer (source of truth for all contracts)
├── models/documents.py  ← Cosmos DB document models (Pydantic v2)
├── models/schemas.py    ← API request/response schemas
├── repositories/        ← Data access (singleton cosmos_repo with typed CRUD)
└── core/                ← Config, security (JWT validation), error handling
```

**Key pattern:** Services are the source of truth. HTTP functions are thin wrappers that validate input, call a service method, and return the response. All Cosmos DB access goes through the `cosmos_repo` singleton.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 20+
- Azure Functions Core Tools v4
- Azure CLI

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure local settings (edit with your values)
# local.settings.json is git-ignored - update placeholder values:
#   - COSMOS_DB_KEY
#   - SIGNALR_CONNECTION_STRING
#   - OPENAI_API_KEY
#   - ENTRA_CLIENT_ID

# Start Functions locally
func start
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.template .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

---

## 📦 Deployment

### Infrastructure

```bash
# Login to Azure
az login

# Deploy infrastructure
cd infrastructure/bicep
az deployment sub create \
  --name pathfinder-deployment \
  --location westus2 \
  --template-file main.bicep \
  --parameters @parameters/prod.parameters.json
```

### Configure Secrets

```bash
# Get Key Vault name
KV_NAME=$(az keyvault list -g pathfinder-rg --query "[0].name" -o tsv)

# Set required secrets
az keyvault secret set --vault-name $KV_NAME --name openai-api-key --value "YOUR_KEY"
az keyvault secret set --vault-name $KV_NAME --name entra-client-id --value "YOUR_ID"
```

### CI/CD Pipeline

Pathfinder uses a **unified CI/CD pipeline** (`ci-cd.yml`) that:

1. **Detects changes** - Only runs jobs for components that changed
2. **Runs tests in parallel** - Backend and frontend tests run simultaneously
3. **Deploys in order** - Infrastructure → Backend → Frontend
4. **Supports manual dispatch** - Deploy specific components on demand

#### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure login |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | SWA deployment token |
| `ENTRA_CLIENT_ID` | Microsoft Entra client ID |

#### Resource Naming Convention

All Azure resources use deterministic, idempotent naming:

| Resource | Production Name |
|----------|----------------|
| Resource Group | `pathfinder-rg` |
| Cosmos DB | `pf-cosmos-<uniqueId>` |
| Function App | `pf-func-<uniqueId>` |
| Static Web App | `pf-swa-<uniqueId>` |
| Key Vault | `pf-kv-<uniqueId>` |
| SignalR | `pf-signalr-<uniqueId>` |
| Storage | `pfstore<uniqueId>` |

> **Note:** `<uniqueId>` is generated from `uniqueString(subscriptionId, 'pathfinder')` for global uniqueness.

Push to `main` to trigger deployment. Only changed components are deployed.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

---

## 🛠️ Development

### Project Structure

```
pathfinder/
├── backend/
│   ├── function_app.py        # Azure Functions entry point
│   ├── core/                   # Config, security, error handling
│   ├── models/
│   │   ├── documents.py        # Cosmos DB document models (Pydantic v2)
│   │   └── schemas.py          # API request/response schemas
│   ├── repositories/
│   │   └── cosmos_repository.py  # Singleton data access layer
│   ├── services/               # Business logic (source of truth)
│   └── functions/
│       ├── http/               # HTTP triggers (API endpoints)
│       ├── queue/              # Queue triggers (async processing)
│       └── timer/              # Timer triggers (scheduled cleanup)
├── frontend/
│   ├── src/
│   │   ├── components/         # React components (Fluent UI v9)
│   │   ├── pages/              # Route pages
│   │   ├── services/           # API clients
│   │   └── lib/                # Utilities
│   └── public/
├── infrastructure/
│   └── bicep/                  # Azure Bicep IaC templates
├── specs/                      # PRD, Tech Spec, Tasks
└── docs/                       # Deployment guide
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/trips` | List user's trips |
| POST | `/api/trips` | Create new trip |
| POST | `/api/trips/{id}/itinerary` | Generate AI itinerary |
| GET | `/api/families` | List user's families |
| POST | `/api/families` | Create new family |
| POST | `/api/trips/{id}/polls` | Create poll |

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests

```bash
cd frontend
npm test -- --coverage
```

### Linting

```bash
# Backend
cd backend && ruff check .

# Frontend
cd frontend && npm run lint
```

---

## 💰 Cost

Estimated monthly cost with serverless architecture:

| Resource | Tier | Cost |
|----------|------|------|
| Static Web Apps | Free | $0 |
| SignalR | Free | $0 |
| Cosmos DB | Serverless | ~$5-10 |
| Functions | Flex Consumption | ~$2-5 |
| Storage | Standard LRS | ~$1 |
| Key Vault | Standard | ~$1 |
| App Insights | Basic | ~$1-2 |

**Total: ~$10-20/month** (vs. $150+ with container-based hosting)

---

## 📄 License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).

---

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Decisions](architecture_decision_records/)
- [Product Requirements](specs/PRD-Pathfinder.md)
- [Technical Specification](specs/Tech_Spec_Pathfinder.md)
- [Implementation Tasks](specs/Tasks.md)

---

## 🔒 Security

This project implements multiple layers of secret protection:

- **Git Ignore:** Comprehensive `.gitignore` blocks all secret file patterns
- **Pre-commit Hooks:** Optional gitleaks integration for secret scanning
- **Key Vault:** Production secrets stored in Azure Key Vault
- **Environment Variables:** Local secrets in git-ignored files only

**Never commit:**
- `.env` files with real values
- `local.settings.json` with real credentials
- API keys, connection strings, or certificates
