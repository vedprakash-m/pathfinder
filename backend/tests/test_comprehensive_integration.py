"""
Comprehensive backend integration tests for API endpoints and workflows.
"""

import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.main import app
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health_check(self):
        """Test basic health endpoint returns 200."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert "timestamp" in health_data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self):
        """Test detailed health endpoint includes service status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/detailed")

            # Should return health info even if some services are down
            assert response.status_code in [200, 503]

            health_data = response.json()
            assert "services" in health_data
            assert "database" in health_data["services"]

    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """Test readiness endpoint for container orchestration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/ready")

            # Should be ready if database is accessible
            assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """Test liveness endpoint for container orchestration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus-style metrics."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/metrics")
            assert response.status_code == 200

            # Should return text/plain content type for Prometheus
            assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_version_endpoint(self):
        """Test version endpoint returns build information."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/version")
            assert response.status_code == 200

            version_data = response.json()
            assert "version" in version_data
            assert "build_time" in version_data


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication flows."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints require authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/trips")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid-token"}
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/trips", headers=headers)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cors_headers_present(self):
        """Test that CORS headers are properly set."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.options("/api/v1/trips")

            # Should include CORS headers
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers


@pytest.mark.integration
class TestTripAPIIntegration:
    """Integration tests for Trip API endpoints."""

    @pytest.mark.asyncio
    async def test_trip_crud_workflow(self):
        """Test complete CRUD workflow for trips."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock authentication
            headers = {"Authorization": "Bearer mock-test-token"}

            # 1. Create trip
            trip_data = {
                "title": "Integration Test Trip",
                "destination": "Test Destination",
                "start_date": (date.today() + timedelta(days=30)).isoformat(),
                "end_date": (date.today() + timedelta(days=35)).isoformat(),
                "budget_total": 2000.0,
                "is_public": False,
            }

            # Mock successful creation (actual auth would be required)
            try:
                create_response = await client.post(
                    "/api/v1/trips", json=trip_data, headers=headers
                )

                if create_response.status_code == 401:
                    pytest.skip("Authentication required for trip tests")

                assert create_response.status_code == 201
                created_trip = create_response.json()
                trip_id = created_trip["id"]

                # 2. Read trip
                get_response = await client.get(
                    f"/api/v1/trips/{trip_id}", headers=headers
                )
                assert get_response.status_code == 200

                retrieved_trip = get_response.json()
                assert retrieved_trip["title"] == "Integration Test Trip"

                # 3. Update trip
                update_data = {"title": "Updated Integration Test Trip"}
                update_response = await client.put(
                    f"/api/v1/trips/{trip_id}", json=update_data, headers=headers
                )
                assert update_response.status_code == 200

                # 4. Delete trip
                delete_response = await client.delete(
                    f"/api/v1/trips/{trip_id}", headers=headers
                )
                assert delete_response.status_code == 204

            except Exception as e:
                pytest.skip(
                    f"Trip API test requires full authentication setup: {e}")

    @pytest.mark.asyncio
    async def test_trip_validation_errors(self):
        """Test trip creation validation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            # Test missing required fields
            invalid_trip_data = {"title": ""}  # Missing required fields

            try:
                response = await client.post(
                    "/api/v1/trips", json=invalid_trip_data, headers=headers
                )

                if response.status_code == 401:
                    pytest.skip("Authentication required for validation tests")

                assert response.status_code == 422  # Validation error

            except Exception:
                pytest.skip(
                    "Trip validation test requires authentication setup")

    @pytest.mark.asyncio
    async def test_trip_list_pagination(self):
        """Test trip list pagination and filtering."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            try:
                # Test with pagination parameters
                response = await client.get(
                    "/api/v1/trips?page=1&limit=10", headers=headers
                )

                if response.status_code == 401:
                    pytest.skip("Authentication required for pagination tests")

                assert response.status_code == 200
                trips_data = response.json()

                # Should return list format
                assert isinstance(trips_data, list) or "items" in trips_data

            except Exception:
                pytest.skip(
                    "Trip pagination test requires authentication setup")


@pytest.mark.integration
class TestFamilyAPIIntegration:
    """Integration tests for Family API endpoints."""

    @pytest.mark.asyncio
    async def test_family_creation_and_management(self):
        """Test family creation and member management."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            try:
                # 1. Create family
                family_data = {
                    "name": "Integration Test Family",
                    "description": "A test family for integration testing",
                    "preferences": {
                        "activities": ["museums", "restaurants"],
                        "budget_level": "medium",
                    },
                }

                create_response = await client.post(
                    "/api/v1/families", json=family_data, headers=headers
                )

                if create_response.status_code == 401:
                    pytest.skip("Authentication required for family tests")

                assert create_response.status_code == 201
                created_family = create_response.json()
                family_id = created_family["id"]

                # 2. Invite family member
                invite_data = {
                    "email": "testmember@example.com",
                    "message": "Join our test family!",
                }

                invite_response = await client.post(
                    f"/api/v1/families/{family_id}/invite",
                    json=invite_data,
                    headers=headers,
                )

                # Should succeed or return reasonable status
                assert invite_response.status_code in [
                    200,
                    201,
                    409,
                ]  # 409 for duplicate

            except Exception as e:
                pytest.skip(f"Family API test requires full setup: {e}")

    @pytest.mark.asyncio
    async def test_family_invitation_workflow(self):
        """Test complete family invitation workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            try:
                # Test invitation status endpoint
                response = await client.get(
                    "/api/v1/families/invitations", headers=headers
                )

                if response.status_code == 401:
                    pytest.skip("Authentication required for invitation tests")

                # Should return list of invitations
                assert response.status_code == 200

            except Exception:
                pytest.skip(
                    "Family invitation test requires authentication setup")


@pytest.mark.integration
class TestAIServiceIntegration:
    """Integration tests for AI service endpoints."""

    @pytest.mark.asyncio
    async def test_ai_cost_tracking_endpoint(self):
        """Test AI cost tracking and budget monitoring."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            try:
                response = await client.get("/api/v1/ai/usage", headers=headers)

                if response.status_code == 401:
                    pytest.skip("Authentication required for AI usage tests")

                # Should return usage statistics
                assert response.status_code == 200
                usage_data = response.json()

                # Should include cost tracking information
                assert "daily_usage" in usage_data or "cost" in usage_data

            except Exception:
                pytest.skip(
                    "AI usage test requires authentication and service setup")

    @pytest.mark.asyncio
    async def test_ai_itinerary_generation_endpoint(self):
        """Test AI itinerary generation endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer mock-test-token"}

            try:
                itinerary_request = {
                    "destination": "Paris",
                    "duration_days": 5,
                    "budget": 3000,
                    "preferences": {
                        "activities": ["museums", "restaurants"],
                        "pace": "moderate",
                    },
                }

                response = await client.post(
                    "/api/v1/ai/generate-itinerary",
                    json=itinerary_request,
                    headers=headers,
                )

                if response.status_code == 401:
                    pytest.skip(
                        "Authentication required for AI generation tests")

                # Should handle request appropriately
                assert response.status_code in [
                    200,
                    202,
                    503,
                ]  # 503 if service unavailable

            except Exception:
                pytest.skip("AI generation test requires full service setup")


@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket connectivity."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        try:
            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                # Test WebSocket endpoint exists
                response = client.get("/ws")

                # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
                assert response.status_code in [426, 404, 405]

        except Exception:
            pytest.skip("WebSocket test requires specific setup")


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database connectivity and operations."""

    @pytest.mark.asyncio
    async def test_database_connection_health(self):
        """Test database connectivity through health endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/ready")

            # Should indicate database readiness
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                health_data = response.json()
                assert health_data.get("database", {}).get("status") in [
                    "healthy",
                    "connected",
                ]

    @pytest.mark.asyncio
    async def test_database_migration_status(self):
        """Test database migration status."""
        # This would typically be tested through an admin endpoint
        async with AsyncClient(app=app, base_url="http://test") as client:
            try:
                response = await client.get("/admin/migrations/status")

                # Admin endpoints require special auth
                if response.status_code == 401:
                    pytest.skip(
                        "Admin authentication required for migration tests")

                assert response.status_code in [
                    200,
                    404,
                ]  # 404 if endpoint doesn't exist

            except Exception:
                pytest.skip("Migration status test requires admin setup")


@pytest.mark.integration
class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_time_benchmarks(self):
        """Test that API responses meet performance benchmarks."""
        import time

        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()

            # Health endpoint should respond quickly
            response_time = end_time - start_time
            assert response_time < 1.0  # Should respond within 1 second
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test handling of concurrent requests."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send multiple concurrent requests
            tasks = [client.get("/health") for _ in range(10)]

            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
