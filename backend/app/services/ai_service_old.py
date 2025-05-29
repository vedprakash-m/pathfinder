"""
AI service for itinerary generation using OpenAI models.
Enhanced with advanced cost optimization and multi-family preference handling.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
from collections import Counter

import openai
from openai import OpenAI
import tiktoken
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging_config import create_logger

settings = get_settings()
logger = create_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Enhanced cache service
class AICache:
    """Redis-based caching for AI responses with intelligent cache key generation."""
    
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL) if hasattr(settings, 'REDIS_URL') else None
        self.local_cache = {}  # Fallback local cache
        
    def _generate_cache_key(self, prompt: str, model: str, preferences: Dict) -> str:
        """Generate deterministic cache key for similar requests."""
        # Create hash from prompt content and key preferences
        key_content = f"{prompt}:{model}:{json.dumps(preferences, sort_keys=True)}"
        return f"ai_cache:{hashlib.md5(key_content.encode()).hexdigest()}"
    
    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        try:
            if self.redis:
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            
            # Fallback to local cache
            return self.local_cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    async def set(self, cache_key: str, data: Dict[str, Any], ttl: int = 3600) -> None:
        """Cache response with TTL."""
        try:
            if self.redis:
                await self.redis.setex(cache_key, ttl, json.dumps(data))
            
            # Also store in local cache
            self.local_cache[cache_key] = data
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")


class CostTracker:
    """Enhanced cost tracker with budget enforcement and analytics."""
    
    # Updated pricing per 1K tokens (as of 2025)
    MODEL_COSTS = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
    }
    
    def __init__(self):
        self.daily_usage = {}
        self.usage_patterns = {}
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        if model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model for cost calculation: {model}")
            return 0.0
        
        costs = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int, 
                   request_type: str = "general") -> float:
        """Enhanced usage tracking with request type categorization."""
        today = datetime.now().date().isoformat()
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {
                "cost": 0, 
                "requests": 0, 
                "models": {},
                "request_types": {}
            }
        
        self.daily_usage[today]["cost"] += cost
        self.daily_usage[today]["requests"] += 1
        
        # Track by model
        if model not in self.daily_usage[today]["models"]:
            self.daily_usage[today]["models"][model] = {"cost": 0, "requests": 0}
        self.daily_usage[today]["models"][model]["cost"] += cost
        self.daily_usage[today]["models"][model]["requests"] += 1
        
        # Track by request type
        if request_type not in self.daily_usage[today]["request_types"]:
            self.daily_usage[today]["request_types"][request_type] = {"cost": 0, "requests": 0}
        self.daily_usage[today]["request_types"][request_type]["cost"] += cost
        self.daily_usage[today]["request_types"][request_type]["requests"] += 1
        
        # Store usage patterns for optimization
        self.usage_patterns[datetime.now().isoformat()] = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "request_type": request_type
        }
        
        logger.info(
            f"AI usage tracked",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            request_type=request_type,
            daily_total=self.daily_usage[today]["cost"]
        )
        
        return cost
    
    def check_budget_limit(self, request_type: str = "general") -> bool:
        """Enhanced budget checking with per-type limits."""
        today = datetime.now().date().isoformat()
        if today not in self.daily_usage:
            return True
        
        daily_cost = self.daily_usage[today]["cost"]
        
        # Check overall daily limit
        if daily_cost >= settings.AI_DAILY_BUDGET_LIMIT:
            return False
        
        # Check request-type specific limits
        request_type_limits = {
            "itinerary_generation": settings.AI_DAILY_BUDGET_LIMIT * 0.6,  # 60% for itinerary generation
            "optimization": settings.AI_DAILY_BUDGET_LIMIT * 0.2,  # 20% for optimization
            "general": settings.AI_DAILY_BUDGET_LIMIT * 0.2  # 20% for other requests
        }
        
        if request_type in request_type_limits:
            type_cost = self.daily_usage[today]["request_types"].get(request_type, {}).get("cost", 0)
            if type_cost >= request_type_limits[request_type]:
                return False
        
        return True
    
    def get_optimization_suggestions(self) -> List[str]:
        """Analyze usage patterns and provide optimization suggestions."""
        suggestions = []
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
        if usage["cost"] > settings.AI_DAILY_BUDGET_LIMIT * 0.8:
            suggestions.append("Approaching daily budget limit - consider request optimization")
        
        return suggestions


class MultiFamilyPreferenceEngine:
    """Engine for reconciling preferences across multiple families."""
    
    @staticmethod
    def reconcile_family_preferences(families_data: List[Dict]) -> Dict[str, Any]:
        """Reconcile conflicting preferences across multiple families."""
        if not families_data:
            return {}
        
        # Extract all preferences
        all_activities = []
        all_dietary = []
        all_accessibility = []
        budget_levels = []
        travel_styles = []
        
        for family in families_data:
            family_prefs = family.get("preferences", {})
            all_activities.extend(family_prefs.get("activities", []))
            
            for member in family.get("members", []):
                all_dietary.extend(member.get("dietary_restrictions", []))
                all_accessibility.extend(member.get("accessibility_needs", []))
            
            if "budget_level" in family_prefs:
                budget_levels.append(family_prefs["budget_level"])
            if "travel_style" in family_prefs:
                travel_styles.append(family_prefs["travel_style"])
        
        # Find common ground and create unified preferences
        # Count frequency of each preference
        from collections import Counter
        
        activity_counts = Counter(all_activities)
        
        # Select activities preferred by at least 30% of families
        threshold = max(1, len(families_data) * 0.3)
        popular_activities = [activity for activity, count in activity_counts.items() 
                            if count >= threshold]
        
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
                "activity_overlaps": dict(activity_counts)
            }
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
    def create_enhanced_itinerary_prompt(
        destination: str,
        duration_days: int,
        families_data: List[Dict],
        preferences: Dict,
        budget_total: Optional[float] = None
    ) -> str:
        """Create enhanced prompt with multi-family preference reconciliation."""
        
        # Use preference engine to reconcile family preferences
        unified_prefs = MultiFamilyPreferenceEngine.reconcile_family_preferences(families_data)
        
        # Format family information
        family_info = []
        total_participants = unified_prefs.get("total_participants", 0)
        
        for i, family in enumerate(families_data, 1):
            family_size = len(family.get("members", []))
            
            ages = [member.get("age", "adult") for member in family.get("members", [])]
            dietary = [member.get("dietary_restrictions", []) for member in family.get("members", [])]
            accessibility = [member.get("accessibility_needs", []) for member in family.get("members", [])]
            
            family_info.append(f"""
            Family {i} ({family.get('name', 'Unknown')}): {family_size} members
            - Ages: {', '.join(map(str, ages))}
            - Dietary restrictions: {', '.join([item for sublist in dietary for item in sublist]) or 'None'}
            - Accessibility needs: {', '.join([item for sublist in accessibility for item in sublist]) or 'None'}
            - Preferences: {family.get('preferences', {})}
            """)
        
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
        {chr(10).join(family_info)}
        
        UNIFIED PREFERENCES (reconciled across families):
        - Popular activities: {unified_prefs.get('unified_activities', [])}
        - All dietary restrictions: {unified_prefs.get('all_dietary_restrictions', [])}
        - All accessibility needs: {unified_prefs.get('all_accessibility_needs', [])}
        - Budget level: {unified_prefs.get('unified_budget_level', 'medium')}
        - Travel style: {unified_prefs.get('unified_travel_style', 'moderate')}
        
        ORIGINAL PREFERENCES:
        - Accommodation type: {preferences.get('accommodation_type', ['family-friendly hotels'])}
        - Transportation: {preferences.get('transportation_mode', ['rental cars'])}
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
            "daily_itinerary": [
                {{
                    "day": 1,
                    "date": "",
                    "theme": "",
                    "morning_meetup": {{
                        "time": "09:00",
                        "location": "",
                        "coordination_notes": ""
                    }},
                    "activities": [
                        {{
                            "time": "09:00",
                            "activity": "",
                            "location": "",
                            "description": "",
                            "duration": "2 hours",
                            "cost_per_person": 0,
                            "group_size_accommodated": "{total_participants}",
                            "booking_required": false,
                            "advance_booking_days": 0,
                            "family_friendly": true,
                            "age_suitability": "all ages",
                            "accessibility_notes": "",
                            "activity_type": "group",
                            "alternatives": [],
                            "weather_dependency": "none",
                            "logistics_notes": "",
                            "cost_splitting_suggestion": ""
                        }}
                    ],
                    "meals": [
                        {{
                            "type": "breakfast",
                            "restaurant": "",
                            "cuisine": "",
                            "cost_per_person": 0,
                            "group_capacity": {total_participants},
                            "dietary_options": [],
                            "reservation_required": false,
                            "kid_friendly": true,
                            "parking_available": true
                        }}
                    ],
                    "accommodation": {{
                        "name": "",
                        "type": "",
                        "rooms_needed": 0,
                        "cost_per_room": 0,
                        "amenities": [],
                        "family_amenities": [],
                        "booking_link": "",
                        "cancellation_policy": ""
                    }},
                    "daily_budget_breakdown": {{
                        "activities": 0,
                        "meals": 0,
                        "accommodation": 0,
                        "transportation": 0,
                        "parking": 0,
                        "total": 0,
                        "per_family_estimate": 0
                    }},
                    "coordination_notes": [],
                    "backup_plan": ""
                }}
            ],
            "budget_summary": {{
                "total_estimated_cost": 0,
                "cost_per_person": 0,
                "cost_per_family": 0,
                "cost_breakdown": {{
                    "accommodation": 0,
                    "activities": 0,
                    "meals": 0,
                    "transportation": 0,
                    "parking": 0,
                    "miscellaneous": 0
                }},
                "cost_saving_tips": [],
                "group_discounts_available": []
            }},
            "logistics": {{
                "coordination_strategy": "",
                "communication_plan": "",
                "meeting_points": [],
                "emergency_procedures": [],
                "parking_arrangements": [],
                "transportation_coordination": ""
            }},
            "packing_suggestions": {{
                "for_families": [],
                "for_kids": [],
                "weather_specific": [],
                "activity_specific": []
            }},
            "important_notes": [],
            "emergency_contacts": [],
            "alternative_plans": {{
                "rainy_day_activities": [],
                "budget_conscious_alternatives": [],
                "shorter_duration_options": []
            }},
            "multi_family_considerations": {{
                "preference_compromises": [],
                "conflict_resolution_notes": [],
                "family_bonding_opportunities": [],
                "individual_family_time_suggestions": []
            }}
        }}
        
        Ensure all costs are realistic and based on current market rates. Include specific venue names, 
        addresses when possible, and practical coordination tips for managing multiple families.
        Consider logistics like parking for multiple vehicles, restaurant reservations for large groups, 
        and activities that can accommodate varying energy levels and interests.
        """
        
        return prompt


class AIService:
    """Enhanced AI service for generating travel itineraries with advanced features."""
    
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.cache = AICache()
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.preference_engine = MultiFamilyPreferenceEngine()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def _select_optimal_model(self, request_type: str, input_tokens: int) -> str:
        """Select optimal model based on request type and complexity."""
        # Simple model selection logic - can be enhanced with ML
        if request_type == "itinerary_generation":
            if input_tokens > 3000:  # Complex multi-family request
                return settings.OPENAI_MODEL_FALLBACK  # gpt-4o
            else:
                return settings.OPENAI_MODEL_PRIMARY  # gpt-4o-mini
        
        return settings.OPENAI_MODEL_PRIMARY
    
    async def generate_itinerary(
        self,
        destination: str,
        duration_days: int,
        families_data: List[Dict],
        preferences: Dict,
        budget_total: Optional[float] = None,
        user_id: Optional[str] = None
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
                user_id=user_id
            )
            
            # Try primary model first (cost-optimized)
            try:
                response = await self._make_api_call(
                    settings.OPENAI_MODEL_PRIMARY,
                    prompt,
                    input_tokens
                )
            except Exception as e:
                logger.warning(f"Primary model failed, falling back: {e}")
                # Fallback to more capable model
                response = await self._make_api_call(
                    settings.OPENAI_MODEL_FALLBACK,
                    prompt,
                    input_tokens
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
                "output_tokens": response.get("output_tokens", 0)
            }
            
            logger.info(
                "Itinerary generated successfully",
                destination=destination,
                cost=response.get("cost", 0),
                user_id=user_id
            )
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Failed to generate itinerary: {e}", user_id=user_id)
            raise
    
    async def _make_api_call(
        self,
        model: str,
        prompt: str,
        input_tokens: int
    ) -> Dict[str, Any]:
        """Make API call to OpenAI."""
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": ItineraryPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                timeout=settings.OPENAI_TIMEOUT,
                response_format={"type": "json_object"}
            )
            
            # Extract response data
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens
            
            # Track costs
            cost = self.cost_tracker.track_usage(model, input_tokens, output_tokens)
            
            return {
                "content": content,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost
            }
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise ValueError("AI service temporarily unavailable due to rate limits")
        except openai.APITimeoutError:
            logger.error("OpenAI API timeout")
            raise ValueError("AI service timeout - please try again")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise ValueError(f"AI service error: {str(e)}")
    
    def _parse_itinerary_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            content = response["content"]
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
            raise ValueError("Invalid AI response format")
        except Exception as e:
            logger.error(f"Failed to validate AI response: {e}")
            raise ValueError(f"AI response validation failed: {str(e)}")
    
    async def enhance_activity(
        self,
        activity_name: str,
        location: str,
        participants: List[Dict],
        preferences: Dict
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Failed to enhance activity: {e}")
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        today = datetime.now().date().isoformat()
        today_usage = self.cost_tracker.daily_usage.get(today, {"cost": 0, "requests": 0})
        
        return {
            "today": today_usage,
            "budget_limit": settings.AI_DAILY_BUDGET_LIMIT,
            "budget_remaining": settings.AI_DAILY_BUDGET_LIMIT - today_usage["cost"],
            "models_available": list(self.cost_tracker.MODEL_COSTS.keys())
        }

    async def generate_with_cost_tracking(self, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Generate AI response with cost tracking."""
        # Check budget limit
        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")
        
        # Count input tokens
        input_tokens = self.count_tokens(prompt)
        
        logger.info(
            f"Generating AI response",
            model=model,
            input_tokens=input_tokens
        )
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                timeout=settings.OPENAI_TIMEOUT
            )
            
            # Extract response data
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens
            
            # Track costs
            cost = self.cost_tracker.track_usage(model, input_tokens, output_tokens)
            
            return {
                "content": content,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost
            }
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise ValueError("AI service temporarily unavailable due to rate limits")
        except openai.APITimeoutError:
            logger.error("OpenAI API timeout")
            raise ValueError("AI service timeout - please try again")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise ValueError(f"AI service error: {str(e)}")
    
    async def optimize_route(
        self,
        destinations: List[str],
        vehicle_constraints: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
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
        preferences: Optional[Dict[str, Any]] = None
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
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
        budget_range: Optional[str] = None
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
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
        family_info: Optional[Dict[str, Any]] = None
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Failed to get restaurant recommendations: {e}")
            raise
    
    async def optimize_itinerary(
        self,
        current_itinerary: Dict[str, Any],
        optimization_type: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize an existing itinerary based on specified criteria."""
        
        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")
        
        constraints_info = constraints or {}
        
        prompt = f"""
        Optimize this existing itinerary for {optimization_type}:
        
        Current itinerary: {json.dumps(current_itinerary, default=str)}
        
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Failed to optimize itinerary: {e}")
            raise
    
    async def get_activity_suggestions(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            response = await self._make_api_call(
                settings.OPENAI_MODEL_PRIMARY,
                prompt,
                input_tokens
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Failed to get activity suggestions: {e}")
            raise