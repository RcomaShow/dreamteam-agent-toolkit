"""Dependency-free DreamTeam runtime configuration with strict validation."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


class Topology(str, Enum):
    LEAN = "lean"
    OPUS_SONNET = "opus-sonnet"
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

    def __post_init__(self) -> None:
        for name in (
            "batch_executor_available",
            "hooks_available",
            "resume_available",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be a boolean")


_PROFILE_DEFAULTS: dict[Profile, dict[str, object]] = {
    Profile.ECONOMY: {
        "minimumSavingsMargin": Decimal("0.40"),
        "maxActiveWorkers": 1,
        "maxRetries": 0,
        "maxWorkerTurns": 6,
        "allowParallelIndependent": False,
    },
    Profile.BALANCED: {
        "minimumSavingsMargin": Decimal("0.30"),
        "maxActiveWorkers": 1,
        "maxRetries": 1,
        "maxWorkerTurns": 10,
        "allowParallelIndependent": False,
    },
    Profile.OFFLOAD: {
        "minimumSavingsMargin": Decimal("0.20"),
        "maxActiveWorkers": 2,
        "maxRetries": 1,
        "maxWorkerTurns": 10,
        "allowParallelIndependent": True,
    },
    Profile.QUALITY: {
        "minimumSavingsMargin": Decimal("0.00"),
        "maxActiveWorkers": 2,
        "maxRetries": 2,
        "maxWorkerTurns": 14,
        "allowParallelIndependent": True,
    },
}


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
    def defaults(
        cls,
        *,
        pricing_as_of: date,
        topology: Topology = Topology.LEAN,
        profile: Profile = Profile.BALANCED,
    ) -> "RuntimeConfig":
        return cls.from_mapping(
            {
                "version": 2,
                "constitution": "DT-C1",
                "topology": topology.value,
                "profile": profile.value,
                "pricingAsOf": pricing_as_of.isoformat(),
                "verification": {
                    "requireIndependentWriterReview": True,
                    "requireAnchorValidation": True,
                },
                "telemetry": {
                    "enabled": False,
                    "storeSourceContent": False,
                    "ledger": "off",
                    "enforcement": "advisory",
                },
            }
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
        _only(
            data,
            {
                "version",
                "constitution",
                "topology",
                "profile",
                "pricingAsOf",
                "models",
                "routing",
                "budgets",
                "verification",
                "telemetry",
            },
            "root",
        )
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

        topology = Topology(_string(data.get("topology", Topology.LEAN.value), "topology"))
        profile = Profile(_string(data.get("profile", Profile.BALANCED.value), "profile"))
        defaults = _PROFILE_DEFAULTS[profile]

        models_raw = _object(data.get("models", {}), "models")
        _only(models_raw, {"executive", "lead", "workers"}, "models")
        models = ModelConfig(
            executive=_string(models_raw.get("executive", "inherit"), "models.executive"),
            lead=_string(models_raw.get("lead", "sonnet"), "models.lead"),
            workers=_string(models_raw.get("workers", "haiku"), "models.workers"),
        )

        routing_raw = _object(data.get("routing", {}), "routing")
        _only(
            routing_raw,
            {
                "minimumSavingsMargin",
                "maxEscalationProbability",
                "maxMainRereadRatio",
                "minSamplesForEnforcement",
                "allowClosedContextBatch",
                "allowParallelIndependent",
            },
            "routing",
        )
        routing = RoutingConfig(
            minimum_savings_margin=_ratio(
                routing_raw.get("minimumSavingsMargin", defaults["minimumSavingsMargin"]),
                "routing.minimumSavingsMargin",
            ),
            max_escalation_probability=_ratio(
                routing_raw.get("maxEscalationProbability", Decimal("0.25")),
                "routing.maxEscalationProbability",
            ),
            max_main_reread_ratio=_ratio(
                routing_raw.get("maxMainRereadRatio", Decimal("0.35")),
                "routing.maxMainRereadRatio",
            ),
            min_samples_for_enforcement=_positive_int(
                routing_raw.get("minSamplesForEnforcement", 20),
                "routing.minSamplesForEnforcement",
            ),
            allow_closed_context_batch=_bool(
                routing_raw.get("allowClosedContextBatch", False),
                "routing.allowClosedContextBatch",
            ),
            allow_parallel_independent=_bool(
                routing_raw.get(
                    "allowParallelIndependent",
                    defaults["allowParallelIndependent"],
                ),
                "routing.allowParallelIndependent",
            ),
        )

        budgets_raw = _object(data.get("budgets", {}), "budgets")
        _only(
            budgets_raw,
            {"maxRunUsd", "maxActiveWorkers", "maxRetries", "maxWorkerTurns"},
            "budgets",
        )
        budgets = BudgetConfig(
            max_run_usd=_nonnegative_decimal(
                budgets_raw.get("maxRunUsd", Decimal("1.0")),
                "budgets.maxRunUsd",
            ),
            max_active_workers=_bounded_int(
                budgets_raw.get("maxActiveWorkers", defaults["maxActiveWorkers"]),
                1,
                4,
                "budgets.maxActiveWorkers",
            ),
            max_retries=_bounded_int(
                budgets_raw.get("maxRetries", defaults["maxRetries"]),
                0,
                20,
                "budgets.maxRetries",
            ),
            max_worker_turns=_positive_int(
                budgets_raw.get("maxWorkerTurns", defaults["maxWorkerTurns"]),
                "budgets.maxWorkerTurns",
            ),
        )

        verification_raw = _object(data.get("verification"), "verification")
        _only(
            verification_raw,
            {
                "requireIndependentWriterReview",
                "requireAnchorValidation",
                "allowFullSuite",
            },
            "verification",
        )
        if verification_raw.get("requireIndependentWriterReview") is not True:
            raise ValueError("verification.requireIndependentWriterReview must be true")
        if verification_raw.get("requireAnchorValidation") is not True:
            raise ValueError("verification.requireAnchorValidation must be true")
        allow_full_suite = _string(
            verification_raw.get("allowFullSuite", "orchestrator-only"),
            "verification.allowFullSuite",
        )
        if allow_full_suite not in {"orchestrator-only", "allowed"}:
            raise ValueError("verification.allowFullSuite is invalid")
        verification = VerificationConfig(True, True, allow_full_suite)

        telemetry_raw = _object(data.get("telemetry"), "telemetry")
        _only(
            telemetry_raw,
            {"enabled", "storeSourceContent", "ledger", "enforcement"},
            "telemetry",
        )
        if telemetry_raw.get("storeSourceContent") is not False:
            raise ValueError("telemetry.storeSourceContent must be false")
        enabled = _bool(telemetry_raw.get("enabled", False), "telemetry.enabled")
        ledger = _string(telemetry_raw.get("ledger", "off"), "telemetry.ledger")
        enforcement = _string(
            telemetry_raw.get("enforcement", "advisory"),
            "telemetry.enforcement",
        )
        if ledger not in {"off", "sqlite"}:
            raise ValueError("telemetry.ledger is invalid")
        if enforcement not in {"advisory", "strict"}:
            raise ValueError("telemetry.enforcement is invalid")
        if enabled and ledger != "sqlite":
            raise ValueError("enabled telemetry requires telemetry.ledger=sqlite")
        if not enabled and (ledger != "off" or enforcement != "advisory"):
            raise ValueError(
                "disabled telemetry requires telemetry.ledger=off and enforcement=advisory"
            )
        if enforcement == "strict" and not enabled:
            raise ValueError("strict enforcement requires telemetry.enabled=true")
        telemetry = TelemetryConfig(
            enabled=enabled,
            store_source_content=False,
            ledger=ledger,
            enforcement=enforcement,
        )

        return cls(
            version=2,
            constitution="DT-C1",
            topology=topology,
            profile=profile,
            pricing_as_of=pricing_as_of,
            models=models,
            routing=routing,
            budgets=budgets,
            verification=verification,
            telemetry=telemetry,
        )


    def effective_mapping(self) -> dict[str, object]:
        """Return a fully materialized, JSON-safe execution configuration."""
        return {
            "version": self.version,
            "constitution": self.constitution,
            "topology": self.topology.value,
            "profile": self.profile.value,
            "pricingAsOf": self.pricing_as_of.isoformat(),
            "models": {
                "executive": self.models.executive,
                "lead": self.models.lead,
                "workers": self.models.workers,
            },
            "routing": {
                "minimumSavingsMargin": format(self.routing.minimum_savings_margin.normalize(), "f"),
                "maxEscalationProbability": format(self.routing.max_escalation_probability.normalize(), "f"),
                "maxMainRereadRatio": format(self.routing.max_main_reread_ratio.normalize(), "f"),
                "minSamplesForEnforcement": self.routing.min_samples_for_enforcement,
                "allowClosedContextBatch": self.routing.allow_closed_context_batch,
                "allowParallelIndependent": self.routing.allow_parallel_independent,
            },
            "budgets": {
                "maxRunUsd": format(self.budgets.max_run_usd.normalize(), "f"),
                "maxActiveWorkers": self.budgets.max_active_workers,
                "maxRetries": self.budgets.max_retries,
                "maxWorkerTurns": self.budgets.max_worker_turns,
            },
            "verification": {
                "requireIndependentWriterReview": self.verification.require_independent_writer_review,
                "requireAnchorValidation": self.verification.require_anchor_validation,
                "allowFullSuite": self.verification.allow_full_suite,
            },
            "telemetry": {
                "enabled": self.telemetry.enabled,
                "storeSourceContent": self.telemetry.store_source_content,
                "ledger": self.telemetry.ledger,
                "enforcement": self.telemetry.enforcement,
            },
        }

    @property
    def effective_hash(self) -> str:
        encoded = json.dumps(
            self.effective_mapping(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "sha256:" + sha256(encoded).hexdigest()


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
    if type(value) is not bool:
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
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _positive_int(value: Any, name: str) -> int:
    return _bounded_int(value, 1, 2**31 - 1, name)


def _bounded_int(value: Any, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value
