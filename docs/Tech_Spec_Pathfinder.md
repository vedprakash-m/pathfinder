# Pathfinder - Technical Specification Document

**Document Version:** 1.0
**Last Updated:** June 27, 2025

---

## Glossary of Key Terms

- **Atomic Family Unit:** The core principle that families, not individuals, join and participate in trips. All decisions and data are scoped to the family level.
- **Pathfinder Assistant:** The conversational AI, powered by a RAG architecture, that helps users plan trips.
- **Golden Path Onboarding:** The interactive, high-priority onboarding experience that generates a sample trip to demonstrate value immediately.
- **Magic Polls:** An AI-assisted polling feature that helps families make decisions by suggesting context-aware options.
- **Consensus Engine:** The underlying logic that facilitates group decision-making, including preference analysis and conflict resolution.

---

## Executive Summary

This Technical Specification defines Pathfinder's implementation architecture. It leverages a production-ready, cost-optimized two-layer Azure architecture to deliver all PRD requirements through modern technologies and proven patterns.

**Key Technical Achievements:**
- ✅ Microsoft Entra External ID migration completed.
- ✅ Two-layer cost-optimized Azure architecture (70% savings when idle).
- ✅ Enhanced local validation with 100% CI/CD parity.
- ✅ Test coverage at 84.2% with robust infrastructure.
- ✅ Production-ready CI/CD pipeline with comprehensive security.

---

## 1. System Architecture Overview

### 1.1 Current Two-Layer Azure Architecture

```
┌─────────────────────────────────────────┐
│        PERSISTENT DATA LAYER            │
│         (pathfinder-db-rg)              │
│  ┌─────────────────────────────────────┐│
│  │         Cosmos DB Account           ││
│  │           (SQL API)                 ││
│  │  ┌─────────────┐ ┌─────────────┐    ││
│  │  │ Structured  │ │  Document   │    ││
│  │  │    Data     │ │    Data     │    ││
│  │  │ -  Users     │ │ -  Itinerary │    ││
│  │  │ -  Families  │ │ -  Messages  │    ││
│  │  │ -  Trips     │ │ -  AI Data   │    ││
│  │  └─────────────┘ └─────────────┘    ││
│  └─────────────────────────────────────┘│
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Storage     │  │ Key Vault       │  │
│  │ Account     │  │ (Secrets)       │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────────┐                   │
│  │ Service Bus     │                   │
│  │ (Task Queue)    │                   │
│  └─────────────────┘                   │
│  Cost: $0-5/month when paused          │
│       Usage-based when active          │
└─────────────────────────────────────────┘
                    ⬆ Data Persistence ⬇
┌─────────────────────────────────────────┐
│       EPHEMERAL COMPUTE LAYER           │
│          (pathfinder-rg)                │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Container   │  │ Backend Service │  │
│  │ Apps Env    │  │ (FastAPI)       │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Frontend    │  │ Container       │  │
│  │ Service     │  │ Registry        │  │
│  └─────────────┘  └─────────────────┘  │
│  Cost: $35-50/month (Paused: $0)       │
└─────────────────────────────────────────┘
```

**Architecture Benefits:**
- Cost Optimization: 90%+ savings during idle periods (serverless database).
- Data Persistence: Critical data never lost during compute pauses.
- Scalability: Auto-scaling from 0-N instances based on demand.
- Global Distribution: Built-in multi-region replication with Cosmos DB.
- Unified Data Model: Single database for all data types reduces complexity.

---

### 1.2 Technology Stack

**Frontend Stack**
- React 18 (UI Framework)
- TypeScript (Type Safety)
- Vite (Build Tool & Dev Server)
- Tailwind CSS (Styling Framework)
- Fluent UI v9 (Microsoft Design System)
- MSAL Browser (Authentication - Entra External ID)
- Socket.IO Client (Real-time Communication)
- PWA Capabilities (Offline Support & Mobile Experience)

**Backend Stack**
- FastAPI (API Framework)
- Python 3.11 (Runtime)
- Pydantic v2 (Data Validation & Serialization)
- azure-cosmos (Cosmos DB SDK)
- Celery (Asynchronous Task Queue)
- Socket.IO (WebSocket Server)
- MSAL Python (Authentication Integration)
- AsyncIO (Asynchronous Processing)

---

## 2. Database Design & Implementation (Cosmos DB SQL API)

Pathfinder uses a unified Cosmos DB account (SQL API) in serverless mode for all persistent data, eliminating the need for traditional relational ORMs.

### 2.1 Unified Cosmos DB Data Model

All application data is stored in a single `entities` container.

```
// User Document Example
{
  "id": "user_123e4567...",
  "type": "user",
  "pk": "user_123e4567...",
  "email": "user@example.com",
  "name": "Jane Doe",
  "role": "FamilyAdmin",
  "preferences": {},
  "createdAt": "2024-01-01T12:00:00Z"
}

// Trip Document Example
{
  "id": "trip_789e4567...",
  "type": "trip",
  "pk": "trip_789e4567...",
  "name": "Summer Family Vacation",
  "destination": "Orlando, FL",
  "startDate": "2024-07-15",
  "endDate": "2024-07-22",
  "status": "planning",
  "budgetTotal": 2500,
  "creatorId": "user_123e4567...",
  "preferences": {},
  "createdAt": "2024-06-01T09:00:00Z"
}

// Magic Poll Document Example
{
  "id": "poll_abc123",
  "type": "magic_poll",
  "pk": "trip_789e4567-e89b-12d3-a456-426614174002",
  "tripId": "trip_789e4567-e89b-12d3-a456-426614174002",
  "question": "Where should we have dinner on our first night?",
  "options": [ { "optionId": "opt_01", "text": "Taverna del Capitano", "aiGenerated": true } ],
  "votes": [ { "userId": "user_123e4567...", "familyId": "family_456e4567...", "optionId": "opt_01" } ],
  "createdAt": "2024-12-27T08:30:00Z"
}

// Consensus Analysis Document Example
{
  "id": "consensus_def456",
  "type": "consensus_analysis",
  "pk": "trip_789e4567-e89b-12d3-a456-426614174002",
  "tripId": "trip_789e4567-e89b-12d3-a456-426614174002",
  "decisionType": "activity_selection",
  "status": "conflict_identified",
  "conflicts": [ { "type": "budget_mismatch", "details": "...", "involvedFamilies": [] } ],
  "suggestedCompromises": [ { "compromiseId": "comp_01", "text": "...", "relatedOptions": [] } ],
  "finalDecision": null,
  "createdAt": "2024-12-28T11:00:00Z"
}
```

### 2.2 Partition Key Strategy

- Synthetic partition key (`/pk`), concatenating entity_type and id (e.g., user_UUID, trip_UUID) for even data distribution and efficient reads.

### 2.3 Database Schema Evolution

- **Schema Versioning:** Documents include a `_schema_version` field.
- **Schema-on-Read:** Application code handles different schema versions and upgrades older documents on the fly.
- **Background Transformations:** For major changes, background tasks transform documents to the new schema.

---

## 3. API Design & Implementation

### 3.1 RESTful API Architecture (FastAPI)

The backend is a FastAPI application with modular routers for core entities and services.

```
from fastapi import FastAPI, APIRouter

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(trips_router, prefix="/trips", tags=["Trip Management"])
api_router.include_router(families_router, prefix="/families", tags=["Family Management"])
api_router.include_router(itineraries_router, prefix="/itineraries", tags=["AI Itineraries"])
api_router.include_router(websocket_router, prefix="/ws", tags=["Real-time Communication"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Services"])
```

### 3.2 Key API Endpoints

- `POST /api/v1/trips`: Create new trip
- `GET /api/v1/trips/{trip_id}`: Get trip details
- `POST /api/v1/trips/{trip_id}/families/{family_id}/invite`: Invite family to trip
- `POST /api/v1/ai/assistant/query`: Natural language trip assistance
- `POST /api/v1/ai/itinerary/generate`: Queue AI itinerary generation (async)
- `POST /api/v1/ai/polls/magic`: Create AI-generated poll options (async)

### 3.3 WebSocket Implementation

- Powered by Socket.IO WebSockets
- **WebSocketManager:** Manages active connections, trip- and family-specific rooms
- **broadcast_to_trip:** Sends structured events (chat, poll_update, itinerary_change) to trip participants

### 3.4 Comprehensive Error Handling & Logging

- **Centralized Error Handling:** ErrorHandlingService for all layers
- **Structured Logging:** JSON logs to Azure Application Insights
- **Monitoring:** Tracks API performance, AI usage, user activity
- **Recovery Strategies:** Circuit breakers, retries, graceful degradation

### 3.5 API Documentation & Contract Management

- FastAPI + OpenAPI: Auto-generated docs at `/docs` and `/redoc`
- Postman Collection: CI/CD generates and publishes from OpenAPI spec
- Contract Testing: Validates API responses against OpenAPI schema

---

## 4. AI Integration Architecture

### 4.1 LLM Orchestration Framework

- **LLMOrchestrationClient:** Manages multiple AI providers (OpenAI, Gemini, Claude) with fallback, cost tracking, budget validation, and dynamic model switching
- **LLMFallbackStrategy:** Failover to alternative LLMs or mock responses

### 4.2 AI Feature Implementation

- **Itinerary Service:** AI-powered itineraries considering family demographics, budget, weather, local events
- **Magic Poll Service:** Context-aware poll options asynchronously
- **Consensus Engine:** Conflict identification, compromise suggestions, resolution facilitation

### 4.3 AI Cost Management & Governance

- **AdvancedAIService:** Centralized handler for all AI ops with budget validation, dynamic model selection, usage tracking, and graceful degradation
- **AICostTracker:** Validates budgets, logs token usage, provides analytics

### 4.4 Conversational AI (Pathfinder Assistant)

- **Retrieval-Augmented Generation (RAG):** Context awareness by retrieving relevant data from a vector DB (Cosmos DB + Azure AI Search)
- **Prompt Engineering:** Context prepended to user prompts for LLM input
- **Prompt Chaining:** Complex queries via dependent prompts
- **Rich Response Cards:** LLM returns structured JSON mapped to frontend components

### 4.5 "Memory Lane" Feature Architecture

- **Data Aggregation:** Background task gathers trip stats
- **AI Superlatives:** LLM generates creative "trip superlatives"
- **Media Handling:** Photos stored in Azure Blob Storage; URLs aggregated for display

---

## 5. Infrastructure Implementation (Azure)

### 5.1 Bicep Infrastructure as Code

- **Persistent Data Layer:** Cosmos DB (serverless), Azure Storage, Key Vault
- **Compute Layer:** Azure Container Apps Environment, backend/frontend apps, Container Registry
- **Scaling:** minReplicas: 0 for cost savings, maxReplicas: 3 for scalability

### 5.2 Container Configuration

- **Backend Dockerfile:** `python:3.11-slim`, uvicorn, non-root user
- **Frontend Dockerfile:** `node:18-alpine` for build, `nginx:alpine` for runtime, Vite for optimized build

---

## 6. Development & Testing Infrastructure

### 6.1 CI/CD Pipeline (GitHub Actions)

- Automated jobs for backend/frontend tests, security scans (CodeQL), E2E tests
- Deployment to Azure on main branch push

### 6.2 Enhanced Local Validation

- `scripts/local-validation-enhanced.sh`: Simulates CI/CD pipeline locally

### 6.3 Testing Strategy

- **Backend:** Pytest with 84.2% coverage
- **E2E:** Playwright automation for workflow testing

---

## 7. Performance & Scalability

### 7.1 Performance Targets

- Page Load Time: <2 seconds (Current: 1.2s average)
- API Response: <100ms for most endpoints
- WebSocket Latency: <500ms
- Database Query: <200ms for complex queries

### 7.2 Operational Limits

- Family Size: Max 12 members per family
- Trip Capacity: Max 6 families per trip
- Chat History: 90-day retention with TTL policies

### 7.3 Cost Optimization

- Serverless Architecture: Cosmos DB serverless, Container Apps scaling to zero
- Scripts: `pause-environment.sh` and `resume-environment.sh` for 90%+ cost reduction during idle

### 7.4 Database Scalability Strategy

- Logical Partitioning: By document type and entity ID
- Cross-Region Replication (Planned Phase 2)
- Container Isolation (Planned Phase 3)
- Analytical Workloads (Planned Phase 4): Azure Synapse Link

### 7.5 CDN Strategy & Static Asset Optimization

- Azure CDN for static assets
- PWA Cache Strategy: Cache-first for app shell/static assets, Network-first for dynamic API

---

## 8. Monitoring & Observability

### 8.1 Health Check System

- Endpoints for `/health`, `/health/ready`, `/health/metrics`

### 8.2 Application Insights Integration

- Telemetry for API performance, AI usage, user activity, error alerting

---

## 9. Security Implementation Details

### 9.1 Microsoft Entra ID Authentication (Vedprakash Domain Standard)

**Identity Provider:** Microsoft Entra ID (`vedid.onmicrosoft.com`) - unified across all Vedprakash applications.

**Frontend Implementation:**
- **MSAL Integration:** `@azure/msal-react` and `@azure/msal-browser` for React authentication
- **SSO Configuration:** `sessionStorage` cache location and `storeAuthStateInCookie: true` for cross-app SSO
- **Standard User Object:** Implements VedUser interface with permissions and vedProfile structure
- **Token Management:** Automatic token refresh with silent acquisition and interactive fallback

**Backend Implementation:**
- **JWT Validation:** Production-ready token validation with JWKS signature verification
- **Security Standards:** Validates audience, issuer, and expiration per Vedprakash requirements
- **User Extraction:** Standardized user object extraction from token claims
- **Error Handling:** Comprehensive error responses with standard codes (AUTH_TOKEN_MISSING, AUTH_TOKEN_INVALID, AUTH_PERMISSION_DENIED)

**Security Features:**
- **JWKS Caching:** 1-hour TTL caching to prevent rate limiting and improve performance
- **Security Headers:** Complete CSP, HSTS, X-Frame-Options, and Permissions-Policy headers
- **Authentication Monitoring:** Comprehensive logging of auth events, failures, and performance metrics
- **Fallback Mechanisms:** Circuit breaker pattern and graceful degradation for service outages

### 9.2 Data Protection

- GDPR Compliance: Data export, deletion, consent management
- COPPA Compliance: Parental consent, limited minor data
- Encryption: TLS 1.3 in transit, AES-256 at rest

---

## 10. Deployment & Operations

### 10.1 Deployment Strategy

- Workflow: `deploy-data-layer.sh`, build/push images, deploy compute layer, validate
- Blue-green deployment with health checks

### 10.2 Environment Management

- Docker Compose for local dev/testing
- Bicep for Azure production

---

## 11. Compliance & Legal Implementation

### 11.1 GDPR Compliance

- Services for data subject requests, consent management, retention

### 11.2 COPPA Compliance

- Parental consent, limiting minor data, deletion

---

## 12. Future Extensibility

### 12.1 Plugin Architecture Framework

- PluginManager for new functionality plugins (AIProviderPlugin, NotificationPlugin)

### 12.2 API Versioning Strategy

- Current `/api/v1/`, strategy for future versions with backward compatibility

---

## 13. Risk Mitigation & Contingency

### 13.1 Technical Risk Mitigation

- AI Service Downtime: LLM orchestration with multi-provider fallbacks
- Database Failure: Cosmos DB multi-region backup, point-in-time restore
- Performance Degradation: Auto-scaling, caching, CDN
- Security Vulnerabilities: Automated scanning, CI/CD security gates

### 13.2 Disaster Recovery & Business Continuity

- RTO Target: 4 hours
- RPO Target: 1 hour
- Cosmos DB Backups: 30 days, geo-redundant, auto failover
- Application Backups: Key Vault, Bicep templates, container images
- DR Testing: Quarterly simulation

### 13.3 Release Management & Feature Toggles

- Progressive Rollout: Gradual rollout, monitoring, auto-rollback
- Feature Flag Service: Controls by percentage, user groups, dependencies
- A/B Testing Framework: Experiments, variants, success metrics

---

## Conclusion

This Technical Specification provides a comprehensive guide for Pathfinder's implementation, leveraging an optimized two-layer Azure architecture with a unified Cosmos DB. It ensures all PRD requirements are met with a focus on cost-efficiency, security, and scalability.

**Immediate Next Steps:**
- Complete AI integration for Phase 1 features (Assistant, Itinerary Generation)
- Deploy Golden Path Onboarding to production
- Validate performance and user experience
- Begin implementation of Phase 2 collaboration features (Magic Polls)
