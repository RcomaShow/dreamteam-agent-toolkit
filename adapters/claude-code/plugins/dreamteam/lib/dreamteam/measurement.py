"""Provider-neutral DreamTeam 0.5 efficiency metrics.

The 0.4 line optimized primarily for API-equivalent USD. 0.5 keeps cost as a
first-class metric but separates it from total token load, main-model token
load, normalized payload bytes, and handoff overhead so savings claims cannot
hide a token regression behind cheaper model pricing.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


def _decimal(value: int | Decimal, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise TypeError(f"{name} must be an int or Decimal")
    result = Decimal(value)
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def _ratio(value: Decimal, name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if not value.is_finite() or not Decimal("0") <= value <= Decimal("1"):
        raise ValueError(f"{name} must be finite and between 0 and 1")
    return value


def savings_ratio(baseline: int | Decimal, candidate: int | Decimal) -> Decimal:
    """Return conservative savings relative to baseline, or zero for zero baseline."""
    base = _decimal(baseline, "baseline")
    current = _decimal(candidate, "candidate")
    if base == 0:
        return Decimal("0")
    return (base - current) / base


@dataclass(frozen=True)
class EfficiencyMetrics:
    direct_cost_usd: Decimal
    candidate_cost_usd: Decimal
    direct_total_tokens: Decimal
    candidate_total_tokens: Decimal
    direct_main_tokens: Decimal
    candidate_main_tokens: Decimal
    direct_payload_bytes: int = 0
    candidate_payload_bytes: int = 0
    handoff_tokens: Decimal = Decimal("0")
    quality_parity: bool = True

    def __post_init__(self) -> None:
        for name in (
            "direct_cost_usd",
            "candidate_cost_usd",
            "direct_total_tokens",
            "candidate_total_tokens",
            "direct_main_tokens",
            "candidate_main_tokens",
            "handoff_tokens",
        ):
            _decimal(getattr(self, name), name)
        for name in ("direct_payload_bytes", "candidate_payload_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise TypeError(f"{name} must be a non-negative integer")
        if type(self.quality_parity) is not bool:
            raise TypeError("quality_parity must be a boolean")
        if self.direct_main_tokens > self.direct_total_tokens:
            raise ValueError("direct_main_tokens cannot exceed direct_total_tokens")
        if self.candidate_main_tokens > self.candidate_total_tokens:
            raise ValueError("candidate_main_tokens cannot exceed candidate_total_tokens")
        if self.handoff_tokens > self.candidate_total_tokens:
            raise ValueError("handoff_tokens cannot exceed candidate_total_tokens")

    @property
    def cost_savings_ratio(self) -> Decimal:
        return savings_ratio(self.direct_cost_usd, self.candidate_cost_usd)

    @property
    def total_token_savings_ratio(self) -> Decimal:
        return savings_ratio(self.direct_total_tokens, self.candidate_total_tokens)

    @property
    def main_token_savings_ratio(self) -> Decimal:
        return savings_ratio(self.direct_main_tokens, self.candidate_main_tokens)

    @property
    def payload_savings_ratio(self) -> Decimal | None:
        if self.direct_payload_bytes == 0:
            return None
        return savings_ratio(self.direct_payload_bytes, self.candidate_payload_bytes)

    @property
    def handoff_overhead_ratio(self) -> Decimal:
        if self.candidate_total_tokens == 0:
            return Decimal("0")
        return self.handoff_tokens / self.candidate_total_tokens


@dataclass(frozen=True)
class EfficiencyGate:
    minimum_cost_savings: Decimal = Decimal("0")
    minimum_total_token_savings: Decimal = Decimal("0")
    minimum_main_token_savings: Decimal = Decimal("0")
    maximum_handoff_overhead: Decimal = Decimal("1")
    require_payload_measurement: bool = False

    def __post_init__(self) -> None:
        for name in (
            "minimum_cost_savings",
            "minimum_total_token_savings",
            "minimum_main_token_savings",
            "maximum_handoff_overhead",
        ):
            _ratio(getattr(self, name), name)
        if type(self.require_payload_measurement) is not bool:
            raise TypeError("require_payload_measurement must be a boolean")

    def evaluate(self, metrics: EfficiencyMetrics) -> "EfficiencyGateResult":
        if not isinstance(metrics, EfficiencyMetrics):
            raise TypeError("metrics must be EfficiencyMetrics")
        reasons: list[str] = []
        if not metrics.quality_parity:
            reasons.append("QUALITY_PARITY_REQUIRED")
        if metrics.cost_savings_ratio < self.minimum_cost_savings:
            reasons.append("COST_SAVINGS_GATE_FAILED")
        if metrics.total_token_savings_ratio < self.minimum_total_token_savings:
            reasons.append("TOTAL_TOKEN_SAVINGS_GATE_FAILED")
        if metrics.main_token_savings_ratio < self.minimum_main_token_savings:
            reasons.append("MAIN_TOKEN_SAVINGS_GATE_FAILED")
        if metrics.handoff_overhead_ratio > self.maximum_handoff_overhead:
            reasons.append("HANDOFF_OVERHEAD_GATE_FAILED")
        payload = metrics.payload_savings_ratio
        if self.require_payload_measurement and payload is None:
            reasons.append("PAYLOAD_MEASUREMENT_REQUIRED")
        return EfficiencyGateResult(not reasons, tuple(reasons))


@dataclass(frozen=True)
class EfficiencyGateResult:
    passed: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.passed) is not bool:
            raise TypeError("passed must be a boolean")
        if self.passed and self.reason_codes:
            raise ValueError("passed result cannot contain failure reasons")
