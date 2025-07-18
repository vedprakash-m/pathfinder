"""
Enhanced AI service for itinerary generation using OpenAI models.
Enhanced with advanced cost optimization and multi-family preference handling.
"""

import asyncio
import json
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import tiktoken

    HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None
    HAS_TIKTOKEN = False
from app.core.cache_service import ai_cache_service
from app.core.config import get_settings
from app.core.logging_config import create_logger
from app.services.llm_orchestration_client import llm_orchestration_client
from openai import OpenAI

settings = get_settings()
logger = create_logger(__name__)

# Initialize OpenAI client with fallback for missing API key
try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    if not client:
        logger.warning("OpenAI client not initialized - API key not provided")
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}")
    client = None


# Note: AICache functionality moved to core.cache_service.AICacheService
# for Redis-free cost optimization


# Enhanced cost tracking with per-model analytics
class CostTracker:
    """Track API costs and usage patterns with model-specific analytics."""

    # Updated pricing per 1K tokens (as of 2025)
    MODEL_COSTS = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    }

    def __init__(self):
        self.daily_usage: Dict[str, Dict[str, Any]] = {}
        self.usage_patterns: Dict[str, Dict[str, Any]] = {}

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        if model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model for cost calculation: {model}")
            return 0.0

        costs = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return input_cost + output_cost

    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_type: str = "general",
    ) -> float:
        """Track usage and return cost."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        today = datetime.now().date().isoformat()

        # Initialize daily tracking
        if today not in self.daily_usage:
            self.daily_usage[today] = {
                "cost": 0.0,
                "requests": 0,
                "models": {},
                "request_types": {},
            }

        # Update daily totals
        self.daily_usage[today]["cost"] += cost
        self.daily_usage[today]["requests"] += 1

        # Track by model
        if model not in self.daily_usage[today]["models"]:
            self.daily_usage[today]["models"][model] = {"cost": 0.0, "requests": 0}

        self.daily_usage[today]["models"][model]["cost"] += cost
        self.daily_usage[today]["models"][model]["requests"] += 1

        # Track by request type
        if request_type not in self.daily_usage[today]["request_types"]:
            self.daily_usage[today]["request_types"][request_type] = {
                "cost": 0.0,
                "requests": 0,
            }

        self.daily_usage[today]["request_types"][request_type]["cost"] += cost
        self.daily_usage[today]["request_types"][request_type]["requests"] += 1

        # Log usage pattern
        self.usage_patterns[datetime.now().isoformat()] = {
            "model": model,
            "tokens": input_tokens + output_tokens,
            "cost": cost,
            "request_type": request_type,
            "daily_total": self.daily_usage[today]["cost"],
        }

        return cost

    def check_budget_limit(self, request_type: str = "general") -> bool:
        """Enhanced budget checking with per-type limits."""
        today = datetime.now().date().isoformat()
        if today not in self.daily_usage:
            return True

        daily_cost = self.daily_usage[today]["cost"]
        daily_budget_limit = getattr(settings, "AI_DAILY_BUDGET_LIMIT", 50.0)

        # Check overall daily limit
        if daily_cost >= daily_budget_limit:
            return False

        # Check request-type specific limits
        request_type_limits = {
            "itinerary_generation": daily_budget_limit * 0.6,  # 60% for itinerary generation
            "optimization": daily_budget_limit * 0.2,  # 20% for optimization
            "general": daily_budget_limit * 0.2,  # 20% for other requests
        }

        if request_type in request_type_limits:
            type_cost = (
                self.daily_usage[today]["request_types"].get(request_type, {}).get("cost", 0)
            )
            if type_cost >= request_type_limits[request_type]:
                return False

        return True

    def get_optimization_suggestions(self) -> List[str]:
        """Analyze usage patterns and provide optimization suggestions."""
        suggestions: List[str] = []
        today = datetime.now().date().isoformat()

        if today not in self.daily_usage:
            return suggestions

        usage = self.daily_usage[today]

        # Suggest model optimization
        if "gpt-4o" in usage["models"] and "gpt-4o-mini" in usage["models"]:
            gpt4_requests = usage["models"]["gpt-4o"]["requests"]
            mini_requests = usage["models"]["gpt-4o-mini"]["requests"]

            if gpt4_requests > mini_requests:
                suggestions.append("Consider using gpt-4o-mini for more requests to reduce costs")

        # Suggest caching
        if usage["requests"] > 20:
            suggestions.append("High request volume detected - ensure caching is enabled")

        # Budget warnings
        daily_budget_limit = getattr(settings, "AI_DAILY_BUDGET_LIMIT", 50.0)
        if usage["cost"] > daily_budget_limit * 0.8:
            suggestions.append("Approaching daily budget limit - consider request optimization")

        return suggestions


class MultiFamilyPreferenceEngine:
    """Engine for reconciling preferences across multiple families."""

    @staticmethod
    def reconcile_family_preferences(
        families_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Reconcile conflicting preferences across multiple families."""
        if not families_data:
            return {}

        # Extract all preferences
        all_activities: List[str] = []
        all_dietary: List[str] = []
        all_accessibility: List[str] = []
        budget_levels: List[str] = []
        travel_styles: List[str] = []

        for family in families_data:
            family_prefs = family.get("preferences", {})
            if isinstance(family_prefs.get("activities"), list):
                all_activities.extend(family_prefs.get("activities", []))

            for member in family.get("members", []):
                if isinstance(member.get("dietary_restrictions"), list):
                    all_dietary.extend(member.get("dietary_restrictions", []))
                if isinstance(member.get("accessibility_needs"), list):
                    all_accessibility.extend(member.get("accessibility_needs", []))

            if "budget_level" in family_prefs:
                budget_levels.append(family_prefs["budget_level"])
            if "travel_style" in family_prefs:
                travel_styles.append(family_prefs["travel_style"])

        # Find common ground and create unified preferences
        activity_counts = Counter(all_activities)

        # Select activities preferred by at least 30% of families
        threshold = max(1, len(families_data) * 0.3)
        popular_activities = [
            activity for activity, count in activity_counts.items() if count >= threshold
        ]

        # Handle budget level conflicts (take conservative approach)
        budget_priority = {"low": 1, "medium": 2, "high": 3}
        if budget_levels:
            unified_budget = min(budget_levels, key=lambda x: budget_priority.get(x, 2))
        else:
            unified_budget = "medium"

        # Handle travel style (take most relaxed approach for families)
        style_priority = {"relaxed": 1, "moderate": 2, "active": 3}
        if travel_styles:
            unified_style = min(travel_styles, key=lambda x: style_priority.get(x, 2))
        else:
            unified_style = "moderate"

        return {
            "unified_activities": popular_activities,
            "all_dietary_restrictions": list(set(all_dietary)),
            "all_accessibility_needs": list(set(all_accessibility)),
            "unified_budget_level": unified_budget,
            "unified_travel_style": unified_style,
            "family_count": len(families_data),
            "total_participants": sum(len(family.get("members", [])) for family in families_data),
            "preference_conflicts": {
                "budget_levels": budget_levels,
                "travel_styles": travel_styles,
                "activity_overlaps": dict(activity_counts),
            },
        }


class ItineraryPrompts:
    """Enhanced template prompts for itinerary generation with multi-family support."""

    SYSTEM_PROMPT = """You are an expert travel planner specializing in multi-family group trips. 
    You create detailed, practical itineraries that accommodate diverse preferences, ages, and needs 
    across multiple families traveling together. Your responses are always in valid JSON format.
    
    Key principles:
    - Prioritize activities that work for all age groups
    - Include flexible options for different energy levels
    - Provide cost-effective solutions
    - Consider logistics for large groups
    - Include backup plans for weather/availability issues
    - Balance group activities with family-specific time"""

    @staticmethod
    def create_itinerary_prompt(
        destination: str,
        duration_days: int,
        families_data: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        budget_total: Optional[float] = None,
    ) -> str:
        """Create enhanced prompt with multi-family preference reconciliation."""

        # Use preference engine to reconcile family preferences
        unified_prefs = MultiFamilyPreferenceEngine.reconcile_family_preferences(families_data)

        # Format family information
        family_info: List[str] = []
        total_participants = unified_prefs.get("total_participants", 0)

        for i, family in enumerate(families_data, 1):
            family_size = len(family.get("members", []))

            ages = [str(member.get("age", "adult")) for member in family.get("members", [])]
            dietary_lists = [
                member.get("dietary_restrictions", []) for member in family.get("members", [])
            ]
            dietary_flat = [
                item for sublist in dietary_lists for item in sublist if isinstance(sublist, list)
            ]

            accessibility_lists = [
                member.get("accessibility_needs", []) for member in family.get("members", [])
            ]
            accessibility_flat = [
                item
                for sublist in accessibility_lists
                for item in sublist
                if isinstance(sublist, list)
            ]

            family_info.append(
                f"""
            Family {i} ({family.get('name', 'Unknown')}): {family_size} members
            - Ages: {', '.join(ages)}
            - Dietary restrictions: {', '.join(dietary_flat) if dietary_flat else 'None'}
            - Accessibility needs: {', '.join(accessibility_flat) if accessibility_flat else 'None'}
            - Preferences: {family.get('preferences', {})}
            """
            )

        budget_info = f"Total budget: ${budget_total:,.2f}" if budget_total else "Budget: Flexible"

        # Create conflict resolution notes
        conflicts = unified_prefs.get("preference_conflicts", {})
        conflict_notes = ""
        if conflicts:
            conflict_notes = f"""
            PREFERENCE CONFLICTS TO RESOLVE:
            - Budget levels vary: {conflicts.get('budget_levels', [])} -> Using conservative: {unified_prefs.get('unified_budget_level')}
            - Travel styles vary: {conflicts.get('travel_styles', [])} -> Using family-friendly: {unified_prefs.get('unified_travel_style')}
            - Activity preferences overlap: {conflicts.get('activity_overlaps', {})}
            """

        prompt = f"""
        Create a detailed {duration_days}-day itinerary for a multi-family group trip to {destination}.
        
        GROUP COMPOSITION:
        - Total participants: {total_participants}
        - Number of families: {len(families_data)}
        {''.join(family_info)}
        
        UNIFIED PREFERENCES (reconciled across families):
        - Popular activities: {unified_prefs.get('unified_activities', [])}
        - All dietary restrictions: {unified_prefs.get('all_dietary_restrictions', [])}
        - All accessibility needs: {unified_prefs.get('all_accessibility_needs', [])}
        - Budget level: {unified_prefs.get('unified_budget_level', 'medium')}
        - Travel style: {unified_prefs.get('unified_travel_style', 'moderate')}
        
        ORIGINAL PREFERENCES:
        - Accommodation type: {preferences.get('accommodation_type', ['family-friendly hotels'])}
        - Transportation: {preferences.get('transportation_mode', ['rental cars'])}
        - Activity types: {preferences.get('activity_types', [])}
        - Dining preferences: {preferences.get('dining_preferences', ['family restaurants'])}
        - Special requirements: {preferences.get('special_requirements', [])}
        
        BUDGET: {budget_info}
        
        {conflict_notes}
        
        SPECIAL INSTRUCTIONS FOR MULTI-FAMILY TRIPS:
        1. Include both group activities and family-specific options
        2. Provide logistics notes for coordinating multiple families
        3. Suggest meeting points and communication strategies
        4. Include backup indoor activities for weather issues
        5. Consider different energy levels and interests within the group
        6. Provide cost splitting suggestions where applicable
        
        Please provide a comprehensive itinerary in JSON format with this enhanced structure:
        {{
            "overview": {{
                "destination": "{destination}",
                "duration": {duration_days},
                "total_participants": {total_participants},
                "family_count": {len(families_data)},
                "estimated_cost_per_person": 0,
                "estimated_cost_per_family": 0,
                "best_time_to_visit": "",
                "weather_info": "",
                "group_coordination_tips": [],
                "travel_tips": []
            }},
            "daily_itinerary": [],
            "budget_summary": {{}},
            "logistics": {{}},
            "packing_suggestions": {{}},
            "important_notes": [],
            "emergency_contacts": [],
            "alternative_plans": {{}},
            "multi_family_considerations": {{}}
        }}
        
        Ensure all costs are realistic and based on current market rates.
        """

        return prompt


class AIService:
    """Enhanced AI service for generating travel itineraries with advanced features."""

    def __init__(self):
        self.cost_tracker = CostTracker()
        self.cache = ai_cache_service  # Use Redis-free cache service
        if HAS_TIKTOKEN:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None
        self.preference_engine = MultiFamilyPreferenceEngine()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback approximation: 1 token ≈ 4 characters
            return len(text) // 4

    def _select_optimal_model(self, request_type: str, input_tokens: int) -> str:
        """Select optimal model based on request type and complexity."""
        # Simple model selection logic - can be enhanced with ML
        primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
        fallback_model = getattr(settings, "OPENAI_MODEL_FALLBACK", "gpt-4o")

        if request_type == "itinerary_generation":
            if input_tokens > 3000:  # Complex multi-family request
                return fallback_model
            else:
                return primary_model

        return primary_model

    async def generate_itinerary(
        self,
        destination: str,
        duration_days: int,
        families_data: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        budget_total: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete travel itinerary using AI."""

        # Check budget limit
        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        try:
            # Create the prompt
            prompt = ItineraryPrompts.create_itinerary_prompt(
                destination, duration_days, families_data, preferences, budget_total
            )

            # Count input tokens
            input_tokens = self.count_tokens(prompt)

            logger.info(
                f"Generating itinerary for {destination}",
                duration_days=duration_days,
                families_count=len(families_data),
                input_tokens=input_tokens,
                user_id=user_id,
            )

            # Try primary model first (cost-optimized)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            fallback_model = getattr(settings, "OPENAI_MODEL_FALLBACK", "gpt-4o")

            try:
                response = await self._make_api_call(
                    primary_model,
                    prompt,
                    input_tokens,
                    task_type="itinerary_generation",
                    user_id=user_id,
                )
            except Exception as e:
                logger.warning(f"Primary model failed, falling back: {e}")
                # Fallback to more capable model
                response = await self._make_api_call(
                    fallback_model,
                    prompt,
                    input_tokens,
                    task_type="itinerary_generation",
                    user_id=user_id,
                )

            # Parse and validate the response
            itinerary = self._parse_itinerary_response(response)

            # Add metadata
            itinerary["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "model_used": response.get("model"),
                "generation_cost": response.get("cost", 0),
                "user_id": user_id,
                "input_tokens": input_tokens,
                "output_tokens": response.get("output_tokens", 0),
            }

            logger.info(
                "Itinerary generated successfully",
                destination=destination,
                cost=response.get("cost", 0),
                user_id=user_id,
            )

            return itinerary

        except Exception as e:
            logger.error(f"Failed to generate itinerary: {e}", user_id=user_id)
            raise

    async def _make_api_call(
        self,
        model: str,
        prompt: str,
        input_tokens: int,
        task_type: str = "general",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make API call using LLM orchestration service if available, fallback to OpenAI."""

        # Try LLM orchestration service first if enabled
        if llm_orchestration_client.enabled:
            try:
                logger.info("Using LLM Orchestration Service for API call")

                max_tokens = getattr(settings, "OPENAI_MAX_TOKENS", 4000)
                temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.7)

                # Enhanced prompt for LLM orchestration with system context
                enhanced_prompt = f"{ItineraryPrompts.SYSTEM_PROMPT}\n\nUser Request:\n{prompt}"

                orchestration_response = await llm_orchestration_client.generate_text(
                    prompt=enhanced_prompt,
                    task_type=task_type,
                    user_id=user_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model_preference=model,
                )

                # Extract tokens for cost tracking (orchestration service handles its own costs)
                output_tokens = orchestration_response.get("tokens_used", 0)
                orchestration_cost = orchestration_response.get("cost", 0.0)

                logger.info(
                    f"LLM Orchestration response: model={orchestration_response.get('model_used')}, "
                    f"provider={orchestration_response.get('provider')}, cost=${orchestration_cost:.4f}"
                )

                return {
                    "content": orchestration_response.get("text", ""),
                    "model": orchestration_response.get("model_used", model),
                    "provider": orchestration_response.get("provider", "unknown"),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": orchestration_cost,
                    "processing_time": orchestration_response.get("processing_time", 0.0),
                    "orchestration_metadata": orchestration_response.get("metadata", {}),
                    "source": "llm_orchestration",
                }

            except Exception as e:
                logger.warning(f"LLM Orchestration failed, falling back to OpenAI: {e}")
                # Fall through to OpenAI fallback

        # Fallback to direct OpenAI API
        try:
            if not client:
                logger.error("OpenAI client not available - API key not configured")
                raise ValueError("AI service not configured - OpenAI API key required")

            logger.info("Using direct OpenAI API call")

            max_tokens = getattr(settings, "OPENAI_MAX_TOKENS", 4000)
            temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.7)
            timeout_val = getattr(settings, "OPENAI_TIMEOUT", 60)

            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": ItineraryPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout_val,
                response_format={"type": "json_object"},
            )

            # Extract response data
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if response.usage else 0

            # Track costs
            cost = self.cost_tracker.track_usage(model, input_tokens, output_tokens)

            return {
                "content": content,
                "model": model,
                "provider": "openai",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "source": "direct_openai",
            }

        except Exception as e:
            error_message = str(e).lower()
            if "rate limit" in error_message:
                logger.error("OpenAI rate limit exceeded")
                raise ValueError("AI service temporarily unavailable due to rate limits") from e
            elif "timeout" in error_message:
                logger.error("OpenAI API timeout")
                raise ValueError("AI service timeout - please try again") from e
            else:
                logger.error(f"OpenAI API error: {e}")
                raise ValueError(f"AI service error: {str(e)}") from e

    def _parse_itinerary_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            content = response["content"]
            if not content:
                raise ValueError("Empty response content")

            itinerary = json.loads(content)

            # Basic validation
            required_fields = ["overview", "daily_itinerary", "budget_summary"]
            for field in required_fields:
                if field not in itinerary:
                    raise ValueError(f"Missing required field: {field}")

            # Validate daily itinerary structure
            if not isinstance(itinerary["daily_itinerary"], list):
                raise ValueError("Daily itinerary must be a list")

            return itinerary

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("Invalid AI response format") from e
        except Exception as e:
            logger.error(f"Failed to validate AI response: {e}")
            raise ValueError(f"AI response validation failed: {str(e)}") from e

    async def enhance_activity(
        self,
        activity_name: str,
        location: str,
        participants: List[Dict[str, Any]],
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enhance a single activity with detailed information."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        prompt = f"""
        Provide detailed information about this activity: {activity_name} in {location}.
        
        Consider these participants: {len(participants)} people
        Preferences: {preferences}
        
        Return JSON with:
        {{
            "enhanced_description": "",
            "duration": "",
            "cost_estimate": 0,
            "age_appropriateness": "",
            "accessibility_info": "",
            "booking_requirements": "",
            "best_times": [],
            "what_to_bring": [],
            "nearby_amenities": [],
            "alternatives": []
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model, prompt, input_tokens, task_type="activity_enhancement"
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to enhance activity: {e}")
            raise

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        today = datetime.now().date().isoformat()
        today_usage = self.cost_tracker.daily_usage.get(today, {"cost": 0, "requests": 0})
        daily_budget_limit = getattr(settings, "AI_DAILY_BUDGET_LIMIT", 50.0)

        return {
            "today": today_usage,
            "budget_limit": daily_budget_limit,
            "budget_remaining": daily_budget_limit - today_usage["cost"],
            "models_available": list(self.cost_tracker.MODEL_COSTS.keys()),
        }

    async def optimize_route(
        self,
        destinations: List[str],
        vehicle_constraints: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize route between multiple destinations."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        vehicle_info = vehicle_constraints or {}
        prefs = preferences or {}

        prompt = f"""
        Optimize the route between these destinations: {', '.join(destinations)}
        
        Vehicle constraints:
        - EV vehicles: {vehicle_info.get('ev_vehicles', False)}
        - Charging range: {vehicle_info.get('charging_range', 300)} miles
        - Prefer scenic routes: {vehicle_info.get('prefer_scenic', False)}
        
        Preferences:
        - Travel style: {prefs.get('travel_style', 'balanced')}
        - Avoid highways: {prefs.get('avoid_highways', False)}
        - Stop preferences: {prefs.get('stop_preferences', [])}
        
        Return JSON with:
        {{
            "optimized_route": {{
                "total_distance": 0,
                "total_drive_time": 0,
                "route_segments": [
                    {{
                        "from": "",
                        "to": "",
                        "distance": 0,
                        "drive_time": 0,
                        "scenic_route": false,
                        "ev_charging_stops": [],
                        "recommended_stops": [],
                        "traffic_considerations": ""
                    }}
                ],
                "total_cost_estimate": 0,
                "optimization_factors": {{
                    "shortest_distance": false,
                    "fastest_time": false,
                    "most_scenic": false,
                    "ev_optimized": false
                }}
            }}
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model, prompt, input_tokens, task_type="route_optimization"
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to optimize route: {e}")
            raise

    async def optimize_budget_allocation(
        self,
        total_budget: float,
        trip_duration_days: int,
        family_count: int,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize budget allocation across trip categories."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        prefs = preferences or {}

        prompt = f"""
        Optimize budget allocation for a family trip:
        
        Total budget: ${total_budget}
        Trip duration: {trip_duration_days} days
        Number of families: {family_count}
        
        Preferences:
        - Accommodation priority: {prefs.get('accommodation_priority', 'medium')}
        - Activity priority: {prefs.get('activity_priority', 'high')}
        - Dining preference: {prefs.get('dining_preference', 'mix')}
        - Transportation mode: {prefs.get('transportation', 'rental_car')}
        
        Return JSON with:
        {{
            "budget_allocation": {{
                "total_budget": {total_budget},
                "categories": {{
                    "accommodation": {{
                        "amount": 0,
                        "percentage": 0,
                        "recommendations": ""
                    }},
                    "food": {{
                        "amount": 0,
                        "percentage": 0,
                        "recommendations": ""
                    }},
                    "activities": {{
                        "amount": 0,
                        "percentage": 0,
                        "recommendations": ""
                    }},
                    "transportation": {{
                        "amount": 0,
                        "percentage": 0,
                        "recommendations": ""
                    }},
                    "emergency": {{
                        "amount": 0,
                        "percentage": 0,
                        "recommendations": ""
                    }}
                }},
                "daily_budget": 0,
                "savings_opportunities": [],
                "cost_saving_tips": []
            }}
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model, prompt, input_tokens, task_type="budget_optimization"
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to optimize budget: {e}")
            raise

    async def get_activity_recommendations(
        self,
        location: str,
        preferences: List[str],
        family_info: Optional[Dict[str, Any]] = None,
        budget_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get AI-powered activity recommendations for a location."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        family_data = family_info or {}
        budget = budget_range or "medium"

        prompt = f"""
        Recommend family-friendly activities in {location}.
        
        Preferences: {', '.join(preferences)}
        Budget range: {budget}
        Family info:
        - Number of families: {family_data.get('family_count', 1)}
        - Age groups: {family_data.get('age_groups', ['mixed ages'])}
        - Special needs: {family_data.get('accessibility_needs', [])}
        
        Return JSON with:
        {{
            "recommendations": [
                {{
                    "title": "",
                    "description": "",
                    "category": "",
                    "duration": 0,
                    "cost_estimate": 0,
                    "rating": 0,
                    "family_friendly": true,
                    "accessibility": "",
                    "best_time_to_visit": "",
                    "booking_required": false,
                    "indoor_outdoor": "",
                    "age_recommendations": "",
                    "group_size_limit": 0,
                    "alternatives": []
                }}
            ]
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model,
                prompt,
                input_tokens,
                task_type="activity_recommendations",
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to get activity recommendations: {e}")
            raise

    async def get_restaurant_recommendations(
        self,
        location: str,
        cuisine_preferences: List[str],
        dietary_restrictions: List[str],
        budget_range: Optional[str] = None,
        family_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get AI-powered restaurant recommendations."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        family_data = family_info or {}
        budget = budget_range or "medium"

        prompt = f"""
        Recommend family-friendly restaurants in {location}.
        
        Cuisine preferences: {', '.join(cuisine_preferences) if cuisine_preferences else 'any'}
        Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'none'}
        Budget range: {budget}
        Family info:
        - Number of families: {family_data.get('family_count', 1)}
        - Kids friendly needed: {family_data.get('kids_friendly', True)}
        - Group size: {family_data.get('group_size', 4)}
        
        Return JSON with:
        {{
            "restaurants": [
                {{
                    "name": "",
                    "cuisine": "",
                    "price_range": "",
                    "rating": 0,
                    "address": "",
                    "dietary_accommodations": [],
                    "accessibility": "",
                    "family_features": [],
                    "recommended_dishes": [],
                    "reservation_required": false,
                    "average_wait_time": "",
                    "best_times": [],
                    "parking_info": ""
                }}
            ]
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model,
                prompt,
                input_tokens,
                task_type="restaurant_recommendations",
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to get restaurant recommendations: {e}")
            raise

    async def optimize_itinerary(
        self,
        current_itinerary: Dict[str, Any],
        optimization_type: str,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize an existing itinerary based on specified criteria."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        constraints_info = constraints or {}

        # Convert itinerary to string for prompt, handling datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        prompt = f"""
        Optimize this existing itinerary for {optimization_type}:
        
        Current itinerary: {json.dumps(current_itinerary, default=json_serializer)}
        
        Optimization type: {optimization_type}
        Constraints:
        - Budget limit: {constraints_info.get('budget_limit')}
        - Time constraints: {constraints_info.get('time_constraints')}
        - Must-keep activities: {constraints_info.get('must_keep', [])}
        - Accessibility requirements: {constraints_info.get('accessibility_needs', [])}
        
        Return JSON with:
        {{
            "optimized_itinerary": {{
                "overview": {{}},
                "daily_itinerary": [],
                "optimization_changes": [
                    {{
                        "day": 0,
                        "change_type": "",
                        "old_activity": "",
                        "new_activity": "",
                        "reason": ""
                    }}
                ],
                "cost_savings": 0,
                "time_savings": 0,
                "improvement_score": 0
            }}
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model, prompt, input_tokens, task_type="itinerary_optimization"
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to optimize itinerary: {e}")
            raise

    async def get_activity_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual activity suggestions during trip planning."""

        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")

        prompt = f"""
        Suggest activities based on this context:
        
        Location: {context.get('location')}
        Current activities: {context.get('current_activities', [])}
        Time of day: {context.get('time_of_day')}
        Weather: {context.get('weather')}
        Group preferences: {context.get('preferences', {})}
        Budget remaining: {context.get('budget_remaining')}
        Duration available: {context.get('duration_available')}
        
        Return JSON with:
        {{
            "suggestions": [
                {{
                    "activity": "",
                    "description": "",
                    "duration": 0,
                    "cost": 0,
                    "why_suggested": "",
                    "alternatives": [],
                    "logistics": ""
                }}
            ]
        }}
        """

        try:
            input_tokens = self.count_tokens(prompt)
            primary_model = getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
            response = await self._make_api_call(
                primary_model, prompt, input_tokens, task_type="activity_suggestions"
            )

            return json.loads(response["content"])

        except Exception as e:
            logger.error(f"Failed to get activity suggestions: {e}")
            raise


# Create global AI service instance
ai_service = AIService()


class AdvancedAIService:
    """
    Advanced AI service with enhanced cost management and graceful degradation.
    This class provides the interface expected by validation scripts and external systems.
    """

    def __init__(self):
        self.ai_service = ai_service
        self.cost_tracker = ai_service.cost_tracker
        self.fallback_responses = {
            "assistant": {
                "greeting": "Hello! I'm here to help with your trip planning. While our AI assistant is temporarily unavailable, I can still help you with basic planning tasks.",
                "suggestions": [
                    "Browse our trip templates",
                    "Use manual itinerary builder",
                    "Check out popular destinations",
                    "View family-friendly activities",
                ],
            },
            "polls": {
                "message": "Voting features are temporarily unavailable. You can still view existing poll results and create basic polls manually.",
                "alternatives": [
                    "Use group chat to discuss options",
                    "Create a simple yes/no vote",
                    "Schedule a family call to decide",
                ],
            },
            "consensus": {
                "message": "AI consensus analysis is temporarily unavailable. Here are some manual approaches to reach group decisions:",
                "strategies": [
                    "List all options and vote",
                    "Use a ranking system (1-5 stars)",
                    "Discuss pros and cons together",
                    "Try the 'elimination' method",
                ],
            },
            "itinerary": {
                "message": "AI itinerary generation is temporarily limited. Use our templates and manual tools:",
                "tools": [
                    "Pre-built destination templates",
                    "Activity suggestion database",
                    "Budget planning worksheets",
                    "Timeline and logistics helpers",
                ],
            },
        }

    def _get_fallback_response(self, context: str) -> Dict[str, Any]:
        """Get graceful fallback response when AI services are unavailable."""

        # Determine the type of request from context
        context_lower = context.lower()

        if any(word in context_lower for word in ["assistant", "help", "question"]):
            fallback_type = "assistant"
        elif any(word in context_lower for word in ["poll", "vote", "decide"]):
            fallback_type = "polls"
        elif any(word in context_lower for word in ["consensus", "agreement", "group"]):
            fallback_type = "consensus"
        elif any(word in context_lower for word in ["itinerary", "plan", "schedule"]):
            fallback_type = "itinerary"
        else:
            fallback_type = "assistant"

        base_response = self.fallback_responses.get(
            fallback_type, self.fallback_responses["assistant"]
        )

        return {
            "type": "fallback_response",
            "service": fallback_type,
            "message": base_response.get("message", base_response.get("greeting", "")),
            "suggestions": base_response.get("suggestions", []),
            "alternatives": base_response.get("alternatives", []),
            "strategies": base_response.get("strategies", []),
            "tools": base_response.get("tools", []),
            "available": True,
            "ai_available": False,
            "retry_suggestion": "You can try again later when AI services are restored.",
            "estimated_retry_time": "15-30 minutes",
        }

    async def generate_with_fallback(self, request_type: str, **kwargs) -> Dict[str, Any]:
        """Generate AI content with graceful fallback for errors."""
        try:
            # Check budget limits first
            if not self.cost_tracker.check_budget_limit(request_type):
                logger.warning(f"Budget limit exceeded for {request_type}, using fallback")
                return self._get_fallback_response(request_type)

            # Try the main AI service
            if request_type == "itinerary_generation":
                return await self.ai_service.generate_itinerary(**kwargs)
            elif request_type == "activity_enhancement":
                return await self.ai_service.enhance_activity(**kwargs)
            elif request_type == "route_optimization":
                return await self.ai_service.optimize_route(**kwargs)
            elif request_type == "budget_optimization":
                return await self.ai_service.optimize_budget_allocation(**kwargs)
            elif request_type == "activity_suggestions":
                return await self.ai_service.get_activity_suggestions(**kwargs)
            else:
                # Generic AI processing
                context = kwargs.get("context", request_type)
                return self._get_fallback_response(context)

        except ValueError as e:
            if "budget" in str(e).lower():
                logger.warning(f"Budget limit hit for {request_type}: {e}")
                return self._get_fallback_response(request_type)
            else:
                logger.error(f"AI service error for {request_type}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error in AI service for {request_type}: {e}")
            return self._get_fallback_response(request_type)

    def get_cost_status(self) -> Dict[str, Any]:
        """Get current cost and budget status."""
        usage_stats = self.ai_service.get_usage_stats()
        today = usage_stats.get("today", {})

        return {
            "daily_cost": today.get("cost", 0),
            "daily_requests": today.get("requests", 0),
            "budget_limit": usage_stats.get("budget_limit", 50.0),
            "budget_remaining": usage_stats.get("budget_remaining", 50.0),
            "models_available": usage_stats.get("models_available", []),
            "budget_status": "ok" if usage_stats.get("budget_remaining", 0) > 5 else "warning",
            "graceful_mode": usage_stats.get("budget_remaining", 0) <= 0,
        }

    def validate_request_budget(self, request_type: str = "general") -> bool:
        """Validate if a request can be processed within budget."""
        return self.cost_tracker.check_budget_limit(request_type)

    def get_optimization_suggestions(self) -> List[str]:
        """Get cost optimization suggestions."""
        return self.cost_tracker.get_optimization_suggestions()


# Create global advanced AI service instance
advanced_ai_service = AdvancedAIService()
