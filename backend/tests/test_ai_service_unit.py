"""
Unit tests for AI service functionality.
"""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.ai_service import AIService


class TestAIServiceItineraryGeneration:
    """Test AI service itinerary generation."""

    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing."""
        return AIService()

    @pytest.fixture
    def sample_trip_data(self):
        """Sample trip data for testing."""
        return {
            "id": "trip-123",
            "title": "Family Road Trip",
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 7, 15),
            "destinations": ["San Francisco", "Los Angeles", "San Diego"],
            "participants": [
                {
                    "family_id": "family-1",
                    "family_name": "Smith Family",
                    "preferences": {
                        "activities": ["museums", "beaches", "restaurants"],
                        "budget_level": "medium",
                        "accessibility_needs": [],
                    },
                }
            ],
            "budget_total": 5000.0,
        }

    @pytest.fixture
    def sample_preferences(self):
        """Sample family preferences for testing."""
        return {
            "family-1": {
                "activities": ["museums", "outdoor_activities", "food_tours"],
                "budget_level": "medium",
                "accessibility_needs": ["wheelchair_accessible"],
                "dietary_restrictions": ["vegetarian"],
                "travel_style": "relaxed",
            },
            "family-2": {
                "activities": ["adventure_sports", "nightlife", "shopping"],
                "budget_level": "high",
                "accessibility_needs": [],
                "dietary_restrictions": [],
                "travel_style": "active",
            },
        }

    @pytest.mark.asyncio
    async def test_generate_itinerary_success(
        self, ai_service, sample_trip_data, sample_preferences
    ):
        """Test successful itinerary generation."""
        with patch("asyncio.to_thread") as mock_to_thread:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "overview": {
                        "destination": "San Francisco",
                        "duration": "7 days",
                        "total_cost": 1200.50,
                        "highlights": ["Golden Gate Bridge", "Alcatraz Island"],
                    },
                    "daily_itinerary": [
                        {
                            "day": 1,
                            "date": "2025-07-01",
                            "location": "San Francisco",
                            "activities": [
                                {
                                    "time": "09:00",
                                    "title": "Golden Gate Bridge Visit",
                                    "description": "Iconic bridge with stunning views",
                                    "duration": 120,
                                    "cost_estimate": 0,
                                }
                            ],
                        }
                    ],
                    "budget_summary": {
                        "total_estimated_cost": 1200.50,
                        "daily_breakdown": [85.50],
                        "categories": {
                            "accommodation": 600.0,
                            "food": 400.0,
                            "activities": 200.50,
                        },
                    },
                }
            )
            mock_response.usage = MagicMock()
            mock_response.usage.completion_tokens = 500

            mock_to_thread.return_value = mock_response

            # Generate itinerary
            result = await ai_service.generate_itinerary(
                destination="San Francisco",
                duration_days=7,
                families_data=[],
                preferences=sample_preferences,
            )

            # Assertions
            assert result is not None
            assert "overview" in result
            assert "daily_itinerary" in result
            assert "budget_summary" in result
            assert len(result["daily_itinerary"]) > 0
            assert "metadata" in result

            # Verify asyncio.to_thread was called
            mock_to_thread.assert_called_once()

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_generate_itinerary_api_error(
        self, mock_to_thread, ai_service, sample_trip_data, sample_preferences
    ):
        """Test itinerary generation with API error."""
        # Mock to_thread to raise an exception
        mock_to_thread.side_effect = Exception("API Error")

        # Extract parameters from trip data
        # Use first destination
        destination = sample_trip_data["destinations"][0]
        duration_days = (
            sample_trip_data["end_date"] - sample_trip_data["start_date"]
        ).days
        families_data = sample_trip_data["participants"]

        # Should handle the error gracefully
        with pytest.raises(Exception):
            await ai_service.generate_itinerary(
                destination, duration_days, families_data, sample_preferences
            )

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_generate_itinerary_invalid_response(
        self, mock_to_thread, ai_service, sample_trip_data, sample_preferences
    ):
        """Test itinerary generation with invalid AI response."""
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_response.usage = MagicMock()
        mock_response.usage.completion_tokens = 100

        mock_to_thread.return_value = mock_response

        # Extract parameters from trip data
        # Use first destination
        destination = sample_trip_data["destinations"][0]
        duration_days = (
            sample_trip_data["end_date"] - sample_trip_data["start_date"]
        ).days
        families_data = sample_trip_data["participants"]

        # Should handle invalid response
        with pytest.raises((json.JSONDecodeError, KeyError, ValueError)):
            await ai_service.generate_itinerary(
                destination, duration_days, families_data, sample_preferences
            )


class TestAIServiceRecommendations:
    """Test AI service recommendation functionality."""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_get_activity_recommendations(self, mock_to_thread, ai_service):
        """Test activity recommendations generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "recommendations": [
                    {
                        "title": "Alcatraz Island Tour",
                        "description": "Historic prison island with audio tours",
                        "category": "historical",
                        "duration": 180,
                        "cost_estimate": 45.0,
                        "rating": 4.5,
                        "family_friendly": True,
                        "accessibility": "Limited mobility access",
                    },
                    {
                        "title": "Fisherman's Wharf",
                        "description": "Waterfront area with shops and restaurants",
                        "category": "entertainment",
                        "duration": 120,
                        "cost_estimate": 30.0,
                        "rating": 4.2,
                        "family_friendly": True,
                        "accessibility": "Fully accessible",
                    },
                ]
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.completion_tokens = 300

        mock_to_thread.return_value = mock_response

        # Get recommendations
        location = "San Francisco"
        preferences = ["museums", "family_friendly", "accessible"]

        result = await ai_service.get_activity_recommendations(location, preferences)

        # Assertions
        assert result is not None
        assert "recommendations" in result
        assert len(result["recommendations"]) == 2
        assert all("title" in rec for rec in result["recommendations"])
        assert all("cost_estimate" in rec for rec in result["recommendations"])

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_get_restaurant_recommendations(self, mock_to_thread, ai_service):
        """Test restaurant recommendations generation."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "restaurants": [
                    {
                        "name": "Green's Restaurant",
                        "cuisine": "Vegetarian Fine Dining",
                        "price_range": "$$$$",
                        "rating": 4.7,
                        "address": "Building A, Fort Mason",
                        "dietary_accommodations": [
                            "vegetarian",
                            "vegan",
                            "gluten-free",
                        ],
                        "accessibility": "wheelchair_accessible",
                        "recommended_dishes": [
                            "Seasonal Vegetable Tasting",
                            "Wild Mushroom Risotto",
                        ],
                    }
                ]
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.completion_tokens = 250

        mock_to_thread.return_value = mock_response

        # Get restaurant recommendations
        location = "San Francisco"
        dietary_restrictions = ["vegetarian"]
        budget_level = "high"

        result = await ai_service.get_restaurant_recommendations(
            location, dietary_restrictions, budget_level
        )

        # Assertions
        assert result is not None
        assert "restaurants" in result
        assert len(result["restaurants"]) == 1
        restaurant = result["restaurants"][0]
        assert "name" in restaurant
        assert "cuisine" in restaurant
        assert "dietary_accommodations" in restaurant
        assert "vegetarian" in restaurant["dietary_accommodations"]


class TestAIServiceOptimization:
    """Test AI service optimization functionality."""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_optimize_route(self, mock_to_thread, ai_service):
        """Test route optimization."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "optimized_route": {
                    "total_distance": 450.2,
                    "total_drive_time": 360,  # minutes
                    "route_segments": [
                        {
                            "from": "San Francisco",
                            "to": "Monterey",
                            "distance": 120.5,
                            "drive_time": 135,
                            "scenic_route": True,
                            "ev_charging_stops": ["Gilroy", "Salinas"],
                        },
                        {
                            "from": "Monterey",
                            "to": "Los Angeles",
                            "distance": 329.7,
                            "drive_time": 225,
                            "scenic_route": False,
                            "ev_charging_stops": ["San Luis Obispo", "Santa Barbara"],
                        },
                    ],
                    "total_cost_estimate": 85.50,
                }
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.completion_tokens = 400

        mock_to_thread.return_value = mock_response

        # Optimize route
        destinations = ["San Francisco", "Monterey", "Los Angeles"]
        vehicle_constraints = {
            "ev_vehicles": True,
            "charging_range": 300,
            "prefer_scenic": True,
        }

        result = await ai_service.optimize_route(destinations, vehicle_constraints)

        # Assertions
        assert result is not None
        assert "optimized_route" in result
        route = result["optimized_route"]
        assert "total_distance" in route
        assert "route_segments" in route
        assert len(route["route_segments"]) == 2

        # Check EV charging considerations
        for segment in route["route_segments"]:
            assert "ev_charging_stops" in segment

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_optimize_budget_allocation(self, mock_to_thread, ai_service):
        """Test budget optimization."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "budget_allocation": {
                    "total_budget": 5000.0,
                    "categories": {
                        "accommodation": {
                            "amount": 2000.0,
                            "percentage": 40.0,
                            "recommendations": "Mid-range hotels and vacation rentals",
                        },
                        "food": {
                            "amount": 1250.0,
                            "percentage": 25.0,
                            "recommendations": "Mix of restaurants and grocery shopping",
                        },
                        "activities": {
                            "amount": 1000.0,
                            "percentage": 20.0,
                            "recommendations": "Entry fees, tours, and experiences",
                        },
                        "transportation": {
                            "amount": 500.0,
                            "percentage": 10.0,
                            "recommendations": "Gas, parking, and local transport",
                        },
                        "emergency": {
                            "amount": 250.0,
                            "percentage": 5.0,
                            "recommendations": "Unexpected expenses buffer",
                        },
                    },
                    "daily_budget": 333.33,
                    "savings_opportunities": [
                        "Book accommodations early for discounts",
                        "Look for family packages at attractions",
                    ],
                }
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.completion_tokens = 450

        mock_to_thread.return_value = mock_response

        # Optimize budget
        total_budget = 5000.0
        trip_duration = 15  # days
        family_count = 2

        result = await ai_service.optimize_budget_allocation(
            total_budget, trip_duration, family_count
        )

        # Assertions
        assert result is not None
        assert "budget_allocation" in result
        allocation = result["budget_allocation"]
        assert "total_budget" in allocation
        assert "categories" in allocation
        assert "daily_budget" in allocation
        assert allocation["total_budget"] == 5000.0

        # Check category allocations sum to total
        category_total = sum(cat["amount"]
                             for cat in allocation["categories"].values())
        assert abs(category_total - allocation["total_budget"]) < 0.01


class TestAIServiceErrorHandling:
    """Test AI service error handling."""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @pytest.mark.asyncio
    async def test_invalid_input_handling(self, ai_service):
        """Test handling of invalid input parameters."""
        # Test with None parameters
        with pytest.raises((ValueError, TypeError)):
            await ai_service.generate_itinerary(None, None, None, None)

        # Test with empty/invalid parameters
        with pytest.raises((ValueError, TypeError)):
            await ai_service.generate_itinerary("", 0, [], {})

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, mock_to_thread, ai_service):
        """Test handling of API timeouts."""
        # Mock timeout exception
        mock_to_thread.side_effect = TimeoutError("Request timeout")

        with pytest.raises(ValueError, match="AI service timeout"):
            await ai_service.generate_itinerary(
                "Paris", 3, [{"id": "family1"}], {"interests": ["culture"]}
            )

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_to_thread, ai_service):
        """Test handling of rate limit errors."""

        # Mock rate limit exception
        class RateLimitError(Exception):
            pass

        mock_to_thread.side_effect = RateLimitError("Rate limit exceeded")

        with pytest.raises(
            ValueError, match="AI service temporarily unavailable due to rate limits"
        ):
            await ai_service.generate_itinerary(
                "Paris", 3, [{"id": "family1"}], {"interests": ["culture"]}
            )


class TestAIServiceCostMonitoring:
    """Test AI service cost monitoring integration."""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @patch("asyncio.to_thread")
    @pytest.mark.asyncio
    async def test_cost_tracking_on_api_call(self, mock_to_thread, ai_service):
        """Test that API calls work with cost tracking."""
        # Mock OpenAI response with proper format
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "overview": {
                    "destination": "Paris",
                    "duration": "3 days",
                    "group_size": 2,
                    "total_budget": "$1000",
                },
                "daily_itinerary": [
                    {
                        "day": 1,
                        "date": "2024-01-01",
                        "activities": [
                            {
                                "name": "Test Activity",
                                "time": "10:00",
                                "description": "Test description",
                            }
                        ],
                    }
                ],
                "budget_summary": {
                    "total_cost": "$1000",
                    "breakdown": {
                        "accommodation": "$300",
                        "food": "$300",
                        "activities": "$300",
                        "transport": "$100",
                    },
                },
            }
        )
        mock_response.usage.total_tokens = 1500
        mock_response.usage.completion_tokens = 500

        mock_to_thread.return_value = mock_response

        # Make API call
        result = await ai_service.generate_itinerary(
            "Paris", 3, [{"id": "family1", "size": 2}], {
                "interests": ["culture"]}
        )

        # Verify the call was made and result is valid
        mock_to_thread.assert_called()
        assert result is not None
        assert "overview" in result
        assert "daily_itinerary" in result
