# ADR-0002: Adopt Unified Cosmos DB + Domain-Driven Design Architecture

**Status:** Proposed  
**Date:** July 3, 2025  
**Deciders:** Senior Engineering Team  
**Technical Impact:** Critical - Requires Full Backend Reconstruction

---

## Context

Deep architectural analysis revealed that the Pathfinder codebase contains **three conflicting architectural patterns** that were implemented incrementally without proper architectural governance:

1. **Legacy SQL Architecture** (SQLAlchemy models, traditional services)
2. **Cosmos DB Unified Architecture** (Document-based, serverless)  
3. **Domain-Driven Design** (Clean architecture, use cases)

This architectural conflict has resulted in:
- 23 out of 26 API files containing syntax errors
- Circular import dependencies between layers
- Conflicting data access patterns
- Unclear service boundaries and responsibilities

## Decision

We will adopt a **Unified Cosmos DB + Domain-Driven Design Architecture** as the single architectural pattern for the entire application.

### Core Architectural Principles:

1. **Single Data Access Pattern**: Only Cosmos DB SQL API for all data storage
2. **Domain-Driven Design**: Clean architecture with clear layer separation
3. **Unified Service Pattern**: Domain services + Use cases for all business logic
4. **Dependency Injection**: FastAPI native dependency injection only

### Architecture Layers:

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (FastAPI routers, endpoints only)      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Application Layer               │
│        (Use cases, orchestration)        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│            Domain Layer                  │
│     (Domain services, business logic)    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Infrastructure Layer             │
│    (Cosmos DB repository, external APIs) │
└─────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Foundation Removal (Days 1-2)
- **Remove all SQL dependencies**: SQLAlchemy models, database engine, sessions
- **Standardize dependency injection**: Use only FastAPI native DI
- **Fix import chains**: Eliminate circular dependencies

### Phase 2: Domain Model Unification (Days 3-4)
- **Single schema source**: Only Cosmos document definitions
- **Repository standardization**: Only `UnifiedCosmosRepository`
- **Data access unification**: All queries through Cosmos SQL API

### Phase 3: Service Layer Standardization (Days 5-6)
- **Domain services only**: Remove traditional service classes
- **Use case standardization**: All API operations through use cases
- **Clean dependency flow**: API → Use Cases → Domain → Repository

### Phase 4: API Layer Reconstruction (Days 7-10)
- **Rebuild 23 API files**: Use new architectural patterns
- **Consistent error handling**: Unified error response patterns
- **Performance optimization**: Efficient Cosmos DB queries

## Consequences

### Positive Consequences:
- **Architectural Clarity**: Single, well-defined architectural pattern
- **Performance**: Optimized Cosmos DB queries with serverless scaling
- **Maintainability**: Clear separation of concerns and responsibilities
- **Cost Efficiency**: Serverless Cosmos DB with optimized resource usage
- **Scalability**: Built-in scaling with Cosmos DB global distribution

### Negative Consequences:
- **Migration Effort**: Requires complete reconstruction of backend API layer
- **Temporary Disruption**: Backend APIs will be non-functional during migration
- **Learning Curve**: Team must adopt domain-driven design patterns
- **Risk**: Potential for introducing new bugs during reconstruction

### Risk Mitigation:
- **Phased Approach**: Migrate incrementally with validation at each phase
- **Comprehensive Testing**: Maintain test coverage throughout migration
- **Frontend Separation**: Frontend remains fully functional during backend migration
- **Rollback Plan**: Maintain current codebase as fallback during migration

## Technical Specifications

### Data Access Pattern:
```python
# ONLY this pattern allowed
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.core.database_unified import get_cosmos_service

# Repository injection
async def get_cosmos_repository() -> UnifiedCosmosRepository:
    return get_cosmos_service().get_repository()
```

### Service Pattern:
```python
# Domain Service Pattern
class TripDomainService:
    def __init__(self, cosmos_repository: UnifiedCosmosRepository):
        self._cosmos_repo = cosmos_repository
    
    async def create_trip(self, trip_data: TripCreate) -> TripResponse:
        # Domain logic here
        pass

# Use Case Pattern
class CreateTripUseCase:
    def __init__(self, trip_service: TripDomainService):
        self._trip_service = trip_service
    
    async def execute(self, trip_data: TripCreate) -> TripResponse:
        return await self._trip_service.create_trip(trip_data)
```

### API Pattern:
```python
# API Endpoint Pattern
@router.post("/trips", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    use_case: CreateTripUseCase = Depends(get_create_trip_use_case)
) -> TripResponse:
    return await use_case.execute(trip_data)
```

## Compliance Validation

### Architectural Constraints:
- **No SQL Dependencies**: No SQLAlchemy imports anywhere in codebase
- **Single Data Access**: Only `UnifiedCosmosRepository` for data operations
- **Service Layer**: Only domain services + use cases for business logic
- **Dependency Direction**: API → Application → Domain → Infrastructure

### Validation Tools:
- **Import Linter**: Validate dependency direction and prevent circular imports
- **Architecture Tests**: Automated tests to ensure pattern compliance
- **Code Review**: Mandatory architectural review for all changes
- **CI/CD Validation**: Automated architectural compliance checking

## Approval

This ADR represents a critical architectural decision that will require:
- **Full Backend Reconstruction**: 7-10 days of intensive development
- **Comprehensive Testing**: Validation of all features and performance
- **Team Alignment**: Agreement on architectural patterns and standards
- **Risk Acceptance**: Acknowledge temporary disruption for long-term benefits

**Recommendation**: Approve and begin immediate implementation to resolve the architectural crisis and establish a maintainable, scalable foundation for the Pathfinder application.
