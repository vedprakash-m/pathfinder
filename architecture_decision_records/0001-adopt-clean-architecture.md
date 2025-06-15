# 0001: Adopt Clean / Hexagonal Architecture

Date: 2025-05-01

## Status
Accepted

## Context
The Pathfinder codebase has organically evolved into a monolithic structure with tight coupling between API controllers, business logic, and infrastructure concerns. This impedes maintainability, scalability, and onboarding of new contributors.

## Decision
We will adopt Clean / Hexagonal Architecture with the following layers:

1. **Domain** – Pure business entities and rules.
2. **Application** – Use-case orchestrators and ports.
3. **Infrastructure** – Adapters for persistence, external services, and cross-cutting concerns.
4. **Interface** – REST, WebSocket, and scheduled adapters.

Rules:
* Dependencies must always point inwards (Interface → Application → Domain).
* Infrastructure may depend on Domain but not vice-versa.
* Shared cross-cutting code (logging, tracing) resides in `infra/observability`.

## Consequences
* Short-term increase in refactoring effort.
* Clear module boundaries will ease testing and future micro-service extraction.
* Allows Import-Linter to enforce layering contracts. 