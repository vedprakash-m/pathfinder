"""
Family Consensus Engine - Solves the #1 pain point: achieving consensus across multiple families.

Features:
- Weighted preference aggregation
- Conflict detection and resolution
- AI-powered compromise suggestions
- Visual consensus dashboard data
- Simple voting mechanisms
"""

import logging
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConflictSeverity(Enum):
    """Severity levels for preference conflicts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VoteStatus(Enum):
    """Voting status for decisions."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_DISCUSSION = "needs_discussion"


@dataclass
class FamilyWeight:
    """Weighting factors for families in consensus calculation."""

    family_id: str
    family_name: str
    participant_count: int
    budget_contribution: float  # Percentage of total budget
    admin_bonus: float = 0.1  # Extra weight for trip organizer family

    @property
    def total_weight(self) -> float:
        """Calculate total weight for this family."""
        # Base weight: 40% equal per family, 30% by participant count, 30% by budget
        base_weight = 0.4
        participant_weight = 0.3 * (self.participant_count / 10)  # Normalize to max 10 participants
        budget_weight = 0.3 * self.budget_contribution

        return base_weight + participant_weight + budget_weight + self.admin_bonus


@dataclass
class PreferenceConflict:
    """Represents a conflict between families' preferences."""

    category: str
    conflicting_values: List[Any]
    families_involved: List[str]
    severity: ConflictSeverity
    suggested_compromise: Optional[str] = None
    ai_explanation: Optional[str] = None


@dataclass
class ConsensusResult:
    """Result of consensus calculation."""

    consensus_score: float  # 0-1, higher = better consensus
    agreed_preferences: Dict[str, Any]
    conflicts: List[PreferenceConflict]
    voting_items: List[Dict[str, Any]]
    compromise_suggestions: Dict[str, Any]
    next_steps: List[str]


@dataclass
class VotingItem:
    """Item requiring family votes."""

    id: str
    category: str
    question: str
    options: List[str]
    current_votes: Dict[str, str]  # family_id -> option
    threshold: float = 0.6  # 60% agreement needed
    status: VoteStatus = VoteStatus.PENDING
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class FamilyConsensusEngine:
    """
    Main engine for achieving consensus across multiple families.

    Addresses the #1 pain point: "Lack of mechanism to achieve consensus on optimal plans
    across families with varying preferences"
    """

    def __init__(self):
        self.consensus_threshold = 0.7  # 70% agreement needed for auto-approval
        self.conflict_threshold = 0.3  # 30% disagreement triggers conflict resolution

    def generate_weighted_consensus(
        self, families_data: List[Dict[str, Any]], total_budget: float
    ) -> ConsensusResult:
        """Generate consensus using weighted family preferences."""

        # Calculate family weights
        family_weights = self.calculate_family_weights(families_data, total_budget)

        # Detect conflicts
        conflicts = self.detect_preference_conflicts(families_data)

        # Generate weighted preferences
        weighted_prefs = self._calculate_weighted_preferences(families_data, family_weights)

        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(conflicts, len(families_data))

        # Generate voting items for unresolved conflicts
        voting_items = self._generate_voting_items(conflicts)

        # Generate AI compromise suggestions
        compromise_suggestions = self._generate_ai_compromises(conflicts, weighted_prefs)

        # Generate next steps
        next_steps = self._generate_next_steps(consensus_score, conflicts, voting_items)

        return ConsensusResult(
            consensus_score=consensus_score,
            agreed_preferences=weighted_prefs,
            conflicts=conflicts,
            voting_items=voting_items,
            compromise_suggestions=compromise_suggestions,
            next_steps=next_steps,
        )

    def calculate_family_weights(
        self, families_data: List[Dict[str, Any]], total_budget: float
    ) -> List[FamilyWeight]:
        """Calculate weighted influence for each family."""
        family_weights = []

        for family in families_data:
            family_id = family.get("id", "")
            family_name = family.get("name", "Unknown Family")
            participant_count = len(family.get("members", []))
            budget_allocation = family.get("budget_allocation", 0)
            is_admin = family.get("is_trip_admin", False)

            # Calculate budget contribution percentage
            budget_contribution = (
                budget_allocation / total_budget if total_budget > 0 else 1.0 / len(families_data)
            )
            admin_bonus = 0.1 if is_admin else 0.0

            weight = FamilyWeight(
                family_id=family_id,
                family_name=family_name,
                participant_count=participant_count,
                budget_contribution=budget_contribution,
                admin_bonus=admin_bonus,
            )

            family_weights.append(weight)

        return family_weights

    def detect_preference_conflicts(
        self, families_data: List[Dict[str, Any]]
    ) -> List[PreferenceConflict]:
        """Identify conflicts between family preferences."""
        conflicts = []

        # Group preferences by category
        preference_categories = {}
        for family in families_data:
            family_id = family.get("id", "")
            family_name = family.get("name", "Unknown")
            preferences = family.get("preferences", {})

            for category, value in preferences.items():
                if category not in preference_categories:
                    preference_categories[category] = {}
                preference_categories[category][family_id] = {
                    "value": value,
                    "family_name": family_name,
                }

        # Check for conflicts in each category
        for category, family_prefs in preference_categories.items():
            if len(family_prefs) < 2:
                continue

            values = [data["value"] for data in family_prefs.values()]
            unique_values = list(set(str(v) for v in values))

            # Conflict exists if families have different preferences
            if len(unique_values) > 1:
                # Calculate severity based on how different the values are
                severity = self._calculate_conflict_severity(category, values)

                conflict = PreferenceConflict(
                    category=category,
                    conflicting_values=unique_values,
                    families_involved=[fid for fid in family_prefs.keys()],
                    severity=severity,
                    suggested_compromise=self._suggest_compromise(category, values),
                )

                conflicts.append(conflict)

        return conflicts

    def _calculate_conflict_severity(self, category: str, values: List[Any]) -> ConflictSeverity:
        """Calculate the severity of a preference conflict."""
        # Critical conflicts (safety/accessibility related)
        critical_categories = [
            "accessibility_needs",
            "dietary_restrictions",
            "medical_requirements",
        ]
        if category in critical_categories:
            return ConflictSeverity.CRITICAL

        # High conflicts (budget/accommodation)
        high_categories = ["budget_level", "accommodation_type", "transportation_mode"]
        if category in high_categories:
            return ConflictSeverity.HIGH

        # Calculate disagreement level
        unique_values = len(set(str(v) for v in values))
        total_values = len(values)
        disagreement_ratio = unique_values / total_values

        if disagreement_ratio > 0.8:
            return ConflictSeverity.HIGH
        elif disagreement_ratio > 0.5:
            return ConflictSeverity.MEDIUM
        else:
            return ConflictSeverity.LOW

    def _suggest_compromise(self, category: str, values: List[Any]) -> str:
        """Suggest a compromise for conflicting preferences."""
        if not values:
            return "No compromise needed"

        # Category-specific compromise logic
        if category == "budget_level":
            # Take the more conservative budget
            budget_priority = {"low": 1, "medium": 2, "high": 3}
            conservative_budget = min(values, key=lambda x: budget_priority.get(str(x).lower(), 2))
            return f"Use conservative budget: {conservative_budget}"

        elif category == "activity_level":
            # Take more relaxed activity level for families
            activity_priority = {"relaxed": 1, "moderate": 2, "active": 3}
            relaxed_level = min(values, key=lambda x: activity_priority.get(str(x).lower(), 2))
            return f"Use family-friendly level: {relaxed_level}"

        elif category == "activities":
            # Find common activities
            all_activities = []
            for val in values:
                if isinstance(val, list):
                    all_activities.extend(val)
                else:
                    all_activities.append(val)
            common_activities = [
                item for item, count in Counter(all_activities).items() if count > 1
            ]
            return f"Focus on shared interests: {', '.join(common_activities[:3])}"

        else:
            # Generic compromise - most popular choice
            value_counts = Counter(str(v) for v in values)
            most_popular = value_counts.most_common(1)[0][0]
            return f"Use most popular choice: {most_popular}"

    def _calculate_weighted_preferences(
        self, families_data: List[Dict[str, Any]], family_weights: List[FamilyWeight]
    ) -> Dict[str, Any]:
        """Calculate preferences using family weights."""
        weighted_prefs = {}
        weight_map = {fw.family_id: fw.total_weight for fw in family_weights}

        # Collect all preference categories
        all_categories = set()
        for family in families_data:
            all_categories.update(family.get("preferences", {}).keys())

        for category in all_categories:
            category_values = []
            category_weights = []

            for family in families_data:
                family_id = family.get("id", "")
                prefs = family.get("preferences", {})

                if category in prefs:
                    value = prefs[category]
                    weight = weight_map.get(family_id, 1.0)

                    category_values.append(value)
                    category_weights.append(weight)

            # Calculate weighted result for this category
            if category_values:
                weighted_result = self._weighted_preference_calculation(
                    category, category_values, category_weights
                )
                weighted_prefs[category] = weighted_result

        return weighted_prefs

    def _weighted_preference_calculation(
        self, category: str, values: List[Any], weights: List[float]
    ) -> Any:
        """Calculate weighted preference for a specific category."""
        if not values:
            return None

        # For numeric values (e.g., budget amounts)
        if all(isinstance(v, (int, float)) for v in values):
            weighted_sum = sum(v * w for v, w in zip(values, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight if total_weight > 0 else sum(values) / len(values)

        # For lists (e.g., activities)
        elif all(isinstance(v, list) for v in values):
            all_items = []
            for val_list, weight in zip(values, weights):
                # Add each item multiple times based on weight
                weight_factor = max(1, int(weight * 10))
                all_items.extend(val_list * weight_factor)

            # Return most popular items
            item_counts = Counter(all_items)
            return [item for item, count in item_counts.most_common(5)]

        # For categorical values (e.g., budget_level, travel_style)
        else:
            value_weights = {}
            for value, weight in zip(values, weights):
                value_str = str(value)
                value_weights[value_str] = value_weights.get(value_str, 0) + weight

            # Return most weighted value
            if value_weights:
                return max(value_weights, key=value_weights.get)
            return values[0]

    def _calculate_consensus_score(
        self, conflicts: List[PreferenceConflict], family_count: int
    ) -> float:
        """Calculate overall consensus score (0-1)."""
        if family_count <= 1:
            return 1.0

        # Start with perfect consensus
        score = 1.0

        # Reduce score based on conflicts
        for conflict in conflicts:
            severity_impact = {
                ConflictSeverity.LOW: 0.05,
                ConflictSeverity.MEDIUM: 0.15,
                ConflictSeverity.HIGH: 0.25,
                ConflictSeverity.CRITICAL: 0.4,
            }

            impact = severity_impact.get(conflict.severity, 0.1)
            families_involved = len(conflict.families_involved)

            # More families in conflict = bigger impact
            conflict_scale = families_involved / family_count
            score -= impact * conflict_scale

        return max(0.0, score)

    def _generate_voting_items(self, conflicts: List[PreferenceConflict]) -> List[Dict[str, Any]]:
        """Generate voting items for conflicts that need family input."""
        voting_items = []

        for i, conflict in enumerate(conflicts):
            # Only create votes for medium+ severity conflicts
            if conflict.severity in [
                ConflictSeverity.MEDIUM,
                ConflictSeverity.HIGH,
                ConflictSeverity.CRITICAL,
            ]:
                voting_item = VotingItem(
                    id=f"vote_{i}_{conflict.category}",
                    category=conflict.category,
                    question=f"How should we resolve the {conflict.category} preference conflict?",
                    options=(
                        conflict.conflicting_values + [conflict.suggested_compromise]
                        if conflict.suggested_compromise
                        else conflict.conflicting_values
                    ),
                    current_votes={},
                    threshold=(0.6 if conflict.severity != ConflictSeverity.CRITICAL else 0.8),
                )

                voting_items.append(asdict(voting_item))

        return voting_items

    def _generate_ai_compromises(
        self, conflicts: List[PreferenceConflict], weighted_prefs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered compromise suggestions."""
        compromises = {}

        for conflict in conflicts:
            category = conflict.category

            # AI-powered compromise logic based on category
            if category == "activities":
                compromises[category] = {
                    "type": "hybrid_approach",
                    "suggestion": "Split time between preferred activities - morning/afternoon rotation",
                    "implementation": "Day 1-2: Adventure activities, Day 3-4: Cultural activities, Day 5-6: Relaxation",
                    "confidence": 0.85,
                }

            elif category == "budget_level":
                compromises[category] = {
                    "type": "tiered_options",
                    "suggestion": "Provide multiple price tiers for each activity",
                    "implementation": "Basic, standard, and premium options for accommodations and dining",
                    "confidence": 0.9,
                }

            elif category == "travel_style":
                compromises[category] = {
                    "type": "flexible_scheduling",
                    "suggestion": "Mix of structured and free time",
                    "implementation": "Planned group activities 60%, free family time 40%",
                    "confidence": 0.8,
                }

            else:
                compromises[category] = {
                    "type": "majority_with_accommodation",
                    "suggestion": "Go with majority preference but accommodate minority needs",
                    "implementation": conflict.suggested_compromise,
                    "confidence": 0.7,
                }

        return compromises

    def _generate_next_steps(
        self,
        consensus_score: float,
        conflicts: List[PreferenceConflict],
        voting_items: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable next steps based on consensus analysis."""
        next_steps = []

        if consensus_score >= 0.8:
            next_steps.append("✅ Strong consensus achieved - proceed with itinerary generation")
            next_steps.append("📋 Share final preferences with all families for confirmation")

        elif consensus_score >= 0.6:
            next_steps.append("⚠️ Moderate consensus - address remaining conflicts")
            if voting_items:
                next_steps.append(f"🗳️ {len(voting_items)} items need family votes")
            next_steps.append("💬 Schedule family discussion to resolve differences")

        else:
            next_steps.append("❌ Low consensus - significant discussion needed")
            next_steps.append("📞 Schedule video call with all families")
            next_steps.append("🔄 Consider revising preferences after discussion")

        # Add specific actions for critical conflicts
        critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
        if critical_conflicts:
            next_steps.append("🚨 Critical conflicts must be resolved before proceeding")
            for conflict in critical_conflicts:
                next_steps.append(f"   - {conflict.category}: {conflict.suggested_compromise}")

        return next_steps

    def process_family_vote(
        self,
        voting_item_id: str,
        family_id: str,
        vote_choice: str,
        voting_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process a family's vote on a consensus item."""

        # Find the voting item
        voting_item = None
        for item in voting_items:
            if item["id"] == voting_item_id:
                voting_item = item
                break

        if not voting_item:
            raise ValueError(f"Voting item {voting_item_id} not found")

        # Record the vote
        voting_item["current_votes"][family_id] = vote_choice

        # Check if threshold is met
        total_families = len(voting_item["current_votes"])
        if total_families > 0:
            vote_counts = Counter(voting_item["current_votes"].values())
            winning_option = vote_counts.most_common(1)[0]

            if winning_option[1] / total_families >= voting_item["threshold"]:
                voting_item["status"] = VoteStatus.APPROVED.value
            elif len(voting_item["current_votes"]) >= voting_item.get("expected_families", 3):
                voting_item["status"] = VoteStatus.NEEDS_DISCUSSION.value

        return voting_item

    def get_consensus_dashboard_data(
        self, families_data: List[Dict[str, Any]], total_budget: float
    ) -> Dict[str, Any]:
        """Generate data for the consensus dashboard visualization."""

        consensus_result = self.generate_weighted_consensus(families_data, total_budget)
        family_weights = self.calculate_family_weights(families_data, total_budget)

        # Prepare dashboard data
        dashboard_data = {
            "consensus_score": consensus_result.consensus_score,
            "status": self._get_consensus_status(consensus_result.consensus_score),
            "family_weights": [asdict(fw) for fw in family_weights],
            "agreement_areas": self._identify_agreement_areas(families_data),
            "conflict_summary": {
                "total_conflicts": len(consensus_result.conflicts),
                "by_severity": {
                    severity.value: len(
                        [c for c in consensus_result.conflicts if c.severity == severity]
                    )
                    for severity in ConflictSeverity
                },
                "critical_items": [
                    c.category
                    for c in consensus_result.conflicts
                    if c.severity == ConflictSeverity.CRITICAL
                ],
            },
            "next_actions": consensus_result.next_steps,
            "voting_summary": {
                "pending_votes": len(
                    [
                        v
                        for v in consensus_result.voting_items
                        if v.get("status") == VoteStatus.PENDING.value
                    ]
                ),
                "items_needing_discussion": len(
                    [
                        v
                        for v in consensus_result.voting_items
                        if v.get("status") == VoteStatus.NEEDS_DISCUSSION.value
                    ]
                ),
            },
        }

        return dashboard_data

    def _get_consensus_status(self, score: float) -> str:
        """Get human-readable consensus status."""
        if score >= 0.8:
            return "Strong Consensus"
        elif score >= 0.6:
            return "Moderate Consensus"
        elif score >= 0.4:
            return "Weak Consensus"
        else:
            return "Significant Conflicts"

    def _identify_agreement_areas(self, families_data: List[Dict[str, Any]]) -> List[str]:
        """Identify areas where families already agree."""
        agreement_areas = []

        if len(families_data) <= 1:
            return ["All preferences (single family)"]

        # Check each preference category for agreement
        preference_categories = {}
        for family in families_data:
            prefs = family.get("preferences", {})
            for category, value in prefs.items():
                if category not in preference_categories:
                    preference_categories[category] = []
                preference_categories[category].append(str(value))

        for category, values in preference_categories.items():
            unique_values = set(values)
            if len(unique_values) == 1:  # All families agree
                agreement_areas.append(category)

        return agreement_areas


# Utility functions for integration with existing services


def analyze_trip_consensus(
    trip_id: str, families_data: List[Dict[str, Any]], total_budget: float
) -> Dict[str, Any]:
    """Main function to analyze consensus for a trip."""
    engine = FamilyConsensusEngine()

    try:
        # Generate consensus analysis
        consensus_result = engine.generate_weighted_consensus(families_data, total_budget)

        # Get dashboard data
        dashboard_data = engine.get_consensus_dashboard_data(families_data, total_budget)

        # Combine results
        analysis = {
            "trip_id": trip_id,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "consensus_result": asdict(consensus_result),
            "dashboard_data": dashboard_data,
            "recommendations": _generate_trip_recommendations(consensus_result),
        }

        logger.info(
            f"Consensus analysis completed for trip {trip_id}. Score: {consensus_result.consensus_score:.2f}"
        )

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing consensus for trip {trip_id}: {str(e)}")
        raise


def _generate_trip_recommendations(consensus_result: ConsensusResult) -> List[str]:
    """Generate specific recommendations for the trip organizer."""
    recommendations = []

    score = consensus_result.consensus_score
    conflicts = consensus_result.conflicts

    if score >= 0.8:
        recommendations.append("Proceed with AI itinerary generation using agreed preferences")
        recommendations.append("Send summary to families for final confirmation")

    elif score >= 0.6:
        recommendations.append("Resolve remaining conflicts before generating itinerary")
        recommendations.append("Consider compromise solutions for disputed preferences")

        high_priority_conflicts = [
            c for c in conflicts if c.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        ]
        if high_priority_conflicts:
            recommendations.append(
                f"Priority: Address {len(high_priority_conflicts)} high-impact conflicts"
            )

    else:
        recommendations.append("Schedule family meeting before proceeding")
        recommendations.append("Consider simplifying or reducing trip scope")
        recommendations.append("Focus on finding common ground in 2-3 key areas")

    return recommendations
