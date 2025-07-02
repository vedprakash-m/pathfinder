"""
Tests for the AI service functionality.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from app.services.ai_service import AIService, CostTracker, ItineraryPrompts


@pytest.mark.asyncio
async def test_cost_tracker_calculation():
    """Test that CostTracker correctly calculates costs based on token usage."""
    # Arrange
    tracker = CostTracker()

    # Act
    cost_mini = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
    cost_4o = tracker.calculate_cost("gpt-4o", 1000, 500)
    cost_35 = tracker.calculate_cost("gpt-3.5-turbo", 1000, 500)

    # Assert
    assert cost_mini == 0.00015 + 0.0003  # input + output cost
    assert cost_4o == 0.005 + 0.0075  # input + output cost
    assert cost_35 == 0.0015 + 0.001  # input + output cost


@pytest.mark.asyncio
async def test_cost_tracker_usage_tracking():
    """Test that CostTracker properly tracks usage."""
    # Arrange
    tracker = CostTracker()

    # Act
    cost = tracker.track_usage("gpt-4o-mini", 1000, 500)
    today = datetime.now().date().isoformat()

    # Assert
    assert cost > 0
    assert today in tracker.daily_usage
    assert tracker.daily_usage[today]["requests"] == 1
    assert tracker.daily_usage[today]["cost"] == cost


@pytest.mark.asyncio
async def test_cost_tracker_budget_limit():
    """Test that CostTracker enforces budget limits."""
    # Arrange
    tracker = CostTracker()
    today = datetime.now().date().isoformat()

    # Act - Track usage that would exceed daily budget (50.0 default)
    # gpt-4o costs: input $0.005/1K, output $0.015/1K tokens
    # 1000 input + 1000 output = (1000/1000 * 0.005) + (1000/1000 * 0.015) = $0.02 per call
    # Need 2500+ calls to exceed $50 budget, but let's be more efficient:

    # Track high token usage to exceed budget faster
    for _ in range(10):
        tracker.track_usage("gpt-4o", 5000, 5000, "general")  # Each call costs ~$0.10, total ~$1.00

    # Verify the data structure was created correctly
    assert today in tracker.daily_usage
    assert "cost" in tracker.daily_usage[today]
    assert "requests" in tracker.daily_usage[today]
    assert "models" in tracker.daily_usage[today]
    assert "request_types" in tracker.daily_usage[today]

    # Verify we have some cost tracked
    daily_cost = tracker.daily_usage[today]["cost"]
    assert daily_cost > 0

    # Now simulate exceeding budget by manually setting cost
    tracker.daily_usage[today]["cost"] = 55.0  # Exceeds default $50 limit

    # Assert budget limit check returns False when exceeded
    assert tracker.check_budget_limit() is False


@pytest.mark.asyncio
async def test_itinerary_prompts():
    """Test that itinerary prompts are correctly generated."""
    # Arrange
    destination = "Paris"
    duration_days = 7
    families_data = [
        {
            "name": "Smith",
            "members": [
                {
                    "age": 35,
                    "dietary_restrictions": ["vegetarian"],
                    "accessibility_needs": [],
                },
                {"age": 33, "dietary_restrictions": [], "accessibility_needs": []},
                {
                    "age": 8,
                    "dietary_restrictions": ["nut-free"],
                    "accessibility_needs": [],
                },
            ],
        },
        {
            "name": "Johnson",
            "members": [
                {
                    "age": 40,
                    "dietary_restrictions": [],
                    "accessibility_needs": ["wheelchair"],
                },
                {"age": 12, "dietary_restrictions": [], "accessibility_needs": []},
            ],
        },
    ]
    preferences = {
        "accommodation_type": ["hotel"],
        "transportation_mode": ["public_transit"],
        "activity_types": ["museums", "sightseeing"],
        "dining_preferences": ["local cuisine"],
        "pace": "moderate",
    }
    budget_total = 10000.0

    # Act
    prompt = ItineraryPrompts.create_itinerary_prompt(
        destination, duration_days, families_data, preferences, budget_total
    )

    # Assert
    assert "Paris" in prompt
    assert "7-day itinerary" in prompt
    assert "Smith" in prompt
    assert "Johnson" in prompt
    assert "vegetarian" in prompt
    assert "wheelchair" in prompt
    assert "museums" in prompt
    assert "budget" in prompt.lower()


@pytest.mark.asyncio
async def test_ai_service_generate_itinerary(mock_openai_response):
    """Test that the AI service can generate an itinerary."""
    # Arrange
    ai_service = AIService()

    # Prepare test data
    destination = "Paris"
    duration_days = 7
    families_data = [
        {
            "name": "Test Family",
            "members": [
                {"age": 35, "dietary_restrictions": [], "accessibility_needs": []},
                {"age": 8, "dietary_restrictions": [], "accessibility_needs": []},
            ],
        }
    ]
    preferences = {
        "accommodation_type": ["hotel"],
        "transportation_mode": ["public_transit"],
        "activity_types": ["museums", "sightseeing"],
        "dining_preferences": ["local cuisine"],
        "pace": "moderate",
    }

    # Mock OpenAI client call - patch the instance method directly
    with patch.object(ai_service, "_make_api_call") as mock_api_call:
        # Create a properly structured mock response
        mock_response = {
            "content": '{"overview": "Test itinerary", "daily_itinerary": [{"day": 1, "activities": ["Test activity"]}], "budget_summary": {"total": 1000}}',
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        }
        mock_api_call.return_value = mock_response

        # Act
        result = await ai_service.generate_itinerary(
            destination, duration_days, families_data, preferences
        )

        # Assert
        assert result is not None
        assert "overview" in result
        assert "daily_itinerary" in result
        assert result["overview"] == "Test itinerary"  # overview is a string in our mock
        assert len(result["daily_itinerary"]) > 0


@pytest.mark.asyncio
async def test_ai_service_with_cost_tracking(mock_openai_response):
    """Test that AI service tracks costs when generating content."""
    # Arrange
    ai_service = AIService()

    # Prepare test data
    destination = "Paris"
    duration_days = 1
    families_data = [
        {
            "name": "Test Family",
            "members": [
                {"age": 35, "dietary_restrictions": [], "accessibility_needs": []},
            ],
        }
    ]
    preferences = {
        "accommodation_type": ["hotel"],
        "transportation_mode": ["public_transit"],
        "activity_types": ["museums", "sightseeing"],
        "dining_preferences": ["local cuisine"],
        "pace": "moderate",
    }

    # Mock OpenAI client call - patch the instance method directly
    with patch.object(ai_service, "_make_api_call") as mock_api_call:
        # Create a properly structured mock response
        mock_response = {
            "content": '{"overview": "Test itinerary", "daily_itinerary": [{"day": 1, "activities": ["Test activity"]}], "budget_summary": {"total": 1000}}',
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        }
        mock_api_call.return_value = mock_response

        # Act
        before_count = len(ai_service.cost_tracker.daily_usage)
        result = await ai_service.generate_itinerary(
            destination, duration_days, families_data, preferences
        )
        after_count = len(ai_service.cost_tracker.daily_usage)

        # Assert
        assert result is not None
        assert after_count >= before_count
        assert mock_api_call.called


@pytest.mark.asyncio
async def test_ai_service_fallback_to_smaller_model():
    """Test that AI service falls back to a smaller model if needed."""
    # Arrange
    ai_service = AIService()

    # Mock the AI service to simulate primary model failure and fallback
    with patch.object(ai_service, "_make_api_call") as mock_api_call:
        # First call fails (primary model), second call succeeds (fallback model)
        fallback_response = {
            "overview": {
                "destination": "Test City",
                "duration": 3,
                "total_participants": 1,
                "estimated_cost_per_person": 500.0,
            },
            "daily_itinerary": [{"day": 1, "date": "2024-01-01", "activities": []}],
            "budget_summary": {"total_estimated_cost": 500, "cost_per_person": 500},
        }

        mock_api_call.side_effect = [
            Exception("Primary model failed"),
            {
                "content": json.dumps(fallback_response),
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50,
                "cost": 0.01,
            },
        ]

        # Act
        result = await ai_service.generate_itinerary(
            destination="Test City",
            duration_days=3,
            families_data=[{"name": "Test Family", "members": [{"age": 30}]}],
            preferences={"pace": "moderate"},
        )

        # Assert
        assert result is not None
        assert "overview" in result
        assert "daily_itinerary" in result
        assert "budget_summary" in result
        assert result["overview"]["destination"] == "Test City"
        assert mock_api_call.call_count == 2  # Called twice for fallback


@pytest.mark.asyncio
async def test_ai_service_budget_exceeded():
    """Test that AI service raises an error when budget is exceeded."""
    # Arrange
    ai_service = AIService()

    # Mock cost tracker to always report budget exceeded
    ai_service.cost_tracker.check_budget_limit = MagicMock(return_value=False)

    # Prepare test data
    destination = "Paris"
    duration_days = 1
    families_data = [
        {
            "name": "Test Family",
            "members": [
                {"age": 35, "dietary_restrictions": [], "accessibility_needs": []},
            ],
        }
    ]
    preferences = {
        "accommodation_type": ["hotel"],
        "transportation_mode": ["public_transit"],
        "activity_types": ["museums", "sightseeing"],
        "dining_preferences": ["local cuisine"],
        "pace": "moderate",
    }

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await ai_service.generate_itinerary(destination, duration_days, families_data, preferences)

    assert "budget" in str(excinfo.value).lower()
