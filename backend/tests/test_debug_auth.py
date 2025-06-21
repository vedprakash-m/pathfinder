"""
Debug authentication issue
"""

import pytest
from app.main import app
from fastapi import status
from fastapi.testclient import TestClient


def test_debug_authenticated_response(authenticated_client):
    """Debug the authenticated response."""
    response = authenticated_client.get("/api/v1/trips")

    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    print(f"Response Headers: {dict(response.headers)}")

    # For now, just document what we get
    assert True  # Always pass for debugging


def test_debug_unauthenticated_response():
    """Debug the unauthenticated response."""
    client = TestClient(app)
    response = client.get("/api/v1/trips")

    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    print(f"Response Headers: {dict(response.headers)}")

    # For now, just document what we get
    assert True  # Always pass for debugging
