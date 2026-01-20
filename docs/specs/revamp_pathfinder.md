# Pathfinder Revamp Plan

**Document Version:** 1.0
**Created:** January 19, 2026
**Status:** Approved for Implementation

---

## Executive Summary

This document outlines the comprehensive plan to migrate Pathfinder from Azure Container Apps to a cost-optimized Azure Static Web Apps + Azure Functions architecture. The migration addresses existing technical debt while achieving 70-80% cost reduction.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend Hosting | Azure Static Web Apps (Free tier) | Zero cost, global CDN |
| Backend Compute | Azure Functions (Flex Consumption) | Pay-per-execution, auto-scale |
| Database | Azure Cosmos DB (Serverless) | Pay-per-request, no idle cost |
| Real-time | Azure SignalR Service (Free tier) | 20K msg/day, Azure-native |
| Authentication | Microsoft Entra ID (Simplified) | SSO across Vedprakash apps |
| Secrets | Azure Key Vault | Secure, managed secrets |
| AI Model | OpenAI gpt-5-mini | Cost-effective for consumer app |
| Region | West US 2 (primary) | Co-located services, low latency |

### Expected Monthly Costs

| Scenario | Estimated Cost |
|----------|----------------|
| Idle/Development | $0-5 |
| Light usage (10 users) | $5-15 |
| Moderate usage (100 users) | $15-30 |

---

## Table of Contents

1. [Resource Architecture](#1-resource-architecture)
2. [Phase 0: Codebase Cleanup](#2-phase-0-codebase-cleanup)
3. [Phase 1: Backend Migration to Azure Functions](#3-phase-1-backend-migration)
4. [Phase 2: Authentication Overhaul](#4-phase-2-authentication-overhaul)
5. [Phase 3: Real-time with Azure SignalR](#5-phase-3-signalr-integration)
6. [Phase 4: Frontend Adaptation](#6-phase-4-frontend-adaptation)
7. [Phase 5: Infrastructure as Code](#7-phase-5-infrastructure-as-code)
8. [Phase 6: CI/CD Pipeline](#8-phase-6-cicd-pipeline)
9. [Phase 7: Testing & Quality](#9-phase-7-testing-quality)
10. [Phase 8: Deployment & Validation](#10-phase-8-deployment-validation)
11. [Task Checklist](#11-task-checklist)

---

## 1. Resource Architecture

### 1.1 Resource Group

All resources deployed to single resource group:

```
Resource Group: pathfinder-rg
Location: West US 2
```

### 1.2 Resource Naming Convention

| Resource Type | Name | Notes |
|---------------|------|-------|
| Static Web App | `pf-swa` | Frontend hosting |
| Function App | `pf-func` | Backend API |
| Function App Plan | `pf-func-plan` | Flex Consumption |
| Storage Account | `pfstore{unique}` | Functions storage |
| Cosmos DB Account | `pf-cosmos` | Database |
| Cosmos DB Database | `pathfinder` | Single database |
| Cosmos DB Container | `entities` | Unified container |
| SignalR Service | `pf-signalr` | Real-time messaging |
| Key Vault | `pf-kv-{unique}` | Secrets management |
| App Insights | `pf-insights` | Monitoring |
| Log Analytics | `pf-logs` | Centralized logging |

*`{unique}` = `uniqueString(resourceGroup().id)` for global uniqueness*

### 1.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        pathfinder-rg                            │
│                        (West US 2)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   pf-swa     │     │   pf-func    │     │  pf-signalr  │    │
│  │ Static Web   │────▶│   Azure      │────▶│   SignalR    │    │
│  │    App       │     │  Functions   │     │   Service    │    │
│  │  (Frontend)  │     │  (Backend)   │     │  (Realtime)  │    │
│  └──────────────┘     └──────┬───────┘     └──────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  pf-cosmos   │     │   pf-kv      │     │ pf-insights  │    │
│  │  Cosmos DB   │     │  Key Vault   │     │ App Insights │    │
│  │ (Serverless) │     │  (Secrets)   │     │ (Monitoring) │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐                         │
│  │  pfstore*    │     │   pf-logs    │                         │
│  │   Storage    │     │Log Analytics │                         │
│  │  (Functions) │     │  Workspace   │                         │
│  └──────────────┘     └──────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

External Services:
┌──────────────┐     ┌──────────────────────┐
│   OpenAI     │     │  Microsoft Entra ID  │
│  gpt-5-mini  │     │ vedid.onmicrosoft.com│
└──────────────┘     └──────────────────────┘
```

---

## 2. Phase 0: Codebase Cleanup

**Duration:** 3-4 days
**Objective:** Remove dead code, consolidate files, prepare clean baseline

### 2.1 Delete Backup Folders

Remove obsolete backup directories that clutter the codebase:

```bash
# Directories to delete
backend/architectural_repair_backup/
backend/phase3_backup/
backend/phase4_backup/
backend/migration_backup/
```

### 2.2 Archive Fix Scripts

Move one-off fix scripts out of main codebase:

```bash
# Create archive directory
mkdir -p scripts/archived

# Files to move from backend/ to scripts/archived/
comprehensive_fixer_v2.py
comprehensive_fixer_v3.py
comprehensive_ruff_fixer.py
comprehensive_syntax_fixer.py
comprehensive_e2e_validation.py
fix_ai_tasks_alt_tests.py
fix_ai_tests.py
fix_ai_unit_tests.py
fix_environment.py
priority_fix_assessment.py
systematic_progress_tracker.py
enhanced_validation.py
```

### 2.3 Consolidate Test Files

Move misplaced test files to proper location:

```bash
# Files to move from backend/ to backend/tests/legacy/
test_api_basic.py
test_ci_environment.py
test_database.py
test_database_migration_status.py
test_day1_migration_completion.py
test_day2_migration_completion.py
test_day3_ai_cost_management.py
test_day3_ai_integration.py
test_day3_e2e_ai_integration.py
test_day4_performance_mock.py
test_day4_performance_optimization.py
test_day4_security_audit.py
test_day4_security_performance.py
test_day5_onboarding_validation.py
test_family_invitation_workflow.py
test_family_invitations.py
test_imports.py
test_onboarding_flow.py
test_schema_validation.py
test_unified_cosmos.py
```

### 2.4 Delete LLM Orchestration Service

Remove over-engineered separate LLM service (will inline into backend):

```bash
# Directory to delete entirely
llm_orchestration/
```

### 2.5 Remove Auth0 Residue

Files and references to update:

| Location | Action |
|----------|--------|
| `backend/app/repositories/cosmos_unified.py` | Remove `auth0_id` field from `UserDocument` |
| `backend/local_validation.py` | Remove auth0_id from test data |
| `backend/test_family_invitation_workflow.py` | Update test fixtures |
| `scripts/local-validation.sh` | Remove AUTH0_* environment variables |
| `.gitignore` | Remove auth0-related entries |
| `README.md` | Update Auth0 reference to Entra ID |

### 2.6 Clean Up Obsolete Files

```bash
# Delete obsolete database files
backend/data.db
backend/pathfinder.db

# Delete obsolete configuration
backend/alembic.ini  # Not using SQL migrations
backend/alembic/     # Not using SQL migrations
```

### 2.7 Create Proper pyproject.toml

```toml
# backend/pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "pathfinder-api"
version = "1.0.0"
description = "Pathfinder Trip Planning API"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "UP"]
ignore = ["E501"]

[tool.ruff.isort]
known-first-party = ["functions", "core", "services", "repositories", "models"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_ignores = true
ignore_missing_imports = true
```

---

## 3. Phase 1: Backend Migration

**Duration:** 5-7 days
**Objective:** Convert FastAPI backend to Azure Functions

### 3.1 New Project Structure

```
backend/
├── function_app.py                 # Main entry point
├── functions/
│   ├── __init__.py
│   ├── http/                       # HTTP triggers (API endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py                 # /api/auth/*
│   │   ├── trips.py                # /api/trips/*
│   │   ├── families.py             # /api/families/*
│   │   ├── itineraries.py          # /api/itineraries/*
│   │   ├── collaboration.py        # /api/polls/*, /api/consensus/*
│   │   ├── assistant.py            # /api/assistant/*
│   │   ├── signalr.py              # /api/signalr/*
│   │   └── health.py               # /api/health
│   ├── queue/                      # Queue triggers (background tasks)
│   │   ├── __init__.py
│   │   ├── itinerary_generator.py  # AI itinerary generation
│   │   └── notification_sender.py  # Email/push notifications
│   └── timer/                      # Timer triggers (scheduled tasks)
│       ├── __init__.py
│       └── cleanup.py              # Data cleanup jobs
├── core/
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── security.py                 # Auth utilities
│   ├── errors.py                   # Error handling
│   └── middleware.py               # Request/response utilities
├── services/
│   ├── __init__.py
│   ├── trip_service.py
│   ├── family_service.py
│   ├── collaboration_service.py    # Polls + Consensus
│   ├── itinerary_service.py
│   ├── assistant_service.py
│   ├── notification_service.py
│   ├── realtime_service.py         # SignalR integration
│   └── llm/
│       ├── __init__.py
│       ├── client.py               # OpenAI client
│       └── prompts.py              # Prompt templates
├── repositories/
│   ├── __init__.py
│   └── cosmos_repository.py        # Single data access layer
├── models/
│   ├── __init__.py
│   ├── documents.py                # Cosmos document models
│   └── schemas.py                  # Request/response schemas
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│       └── cosmos_mock.py
├── host.json
├── local.settings.json
├── requirements.txt
└── pyproject.toml
```

### 3.2 Main Function App Entry Point

```python
# backend/function_app.py
import azure.functions as func

# Import HTTP blueprints
from functions.http.auth import bp as auth_bp
from functions.http.trips import bp as trips_bp
from functions.http.families import bp as families_bp
from functions.http.itineraries import bp as itineraries_bp
from functions.http.collaboration import bp as collaboration_bp
from functions.http.assistant import bp as assistant_bp
from functions.http.signalr import bp as signalr_bp
from functions.http.health import bp as health_bp

# Import Queue blueprints
from functions.queue.itinerary_generator import bp as itinerary_queue_bp
from functions.queue.notification_sender import bp as notification_queue_bp

# Import Timer blueprints
from functions.timer.cleanup import bp as cleanup_bp

# Create function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(trips_bp)
app.register_blueprint(families_bp)
app.register_blueprint(itineraries_bp)
app.register_blueprint(collaboration_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(signalr_bp)
app.register_blueprint(health_bp)
app.register_blueprint(itinerary_queue_bp)
app.register_blueprint(notification_queue_bp)
app.register_blueprint(cleanup_bp)
```

### 3.3 Configuration Management

```python
# core/config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Cosmos DB
    COSMOS_DB_URL: str
    COSMOS_DB_KEY: str
    COSMOS_DB_DATABASE: str = "pathfinder"
    COSMOS_DB_CONTAINER: str = "entities"

    # SignalR
    SIGNALR_CONNECTION_STRING: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_MAX_TOKENS: int = 2000

    # Microsoft Entra ID
    ENTRA_TENANT_ID: str = "vedid.onmicrosoft.com"
    ENTRA_CLIENT_ID: str
    ENTRA_AUTHORITY: str = "https://login.microsoftonline.com/vedid.onmicrosoft.com"

    # Application Insights
    APPINSIGHTS_INSTRUMENTATIONKEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 3.4 Cosmos Repository (Simplified)

```python
# repositories/cosmos_repository.py
import os
import logging
from typing import Optional, List, TypeVar, Type
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from models.documents import BaseDocument

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseDocument)

class CosmosRepository:
    """Unified Cosmos DB repository - single data access layer."""

    _instance: Optional['CosmosRepository'] = None
    _client: Optional[CosmosClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _get_container(self):
        """Get or create Cosmos DB container client."""
        if self._client is None:
            self._client = CosmosClient(
                url=os.environ["COSMOS_DB_URL"],
                credential=os.environ["COSMOS_DB_KEY"]
            )

        database = self._client.get_database_client(
            os.environ.get("COSMOS_DB_DATABASE", "pathfinder")
        )
        return database.get_container_client(
            os.environ.get("COSMOS_DB_CONTAINER", "entities")
        )

    async def create(self, document: T) -> T:
        """Create a new document."""
        container = await self._get_container()
        doc_dict = document.model_dump(mode='json')
        result = await container.create_item(body=doc_dict)
        return type(document)(**result)

    async def get_by_id(
        self,
        doc_id: str,
        partition_key: str,
        model_class: Type[T]
    ) -> Optional[T]:
        """Get document by ID and partition key."""
        container = await self._get_container()
        try:
            result = await container.read_item(
                item=doc_id,
                partition_key=partition_key
            )
            return model_class(**result)
        except exceptions.CosmosResourceNotFoundError:
            return None

    async def query(
        self,
        query: str,
        parameters: Optional[List[dict]] = None,
        model_class: Optional[Type[T]] = None
    ) -> List[T]:
        """Query documents with SQL-like syntax."""
        container = await self._get_container()
        items = []

        async for item in container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True
        ):
            if model_class:
                items.append(model_class(**item))
            else:
                items.append(item)

        return items

    async def update(self, document: T) -> T:
        """Update an existing document."""
        container = await self._get_container()
        doc_dict = document.model_dump(mode='json')
        result = await container.replace_item(
            item=doc_dict["id"],
            body=doc_dict
        )
        return type(document)(**result)

    async def delete(self, doc_id: str, partition_key: str) -> bool:
        """Delete a document."""
        container = await self._get_container()
        try:
            await container.delete_item(item=doc_id, partition_key=partition_key)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False

    async def upsert(self, document: T) -> T:
        """Create or update a document."""
        container = await self._get_container()
        doc_dict = document.model_dump(mode='json')
        result = await container.upsert_item(body=doc_dict)
        return type(document)(**result)


# Singleton instance
cosmos_repo = CosmosRepository()
```

### 3.5 Document Models

```python
# models/documents.py
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from uuid import uuid4

class BaseDocument(BaseModel):
    """Base document for all Cosmos DB entities."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    pk: str = Field(..., description="Partition key")
    entity_type: str = Field(..., description="Document type discriminator")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class UserDocument(BaseDocument):
    """User document."""
    entity_type: Literal["user"] = "user"

    # Identity (Entra ID)
    entra_id: str
    email: str
    name: Optional[str] = None

    # Profile
    role: str = "family_admin"
    picture: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

    # Status
    is_active: bool = True
    is_verified: bool = False

    # Onboarding
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None

    # Relationships
    family_ids: List[str] = Field(default_factory=list)

class FamilyDocument(BaseDocument):
    """Family document."""
    entity_type: Literal["family"] = "family"

    name: str
    description: Optional[str] = None
    admin_user_id: str
    member_ids: List[str] = Field(default_factory=list)
    settings: Optional[Dict[str, Any]] = None

class TripDocument(BaseDocument):
    """Trip document."""
    entity_type: Literal["trip"] = "trip"

    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "planning"
    budget: Optional[float] = None

    organizer_user_id: str
    participating_family_ids: List[str] = Field(default_factory=list)

    itinerary: Optional[Dict[str, Any]] = None
    expenses: List[Dict[str, Any]] = Field(default_factory=list)

class MessageDocument(BaseDocument):
    """Chat message document."""
    entity_type: Literal["message"] = "message"

    trip_id: str
    user_id: str
    user_name: str
    content: str
    message_type: str = "text"

class PollDocument(BaseDocument):
    """Poll document."""
    entity_type: Literal["poll"] = "poll"

    trip_id: str
    creator_id: str
    title: str
    description: Optional[str] = None
    poll_type: str
    options: List[Dict[str, Any]] = Field(default_factory=list)
    votes: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    expires_at: Optional[datetime] = None
```

### 3.6 Example HTTP Function (Trips)

```python
# functions/http/trips.py
import json
import logging
import azure.functions as func
from pydantic import ValidationError

from core.security import validate_token, get_user_from_request
from core.errors import APIError, error_response
from services.trip_service import TripService
from models.schemas import TripCreate, TripUpdate, TripResponse

logger = logging.getLogger(__name__)
bp = func.Blueprint()

@bp.function_name("GetTrips")
@bp.route(route="trips", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_trips(req: func.HttpRequest) -> func.HttpResponse:
    """Get all trips for the authenticated user."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        trip_service = TripService()
        trips = await trip_service.get_user_trips(user.id)

        return func.HttpResponse(
            json.dumps([TripResponse.from_document(t).model_dump(mode='json') for t in trips]),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error getting trips")
        return error_response(str(e), 500)

@bp.function_name("CreateTrip")
@bp.route(route="trips", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def create_trip(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new trip."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        # Parse and validate request body
        body = req.get_body().decode('utf-8')
        trip_data = TripCreate.model_validate_json(body)

        # Create trip
        trip_service = TripService()
        trip = await trip_service.create_trip(trip_data, user)

        return func.HttpResponse(
            TripResponse.from_document(trip).model_dump_json(),
            status_code=201,
            mimetype="application/json"
        )
    except ValidationError as e:
        return error_response(f"Validation error: {e}", 400)
    except Exception as e:
        logger.exception("Error creating trip")
        return error_response(str(e), 500)

@bp.function_name("GetTrip")
@bp.route(route="trips/{trip_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_trip(req: func.HttpRequest) -> func.HttpResponse:
    """Get a specific trip by ID."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        trip_id = req.route_params.get('trip_id')

        trip_service = TripService()
        trip = await trip_service.get_trip(trip_id)

        if not trip:
            return error_response("Trip not found", 404)

        # Check access
        if not trip_service.user_has_access(trip, user.id):
            return error_response("Forbidden", 403)

        return func.HttpResponse(
            TripResponse.from_document(trip).model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error getting trip")
        return error_response(str(e), 500)

@bp.function_name("UpdateTrip")
@bp.route(route="trips/{trip_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
async def update_trip(req: func.HttpRequest) -> func.HttpResponse:
    """Update a trip."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        trip_id = req.route_params.get('trip_id')
        body = req.get_body().decode('utf-8')
        update_data = TripUpdate.model_validate_json(body)

        trip_service = TripService()
        trip = await trip_service.update_trip(trip_id, update_data, user)

        if not trip:
            return error_response("Trip not found or access denied", 404)

        return func.HttpResponse(
            TripResponse.from_document(trip).model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
    except ValidationError as e:
        return error_response(f"Validation error: {e}", 400)
    except Exception as e:
        logger.exception("Error updating trip")
        return error_response(str(e), 500)

@bp.function_name("DeleteTrip")
@bp.route(route="trips/{trip_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
async def delete_trip(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a trip."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        trip_id = req.route_params.get('trip_id')

        trip_service = TripService()
        success = await trip_service.delete_trip(trip_id, user)

        if not success:
            return error_response("Trip not found or access denied", 404)

        return func.HttpResponse(status_code=204)
    except Exception as e:
        logger.exception("Error deleting trip")
        return error_response(str(e), 500)
```

### 3.7 Queue Function (Background AI)

```python
# functions/queue/itinerary_generator.py
import json
import logging
import azure.functions as func
from services.itinerary_service import ItineraryService
from services.realtime_service import RealtimeService

logger = logging.getLogger(__name__)
bp = func.Blueprint()

@bp.function_name("GenerateItinerary")
@bp.queue_trigger(
    arg_name="msg",
    queue_name="itinerary-requests",
    connection="AzureWebJobsStorage"
)
async def generate_itinerary(msg: func.QueueMessage) -> None:
    """Process itinerary generation request from queue."""
    try:
        # Parse message
        data = json.loads(msg.get_body().decode('utf-8'))
        trip_id = data["trip_id"]
        user_id = data["user_id"]
        preferences = data.get("preferences", {})

        logger.info(f"Generating itinerary for trip {trip_id}")

        # Generate itinerary using AI
        itinerary_service = ItineraryService()
        itinerary = await itinerary_service.generate_itinerary(
            trip_id=trip_id,
            preferences=preferences
        )

        # Notify via SignalR
        realtime = RealtimeService()
        await realtime.broadcast_to_trip(
            trip_id=trip_id,
            event="itinerary_generated",
            data={"itinerary": itinerary, "generated_by": user_id}
        )

        logger.info(f"Itinerary generated successfully for trip {trip_id}")

    except Exception as e:
        logger.exception(f"Failed to generate itinerary: {e}")
        raise  # Re-raise to trigger retry
```

### 3.8 LLM Client

```python
# services/llm/client.py
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from core.config import get_settings

logger = logging.getLogger(__name__)

class LLMClient:
    """OpenAI client wrapper with cost tracking."""

    _instance: Optional['LLMClient'] = None
    _client: Optional[AsyncOpenAI] = None

    # Cost per 1K tokens (gpt-5-mini estimated pricing)
    COST_PER_1K_INPUT = 0.0001
    COST_PER_1K_OUTPUT = 0.0004

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            settings = get_settings()
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate completion using gpt-5-mini."""
        settings = get_settings()
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,  # gpt-5-mini
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Extract response
            content = response.choices[0].message.content
            usage = response.usage

            # Calculate cost
            input_cost = (usage.prompt_tokens / 1000) * self.COST_PER_1K_INPUT
            output_cost = (usage.completion_tokens / 1000) * self.COST_PER_1K_OUTPUT
            total_cost = input_cost + output_cost

            logger.info(
                f"LLM request completed: {usage.total_tokens} tokens, ${total_cost:.6f}"
            )

            return {
                "content": content,
                "tokens_used": usage.total_tokens,
                "cost": total_cost,
                "model": settings.OPENAI_MODEL
            }

        except Exception as e:
            logger.exception(f"LLM request failed: {e}")
            raise

# Singleton instance
llm_client = LLMClient()
```

### 3.9 host.json Configuration

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 5
      }
    },
    "logLevel": {
      "default": "Information",
      "Host.Results": "Error",
      "Function": "Information",
      "Host.Aggregator": "Trace"
    }
  },
  "extensions": {
    "http": {
      "routePrefix": "api",
      "maxOutstandingRequests": 200,
      "maxConcurrentRequests": 100
    },
    "queues": {
      "maxPollingInterval": "00:00:02",
      "visibilityTimeout": "00:00:30",
      "batchSize": 16,
      "maxDequeueCount": 5
    }
  },
  "functionTimeout": "00:05:00"
}
```

### 3.10 requirements.txt

```txt
# Azure Functions
azure-functions>=1.17.0

# Azure Services
azure-cosmos>=4.5.0
azure-identity>=1.15.0
azure-messaging-webpubsubservice>=1.0.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# OpenAI
openai>=1.10.0

# Authentication
PyJWT>=2.8.0
cryptography>=41.0.0

# HTTP Client
httpx>=0.25.0

# Utilities
python-dateutil>=2.8.2
```

---

## 4. Phase 2: Authentication Overhaul

**Duration:** 3-4 days
**Objective:** Implement clean, simplified Microsoft Entra ID authentication

### 4.1 Authentication Architecture

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│    Frontend      │      │  Azure Function  │      │  Microsoft       │
│   (SPA + MSAL)   │─────▶│    (Validate)    │─────▶│   Entra ID       │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                         │
         │ 1. Login popup          │ 2. Validate JWT
         │ 2. Get access token     │ 3. Extract user
         │ 3. Send token           │ 4. Check/create user
         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│   MSAL React     │      │   Cosmos DB      │
│   (Token cache)  │      │   (User store)   │
└──────────────────┘      └──────────────────┘
```

### 4.2 Backend Security Module

```python
# core/security.py
import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache
import jwt
from jwt import PyJWKClient
import azure.functions as func
from models.documents import UserDocument
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)

# Cache JWKS client
_jwks_client: Optional[PyJWKClient] = None

def get_jwks_client() -> PyJWKClient:
    """Get cached JWKS client for token validation."""
    global _jwks_client
    if _jwks_client is None:
        tenant_id = os.environ.get("ENTRA_TENANT_ID", "vedid.onmicrosoft.com")
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client

def extract_token(req: func.HttpRequest) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None

async def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate JWT token and return claims."""
    try:
        # Get signing key from JWKS
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Validate token
        client_id = os.environ.get("ENTRA_CLIENT_ID")
        tenant_id = os.environ.get("ENTRA_TENANT_ID", "vedid.onmicrosoft.com")

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            options={"verify_exp": True}
        )

        return claims

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.exception(f"Token validation error: {e}")
        return None

async def get_or_create_user(claims: Dict[str, Any]) -> UserDocument:
    """Get existing user or create new one from token claims."""
    entra_id = claims.get("sub") or claims.get("oid")
    email = claims.get("email") or claims.get("preferred_username", "")
    name = claims.get("name", "")

    # Try to find existing user
    query = "SELECT * FROM c WHERE c.entity_type = 'user' AND c.entra_id = @entraId"
    users = await cosmos_repo.query(
        query=query,
        parameters=[{"name": "@entraId", "value": entra_id}],
        model_class=UserDocument
    )

    if users:
        return users[0]

    # Create new user
    user = UserDocument(
        pk=f"user_{entra_id}",
        entra_id=entra_id,
        email=email,
        name=name,
        role="family_admin"  # Default role per PRD
    )

    return await cosmos_repo.create(user)

async def get_user_from_request(req: func.HttpRequest) -> Optional[UserDocument]:
    """Extract and validate user from request."""
    token = extract_token(req)
    if not token:
        return None

    claims = await validate_token(token)
    if not claims:
        return None

    return await get_or_create_user(claims)
```

### 4.3 Frontend Auth Context

```typescript
// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useMsal, useAccount, useIsAuthenticated } from '@azure/msal-react';
import { InteractionStatus } from '@azure/msal-browser';
import { loginRequest } from '@/lib/msal-config';
import { User, AuthContextType } from '@/types/auth';
import { api, setTokenGetter } from '@/services/api';

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { instance, accounts, inProgress } = useMsal();
  const account = useAccount(accounts[0] || null);
  const isMsalAuthenticated = useIsAuthenticated();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Token acquisition function
  const getAccessToken = useCallback(async (): Promise<string | null> => {
    if (!account) return null;

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      });
      return response.accessToken;
    } catch (e) {
      // Silent acquisition failed, try interactive
      try {
        const response = await instance.acquireTokenPopup({
          ...loginRequest,
          account,
        });
        return response.accessToken;
      } catch (popupError) {
        console.error('Token acquisition failed:', popupError);
        return null;
      }
    }
  }, [instance, account]);

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      if (inProgress !== InteractionStatus.None) return;

      setIsLoading(true);
      setError(null);

      try {
        if (isMsalAuthenticated && account) {
          // Set up API token getter
          setTokenGetter(getAccessToken);

          // Fetch user profile from backend
          const response = await api.get('/auth/me');
          setUser(response.data);
        } else {
          setUser(null);
        }
      } catch (e) {
        console.error('Auth initialization error:', e);
        setError('Failed to initialize authentication');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [isMsalAuthenticated, account, inProgress, getAccessToken]);

  // Login function
  const login = useCallback(async () => {
    try {
      setError(null);
      await instance.loginPopup(loginRequest);
    } catch (e) {
      console.error('Login error:', e);
      setError('Login failed. Please try again.');
      throw e;
    }
  }, [instance]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      setError(null);
      await instance.logoutPopup({
        postLogoutRedirectUri: window.location.origin,
      });
      setUser(null);
    } catch (e) {
      console.error('Logout error:', e);
      setError('Logout failed');
      throw e;
    }
  }, [instance]);

  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading: isLoading || inProgress !== InteractionStatus.None,
    error,
    login,
    logout,
    getAccessToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### 4.4 MSAL Configuration

```typescript
// frontend/src/lib/msal-config.ts
import { Configuration, LogLevel, PopupRequest } from '@azure/msal-browser';

const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID;
const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID || 'vedid.onmicrosoft.com';
const redirectUri = import.meta.env.VITE_REDIRECT_URI || window.location.origin;

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri,
    postLogoutRedirectUri: redirectUri,
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: true,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            break;
          case LogLevel.Warning:
            console.warn(message);
            break;
          case LogLevel.Info:
            console.info(message);
            break;
          case LogLevel.Verbose:
            console.debug(message);
            break;
        }
      },
      logLevel: import.meta.env.DEV ? LogLevel.Verbose : LogLevel.Warning,
    },
  },
};

export const loginRequest: PopupRequest = {
  scopes: [`api://${clientId}/access_as_user`],
};
```

### 4.5 Auth Function Endpoints

```python
# functions/http/auth.py
import json
import logging
import azure.functions as func
from core.security import get_user_from_request, extract_token, validate_token
from core.errors import error_response
from models.schemas import UserProfile

logger = logging.getLogger(__name__)
bp = func.Blueprint()

@bp.function_name("GetCurrentUser")
@bp.route(route="auth/me", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_current_user(req: func.HttpRequest) -> func.HttpResponse:
    """Get current authenticated user profile."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        profile = UserProfile.from_document(user)
        return func.HttpResponse(
            profile.model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error getting current user")
        return error_response(str(e), 500)

@bp.function_name("GetOnboardingStatus")
@bp.route(route="auth/onboarding-status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_onboarding_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get user's onboarding status."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        return func.HttpResponse(
            json.dumps({
                "onboarding_completed": user.onboarding_completed,
                "onboarding_completed_at": user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None,
                "family_ids": user.family_ids,
                "has_family": len(user.family_ids) > 0
            }),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error getting onboarding status")
        return error_response(str(e), 500)

@bp.function_name("CompleteOnboarding")
@bp.route(route="auth/complete-onboarding", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def complete_onboarding(req: func.HttpRequest) -> func.HttpResponse:
    """Mark user's onboarding as complete."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        from datetime import datetime
        from repositories.cosmos_repository import cosmos_repo

        user.onboarding_completed = True
        user.onboarding_completed_at = datetime.utcnow()

        updated_user = await cosmos_repo.update(user)

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("Error completing onboarding")
        return error_response(str(e), 500)
```

---

## 5. Phase 3: SignalR Integration

**Duration:** 2-3 days
**Objective:** Implement real-time messaging using Azure SignalR Service

### 5.1 SignalR Service Configuration

Azure SignalR Service (Free tier):
- 20,000 messages/day
- 20 concurrent connections
- Serverless mode (no persistent connection needed)
- Native Azure service (uses Azure credits)

### 5.2 Realtime Service

```python
# services/realtime_service.py
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from azure.messaging.webpubsubservice import WebPubSubServiceClient

logger = logging.getLogger(__name__)

class RealtimeService:
    """Azure SignalR/Web PubSub service for real-time messaging."""

    _instance: Optional['RealtimeService'] = None
    _client: Optional[WebPubSubServiceClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self) -> WebPubSubServiceClient:
        if self._client is None:
            connection_string = os.environ["SIGNALR_CONNECTION_STRING"]
            self._client = WebPubSubServiceClient.from_connection_string(
                connection_string,
                hub="pathfinder"
            )
        return self._client

    async def broadcast_to_trip(
        self,
        trip_id: str,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        """Broadcast message to all participants in a trip."""
        client = self._get_client()

        message = json.dumps({
            "event": event,
            "tripId": trip_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            client.send_to_group(
                group=f"trip_{trip_id}",
                message=message,
                content_type="application/json"
            )
            logger.info(f"Broadcast to trip {trip_id}: {event}")
        except Exception as e:
            logger.exception(f"Failed to broadcast to trip {trip_id}: {e}")

    async def notify_user(
        self,
        user_id: str,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        """Send notification to specific user."""
        client = self._get_client()

        message = json.dumps({
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            client.send_to_user(
                user_id=user_id,
                message=message,
                content_type="application/json"
            )
            logger.info(f"Notification sent to user {user_id}: {event}")
        except Exception as e:
            logger.exception(f"Failed to notify user {user_id}: {e}")

    def get_client_token(
        self,
        user_id: str,
        trip_ids: List[str]
    ) -> Dict[str, str]:
        """Generate client access token with group permissions."""
        client = self._get_client()

        # Create roles for joining trip groups
        roles = [f"webpubsub.joinLeaveGroup.trip_{tid}" for tid in trip_ids]

        token_response = client.get_client_access_token(
            user_id=user_id,
            roles=roles,
            minutes_to_expire=60
        )

        return {
            "url": token_response["baseUrl"],
            "token": token_response["token"]
        }

# Singleton instance
realtime_service = RealtimeService()
```

### 5.3 SignalR Negotiate Function

```python
# functions/http/signalr.py
import json
import logging
import azure.functions as func
from core.security import get_user_from_request
from core.errors import error_response
from services.realtime_service import realtime_service
from services.trip_service import TripService

logger = logging.getLogger(__name__)
bp = func.Blueprint()

@bp.function_name("SignalRNegotiate")
@bp.route(route="signalr/negotiate", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def negotiate(req: func.HttpRequest) -> func.HttpResponse:
    """Get SignalR connection token for authenticated user."""
    try:
        user = await get_user_from_request(req)
        if not user:
            return error_response("Unauthorized", 401)

        # Get user's trips for group membership
        trip_service = TripService()
        trips = await trip_service.get_user_trips(user.id)
        trip_ids = [t.id for t in trips]

        # Generate token
        token_data = realtime_service.get_client_token(user.id, trip_ids)

        return func.HttpResponse(
            json.dumps(token_data),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.exception("SignalR negotiate failed")
        return error_response(str(e), 500)
```

### 5.4 Frontend SignalR Client

```typescript
// frontend/src/services/realtimeService.ts
import { api } from './api';

type EventCallback = (data: any) => void;

class RealtimeService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  async connect(): Promise<void> {
    try {
      // Get connection token from backend
      const response = await api.post('/signalr/negotiate');
      const { url, token } = response.data;

      // Connect to SignalR
      this.ws = new WebSocket(`${url}&access_token=${token}`);

      this.ws.onopen = () => {
        console.log('SignalR connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.emit(message.event, message.data);
        } catch (e) {
          console.error('Failed to parse SignalR message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('SignalR disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('SignalR error:', error);
      };

    } catch (error) {
      console.error('Failed to connect to SignalR:', error);
      throw error;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }

  on(event: string, callback: EventCallback): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  off(event: string, callback: EventCallback): void {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (e) {
        console.error(`Error in event handler for ${event}:`, e);
      }
    });
  }

  async disconnect(): Promise<void> {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const realtimeService = new RealtimeService();
```

---

## 6. Phase 4: Frontend Adaptation

**Duration:** 3-4 days
**Objective:** Adapt frontend for Static Web Apps deployment

### 6.1 Vite Configuration

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@fluentui/react-components', '@fluentui/react-icons'],
          msal: ['@azure/msal-browser', '@azure/msal-react'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:7071',
        changeOrigin: true,
      },
    },
  },
});
```

### 6.2 Static Web App Configuration

```json
// frontend/staticwebapp.config.json
{
  "routes": [
    {
      "route": "/api/*",
      "rewrite": "/api/*"
    },
    {
      "route": "/*",
      "rewrite": "/index.html"
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/*.{css,js,ico,png,svg,woff,woff2}"]
  },
  "mimeTypes": {
    ".json": "application/json"
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()"
  },
  "platform": {
    "apiRuntime": "python:3.11"
  }
}
```

### 6.3 API Client Update

```typescript
// frontend/src/services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

// Token getter function - set by AuthProvider
let tokenGetter: (() => Promise<string | null>) | null = null;

export const setTokenGetter = (getter: () => Promise<string | null>) => {
  tokenGetter = getter;
};

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(async (config) => {
  if (tokenGetter) {
    try {
      const token = await tokenGetter();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.warn('Failed to get access token:', error);
    }
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export { api };
```

### 6.4 Environment Variables

```bash
# frontend/.env.example
VITE_API_URL=/api
VITE_ENTRA_CLIENT_ID=your-client-id
VITE_ENTRA_TENANT_ID=vedid.onmicrosoft.com
VITE_REDIRECT_URI=http://localhost:3000
```

---

## 7. Phase 5: Infrastructure as Code

**Duration:** 2-3 days
**Objective:** Create Bicep templates for single-environment deployment

### 7.1 Main Bicep Template

```bicep
// infrastructure/main.bicep
@description('Location for all resources')
param location string = 'westus2'

@secure()
@description('OpenAI API Key')
param openAiApiKey string

@description('Microsoft Entra ID Client ID')
param entraClientId string

// Unique suffix for globally unique names
var uniqueSuffix = uniqueString(resourceGroup().id)

// Tags applied to all resources
var tags = {
  app: 'pathfinder'
  managedBy: 'bicep'
}

// Resource names following naming convention
var names = {
  swa: 'pf-swa'
  func: 'pf-func'
  funcPlan: 'pf-func-plan'
  storage: 'pfstore${uniqueSuffix}'
  cosmos: 'pf-cosmos'
  signalr: 'pf-signalr'
  keyVault: 'pf-kv-${uniqueSuffix}'
  insights: 'pf-insights'
  logs: 'pf-logs'
}

// ============================================================================
// Log Analytics Workspace
// ============================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: names.logs
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: 1
    }
  }
}

// ============================================================================
// Application Insights
// ============================================================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: names.insights
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================================
// Storage Account (for Functions)
// ============================================================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: names.storage
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

// Queue for background tasks
resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource itineraryQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-01-01' = {
  parent: queueService
  name: 'itinerary-requests'
}

resource notificationQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-01-01' = {
  parent: queueService
  name: 'notification-requests'
}

// ============================================================================
// Cosmos DB (Serverless)
// ============================================================================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: names.cosmos
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    enableFreeTier: false
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'pathfinder'
  properties: {
    resource: {
      id: 'pathfinder'
    }
  }
}

resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'entities'
  properties: {
    resource: {
      id: 'entities'
      partitionKey: {
        paths: ['/pk']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/preferences/*'
          }
          {
            path: '/itinerary/*'
          }
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

// ============================================================================
// SignalR Service (Free tier)
// ============================================================================
resource signalr 'Microsoft.SignalRService/signalR@2023-02-01' = {
  name: names.signalr
  location: location
  tags: tags
  sku: {
    name: 'Free_F1'
    tier: 'Free'
    capacity: 1
  }
  properties: {
    features: [
      {
        flag: 'ServiceMode'
        value: 'Serverless'
      }
    ]
    cors: {
      allowedOrigins: [
        'https://${names.swa}.azurestaticapps.net'
        'http://localhost:3000'
      ]
    }
  }
}

// ============================================================================
// Key Vault
// ============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: names.keyVault
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
  }
}

// Secrets
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openAiApiKey
  }
}

resource cosmosKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'cosmos-db-key'
  properties: {
    value: cosmosAccount.listKeys().primaryMasterKey
  }
}

resource signalrConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'signalr-connection-string'
  properties: {
    value: signalr.listKeys().primaryConnectionString
  }
}

// ============================================================================
// Function App (Flex Consumption)
// ============================================================================
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: names.func
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      pythonVersion: '3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'COSMOS_DB_URL'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_DB_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/cosmos-db-key/)'
        }
        {
          name: 'COSMOS_DB_DATABASE'
          value: 'pathfinder'
        }
        {
          name: 'COSMOS_DB_CONTAINER'
          value: 'entities'
        }
        {
          name: 'SIGNALR_CONNECTION_STRING'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/signalr-connection-string/)'
        }
        {
          name: 'OPENAI_API_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/openai-api-key/)'
        }
        {
          name: 'OPENAI_MODEL'
          value: 'gpt-5-mini'
        }
        {
          name: 'ENTRA_TENANT_ID'
          value: 'vedid.onmicrosoft.com'
        }
        {
          name: 'ENTRA_CLIENT_ID'
          value: entraClientId
        }
      ]
      cors: {
        allowedOrigins: [
          'https://${names.swa}.azurestaticapps.net'
          'http://localhost:3000'
        ]
        supportCredentials: true
      }
    }
  }
}

// Key Vault access for Function App
resource kvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Static Web App
// ============================================================================
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: names.swa
  location: 'westus2'
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    buildProperties: {
      appLocation: '/frontend'
      outputLocation: 'dist'
      skipGithubActionWorkflowGeneration: true
    }
  }
}

// Link SWA to Function App backend
resource swaBackendLink 'Microsoft.Web/staticSites/linkedBackends@2022-09-01' = {
  parent: staticWebApp
  name: 'backend'
  properties: {
    backendResourceId: functionApp.id
    region: location
  }
}

// ============================================================================
// Outputs
// ============================================================================
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'
output staticWebAppName string = staticWebApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppName string = functionApp.name
output cosmosDbEndpoint string = cosmosAccount.properties.documentEndpoint
output keyVaultUri string = keyVault.properties.vaultUri
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
```

### 7.2 Deployment Script

```bash
#!/bin/bash
# infrastructure/deploy.sh

set -e

# Configuration
RESOURCE_GROUP="pathfinder-rg"
LOCATION="westus2"
DEPLOYMENT_NAME="pathfinder-deployment-$(date +%Y%m%d%H%M%S)"

echo "=========================================="
echo "  Pathfinder Azure Deployment"
echo "=========================================="
echo ""

# Validate required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is required"
    exit 1
fi

if [ -z "$ENTRA_CLIENT_ID" ]; then
    echo "❌ Error: ENTRA_CLIENT_ID environment variable is required"
    exit 1
fi

echo "📍 Resource Group: $RESOURCE_GROUP"
echo "📍 Location: $LOCATION"
echo ""

# Create resource group if it doesn't exist
echo "🔧 Ensuring resource group exists..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none

echo "✅ Resource group ready"
echo ""

# Deploy Bicep template
echo "🚀 Deploying infrastructure..."
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --template-file main.bicep \
    --parameters \
        openAiApiKey="$OPENAI_API_KEY" \
        entraClientId="$ENTRA_CLIENT_ID" \
    --output none

echo "✅ Infrastructure deployed"
echo ""

# Get outputs
echo "📋 Deployment Outputs:"
echo "----------------------------------------"

SWA_URL=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --query properties.outputs.staticWebAppUrl.value \
    --output tsv)

FUNC_URL=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --query properties.outputs.functionAppUrl.value \
    --output tsv)

SWA_NAME=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --query properties.outputs.staticWebAppName.value \
    --output tsv)

FUNC_NAME=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --query properties.outputs.functionAppName.value \
    --output tsv)

echo "  Frontend URL: $SWA_URL"
echo "  Backend URL:  $FUNC_URL"
echo "  SWA Name:     $SWA_NAME"
echo "  Func Name:    $FUNC_NAME"
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
```

---

## 8. Phase 6: CI/CD Pipeline

**Duration:** 2 days
**Objective:** Create GitHub Actions workflow for automated deployment

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  RESOURCE_GROUP: pathfinder-rg
  FUNCTION_APP_NAME: pf-func
  SWA_NAME: pf-swa
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  # ============================================
  # Backend Tests
  # ============================================
  test-backend:
    name: Test Backend
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          cache-dependency-path: backend/requirements.txt

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=. --cov-report=xml
        env:
          ENVIRONMENT: testing
          COSMOS_DB_URL: https://test.documents.azure.com:443/
          COSMOS_DB_KEY: test-key
          SIGNALR_CONNECTION_STRING: test-connection
          OPENAI_API_KEY: test-key
          ENTRA_CLIENT_ID: test-client-id

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
          flags: backend

  # ============================================
  # Frontend Tests
  # ============================================
  test-frontend:
    name: Test Frontend
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: Install dependencies
        run: |
          cd frontend
          pnpm install --frozen-lockfile

      - name: Type check
        run: |
          cd frontend
          pnpm run type-check

      - name: Run tests
        run: |
          cd frontend
          pnpm run test -- --run

  # ============================================
  # Deploy Backend (Functions)
  # ============================================
  deploy-backend:
    name: Deploy Backend
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt --target=".python_packages/lib/site-packages"

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: ${{ env.FUNCTION_APP_NAME }}
          package: backend
          respect-funcignore: true

  # ============================================
  # Deploy Frontend (Static Web App)
  # ============================================
  deploy-frontend:
    name: Deploy Frontend
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: Install dependencies
        run: |
          cd frontend
          pnpm install --frozen-lockfile

      - name: Build frontend
        run: |
          cd frontend
          pnpm run build
        env:
          VITE_API_URL: /api
          VITE_ENTRA_CLIENT_ID: ${{ secrets.ENTRA_CLIENT_ID }}
          VITE_ENTRA_TENANT_ID: vedid.onmicrosoft.com

      - name: Deploy to Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.SWA_DEPLOYMENT_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: upload
          app_location: frontend
          output_location: dist
          skip_api_build: true
```

### 8.2 GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Azure Service Principal credentials (JSON) |
| `SWA_DEPLOYMENT_TOKEN` | Static Web App deployment token |
| `ENTRA_CLIENT_ID` | Microsoft Entra ID application client ID |
| `OPENAI_API_KEY` | OpenAI API key |

---

## 9. Phase 7: Testing & Quality

**Duration:** 3-4 days
**Objective:** Establish comprehensive test coverage

### 9.1 Test Structure

```
backend/tests/
├── conftest.py               # Shared fixtures
├── fixtures/
│   └── cosmos_mock.py        # Mock Cosmos repository
├── unit/
│   ├── test_trip_service.py
│   ├── test_family_service.py
│   ├── test_collaboration_service.py
│   ├── test_llm_client.py
│   └── test_security.py
├── integration/
│   ├── test_trips_api.py
│   ├── test_families_api.py
│   ├── test_auth_api.py
│   └── test_signalr_api.py
└── e2e/
    └── test_user_journey.py
```

### 9.2 Mock Cosmos Repository

```python
# backend/tests/fixtures/cosmos_mock.py
from typing import Dict, List, Optional, Type, TypeVar
from models.documents import BaseDocument
from repositories.cosmos_repository import CosmosRepository

T = TypeVar('T', bound=BaseDocument)

class MockCosmosRepository(CosmosRepository):
    """In-memory mock repository for testing."""

    def __init__(self):
        self._data: Dict[str, Dict[str, dict]] = {}

    async def _get_container(self):
        # Not needed for mock
        return None

    async def create(self, document: T) -> T:
        doc_dict = document.model_dump(mode='json')
        pk = doc_dict["pk"]
        doc_id = doc_dict["id"]

        if pk not in self._data:
            self._data[pk] = {}

        self._data[pk][doc_id] = doc_dict
        return document

    async def get_by_id(
        self,
        doc_id: str,
        partition_key: str,
        model_class: Type[T]
    ) -> Optional[T]:
        doc = self._data.get(partition_key, {}).get(doc_id)
        return model_class(**doc) if doc else None

    async def query(
        self,
        query: str,
        parameters: Optional[List[dict]] = None,
        model_class: Optional[Type[T]] = None
    ) -> List[T]:
        # Simple mock - return all documents
        results = []
        for pk_data in self._data.values():
            for doc in pk_data.values():
                if model_class:
                    results.append(model_class(**doc))
                else:
                    results.append(doc)
        return results

    async def update(self, document: T) -> T:
        doc_dict = document.model_dump(mode='json')
        pk = doc_dict["pk"]
        doc_id = doc_dict["id"]

        if pk in self._data and doc_id in self._data[pk]:
            self._data[pk][doc_id] = doc_dict

        return document

    async def delete(self, doc_id: str, partition_key: str) -> bool:
        if partition_key in self._data and doc_id in self._data[partition_key]:
            del self._data[partition_key][doc_id]
            return True
        return False

    def reset(self):
        """Clear all data - call between tests."""
        self._data = {}
```

### 9.3 Test Fixtures

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from tests.fixtures.cosmos_mock import MockCosmosRepository
from models.documents import UserDocument, TripDocument, FamilyDocument
from datetime import datetime

@pytest.fixture
def mock_cosmos_repo():
    """Provide fresh mock repository for each test."""
    repo = MockCosmosRepository()
    yield repo
    repo.reset()

@pytest.fixture
def sample_user():
    """Create sample user document."""
    return UserDocument(
        pk="user_test-user-id",
        entra_id="test-entra-id",
        email="test@example.com",
        name="Test User",
        role="family_admin"
    )

@pytest.fixture
def sample_trip(sample_user):
    """Create sample trip document."""
    return TripDocument(
        pk="trip_test-trip-id",
        title="Test Trip",
        destination="Test City",
        organizer_user_id=sample_user.id,
        start_date=datetime(2026, 6, 1),
        end_date=datetime(2026, 6, 7),
        status="planning"
    )

@pytest.fixture
def sample_family(sample_user):
    """Create sample family document."""
    return FamilyDocument(
        pk="family_test-family-id",
        name="Test Family",
        admin_user_id=sample_user.id,
        member_ids=[sample_user.id]
    )
```

### 9.4 Coverage Targets

| Layer | Target | Priority |
|-------|--------|----------|
| Services | 80% | High |
| Repositories | 90% | High |
| HTTP Functions | 70% | Medium |
| Models | 95% | Medium |
| Utilities | 60% | Low |

---

## 10. Phase 8: Deployment & Validation

**Duration:** 2 days
**Objective:** Deploy to Azure and validate functionality

### 10.1 Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Environment variables documented
- [ ] Bicep template validated (`az bicep build`)
- [ ] GitHub secrets configured
- [ ] Entra ID app registration verified
- [ ] OpenAI API key valid

### 10.2 Deployment Steps

1. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   export OPENAI_API_KEY="your-key"
   export ENTRA_CLIENT_ID="your-client-id"
   ./deploy.sh
   ```

2. **Deploy Backend**
   ```bash
   cd backend
   func azure functionapp publish pf-func
   ```

3. **Deploy Frontend**
   - Push to main branch triggers GitHub Actions
   - Or manual deploy via Azure CLI

### 10.3 Post-Deployment Validation

```bash
# Health check
curl https://pf-func.azurewebsites.net/api/health

# Auth flow test
# 1. Open frontend URL
# 2. Click Login
# 3. Complete Entra ID authentication
# 4. Verify redirect and user profile

# API tests
curl -H "Authorization: Bearer $TOKEN" \
     https://pf-func.azurewebsites.net/api/trips
```

### 10.4 Monitoring Setup

1. **Application Insights Dashboard**
   - Request rate
   - Response times
   - Error rate
   - Dependency calls

2. **Alerts** (configure in Azure Portal)
   - Error rate > 5%
   - Response time > 5s
   - Availability < 99%

---

## 11. Task Checklist

### Phase 0: Codebase Cleanup (Week 1, Days 1-4)

- [ ] **0.1** Delete backup folders
  - [ ] `backend/architectural_repair_backup/`
  - [ ] `backend/phase3_backup/`
  - [ ] `backend/phase4_backup/`
  - [ ] `backend/migration_backup/`

- [ ] **0.2** Archive fix scripts
  - [ ] Create `scripts/archived/` directory
  - [ ] Move all `comprehensive_*.py` files
  - [ ] Move all `fix_*.py` files
  - [ ] Move `priority_fix_assessment.py`
  - [ ] Move `systematic_progress_tracker.py`
  - [ ] Move `enhanced_validation.py`

- [ ] **0.3** Consolidate test files
  - [ ] Create `backend/tests/legacy/` directory
  - [ ] Move all `test_*.py` from backend root

- [ ] **0.4** Delete LLM orchestration service
  - [ ] Remove `llm_orchestration/` directory entirely

- [ ] **0.5** Remove Auth0 residue
  - [ ] Remove `auth0_id` from UserDocument
  - [ ] Update test fixtures
  - [ ] Clean scripts
  - [ ] Update README.md

- [ ] **0.6** Delete obsolete files
  - [ ] Remove `backend/data.db`
  - [ ] Remove `backend/pathfinder.db`
  - [ ] Remove `backend/alembic.ini`
  - [ ] Remove `backend/alembic/` directory

- [ ] **0.7** Create proper `pyproject.toml`

### Phase 1: Backend Migration (Week 1-2, Days 5-11)

- [ ] **1.1** Create new project structure
  - [ ] `function_app.py`
  - [ ] `functions/http/` directory
  - [ ] `functions/queue/` directory
  - [ ] `functions/timer/` directory
  - [ ] `core/` directory
  - [ ] `services/` directory
  - [ ] `repositories/` directory
  - [ ] `models/` directory

- [ ] **1.2** Implement core modules
  - [ ] `core/config.py`
  - [ ] `core/security.py`
  - [ ] `core/errors.py`

- [ ] **1.3** Implement Cosmos repository
  - [ ] `repositories/cosmos_repository.py`

- [ ] **1.4** Implement document models
  - [ ] `models/documents.py`
  - [ ] `models/schemas.py`

- [ ] **1.5** Implement services
  - [ ] `services/trip_service.py`
  - [ ] `services/family_service.py`
  - [ ] `services/collaboration_service.py`
  - [ ] `services/itinerary_service.py`
  - [ ] `services/assistant_service.py`
  - [ ] `services/notification_service.py`
  - [ ] `services/realtime_service.py`
  - [ ] `services/llm/client.py`
  - [ ] `services/llm/prompts.py`

- [ ] **1.6** Implement HTTP functions
  - [ ] `functions/http/auth.py`
  - [ ] `functions/http/trips.py`
  - [ ] `functions/http/families.py`
  - [ ] `functions/http/itineraries.py`
  - [ ] `functions/http/collaboration.py`
  - [ ] `functions/http/assistant.py`
  - [ ] `functions/http/signalr.py`
  - [ ] `functions/http/health.py`

- [ ] **1.7** Implement queue functions
  - [ ] `functions/queue/itinerary_generator.py`
  - [ ] `functions/queue/notification_sender.py`

- [ ] **1.8** Implement timer functions
  - [ ] `functions/timer/cleanup.py`

- [ ] **1.9** Configuration files
  - [ ] `host.json`
  - [ ] `requirements.txt`
  - [ ] `local.settings.json`

### Phase 2: Authentication (Week 2, Days 12-15)

- [ ] **2.1** Backend authentication
  - [ ] Implement JWKS client caching
  - [ ] Implement token validation
  - [ ] Implement user extraction
  - [ ] Implement get_or_create_user

- [ ] **2.2** Frontend authentication
  - [ ] Update MSAL configuration
  - [ ] Update AuthContext
  - [ ] Update API client with token getter
  - [ ] Test login/logout flow

- [ ] **2.3** Auth API endpoints
  - [ ] GET `/api/auth/me`
  - [ ] GET `/api/auth/onboarding-status`
  - [ ] POST `/api/auth/complete-onboarding`

### Phase 3: SignalR Integration (Week 2-3, Days 16-18)

- [ ] **3.1** Backend SignalR
  - [ ] Implement `RealtimeService`
  - [ ] Implement negotiate function
  - [ ] Add SignalR broadcasts to services

- [ ] **3.2** Frontend SignalR
  - [ ] Implement `realtimeService.ts`
  - [ ] Add connection in App.tsx
  - [ ] Add event listeners in components

### Phase 4: Frontend Adaptation (Week 3, Days 19-22)

- [ ] **4.1** Configuration updates
  - [ ] Update `vite.config.ts`
  - [ ] Create `staticwebapp.config.json`
  - [ ] Update environment variables

- [ ] **4.2** API client updates
  - [ ] Update base URL handling
  - [ ] Update error handling

- [ ] **4.3** Component updates
  - [ ] Update auth-dependent components
  - [ ] Add loading states
  - [ ] Add error boundaries

### Phase 5: Infrastructure (Week 3, Days 23-25)

- [ ] **5.1** Bicep template
  - [ ] Create `infrastructure/main.bicep`
  - [ ] Validate with `az bicep build`

- [ ] **5.2** Deployment script
  - [ ] Create `infrastructure/deploy.sh`
  - [ ] Test locally

### Phase 6: CI/CD (Week 4, Days 26-27)

- [ ] **6.1** GitHub Actions
  - [ ] Create `.github/workflows/deploy.yml`
  - [ ] Configure secrets
  - [ ] Test workflow

### Phase 7: Testing (Week 4, Days 28-31)

- [ ] **7.1** Test infrastructure
  - [ ] Create `tests/conftest.py`
  - [ ] Create `tests/fixtures/cosmos_mock.py`

- [ ] **7.2** Unit tests
  - [ ] Trip service tests
  - [ ] Family service tests
  - [ ] Collaboration service tests
  - [ ] LLM client tests
  - [ ] Security tests

- [ ] **7.3** Integration tests
  - [ ] Trips API tests
  - [ ] Families API tests
  - [ ] Auth API tests

- [ ] **7.4** Frontend tests
  - [ ] Update existing tests
  - [ ] Add auth flow tests

### Phase 8: Deployment (Week 4, Days 32-33)

- [ ] **8.1** Pre-deployment
  - [ ] Complete checklist verification
  - [ ] Final code review

- [ ] **8.2** Deploy infrastructure
  - [ ] Run Bicep deployment
  - [ ] Verify all resources created

- [ ] **8.3** Deploy applications
  - [ ] Deploy Functions
  - [ ] Deploy Static Web App

- [ ] **8.4** Post-deployment validation
  - [ ] Health check
  - [ ] Auth flow test
  - [ ] API tests
  - [ ] SignalR test

- [ ] **8.5** Monitoring setup
  - [ ] Configure alerts
  - [ ] Verify App Insights

---

## Appendix A: Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- pnpm
- Azure Functions Core Tools v4
- Azure CLI

### Backend Local Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create local.settings.json
cp local.settings.example.json local.settings.json
# Edit local.settings.json with your values

# Start Functions
func start
```

### Frontend Local Development

```bash
cd frontend

# Install dependencies
pnpm install

# Create .env.local
cp .env.example .env.local
# Edit .env.local with your values

# Start dev server
pnpm dev
```

---

## Appendix B: Cost Estimate Details

### Monthly Cost Breakdown (Estimated)

| Resource | SKU | Idle Cost | Active Cost |
|----------|-----|-----------|-------------|
| Static Web App | Free | $0 | $0 |
| Functions (Flex) | Consumption | $0 | $1-5 |
| Cosmos DB | Serverless | $0-2 | $5-15 |
| SignalR | Free | $0 | $0 |
| Key Vault | Standard | $0.03 | $0.03 |
| Storage | LRS | $0.10 | $0.50 |
| App Insights | Pay-per-use | $0 | $2-5 |
| Log Analytics | Pay-per-use | $0 | $1-3 |
| **Total** | | **$0-3** | **$10-30** |

### OpenAI Costs (Separate)

| Usage | Estimated Tokens | Cost |
|-------|-----------------|------|
| Light (10 users) | 100K/month | ~$0.05 |
| Moderate (100 users) | 1M/month | ~$0.50 |
| Heavy (1000 users) | 10M/month | ~$5.00 |

---

## Appendix C: Troubleshooting

### Common Issues

1. **Function cold starts**
   - First request may take 1-5 seconds
   - Consider Premium plan if unacceptable

2. **SignalR connection issues**
   - Verify CORS settings include frontend URL
   - Check token expiration

3. **Auth token validation fails**
   - Verify ENTRA_CLIENT_ID matches app registration
   - Check audience in token

4. **Cosmos DB throttling**
   - Serverless has 5000 RU/s limit
   - Optimize queries and indexing

---

*Document End*
