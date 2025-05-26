# Pathfinder - AI-Powered Group Trip Planner

[![Build Status](https://github.com/vedprakash-m/pathfinder/workflows/CI/badge.svg)](https://github.com/vedprakash-m/pathfinder/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready web application for multi-family road trip coordination with AI-driven itinerary generation, real-time collaboration, and comprehensive trip management features.

## Features

### Phase 1 (Current)
- **Trip Creation & Management**: Create and manage multi-family trips with family group coordination
- **AI-Powered Itinerary Generation**: Intelligent itinerary creation using OpenAI models with cost optimization
- **Real-time Collaboration**: Live updates and communication through WebSocket connections
- **Family Management**: Organize families, assign coordinators, and manage participants
- **Preferences Collection**: Capture detailed family preferences for personalized experiences
- **Authentication & Security**: Auth0 integration with role-based access control

### Coming Soon (Phase 2)
- Real-time location tracking and check-ins
- Advanced budget management and expense tracking
- Emergency protocols and safety features
- Enhanced mobile experience

## Architecture

### Technology Stack
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, Alembic
- **Frontend**: React 18, TypeScript, Fluent UI, Zustand
- **Database**: Azure SQL Database + Cosmos DB (hybrid strategy)
- **Cache**: Redis with multi-layer caching
- **AI**: OpenAI GPT-4o with cost-optimized fallback strategy
- **Infrastructure**: Azure Container Apps, Application Insights
- **Authentication**: Auth0 with zero-trust security model

### System Design
- **Microservices Architecture**: Modular backend services with clear separation of concerns
- **Hybrid Database Strategy**: SQL for structured data, Cosmos DB for flexible trip data
- **Multi-layer Caching**: Application, database, and CDN caching for optimal performance
- **Real-time Communication**: WebSocket-based live updates and collaboration

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- Azure CLI (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/vedprakash-m/pathfinder.git
   cd pathfinder
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Setup environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run database migrations
   alembic upgrade head
   
   # Start the backend server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   
   # Setup environment variables
   cp .env.example .env.local
   # Edit .env.local with your configuration
   
   # Start the development server
   npm run dev
   ```

4. **Using Docker Compose (Recommended)**
   ```bash
   # Copy environment files
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

### Environment Configuration

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

## Development

### Project Structure
```
pathfinder/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route definitions
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application entry point
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services and utilities
│   │   ├── store/          # Zustand state management
│   │   └── types/          # TypeScript type definitions
├── infrastructure/         # Infrastructure as Code
│   ├── bicep/             # Azure Bicep templates
│   └── terraform/         # Terraform configurations (alternative)
├── shared/                # Shared types and utilities
└── docs/                  # Documentation
```

### API Documentation
- **Development**: http://localhost:8000/docs (Swagger UI)
- **Alternative**: http://localhost:8000/redoc (ReDoc)

### Database Management
```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Azure Deployment
1. **Setup Azure Resources**
   ```bash
   cd infrastructure/bicep
   az deployment group create \
     --resource-group pathfinder-rg \
     --template-file main.bicep \
     --parameters @parameters.json
   ```

2. **Deploy Application**
   ```bash
   # Build and push containers
   docker build -t pathfinder-backend ./backend
   docker build -t pathfinder-frontend ./frontend
   
   # Deploy using GitHub Actions (recommended)
   git push origin main
   ```

### Environment Variables for Production
See `infrastructure/bicep/main.bicep` for complete Azure configuration including:
- Azure SQL Database
- Cosmos DB
- Azure Container Apps
- Application Insights
- Key Vault for secrets

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

## Monitoring & Observability

### Application Insights
- **Performance Monitoring**: Response times, throughput, error rates
- **Cost Tracking**: AI model usage, database operations
- **User Analytics**: Feature adoption, usage patterns

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: ERROR, WARN, INFO, DEBUG
- **Retention**: 30 days in development, 90 days in production

## Security

### Zero-Trust Architecture
- **Authentication**: Auth0 with multi-factor authentication
- **Authorization**: Role-based access control (RBAC)
- **API Security**: JWT tokens, rate limiting, input validation
- **Infrastructure**: Azure Key Vault for secrets, HTTPS everywhere

### Data Protection
- **Encryption**: At rest and in transit
- **GDPR Compliance**: Data anonymization and deletion capabilities
- **Audit Logging**: All data access and modifications tracked

## Performance

### Optimization Strategies
- **Caching**: Multi-layer caching (Redis, CDN, application)
- **Database**: Query optimization, indexing, connection pooling
- **AI Models**: Cost-optimized model selection with fallback
- **Frontend**: Code splitting, lazy loading, memoization

### Scalability
- **Horizontal Scaling**: Container Apps auto-scaling
- **Database Scaling**: Read replicas, sharding strategies
- **CDN**: Global content distribution

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