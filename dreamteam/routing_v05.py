"""DreamTeam 0.5 measurement-first routing overlay.

0.4 remains the compatibility router. The 0.5 overlay fixes the missing Lean
executive-overhead accounting discovered during review, emits separate cost,
total-token, and main-token forecasts, and can optionally enforce token gates.
The token gates default to shadow mode until paired benchmarks calibrate them.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any

from .config import RuntimeCapabilities, RuntimeConfig, Topology
from .measurement import EfficiencyMetrics
from .pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost, resolve_model
from .routing import (
    CostComponent,
    Route,
    RouteCostForecast,
    RouteDecision,
    RouteRequest,
    choose_route as choose_route_v04,
)


@dataclass(frozen=True)
class V05RoutingPolicy:
    """Token gates are measurable in 0.5 but shadow-only unless explicitly enabled."""

    minimum_total_token_savings: Decimal = Decimal("0.05")
    minimum_main_token_savings: Decimal = Decimal("0.15")
    enforce_token_gates: bool = False
    require_lean_executive_usage: bool = True

    def __post_init__(self) -> None:
        for name in ("minimum_total_token_savings", "minimum_main_token_savings"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be Decimal")
            if not value.is_finite() or not Decimal("0") <= value <= Decimal("1"):
                raise ValueError(f"{name} must be finite and between 0 and 1")
        for name in ("enforce_token_gates", "require_lean_executive_usage"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")


@dataclass(frozen=True)
class V05RouteDecision:
    decision: RouteDecision
    efficiency: EfficiencyMetrics | None
    lean_executive_overhead_usd: Decimal
    cost_gate_pass: bool
    token_gate_pass: bool
    token_gates_enforced: bool
    empirical_claim_allowed: bool = False

    @property
    def selected_route(self) -> Route:
        return self.decision.selected_route

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return self.decision.reason_codes

    def to_mapping(self) -> dict[str, Any]:
        policy = self.decision.execution_policy
        payload: dict[str, Any] = {
            "router_version": "0.5",
            "selected_route": self.decision.selected_route.value,
            "selected_route_usd": str(self.decision.selected_route_usd),
            "direct_baseline_usd": str(self.decision.direct_baseline_usd),
            "candidate_delegated_usd": (
                None
                if self.decision.candidate_delegated_usd is None
                else str(self.decision.candidate_delegated_usd)
            ),
            "cost_savings_ratio": str(self.decision.savings_ratio),
            "reason_codes": list(self.decision.reason_codes),
            "blocked": self.decision.blocked,
            "batch_eligible": self.decision.batch_eligible,
            "selected_agent_role": self.decision.selected_agent_role,
            "support_agent_role": self.decision.support_agent_role,
            "execution_chain": list(self.decision.execution_chain),
            "lean_executive_overhead_usd": str(self.lean_executive_overhead_usd),
            "cost_gate_pass": self.cost_gate_pass,
            "token_gate_pass": self.token_gate_pass,
            "token_gates_enforced": self.token_gates_enforced,
            "empirical_claim_allowed": self.empirical_claim_allowed,
        }
        if policy is not None:
            payload["execution_policy"] = {
                "profile": policy.profile.value,
                "max_active_workers": policy.max_active_workers,
                "max_retries": policy.max_retries,
                "max_worker_turns": policy.max_worker_turns,
                "allow_parallel_independent": policy.allow_parallel_independent,
            }
        if self.efficiency is not None:
            payload["token_forecast"] = {
                "direct_total_tokens": str(self.efficiency.direct_total_tokens),
                "candidate_total_tokens": str(self.efficiency.candidate_total_tokens),
                "total_token_savings_ratio": str(
                    self.efficiency.total_token_savings_ratio
                ),
                "direct_main_tokens": str(self.efficiency.direct_main_tokens),
                "candidate_main_tokens": str(self.efficiency.candidate_main_tokens),
                "main_token_savings_ratio": str(self.efficiency.main_token_savings_ratio),
            }
        return payload


def _component_tokens(component: CostComponent) -> Decimal:
    return Decimal(component.usage.total_tokens)


def _is_worker_component(component: CostComponent) -> bool:
    return component.name in {"haiku-worker", "frontier-haiku-worker"}


def _is_retryable_component(component: CostComponent) -> bool:
    # A bounded worker/lead/reviewer retry does not replay the root Lean executive session.
    return component.name != "sonnet-executive-overhead"


def _candidate_token_forecast(
    request: RouteRequest,
    candidate: RouteCostForecast,
) -> tuple[Decimal, Decimal]:
    base_total = sum((_component_tokens(item) for item in candidate.components), Decimal("0"))
    base_main = sum(
        (_component_tokens(item) for item in candidate.components if not _is_worker_component(item)),
        Decimal("0"),
    )
    retry_total = sum(
        (_component_tokens(item) for item in candidate.components if _is_retryable_component(item)),
        Decimal("0"),
    ) * request.retry_probability
    retry_main = sum(
        (
            _component_tokens(item)
            for item in candidate.components
            if _is_retryable_component(item) and not _is_worker_component(item)
        ),
        Decimal("0"),
    ) * request.retry_probability
    fallback = Decimal(request.direct_usage.total_tokens) * request.escalation_probability
    return base_total + retry_total + fallback, base_main + retry_main + fallback


def _with_lean_executive(
    candidate: RouteCostForecast,
    request: RouteRequest,
    config: RuntimeConfig,
) -> tuple[RouteCostForecast, Decimal]:
    book = PriceBook(config.pricing_as_of)
    model = resolve_model(config.models.executive, inherited="sonnet")
    cost = estimate_cost(
        model,
        request.executive_usage,
        price_book=book,
        lane=ExecutionLane.INTERACTIVE,
    )
    component = CostComponent(
        "sonnet-executive-overhead",
        cost.model,
        ExecutionLane.INTERACTIVE,
        request.executive_usage,
        cost.total_usd,
    )
    adjusted = RouteCostForecast(
        components=(component, *candidate.components),
        base_usd=candidate.base_usd + cost.total_usd,
        expected_retry_usd=candidate.expected_retry_usd,
        expected_escalation_usd=candidate.expected_escalation_usd,
        total_usd=candidate.total_usd + cost.total_usd,
        pricing_catalog_id=candidate.pricing_catalog_id,
    )
    return adjusted, cost.total_usd


def _savings(direct: Decimal, candidate: Decimal) -> Decimal:
    if direct <= 0:
        return Decimal("0")
    return (direct - candidate) / direct


def _fallback_to_direct(
    decision: RouteDecision,
    config: RuntimeConfig,
    *,
    candidate: RouteCostForecast | None,
    savings: Decimal,
    reasons: tuple[str, ...],
) -> RouteDecision:
    blocked = decision.direct_baseline_usd > config.budgets.max_run_usd
    route = Route.BLOCKED if blocked else Route.MAIN_DIRECT
    suffix = ("DIRECT_BUDGET_EXCEEDED_AFTER_V05_GATE",) if blocked else ()
    return replace(
        decision,
        selected_route=route,
        selected_route_usd=decision.direct_baseline_usd,
        candidate_delegated_usd=None if candidate is None else candidate.total_usd,
        savings_ratio=savings,
        reason_codes=(*reasons, *suffix),
        candidate_forecast=candidate,
        batch_eligible=False,
        selected_agent_role=None,
        support_agent_role=None,
        execution_chain=() if blocked else ("direct-sonnet",),
        blocked=blocked,
    )


def choose_route_v05(
    request: RouteRequest,
    *,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities = RuntimeCapabilities(),
    enforce_calibration: bool = True,
    policy: V05RoutingPolicy = V05RoutingPolicy(),
) -> V05RouteDecision:
    """Run 0.4 compatibility routing, then apply 0.5 accounting and token telemetry."""
    if not isinstance(request, RouteRequest):
        raise TypeError("request must be RouteRequest")
    if not isinstance(config, RuntimeConfig):
        raise TypeError("config must be RuntimeConfig")
    if not isinstance(policy, V05RoutingPolicy):
        raise TypeError("policy must be V05RoutingPolicy")

    is_lean = config.topology is Topology.LEAN
    legacy_request = request
    if is_lean and request.executive_usage.total_tokens:
        # 0.4 rejects Lean executive_usage because it did not account root overhead.
        legacy_request = replace(request, executive_usage=TokenUsage())

    legacy = choose_route_v04(
        legacy_request,
        config=config,
        capabilities=capabilities,
        enforce_calibration=enforce_calibration,
    )
    candidate = legacy.candidate_forecast
    overhead_usd = Decimal("0")
    lean_usage_present = False

    if is_lean and candidate is not None and request.executive_usage.total_tokens:
        candidate, overhead_usd = _with_lean_executive(candidate, request, config)
        lean_usage_present = True

    savings = (
        legacy.savings_ratio
        if candidate is None
        else _savings(legacy.direct_baseline_usd, candidate.total_usd)
    )
    decision = replace(
        legacy,
        candidate_delegated_usd=None if candidate is None else candidate.total_usd,
        savings_ratio=savings,
        candidate_forecast=candidate,
    )

    delegated = legacy.selected_route not in {Route.MAIN_DIRECT, Route.BLOCKED}
    reasons = tuple(legacy.reason_codes)
    if delegated and is_lean and policy.require_lean_executive_usage and not lean_usage_present:
        decision = _fallback_to_direct(
            decision,
            config,
            candidate=candidate,
            savings=savings,
            reasons=(*reasons, "LEAN_EXECUTIVE_USAGE_REQUIRED"),
        )
        delegated = False
    elif delegated and candidate is not None:
        if candidate.total_usd > config.budgets.max_run_usd:
            decision = _fallback_to_direct(
                decision,
                config,
                candidate=candidate,
                savings=savings,
                reasons=(*reasons, "V05_CANDIDATE_BUDGET_EXCEEDED"),
            )
            delegated = False
        elif savings < config.routing.minimum_savings_margin:
            decision = _fallback_to_direct(
                decision,
                config,
                candidate=candidate,
                savings=savings,
                reasons=(*reasons, "LEAN_EXECUTIVE_OVERHEAD_MARGIN_NOT_CLEARED"),
            )
            delegated = False
        elif is_lean and overhead_usd:
            decision = replace(
                decision,
                selected_route_usd=candidate.total_usd,
                reason_codes=(*reasons, "LEAN_EXECUTIVE_OVERHEAD_ACCOUNTED"),
            )

    efficiency: EfficiencyMetrics | None = None
    token_gate_pass = False
    if candidate is not None:
        candidate_total, candidate_main = _candidate_token_forecast(request, candidate)
        direct_tokens = Decimal(request.direct_usage.total_tokens)
        efficiency = EfficiencyMetrics(
            direct_cost_usd=legacy.direct_baseline_usd,
            candidate_cost_usd=candidate.total_usd,
            direct_total_tokens=direct_tokens,
            candidate_total_tokens=candidate_total,
            direct_main_tokens=direct_tokens,
            candidate_main_tokens=candidate_main,
        )
        token_gate_pass = (
            efficiency.total_token_savings_ratio >= policy.minimum_total_token_savings
            and efficiency.main_token_savings_ratio >= policy.minimum_main_token_savings
        )

    if delegated and policy.enforce_token_gates and not token_gate_pass:
        assert candidate is not None
        decision = _fallback_to_direct(
            decision,
            config,
            candidate=candidate,
            savings=savings,
            reasons=(*decision.reason_codes, "V05_TOKEN_SAVINGS_GATE_NOT_CLEARED"),
        )

    cost_gate_pass = (
        candidate is not None
        and savings >= config.routing.minimum_savings_margin
        and candidate.total_usd <= config.budgets.max_run_usd
    )
    return V05RouteDecision(
        decision=decision,
        efficiency=efficiency,
        lean_executive_overhead_usd=overhead_usd,
        cost_gate_pass=cost_gate_pass,
        token_gate_pass=token_gate_pass,
        token_gates_enforced=policy.enforce_token_gates,
        empirical_claim_allowed=False,
    )
