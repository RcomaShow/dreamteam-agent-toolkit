"""Dependency-free DreamTeam runtime configuration with strict validation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


class Topology(str, Enum):
    LEAN = "lean"
    FRONTIER = "frontier"


class Profile(str, Enum):
    ECONOMY = "economy"
    BALANCED = "balanced"
    OFFLOAD = "offload"
    QUALITY = "quality"


@dataclass(frozen=True)
class ModelConfig:
    executive: str = "inherit"
    lead: str = "sonnet"
    workers: str = "haiku"


@dataclass(frozen=True)
class RoutingConfig:
    minimum_savings_margin: Decimal = Decimal("0.30")
    max_escalation_probability: Decimal = Decimal("0.25")
    max_main_reread_ratio: Decimal = Decimal("0.35")
    min_samples_for_enforcement: int = 20
    allow_closed_context_batch: bool = False
    allow_parallel_independent: bool = False


@dataclass(frozen=True)
class BudgetConfig:
    max_run_usd: Decimal = Decimal("1.0")
    max_active_workers: int = 1
    max_retries: int = 1
    max_worker_turns: int = 10


@dataclass(frozen=True)
class VerificationConfig:
    require_independent_writer_review: bool = True
    require_anchor_validation: bool = True
    allow_full_suite: str = "orchestrator-only"


@dataclass(frozen=True)
class TelemetryConfig:
    enabled: bool = False
    store_source_content: bool = False
    ledger: str = "off"
    enforcement: str = "advisory"


@dataclass(frozen=True)
class RuntimeCapabilities:
    batch_executor_available: bool = False
    hooks_available: bool = False
    resume_available: bool = False


@dataclass(frozen=True)
class RuntimeConfig:
    version: int
    constitution: str
    topology: Topology
    profile: Profile
    pricing_as_of: date
    models: ModelConfig
    routing: RoutingConfig
    budgets: BudgetConfig
    verification: VerificationConfig
    telemetry: TelemetryConfig

    @classmethod
    def defaults(cls, *, pricing_as_of: date, topology: Topology = Topology.LEAN) -> "RuntimeConfig":
        return cls(
            version=2,
            constitution="DT-C1",
            topology=topology,
            profile=Profile.BALANCED,
            pricing_as_of=pricing_as_of,
            models=ModelConfig(),
            routing=RoutingConfig(),
            budgets=BudgetConfig(),
            verification=VerificationConfig(),
            telemetry=TelemetryConfig(),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "RuntimeConfig":
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON configuration: {exc}") from exc
        if not isinstance(data, dict):
            raise TypeError("configuration root must be an object")
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RuntimeConfig":
        _only(data, {"version", "constitution", "topology", "profile", "pricingAsOf", "models", "routing", "budgets", "verification", "telemetry"}, "root")
        if data.get("version") != 2:
            raise ValueError("version must be 2")
        if data.get("constitution", "DT-C1") != "DT-C1":
            raise ValueError("constitution must be DT-C1")
        if "pricingAsOf" not in data:
            raise ValueError("pricingAsOf is required")
        try:
            pricing_as_of = date.fromisoformat(_string(data["pricingAsOf"], "pricingAsOf"))
        except ValueError as exc:
            raise ValueError("pricingAsOf must use YYYY-MM-DD") from exc

        models_raw = _object(data.get("models", {}), "models")
        _only(models_raw, {"executive", "lead", "workers"}, "models")
        models = ModelConfig(
            executive=_string(models_raw.get("executive", "inherit"), "models.executive"),
            lead=_string(models_raw.get("lead", "sonnet"), "models.lead"),
            workers=_string(models_raw.get("workers", "haiku"), "models.workers"),
        )

        routing_raw = _object(data.get("routing", {}), "routing")
        _only(routing_raw, {"minimumSavingsMargin", "maxEscalationProbability", "maxMainRereadRatio", "minSamplesForEnforcement", "allowClosedContextBatch", "allowParallelIndependent"}, "routing")
        routing = RoutingConfig(
            minimum_savings_margin=_ratio(routing_raw.get("minimumSavingsMargin", 0.30), "routing.minimumSavingsMargin"),
            max_escalation_probability=_ratio(routing_raw.get("maxEscalationProbability", 0.25), "routing.maxEscalationProbability"),
            max_main_reread_ratio=_ratio(routing_raw.get("maxMainRereadRatio", 0.35), "routing.maxMainRereadRatio"),
            min_samples_for_enforcement=_positive_int(routing_raw.get("minSamplesForEnforcement", 20), "routing.minSamplesForEnforcement"),
            allow_closed_context_batch=_bool(routing_raw.get("allowClosedContextBatch", False), "routing.allowClosedContextBatch"),
            allow_parallel_independent=_bool(routing_raw.get("allowParallelIndependent", False), "routing.allowParallelIndependent"),
        )

        budgets_raw = _object(data.get("budgets", {}), "budgets")
        _only(budgets_raw, {"maxRunUsd", "maxActiveWorkers", "maxRetries", "maxWorkerTurns"}, "budgets")
        budgets = BudgetConfig(
            max_run_usd=_nonnegative_decimal(budgets_raw.get("maxRunUsd", 1.0), "budgets.maxRunUsd"),
            max_active_workers=_bounded_int(budgets_raw.get("maxActiveWorkers", 1), 1, 4, "budgets.maxActiveWorkers"),
            max_retries=_bounded_int(budgets_raw.get("maxRetries", 1), 0, 20, "budgets.maxRetries"),
            max_worker_turns=_positive_int(budgets_raw.get("maxWorkerTurns", 10), "budgets.maxWorkerTurns"),
        )

        verification_raw = _object(data.get("verification"), "verification")
        _only(verification_raw, {"requireIndependentWriterReview", "requireAnchorValidation", "allowFullSuite"}, "verification")
        if verification_raw.get("requireIndependentWriterReview") is not True:
            raise ValueError("verification.requireIndependentWriterReview must be true")
        if verification_raw.get("requireAnchorValidation") is not True:
            raise ValueError("verification.requireAnchorValidation must be true")
        allow_full_suite = _string(verification_raw.get("allowFullSuite", "orchestrator-only"), "verification.allowFullSuite")
        if allow_full_suite not in {"orchestrator-only", "allowed"}:
            raise ValueError("verification.allowFullSuite is invalid")
        verification = VerificationConfig(True, True, allow_full_suite)

        telemetry_raw = _object(data.get("telemetry"), "telemetry")
        _only(telemetry_raw, {"enabled", "storeSourceContent", "ledger", "enforcement"}, "telemetry")
        if telemetry_raw.get("storeSourceContent") is not False:
            raise ValueError("telemetry.storeSourceContent must be false")
        ledger = _string(telemetry_raw.get("ledger", "off"), "telemetry.ledger")
        enforcement = _string(telemetry_raw.get("enforcement", "advisory"), "telemetry.enforcement")
        if ledger not in {"off", "sqlite"}:
            raise ValueError("telemetry.ledger is invalid")
        if enforcement not in {"advisory", "strict"}:
            raise ValueError("telemetry.enforcement is invalid")
        telemetry = TelemetryConfig(
            enabled=_bool(telemetry_raw.get("enabled", False), "telemetry.enabled"),
            store_source_content=False,
            ledger=ledger,
            enforcement=enforcement,
        )

        return cls(
            version=2,
            constitution="DT-C1",
            topology=Topology(_string(data.get("topology", "lean"), "topology")),
            profile=Profile(_string(data.get("profile", "balanced"), "profile")),
            pricing_as_of=pricing_as_of,
            models=models,
            routing=routing,
            budgets=budgets,
            verification=verification,
            telemetry=telemetry,
        )


def _only(data: Mapping[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"{context}: unknown properties {sorted(unknown)}")


def _object(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be an object")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a non-empty string")
    return value


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")
    return value


def _ratio(value: Any, name: str) -> Decimal:
    result = _nonnegative_decimal(value, name)
    if result > 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _nonnegative_decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise TypeError(f"{name} must be numeric")
    result = Decimal(str(value))
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _positive_int(value: Any, name: str) -> int:
    return _bounded_int(value, 1, 2**31 - 1, name)


def _bounded_int(value: Any, minimum: int, maximum: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value
