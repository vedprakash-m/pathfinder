"""
AI service for itinerary generation using OpenAI models.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

import openai
from openai import OpenAI
import tiktoken

from app.core.config import get_settings
from app.core.logging_config import create_logger
from app.services.cost_monitoring import cost_monitoring_service, ai_model_selector
from app.core.telemetry import monitoring

settings = get_settings()
logger = create_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class CostTracker:
    """Track AI model usage costs."""
    
    # Pricing per 1K tokens (as of 2024)
    MODEL_COSTS = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
    }
    
    def __init__(self):
        self.daily_usage = {}
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        if model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model for cost calculation: {model}")
            return 0.0
        
        costs = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Track daily usage and return cost."""
        today = datetime.now().date().isoformat()
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {"cost": 0, "requests": 0}
        
        self.daily_usage[today]["cost"] += cost
        self.daily_usage[today]["requests"] += 1
        
        logger.info(
            f"AI usage tracked",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            daily_total=self.daily_usage[today]["cost"]
        )
        
        return cost
    
    def check_budget_limit(self) -> bool:
        """Check if daily budget limit is exceeded."""
        today = datetime.now().date().isoformat()
        if today not in self.daily_usage:
            return True
        
        return self.daily_usage[today]["cost"] < settings.AI_DAILY_BUDGET_LIMIT


class ItineraryPrompts:
    """Template prompts for itinerary generation."""
    
    SYSTEM_PROMPT = """
    You are a professional travel planner specializing in multi-family group trips. 
    Your goal is to create detailed, realistic, and engaging itineraries that consider:
    - Multiple families with different preferences and budgets
    - Age-appropriate activities for children and adults
    - Accessibility requirements
    - Dietary restrictions and preferences
    - Transportation logistics between locations
    - Budget constraints and cost optimization
    - Local culture and authentic experiences
    
    Always provide practical, actionable recommendations with specific times, locations, and costs when possible.
    """
    
    @staticmethod
    def create_itinerary_prompt(
        destination: str,
        duration_days: int,
        families_data: List[Dict],
        preferences: Dict,
        budget_total: Optional[float] = None
    ) -> str:
        """Create a detailed prompt for itinerary generation."""
        
        # Format family information
        family_info = []
        total_participants = 0
        
        for family in families_data:
            family_size = len(family.get("members", []))
            total_participants += family_size
            
            ages = [member.get("age", "adult") for member in family.get("members", [])]
            dietary = [member.get("dietary_restrictions", []) for member in family.get("members", [])]
            accessibility = [member.get("accessibility_needs", []) for member in family.get("members", [])]
            
            family_info.append(f"""
            Family {family.get('name', 'Unknown')}: {family_size} members
            - Ages: {', '.join(map(str, ages))}
            - Dietary restrictions: {', '.join([item for sublist in dietary for item in sublist]) or 'None'}
            - Accessibility needs: {', '.join([item for sublist in accessibility for item in sublist]) or 'None'}
            """)
        
        budget_info = f"Total budget: ${budget_total:,.2f}" if budget_total else "Budget: Flexible"
        
        prompt = f"""
        Create a detailed {duration_days}-day itinerary for a group trip to {destination}.
        
        GROUP INFORMATION:
        - Total participants: {total_participants}
        - Number of families: {len(families_data)}
        {chr(10).join(family_info)}
        
        PREFERENCES:
        - Accommodation type: {preferences.get('accommodation_type', ['hotels'])}
        - Transportation: {preferences.get('transportation_mode', ['car'])}
        - Activity types: {preferences.get('activity_types', ['sightseeing'])}
        - Dining preferences: {preferences.get('dining_preferences', ['local cuisine'])}
        - Trip pace: {preferences.get('pace', 'moderate')}
        - Special requirements: {preferences.get('special_requirements', [])}
        
        BUDGET: {budget_info}
        
        Please provide a comprehensive itinerary in JSON format with the following structure:
        {{
            "overview": {{
                "destination": "{destination}",
                "duration": {duration_days},
                "total_participants": {total_participants},
                "estimated_cost_per_person": 0,
                "best_time_to_visit": "",
                "weather_info": "",
                "travel_tips": []
            }},
            "daily_itinerary": [
                {{
                    "day": 1,
                    "date": "",
                    "theme": "",
                    "activities": [
                        {{
                            "time": "09:00",
                            "activity": "",
                            "location": "",
                            "description": "",
                            "duration": "2 hours",
                            "cost_per_person": 0,
                            "booking_required": false,
                            "family_friendly": true,
                            "accessibility_notes": "",
                            "alternatives": []
                        }}
                    ],
                    "meals": [
                        {{
                            "type": "breakfast",
                            "restaurant": "",
                            "cuisine": "",
                            "cost_per_person": 0,
                            "dietary_options": [],
                            "reservation_required": false
                        }}
                    ],
                    "accommodation": {{
                        "name": "",
                        "type": "",
                        "cost_per_room": 0,
                        "amenities": [],
                        "booking_link": ""
                    }},
                    "daily_budget_breakdown": {{
                        "activities": 0,
                        "meals": 0,
                        "accommodation": 0,
                        "transportation": 0,
                        "total": 0
                    }}
                }}
            ],
            "budget_summary": {{
                "total_estimated_cost": 0,
                "cost_per_person": 0,
                "cost_breakdown": {{
                    "accommodation": 0,
                    "activities": 0,
                    "meals": 0,
                    "transportation": 0,
                    "miscellaneous": 0
                }}
            }},
            "packing_suggestions": [],
            "important_notes": [],
            "emergency_contacts": [],
            "alternative_plans": []
        }}
        
        Ensure all costs are realistic and based on current market rates. Include specific venue names, addresses when possible, and practical tips for families traveling together.
        """
        
        return prompt


class AIService:
    """AI service for generating travel itineraries."""
    
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
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


# Global AI service instance
ai_service = AIService()