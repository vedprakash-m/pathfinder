"""
Test with proper JWT tokens for authentication.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.core.security import User, create_access_token
from app.core.config import get_settings
from uuid import uuid4
import jwt


def test_trips_with_valid_jwt():
    """Test trip creation with a valid JWT token."""
    
    settings = get_settings()
    
    # Create a test user
    test_user_id = str(uuid4())
    test_user = User(
        id=test_user_id,
        email="test@example.com",
        roles=["user"],
        permissions=["create:trips"]
    )
    
    # Create a valid JWT token
    token_data = {
        "sub": test_user_id,
        "email": "test@example.com",
        "https://pathfinder.app/roles": ["user"],
        "https://pathfinder.app/permissions": ["create:trips", "read:trips", "update:trips", "delete:trips"]
    }
    
    valid_token = create_access_token(token_data)
    print(f"Created token: {valid_token}")
    
    # Mock the authentication to return our test user
    async def mock_auth(*args, **kwargs):
        return test_user
    
    with patch("app.core.zero_trust.require_permissions", return_value=mock_auth):
        with patch("app.api.trips.require_permissions", return_value=mock_auth):
            
            client = TestClient(app)
            
            # Get CSRF token first
            csrf_response = client.get("/health")
            csrf_token = csrf_response.headers.get("x-csrf-token")
            
            trip_data = {
                "name": "Test Trip",
                "description": "Test description",
                "destination": "Test Destination",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "budget_total": 5000.00,
                "is_public": False,
            }
            
            headers = {
                "Authorization": f"Bearer {valid_token}",
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json"
            }
            
            response = client.post("/api/v1/trips", json=trip_data, headers=headers)
            
            print(f"Valid JWT response status: {response.status_code}")
            print(f"Valid JWT response content: {response.content}")
            
            # Should not be an auth error
            assert response.status_code not in [401, 403]


def test_trips_with_mocked_verify_token():
    """Test by directly mocking the verify_token function."""
    
    from app.core.security import TokenData
    
    # Create mock token data
    test_user_id = str(uuid4())
    mock_token_data = TokenData(
        sub=test_user_id,
        email="test@example.com",
        roles=["user"],
        permissions=["create:trips", "read:trips", "update:trips", "delete:trips"]
    )
    
    # Mock verify_token to return our token data
    with patch("app.core.zero_trust.verify_token", return_value=mock_token_data):
        with patch("app.core.security.verify_token", return_value=mock_token_data):
            
            client = TestClient(app)
            
            # Get CSRF token first
            csrf_response = client.get("/health")
            csrf_token = csrf_response.headers.get("x-csrf-token")
            
            trip_data = {
                "name": "Test Trip",
                "description": "Test description",
                "destination": "Test Destination",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "budget_total": 5000.00,
                "is_public": False,
            }
            
            headers = {
                "Authorization": "Bearer valid-token",  # Any token will work now
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json"
            }
            
            response = client.post("/api/v1/trips", json=trip_data, headers=headers)
            
            print(f"Mocked verify_token response status: {response.status_code}")
            print(f"Mocked verify_token response content: {response.content}")
            
            # Should not be an auth error
            assert response.status_code not in [401, 403]


def test_token_verification_directly():
    """Test token creation and verification directly."""
    
    import asyncio
    from app.core.security import verify_token
    
    settings = get_settings()
    
    # Create a token
    token_data = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "https://pathfinder.app/roles": ["user"],
        "https://pathfinder.app/permissions": ["create:trips"]
    }
    
    token = create_access_token(token_data)
    print(f"Token created: {token}")
    
    # Try to verify it
    async def verify_async():
        try:
            verified_data = await verify_token(token)
            print(f"Token verified successfully: {verified_data}")
            
            assert verified_data.sub == "test-user-123"
            assert verified_data.email == "test@example.com"
            return True
            
        except Exception as e:
            print(f"Token verification failed: {e}")
            return False
    
    # Run the async verification
    result = asyncio.run(verify_async())
    assert result, "Token verification should work"

@pytest.mark.asyncio
async def test_async_token_verification():
    """Test async token verification."""
    
    from app.core.security import verify_token
    
    # Create a token
    token_data = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "https://pathfinder.app/roles": ["user"],
        "https://pathfinder.app/permissions": ["create:trips"]
    }
    
    token = create_access_token(token_data)
    print(f"Async test - Token created: {token}")
    
    try:
        verified_data = await verify_token(token)
        print(f"Async test - Token verified: {verified_data}")
        
        assert verified_data.sub == "test-user-123"
        assert verified_data.email == "test@example.com"
        
    except Exception as e:
        print(f"Async test - Token verification failed: {e}")
        pytest.fail(f"Token verification should work: {e}")
