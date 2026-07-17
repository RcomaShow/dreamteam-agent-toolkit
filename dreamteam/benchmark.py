"""Paired benchmark accounting with strict types and fail-closed claims."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from statistics import mean, median
from typing import Any, Iterable, Mapping


class Arm(str, Enum):
    DIRECT = "direct"
    DREAMTEAM = "dreamteam"


@dataclass(frozen=True)
class ModelUsageRecord:
    model: str
    effort: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass(frozen=True)
class RunResult:
    run_id: str
    pair_id: str
    task_id: str
    replicate_id: str
    arm: Arm
    repo_commit: str
    task_archetype: str
    topology: str
    route: str
    cache_cohort: str
    arm_order: int
    quality_oracle_id: str
    quality_pass: bool
    billed_usd: Decimal
    api_equivalent_usd: Decimal
    main_tokens: int
    worker_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    reread_bytes: int
    retries: int
    escalations: int
    failed_attempts: int
    elapsed_seconds: float
    pricing_catalog_id: str
    model_usage: tuple[ModelUsageRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.arm, Arm):
            raise TypeError("arm must be Arm")
        if not isinstance(self.quality_pass, bool):
            raise TypeError("quality_pass must be a boolean")
        for name in ("main_tokens", "worker_tokens", "cache_read_tokens", "cache_write_tokens", "reread_bytes", "retries", "escalations", "failed_attempts", "arm_order"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("billed_usd", "api_equivalent_usd"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or value < 0:
                raise ValueError(f"{name} must be a non-negative Decimal")
        required = (
            "run_id", "pair_id", "task_id", "replicate_id", "repo_commit",
            "task_archetype", "topology", "route", "cache_cohort",
            "quality_oracle_id", "pricing_catalog_id",
        )
        for name in required:
            if not getattr(self, name):
                raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class PairResult:
    pair_id: str
    replicate_id: str
    direct: RunResult
    dreamteam: RunResult

    @property
    def quality_parity(self) -> bool:
        return (
            self.direct.quality_pass
            and self.dreamteam.quality_pass
            and self.direct.quality_oracle_id == self.dreamteam.quality_oracle_id
            and self.direct.repo_commit == self.dreamteam.repo_commit
            and self.direct.pricing_catalog_id == self.dreamteam.pricing_catalog_id
        )

    @property
    def api_savings_ratio(self) -> Decimal | None:
        if self.direct.api_equivalent_usd <= 0:
            return None
        return (
            self.direct.api_equivalent_usd - self.dreamteam.api_equivalent_usd
        ) / self.direct.api_equivalent_usd


def load_results(data: Any) -> list[RunResult]:
    if not isinstance(data, list):
        raise TypeError("benchmark JSON root must be an array")
    return [_parse_run(item, index) for index, item in enumerate(data)]


def _parse_run(item: Any, index: int) -> RunResult:
    if not isinstance(item, dict):
        raise TypeError(f"result {index} must be an object")
    required = {
        "run_id", "pair_id", "task_id", "replicate_id", "arm", "repo_commit",
        "task_archetype", "topology", "route", "cache_cohort", "arm_order",
        "quality_oracle_id", "quality_pass", "billed_usd", "api_equivalent_usd",
        "main_tokens", "worker_tokens", "cache_read_tokens", "cache_write_tokens",
        "reread_bytes", "retries", "escalations", "failed_attempts",
        "elapsed_seconds", "pricing_catalog_id", "model_usage",
    }
    missing = required - set(item)
    unknown = set(item) - required
    if missing:
        raise ValueError(f"result {index}: missing fields {sorted(missing)}")
    if unknown:
        raise ValueError(f"result {index}: unknown fields {sorted(unknown)}")
    if type(item["quality_pass"]) is not bool:
        raise TypeError(f"result {index}: quality_pass must be JSON boolean")
    model_usage_raw = item["model_usage"]
    if not isinstance(model_usage_raw, list):
        raise TypeError(f"result {index}: model_usage must be an array")
    model_usage = tuple(_parse_model_usage(row, index) for row in model_usage_raw)
    return RunResult(
        run_id=_str(item["run_id"], "run_id"),
        pair_id=_str(item["pair_id"], "pair_id"),
        task_id=_str(item["task_id"], "task_id"),
        replicate_id=_str(item["replicate_id"], "replicate_id"),
        arm=Arm(_str(item["arm"], "arm")),
        repo_commit=_str(item["repo_commit"], "repo_commit"),
        task_archetype=_str(item["task_archetype"], "task_archetype"),
        topology=_str(item["topology"], "topology"),
        route=_str(item["route"], "route"),
        cache_cohort=_str(item["cache_cohort"], "cache_cohort"),
        arm_order=_int(item["arm_order"], "arm_order"),
        quality_oracle_id=_str(item["quality_oracle_id"], "quality_oracle_id"),
        quality_pass=item["quality_pass"],
        billed_usd=_decimal(item["billed_usd"], "billed_usd"),
        api_equivalent_usd=_decimal(item["api_equivalent_usd"], "api_equivalent_usd"),
        main_tokens=_int(item["main_tokens"], "main_tokens"),
        worker_tokens=_int(item["worker_tokens"], "worker_tokens"),
        cache_read_tokens=_int(item["cache_read_tokens"], "cache_read_tokens"),
        cache_write_tokens=_int(item["cache_write_tokens"], "cache_write_tokens"),
        reread_bytes=_int(item["reread_bytes"], "reread_bytes"),
        retries=_int(item["retries"], "retries"),
        escalations=_int(item["escalations"], "escalations"),
        failed_attempts=_int(item["failed_attempts"], "failed_attempts"),
        elapsed_seconds=_float(item["elapsed_seconds"], "elapsed_seconds"),
        pricing_catalog_id=_str(item["pricing_catalog_id"], "pricing_catalog_id"),
        model_usage=model_usage,
    )


def _parse_model_usage(item: Any, index: int) -> ModelUsageRecord:
    if not isinstance(item, dict):
        raise TypeError(f"result {index}: model usage must be an object")
    allowed = {"model", "effort", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"}
    if set(item) != allowed:
        raise ValueError(f"result {index}: invalid model usage fields")
    return ModelUsageRecord(
        model=_str(item["model"], "model"),
        effort=_str(item["effort"], "effort"),
        input_tokens=_int(item["input_tokens"], "input_tokens"),
        output_tokens=_int(item["output_tokens"], "output_tokens"),
        cache_read_tokens=_int(item["cache_read_tokens"], "cache_read_tokens"),
        cache_write_tokens=_int(item["cache_write_tokens"], "cache_write_tokens"),
    )


def pair_results(results: Iterable[RunResult]) -> list[PairResult]:
    grouped: dict[tuple[str, str], dict[Arm, RunResult]] = {}
    for result in results:
        key = (result.pair_id, result.replicate_id)
        arms = grouped.setdefault(key, {})
        if result.arm in arms:
            raise ValueError(f"{key}: duplicate arm {result.arm.value}")
        arms[result.arm] = result
    pairs: list[PairResult] = []
    for (pair_id, replicate_id), arms in sorted(grouped.items()):
        if set(arms) != {Arm.DIRECT, Arm.DREAMTEAM}:
            raise ValueError(f"{pair_id}/{replicate_id}: expected direct and dreamteam arms")
        pairs.append(PairResult(pair_id, replicate_id, arms[Arm.DIRECT], arms[Arm.DREAMTEAM]))
    return pairs


def summarize(
    pairs: Iterable[PairResult],
    *,
    minimum_savings_margin: Decimal = Decimal("0.30"),
    minimum_samples: int = 20,
) -> dict[str, object]:
    items = list(pairs)
    parity = [item for item in items if item.quality_parity]
    economic = [(item, item.api_savings_ratio) for item in parity if item.api_savings_ratio is not None]
    savings = [value for _, value in economic if value is not None]
    ordered = sorted(savings)
    median_savings = Decimal("0") if not ordered else median(ordered)
    mean_savings = Decimal("0") if not ordered else sum(ordered, Decimal("0")) / Decimal(len(ordered))
    p10 = Decimal("0") if not ordered else ordered[max(0, (len(ordered) - 1) // 10)]
    quality_allowed = bool(items) and len(parity) == len(items)
    positive = quality_allowed and bool(ordered) and median_savings > 0
    margin = positive and median_savings >= minimum_savings_margin
    publication = margin and len(ordered) >= minimum_samples and p10 > 0
    reasons: list[str] = []
    if not quality_allowed:
        reasons.append("quality parity is not complete")
    if not ordered:
        reasons.append("no pair has a positive direct cost")
    elif median_savings <= 0:
        reasons.append("median savings is not positive")
    elif median_savings < minimum_savings_margin:
        reasons.append("median savings does not clear the configured margin")
    if len(ordered) < minimum_samples:
        reasons.append("minimum sample count not reached")
    if ordered and p10 <= 0:
        reasons.append("lower-tail savings is not positive")
    return {
        "pairs": len(items),
        "valid_economic_pairs": len(ordered),
        "quality_parity_pairs": len(parity),
        "quality_parity_rate": 0.0 if not items else len(parity) / len(items),
        "median_api_savings_ratio": float(median_savings),
        "p10_api_savings_ratio": float(p10),
        "mean_api_savings_ratio": float(mean_savings),
        "negative_roi_pairs": sum(1 for value in ordered if value < 0),
        "quality_claim_allowed": quality_allowed,
        "positive_cost_claim_allowed": positive,
        "margin_claim_allowed": margin,
        "publication_claim_allowed": publication,
        "reasons": reasons,
    }


def require_paid_guard(allow_paid: bool, confirmation: str | None) -> None:
    if not allow_paid or confirmation != "I_UNDERSTAND_THIS_SPENDS_MONEY":
        raise PermissionError("paid inference disabled; pass both explicit safeguards")


def _str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a non-empty string")
    return value


def _int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative integer")
    return value


def _float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise TypeError(f"{name} must be a non-negative number")
    return float(value)


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"{name} must be numeric")
    result = Decimal(str(value))
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result
