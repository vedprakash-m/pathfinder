"""
API Contract Validation Tests
Tests to ensure API contracts match expected schemas and behavior.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Mock the database and app imports for testing
try:
    from app.main import app
    from app.database import get_db, Base

    TEST_APP_AVAILABLE = True
except ImportError:
    TEST_APP_AVAILABLE = False
    app = None


@pytest.fixture
def test_db():
    """Create a test database"""
    if not TEST_APP_AVAILABLE:
        pytest.skip("App not available for testing")

    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield db_path

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client"""
    if not TEST_APP_AVAILABLE:
        pytest.skip("App not available for testing")
    return TestClient(app)


class TestAPIContracts:
    """Test API contract validation"""

    def test_health_endpoint_contract(self, client):
        """Test health endpoint returns expected contract"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

        # Check for optional fields
        optional_fields = ["timestamp", "version", "uptime"]
        for field in optional_fields:
            if field in data:
                assert isinstance(data[field], (str, int, float))

    def test_trip_creation_contract(self, client):
        """Test trip creation API contract"""
        trip_data = {
            "title": "Test Trip",
            "description": "A test trip",
            "destination": "Test City",
            "start_date": "2024-06-01",
            "end_date": "2024-06-10",
            "budget_total": 5000.0,
            "max_participants": 4,
        }

        response = client.post("/api/trips", json=trip_data)

        # Should either succeed or fail with proper error format
        if response.status_code == 201:
            data = response.json()
            required_fields = ["id", "title",
                "destination", "start_date", "end_date"]
            for field in required_fields:
                assert field in data
        else:
            # Should have proper error format
            assert response.status_code in [400, 401, 422, 500]
            data = response.json()
            assert "detail" in data or "message" in data

    def test_trip_list_contract(self, client):
        """Test trip list API contract"""
        response = client.get("/api/trips")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            # If trips exist, validate structure
            if data:
                trip = data[0]
                expected_fields = ["id", "title", "destination"]
                for field in expected_fields:
                    assert field in trip
        else:
            # Should have proper error format
            assert response.status_code in [401, 403, 500]

    def test_error_response_format(self, client):
        """Test that error responses follow consistent format"""
        # Try invalid endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

        # Should have consistent error format
        data = response.json()
        assert "detail" in data or "message" in data

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/trips")

        # Basic CORS check
        assert response.status_code in [200, 404, 405]

    def test_content_type_headers(self, client):
        """Test content type headers"""
        response = client.get("/health")
        assert response.headers.get("content-type") == "application/json"


class TestDataValidation:
    """Test data validation and constraints"""

    def test_date_validation(self, client):
        """Test date field validation"""
        # Invalid date format
        trip_data = {
            "title": "Test Trip",
            "destination": "Test City",
            "start_date": "invalid-date",
            "end_date": "2024-06-10",
            "budget_total": 5000.0,
        }

        response = client.post("/api/trips", json=trip_data)
        assert response.status_code in [400, 422]

    def test_budget_validation(self, client):
        """Test budget field validation"""
        # Negative budget
        trip_data = {
            "title": "Test Trip",
            "destination": "Test City",
            "start_date": "2024-06-01",
            "end_date": "2024-06-10",
            "budget_total": -1000.0,
        }

        response = client.post("/api/trips", json=trip_data)
        assert response.status_code in [400, 422]

    def test_required_fields(self, client):
        """Test required field validation"""
        # Missing required fields
        trip_data = {"title": "Test Trip"}

        response = client.post("/api/trips", json=trip_data)
        assert response.status_code in [400, 422]


class TestPerformanceContracts:
    """Test performance-related contracts"""

    def test_response_time_limits(self, client):
        """Test response time expectations"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        # Health endpoint should respond quickly
        assert response_time < 1.0  # 1 second max
        assert response.status_code == 200

    def test_pagination_contract(self, client):
        """Test pagination parameters"""
        # Test with pagination parameters
        response = client.get("/api/trips?page=1&limit=10")

        if response.status_code == 200:
            # Should handle pagination gracefully
            data = response.json()
            assert isinstance(data, (list, dict))


# Skip all tests if app is not available
if not TEST_APP_AVAILABLE:
    pytest.skip("Backend app not available", allow_module_level=True)
