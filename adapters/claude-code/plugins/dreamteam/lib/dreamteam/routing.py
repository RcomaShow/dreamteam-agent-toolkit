"""Conservative whole-tree routing against a pinned Sonnet 5 baseline."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .config import RuntimeCapabilities, RuntimeConfig, Topology
from .pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost


class Criticality(str, Enum):
    M0 = "M0"
    L1 = "L1"
    L2 = "L2"
    C3 = "C3"


class TaskKind(str, Enum):
    DISCOVERY = "discovery"
    EDIT = "edit"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    SCAFFOLD = "scaffold"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    MIGRATION = "migration"

    @property
    def writes_code(self) -> bool:
        return self in {
            TaskKind.EDIT,
            TaskKind.IMPLEMENTATION,
            TaskKind.TEST,
            TaskKind.SCAFFOLD,
            TaskKind.DOCUMENTATION,
            TaskKind.MIGRATION,
        }


class Route(str, Enum):
    MAIN_DIRECT = "MAIN_DIRECT"
    HAIKU_DISCOVERY = "HAIKU_DISCOVERY"
    HAIKU_EXECUTE = "HAIKU_EXECUTE"
    SONNET_LEAD = "SONNET_LEAD"
    OPUS_DECISION = "OPUS_DECISION"


@dataclass(frozen=True)
class RouteRequest:
    criticality: Criticality
    task_kind: TaskKind
    direct_usage: TokenUsage
    worker_usage: TokenUsage = TokenUsage()
    lead_usage: TokenUsage = TokenUsage()
    verifier_usage: TokenUsage = TokenUsage()
    executive_usage: TokenUsage = TokenUsage()
    retry_probability: Decimal = Decimal("0")
    escalation_probability: Decimal = Decimal("0")
    main_context_is_hot: bool = False
    independent_verifier_available: bool = False
    closed_context: bool = False
    content_retention_confirmed: bool = False
    observed_main_reread_ratio: Decimal = Decimal("0")
    calibration_samples: int = 0

    def __post_init__(self) -> None:
        for name in ("retry_probability", "escalation_probability", "observed_main_reread_ratio"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be Decimal")
            if not Decimal("0") <= value <= Decimal("1"):
                raise ValueError(f"{name} must be between 0 and 1")
        if not isinstance(self.calibration_samples, int) or isinstance(self.calibration_samples, bool):
            raise TypeError("calibration_samples must be an integer")
        if self.calibration_samples < 0:
            raise ValueError("calibration_samples must be non-negative")


@dataclass(frozen=True)
class CostComponent:
    name: str
    model: str
    lane: ExecutionLane
    usage: TokenUsage
    usd: Decimal


@dataclass(frozen=True)
class RouteCostForecast:
    components: tuple[CostComponent, ...]
    base_usd: Decimal
    expected_retry_usd: Decimal
    expected_escalation_usd: Decimal
    total_usd: Decimal
    pricing_catalog_id: str


@dataclass(frozen=True)
class RouteDecision:
    selected_route: Route
    selected_route_usd: Decimal
    direct_baseline_usd: Decimal
    candidate_delegated_usd: Decimal | None
    savings_ratio: Decimal
    reason_codes: tuple[str, ...]
    direct_forecast: RouteCostForecast
    candidate_forecast: RouteCostForecast | None
    batch_eligible: bool = False

    @property
    def route(self) -> Route:
        """Compatibility alias for 0.3 callers."""
        return self.selected_route


def _component(name: str, model: str, usage: TokenUsage, lane: ExecutionLane, book: PriceBook) -> CostComponent:
    cost = estimate_cost(model, usage, price_book=book, lane=lane)
    return CostComponent(name, model, lane, usage, cost.total_usd)


def _forecast(
    components: list[CostComponent],
    *,
    retry_probability: Decimal,
    escalation_probability: Decimal,
    direct_fallback_usd: Decimal,
    pricing_catalog_id: str,
) -> RouteCostForecast:
    base = sum((item.usd for item in components), Decimal("0"))
    retry = base * retry_probability
    escalation = direct_fallback_usd * escalation_probability
    return RouteCostForecast(
        components=tuple(components),
        base_usd=base,
        expected_retry_usd=retry,
        expected_escalation_usd=escalation,
        total_usd=base + retry + escalation,
        pricing_catalog_id=pricing_catalog_id,
    )


def _direct_forecast(request: RouteRequest, book: PriceBook) -> RouteCostForecast:
    direct = _component("direct-sonnet", "claude-sonnet-5", request.direct_usage, ExecutionLane.INTERACTIVE, book)
    return _forecast(
        [direct],
        retry_probability=Decimal("0"),
        escalation_probability=Decimal("0"),
        direct_fallback_usd=Decimal("0"),
        pricing_catalog_id=book.catalog_id,
    )


def _batch_allowed(request: RouteRequest, config: RuntimeConfig, capabilities: RuntimeCapabilities) -> bool:
    return all(
        (
            request.closed_context,
            request.content_retention_confirmed,
            config.routing.allow_closed_context_batch,
            capabilities.batch_executor_available,
        )
    )


def _candidate_forecast(
    request: RouteRequest,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities,
    book: PriceBook,
    direct_usd: Decimal,
) -> tuple[RouteCostForecast, bool]:
    batch = _batch_allowed(request, config, capabilities)
    worker_lane = ExecutionLane.BATCH if batch else ExecutionLane.INTERACTIVE
    components: list[CostComponent] = []
    if request.worker_usage.total_tokens:
        components.append(_component("haiku-worker", "claude-haiku-4-5", request.worker_usage, worker_lane, book))
    if request.lead_usage.total_tokens:
        components.append(_component("sonnet-lead", "claude-sonnet-5", request.lead_usage, ExecutionLane.INTERACTIVE, book))
    if request.task_kind.writes_code and request.verifier_usage.total_tokens:
        components.append(_component("sonnet-independent-verifier", "claude-sonnet-5", request.verifier_usage, ExecutionLane.INTERACTIVE, book))
    if config.topology is Topology.FRONTIER:
        if request.executive_usage.total_tokens == 0:
            raise ValueError("Frontier routing requires explicit Opus executive usage")
        components.append(_component("opus-executive", "claude-opus-4-8", request.executive_usage, ExecutionLane.INTERACTIVE, book))
    return (
        _forecast(
            components,
            retry_probability=request.retry_probability,
            escalation_probability=request.escalation_probability,
            direct_fallback_usd=direct_usd,
            pricing_catalog_id=book.catalog_id,
        ),
        batch,
    )


def choose_route(
    request: RouteRequest,
    *,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities = RuntimeCapabilities(),
    enforce_calibration: bool = True,
) -> RouteDecision:
    book = PriceBook(config.pricing_as_of)
    direct = _direct_forecast(request, book)

    if request.criticality is Criticality.C3:
        if config.topology is Topology.LEAN:
            return RouteDecision(
                Route.MAIN_DIRECT,
                direct.total_usd,
                direct.total_usd,
                None,
                Decimal("0"),
                ("C3_EXECUTIVE_OWNERSHIP",),
                direct,
                None,
            )
        candidate, batch = _candidate_forecast(request, config, capabilities, book, direct.total_usd)
        savings = _savings(direct.total_usd, candidate.total_usd)
        return RouteDecision(
            Route.OPUS_DECISION,
            candidate.total_usd,
            direct.total_usd,
            candidate.total_usd,
            savings,
            ("C3_FRONTIER_EXECUTIVE", "QUALITY_ROUTE_NOT_SAVINGS_CLAIM"),
            direct,
            candidate,
            batch,
        )

    direct_reasons: list[str] = []
    if request.main_context_is_hot:
        direct_reasons.append("MAIN_CONTEXT_HOT")
    if request.direct_usage.total_tokens <= 1200:
        direct_reasons.append("SOURCE_VOLUME_SMALL")
    if request.escalation_probability > config.routing.max_escalation_probability:
        direct_reasons.append("ESCALATION_LIMIT_EXCEEDED")
    if request.observed_main_reread_ratio > config.routing.max_main_reread_ratio:
        direct_reasons.append("REREAD_LIMIT_EXCEEDED")
    if enforce_calibration and request.calibration_samples < config.routing.min_samples_for_enforcement:
        direct_reasons.append("INSUFFICIENT_CALIBRATION_SAMPLES")
    if request.task_kind.writes_code and config.verification.require_independent_writer_review and not request.independent_verifier_available:
        direct_reasons.append("INDEPENDENT_VERIFIER_REQUIRED")
    if direct_reasons:
        return RouteDecision(
            Route.MAIN_DIRECT,
            direct.total_usd,
            direct.total_usd,
            None,
            Decimal("0"),
            tuple(direct_reasons),
            direct,
            None,
        )

    try:
        candidate, batch = _candidate_forecast(request, config, capabilities, book, direct.total_usd)
    except ValueError as exc:
        return RouteDecision(
            Route.MAIN_DIRECT,
            direct.total_usd,
            direct.total_usd,
            None,
            Decimal("0"),
            ("FRONTIER_EXECUTIVE_USAGE_REQUIRED", str(exc)),
            direct,
            None,
        )

    savings = _savings(direct.total_usd, candidate.total_usd)
    if candidate.total_usd > config.budgets.max_run_usd:
        return RouteDecision(
            Route.MAIN_DIRECT,
            direct.total_usd,
            direct.total_usd,
            candidate.total_usd,
            savings,
            ("RUN_BUDGET_EXCEEDED",),
            direct,
            candidate,
            batch,
        )
    if savings < config.routing.minimum_savings_margin:
        return RouteDecision(
            Route.MAIN_DIRECT,
            direct.total_usd,
            direct.total_usd,
            candidate.total_usd,
            savings,
            ("SAVINGS_MARGIN_NOT_CLEARED",),
            direct,
            candidate,
            batch,
        )

    if request.task_kind.writes_code:
        selected = Route.SONNET_LEAD if request.criticality is Criticality.L2 else Route.HAIKU_EXECUTE
    else:
        selected = Route.HAIKU_DISCOVERY
    return RouteDecision(
        selected,
        candidate.total_usd,
        direct.total_usd,
        candidate.total_usd,
        savings,
        ("SAVINGS_MARGIN_CLEARED",),
        direct,
        candidate,
        batch,
    )


def _savings(direct: Decimal, candidate: Decimal) -> Decimal:
    if direct <= 0:
        return Decimal("0")
    return (direct - candidate) / direct
