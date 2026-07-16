#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'dreamteam_runtime/benchmark.py')"
cat > 'dreamteam_runtime/benchmark.py' <<'__DT_V03_0033__'
"""Paired USD benchmark analysis for DreamTeam 0.3."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Iterable, Mapping, Sequence
import json
import math

from .pricing import PricingCatalog, PricingError, Usage


class BenchmarkError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class QualityResult:
    passed: bool
    score: float
    gates: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "QualityResult":
        score = float(value.get("score", 1.0 if value.get("passed") else 0.0))
        if not 0 <= score <= 1:
            raise BenchmarkError("quality score must be in [0, 1]")
        return cls(
            passed=bool(value.get("passed", False)),
            score=score,
            gates={str(k): str(v) for k, v in value.get("gates", {}).items()},
        )


@dataclass(frozen=True, slots=True)
class RunRecord:
    pair_id: str
    arm: str
    task_id: str
    task_class: str
    topology: str
    commit: str
    model_usage: Mapping[str, Usage]
    quality: QualityResult
    retries: int = 0
    escalations: int = 0
    elapsed_seconds: float | None = None
    cache_mode: str = "unspecified"
    billing_surface: str = "api-equivalent"
    batch_models: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RunRecord":
        required = {"pair_id", "arm", "task_id", "task_class", "topology", "commit", "model_usage", "quality"}
        missing = required - set(value)
        if missing:
            raise BenchmarkError(f"missing run fields: {sorted(missing)}")
        arm = str(value["arm"])
        if arm not in {"direct", "hybrid"}:
            raise BenchmarkError(f"unsupported arm {arm}")
        retries = int(value.get("retries", 0))
        escalations = int(value.get("escalations", 0))
        if retries < 0 or escalations < 0:
            raise BenchmarkError("retries and escalations must be non-negative")
        usage = {
            str(model): Usage.from_mapping(item)
            for model, item in value["model_usage"].items()
        }
        if not usage:
            raise BenchmarkError("model_usage cannot be empty")
        elapsed = value.get("elapsed_seconds")
        return cls(
            pair_id=str(value["pair_id"]),
            arm=arm,
            task_id=str(value["task_id"]),
            task_class=str(value["task_class"]),
            topology=str(value["topology"]),
            commit=str(value["commit"]),
            model_usage=usage,
            quality=QualityResult.from_mapping(value["quality"]),
            retries=retries,
            escalations=escalations,
            elapsed_seconds=float(elapsed) if elapsed is not None else None,
            cache_mode=str(value.get("cache_mode", "unspecified")),
            billing_surface=str(value.get("billing_surface", "api-equivalent")),
            batch_models=frozenset(str(item) for item in value.get("batch_models", [])),
            metadata=value.get("metadata", {}),
        )

    def cost(self, catalog: PricingCatalog) -> Decimal:
        return catalog.aggregate_cost(self.model_usage, batch_models=self.batch_models)


@dataclass(frozen=True, slots=True)
class PairResult:
    pair_id: str
    task_id: str
    task_class: str
    topology: str
    direct_usd: Decimal
    hybrid_usd: Decimal
    savings_usd: Decimal
    savings_ratio: float
    quality_parity: bool
    direct_quality: float
    hybrid_quality: float
    retries_delta: int
    escalation_count: int
    valid: bool
    invalid_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("direct_usd", "hybrid_usd", "savings_usd"):
            result[key] = str(result[key])
        return result


@dataclass(frozen=True, slots=True)
class AggregateResult:
    bucket: str
    samples: int
    valid_samples: int
    quality_parity_rate: float
    mean_savings_ratio: float
    lower_savings_bound: float
    upper_savings_bound: float
    total_direct_usd: Decimal
    total_hybrid_usd: Decimal
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["total_direct_usd"] = str(self.total_direct_usd)
        result["total_hybrid_usd"] = str(self.total_hybrid_usd)
        return result


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    catalog_id: str
    pairs: tuple[PairResult, ...]
    aggregates: tuple[AggregateResult, ...]
    valid: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "catalog_id": self.catalog_id,
            "valid": self.valid,
            "warnings": list(self.warnings),
            "pairs": [pair.to_dict() for pair in self.pairs],
            "aggregates": [aggregate.to_dict() for aggregate in self.aggregates],
        }

    def to_markdown(self) -> str:
        lines = [
            "# DreamTeam paired USD benchmark",
            "",
            f"Pricing catalog: `{self.catalog_id}`",
            f"Report validity: **{'VALID' if self.valid else 'INVALID'}**",
            "",
            "| Bucket | Valid pairs | Quality parity | Mean saving | 95% interval | Recommendation |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for aggregate in self.aggregates:
            lines.append(
                "| {bucket} | {valid}/{total} | {quality:.1%} | {mean:.1%} | {lower:.1%} … {upper:.1%} | {rec} |".format(
                    bucket=aggregate.bucket,
                    valid=aggregate.valid_samples,
                    total=aggregate.samples,
                    quality=aggregate.quality_parity_rate,
                    mean=aggregate.mean_savings_ratio,
                    lower=aggregate.lower_savings_bound,
                    upper=aggregate.upper_savings_bound,
                    rec=aggregate.recommendation,
                )
            )
        if self.warnings:
            lines += ["", "## Warnings", *[f"- {warning}" for warning in self.warnings]]
        lines += [
            "",
            "## Pair details",
            "",
            "| Pair | Class | Topology | Direct USD | Hybrid USD | Saving | Quality parity | Valid |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
        for pair in self.pairs:
            lines.append(
                f"| {pair.pair_id} | {pair.task_class} | {pair.topology} | "
                f"{pair.direct_usd:.8f} | {pair.hybrid_usd:.8f} | {pair.savings_ratio:.1%} | "
                f"{'yes' if pair.quality_parity else 'no'} | {'yes' if pair.valid else 'no'} |"
            )
        return "\n".join(lines) + "\n"


def load_run_records(path: str | Path) -> list[RunRecord]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise BenchmarkError(f"cannot read {source}: {exc}") from exc
    stripped = text.lstrip()
    values: list[Mapping[str, Any]]
    try:
        if stripped.startswith("["):
            loaded = json.loads(text)
            if not isinstance(loaded, list):
                raise BenchmarkError("benchmark JSON must be a list")
            values = loaded
        else:
            values = [json.loads(line) for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"invalid benchmark JSON: {exc}") from exc
    return [RunRecord.from_mapping(value) for value in values]


def _validate_models(record: RunRecord) -> list[str]:
    reasons: list[str] = []
    models = set(record.model_usage)
    if record.arm == "direct":
        expected = "claude-sonnet-5" if record.topology == "sonnet-haiku" else "claude-opus-4-8"
        if models != {expected}:
            reasons.append(f"DIRECT_MODEL_CONTAMINATION:{sorted(models)}")
    elif record.topology == "sonnet-haiku":
        allowed = {"claude-sonnet-5", "claude-haiku-4-5"}
        if not models <= allowed or "claude-sonnet-5" not in models:
            reasons.append(f"HYBRID_MODEL_MISMATCH:{sorted(models)}")
    elif record.topology == "opus-sonnet-haiku":
        allowed = {"claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"}
        if not models <= allowed or "claude-opus-4-8" not in models:
            reasons.append(f"TRI_TIER_MODEL_MISMATCH:{sorted(models)}")
    else:
        reasons.append(f"UNKNOWN_TOPOLOGY:{record.topology}")
    return reasons


def pair_records(
    records: Sequence[RunRecord],
    catalog: PricingCatalog,
    *,
    quality_tolerance: float = 0.0,
) -> list[PairResult]:
    grouped: dict[str, dict[str, RunRecord]] = {}
    for record in records:
        arms = grouped.setdefault(record.pair_id, {})
        if record.arm in arms:
            raise BenchmarkError(f"duplicate {record.arm} arm for {record.pair_id}")
        arms[record.arm] = record
    results: list[PairResult] = []
    for pair_id, arms in sorted(grouped.items()):
        if set(arms) != {"direct", "hybrid"}:
            missing = {"direct", "hybrid"} - set(arms)
            raise BenchmarkError(f"pair {pair_id} is missing arms {sorted(missing)}")
        direct = arms["direct"]
        hybrid = arms["hybrid"]
        reasons = _validate_models(direct) + _validate_models(hybrid)
        for field_name in ("task_id", "task_class", "topology", "commit", "cache_mode", "billing_surface"):
            if getattr(direct, field_name) != getattr(hybrid, field_name):
                reasons.append(f"PAIR_MISMATCH:{field_name}")
        if set(direct.quality.gates) != set(hybrid.quality.gates):
            reasons.append("ACCEPTANCE_GATE_MISMATCH")
        if direct.metadata.get("acceptance_hash") != hybrid.metadata.get("acceptance_hash"):
            reasons.append("ACCEPTANCE_HASH_MISMATCH")
        direct_cost = direct.cost(catalog)
        hybrid_cost = hybrid.cost(catalog)
        savings = direct_cost - hybrid_cost
        savings_ratio = float(savings / direct_cost) if direct_cost > 0 else float("-inf")
        parity = (
            direct.quality.passed
            and hybrid.quality.passed
            and hybrid.quality.score + quality_tolerance >= direct.quality.score
        )
        if not parity:
            reasons.append("QUALITY_PARITY_FAILED")
        results.append(
            PairResult(
                pair_id=pair_id,
                task_id=direct.task_id,
                task_class=direct.task_class,
                topology=direct.topology,
                direct_usd=direct_cost,
                hybrid_usd=hybrid_cost,
                savings_usd=savings,
                savings_ratio=savings_ratio,
                quality_parity=parity,
                direct_quality=direct.quality.score,
                hybrid_quality=hybrid.quality.score,
                retries_delta=hybrid.retries - direct.retries,
                escalation_count=hybrid.escalations,
                valid=not reasons,
                invalid_reasons=tuple(dict.fromkeys(reasons)),
            )
        )
    return results


def _confidence(values: Sequence[float], z: float = 1.96) -> tuple[float, float, float]:
    if not values:
        return 0.0, float("-inf"), float("inf")
    mean = fmean(values)
    if len(values) < 2:
        return mean, float("-inf"), float("inf")
    half = z * stdev(values) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def aggregate_pairs(
    pairs: Sequence[PairResult],
    *,
    minimum_samples: int = 5,
    minimum_savings_margin: float = 0.30,
    minimum_quality_parity_rate: float = 0.95,
) -> list[AggregateResult]:
    buckets: dict[str, list[PairResult]] = {}
    for pair in pairs:
        bucket = f"{pair.topology}:{pair.task_class}"
        buckets.setdefault(bucket, []).append(pair)
    results: list[AggregateResult] = []
    for bucket, values in sorted(buckets.items()):
        valid = [pair for pair in values if pair.valid]
        quality_rate = fmean(1.0 if pair.quality_parity else 0.0 for pair in values)
        mean, lower, upper = _confidence([pair.savings_ratio for pair in valid])
        direct_total = sum((pair.direct_usd for pair in valid), Decimal(0))
        hybrid_total = sum((pair.hybrid_usd for pair in valid), Decimal(0))
        if len(valid) < minimum_samples:
            recommendation = "INSUFFICIENT_DATA"
        elif quality_rate < minimum_quality_parity_rate:
            recommendation = "MAIN_DIRECT_QUALITY"
        elif upper < 0:
            recommendation = "MAIN_DIRECT_NEGATIVE_ROI"
        elif lower >= minimum_savings_margin:
            recommendation = "DELEGATE_ENFORCED"
        else:
            recommendation = "SHADOW"
        results.append(
            AggregateResult(
                bucket=bucket,
                samples=len(values),
                valid_samples=len(valid),
                quality_parity_rate=quality_rate,
                mean_savings_ratio=mean,
                lower_savings_bound=lower,
                upper_savings_bound=upper,
                total_direct_usd=direct_total,
                total_hybrid_usd=hybrid_total,
                recommendation=recommendation,
            )
        )
    return results


def analyze(
    records: Sequence[RunRecord],
    catalog: PricingCatalog,
    *,
    quality_tolerance: float = 0.0,
    minimum_samples: int = 5,
    minimum_savings_margin: float = 0.30,
    minimum_quality_parity_rate: float = 0.95,
) -> BenchmarkReport:
    pairs = pair_records(records, catalog, quality_tolerance=quality_tolerance)
    aggregates = aggregate_pairs(
        pairs,
        minimum_samples=minimum_samples,
        minimum_savings_margin=minimum_savings_margin,
        minimum_quality_parity_rate=minimum_quality_parity_rate,
    )
    warnings: list[str] = []
    billing = {record.billing_surface for record in records}
    if len(billing) > 1:
        warnings.append(f"mixed billing surfaces: {sorted(billing)}")
    if billing == {"subscription"}:
        warnings.append("subscription runs report API-equivalent USD, not invoice USD")
    if any(record.metadata.get("synthetic") for record in records):
        warnings.append("synthetic records are present; do not publish them as measured savings")
    valid = all(pair.valid for pair in pairs) and bool(pairs)
    return BenchmarkReport(
        catalog_id=catalog.catalog_id,
        pairs=tuple(pairs),
        aggregates=tuple(aggregates),
        valid=valid,
        warnings=tuple(warnings),
    )
__DT_V03_0033__
