#!/usr/bin/env python3
"""
AI Service Test Fixes
====================

This script fixes test mocking issues for AI service tests to work properly
in CI/CD environments where OpenAI client might be None.
"""

import re


def fix_ai_service_tests():
    """Fix AI service test mocking to work with None client."""

    test_file = "/Users/vedprakashmishra/pathfinder/backend/tests/test_ai_service.py"

    # Read the current file
    with open(test_file, "r") as f:
        content = f.read()

    # Replace client import to avoid None issues
    content = content.replace(
        "from app.services.ai_service import AIService, CostTracker, ItineraryPrompts",
        "from app.services.ai_service import AIService, CostTracker, ItineraryPrompts\nfrom app.services import ai_service",
    )

    # Fix the mocking pattern to mock the service's _make_api_call method instead
    # This is more robust than trying to mock the global client
    old_pattern = r'with patch\.object\(client\.chat\.completions, "create"\) as mock_create:'
    new_pattern = 'with patch.object(ai_service.AIService, "_make_api_call") as mock_api_call:'

    content = re.sub(old_pattern, new_pattern, content)

    # Fix the mock setup
    content = content.replace(
        "mock_create.return_value = mock_openai_response",
        "mock_api_call.return_value = mock_openai_response",
    )

    # Write the fixed content back
    with open(test_file, "w") as f:
        f.write(content)

    print("✅ Fixed AI service test mocking patterns")


if __name__ == "__main__":
    fix_ai_service_tests()
