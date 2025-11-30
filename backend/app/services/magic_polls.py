"""
Magic Polls Service - AI-powered group decision making with intelligent preference aggregation
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from app.models.cosmos.enums import PollStatus, PollType
from app.repositories.cosmos_unified import UnifiedCosmosRepository

logger = logging.getLogger(__name__)


class MagicPollsService:
    """Service for handling Magic Polls with AI-powered decision making"""

    def __init__(self, cosmos_repo: UnifiedCosmosRepository):
        self.cosmos_repo = cosmos_repo
        self.llm_orchestration_url = "http://localhost:8001"

    async def create_poll(
        self,
        trip_id: str,
        creator_id: str,
        title: str,
        poll_type: str,
        options: List[Dict[str, Any]],
        description: Optional[str] = None,
        expires_hours: int = 72,
    ) -> Dict[str, Any]:
        """Create a new Magic Poll with AI enhancement"""
        try:
            # Validate poll type
            if poll_type not in [pt.value for pt in PollType]:
                raise ValueError(f"Invalid poll type: {poll_type}")

            # Enhance options with AI if needed
            enhanced_options = await self._enhance_poll_options(options, poll_type)

            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

            # Create poll document
            poll_data = {
                "trip_id": trip_id,
                "creator_id": creator_id,
                "title": title,
                "description": description,
                "poll_type": poll_type,
                "options": enhanced_options,
                "votes": {},
                "ai_analysis": None,
                "consensus_recommendation": None,
                "status": PollStatus.ACTIVE.value,
                "expires_at": expires_at,
            }

            # Create poll in Cosmos DB
            poll_doc = await self.cosmos_repo.create_poll(poll_data)

            poll_response = {
                "id": poll_doc.id,
                "trip_id": poll_doc.trip_id,
                "creator_id": poll_doc.creator_id,
                "title": poll_doc.title,
                "description": poll_doc.description,
                "poll_type": poll_doc.poll_type,
                "options": poll_doc.options,
                "votes": poll_doc.votes,
                "status": poll_doc.status,
                "expires_at": poll_doc.expires_at.isoformat() if poll_doc.expires_at else None,
                "created_at": poll_doc.created_at.isoformat(),
            }

            # Broadcast poll creation via WebSocket
            from app.services.websocket import notify_poll_created

            await notify_poll_created(trip_id=trip_id, poll_id=poll_doc.id, poll_data=poll_response)

            return {
                "success": True,
                "poll": poll_response,
                "message": "Magic Poll created successfully with AI enhancements",
            }

        except Exception as e:
            logger.error(f"Error creating Magic Poll: {str(e)}")
            return {"success": False, "error": str(e)}

    async def submit_vote(
        self, poll_id: str, trip_id: str, user_id: str, option_indices: List[int]
    ) -> Dict[str, Any]:
        """Submit a vote to a Magic Poll"""
        try:
            # Get poll from Cosmos DB
            poll = await self.cosmos_repo.get_poll_by_id(poll_id, trip_id)

            if not poll:
                return {"success": False, "error": "Poll not found"}

            if poll.status != PollStatus.ACTIVE.value:
                return {"success": False, "error": "Poll is not active"}

            # Check if poll has expired
            if poll.expires_at and datetime.now(timezone.utc) > poll.expires_at:
                # Update status to expired
                await self.cosmos_repo.update_poll(
                    poll_id, trip_id, {"status": PollStatus.EXPIRED.value}
                )
                return {"success": False, "error": "Poll has expired"}

            # Add/update vote
            poll.votes[user_id] = {
                "option_indices": option_indices,
                "voted_at": datetime.now(timezone.utc).isoformat(),
            }

            # Update poll with new vote
            update_data = {"votes": poll.votes}

            # Trigger AI analysis if we have enough votes
            if len(poll.votes) >= 2:
                ai_analysis = await self._analyze_poll_responses(poll)
                consensus = await self._generate_consensus_recommendation(poll, ai_analysis)
                update_data["ai_analysis"] = ai_analysis
                update_data["consensus_recommendation"] = consensus

            updated_poll = await self.cosmos_repo.update_poll(poll_id, trip_id, update_data)

            # Broadcast vote event via WebSocket
            from app.services.websocket import notify_poll_vote

            await notify_poll_vote(
                trip_id=trip_id,
                poll_id=poll_id,
                voter_id=user_id,
                vote_data={
                    "option_indices": option_indices,
                    "vote_count": len(updated_poll.votes),
                    "has_ai_analysis": bool(updated_poll.ai_analysis),
                },
            )

            # If AI analysis was generated, broadcast results
            if updated_poll.ai_analysis:
                from app.services.websocket import notify_poll_results

                await notify_poll_results(
                    trip_id=trip_id,
                    poll_id=poll_id,
                    results_data={
                        "ai_analysis": updated_poll.ai_analysis,
                        "consensus": updated_poll.consensus_recommendation,
                        "vote_count": len(updated_poll.votes),
                    },
                )

            return {
                "success": True,
                "poll_id": updated_poll.id,
                "vote_count": len(updated_poll.votes),
                "ai_analysis": updated_poll.ai_analysis,
                "consensus": updated_poll.consensus_recommendation,
            }

        except Exception as e:
            logger.error(f"Error submitting poll vote: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_poll_results(self, poll_id: str, trip_id: str, user_id: str) -> Dict[str, Any]:
        """Get poll results with AI analysis"""
        try:
            # Get poll from Cosmos DB
            poll = await self.cosmos_repo.get_poll_by_id(poll_id, trip_id)

            if not poll:
                return {"success": False, "error": "Poll not found"}

            # Check if user has access to this poll's trip
            # TODO: Add proper authorization check

            # Calculate current results
            results = self._calculate_poll_results(poll)

            return {
                "success": True,
                "poll": {
                    "id": poll.id,
                    "title": poll.title,
                    "description": poll.description,
                    "poll_type": poll.poll_type,
                    "options": poll.options,
                    "status": poll.status,
                    "created_at": poll.created_at.isoformat(),
                },
                "results": results,
                "ai_analysis": poll.ai_analysis or {},
                "consensus_recommendation": poll.consensus_recommendation,
            }

        except Exception as e:
            logger.error(f"Error getting poll results: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_trip_polls(self, trip_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all polls for a trip"""
        try:
            # Get polls from Cosmos DB
            polls = await self.cosmos_repo.get_trip_polls(trip_id)

            return [
                {
                    "id": poll.id,
                    "title": poll.title,
                    "description": poll.description,
                    "poll_type": poll.poll_type,
                    "status": poll.status,
                    "vote_count": len(poll.votes),
                    "created_at": poll.created_at.isoformat(),
                }
                for poll in polls
            ]

        except Exception as e:
            logger.error(f"Error getting trip polls: {str(e)}")
            return []

    async def _enhance_poll_options(
        self, options: List[Dict[str, Any]], poll_type: str
    ) -> List[Dict[str, Any]]:
        """Enhance poll options with AI suggestions"""
        try:
            # Add AI-generated additional context to options
            enhanced_options = []

            for option in options:
                enhanced_option = option.copy()

                # Add AI enhancement based on poll type
                if poll_type == PollType.DESTINATION_CHOICE.value:
                    enhanced_option["ai_insights"] = await self._get_destination_insights(option)
                elif poll_type == PollType.ACTIVITY_PREFERENCE.value:
                    enhanced_option["ai_insights"] = await self._get_activity_insights(option)
                elif poll_type == PollType.BUDGET_RANGE.value:
                    enhanced_option["ai_insights"] = await self._get_budget_insights(option)

                enhanced_options.append(enhanced_option)

            return enhanced_options

        except Exception as e:
            logger.error(f"Error enhancing poll options: {str(e)}")
            return options

    async def _get_destination_insights(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for destination options"""
        _destination = option.get("value", "")

        # Simplified insights - in production, this would call AI service
        return {
            "best_time_to_visit": "Spring/Fall",
            "family_friendly_rating": 8,
            "estimated_cost_level": "moderate",
            "top_activities": ["sightseeing", "family dining", "outdoor activities"],
        }

    async def _get_activity_insights(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for activity options"""
        _activity = option.get("value", "")

        return {
            "duration": "2-3 hours",
            "age_suitability": "all ages",
            "weather_dependent": False,
            "cost_estimate": "$50-100 per family",
        }

    async def _get_budget_insights(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for budget options"""
        _budget_range = option.get("value", "")

        return {
            "what_it_includes": ["accommodation", "meals", "activities"],
            "per_person_estimate": True,
            "typical_trip_length": "3-4 days",
        }

    async def _analyze_poll_responses(self, poll) -> Optional[Dict[str, Any]]:
        """Analyze poll responses with AI to find patterns and consensus"""
        try:
            # Need at least 2 votes for analysis
            if len(poll.votes) < 2:
                return None

            # Prepare analysis data from votes
            analysis_data = {
                "poll_type": poll.poll_type,
                "options": poll.options,
                "votes": poll.votes,
                "title": poll.title,
            }

            # Call AI service for analysis
            ai_analysis = await self._generate_ai_analysis(analysis_data)
            return ai_analysis

        except Exception as e:
            logger.error(f"Error analyzing poll responses: {str(e)}")
            return None

    async def _generate_ai_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis of poll responses"""
        try:
            # Prepare prompt for AI analysis
            prompt = self._build_analysis_prompt(analysis_data)

            # Call LLM Orchestration service
            response = requests.post(
                f"{self.llm_orchestration_url}/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI assistant that analyzes group preferences for family trip planning. Provide insights about group consensus, conflicts, and recommendations.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.3,
                },
                timeout=30,
            )

            if response.status_code == 200:
                ai_data = response.json()
                analysis_text = ai_data["choices"][0]["message"]["content"]

                return {
                    "summary": analysis_text,
                    "patterns": self._extract_patterns(analysis_data),
                    "conflicts": self._identify_conflicts(analysis_data),
                    "consensus_level": self._calculate_consensus_level(analysis_data),
                    "generated_at": datetime.utcnow().isoformat(),
                }
            else:
                raise Exception(f"AI service error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            return {
                "summary": "Analysis temporarily unavailable",
                "patterns": [],
                "conflicts": [],
                "consensus_level": 0.5,
                "error": str(e),
            }

    def _build_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Build prompt for AI analysis"""
        responses = analysis_data["responses"]
        options = analysis_data["options"]

        prompt = f"Analyze these group poll responses for: {analysis_data['title']}\n\n"
        prompt += f"Poll type: {analysis_data['poll_type']}\n"
        prompt += f"Options: {[opt.get('value', opt) for opt in options]}\n"
        prompt += f"Responses: {len(responses)} people responded\n\n"

        for i, response in enumerate(responses):
            prompt += f"Response {i+1}: {response.get('response', {})}\n"

        prompt += (
            "\nProvide insights about group preferences, consensus level, and recommendations."
        )

        return prompt

    async def _generate_consensus_recommendation(
        self, poll, ai_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered consensus recommendation from poll votes"""
        try:
            votes = poll.votes

            if not votes:
                return {
                    "recommended_choice": None,
                    "message": "No votes yet",
                    "confidence": "low",
                }

            # Calculate voting results - count votes for each option
            option_votes: Dict[int, int] = {}
            for vote_data in votes.values():
                option_indices = vote_data.get("option_indices", [])
                for idx in option_indices:
                    option_votes[idx] = option_votes.get(idx, 0) + 1

            # Find the most popular option
            if option_votes:
                top_option_idx = max(option_votes.items(), key=lambda x: x[1])[0]
                top_option_votes = option_votes[top_option_idx]
                consensus_strength = top_option_votes / len(votes)

                # Get the option details
                top_option = (
                    poll.options[top_option_idx] if top_option_idx < len(poll.options) else {}
                )

                return {
                    "recommended_choice": top_option.get("value", f"Option {top_option_idx}"),
                    "vote_count": top_option_votes,
                    "total_votes": len(votes),
                    "consensus_strength": consensus_strength,
                    "confidence": (
                        "high"
                        if consensus_strength > 0.7
                        else "moderate" if consensus_strength > 0.5 else "low"
                    ),
                    "rationale": (
                        ai_analysis.get("summary", "Based on group preferences")
                        if ai_analysis
                        else "Based on voting results"
                    ),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }

            return {
                "recommended_choice": None,
                "message": "No clear consensus yet - more votes needed",
                "confidence": "low",
            }

        except Exception as e:
            logger.error(f"Error generating consensus recommendation: {str(e)}")
            return {"error": str(e)}

    def _extract_patterns(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract patterns from poll responses"""
        # Simplified pattern extraction
        patterns = []
        responses = analysis_data["responses"]

        if len(responses) >= 3:
            patterns.append("Sufficient responses for meaningful analysis")

        return patterns

    def _identify_conflicts(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify conflicts in poll responses"""
        conflicts = []
        responses = analysis_data["responses"]

        # Check for split decisions
        vote_counts = {}
        for response in responses:
            choice = response.get("response", {}).get("choice")
            if choice:
                vote_counts[choice] = vote_counts.get(choice, 0) + 1

        if len(vote_counts) > 1:
            sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_votes) >= 2 and sorted_votes[0][1] == sorted_votes[1][1]:
                conflicts.append(
                    {
                        "type": "tie",
                        "description": f"Tie between {sorted_votes[0][0]} and {sorted_votes[1][0]}",
                        "options": [sorted_votes[0][0], sorted_votes[1][0]],
                    }
                )

        return conflicts

    def _calculate_consensus_level(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate consensus level (0-1)"""
        responses = analysis_data["responses"]

        if len(responses) < 2:
            return 0.0

        # Calculate based on vote distribution
        vote_counts = {}
        for response in responses:
            choice = response.get("response", {}).get("choice")
            if choice:
                vote_counts[choice] = vote_counts.get(choice, 0) + 1

        if not vote_counts:
            return 0.0

        max_votes = max(vote_counts.values())
        return max_votes / len(responses)

    def _calculate_poll_results(self, poll) -> Dict[str, Any]:
        """Calculate current poll results from votes"""
        votes = poll.votes if hasattr(poll, "votes") else {}

        # Count votes for each option index
        vote_counts: Dict[int, int] = {}
        for vote_data in votes.values():
            option_indices = vote_data.get("option_indices", [])
            for idx in option_indices:
                vote_counts[idx] = vote_counts.get(idx, 0) + 1

        # Calculate percentages
        total_votes = len(votes)
        results = []

        for idx, option in enumerate(poll.options):
            option_value = option.get("value", str(option))
            vote_count = vote_counts.get(idx, 0)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0

            results.append(
                {
                    "option": option_value,
                    "votes": vote_count,
                    "percentage": round(percentage, 1),
                    "details": option,
                }
            )

        return {
            "total_responses": total_votes,
            "results": results,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
