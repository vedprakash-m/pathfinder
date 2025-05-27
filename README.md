# Pathfinder - AI-Powered Group Trip Planner

[![Build Status](https://github.com/vedprakash-m/pathfinder/workflows/Enhanced%20Production%20Pipeline/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)](https://codecov.io/gh/vedprakash-m/pathfinder)
[![Phase 1](https://img.shields.io/badge/Phase%201-80%25%20Complete-yellow.svg)](#phase-1-completion-status)

A production-ready web application for multi-family road trip coordination with AI-driven itinerary generation, real-time collaboration, and comprehensive trip management features.

> **Project Status**: Phase 1 is ~80% complete with strong architectural foundation. Ready for production deployment with remaining service integrations.

## 🎯 Phase 1 Completion Status

### ✅ **Completed Components (90-95%)**
- **🏗️ Backend Infrastructure**: Comprehensive FastAPI implementation
  - Complete database models (User, Family, Trip, Itinerary, Notification, Reservation)
  - API endpoints for all core functionality
  - Service layer with AI, email, notification, and file services
  - Background task system with Celery integration
  - Comprehensive test suite with 80%+ coverage

- **🔐 Authentication & Security**: Zero-trust security model
  - Auth0 integration with role-based access control
  - Security middleware and audit logging
  - CSRF protection and input validation

- **🏭 Infrastructure as Code**: Production-ready Azure deployment
  - Azure Bicep templates for Container Apps, Cosmos DB, SQL Database
  - CI/CD pipeline with GitHub Actions
  - Multi-environment support and security scanning

### 🚧 **In Progress (70-80%)**
- **⚛️ Frontend Application**: React TypeScript with modern architecture
  - Component library and routing system
  - Auth0 integration and state management
  - API services and real-time features
  - *Issue*: TypeScript compilation errors need resolution

- **📊 Monitoring & Observability**: Application Insights integration
  - Telemetry collection and custom metrics
  - Cost monitoring and budget alerts
  - Performance tracking and alerting

### 🔧 **Remaining Tasks (Priority Order)**
1. **🚨 Critical**: Fix frontend build issues and deploy infrastructure
2. **📧 High**: Complete email service integration and PDF generation
3. **🗺️ High**: Finalize Google Maps API integration
4. **💬 Medium**: Enhance WebSocket real-time features
5. **🧪 Medium**: Complete end-to-end testing and performance validation

## ✨ Core Features

### **Current Capabilities**
- **Trip Management**: Create, manage, and coordinate multi-family trips
- **AI Itinerary Generation**: Cost-optimized OpenAI integration with fallback strategies
- **Family Coordination**: Invite families, manage participants, collect preferences
- **Real-time Updates**: WebSocket-based live collaboration
- **Notification System**: Comprehensive alert and messaging system
- **Export Capabilities**: PDF generation for trip reports and itineraries
- **Security**: Enterprise-grade authentication and data protection

### **Coming in Phase 2**
- Real-time location tracking and check-ins
- Advanced budget management and expense splitting
- Emergency protocols and safety features
- Enhanced mobile experience with React Native

## 🏗️ Architecture

### **Technology Stack**
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, Alembic, Celery
- **Frontend**: React 18, TypeScript, Vite, Zustand, Tailwind CSS
- **Database**: Hybrid strategy - Azure SQL Database + Cosmos DB
- **Cache**: Redis with multi-layer caching strategy
- **AI**: OpenAI GPT-4o with cost optimization and fallback to GPT-4o-mini
- **Infrastructure**: Azure Container Apps, Application Insights, Key Vault
- **Authentication**: Auth0 with zero-trust security model
- **Real-time**: WebSocket-based live updates and collaboration

### **System Design Principles**
- **Hybrid Database Strategy**: SQL for relational data, Cosmos DB for flexible document storage
- **Cost-Optimized AI**: Smart model selection with caching and budget controls
- **Zero-Trust Security**: Comprehensive authentication, authorization, and audit logging
- **Microservices Architecture**: Modular backend services with clear separation of concerns
- **Performance-First**: Multi-layer caching, code splitting, and lazy loading

### **Infrastructure Overview**
```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ React Frontend  │ │ Auth0           │ │ GitHub Actions  │
│ (Static Web App)│◄─►│ (Authentication)│ │ (CI/CD)         │
└─────────┬───────┘ └─────────────────┘ └─────────────────┘
          │
          │ HTTPS/WebSocket
          ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Azure CDN       │ │ Container Apps  │ │ Application     │
│ + Load Balancer │◄─►│ (FastAPI)       │◄─►│ Insights        │
└─────────┬───────┘ └─────────┬───────┘ └─────────────────┘
          │                   │
          │                   ▼
          │         ┌─────────────────┐ ┌─────────────────┐
          │         │ Redis Cache     │ │ Service Bus     │
          │         │ (Multi-layer)   │ │ (Background)    │
          │         └─────────────────┘ └─────────────────┘
          │
          ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Azure SQL DB    │ │ Cosmos DB       │ │ External APIs   │
│ (Relational)    │ │ (Documents)     │ │ (OpenAI, Maps)  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🚀 Quick Start

### **Prerequisites**
- Node.js 18+ and npm
- Python 3.11+ 
- Docker and Docker Compose
- Azure CLI (for production deployment)
- Git

### **Local Development Setup**

#### **Option 1: Docker Compose (Recommended)**
```bash
# Clone the repository
git clone https://github.com/vedprakash-m/pathfinder.git
cd pathfinder

# Setup environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit environment files with your configuration
# Required: AUTH0_DOMAIN, AUTH0_CLIENT_ID, OPENAI_API_KEY

# Start all services (backend, frontend, redis, postgres)
docker-compose up -d

# View logs
docker-compose logs -f

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### **Option 2: Manual Setup**
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations and start server
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Frontend setup (in new terminal)
cd frontend
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

### **Essential Environment Variables**

#### **Backend (.env)**
```env
# Database (Local development)
DATABASE_URL=postgresql://postgres:password@localhost:5432/pathfinder
COSMOS_DB_URL=your_cosmos_db_url  # Optional for local dev
REDIS_URL=redis://localhost:6379

# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your-api-identifier
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Application Settings
SECRET_KEY=your-secret-key-min-32-chars
ENVIRONMENT=development
AI_DAILY_BUDGET_LIMIT=10.00
```

#### **Frontend (.env.local)**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-frontend-client-id
VITE_AUTH0_AUDIENCE=your-api-identifier
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
```

> **💡 Quick Setup Tip**: For fastest local development, use the Docker Compose option which handles all service dependencies automatically.

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pathfinder
COSMOS_DB_URL=your_cosmos_db_url
COSMOS_DB_KEY=your_cosmos_db_key

# Redis
REDIS_URL=redis://localhost:6379

# Auth0
AUTH0_DOMAIN=your_domain.auth0.com
AUTH0_AUDIENCE=your_api_identifier
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=your_domain.auth0.com
VITE_AUTH0_CLIENT_ID=your_frontend_client_id
VITE_AUTH0_AUDIENCE=your_api_identifier
```

## 💻 Development Guide

### **Project Structure**
```
pathfinder/
├── 📁 backend/                 # FastAPI backend application
│   ├── 📁 app/
│   │   ├── 📁 api/            # API route definitions & endpoints
│   │   ├── 📁 core/           # Configuration, security, database
│   │   ├── 📁 models/         # SQLAlchemy database models
│   │   ├── 📁 services/       # Business logic services
│   │   ├── 📁 tasks/          # Background task definitions
│   │   └── 📄 main.py         # FastAPI application entry point
│   ├── 📁 alembic/            # Database migrations
│   ├── 📁 tests/              # Comprehensive test suite
│   └── 📄 requirements.txt    # Python dependencies
├── 📁 frontend/               # React frontend application  
│   ├── 📁 src/
│   │   ├── 📁 components/     # Reusable React components
│   │   ├── 📁 pages/          # Page-level components
│   │   ├── 📁 services/       # API services and utilities
│   │   ├── 📁 store/          # Zustand state management
│   │   ├── 📁 hooks/          # Custom React hooks
│   │   └── 📁 types/          # TypeScript type definitions
│   └── 📄 package.json       # Node.js dependencies
├── 📁 infrastructure/         # Infrastructure as Code
│   ├── 📁 bicep/             # Azure Bicep templates
│   └── 📁 scripts/           # Deployment scripts
├── 📁 shared/                # Shared types and utilities
├── 📁 docs/                  # Documentation
└── 📄 docker-compose.yml     # Local development setup
```

### **API Documentation**
- **Development**: http://localhost:8000/docs (Interactive Swagger UI)
- **Alternative**: http://localhost:8000/redoc (ReDoc format)
- **Health Check**: http://localhost:8000/health

### **Database Management**
```bash
# Create a new migration after model changes
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (development only)
alembic downgrade base && alembic upgrade head
```

### **Testing Strategy**
```bash
# Backend testing (80%+ coverage required)
cd backend
pytest                          # Run all tests
pytest --cov=app               # Run with coverage
pytest tests/test_trips.py     # Run specific test file
pytest -v -s                   # Verbose output with print statements

# Frontend testing
cd frontend
npm test                       # Run unit tests
npm run test:coverage          # Run with coverage
npm run test:e2e              # Run E2E tests
npm run test:e2e:headless     # Run E2E tests headless

# Integration testing
cd backend
pytest tests/test_integration.py  # Full integration tests
```

### **Code Quality & Standards**
```bash
# Backend linting and formatting
cd backend
black .                        # Format code
flake8 .                      # Lint code
mypy .                        # Type checking

# Frontend linting and formatting
cd frontend
npm run lint                   # ESLint
npm run lint:fix              # Auto-fix linting issues
npm run type-check            # TypeScript checking
npm run format                # Prettier formatting
```

### **Development Workflow**
1. **Feature Development**:
   - Create feature branch: `git checkout -b feature/amazing-feature`
   - Implement backend API endpoints and services
   - Add comprehensive tests (unit, integration, E2E)
   - Implement frontend components and pages
   - Update documentation

2. **Code Quality Checks**:
   - Run linting and formatting tools
   - Ensure test coverage meets requirements (80%+ backend, 70%+ frontend)
   - Manual testing in local environment

3. **Commit and Push**:
   - Use conventional commit messages: `feat: add trip sharing functionality`
   - Push to feature branch: `git push origin feature/amazing-feature`
   - Create Pull Request with description

4. **CI/CD Pipeline**:
   - Automated testing and security scanning
   - Code coverage validation
   - Build verification
   - Deployment to staging environment (on main branch)

## 🚀 Deployment

### **Azure Production Deployment**

#### **Prerequisites**
- Azure CLI installed and logged in
- Azure subscription with appropriate permissions
- GitHub repository with secrets configured

#### **1. Setup Azure Resources**
```bash
# Login to Azure
az login

# Create resource group
az group create --name pathfinder-rg --location eastus

# Deploy infrastructure using Bicep
cd infrastructure/bicep
az deployment group create \
  --resource-group pathfinder-rg \
  --template-file main.bicep \
  --parameters appName=pathfinder environment=prod \
               sqlAdminLogin=your_admin \
               sqlAdminPassword=your_secure_password \
               openAIApiKey=your_openai_key
```

#### **2. Configure GitHub Secrets**
Set up the following secrets in your GitHub repository:
```bash
AZURE_CREDENTIALS          # Service principal JSON
AZURE_SUBSCRIPTION_ID      # Azure subscription ID
AZURE_RG                   # Resource group name
SQL_ADMIN_LOGIN           # Database admin username
SQL_ADMIN_PASSWORD        # Database admin password
```

#### **3. Deploy via GitHub Actions**
```bash
# Push to main branch triggers deployment
git push origin main

# Monitor deployment in GitHub Actions
# https://github.com/your-username/pathfinder/actions
```

### **Local Production Testing**
```bash
# Build production images
docker build -t pathfinder-backend:prod ./backend
docker build -t pathfinder-frontend:prod ./frontend

# Run production-like environment
docker-compose -f docker-compose.prod.yml up -d

# Test production endpoints
curl https://localhost:8000/health
```

### **Environment-Specific Configuration**

#### **Development**
- Local SQLite database
- Basic Auth0 configuration
- Local Redis instance
- OpenAI with low rate limits

#### **Staging**
- Azure SQL Database (Basic tier)
- Full Auth0 configuration
- Azure Redis Cache (Basic)
- OpenAI with moderate limits

#### **Production**
- Azure SQL Database (Standard tier)
- Production Auth0 tenant
- Azure Redis Cache (Standard)
- OpenAI with full budget allocation
- Azure Cosmos DB for document storage
- Application Insights monitoring
- Azure Key Vault for secrets

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- **Backend**: Follow PEP 8, use type hints, maintain 90%+ test coverage
- **Frontend**: Use TypeScript strict mode, follow React best practices
- **Commits**: Use conventional commit messages
- **Documentation**: Update docs for any API or feature changes

## 📊 Monitoring & Performance

### **Application Insights Dashboard**
- **Performance Metrics**: Response times, throughput, error rates
- **Cost Tracking**: AI token usage, database operations, infrastructure costs
- **User Analytics**: Feature adoption, user journeys, conversion rates
- **Custom Metrics**: Trip completion rates, AI generation success rates

### **Key Performance Indicators (KPIs)**
- **Response Time**: P95 < 2 seconds for API endpoints
- **System Uptime**: > 99.9% availability target
- **Error Rate**: < 1% error rate for critical paths
- **AI Generation**: < 30 seconds for itinerary generation
- **Cost Efficiency**: < $5/month per active user

### **Logging & Observability**
```python
# Structured logging with correlation IDs
logger.info(
    "Trip created successfully",
    trip_id=trip.id,
    user_id=current_user.id,
    family_count=len(families),
    cost_estimate=ai_cost
)
```

### **Cost Monitoring**
- **Real-time Tracking**: Azure costs and OpenAI token usage
- **Budget Alerts**: Automated notifications when approaching limits
- **Optimization Reports**: Weekly usage analysis and recommendations
- **Smart Model Selection**: Automatic fallback to cost-effective AI models

## 🔒 Security & Compliance

### **Zero-Trust Security Architecture**
- **Authentication**: Auth0 with MFA and social login support
- **Authorization**: Role-based access control (RBAC) with granular permissions
- **API Security**: JWT tokens, rate limiting, input validation, CORS
- **Infrastructure**: Azure Key Vault, managed identities, network security groups

### **Data Protection**
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **GDPR Compliance**: Data anonymization, deletion, and export capabilities
- **Audit Logging**: All data access and modifications tracked with correlation IDs
- **Privacy**: PII encryption, secure file handling, minimal data collection

### **Security Monitoring**
- **Threat Detection**: Automated security scanning in CI/CD pipeline
- **Vulnerability Management**: Trivy security scanning, dependency updates
- **Access Monitoring**: Failed login attempts, permission escalation alerts
- **Incident Response**: Automated security incident workflows

## ⚡ Performance Optimization

### **Backend Optimizations**
- **Database**: Query optimization, connection pooling, read replicas
- **Caching**: Multi-layer caching (Redis, application-level, CDN)
- **AI Models**: Cost-optimized selection with quality fallbacks
- **Background Jobs**: Async processing with Celery for heavy operations

### **Frontend Optimizations**
- **Code Splitting**: Route-based lazy loading reduces initial bundle size
- **Caching**: API response caching with invalidation strategies
- **Performance Monitoring**: Core Web Vitals tracking and optimization
- **Progressive Loading**: Skeleton screens and progressive enhancement

### **Infrastructure Scaling**
- **Auto-scaling**: Container Apps with HTTP-based scaling rules
- **Load Balancing**: Azure Application Gateway with health checks
- **Geographic Distribution**: CDN for global content delivery
- **Database Scaling**: Horizontal scaling strategies for high load

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/vedprakash-m/pathfinder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vedprakash-m/pathfinder/discussions)

## Roadmap

### Phase 1 ✅ (Current)
- Trip creation and family management
- AI-powered itinerary generation
- Real-time collaboration
- Basic authentication and security

### Phase 2 🚧 (Q2 2024)
- Real-time location tracking
- Advanced budget management
- Emergency protocols
- Enhanced mobile experience

### Phase 3 📋 (Q3 2024)
- Advanced AI features
- Third-party integrations
- Enterprise features
- Global expansion

---

**Made with ❤️ for families who love to travel together**