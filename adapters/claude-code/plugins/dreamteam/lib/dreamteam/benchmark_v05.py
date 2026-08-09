"""DreamTeam 0.5 paired benchmark extensions for token and payload efficiency."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Any, Iterable, Mapping

from .benchmark import PairResult, summarize as summarize_v04
from .measurement import savings_ratio
from .pricing import resolve_model


@dataclass(frozen=True)
class NormalizedRunMeasurement:
    run_id: str
    normalized_payload_bytes: int
    handoff_tokens: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id:
            raise TypeError("run_id must be a non-empty string")
        for name in ("normalized_payload_bytes", "handoff_tokens"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise TypeError(f"{name} must be a non-negative integer")


def load_normalized_measurements(data: Any) -> dict[str, NormalizedRunMeasurement]:
    if not isinstance(data, list):
        raise TypeError("normalized measurement JSON root must be an array")
    result: dict[str, NormalizedRunMeasurement] = {}
    required = {"run_id", "normalized_payload_bytes", "handoff_tokens"}
    for index, row in enumerate(data):
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError(f"measurement {index}: invalid fields")
        measurement = NormalizedRunMeasurement(
            run_id=row["run_id"],
            normalized_payload_bytes=row["normalized_payload_bytes"],
            handoff_tokens=row["handoff_tokens"],
        )
        if measurement.run_id in result:
            raise ValueError(f"duplicate normalized measurement run_id: {measurement.run_id}")
        result[measurement.run_id] = measurement
    return result


def _distribution(values: list[Decimal]) -> tuple[Decimal, Decimal, Decimal]:
    ordered = sorted(values)
    if not ordered:
        return Decimal("0"), Decimal("0"), Decimal("0")
    med = median(ordered)
    mean = sum(ordered, Decimal("0")) / Decimal(len(ordered))
    p10 = ordered[max(0, (len(ordered) - 1) // 10)]
    return med, mean, p10


def _validate_v05_pair_semantics(pair: PairResult) -> None:
    """Reject 0.4-compatible benchmark rows that omit 0.5 whole-tree overhead."""
    dreamteam = pair.dreamteam
    if not dreamteam.adapter_version.startswith("0.5."):
        raise ValueError("0.5 benchmark requires adapter_version 0.5.x")
    if dreamteam.topology != "lean":
        return
    if dreamteam.route not in {"HAIKU_DISCOVERY", "HAIKU_EXECUTE"}:
        return
    models = {resolve_model(record.model) for record in dreamteam.model_usage}
    required = {"claude-sonnet-5", "claude-haiku-4-5"}
    if not required.issubset(models):
        raise ValueError(
            "0.5 Lean delegated benchmark requires explicit Sonnet executive "
            "and Haiku worker usage"
        )
    if dreamteam.main_tokens <= 0 or dreamteam.worker_tokens <= 0:
        raise ValueError(
            "0.5 Lean delegated benchmark requires non-zero main and worker tokens"
        )


def _pair_token_metrics(pair: PairResult) -> tuple[Decimal, Decimal]:
    direct_total = Decimal(pair.direct.main_tokens + pair.direct.worker_tokens)
    dreamteam_total = Decimal(pair.dreamteam.main_tokens + pair.dreamteam.worker_tokens)
    return (
        savings_ratio(direct_total, dreamteam_total),
        savings_ratio(pair.direct.main_tokens, pair.dreamteam.main_tokens),
    )


def summarize_v05(
    pairs: Iterable[PairResult],
    *,
    normalized_measurements: Mapping[str, NormalizedRunMeasurement] | None = None,
    minimum_cost_savings_margin: Decimal = Decimal("0.30"),
    minimum_total_token_savings: Decimal = Decimal("0.05"),
    minimum_main_token_savings: Decimal = Decimal("0.15"),
    minimum_samples: int = 20,
) -> dict[str, object]:
    for name, value in (
        ("minimum_total_token_savings", minimum_total_token_savings),
        ("minimum_main_token_savings", minimum_main_token_savings),
    ):
        if (
            not isinstance(value, Decimal)
            or not value.is_finite()
            or not Decimal("0") <= value <= Decimal("1")
        ):
            raise ValueError(f"{name} must be a finite Decimal between 0 and 1")
    if type(minimum_samples) is not int or minimum_samples < 1:
        raise ValueError("minimum_samples must be a positive integer")

    items = list(pairs)
    for pair in items:
        _validate_v05_pair_semantics(pair)
    base = summarize_v04(
        items,
        minimum_savings_margin=minimum_cost_savings_margin,
        minimum_samples=minimum_samples,
    )
    normalized = {} if normalized_measurements is None else dict(normalized_measurements)
    expected_run_ids = {
        run_id
        for pair in items
        for run_id in (pair.direct.run_id, pair.dreamteam.run_id)
    }
    unknown_run_ids = set(normalized) - expected_run_ids
    if unknown_run_ids:
        raise ValueError(
            f"normalized measurements contain unknown run ids: {sorted(unknown_run_ids)}"
        )

    quality_pairs = [pair for pair in items if pair.quality_parity]
    total_values: list[Decimal] = []
    main_values: list[Decimal] = []
    payload_values: list[Decimal] = []
    handoff_values: list[Decimal] = []
    buckets: dict[tuple[str, ...], list[tuple[Decimal, Decimal]]] = {}
    normalized_complete = bool(items)

    for pair in quality_pairs:
        total_savings, main_savings = _pair_token_metrics(pair)
        total_values.append(total_savings)
        main_values.append(main_savings)
        buckets.setdefault(pair.bucket_key, []).append((total_savings, main_savings))

        direct_measurement = normalized.get(pair.direct.run_id)
        dreamteam_measurement = normalized.get(pair.dreamteam.run_id)
        if direct_measurement is None or dreamteam_measurement is None:
            normalized_complete = False
            continue
        if direct_measurement.handoff_tokens != 0:
            raise ValueError("direct benchmark arm may not report DreamTeam handoff tokens")
        dreamteam_total = Decimal(pair.dreamteam.main_tokens + pair.dreamteam.worker_tokens)
        if Decimal(dreamteam_measurement.handoff_tokens) > dreamteam_total:
            raise ValueError("DreamTeam handoff tokens cannot exceed total active tokens")
        if direct_measurement.normalized_payload_bytes > 0:
            payload_values.append(
                savings_ratio(
                    direct_measurement.normalized_payload_bytes,
                    dreamteam_measurement.normalized_payload_bytes,
                )
            )
        handoff_values.append(
            Decimal("0")
            if dreamteam_total == 0
            else Decimal(dreamteam_measurement.handoff_tokens) / dreamteam_total
        )

    total_median, total_mean, total_p10 = _distribution(total_values)
    main_median, main_mean, main_p10 = _distribution(main_values)
    payload_median, payload_mean, payload_p10 = _distribution(payload_values)
    handoff_median, handoff_mean, handoff_p10 = _distribution(handoff_values)

    bucket_results: dict[str, dict[str, object]] = {}
    token_buckets_publishable = bool(buckets)
    for key, values in sorted(buckets.items()):
        totals = [item[0] for item in values]
        mains = [item[1] for item in values]
        b_total_median, _, b_total_p10 = _distribution(totals)
        b_main_median, _, b_main_p10 = _distribution(mains)
        publishable = (
            len(values) >= minimum_samples
            and b_total_median >= minimum_total_token_savings
            and b_total_p10 > 0
            and b_main_median >= minimum_main_token_savings
            and b_main_p10 > 0
        )
        token_buckets_publishable = token_buckets_publishable and publishable
        bucket_results["|".join(key)] = {
            "samples": len(values),
            "median_total_token_savings_ratio": float(b_total_median),
            "p10_total_token_savings_ratio": float(b_total_p10),
            "median_main_token_savings_ratio": float(b_main_median),
            "p10_main_token_savings_ratio": float(b_main_p10),
            "token_claim_allowed": publishable,
        }

    quality_complete = bool(items) and len(quality_pairs) == len(items)
    token_claim = (
        quality_complete
        and bool(total_values)
        and token_buckets_publishable
        and total_median >= minimum_total_token_savings
        and total_p10 > 0
        and main_median >= minimum_main_token_savings
        and main_p10 > 0
    )
    payload_claim = (
        quality_complete
        and normalized_complete
        and len(payload_values) == len(items)
        and bool(payload_values)
        and payload_p10 > 0
    )
    cost_claim = bool(base["publication_claim_allowed"])

    reasons = list(base.get("reasons", []))
    if not token_claim:
        reasons.append("token efficiency gates are not publishable")
    if not normalized_complete:
        reasons.append("normalized payload measurements are incomplete")

    return {
        **base,
        "benchmark_version": "0.5",
        "median_total_token_savings_ratio": float(total_median),
        "mean_total_token_savings_ratio": float(total_mean),
        "p10_total_token_savings_ratio": float(total_p10),
        "median_main_token_savings_ratio": float(main_median),
        "mean_main_token_savings_ratio": float(main_mean),
        "p10_main_token_savings_ratio": float(main_p10),
        "median_payload_savings_ratio": float(payload_median),
        "mean_payload_savings_ratio": float(payload_mean),
        "p10_payload_savings_ratio": float(payload_p10),
        "median_handoff_overhead_ratio": float(handoff_median),
        "mean_handoff_overhead_ratio": float(handoff_mean),
        "p10_handoff_overhead_ratio": float(handoff_p10),
        "normalized_measurement_complete": normalized_complete,
        "cost_claim_allowed_v05": cost_claim,
        "token_claim_allowed": token_claim,
        "payload_claim_allowed": payload_claim,
        "efficiency_claim_allowed": cost_claim and token_claim,
        "token_buckets": bucket_results,
        "reasons_v05": list(dict.fromkeys(reasons)),
    }
