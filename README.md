# Pathfinder - AI-Powered Group Trip Planner

[![Build Status](https://github.com/vedprakash-m/pathfinder/workflows/Enhanced%20Production%20Pipeline/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)](https://codecov.io/gh/vedprakash-m/pathfinder)
[![Deployment](https://img.shields.io/badge/Deployment-Live-green.svg)](#live-application)

AI-powered platform for coordinating multi-family group trips with intelligent itinerary generation, budget management, and real-time collaboration.

## 🚀 Live Demo

- **Frontend**: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/
- **API Docs**: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/docs
- **Health Check**: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health

## ✨ Key Features

### Core Functionality
- **AI Itinerary Generation**: Multi-provider LLM integration (OpenAI, Gemini, Anthropic) with cost optimization
- **Multi-Family Coordination**: Role-based access control with family-specific preferences and constraints
- **Real-Time Collaboration**: WebSocket-powered chat, live presence indicators, and instant notifications
- **Budget Management**: Transparent cost tracking, expense splitting, and financial reporting
- **Smart Recommendations**: Context-aware suggestions based on location, weather, and family preferences

### Technical Features
- **LLM Orchestration Service**: Production-ready AI service with circuit breaker pattern and automatic failover
- **Hybrid Database**: Azure SQL Database for relational data, Cosmos DB for flexible document storage
- **Enterprise Security**: Auth0 integration with zero-trust architecture and GDPR compliance
- **Performance Optimization**: Ultra-cost-optimized containers (0.25 CPU / 0.5Gi), code splitting, and lazy loading
- **Monitoring**: Application Insights with custom metrics and automated alerting

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, Alembic, Celery
- **Frontend**: React 18, TypeScript, Vite, Zustand, Tailwind CSS, Fluent UI
- **Database**: Azure SQL Database + Cosmos DB
- **AI**: Custom FastAPI orchestration service with multi-provider support
- **Infrastructure**: Azure Container Apps, Application Insights, Key Vault
- **Authentication**: Auth0 with role-based access control
- **Resource Optimization**: Ultra-low resource containers for maximum cost efficiency

### System Design
```
┌─────────────────┐   ┌─────────────────┐ ┌─────────────────┐
│ React Frontend  │   │ Auth0           │ │ GitHub Actions  │
│ (Container Apps)│◄─►│ (Authentication)│ │ (CI/CD)         │
└─────────┬───────┘   └─────────────────┘ └─────────────────┘
          │
          │ HTTPS/WebSocket
          ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Azure CDN       │   │ Container Apps  │   │ Application     │
│ + Load Balancer │◄─►│ (Backend API)   │◄─►│ Insights        │
└─────────┬───────┘   └─────────┬───────┘   └─────────────────┘
          │                     │
          │                     ▼
          │         ┌─────────────────┐ ┌─────────────────┐
          │         │ LLM Orchestration│ │ In-Memory Cache │
          │         │ Service         │ │ (Application)   │
          │         └─────────┬───────┘ └─────────────────┘
          │                   │
          │                   ▼
          │         ┌─────────────────┐ ┌─────────────────┐
          │         │ Multi-Provider  │ │ External APIs   │
          │         │ LLM APIs        │ │ (Travel, Maps)  │
          │         └─────────────────┘ └─────────────────┘
          │
          ▼
┌─────────────────┐ ┌─────────────────┐
│ Azure SQL DB    │ │ Cosmos DB       │
│ (Relational)    │ │ (Documents)     │
└─────────────────┘ └─────────────────┘
```

## 🚀 Quick Start

### Try the Live Demo
Visit the [live application](https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/) to explore all features without setup.

### Local Development

**Prerequisites**: Node.js 18+, Python 3.11+, Docker

#### Option 1: Docker Compose (Recommended)
```bash
git clone https://github.com/vedprakashmishra/pathfinder.git
cd pathfinder

# Setup environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Start all services
docker-compose up -d

# Access application
open http://localhost:3000  # Frontend
open http://localhost:8000/docs  # API
```

## 🏗️ Production Deployment

### Step 1: Infrastructure Setup

**Option A: GitHub Actions (Recommended)**
1. Fork this repository
2. Set up GitHub secrets (see below)
3. Go to Actions → "Deploy Infrastructure" → "Run workflow"
4. Wait for infrastructure deployment to complete

**Option B: Manual Deployment**
```bash
# Login to Azure
az login

# Deploy infrastructure
./scripts/deploy-single-rg.sh
```

### Step 2: Required GitHub Secrets

Set these secrets in your GitHub repository (Settings → Secrets → Actions):

```bash
# Azure Credentials (Service Principal)
AZURE_CREDENTIALS='{
  "clientId": "your-client-id",
  "clientSecret": "your-client-secret", 
  "subscriptionId": "your-subscription-id",
  "tenantId": "your-tenant-id"
}'

# Database Configuration
SQL_ADMIN_USERNAME=pathfinderadmin
SQL_ADMIN_PASSWORD=your-secure-password

# AI Integration (Optional)
OPENAI_API_KEY=your-openai-key
```

### Step 3: Application Deployment

Once infrastructure is deployed, the main CI/CD pipeline will automatically:
1. Build and test the application
2. Build Docker images 
3. Deploy to Azure Container Apps
4. Run health checks

### Infrastructure Architecture

**Single Resource Group Strategy**: All resources in `pathfinder-rg`
- **Cost Optimized**: $45-65/month (vs $110+ multi-environment)
- **Simplified Management**: Unified resource lifecycle
- **Scale-to-Zero**: Container apps scale down when idle

#### Option 2: Development Mode
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Essential Configuration
```env
# Backend (.env)
OPENAI_API_KEY=sk-your-key-here
AUTH0_DOMAIN=YOUR_DOMAIN.auth0.com
AUTH0_AUDIENCE=your-api-identifier
DATABASE_URL=sqlite:///./app.db

# Frontend (.env.local)
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=YOUR_DOMAIN.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
```

## 💻 Development

### Project Structure
```
pathfinder/
├── backend/           # FastAPI application
├── frontend/          # React TypeScript application
├── llm_orchestration/ # AI service layer
├── infrastructure/    # Azure Bicep templates
├── scripts/          # Deployment scripts
└── docs/             # Documentation
```

### API Documentation
- **Development**: http://localhost:8000/docs
- **Production**: [Live API Docs](https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/docs)

### Testing
```bash
# Backend
cd backend
pytest --cov=app

# Frontend
cd frontend
npm test
npm run test:e2e
```

### Code Quality
```bash
# Backend
black . && flake8 . && mypy .

# Frontend
npm run lint && npm run type-check
```

## 💰 Cost Optimization

This deployment implements **aggressive container resource optimization** and **pause/resume architecture** for maximum cost efficiency:

### 🔄 Pause/Resume Strategy (NEW)
- **Active**: $50-75/month (full functionality)
- **Paused**: $15-25/month (70% savings, data preserved)
- **Resume Time**: 5-10 minutes to full functionality
- **Use Cases**: Development breaks, demos, extended idle periods

```bash
# Pause environment (delete compute layer)
./scripts/pause-environment.sh

# Resume environment (restore compute layer)  
./scripts/resume-environment.sh

# Or use GitHub Actions workflow for management
```

### Resource Configuration
- **CPU**: 0.25 cores per container (75% reduction from default)
- **Memory**: 0.5 GiB per container (75% reduction from default)
- **Data Layer**: Persistent databases ($15-25/month, never deleted)
- **Compute Layer**: Ephemeral apps ($35-50/month, pausable)

### Architecture Benefits
- **Pause/Resume**: Delete compute layer when idle for 70% cost savings
- **Data Preservation**: All user data preserved during pause periods
- **Redis-free**: Eliminates external cache dependency and costs
- **In-memory caching**: Application-level caching for essential operations
- **Auto-scaling**: Container Apps can scale based on demand

## 🚀 Deployment

### Azure Production
Complete deployment guide available in [docs/](docs/). Key steps:

1. **Setup Azure Resources**: Use provided Bicep templates
2. **Configure Secrets**: Set up Key Vault with required credentials
3. **Deploy via GitHub Actions**: Push to main branch triggers deployment

### Environment Configuration
- **Development**: Local SQLite, basic Auth0, in-memory caching
- **Production**: Azure SQL Database, full Auth0 setup, Application Insights

## 📄 License

Licensed under [GNU Affero General Public License v3.0](LICENSE).

### Key Requirements
- **Network Service**: Must provide source code access to users of hosted services
- **Commercial Use**: Permitted under AGPL terms
- **Dual Licensing**: Available for proprietary use cases

See [docs/NOTICE](docs/NOTICE) for practical guidance and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for contribution terms.

## 🗺️ Roadmap

### ✅ Phase 1 - MVP (Complete)
Core infrastructure, AI integration, real-time features, production deployment

### ✅ Phase 2 - Enhanced UX (Complete - June 2025)
- ✅ Golden Path Onboarding with interactive trip type selection
- ✅ Sample trip generation with 6 detailed destination templates
- ✅ Interactive consensus engine demonstration
- ✅ Comprehensive analytics and A/B testing framework
- ✅ Mobile-responsive design with Tailwind CSS breakpoints
- ✅ Database migration system with onboarding tracking

### 🚧 Phase 3 - AI Integration Enhancement (Q3 2025)
- Pathfinder Assistant with @mention functionality
- Magic Polls for intelligent group decision-making
- Rich response cards with structured AI recommendations
- Advanced collaboration features and conflict resolution

### 📋 Phase 4 - Advanced PWA & Intelligence (Q4 2025)
- Mobile-optimized "Day Of" itinerary interface
- Post-trip Memory Lane with AI-generated summaries
- Offline capabilities and enhanced mobile experience
- Advanced AI features and enterprise-level multi-tenancy

## 📚 Documentation

- **Getting Started**: [docs/](docs/)
- **API Reference**: [Live API Docs](https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/docs)
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Deployment**: [docs/DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/vedprakash-m/pathfinder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vedprakash-m/pathfinder/discussions)
- **Documentation**: [docs/](docs/)

---

**Built for families who love to travel together** ❤️🚀 Production deployment ready - OpenAI key to be configured post-deployment

<!-- CI/CD Pipeline Trigger: June 10, 2025 - Fresh deployment with all fixes -->
