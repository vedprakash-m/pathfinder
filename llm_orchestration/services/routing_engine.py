"""
Routing Strategy Engine - Intelligent model selection and routing
Handles context-aware routing, fallback tiers, and A/B testing
"""

from typing import Any, Dict, List, Optional, Tuple

import structlog
from core.llm_types import (
    LLMConfigurationError,
    LLMProvider,
    LLMRequest,
    ModelHealth,
    TaskType,
)
from services.config_manager import get_config_manager

logger = structlog.get_logger(__name__)


class RoutingContext:
    """Context information for routing decisions"""

    def __init__(
        self,
        request: LLMRequest,
        model_health: Dict[str, ModelHealth],
        budget_status: Dict[str, float],  # user_id -> remaining budget
        current_load: Dict[str, int],  # model_id -> current requests
        ab_test_assignment: Optional[str] = None,
    ):
        self.request = request
        self.model_health = model_health
        self.budget_status = budget_status
        self.current_load = current_load
        self.ab_test_assignment = ab_test_assignment


class RoutingRule:
    """Represents a routing rule with condition evaluation"""

    def __init__(self, condition: str, models: List[str]):
        self.condition = condition
        self.models = models

    def matches(self, context: RoutingContext) -> bool:
        """Check if this rule matches the current context"""
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            if self.condition == "default":
                return True

            # Parse conditions like "task_type == 'simple_qa'"
            if "task_type ==" in self.condition:
                expected_task = self.condition.split("'")[1]
                return context.request.task_type.value == expected_task

            if "priority ==" in self.condition:
                expected_priority = self.condition.split("'")[1]
                return context.request.priority.value == expected_priority

            # Add more condition types as needed
            return False

        except Exception as e:
            logger.error(
                "Error evaluating routing condition", condition=self.condition, error=str(e)
            )
            return False


class RoutingStrategyEngine:
    """
    Intelligent routing engine that selects optimal models based on:
    - Request context (task type, priority, user preferences)
    - Model health and availability
    - Budget constraints
    - Load balancing
    - A/B testing configuration
    """

    def __init__(self):
        self.config_manager = get_config_manager()
        self._model_definitions: Dict[str, Dict[str, Any]] = {}
        self._routing_strategies: Dict[str, List[RoutingRule]] = {}
        self._ab_test_config: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize routing engine with configuration"""
        await self._load_configuration()

    async def _load_configuration(self):
        """Load model definitions and routing strategies"""
        config = await self.config_manager.get_config()

        # Load model definitions
        model_defs = config.get("models", {}).get("definitions", [])
        for model_def in model_defs:
            self._model_definitions[model_def["id"]] = model_def

        # Load routing strategies
        strategies_config = (
            config.get("models", {}).get("routing_strategy", {}).get("strategies", {})
        )
        for strategy_name, strategy_config in strategies_config.items():
            rules = []
            for rule_config in strategy_config.get("rules", []):
                rule = RoutingRule(rule_config["condition"], rule_config["models"])
                rules.append(rule)
            self._routing_strategies[strategy_name] = rules

        # Load A/B test configuration
        ab_config = config.get("models", {}).get("routing_strategy", {}).get("ab_test", {})
        if ab_config.get("enabled", False):
            self._ab_test_config = ab_config

        logger.info(
            "Routing engine initialized",
            models_count=len(self._model_definitions),
            strategies_count=len(self._routing_strategies),
            ab_testing_enabled=bool(self._ab_test_config),
        )

    async def select_model(
        self,
        request: LLMRequest,
        model_health: Dict[str, ModelHealth],
        budget_status: Dict[str, float],
        current_load: Dict[str, int],
        tenant_id: Optional[str] = None,
    ) -> Tuple[str, LLMProvider]:
        """
        Select the optimal model for the given request

        Returns:
            Tuple[str, LLMProvider]: Selected model ID and provider
        """
        try:
            # Get tenant-specific configuration
            config = await self.config_manager.get_config(tenant_id)
            default_strategy = (
                config.get("models", {})
                .get("routing_strategy", {})
                .get("default_strategy", "cost_optimized")
            )

            # Check for A/B test assignment
            ab_assignment = self._get_ab_test_assignment(request.user_id)

            # Create routing context
            context = RoutingContext(
                request=request,
                model_health=model_health,
                budget_status=budget_status,
                current_load=current_load,
                ab_test_assignment=ab_assignment,
            )

            # Get candidate models based on strategy
            if ab_assignment:
                candidate_models = self._get_ab_test_models(ab_assignment)
                logger.debug(
                    "Using A/B test assignment", user_id=request.user_id, assignment=ab_assignment
                )
            else:
                candidate_models = await self._get_candidate_models(context, default_strategy)

            # Apply user preferences
            candidate_models = self._apply_user_preferences(candidate_models, request)

            # Filter by health and availability
            available_models = self._filter_available_models(candidate_models, model_health)

            if not available_models:
                raise LLMConfigurationError("No available models found for request")

            # Select best model based on multiple criteria
            selected_model = self._select_optimal_model(
                available_models, context, budget_status, current_load
            )

            model_def = self._model_definitions[selected_model]
            provider = LLMProvider(model_def["provider"])

            logger.info(
                "Model selected",
                model=selected_model,
                provider=provider.value,
                user_id=request.user_id,
                task_type=request.task_type.value,
                strategy=default_strategy,
            )

            return selected_model, provider

        except Exception as e:
            logger.error("Model selection failed", error=str(e), user_id=request.user_id)
            raise LLMConfigurationError(f"Failed to select model: {str(e)}")

    def _get_ab_test_assignment(self, user_id: str) -> Optional[str]:
        """Get A/B test assignment for user"""
        if not self._ab_test_config:
            return None

        # Simple hash-based assignment (use consistent hashing in production)
        user_hash = hash(user_id) % 100
        cumulative = 0

        for split in self._ab_test_config.get("traffic_split", []):
            cumulative += split["percentage"]
            if user_hash < cumulative:
                return split["model"]

        return None

    def _get_ab_test_models(self, assignment: str) -> List[str]:
        """Get models for A/B test assignment"""
        return [assignment]

    async def _get_candidate_models(self, context: RoutingContext, strategy_name: str) -> List[str]:
        """Get candidate models based on routing strategy"""
        if strategy_name not in self._routing_strategies:
            logger.warning("Unknown routing strategy, using default", strategy=strategy_name)
            strategy_name = "cost_optimized"

        rules = self._routing_strategies.get(strategy_name, [])

        # Find first matching rule
        for rule in rules:
            if rule.matches(context):
                logger.debug("Routing rule matched", condition=rule.condition, models=rule.models)
                return rule.models.copy()

        # Fallback to all available models
        logger.warning("No routing rules matched, using all models")
        return list(self._model_definitions.keys())

    def _apply_user_preferences(
        self, candidate_models: List[str], request: LLMRequest
    ) -> List[str]:
        """Apply user preferences to candidate models"""
        # Handle preferred model
        if request.preferred_model and request.preferred_model in self._model_definitions:
            if request.preferred_model in candidate_models:
                # Move preferred model to front
                candidate_models = [request.preferred_model] + [
                    m for m in candidate_models if m != request.preferred_model
                ]
            else:
                # Add preferred model if not in candidates
                candidate_models = [request.preferred_model] + candidate_models

        # Remove avoided models
        if request.avoid_models:
            candidate_models = [m for m in candidate_models if m not in request.avoid_models]

        # Filter by active models only
        active_models = [
            m for m in candidate_models if self._model_definitions.get(m, {}).get("active", False)
        ]

        return active_models

    def _filter_available_models(
        self, candidate_models: List[str], model_health: Dict[str, ModelHealth]
    ) -> List[str]:
        """Filter models by health and availability"""
        available = []

        for model_id in candidate_models:
            health = model_health.get(model_id)

            if health is None:
                # If no health data, assume healthy (for new models)
                available.append(model_id)
                continue

            if health.is_healthy:
                available.append(model_id)
            else:
                logger.debug("Filtering out unhealthy model", model=model_id)

        return available

    def _select_optimal_model(
        self,
        available_models: List[str],
        context: RoutingContext,
        budget_status: Dict[str, float],
        current_load: Dict[str, int],
    ) -> str:
        """Select the optimal model from available candidates"""
        if len(available_models) == 1:
            return available_models[0]

        # Score each model based on multiple criteria
        model_scores = []

        for model_id in available_models:
            score = self._calculate_model_score(model_id, context, budget_status, current_load)
            model_scores.append((model_id, score))

        # Sort by score (higher is better)
        model_scores.sort(key=lambda x: x[1], reverse=True)

        selected_model = model_scores[0][0]

        logger.debug(
            "Model scoring completed",
            scores=[(model, round(score, 3)) for model, score in model_scores[:3]],
            selected=selected_model,
        )

        return selected_model

    def _calculate_model_score(
        self,
        model_id: str,
        context: RoutingContext,
        budget_status: Dict[str, float],
        current_load: Dict[str, int],
    ) -> float:
        """Calculate composite score for model selection"""
        model_def = self._model_definitions[model_id]
        score = 0.0

        # Cost efficiency (higher score for lower cost)
        avg_cost = (
            model_def["cost_per_1k_tokens"]["input"] + model_def["cost_per_1k_tokens"]["output"]
        ) / 2
        cost_score = 1.0 / (avg_cost * 1000 + 1)  # Normalize
        score += cost_score * 0.3

        # Load balancing (higher score for lower load)
        current_requests = current_load.get(model_id, 0)
        max_requests = 100  # Configuration-based
        load_score = max(0, (max_requests - current_requests) / max_requests)
        score += load_score * 0.2

        # Health score
        health = context.model_health.get(model_id)
        if health:
            health_score = health.success_rate
            response_time_score = max(
                0, 1.0 - (health.avg_response_time_ms / 10000)
            )  # Penalty for slow responses
            score += health_score * 0.3
            score += response_time_score * 0.1
        else:
            score += 0.4  # Default score for unknown health

        # Capability matching (bonus for models with required capabilities)
        task_capability_map = {
            TaskType.CODE_GENERATION: "code",
            TaskType.CREATIVE_WRITING: "text",
            TaskType.COMPLEX_REASONING: "reasoning",
        }

        required_capability = task_capability_map.get(context.request.task_type)
        if required_capability and required_capability in model_def.get("capabilities", []):
            score += 0.1

        return score

    async def get_fallback_models(
        self, original_model: str, context: RoutingContext, exclude_models: List[str]
    ) -> List[str]:
        """Get fallback models when primary model fails"""
        try:
            # Get the original strategy
            config = await self.config_manager.get_config()
            default_strategy = (
                config.get("models", {})
                .get("routing_strategy", {})
                .get("default_strategy", "cost_optimized")
            )

            # Get candidate models
            candidate_models = await self._get_candidate_models(context, default_strategy)

            # Remove the failed model and excluded models
            fallback_models = [
                m for m in candidate_models if m != original_model and m not in exclude_models
            ]

            # Filter by availability
            fallback_models = self._filter_available_models(fallback_models, context.model_health)

            logger.info(
                "Fallback models identified",
                original_model=original_model,
                fallback_count=len(fallback_models),
                fallbacks=fallback_models[:3],  # Log first 3
            )

            return fallback_models

        except Exception as e:
            logger.error(
                "Failed to get fallback models", original_model=original_model, error=str(e)
            )
            return []
