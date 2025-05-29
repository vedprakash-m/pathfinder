# filepath: /Users/vedprakashmishra/pathfinder/backend/app/services/ai_service.py
"""
AI service for itinerary generation using OpenAI models.
Enhanced with advanced cost optimization and multi-family preference handling.
"""

import json
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
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
        self.redis: Optional[redis.Redis] = None
        if hasattr(settings, 'REDIS_URL'):
            try:
                self.redis = redis.Redis.from_url(settings.REDIS_URL)
            except Exception:
                self.redis = None
        self.local_cache: Dict[str, Any] = {}  # Fallback local cache
        
    def _generate_cache_key(self, prompt: str, model: str, preferences: Dict[str, Any]) -> str:
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
                    return json.loads(cached.decode() if isinstance(cached, bytes) else cached)
            
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
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int, 
                   request_type: str = "general") -> float:
        """Enhanced usage tracking with request type categorization."""
        today = datetime.now().date().isoformat()
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {
                "cost": 0.0, 
                "requests": 0, 
                "models": {},
                "request_types": {}
            }
        
        self.daily_usage[today]["cost"] += cost
        self.daily_usage[today]["requests"] += 1
        
        # Track by model
        if model not in self.daily_usage[today]["models"]:
            self.daily_usage[today]["models"][model] = {"cost": 0.0, "requests": 0}
        self.daily_usage[today]["models"][model]["cost"] += cost
        self.daily_usage[today]["models"][model]["requests"] += 1
        
        # Track by request type
        if request_type not in self.daily_usage[today]["request_types"]:
            self.daily_usage[today]["request_types"][request_type] = {"cost": 0.0, "requests": 0}
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
            f"AI usage tracked: model={model}, input_tokens={input_tokens}, "
            f"output_tokens={output_tokens}, cost={cost}, request_type={request_type}, "
            f"daily_total={self.daily_usage[today]['cost']}"
        )
        
        return cost
    
    def check_budget_limit(self, request_type: str = "general") -> bool:
        """Enhanced budget checking with per-type limits."""
        today = datetime.now().date().isoformat()
        if today not in self.daily_usage:
            return True
        
        daily_cost = self.daily_usage[today]["cost"]
        
        # Check overall daily limit
        daily_limit = getattr(settings, 'AI_DAILY_BUDGET_LIMIT', 50.0)
        if daily_cost >= daily_limit:
            return False
        
        # Check request-type specific limits
        request_type_limits = {
            "itinerary_generation": daily_limit * 0.6,  # 60% for itinerary generation
            "optimization": daily_limit * 0.2,  # 20% for optimization
            "general": daily_limit * 0.2  # 20% for other requests
        }
        
        if request_type in request_type_limits:
            type_usage = self.daily_usage[today]["request_types"].get(request_type, {"cost": 0.0})
            type_cost = type_usage["cost"]
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
        daily_limit = getattr(settings, 'AI_DAILY_BUDGET_LIMIT', 50.0)
        if usage["cost"] > daily_limit * 0.8:
            suggestions.append("Approaching daily budget limit - consider request optimization")
        
        return suggestions


class MultiFamilyPreferenceEngine:
    """Engine for reconciling preferences across multiple families."""
    
    @staticmethod
    def reconcile_family_preferences(families_data: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        activity_counts = Counter(all_activities)
        
        # Select activities preferred by at least 30% of families
        threshold = max(1, len(families_data) * 0.3)
        popular_activities = [activity for activity, count in activity_counts.items() 
                            if count >= threshold]
        
        # Handle budget level conflicts (take conservative approach)
        budget_priority = {"low": 1, "medium": 2, "high": 3}
        unified_budget = "medium"
        if budget_levels:
            unified_budget = min(budget_levels, key=lambda x: budget_priority.get(x, 2))
        
        # Handle travel style (take most relaxed approach for families)
        style_priority = {"relaxed": 1, "moderate": 2, "active": 3}
        unified_style = "moderate"
        if travel_styles:
            unified_style = min(travel_styles, key=lambda x: style_priority.get(x, 2))
        
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
    def create_itinerary_prompt(
        destination: str,
        duration_days: int,
        families_data: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        budget_total: Optional[float] = None
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
            dietary_items = []
            accessibility_items = []
            
            for member in family.get("members", []):
                dietary_items.extend(member.get("dietary_restrictions", []))
                accessibility_items.extend(member.get("accessibility_needs", []))
            
            family_info.append(f"""
            Family {i} ({family.get('name', 'Unknown')}): {family_size} members
            - Ages: {', '.join(ages)}
            - Dietary restrictions: {', '.join(dietary_items) or 'None'}
            - Accessibility needs: {', '.join(accessibility_items) or 'None'}
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
        - Dining preferences: {preferences.get('dining_preferences', ['family restaurants'])}
        - Special requirements: {preferences.get('special_requirements', [])}
        
        BUDGET: {budget_info}
        
        {conflict_notes}
        
        Please provide a comprehensive itinerary in JSON format with detailed structure including 
        overview, daily_itinerary, budget_summary, logistics, and multi_family_considerations.
        
        Ensure all costs are realistic and based on current market rates. Include specific venue names, 
        addresses when possible, and practical coordination tips for managing multiple families.
        """
        
        return prompt


class AIService:
    """Enhanced AI service for generating travel itineraries with advanced features."""
    
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.cache = AICache()
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback if tiktoken is not available
            self.encoding = None
        self.preference_engine = MultiFamilyPreferenceEngine()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Rough estimation: ~4 characters per token
            return len(text) // 4
    
    def _select_optimal_model(self, request_type: str, input_tokens: int) -> str:
        """Select optimal model based on request type and complexity."""
        # Simple model selection logic - can be enhanced with ML
        primary_model = getattr(settings, 'OPENAI_MODEL_PRIMARY', 'gpt-4o-mini')
        fallback_model = getattr(settings, 'OPENAI_MODEL_FALLBACK', 'gpt-4o')
        
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
                f"Generating itinerary for {destination}: duration_days={duration_days}, "
                f"families_count={len(families_data)}, input_tokens={input_tokens}, user_id={user_id}"
            )
            
            # Try primary model first (cost-optimized)
            primary_model = getattr(settings, 'OPENAI_MODEL_PRIMARY', 'gpt-4o-mini')
            fallback_model = getattr(settings, 'OPENAI_MODEL_FALLBACK', 'gpt-4o')
            
            try:
                response = await self._make_api_call(
                    primary_model,
                    prompt,
                    input_tokens
                )
            except Exception as e:
                logger.warning(f"Primary model failed, falling back: {e}")
                # Fallback to more capable model
                response = await self._make_api_call(
                    fallback_model,
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
                f"Itinerary generated successfully: destination={destination}, "
                f"cost={response.get('cost', 0)}, user_id={user_id}"
            )
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Failed to generate itinerary: {e}, user_id={user_id}")
            raise
    
    async def _make_api_call(
        self,
        model: str,
        prompt: str,
        input_tokens: int
    ) -> Dict[str, Any]:
        """Make API call to OpenAI."""
        
        try:
            max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 4000)
            temperature = getattr(settings, 'OPENAI_TEMPERATURE', 0.7)
            timeout = getattr(settings, 'OPENAI_TIMEOUT', 60)
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": ItineraryPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                response_format={"type": "json_object"}
            )
            
            # Extract response data
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
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
            if not content:
                raise ValueError("Empty response from AI service")
                
            itinerary = json.loads(content)
            
            # Basic validation
            required_fields = ["overview", "daily_itinerary", "budget_summary"]
            for field in required_fields:
                if field not in itinerary:
                    logger.warning(f"Missing field {field}, adding default")
                    if field == "overview":
                        itinerary[field] = {"destination": "Unknown", "duration": 0}
                    elif field == "daily_itinerary":
                        itinerary[field] = []
                    elif field == "budget_summary":
                        itinerary[field] = {"total_estimated_cost": 0}
            
            # Validate daily itinerary structure
            if not isinstance(itinerary["daily_itinerary"], list):
                logger.warning("Daily itinerary is not a list, converting")
                itinerary["daily_itinerary"] = []
            
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
        participants: List[Dict[str, Any]],
        preferences: Dict[str, Any]
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
            primary_model = getattr(settings, 'OPENAI_MODEL_PRIMARY', 'gpt-4o-mini')
            response = await self._make_api_call(
                primary_model,
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
        today_usage = self.cost_tracker.daily_usage.get(today, {"cost": 0.0, "requests": 0})
        daily_limit = getattr(settings, 'AI_DAILY_BUDGET_LIMIT', 50.0)
        
        return {
            "today": today_usage,
            "budget_limit": daily_limit,
            "budget_remaining": daily_limit - today_usage["cost"],
            "models_available": list(self.cost_tracker.MODEL_COSTS.keys())
        }

    async def generate_with_cost_tracking(self, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Generate AI response with cost tracking."""
        # Check budget limit
        if not self.cost_tracker.check_budget_limit():
            raise ValueError("Daily AI budget limit exceeded")
        
        # Count input tokens
        input_tokens = self.count_tokens(prompt)
        
        logger.info(f"Generating AI response: model={model}, input_tokens={input_tokens}")
        
        try:
            max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 4000)
            temperature = getattr(settings, 'OPENAI_TEMPERATURE', 0.7)
            timeout = getattr(settings, 'OPENAI_TIMEOUT', 60)
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            # Extract response data
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
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


# Create service instance
ai_service = AIService()
