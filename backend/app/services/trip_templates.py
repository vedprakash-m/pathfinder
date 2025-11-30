"""
Trip Template Service - Pre-configured trip templates for Golden Path onboarding.

This service provides realistic trip templates that demonstrate the platform's value
within 60 seconds of onboarding start, per PRD requirements.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List


class TripTemplateType(str, Enum):
    """Supported trip template types."""

    WEEKEND_GETAWAY = "weekend_getaway"
    FAMILY_VACATION = "family_vacation"
    ADVENTURE_TRIP = "adventure_trip"


class TripTemplateService:
    """Service for managing trip templates."""

    @staticmethod
    def get_template(template_type: TripTemplateType) -> Dict[str, Any]:
        """
        Get a complete trip template by type.

        Returns a dictionary with all trip data including:
        - Basic trip info (name, description, dates)
        - Budget breakdown
        - Sample activities
        - Decision scenarios for consensus demo
        - Sample families for demonstration
        """
        templates = {
            TripTemplateType.WEEKEND_GETAWAY: {
                "name": "Napa Valley Family Weekend",
                "description": "A delightful weekend escape to California's wine country with family-friendly activities for all ages",
                "destination": "Napa Valley, California",
                "start_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "end_date": (datetime.now() + timedelta(days=33)).isoformat(),
                "duration_days": 3,
                "budget": 1200.0,
                "budget_breakdown": {
                    "accommodation": 400.0,
                    "activities": 450.0,
                    "food": 300.0,
                    "transportation": 50.0,
                },
                "activities": [
                    {
                        "name": "Family-friendly wineries",
                        "description": "Visit wineries with kids' activities and grape juice tastings",
                        "duration": "3-4 hours",
                        "cost": 80.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Hot air balloon ride",
                        "description": "Early morning balloon ride over vineyards",
                        "duration": "2-3 hours",
                        "cost": 200.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Oxbow Public Market",
                        "description": "Explore local food vendors and artisan shops",
                        "duration": "2 hours",
                        "cost": 50.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Castello di Amorosa",
                        "description": "Tour the authentic Tuscan castle and winery",
                        "duration": "2 hours",
                        "cost": 120.0,
                        "difficulty": "Easy",
                    },
                ],
                "decision_scenarios": [
                    {
                        "title": "Balloon Ride Timing",
                        "question": "When should we schedule the hot air balloon ride?",
                        "options": [
                            "Early morning (6 AM) - Best weather and views",
                            "Late afternoon (4 PM) - Kids prefer sleeping in",
                        ],
                        "context": "Weather is best in morning, but kids prefer afternoon",
                        "poll_type": "TIMING_PREFERENCE",
                    },
                    {
                        "title": "Winery Selection",
                        "question": "Which family-friendly winery should we visit?",
                        "options": [
                            "V. Sattui Winery - Great picnic grounds",
                            "Grgich Hills Estate - Educational tours",
                            "Sterling Vineyards - Aerial tram experience",
                        ],
                        "context": "All are kid-friendly with different unique features",
                        "poll_type": "DESTINATION_CHOICE",
                    },
                ],
                "sample_families": [
                    {
                        "name": "The Johnsons",
                        "members": 4,
                        "adults": 2,
                        "children": 2,
                        "ages": [35, 37, 8, 10],
                        "preferences": ["Wine tasting", "Kid activities", "Photography"],
                    },
                    {
                        "name": "The Garcias",
                        "members": 3,
                        "adults": 2,
                        "children": 1,
                        "ages": [32, 34, 6],
                        "preferences": ["Food tours", "Relaxation", "Shopping"],
                    },
                ],
                "tags": ["Weekend", "Wine Country", "Family-Friendly", "California"],
            },
            TripTemplateType.FAMILY_VACATION: {
                "name": "Yellowstone National Park Adventure",
                "description": "A week-long family adventure exploring America's first national park with wildlife, geysers, and stunning landscapes",
                "destination": "Yellowstone National Park, Wyoming",
                "start_date": (datetime.now() + timedelta(days=60)).isoformat(),
                "end_date": (datetime.now() + timedelta(days=67)).isoformat(),
                "duration_days": 7,
                "budget": 3200.0,
                "budget_breakdown": {
                    "accommodation": 1200.0,
                    "activities": 800.0,
                    "food": 900.0,
                    "transportation": 300.0,
                },
                "activities": [
                    {
                        "name": "Old Faithful viewing",
                        "description": "Watch the iconic geyser erupt on schedule",
                        "duration": "2 hours",
                        "cost": 0.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Wildlife safari tour",
                        "description": "Guided tour to spot bison, elk, and bears",
                        "duration": "4 hours",
                        "cost": 150.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Grand Prismatic Spring",
                        "description": "Hike to viewpoint of the colorful hot spring",
                        "duration": "3 hours",
                        "cost": 0.0,
                        "difficulty": "Moderate",
                    },
                    {
                        "name": "Junior Ranger Program",
                        "description": "Kids earn badges while learning about the park",
                        "duration": "All week",
                        "cost": 0.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Mammoth Hot Springs",
                        "description": "Explore terraced limestone formations",
                        "duration": "2 hours",
                        "cost": 0.0,
                        "difficulty": "Easy",
                    },
                ],
                "decision_scenarios": [
                    {
                        "title": "Accommodation Location",
                        "question": "Where should we stay?",
                        "options": [
                            "Inside the park (Old Faithful Inn) - Convenient but pricier",
                            "West Yellowstone town - More amenities and restaurants",
                            "Gardiner entrance - Budget-friendly with good access",
                        ],
                        "context": "Trade-off between convenience and cost",
                        "poll_type": "ACCOMMODATION_CHOICE",
                    },
                    {
                        "title": "Activity Pace",
                        "question": "How should we pace our activities?",
                        "options": [
                            "Relaxed - 1-2 activities per day with rest time",
                            "Moderate - 2-3 activities per day",
                            "Packed - Try to see everything possible",
                        ],
                        "context": "Kids' energy levels vs. seeing all highlights",
                        "poll_type": "ACTIVITY_PREFERENCE",
                    },
                ],
                "sample_families": [
                    {
                        "name": "The Smiths",
                        "members": 5,
                        "adults": 2,
                        "children": 3,
                        "ages": [40, 42, 12, 10, 7],
                        "preferences": ["Wildlife", "Hiking", "Photography", "Education"],
                    },
                    {
                        "name": "The Chens",
                        "members": 4,
                        "adults": 2,
                        "children": 2,
                        "ages": [38, 39, 14, 11],
                        "preferences": ["Nature", "Camping", "Adventure", "Stargazing"],
                    },
                    {
                        "name": "The Patels",
                        "members": 3,
                        "adults": 2,
                        "children": 1,
                        "ages": [35, 36, 9],
                        "preferences": ["Geology", "Hot springs", "Scenic drives"],
                    },
                ],
                "tags": ["Nature", "Wildlife", "National Park", "Educational", "Family"],
            },
            TripTemplateType.ADVENTURE_TRIP: {
                "name": "Costa Rica Eco-Adventure",
                "description": "An action-packed adventure through rainforests, beaches, and volcanic landscapes with zip-lining, wildlife, and cultural experiences",
                "destination": "Costa Rica (Arenal & Manuel Antonio)",
                "start_date": (datetime.now() + timedelta(days=90)).isoformat(),
                "end_date": (datetime.now() + timedelta(days=100)).isoformat(),
                "duration_days": 10,
                "budget": 4500.0,
                "budget_breakdown": {
                    "accommodation": 1500.0,
                    "activities": 1500.0,
                    "food": 1000.0,
                    "transportation": 500.0,
                },
                "activities": [
                    {
                        "name": "Zip-lining through cloud forest",
                        "description": "World-class canopy tour with 10+ zip lines",
                        "duration": "3 hours",
                        "cost": 100.0,
                        "difficulty": "Moderate",
                    },
                    {
                        "name": "Arenal Volcano hike",
                        "description": "Hike around the active volcano and hot springs",
                        "duration": "4 hours",
                        "cost": 50.0,
                        "difficulty": "Moderate",
                    },
                    {
                        "name": "Wildlife spotting tour",
                        "description": "See sloths, monkeys, toucans, and more",
                        "duration": "3 hours",
                        "cost": 80.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "White water rafting",
                        "description": "Class II-III rapids on Balsa River",
                        "duration": "5 hours",
                        "cost": 120.0,
                        "difficulty": "Challenging",
                    },
                    {
                        "name": "Manuel Antonio beach day",
                        "description": "Pristine beaches and snorkeling",
                        "duration": "Full day",
                        "cost": 30.0,
                        "difficulty": "Easy",
                    },
                    {
                        "name": "Coffee plantation tour",
                        "description": "Learn about coffee production and taste fresh brews",
                        "duration": "2 hours",
                        "cost": 40.0,
                        "difficulty": "Easy",
                    },
                ],
                "decision_scenarios": [
                    {
                        "title": "Adventure Level",
                        "question": "What intensity of activities should we focus on?",
                        "options": [
                            "High Adventure - Rafting, zip-lining, challenging hikes",
                            "Moderate Mix - Balance of adventure and relaxation",
                            "Relaxed Eco-Tourism - Wildlife, beaches, cultural experiences",
                        ],
                        "context": "Different fitness levels and adventure preferences",
                        "poll_type": "ACTIVITY_PREFERENCE",
                    },
                    {
                        "title": "Accommodation Style",
                        "question": "Where should we stay?",
                        "options": [
                            "Eco-lodge in rainforest - Immersive nature experience",
                            "Beach resort in Manuel Antonio - Comfort and amenities",
                            "Mix of both - Split time between locations",
                        ],
                        "context": "Experience style vs. convenience trade-off",
                        "poll_type": "ACCOMMODATION_CHOICE",
                    },
                ],
                "sample_families": [
                    {
                        "name": "The Andersons",
                        "members": 4,
                        "adults": 2,
                        "children": 2,
                        "ages": [36, 38, 15, 13],
                        "preferences": ["Adventure", "Wildlife", "Photography", "Eco-tourism"],
                    },
                    {
                        "name": "The Thompsons",
                        "members": 5,
                        "adults": 2,
                        "children": 3,
                        "ages": [41, 42, 16, 14, 11],
                        "preferences": ["Zip-lining", "Beaches", "Cultural experiences", "Food"],
                    },
                ],
                "tags": ["Adventure", "Eco-Tourism", "International", "Wildlife", "Active"],
            },
        }

        return templates.get(template_type, templates[TripTemplateType.WEEKEND_GETAWAY])

    @staticmethod
    def get_all_template_types() -> List[str]:
        """Get list of all available template types."""
        return [t.value for t in TripTemplateType]

    @staticmethod
    def validate_template_type(template_type: str) -> bool:
        """Validate if a template type is supported."""
        return template_type in [t.value for t in TripTemplateType]
