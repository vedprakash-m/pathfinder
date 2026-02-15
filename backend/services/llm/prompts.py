"""
LLM Prompts

System prompts and prompt builders for AI features.
"""

from typing import Any

# System prompt for itinerary generation
ITINERARY_SYSTEM_PROMPT = """You are an expert travel planner assistant for Pathfinder, an AI-powered multi-family trip planning app.

Your role is to create detailed, practical itineraries for family groups traveling together. Consider:

1. **Family-Friendly Activities**: Include activities suitable for all ages when families with children are involved
2. **Balanced Pacing**: Mix active excursions with relaxation time
3. **Logistics**: Consider travel times between locations, meal times, and rest breaks
4. **Budget Awareness**: Respect budget constraints when provided
5. **Local Experiences**: Include authentic local experiences alongside popular attractions
6. **Flexibility**: Build in free time and backup options for weather-dependent activities

Always respond with a valid JSON object in this format:
{
    "summary": "Brief 2-3 sentence overview of the itinerary",
    "days": [
        {
            "day_number": 1,
            "date": "2026-06-01T00:00:00Z",
            "title": "Arrival & Exploration",
            "activities": [
                {
                    "time": "09:00",
                    "duration_minutes": 120,
                    "title": "Activity name",
                    "description": "Detailed description",
                    "location": "Location name",
                    "cost_estimate": 50.00,
                    "booking_required": false,
                    "family_friendly": true
                }
            ],
            "meals": [
                {
                    "type": "lunch",
                    "time": "12:30",
                    "suggestion": "Restaurant name or meal type",
                    "cost_estimate": 30.00
                }
            ],
            "accommodation": {
                "name": "Hotel/Airbnb name",
                "check_in": "15:00",
                "notes": "Any relevant notes"
            },
            "notes": "Day-specific notes or tips"
        }
    ]
}
"""

# System prompt for the AI assistant
ASSISTANT_SYSTEM_PROMPT = """You are Pathfinder's AI travel assistant, helping families plan amazing trips together.

Your capabilities:
- Answer questions about destinations, activities, and travel logistics
- Provide recommendations based on user preferences
- Help with budget planning and cost estimates
- Suggest activities suitable for multi-generational groups
- Offer tips for traveling with children

Communication style:
- Be friendly, helpful, and concise
- Use a warm, conversational tone appropriate for family audiences
- Provide actionable suggestions
- When uncertain, acknowledge limitations and suggest alternatives
- Respect cultural sensitivities and diverse family structures

Context awareness:
- You may receive information about the current trip being planned
- Use this context to provide relevant, personalized suggestions
- Consider all participating families' preferences when applicable

Always maintain user privacy and avoid requesting sensitive personal information."""


def build_itinerary_prompt(trip: Any, preferences: dict[str, Any] | None = None) -> str:
    """
    Build a prompt for itinerary generation.

    Args:
        trip: TripDocument with trip details
        preferences: Optional generation preferences

    Returns:
        Formatted prompt string
    """
    # Base trip info
    prompt_parts = [
        "Please create a detailed travel itinerary for the following trip:",
        "",
        f"**Destination:** {trip.destination or 'To be determined'}",
    ]

    # Add dates if available
    if trip.start_date and trip.end_date:
        duration = (trip.end_date - trip.start_date).days + 1
        prompt_parts.append(f"**Dates:** {trip.start_date.strftime('%B %d')} to {trip.end_date.strftime('%B %d, %Y')}")
        prompt_parts.append(f"**Duration:** {duration} days")

    # Add budget if available
    if trip.budget:
        prompt_parts.append(f"**Budget:** {trip.currency} {trip.budget:.2f} total")

    # Add trip description
    if trip.description:
        prompt_parts.append(f"**Trip Notes:** {trip.description}")

    # Add preferences if provided
    if preferences:
        prompt_parts.append("")
        prompt_parts.append("**Preferences:**")

        if preferences.get("activity_level"):
            prompt_parts.append(f"- Activity level: {preferences['activity_level']}")

        if preferences.get("interests"):
            prompt_parts.append(f"- Interests: {', '.join(preferences['interests'])}")

        if preferences.get("budget_per_day"):
            prompt_parts.append(f"- Daily budget: ${preferences['budget_per_day']:.2f}")

        if preferences.get("dietary_restrictions"):
            prompt_parts.append(f"- Dietary restrictions: {', '.join(preferences['dietary_restrictions'])}")

        if preferences.get("accessibility_needs"):
            prompt_parts.append(f"- Accessibility needs: {preferences['accessibility_needs']}")

    # Add instructions
    prompt_parts.extend(
        [
            "",
            "Please create a comprehensive day-by-day itinerary in JSON format.",
            "Include specific activity recommendations, estimated costs, and practical logistics.",
            "Ensure activities are suitable for multi-family groups.",
        ]
    )

    return "\n".join(prompt_parts)


def build_assistant_prompt(
    message: str, trip: Any | None = None, conversation_history: list[dict[str, str]] | None = None
) -> str:
    """
    Build a prompt for the AI assistant.

    Args:
        message: User's message
        trip: Optional current trip context
        conversation_history: Optional previous messages

    Returns:
        Formatted prompt string
    """
    prompt_parts = []

    # Add trip context if available
    if trip:
        prompt_parts.extend(
            [
                "**Current Trip Context:**",
                f"- Destination: {trip.destination or 'Not set'}",
                f"- Status: {trip.status}",
            ]
        )

        if trip.start_date:
            prompt_parts.append(
                f"- Dates: {trip.start_date.strftime('%B %d')} - {trip.end_date.strftime('%B %d, %Y') if trip.end_date else 'TBD'}"
            )

        if trip.budget:
            prompt_parts.append(f"- Budget: {trip.currency} {trip.budget:.2f}")

        prompt_parts.append("")

    # Add user message
    prompt_parts.append(f"**User Question:**\n{message}")

    return "\n".join(prompt_parts)


def build_consensus_prompt(poll_results: list[dict[str, Any]], trip_context: dict[str, Any] | None = None) -> str:
    """
    Build a prompt for consensus analysis.

    Args:
        poll_results: List of poll results to analyze
        trip_context: Optional trip context

    Returns:
        Formatted prompt string
    """
    prompt_parts = ["Analyze the following poll results and provide a consensus recommendation:", ""]

    for i, poll in enumerate(poll_results, 1):
        prompt_parts.append(f"**Poll {i}: {poll.get('title', 'Untitled')}**")

        for option in poll.get("options", []):
            votes = option.get("vote_count", 0)
            prompt_parts.append(f"  - {option.get('text')}: {votes} votes")

        prompt_parts.append("")

    prompt_parts.extend(
        [
            "Based on these results, provide:",
            "1. A summary of the group's preferences",
            "2. The recommended choice(s) that best satisfy the majority",
            "3. Any suggestions for accommodating minority preferences",
        ]
    )

    return "\n".join(prompt_parts)
