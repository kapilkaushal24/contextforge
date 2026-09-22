"""ModelRouter (docs/architecture/ai-ml.md §5): decides whether the LLM strategy runs.

CHEAPEST SAFE TRANSFORMATION FIRST — the LLM is used only when every gate passes:
configured, enabled, privacy allows cloud, no detected sensitive content (unless the
policy explicitly allows it), mode/type allow it, and the estimated cost of the
compression call is below the estimated downstream savings (so the optimizer never
costs more than it saves). Reasons are stable codes, safe to log.
"""

from __future__ import annotations

from dataclasses import dataclass

from optimization_core.entities import OptimizationRequest
from optimization_core.enums import PrivacyPolicy, PromptType
from optimization_core.interfaces import IOptimizationStrategy, RoutingDecision


@dataclass(frozen=True, slots=True)
class RouterPolicy:
    llm_enabled: bool = False
    cost_optimization_enabled: bool = True
    # docs/security/privacy-security.md §1: detected PII/secrets block cloud LLM routing
    # by default, regardless of privacy_policy — an explicit opt-out for orgs that
    # accept that risk, not the default posture.
    block_pii_from_cloud: bool = True
    # USD per 1k tokens: the optimizer LLM's prices, and the downstream model's input price.
    optimizer_input_price_per_1k: float = 0.00015
    optimizer_output_price_per_1k: float = 0.0006
    downstream_input_price_per_1k: float = 0.003
    # Tokens of system-prompt overhead the compression call always pays for.
    prompt_overhead_tokens: int = 250
    # Planning assumptions used only for the cost gate.
    expected_reduction_ratio: float = 0.25
    expected_output_ratio: float = 0.75


class ModelRouter:
    def __init__(
        self, semantic_strategy: IOptimizationStrategy | None, policy: RouterPolicy | None = None
    ) -> None:
        self._semantic = semantic_strategy
        self._policy = policy or RouterPolicy()

    def route(
        self,
        request: OptimizationRequest,
        prompt_type: PromptType,
        current_tokens: int,
        *,
        contains_sensitive_content: bool = False,
    ) -> RoutingDecision:
        policy = self._policy
        if self._semantic is None:
            return RoutingDecision(None, "llm_not_configured")
        if not policy.llm_enabled:
            return RoutingDecision(None, "llm_disabled")
        if request.privacy_policy is PrivacyPolicy.LOCAL_ONLY:
            return RoutingDecision(None, "privacy_local_only")
        if contains_sensitive_content and policy.block_pii_from_cloud:
            return RoutingDecision(None, "sensitive_content_detected")
        if not self._semantic.applies_to(prompt_type, request.mode):
            return RoutingDecision(None, "mode_or_type_excludes_llm")
        if policy.cost_optimization_enabled and not self._is_worth_it(current_tokens):
            return RoutingDecision(None, "cost_exceeds_savings")
        return RoutingDecision(self._semantic, "llm_selected")

    def _is_worth_it(self, tokens: int) -> bool:
        p = self._policy
        estimated_cost = (tokens + p.prompt_overhead_tokens) / 1000 * p.optimizer_input_price_per_1k
        estimated_cost += tokens * p.expected_output_ratio / 1000 * p.optimizer_output_price_per_1k
        estimated_savings = tokens * p.expected_reduction_ratio / 1000 * p.downstream_input_price_per_1k
        return estimated_cost < estimated_savings
