"""
Test trip endpoints with minimal authentication bypass for unit testing.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.core.security import VedUser
from app.core.config import get_settings
from uuid import uuid4
import jwt
from datetime import datetime, timedelta


def create_valid_jwt_token(user_data: dict) -> str:
    """Create a valid JWT token for testing."""
    payload = {
        "sub": user_data.get("id", str(uuid4())),
        "email": user_data.get("email", "test@example.com"),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "https://pathfinder.app/roles": user_data.get("roles", ["user"]),
        "https://pathfinder.app/permissions": user_data.get("permissions", [
            "read:trips", "create:trips", "update:trips", "delete:trips"
        ])
    }
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


@pytest.fixture
def simple_client():
    """Create a test client with minimal setup."""
    return TestClient(app)


def test_trips_with_proper_auth_bypass(simple_client):
    """Test trip creation with proper FastAPI security bypass using valid JWT."""
    
    # Set environment to testing first
    original_env = os.environ.get('ENVIRONMENT')
    os.environ['ENVIRONMENT'] = 'testing'
    
    try:
        # Clear the cached settings
        get_settings.cache_clear()
        
        # Create a test user
        test_user_data = {
            "id": str(uuid4()),
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["create:trips", "read:trips", "update:trips", "delete:trips"],
        }
        
        # Create a valid JWT token
        valid_jwt_token = create_valid_jwt_token(test_user_data)
        
        # Import the actual security dependency
        from app.core.zero_trust import security
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Mock credentials with valid JWT token
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_jwt_token
        )
        
        # Mock the security dependency to return our mock credentials
        def mock_security():
            return mock_credentials
        
        # Force reload the settings module with test environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing', 'SECRET_KEY': 'test-secret-key'}):
            get_settings.cache_clear()  # Clear cache again to pick up env changes
            
            # Override the security dependency
            app.dependency_overrides[security] = mock_security
            
            try:
                trip_data = {
                    "name": "Test Trip",
                    "description": "Test description", 
                    "destination": "Test Destination",
                    "start_date": "2025-07-01",
                    "end_date": "2025-07-15",
                    "budget_total": 5000.00,
                    "is_public": False,
                }
                
                response = simple_client.post("/api/v1/trips", json=trip_data)
                
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.content}")
                
                # Should not be an auth error
                assert response.status_code not in [401, 403]
                
            finally:
                # Clean up
                app.dependency_overrides.clear()
                
    finally:
        # Restore environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        else:
            os.environ.pop('ENVIRONMENT', None)
        get_settings.cache_clear()


def test_trips_with_environment_bypass():
    """Test with environment-based auth bypass using valid JWT."""
    
    # Set testing environment  
    original_env = os.environ.get('ENVIRONMENT')
    original_secret = os.environ.get('SECRET_KEY')
    
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    try:
        # Clear cached settings to pick up environment changes
        get_settings.cache_clear()
        
        # Create test user data
        test_user_data = {
            "id": str(uuid4()),
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["create:trips", "read:trips", "update:trips", "delete:trips"],
        }
        
        # Create valid JWT token
        valid_jwt_token = create_valid_jwt_token(test_user_data)
        
        # Mock the security dependencies
        from app.core.zero_trust import security
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials=valid_jwt_token
        )
        
        def mock_security():
            return mock_credentials
            
        app.dependency_overrides[security] = mock_security
        
        try:
            client = TestClient(app)
            
            trip_data = {
                "name": "Test Trip",
                "description": "Test description",
                "destination": "Test Destination", 
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "budget_total": 5000.00,
                "is_public": False,
            }
            
            response = client.post("/api/v1/trips", json=trip_data)
            
            print(f"Environment bypass response status: {response.status_code}")
            print(f"Environment bypass response content: {response.content}")
            
            # Should not get auth errors
            assert response.status_code not in [401, 403]
            
        finally:
            app.dependency_overrides.clear()
                
    finally:
        # Restore environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        else:
            os.environ.pop('ENVIRONMENT', None)
            
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        else:
            os.environ.pop('SECRET_KEY', None)
            
        get_settings.cache_clear()


def test_check_auth_with_complete_mock_stack():
    """Test using complete mock of the entire auth stack with valid JWT."""
    
    # Set up test environment
    original_env = os.environ.get('ENVIRONMENT')
    original_secret = os.environ.get('SECRET_KEY')
    
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    try:
        # Clear cached settings
        get_settings.cache_clear()
        
        test_user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["create:trips"],
        }
        
        # Create valid JWT token
        valid_jwt_token = create_valid_jwt_token(test_user_data)
        
        # Import all the auth components we need to mock
        from app.core.zero_trust import security, zero_trust_security
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_jwt_token
        )
        
        def mock_security():
            return mock_credentials
        
        # Mock the zero trust security verification
        with patch.object(zero_trust_security, 'verify_access', return_value=True):
            
            app.dependency_overrides[security] = mock_security
            
            try:
                client = TestClient(app)
                
                trip_data = {
                    "name": "Test Trip",
                    "description": "Test description",
                    "destination": "Test Destination",
                    "start_date": "2025-07-01", 
                    "end_date": "2025-07-15",
                    "budget_total": 5000.00,
                    "is_public": False,
                }
                
                response = client.post("/api/v1/trips", json=trip_data)
                
                print(f"Complete mock response status: {response.status_code}")
                print(f"Complete mock response content: {response.content}")
                
                # Should not get auth errors
                assert response.status_code not in [401, 403]
                
            finally:
                app.dependency_overrides.clear()
                
    finally:
        # Restore environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        else:
            os.environ.pop('ENVIRONMENT', None)
            
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        else:
            os.environ.pop('SECRET_KEY', None)
            
        get_settings.cache_clear()
