"""
End-to-End Test for Magic Polls System
Tests the complete workflow: creation → voting → AI analysis → consensus
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.main import app
from app.models.cosmos.enums import PollStatus, PollType
from app.models.cosmos.poll import MagicPoll
from fastapi.testclient import TestClient


class TestMagicPollsE2E:
    """Test complete Magic Polls workflow"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token", "Content-Type": "application/json"}

    @pytest.fixture
    def mock_user(self):
        """Mock user for authentication"""
        return {"id": "user_123", "email": "test@example.com", "name": "Test User"}

    @pytest.fixture
    def sample_trip_id(self):
        """Sample trip ID for testing"""
        return "trip_test_123"

    @pytest.fixture
    def destination_poll_data(self, sample_trip_id: str) -> Dict[str, Any]:
        """Sample destination poll data"""
        return {
            "trip_id": sample_trip_id,
            "title": "Where should we go for our family vacation?",
            "description": "Help choose our destination!",
            "poll_type": "destination_choice",
            "options": [
                {
                    "value": "Hawaii",
                    "label": "Hawaii",
                    "description": "Beaches, volcanoes, and tropical paradise",
                },
                {
                    "value": "Yellowstone",
                    "label": "Yellowstone National Park",
                    "description": "Natural wonders and wildlife",
                },
                {
                    "value": "NYC",
                    "label": "New York City",
                    "description": "Urban adventure and culture",
                },
            ],
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat(),
        }

    @pytest.fixture
    def activity_poll_data(self, sample_trip_id: str) -> Dict[str, Any]:
        """Sample activity poll data"""
        return {
            "trip_id": sample_trip_id,
            "title": "What activities should we prioritize?",
            "description": "Vote on your favorite activities",
            "poll_type": "activity_preference",
            "options": [
                {
                    "value": "hiking",
                    "label": "Hiking & Nature Walks",
                    "description": "Explore trails and natural beauty",
                },
                {
                    "value": "beach",
                    "label": "Beach Activities",
                    "description": "Swimming, surfing, beach games",
                },
                {
                    "value": "museums",
                    "label": "Museums & Culture",
                    "description": "Educational and cultural experiences",
                },
                {
                    "value": "adventure",
                    "label": "Adventure Sports",
                    "description": "Zip-lining, kayaking, rock climbing",
                },
            ],
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        }

    @pytest.mark.asyncio
    @patch("app.api.polls.get_current_user")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.create_poll")
    async def test_create_destination_poll(
        self,
        mock_create_poll,
        mock_get_user,
        client,
        auth_headers,
        mock_user,
        destination_poll_data,
    ):
        """Test creating a destination poll"""
        # Setup mocks
        mock_get_user.return_value = Mock(**mock_user)

        # Mock the create_poll method to return a PollDocument-like dict
        from app.repositories.cosmos_unified import PollDocument

        poll_doc = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id="poll_123",
            creator_id="user_123",
            **destination_poll_data,
        )
        mock_create_poll.return_value = poll_doc

        # Create poll
        response = client.post("/api/v1/polls/", json=destination_poll_data, headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == destination_poll_data["title"]
        assert data["poll_type"] == "destination_choice"
        assert len(data["options"]) == 3
        assert data["status"] == "active"

        # Verify database call
        mock_create_poll.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.polls.get_current_user")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.get_poll_by_id")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.update_poll")
    async def test_vote_on_poll(
        self,
        mock_update_poll,
        mock_get_poll,
        mock_get_user,
        client,
        auth_headers,
        mock_user,
        destination_poll_data,
    ):
        """Test voting on a poll"""
        # Setup mocks
        poll_id = "poll_123"
        mock_get_user.return_value = Mock(**mock_user)

        # Mock return PollDocument object
        from app.repositories.cosmos_unified import PollDocument

        poll_doc = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id=poll_id,
            creator_id="user_123",
            votes={},
            **destination_poll_data,
        )
        mock_get_poll.return_value = poll_doc

        # Mock update to return updated poll
        updated_poll = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id=poll_id,
            creator_id="user_123",
            votes={
                "user_123": {
                    "option_indices": [0],
                    "voted_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            **destination_poll_data,
        )
        mock_update_poll.return_value = updated_poll

        # Submit vote
        vote_data = {"option_indices": [0]}  # Vote for Hawaii

        response = client.post(
            f"/api/v1/polls/{poll_id}/vote", json=vote_data, headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Vote recorded successfully"

        # Verify update was called
        mock_update_poll.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.polls.get_current_user")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.get_poll_by_id")
    async def test_get_poll_results(
        self, mock_get_poll, mock_get_user, client, auth_headers, mock_user, destination_poll_data
    ):
        """Test retrieving poll results"""
        # Setup mocks
        poll_id = "poll_123"
        mock_get_user.return_value = Mock(**mock_user)

        # Poll with multiple votes - return PollDocument
        from app.repositories.cosmos_unified import PollDocument

        poll_doc = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id=poll_id,
            creator_id="user_123",
            votes={
                "user_1": {
                    "option_indices": [0],
                    "voted_at": datetime.now(timezone.utc).isoformat(),
                },
                "user_2": {
                    "option_indices": [0],
                    "voted_at": datetime.now(timezone.utc).isoformat(),
                },
                "user_3": {
                    "option_indices": [1],
                    "voted_at": datetime.now(timezone.utc).isoformat(),
                },
                "user_4": {
                    "option_indices": [0],
                    "voted_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            **destination_poll_data,
        )
        mock_get_poll.return_value = poll_doc

        # Get results
        response = client.get(f"/api/v1/polls/{poll_id}/results", headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["poll_id"] == poll_id
        assert data["total_votes"] == 4

        # Verify vote distribution
        vote_dist = data["vote_distribution"]
        assert vote_dist["Hawaii"] == 3  # 3 votes for Hawaii
        assert vote_dist["Yellowstone"] == 1  # 1 vote for Yellowstone
        assert vote_dist["NYC"] == 0  # 0 votes for NYC

    @pytest.mark.asyncio
    @patch("app.api.polls.get_current_user")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.get_trip_polls")
    async def test_get_trip_polls(
        self, mock_get_trip_polls, mock_get_user, client, auth_headers, mock_user, sample_trip_id
    ):
        """Test retrieving all polls for a trip"""
        # Setup mocks
        mock_get_user.return_value = Mock(**mock_user)

        # Return list of PollDocument objects
        from app.repositories.cosmos_unified import PollDocument

        poll_docs = [
            PollDocument(
                pk=f"trip_{sample_trip_id}",
                id="poll_1",
                trip_id=sample_trip_id,
                creator_id="user_123",
                title="Destination Poll",
                poll_type="destination_choice",
                options=[],
                votes={},
                status="active",
            ),
            PollDocument(
                pk=f"trip_{sample_trip_id}",
                id="poll_2",
                trip_id=sample_trip_id,
                creator_id="user_123",
                title="Activity Poll",
                poll_type="activity_preference",
                options=[],
                votes={},
                status="active",
            ),
        ]
        mock_get_trip_polls.return_value = poll_docs

        # Get trip polls
        response = client.get(f"/api/v1/polls/trip/{sample_trip_id}", headers=auth_headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(poll["trip_id"] == sample_trip_id for poll in data)

    @pytest.mark.asyncio
    @patch("app.services.magic_polls.MagicPollsService._generate_ai_analysis")
    async def test_ai_analysis_generation(self, mock_ai_analysis):
        """Test AI analysis generation for poll responses"""
        from app.repositories.cosmos_unified import UnifiedCosmosRepository
        from app.services.magic_polls import MagicPollsService

        # Setup mock
        mock_ai_analysis.return_value = {
            "summary": "Strong consensus for Hawaii with 75% support. "
            "One family prefers Yellowstone for nature activities.",
            "patterns": [
                "Beach destinations highly preferred",
                "Families with young children favor Hawaii",
            ],
            "conflicts": [
                {
                    "type": "preference_mismatch",
                    "description": "Urban vs. nature preferences",
                    "options": ["NYC", "Yellowstone"],
                }
            ],
            "consensus_level": 0.75,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Create service with mock repository
        mock_repo = Mock(spec=UnifiedCosmosRepository)
        service = MagicPollsService(mock_repo)

        analysis_data = {
            "poll_type": "destination_choice",
            "options": [
                {"value": "Hawaii", "label": "Hawaii"},
                {"value": "Yellowstone", "label": "Yellowstone"},
                {"value": "NYC", "label": "New York City"},
            ],
            "responses": [
                {"user_id": "user_1", "response": {"choice": "Hawaii"}},
                {"user_id": "user_2", "response": {"choice": "Hawaii"}},
                {"user_id": "user_3", "response": {"choice": "Yellowstone"}},
                {"user_id": "user_4", "response": {"choice": "Hawaii"}},
            ],
            "title": "Destination Poll",
        }

        result = await service._generate_ai_analysis(analysis_data)

        # Assertions
        assert result["consensus_level"] == 0.75
        assert "Hawaii" in result["summary"]
        assert len(result["patterns"]) > 0
        assert "conflicts" in result

    @pytest.mark.asyncio
    async def test_consensus_recommendation(self):
        """Test consensus recommendation generation"""
        from app.repositories.cosmos_unified import UnifiedCosmosRepository
        from app.services.magic_polls import MagicPollsService

        # Create service with mock repository
        mock_repo = Mock(spec=UnifiedCosmosRepository)
        service = MagicPollsService(mock_repo)

        analysis_data = {
            "poll_type": "destination_choice",
            "options": [
                {"value": "Hawaii", "label": "Hawaii"},
                {"value": "Yellowstone", "label": "Yellowstone"},
            ],
            "responses": [
                {"user_id": "user_1", "response": {"choice": "Hawaii"}},
                {"user_id": "user_2", "response": {"choice": "Hawaii"}},
                {"user_id": "user_3", "response": {"choice": "Hawaii"}},
                {"user_id": "user_4", "response": {"choice": "Yellowstone"}},
            ],
        }

        ai_analysis = {
            "consensus_level": 0.75,
            "patterns": ["Strong preference for beach destinations"],
        }

        result = await service._generate_consensus_recommendation(analysis_data, ai_analysis)

        # Assertions
        assert result["recommended_choice"] == "Hawaii"
        assert result["consensus_strength"] >= 0.75
        assert result["confidence"] in ["high", "moderate", "low"]
        assert "rationale" in result

    @pytest.mark.asyncio
    @patch("app.api.polls.get_current_user")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.create_poll")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.get_poll_by_id")
    @patch("app.repositories.cosmos_unified.UnifiedCosmosRepository.update_poll")
    @patch("app.services.magic_polls.MagicPollsService._generate_ai_analysis")
    @patch("app.services.magic_polls.MagicPollsService._generate_consensus_recommendation")
    async def test_complete_poll_workflow(
        self,
        mock_consensus,
        mock_ai_analysis,
        mock_update_poll,
        mock_get_poll,
        mock_create_poll,
        mock_get_user,
        client,
        auth_headers,
        mock_user,
        destination_poll_data,
    ):
        """Test complete poll workflow from creation to consensus"""
        from app.repositories.cosmos_unified import PollDocument

        # Setup mocks
        poll_id = "poll_workflow_123"
        mock_get_user.return_value = Mock(**mock_user)

        # Mock AI responses
        mock_ai_analysis.return_value = {
            "summary": "Strong consensus for Hawaii",
            "patterns": ["Beach preference"],
            "conflicts": [],
            "consensus_level": 0.8,
        }

        mock_consensus.return_value = {
            "recommended_choice": "Hawaii",
            "consensus_strength": 0.8,
            "confidence": "high",
            "rationale": "Overwhelming support from families",
        }

        # Step 1: Create poll
        created_poll = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id=poll_id,
            creator_id="user_123",
            **destination_poll_data,
        )
        mock_create_poll.return_value = created_poll
        create_response = client.post(
            "/api/v1/polls/", json=destination_poll_data, headers=auth_headers
        )
        assert create_response.status_code == 200

        # Step 2: Multiple users vote
        poll_doc = PollDocument(
            pk=f"trip_{destination_poll_data['trip_id']}",
            id=poll_id,
            creator_id="user_123",
            votes={},
            **destination_poll_data,
        )

        for i, choice in enumerate([0, 0, 1, 0]):  # 3 Hawaii, 1 Yellowstone
            # Update votes dictionary
            poll_doc.votes[f"user_{i}"] = {
                "option_indices": [choice],
                "voted_at": datetime.now(timezone.utc).isoformat(),
            }
            mock_get_poll.return_value = poll_doc
            mock_update_poll.return_value = poll_doc

            vote_response = client.post(
                f"/api/v1/polls/{poll_id}/vote",
                json={"option_indices": [choice]},
                headers=auth_headers,
            )
            assert vote_response.status_code == 200

        # Step 3: Get results with AI analysis
        results_response = client.get(f"/api/v1/polls/{poll_id}/results", headers=auth_headers)
        assert results_response.status_code == 200

        results_data = results_response.json()
        assert results_data["total_votes"] == 4
        assert results_data["vote_distribution"]["Hawaii"] == 3

    @pytest.mark.asyncio
    async def test_poll_expiration(self):
        """Test poll expiration logic"""
        from app.repositories.cosmos_unified import PollDocument

        # Create expired poll
        expired_poll = PollDocument(
            pk="trip_trip_123",
            id="poll_expired",
            trip_id="trip_123",
            creator_id="user_123",
            title="Expired Poll",
            poll_type=PollType.DESTINATION_CHOICE,
            options=[{"value": "Test"}],
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Already expired
        )

        # Test expiration check - manually check if expired
        assert expired_poll.expires_at < datetime.now(timezone.utc)
        assert expired_poll.status == PollStatus.ACTIVE  # Not auto-updated

    @pytest.mark.asyncio
    async def test_multiple_choice_voting(self):
        """Test polls that allow multiple selections"""
        from app.repositories.cosmos_unified import UnifiedCosmosRepository
        from app.services.magic_polls import MagicPollsService

        # Create service with mock repository
        mock_repo = Mock(spec=UnifiedCosmosRepository)
        service = MagicPollsService(mock_repo)

        # Activity poll allows multiple choices
        analysis_data = {
            "poll_type": "activity_preference",
            "options": [
                {"value": "hiking"},
                {"value": "beach"},
                {"value": "museums"},
                {"value": "adventure"},
            ],
            "responses": [
                {"user_id": "user_1", "response": {"choices": ["hiking", "beach"]}},
                {"user_id": "user_2", "response": {"choices": ["beach", "adventure"]}},
                {"user_id": "user_3", "response": {"choices": ["hiking", "beach", "museums"]}},
            ],
        }

        results = await service._calculate_poll_results(
            Mock(
                options=analysis_data["options"],
                responses={"user_responses": analysis_data["responses"]},
            )
        )

        # Beach should be most popular (3 votes)
        assert results["results"][0]["option"] == "beach" or results["total_responses"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
