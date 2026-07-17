"""Conservative whole-tree routing with executable role and policy selection."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .config import Profile, RuntimeCapabilities, RuntimeConfig, Topology
from .pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost, resolve_model


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
    BLOCKED = "BLOCKED"
    MAIN_DIRECT = "MAIN_DIRECT"
    HAIKU_DISCOVERY = "HAIKU_DISCOVERY"
    HAIKU_EXECUTE = "HAIKU_EXECUTE"
    SONNET_LEAD = "SONNET_LEAD"
    OPUS_DECISION = "OPUS_DECISION"


ROLE_SYMBOL = "discovery-symbol-locator"
ROLE_FLOW = "discovery-flow-tracer"
ROLE_PATTERN = "discovery-pattern-miner"
ROLE_IMPACT = "discovery-impact-mapper"
ROLE_CONTEXT = "discovery-context-synthesizer"
ROLE_SCAFFOLD = "execution-scaffold-builder"
ROLE_MECHANICAL = "execution-mechanical-editor"
ROLE_BOUNDED_LOGIC = "execution-bounded-logic"
ROLE_TEST = "execution-test-writer"
ROLE_DOCUMENTATION = "execution-documentation-updater"
ROLE_SONNET_LEAD = "execution-sonnet-lead"
ROLE_FAILURE = "verification-failure-triage"
ROLE_DIFF = "verification-diff-auditor"
ROLE_TEST_GAPS = "verification-test-gap-finder"
ROLE_DECISION = "coordination-decision-analyst"
ROLE_REVIEWER = "verification-independent-reviewer"

_DISCOVERY_ROLES = {ROLE_SYMBOL, ROLE_FLOW, ROLE_PATTERN, ROLE_IMPACT, ROLE_CONTEXT}
_HAIKU_EXECUTION_ROLES = {
    ROLE_SCAFFOLD,
    ROLE_MECHANICAL,
    ROLE_BOUNDED_LOGIC,
    ROLE_TEST,
    ROLE_DOCUMENTATION,
}
_HAIKU_VERIFICATION_ROLES = {ROLE_FAILURE, ROLE_DIFF, ROLE_TEST_GAPS}
_HAIKU_ROLES = _DISCOVERY_ROLES | _HAIKU_EXECUTION_ROLES | _HAIKU_VERIFICATION_ROLES
_SONNET_ROLES = {ROLE_DECISION, ROLE_REVIEWER, ROLE_SONNET_LEAD}

_DEFAULT_ROLE_BY_KIND: dict[TaskKind, str] = {
    TaskKind.DISCOVERY: ROLE_CONTEXT,
    TaskKind.EDIT: ROLE_MECHANICAL,
    TaskKind.IMPLEMENTATION: ROLE_BOUNDED_LOGIC,
    TaskKind.TEST: ROLE_TEST,
    TaskKind.SCAFFOLD: ROLE_SCAFFOLD,
    TaskKind.DOCUMENTATION: ROLE_DOCUMENTATION,
    TaskKind.REVIEW: ROLE_REVIEWER,
    TaskKind.MIGRATION: ROLE_SONNET_LEAD,
}


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
    requested_role: str | None = None
    requested_worker_role: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.criticality, Criticality):
            raise TypeError("criticality must be Criticality")
        if not isinstance(self.task_kind, TaskKind):
            raise TypeError("task_kind must be TaskKind")
        for name in (
            "direct_usage",
            "worker_usage",
            "lead_usage",
            "verifier_usage",
            "executive_usage",
        ):
            if not isinstance(getattr(self, name), TokenUsage):
                raise TypeError(f"{name} must be TokenUsage")
        for name in (
            "retry_probability",
            "escalation_probability",
            "observed_main_reread_ratio",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be Decimal")
            if not value.is_finite() or not Decimal("0") <= value <= Decimal("1"):
                raise ValueError(f"{name} must be finite and between 0 and 1")
        if type(self.calibration_samples) is not int:
            raise TypeError("calibration_samples must be an integer")
        if self.calibration_samples < 0:
            raise ValueError("calibration_samples must be non-negative")
        for name in (
            "main_context_is_hot",
            "independent_verifier_available",
            "closed_context",
            "content_retention_confirmed",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")
        for name in ("requested_role", "requested_worker_role"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value):
                raise TypeError(f"{name} must be a non-empty string")


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
class ExecutionPolicy:
    profile: Profile
    max_active_workers: int
    max_retries: int
    max_worker_turns: int
    allow_parallel_independent: bool


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
    selected_agent_role: str | None = None
    support_agent_role: str | None = None
    execution_chain: tuple[str, ...] = ()
    execution_policy: ExecutionPolicy | None = None
    blocked: bool = False

    @property
    def route(self) -> Route:
        """Compatibility alias for 0.3 callers."""
        return self.selected_route


@dataclass(frozen=True)
class _Models:
    baseline: str
    executive: str
    lead: str
    worker: str


def _models(config: RuntimeConfig) -> _Models:
    inherited_executive = "sonnet" if config.topology is Topology.LEAN else "opus"
    return _Models(
        baseline=resolve_model("sonnet"),
        executive=resolve_model(config.models.executive, inherited=inherited_executive),
        lead=resolve_model(config.models.lead),
        worker=resolve_model(config.models.workers),
    )


def _policy(config: RuntimeConfig) -> ExecutionPolicy:
    return ExecutionPolicy(
        profile=config.profile,
        max_active_workers=config.budgets.max_active_workers,
        max_retries=config.budgets.max_retries,
        max_worker_turns=config.budgets.max_worker_turns,
        allow_parallel_independent=config.routing.allow_parallel_independent,
    )


def _component(
    name: str,
    model: str,
    usage: TokenUsage,
    lane: ExecutionLane,
    book: PriceBook,
) -> CostComponent:
    cost = estimate_cost(model, usage, price_book=book, lane=lane)
    return CostComponent(name, cost.model, lane, usage, cost.total_usd)


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


def _direct_forecast(
    request: RouteRequest,
    book: PriceBook,
    models: _Models,
) -> RouteCostForecast:
    direct = _component(
        "direct-sonnet",
        models.baseline,
        request.direct_usage,
        ExecutionLane.INTERACTIVE,
        book,
    )
    return _forecast(
        [direct],
        retry_probability=Decimal("0"),
        escalation_probability=Decimal("0"),
        direct_fallback_usd=Decimal("0"),
        pricing_catalog_id=book.catalog_id,
    )


def _batch_allowed(
    request: RouteRequest,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities,
) -> bool:
    return all(
        (
            request.closed_context,
            request.content_retention_confirmed,
            config.routing.allow_closed_context_batch,
            capabilities.batch_executor_available,
        )
    )


def _proposed_route(request: RouteRequest, topology: Topology) -> Route:
    if request.criticality is Criticality.C3:
        return Route.MAIN_DIRECT if topology is Topology.LEAN else Route.OPUS_DECISION
    if topology is Topology.OPUS_SONNET:
        return Route.SONNET_LEAD
    if request.task_kind.writes_code:
        return Route.SONNET_LEAD if request.criticality is Criticality.L2 else Route.HAIKU_EXECUTE
    if request.criticality is Criticality.L2 or request.task_kind is TaskKind.REVIEW:
        return Route.SONNET_LEAD
    return Route.HAIKU_DISCOVERY


def _primary_role(request: RouteRequest, route: Route) -> str:
    if route is Route.OPUS_DECISION:
        allowed = {ROLE_DECISION, ROLE_REVIEWER}
        default = ROLE_DECISION
    elif route is Route.SONNET_LEAD:
        if request.task_kind is TaskKind.REVIEW:
            allowed = {ROLE_REVIEWER}
            default = ROLE_REVIEWER
        elif request.task_kind.writes_code:
            allowed = {ROLE_SONNET_LEAD}
            default = ROLE_SONNET_LEAD
        else:
            allowed = _SONNET_ROLES
            default = ROLE_DECISION
    elif route is Route.HAIKU_DISCOVERY:
        allowed = _DISCOVERY_ROLES | _HAIKU_VERIFICATION_ROLES
        default = _DEFAULT_ROLE_BY_KIND[request.task_kind]
    elif route is Route.HAIKU_EXECUTE:
        allowed = _HAIKU_EXECUTION_ROLES
        default = _DEFAULT_ROLE_BY_KIND[request.task_kind]
    else:
        raise ValueError("route has no delegated agent role")
    role = request.requested_role or default
    if role not in allowed:
        raise ValueError(f"role {role!r} is not allowed for {route.value}")
    return role


def _support_role(request: RouteRequest, topology: Topology) -> str | None:
    if topology is not Topology.FRONTIER:
        if request.requested_worker_role is not None:
            raise ValueError("requested_worker_role is only valid for Frontier")
        return None
    role = request.requested_worker_role or ROLE_CONTEXT
    if role not in _HAIKU_ROLES:
        raise ValueError(f"Frontier support role {role!r} must be a Haiku role")
    return role


def _validate_usage_shape(
    request: RouteRequest,
    topology: Topology,
    route: Route,
) -> None:
    worker = request.worker_usage.total_tokens > 0
    lead = request.lead_usage.total_tokens > 0
    executive = request.executive_usage.total_tokens > 0
    verifier = request.verifier_usage.total_tokens > 0

    if topology is Topology.LEAN:
        if executive:
            raise ValueError("Lean does not include an Opus executive component")
        if route in {Route.HAIKU_DISCOVERY, Route.HAIKU_EXECUTE}:
            if not worker or lead:
                raise ValueError("Lean Haiku routes require worker usage and forbid hidden lead usage")
        elif route is Route.SONNET_LEAD:
            if not lead or worker:
                raise ValueError("Lean Sonnet routes require lead usage and forbid hidden worker usage")
        else:
            raise ValueError("Lean has no delegated candidate for this route")
    elif topology is Topology.OPUS_SONNET:
        if not executive or not lead:
            raise ValueError("Opus-Sonnet requires explicit Opus executive and Sonnet lead usage")
        if worker:
            raise ValueError("Opus-Sonnet does not include Haiku worker usage")
    else:
        if not executive or not lead or not worker:
            raise ValueError("Frontier requires explicit Opus, Sonnet, and Haiku usage")

    delegated_write = route in {Route.HAIKU_EXECUTE, Route.SONNET_LEAD} and request.task_kind.writes_code
    c3_review = route is Route.OPUS_DECISION and request.task_kind.writes_code
    if delegated_write or c3_review:
        if not request.independent_verifier_available or not verifier:
            raise ValueError("writing routes require a distinct non-zero-cost verifier")
    elif verifier:
        raise ValueError("verifier usage is not part of this non-writing route")


def _candidate_forecast(
    request: RouteRequest,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities,
    book: PriceBook,
    models: _Models,
    direct_usd: Decimal,
    route: Route,
) -> tuple[RouteCostForecast, bool]:
    _validate_usage_shape(request, config.topology, route)
    batch = _batch_allowed(request, config, capabilities)
    worker_lane = ExecutionLane.BATCH if batch else ExecutionLane.INTERACTIVE
    components: list[CostComponent] = []

    if config.topology in {Topology.OPUS_SONNET, Topology.FRONTIER}:
        components.append(
            _component(
                "opus-executive",
                models.executive,
                request.executive_usage,
                ExecutionLane.INTERACTIVE,
                book,
            )
        )
    if route is Route.SONNET_LEAD or config.topology in {Topology.OPUS_SONNET, Topology.FRONTIER}:
        components.append(
            _component(
                "sonnet-lead",
                models.lead,
                request.lead_usage,
                ExecutionLane.INTERACTIVE,
                book,
            )
        )
    if route in {Route.HAIKU_DISCOVERY, Route.HAIKU_EXECUTE} or config.topology is Topology.FRONTIER:
        components.append(
            _component(
                "haiku-worker",
                models.worker,
                request.worker_usage,
                worker_lane,
                book,
            )
        )
    if request.verifier_usage.total_tokens:
        components.append(
            _component(
                "sonnet-independent-verifier",
                models.lead,
                request.verifier_usage,
                ExecutionLane.INTERACTIVE,
                book,
            )
        )

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


def _execution_chain(
    topology: Topology,
    route: Route,
    primary_role: str,
    support_role: str | None,
    *,
    writes_code: bool,
) -> tuple[str, ...]:
    if topology is Topology.LEAN:
        chain = ["sonnet-executive", primary_role]
    elif topology is Topology.OPUS_SONNET:
        chain = ["opus-executive", primary_role]
    elif route in {Route.HAIKU_DISCOVERY, Route.HAIKU_EXECUTE}:
        chain = ["opus-executive", ROLE_SONNET_LEAD, primary_role]
    else:
        chain = ["opus-executive", primary_role]
        if support_role:
            chain.append(support_role)
    if writes_code and primary_role != ROLE_REVIEWER:
        chain.append(ROLE_REVIEWER)
    return tuple(dict.fromkeys(chain))


def _decision(
    *,
    config: RuntimeConfig,
    route: Route,
    selected_usd: Decimal,
    direct: RouteCostForecast,
    candidate: RouteCostForecast | None,
    savings: Decimal,
    reasons: tuple[str, ...],
    batch: bool = False,
    role: str | None = None,
    support_role: str | None = None,
    chain: tuple[str, ...] = (),
) -> RouteDecision:
    return RouteDecision(
        selected_route=route,
        selected_route_usd=selected_usd,
        direct_baseline_usd=direct.total_usd,
        candidate_delegated_usd=None if candidate is None else candidate.total_usd,
        savings_ratio=savings,
        reason_codes=reasons,
        direct_forecast=direct,
        candidate_forecast=candidate,
        batch_eligible=batch,
        selected_agent_role=role,
        support_agent_role=support_role,
        execution_chain=chain,
        execution_policy=_policy(config),
        blocked=route is Route.BLOCKED,
    )


def _direct_or_blocked(
    direct: RouteCostForecast,
    config: RuntimeConfig,
    reasons: tuple[str, ...],
    *,
    candidate: RouteCostForecast | None = None,
    savings: Decimal = Decimal("0"),
    batch: bool = False,
) -> RouteDecision:
    if direct.total_usd > config.budgets.max_run_usd:
        return _decision(
            config=config,
            route=Route.BLOCKED,
            selected_usd=direct.total_usd,
            direct=direct,
            candidate=candidate,
            savings=savings,
            reasons=(*reasons, "DIRECT_BUDGET_EXCEEDED"),
            batch=batch,
        )
    return _decision(
        config=config,
        route=Route.MAIN_DIRECT,
        selected_usd=direct.total_usd,
        direct=direct,
        candidate=candidate,
        savings=savings,
        reasons=reasons,
        batch=batch,
        chain=("direct-sonnet",),
    )


def choose_route(
    request: RouteRequest,
    *,
    config: RuntimeConfig,
    capabilities: RuntimeCapabilities = RuntimeCapabilities(),
    enforce_calibration: bool = True,
) -> RouteDecision:
    book = PriceBook(config.pricing_as_of)
    try:
        models = _models(config)
        # Resolve all configured models before making any decision.
        for model in (models.baseline, models.executive, models.lead, models.worker):
            book.get(model)
    except (KeyError, TypeError, ValueError) as exc:
        fallback_models = _Models(
            baseline=resolve_model("sonnet"),
            executive=resolve_model("sonnet"),
            lead=resolve_model("sonnet"),
            worker=resolve_model("haiku"),
        )
        direct = _direct_forecast(request, book, fallback_models)
        return _decision(
            config=config,
            route=Route.BLOCKED,
            selected_usd=direct.total_usd,
            direct=direct,
            candidate=None,
            savings=Decimal("0"),
            reasons=("MODEL_CONFIGURATION_INVALID", str(exc)),
        )

    direct = _direct_forecast(request, book, models)
    if config.telemetry.enforcement == "strict" and not capabilities.hooks_available:
        return _decision(
            config=config,
            route=Route.BLOCKED,
            selected_usd=direct.total_usd,
            direct=direct,
            candidate=None,
            savings=Decimal("0"),
            reasons=("STRICT_HOOKS_REQUIRED",),
        )

    route = _proposed_route(request, config.topology)
    if route is Route.MAIN_DIRECT:
        if request.worker_usage.total_tokens or request.lead_usage.total_tokens or request.executive_usage.total_tokens:
            return _direct_or_blocked(
                direct,
                config,
                ("C3_EXECUTIVE_OWNERSHIP", "UNUSED_DELEGATION_FORECAST_IGNORED"),
            )
        return _direct_or_blocked(direct, config, ("C3_EXECUTIVE_OWNERSHIP",))

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
    writing_route = request.task_kind.writes_code and route in {
        Route.HAIKU_EXECUTE, Route.SONNET_LEAD, Route.OPUS_DECISION
    }
    if writing_route and (
        not request.independent_verifier_available
        or request.verifier_usage.total_tokens == 0
    ):
        if request.criticality is Criticality.C3:
            return _decision(
                config=config,
                route=Route.BLOCKED,
                selected_usd=direct.total_usd,
                direct=direct,
                candidate=None,
                savings=Decimal("0"),
                reasons=("INDEPENDENT_VERIFIER_REQUIRED",),
            )
        direct_reasons.append("INDEPENDENT_VERIFIER_REQUIRED")
    if direct_reasons and request.criticality is not Criticality.C3:
        return _direct_or_blocked(direct, config, tuple(direct_reasons))

    try:
        role = _primary_role(request, route)
        support_role = _support_role(request, config.topology)
        candidate, batch = _candidate_forecast(
            request,
            config,
            capabilities,
            book,
            models,
            direct.total_usd,
            route,
        )
    except ValueError as exc:
        if request.criticality is Criticality.C3:
            return _decision(
                config=config,
                route=Route.BLOCKED,
                selected_usd=direct.total_usd,
                direct=direct,
                candidate=None,
                savings=Decimal("0"),
                reasons=("C3_CANDIDATE_INVALID", str(exc)),
            )
        return _direct_or_blocked(
            direct,
            config,
            ("CANDIDATE_FORECAST_INVALID", str(exc)),
        )

    savings = _savings(direct.total_usd, candidate.total_usd)
    if candidate.total_usd > config.budgets.max_run_usd:
        if request.criticality is Criticality.C3:
            return _decision(
                config=config,
                route=Route.BLOCKED,
                selected_usd=candidate.total_usd,
                direct=direct,
                candidate=candidate,
                savings=savings,
                reasons=("C3_RUN_BUDGET_EXCEEDED",),
                batch=batch,
            )
        return _direct_or_blocked(
            direct,
            config,
            ("RUN_BUDGET_EXCEEDED",),
            candidate=candidate,
            savings=savings,
            batch=batch,
        )

    if request.criticality is Criticality.C3:
        return _decision(
            config=config,
            route=Route.OPUS_DECISION,
            selected_usd=candidate.total_usd,
            direct=direct,
            candidate=candidate,
            savings=savings,
            reasons=("C3_OPUS_EXECUTIVE", "QUALITY_ROUTE_NOT_SAVINGS_CLAIM"),
            batch=batch,
            role=role,
            support_role=support_role,
            chain=_execution_chain(
                config.topology,
                route,
                role,
                support_role,
                writes_code=request.task_kind.writes_code,
            ),
        )

    if savings < config.routing.minimum_savings_margin:
        return _direct_or_blocked(
            direct,
            config,
            ("SAVINGS_MARGIN_NOT_CLEARED",),
            candidate=candidate,
            savings=savings,
            batch=batch,
        )

    return _decision(
        config=config,
        route=route,
        selected_usd=candidate.total_usd,
        direct=direct,
        candidate=candidate,
        savings=savings,
        reasons=("SAVINGS_MARGIN_CLEARED",),
        batch=batch,
        role=role,
        support_role=support_role,
        chain=_execution_chain(
            config.topology,
            route,
            role,
            support_role,
            writes_code=request.task_kind.writes_code,
        ),
    )


def _savings(direct: Decimal, candidate: Decimal) -> Decimal:
    if direct <= 0:
        return Decimal("0")
    return (direct - candidate) / direct
