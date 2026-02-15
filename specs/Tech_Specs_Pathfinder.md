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
- ✅ Microsoft Entra ID authentication with JWKS validation.
- ✅ Two-layer cost-optimized Azure serverless architecture (90%+ savings when idle).
- ✅ Azure Functions v2 (Python) with Blueprint-based modular HTTP/Queue/Timer triggers.
- ✅ Unified Cosmos DB single-container design with synthetic partition keys.
- ✅ CI/CD pipeline via GitHub Actions with change-detection gating.

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
│  ┌─────────────────┐  ┌─────────────┐  │
│  │ Storage Queues  │  │ SignalR      │  │
│  │ (Task Queue)    │  │ (Real-time)  │  │
│  └─────────────────┘  └─────────────┘  │
│  Cost: $0-5/month when paused          │
│       Usage-based when active          │
└─────────────────────────────────────────┘
                    ⬆ Data Persistence ⬇
┌─────────────────────────────────────────┐
│       EPHEMERAL COMPUTE LAYER           │
│          (pathfinder-rg)                │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Azure       │  │ Backend API     │  │
│  │ Functions   │  │ (Python 3.13)   │  │
│  │ (Flex Plan) │  │                 │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────────────────────────┐    │
│  │ Static Web Apps (Frontend)     │    │
│  └─────────────────────────────────┘    │
│  Cost: Pay-per-execution (idle: ~$0)   │
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
- MSAL Browser (Authentication - Entra ID)
- Azure SignalR Client (Real-time Communication)
- PWA Capabilities (Offline Support & Mobile Experience)

**Backend Stack**
- Azure Functions v2 Programming Model (Serverless API Framework)
- Python 3.13 (Runtime)
- Pydantic v2 (Data Validation & Serialization)
- azure-cosmos (Cosmos DB SDK — async client)
- Azure Storage Queues (Asynchronous Task Processing)
- Azure SignalR Service (Real-time Messaging)
- PyJWT + JWKS (Microsoft Entra ID Token Validation)
- AsyncIO (Asynchronous Processing)

---

## 1.3 CI/CD & Quality Assurance Enhancement (June 30, 2025)

### 1.3.1 Problem Solved

**Root Cause Analysis**: CI/CD pipeline failure due to missing import validation in local development workflow.

**Original Issues**:
- Import errors (`User` class missing in `app/api/feedback.py`)
- Incomplete local validation coverage (AI-focused only)
- No systematic import checking
- Binary compatibility issues (pandas/numpy) in local environments

### 1.3.2 Enhanced Validation Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 VALIDATION PYRAMID                       │
├─────────────────────────────────────────────────────────┤
│  Level 1: Critical Import Validation                    │
│  • Systematic import checking                           │
│  • Binary compatibility detection                       │
│  • CI/CD parity verification                           │
├─────────────────────────────────────────────────────────┤
│  Level 2: Comprehensive Testing                         │
│  • Test collection validation                           │
│  • Unit & integration tests                             │
│  • Coverage threshold enforcement                       │
├─────────────────────────────────────────────────────────┤
│  Level 3: Architecture Compliance                       │
│  • Import-linter contract validation                    │
│  • Type checking (mypy)                                 │
│  • Code quality (flake8, black, ruff)                  │
├─────────────────────────────────────────────────────────┤
│  Level 4: Environment Readiness                         │
│  • Dependency consistency                               │
│  • Security vulnerability scanning                      │
│  • Environment variable validation                      │
└─────────────────────────────────────────────────────────┘
```

### 1.3.3 Validation Scripts

**1. `local_validation.py` (Quick Validation)**
- **Purpose**: Daily development validation
- **Runtime**: 2-5 minutes
- **Scope**: Critical imports, basic tests, AI functionality
- **Usage**: Before every commit

**2. `comprehensive_e2e_validation.py` (Full Validation)**
- **Purpose**: Complete CI/CD simulation
- **Runtime**: 10-20 minutes
- **Scope**: All imports, architecture, quality, comprehensive testing
- **Usage**: Before major pushes, releases

**3. `fix_environment.py` (Environment Repair)**
- **Purpose**: Binary compatibility issue resolution
- **Scope**: pandas/numpy version conflicts, dependency fixes
- **Usage**: When import errors occur

### 1.3.4 CI/CD Debug Workflow

**Workflow**: `.github/workflows/debug-ci-cd.yml`
- **Environment Analysis**: System info, secrets validation, dependency analysis
- **Import Validation**: Critical module testing, comprehensive scanning
- **Test Debugging**: Collection analysis, individual module checks
- **Architecture Validation**: Contract enforcement, quality checks

### 1.3.5 Import Management Standards

**Critical Import Patterns**:
```python
# API modules - always import User for authentication
from ..models.user import User

# Repository dependencies - explicit imports
from app.core.repositories.trip_cosmos_repository import TripCosmosRepository

# Service layer - follow dependency injection patterns
from app.services.cosmos.preference_service import PreferenceDocumentService
```

**Architecture Enforcement**:
- Import-linter contracts prevent layer violations
- Automated validation in CI/CD pipeline
- Local validation ensures compliance before commits

### 1.3.6 Reliability Metrics

**Before Enhancement (June 29, 2025)**:
- Import error detection: Manual only
- Local validation coverage: ~30% (AI-focused)
- CI/CD failure prevention: Reactive

**After Enhancement (June 30, 2025)**:
- Import error detection: 100% automated
- Local validation coverage: 100% CI/CD parity
- CI/CD failure prevention: Proactive with comprehensive validation

**Quality Gates**:
- ✅ 100% critical import validation
- ✅ Comprehensive test collection validation
- ✅ Architecture contract enforcement
- ✅ Binary compatibility monitoring
- ✅ Environment readiness verification

### 1.3.7 Development Workflow Integration

**Pre-Commit Checklist**:
1. Run `python local_validation.py`
2. Verify all imports are explicit
3. Ensure tests pass locally
4. Check architecture compliance

**CI/CD Pipeline Stages**:
1. **Quality Checks**: Import validation, testing, architecture
2. **Security Scanning**: Dependency vulnerabilities, secrets scanning
3. **Build & Deploy**: Container builds, Azure deployment
4. **Performance Testing**: Load testing, monitoring

This enhancement ensures zero CI/CD failures due to preventable issues like import errors, providing robust development workflow with comprehensive validation at every stage.

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

### 3.1 RESTful API Architecture (Azure Functions Blueprints)

The backend uses Azure Functions v2 programming model with Blueprints for modular route registration.

```python
# function_app.py — entry point
import azure.functions as func
from functions.http.auth import bp as auth_bp
from functions.http.trips import bp as trips_bp
from functions.http.families import bp as families_bp
from functions.http.itineraries import bp as itineraries_bp
from functions.http.collaboration import bp as collaboration_bp
from functions.http.assistant import bp as assistant_bp
from functions.http.signalr import bp as signalr_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_blueprint(auth_bp)
app.register_blueprint(trips_bp)
# ... all blueprints registered
```

### 3.2 Key API Endpoints

- `POST /api/v1/trips`: Create new trip
- `GET /api/v1/trips/{trip_id}`: Get trip details
- `POST /api/v1/trips/{trip_id}/families/{family_id}/invite`: Invite family to trip
- `POST /api/v1/ai/assistant/query`: Natural language trip assistance
- `POST /api/v1/ai/itinerary/generate`: Queue AI itinerary generation (async)
- `POST /api/v1/ai/polls/magic`: Create AI-generated poll options (async)

### 3.3 Real-time Communication (Azure SignalR Service)

- Powered by Azure SignalR Service (serverless mode)
- **RealtimeService:** Manages JWT-based negotiate endpoint, group membership, and message delivery
- **SignalR Groups:** Users join trip-scoped groups for real-time events (poll updates, itinerary changes, chat)
- **Server-to-client:** REST API calls from Azure Functions to SignalR Service for push messaging

### 3.4 Comprehensive Error Handling & Logging

- **Centralized Error Handling:** ErrorHandlingService for all layers
- **Structured Logging:** JSON logs to Azure Application Insights
- **Monitoring:** Tracks API performance, AI usage, user activity
- **Recovery Strategies:** Circuit breakers, retries, graceful degradation

### 3.5 API Documentation & Contract Management

- OpenAPI spec generated manually / from Pydantic schemas
- Health, readiness, and liveness endpoints at `/api/health`, `/api/health/ready`, `/api/health/live`

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

- **Persistent Data Layer:** Cosmos DB (serverless), Azure Storage, Key Vault, Azure SignalR Service (Free tier)
- **Compute Layer:** Azure Functions (Flex Consumption plan), Azure Static Web Apps (Free tier)
- **Scaling:** Azure Functions scale to zero when idle; auto-scale on demand

### 5.2 Deployment Configuration

- **Backend:** Azure Functions v2 Python — deployed via `Azure/functions-action` with Oryx build
- **Frontend:** Vite production build deployed to Azure Static Web Apps via `Azure/static-web-apps-deploy`
- **No containers required:** Both services use managed Azure platform runtimes

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

### 12.3 Contextual Data Enrichment (Phase 5+ Consideration)

**Status:** Deferred pending Phase 1-4 completion and user validation

If user feedback validates the need for contextual enrichment, a minimal implementation would follow these principles:

**Architecture Pattern:**
```python
class ContextEnrichmentService:
    """
    Lightweight service for read-only contextual data.

    Design Constraints:
    - Read-only queries only (no transactional features)
    - Aggressive caching (24hr+ TTL)
    - Graceful degradation (never blocks core features)
    - Cost-capped ($100/month maximum)
    - Maintains serverless cost optimization
    """

    async def get_weather_context(
        self, location: str, dates: List[date]
    ) -> Optional[WeatherContext]:
        """Get weather forecast to enrich itinerary suggestions."""
        try:
            # Check cache first (24hr TTL)
            cached = await self.cache.get(f"weather:{location}")
            if cached:
                return cached

            # Query external API (OpenWeatherMap free tier)
            result = await self.weather_api.query(location, dates)
            await self.cache.set(f"weather:{location}", result, ttl=86400)
            return result
        except Exception as e:
            logger.warning(f"Weather context unavailable: {e}")
            return None  # Graceful degradation
```

**Potential Data Sources (If Validated):**
- Weather API (OpenWeatherMap - $0-10/month)
- Events API (PredictHQ - $50-100/month)
- Basic place info (Google Places - pay-per-use, with caps)

**Integration Points:**
- AI Assistant context enhancement (not primary feature)
- Magic Polls enrichment (optional suggestions)
- Itinerary generation improvements (fallback to internal data)

**Explicitly Out of Scope:**
- ❌ Booking system integrations
- ❌ Price monitoring or alerts
- ❌ Real-time disruption management
- ❌ Transactional features
- ❌ Any feature that conflicts with cost-optimization architecture

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
