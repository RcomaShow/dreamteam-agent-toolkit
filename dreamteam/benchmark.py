"""Paired benchmark accounting with strict invariants and recomputed costs."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from statistics import median
from typing import Any, Iterable

from .pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost, resolve_model


class Arm(str, Enum):
    DIRECT = "direct"
    DREAMTEAM = "dreamteam"


_VALID_CRITICALITIES = {"M0", "L1", "L2", "C3"}
_VALID_TASK_KINDS = {
    "discovery", "edit", "implementation", "test", "scaffold",
    "documentation", "review", "migration",
}
_VALID_SIZE_BANDS = {"small", "medium", "large", "xlarge"}
_VALID_TOPOLOGIES = {"lean", "opus-sonnet", "frontier"}
_VALID_ROUTES = {
    "BLOCKED", "MAIN_DIRECT", "HAIKU_DISCOVERY", "HAIKU_EXECUTE",
    "SONNET_LEAD", "OPUS_DECISION",
}
_VALID_CACHE_COHORTS = {"cold", "warm"}


@dataclass(frozen=True)
class ModelUsageRecord:
    model: str
    effort: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_5m_tokens: int = 0
    cache_write_1h_tokens: int = 0
    lane: ExecutionLane = ExecutionLane.INTERACTIVE

    def __post_init__(self) -> None:
        if not self.model or not self.effort:
            raise ValueError("model and effort are required")
        for name in (
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_5m_tokens",
            "cache_write_1h_tokens",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.lane, ExecutionLane):
            raise TypeError("lane must be ExecutionLane")

    @property
    def usage(self) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_read_tokens=self.cache_read_tokens,
            cache_write_5m_tokens=self.cache_write_5m_tokens,
            cache_write_1h_tokens=self.cache_write_1h_tokens,
        )


@dataclass(frozen=True)
class RunResult:
    run_id: str
    pair_id: str
    task_id: str
    replicate_id: str
    arm: Arm
    repo_commit: str
    task_archetype: str
    criticality: str
    task_kind: str
    size_band: str
    topology: str
    route: str
    agent_role: str
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
    adapter_version: str
    config_hash: str
    environment_id: str
    timeout_seconds: float
    model_usage: tuple[ModelUsageRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.arm, Arm):
            raise TypeError("arm must be Arm")
        if type(self.quality_pass) is not bool:
            raise TypeError("quality_pass must be a boolean")
        for name in (
            "main_tokens",
            "worker_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "reread_bytes",
            "retries",
            "escalations",
            "failed_attempts",
            "arm_order",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.arm_order not in {0, 1}:
            raise ValueError("arm_order must be 0 or 1")
        for name in ("billed_usd", "api_equivalent_usd"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError(f"{name} must be a finite non-negative Decimal")
        for name in ("elapsed_seconds", "timeout_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{name} must be a non-negative number")
        required = (
            "run_id",
            "pair_id",
            "task_id",
            "replicate_id",
            "repo_commit",
            "task_archetype",
            "criticality",
            "task_kind",
            "size_band",
            "topology",
            "route",
            "agent_role",
            "cache_cohort",
            "quality_oracle_id",
            "pricing_catalog_id",
            "adapter_version",
            "config_hash",
            "environment_id",
        )
        for name in required:
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if self.criticality not in _VALID_CRITICALITIES:
            raise ValueError("criticality is invalid")
        if self.task_kind not in _VALID_TASK_KINDS:
            raise ValueError("task_kind is invalid")
        if self.size_band not in _VALID_SIZE_BANDS:
            raise ValueError("size_band is invalid")
        if self.topology not in _VALID_TOPOLOGIES:
            raise ValueError("topology is invalid")
        if self.route not in _VALID_ROUTES:
            raise ValueError("route is invalid")
        if self.cache_cohort not in _VALID_CACHE_COHORTS:
            raise ValueError("cache_cohort is invalid")
        if not self.model_usage:
            raise ValueError("model_usage must not be empty")
        computed = recompute_api_equivalent_usd(self)
        if computed != self.api_equivalent_usd:
            raise ValueError(
                f"api_equivalent_usd mismatch: declared={self.api_equivalent_usd} computed={computed}"
            )
        input_output = sum(
            record.input_tokens + record.output_tokens for record in self.model_usage
        )
        if input_output != self.main_tokens + self.worker_tokens:
            raise ValueError(
                "main_tokens + worker_tokens must equal model_usage input/output tokens"
            )
        cache_reads = sum(record.cache_read_tokens for record in self.model_usage)
        if cache_reads != self.cache_read_tokens:
            raise ValueError("cache_read_tokens must equal model_usage cache reads")
        cache_writes = sum(
            record.cache_write_5m_tokens + record.cache_write_1h_tokens
            for record in self.model_usage
        )
        if cache_writes != self.cache_write_tokens:
            raise ValueError("cache_write_tokens must equal model_usage cache writes")
        validate_arm_semantics(self)

    @property
    def bucket_key(self) -> tuple[str, ...]:
        return (
            self.task_archetype,
            self.criticality,
            self.task_kind,
            self.size_band,
            self.topology,
            self.route,
            self.agent_role,
            self.cache_cohort,
            self.adapter_version,
        )


@dataclass(frozen=True)
class PairResult:
    pair_id: str
    replicate_id: str
    direct: RunResult
    dreamteam: RunResult

    def __post_init__(self) -> None:
        equal_fields = (
            "task_id",
            "repo_commit",
            "task_archetype",
            "criticality",
            "task_kind",
            "size_band",
            "cache_cohort",
            "quality_oracle_id",
            "pricing_catalog_id",
            "adapter_version",
            "config_hash",
            "environment_id",
            "timeout_seconds",
        )
        mismatches = [
            name
            for name in equal_fields
            if getattr(self.direct, name) != getattr(self.dreamteam, name)
        ]
        if mismatches:
            raise ValueError(f"pair invariant mismatch: {mismatches}")
        if self.direct.arm_order == self.dreamteam.arm_order:
            raise ValueError("paired arms must have distinct arm_order")

    @property
    def quality_parity(self) -> bool:
        return self.direct.quality_pass and self.dreamteam.quality_pass

    @property
    def api_savings_ratio(self) -> Decimal | None:
        if self.direct.api_equivalent_usd <= 0:
            return None
        return (
            self.direct.api_equivalent_usd - self.dreamteam.api_equivalent_usd
        ) / self.direct.api_equivalent_usd

    @property
    def bucket_key(self) -> tuple[str, ...]:
        return self.dreamteam.bucket_key


def validate_arm_semantics(result: RunResult) -> None:
    models = {resolve_model(record.model) for record in result.model_usage}
    sonnet = "claude-sonnet-5"
    haiku = "claude-haiku-4-5"
    opus = "claude-opus-4-8"
    if result.arm is Arm.DIRECT:
        if result.route != "MAIN_DIRECT":
            raise ValueError("direct arm must use MAIN_DIRECT")
        if result.agent_role != "direct-sonnet":
            raise ValueError("direct arm must use direct-sonnet role")
        if result.worker_tokens != 0:
            raise ValueError("direct arm may not report worker tokens")
        if models != {sonnet}:
            raise ValueError("direct arm must be Sonnet-only")
        if any(record.lane is not ExecutionLane.INTERACTIVE for record in result.model_usage):
            raise ValueError("direct arm must use the interactive lane")
        return

    if result.route == "MAIN_DIRECT":
        if result.worker_tokens != 0 or models != {sonnet}:
            raise ValueError("DreamTeam MAIN_DIRECT fallback must remain Sonnet-only")
        return
    if result.topology == "lean":
        if opus in models:
            raise ValueError("Lean benchmark arm may not contain Opus usage")
        if result.route in {"HAIKU_DISCOVERY", "HAIKU_EXECUTE"} and haiku not in models:
            raise ValueError("Lean Haiku route must contain Haiku usage")
        if result.route == "SONNET_LEAD" and sonnet not in models:
            raise ValueError("Lean Sonnet route must contain Sonnet usage")
        return
    if result.topology == "opus-sonnet":
        if haiku in models or not {opus, sonnet}.issubset(models):
            raise ValueError("Opus-Sonnet must contain Opus and Sonnet with no hidden Haiku")
        return
    if result.topology == "frontier":
        if not {opus, sonnet, haiku}.issubset(models):
            raise ValueError("Frontier must account for Opus, Sonnet, and Haiku")
        return
    raise ValueError("unsupported benchmark topology")


def recompute_api_equivalent_usd(result: RunResult) -> Decimal:
    book = PriceBook.from_catalog_id(result.pricing_catalog_id)
    return sum(
        (
            estimate_cost(
                record.model,
                record.usage,
                price_book=book,
                lane=record.lane,
            ).total_usd
            for record in result.model_usage
        ),
        Decimal("0"),
    )


def load_results(data: Any) -> list[RunResult]:
    if not isinstance(data, list):
        raise TypeError("benchmark JSON root must be an array")
    return [_parse_run(item, index) for index, item in enumerate(data)]


def _parse_run(item: Any, index: int) -> RunResult:
    if not isinstance(item, dict):
        raise TypeError(f"result {index} must be an object")
    required = {
        "run_id",
        "pair_id",
        "task_id",
        "replicate_id",
        "arm",
        "repo_commit",
        "task_archetype",
        "criticality",
        "task_kind",
        "size_band",
        "topology",
        "route",
        "agent_role",
        "cache_cohort",
        "arm_order",
        "quality_oracle_id",
        "quality_pass",
        "billed_usd",
        "api_equivalent_usd",
        "main_tokens",
        "worker_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reread_bytes",
        "retries",
        "escalations",
        "failed_attempts",
        "elapsed_seconds",
        "pricing_catalog_id",
        "adapter_version",
        "config_hash",
        "environment_id",
        "timeout_seconds",
        "model_usage",
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
        criticality=_str(item["criticality"], "criticality"),
        task_kind=_str(item["task_kind"], "task_kind"),
        size_band=_str(item["size_band"], "size_band"),
        topology=_str(item["topology"], "topology"),
        route=_str(item["route"], "route"),
        agent_role=_str(item["agent_role"], "agent_role"),
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
        adapter_version=_str(item["adapter_version"], "adapter_version"),
        config_hash=_str(item["config_hash"], "config_hash"),
        environment_id=_str(item["environment_id"], "environment_id"),
        timeout_seconds=_float(item["timeout_seconds"], "timeout_seconds"),
        model_usage=model_usage,
    )


def _parse_model_usage(item: Any, index: int) -> ModelUsageRecord:
    if not isinstance(item, dict):
        raise TypeError(f"result {index}: model usage must be an object")
    allowed = {
        "model",
        "effort",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_5m_tokens",
        "cache_write_1h_tokens",
        "lane",
    }
    if set(item) != allowed:
        raise ValueError(f"result {index}: invalid model usage fields")
    return ModelUsageRecord(
        model=_str(item["model"], "model"),
        effort=_str(item["effort"], "effort"),
        input_tokens=_int(item["input_tokens"], "input_tokens"),
        output_tokens=_int(item["output_tokens"], "output_tokens"),
        cache_read_tokens=_int(item["cache_read_tokens"], "cache_read_tokens"),
        cache_write_5m_tokens=_int(item["cache_write_5m_tokens"], "cache_write_5m_tokens"),
        cache_write_1h_tokens=_int(item["cache_write_1h_tokens"], "cache_write_1h_tokens"),
        lane=ExecutionLane(_str(item["lane"], "lane")),
    )


def pair_results(results: Iterable[RunResult]) -> list[PairResult]:
    grouped: dict[tuple[str, str], dict[Arm, RunResult]] = {}
    run_ids: set[str] = set()
    for result in results:
        if result.run_id in run_ids:
            raise ValueError(f"duplicate run_id: {result.run_id}")
        run_ids.add(result.run_id)
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


def _distribution(values: list[Decimal]) -> tuple[Decimal, Decimal, Decimal]:
    ordered = sorted(values)
    if not ordered:
        return Decimal("0"), Decimal("0"), Decimal("0")
    med = median(ordered)
    mean = sum(ordered, Decimal("0")) / Decimal(len(ordered))
    p10 = ordered[max(0, (len(ordered) - 1) // 10)]
    return med, mean, p10


def summarize(
    pairs: Iterable[PairResult],
    *,
    minimum_savings_margin: Decimal = Decimal("0.30"),
    minimum_samples: int = 20,
) -> dict[str, object]:
    if (
        not isinstance(minimum_savings_margin, Decimal)
        or not minimum_savings_margin.is_finite()
        or not Decimal("0") <= minimum_savings_margin <= Decimal("1")
    ):
        raise ValueError("minimum_savings_margin must be a finite Decimal between 0 and 1")
    if type(minimum_samples) is not int or minimum_samples < 1:
        raise ValueError("minimum_samples must be a positive integer")
    items = list(pairs)
    parity = [item for item in items if item.quality_parity]
    economic = [(item, item.api_savings_ratio) for item in parity if item.api_savings_ratio is not None]
    savings = [value for _, value in economic if value is not None]
    median_savings, mean_savings, p10 = _distribution(savings)
    quality_allowed = bool(items) and len(parity) == len(items)
    positive = quality_allowed and bool(savings) and median_savings > 0
    margin = positive and median_savings >= minimum_savings_margin

    buckets: dict[tuple[str, ...], list[Decimal]] = {}
    for pair, value in economic:
        if value is not None:
            buckets.setdefault(pair.bucket_key, []).append(value)
    bucket_results: dict[str, dict[str, object]] = {}
    buckets_publishable = bool(buckets)
    for key, values in sorted(buckets.items()):
        b_median, b_mean, b_p10 = _distribution(values)
        publishable = (
            len(values) >= minimum_samples
            and b_median >= minimum_savings_margin
            and b_p10 > 0
        )
        buckets_publishable = buckets_publishable and publishable
        bucket_results["|".join(key)] = {
            "samples": len(values),
            "median_api_savings_ratio": float(b_median),
            "mean_api_savings_ratio": float(b_mean),
            "p10_api_savings_ratio": float(b_p10),
            "publication_claim_allowed": publishable,
        }

    publication = margin and buckets_publishable
    quality_failures = len(items) - len(parity)
    dreamteam_success_cost = sum(
        (pair.dreamteam.api_equivalent_usd for pair in parity), Decimal("0")
    )
    cost_per_success = (
        None
        if not parity
        else float(dreamteam_success_cost / Decimal(len(parity)))
    )
    mean_direct_elapsed = (
        0.0
        if not items
        else sum(pair.direct.elapsed_seconds for pair in items) / len(items)
    )
    mean_dreamteam_elapsed = (
        0.0
        if not items
        else sum(pair.dreamteam.elapsed_seconds for pair in items) / len(items)
    )
    reasons: list[str] = []
    if not quality_allowed:
        reasons.append("quality parity is not complete")
    if not savings:
        reasons.append("no pair has a positive direct cost")
    elif median_savings <= 0:
        reasons.append("median savings is not positive")
    elif median_savings < minimum_savings_margin:
        reasons.append("median savings does not clear the configured margin")
    if not buckets_publishable:
        reasons.append("one or more benchmark buckets fail sample, margin, or lower-tail gates")
    return {
        "pairs": len(items),
        "valid_economic_pairs": len(savings),
        "quality_parity_pairs": len(parity),
        "quality_parity_rate": 0.0 if not items else len(parity) / len(items),
        "median_api_savings_ratio": float(median_savings),
        "p10_api_savings_ratio": float(p10),
        "mean_api_savings_ratio": float(mean_savings),
        "negative_roi_pairs": sum(1 for value in savings if value < 0),
        "quality_failure_pairs": quality_failures,
        "quality_failure_rate": 0.0 if not items else quality_failures / len(items),
        "dreamteam_api_cost_per_quality_pair": cost_per_success,
        "mean_direct_elapsed_seconds": mean_direct_elapsed,
        "mean_dreamteam_elapsed_seconds": mean_dreamteam_elapsed,
        "quality_claim_allowed": quality_allowed,
        "positive_cost_claim_allowed": positive,
        "margin_claim_allowed": margin,
        "publication_claim_allowed": publication,
        "buckets": bucket_results,
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
    result = float(value)
    if result == float("inf") or result != result:
        raise ValueError(f"{name} must be finite")
    return result


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"{name} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result
