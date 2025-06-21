"""
Magic Polls Service - AI-powered group decision making with intelligent preference aggregation
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from app.core.database import get_db
from app.models.ai_integration import MagicPoll, PollStatus, PollType, create_magic_poll
from sqlalchemy import and_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MagicPollsService:
    """Service for handling Magic Polls with AI-powered decision making"""

    def __init__(self):
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
        db: Session = None,
    ) -> Dict[str, Any]:
        """Create a new Magic Poll with AI enhancement"""
        try:
            # Validate poll type
            if poll_type not in [pt.value for pt in PollType]:
                raise ValueError(f"Invalid poll type: {poll_type}")

            # Enhance options with AI if needed
            enhanced_options = await self._enhance_poll_options(options, poll_type)

            # Create the poll
            poll = create_magic_poll(
                trip_id=trip_id,
                creator_id=creator_id,
                title=title,
                poll_type=PollType(poll_type),
                options=enhanced_options,
                description=description,
                expires_hours=expires_hours,
            )

            db.add(poll)
            db.commit()

            return {
                "success": True,
                "poll": poll.to_dict(),
                "message": "Magic Poll created successfully with AI enhancements",
            }

        except Exception as e:
            logger.error(f"Error creating Magic Poll: {str(e)}")
            return {"success": False, "error": str(e)}

    async def submit_response(
        self, poll_id: str, user_id: str, response_data: Dict[str, Any], db: Session
    ) -> Dict[str, Any]:
        """Submit a response to a Magic Poll"""
        try:
            poll = db.query(MagicPoll).filter(MagicPoll.id == poll_id).first()

            if not poll:
                return {"success": False, "error": "Poll not found"}

            if poll.status != PollStatus.ACTIVE.value:
                return {"success": False, "error": "Poll is not active"}

            if poll.is_expired():
                poll.status = PollStatus.EXPIRED.value
                db.commit()
                return {"success": False, "error": "Poll has expired"}

            # Update responses
            if not poll.responses:
                poll.responses = {"user_responses": []}

            # Remove existing response from this user if it exists
            poll.responses["user_responses"] = [
                r for r in poll.responses["user_responses"] if r.get("user_id") != user_id
            ]

            # Add new response
            new_response = {
                "user_id": user_id,
                "response": response_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            poll.responses["user_responses"].append(new_response)

            # Trigger AI analysis if we have enough responses
            if len(poll.responses["user_responses"]) >= 2:
                await self._analyze_poll_responses(poll, db)

            poll.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "poll": poll.to_dict(),
                "response_count": len(poll.responses["user_responses"]),
            }

        except Exception as e:
            logger.error(f"Error submitting poll response: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_poll_results(self, poll_id: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Get poll results with AI analysis"""
        try:
            poll = db.query(MagicPoll).filter(MagicPoll.id == poll_id).first()

            if not poll:
                return {"success": False, "error": "Poll not found"}

            # Check if user has access to this poll's trip
            # TODO: Add proper authorization check

            # Get current results
            results = await self._calculate_poll_results(poll)

            # Get AI analysis if available
            ai_analysis = poll.ai_analysis or {}

            return {
                "success": True,
                "poll": poll.to_dict(),
                "results": results,
                "ai_analysis": ai_analysis,
                "consensus_recommendation": poll.consensus_recommendation,
            }

        except Exception as e:
            logger.error(f"Error getting poll results: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_trip_polls(self, trip_id: str, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get all polls for a trip"""
        try:
            polls = (
                db.query(MagicPoll)
                .filter(MagicPoll.trip_id == trip_id)
                .order_by(MagicPoll.created_at.desc())
                .all()
            )

            return [poll.to_dict() for poll in polls]

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
        destination = option.get("value", "")

        # Simplified insights - in production, this would call AI service
        return {
            "best_time_to_visit": "Spring/Fall",
            "family_friendly_rating": 8,
            "estimated_cost_level": "moderate",
            "top_activities": ["sightseeing", "family dining", "outdoor activities"],
        }

    async def _get_activity_insights(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for activity options"""
        activity = option.get("value", "")

        return {
            "duration": "2-3 hours",
            "age_suitability": "all ages",
            "weather_dependent": False,
            "cost_estimate": "$50-100 per family",
        }

    async def _get_budget_insights(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI insights for budget options"""
        budget_range = option.get("value", "")

        return {
            "what_it_includes": ["accommodation", "meals", "activities"],
            "per_person_estimate": True,
            "typical_trip_length": "3-4 days",
        }

    async def _analyze_poll_responses(self, poll: MagicPoll, db: Session):
        """Analyze poll responses with AI to find patterns and consensus"""
        try:
            responses = poll.responses.get("user_responses", [])

            if len(responses) < 2:
                return

            # Prepare analysis data
            analysis_data = {
                "poll_type": poll.poll_type,
                "options": poll.options,
                "responses": responses,
                "title": poll.title,
            }

            # Call AI service for analysis
            ai_analysis = await self._generate_ai_analysis(analysis_data)

            # Generate consensus recommendation
            consensus = await self._generate_consensus_recommendation(analysis_data, ai_analysis)

            # Update poll with analysis
            poll.ai_analysis = ai_analysis
            poll.consensus_recommendation = consensus
            poll.updated_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error analyzing poll responses: {str(e)}")

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
        self, analysis_data: Dict[str, Any], ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered consensus recommendation"""
        try:
            responses = analysis_data["responses"]

            # Calculate voting results
            vote_counts = {}
            for response in responses:
                choice = response.get("response", {}).get("choice")
                if choice:
                    vote_counts[choice] = vote_counts.get(choice, 0) + 1

            # Find the most popular choice
            if vote_counts:
                top_choice = max(vote_counts.items(), key=lambda x: x[1])
                consensus_strength = top_choice[1] / len(responses)

                return {
                    "recommended_choice": top_choice[0],
                    "vote_count": top_choice[1],
                    "total_votes": len(responses),
                    "consensus_strength": consensus_strength,
                    "confidence": (
                        "high"
                        if consensus_strength > 0.7
                        else "moderate" if consensus_strength > 0.5 else "low"
                    ),
                    "rationale": ai_analysis.get("summary", "Based on group preferences"),
                    "generated_at": datetime.utcnow().isoformat(),
                }

            return {
                "recommended_choice": None,
                "message": "No clear consensus yet - more responses needed",
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

    async def _calculate_poll_results(self, poll: MagicPoll) -> Dict[str, Any]:
        """Calculate current poll results"""
        responses = poll.responses.get("user_responses", []) if poll.responses else []

        # Count votes for each option
        vote_counts = {}
        for response in responses:
            choice = response.get("response", {}).get("choice")
            if choice:
                vote_counts[choice] = vote_counts.get(choice, 0) + 1

        # Calculate percentages
        total_votes = len(responses)
        results = []

        for option in poll.options:
            option_value = option.get("value", str(option))
            votes = vote_counts.get(option_value, 0)
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0

            results.append(
                {
                    "option": option_value,
                    "votes": votes,
                    "percentage": round(percentage, 1),
                    "details": option,
                }
            )

        return {
            "total_responses": total_votes,
            "results": results,
            "updated_at": datetime.utcnow().isoformat(),
        }


# Global instance
magic_polls_service = MagicPollsService()
