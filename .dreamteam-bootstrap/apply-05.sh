#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'dreamteam_runtime/budget.py')"
cat > 'dreamteam_runtime/budget.py' <<'__DT_V03_0034__'
"""Thread-safe usage limits and USD reservations for an orchestration run."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from threading import RLock
from typing import Any, Mapping
import uuid

from .pricing import PricingCatalog, Usage


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BudgetLimits:
    max_usd: Decimal | None = None
    max_requests: int | None = 50
    max_tool_calls: int | None = 200
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_total_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.max_usd is not None and Decimal(self.max_usd) < 0:
            raise ValueError("max_usd must be non-negative")
        for name in (
            "max_requests",
            "max_tool_calls",
            "max_input_tokens",
            "max_output_tokens",
            "max_total_tokens",
        ):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ValueError(f"{name} must be positive or None")


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    spent_usd: Decimal
    reserved_usd: Decimal
    requests: int
    tool_calls: int
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["spent_usd"] = str(self.spent_usd)
        result["reserved_usd"] = str(self.reserved_usd)
        result["total_tokens"] = self.total_tokens
        return result


class BudgetState:
    """Atomic budget accounting for parallel work waves.

    Callers reserve the conservative upper-bound USD cost before dispatch.  A
    reservation is settled with actual usage or released when dispatch is cancelled.
    """

    def __init__(self, limits: BudgetLimits = BudgetLimits()) -> None:
        self.limits = limits
        self._spent_usd = Decimal(0)
        self._reservations: dict[str, Decimal] = {}
        self._requests = 0
        self._tool_calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._lock = RLock()

    def snapshot(self) -> BudgetSnapshot:
        with self._lock:
            return BudgetSnapshot(
                spent_usd=self._spent_usd,
                reserved_usd=sum(self._reservations.values(), Decimal(0)),
                requests=self._requests,
                tool_calls=self._tool_calls,
                input_tokens=self._input_tokens,
                output_tokens=self._output_tokens,
            )

    def _check(self, snapshot: BudgetSnapshot, *, next_request: bool = False) -> None:
        limits = self.limits
        if limits.max_usd is not None and snapshot.spent_usd + snapshot.reserved_usd > limits.max_usd:
            raise BudgetExceeded(
                f"USD budget exceeded: {snapshot.spent_usd + snapshot.reserved_usd} > {limits.max_usd}"
            )
        request_count = snapshot.requests + int(next_request)
        if limits.max_requests is not None and request_count > limits.max_requests:
            raise BudgetExceeded(f"request budget exceeded: {request_count} > {limits.max_requests}")
        if limits.max_tool_calls is not None and snapshot.tool_calls > limits.max_tool_calls:
            raise BudgetExceeded(f"tool-call budget exceeded: {snapshot.tool_calls} > {limits.max_tool_calls}")
        if limits.max_input_tokens is not None and snapshot.input_tokens > limits.max_input_tokens:
            raise BudgetExceeded(f"input-token budget exceeded: {snapshot.input_tokens} > {limits.max_input_tokens}")
        if limits.max_output_tokens is not None and snapshot.output_tokens > limits.max_output_tokens:
            raise BudgetExceeded(f"output-token budget exceeded: {snapshot.output_tokens} > {limits.max_output_tokens}")
        if limits.max_total_tokens is not None and snapshot.total_tokens > limits.max_total_tokens:
            raise BudgetExceeded(f"total-token budget exceeded: {snapshot.total_tokens} > {limits.max_total_tokens}")

    def check_before_request(self, *, estimated_usd: Decimal = Decimal(0)) -> None:
        with self._lock:
            current = self.snapshot()
            projected = BudgetSnapshot(
                spent_usd=current.spent_usd,
                reserved_usd=current.reserved_usd + estimated_usd,
                requests=current.requests,
                tool_calls=current.tool_calls,
                input_tokens=current.input_tokens,
                output_tokens=current.output_tokens,
            )
            self._check(projected, next_request=True)

    def reserve(self, estimated_usd: Decimal) -> str:
        estimated = Decimal(estimated_usd)
        if estimated < 0:
            raise ValueError("estimated_usd must be non-negative")
        with self._lock:
            self.check_before_request(estimated_usd=estimated)
            reservation_id = str(uuid.uuid4())
            self._reservations[reservation_id] = estimated
            return reservation_id

    def release(self, reservation_id: str) -> None:
        with self._lock:
            if reservation_id not in self._reservations:
                raise KeyError(reservation_id)
            del self._reservations[reservation_id]

    def settle(
        self,
        reservation_id: str,
        *,
        model: str,
        usage: Usage | Mapping[str, Any],
        catalog: PricingCatalog,
        batch: bool = False,
    ) -> Decimal:
        canonical = usage if isinstance(usage, Usage) else Usage.from_mapping(usage)
        actual = catalog.cost(model, canonical, batch=batch)
        with self._lock:
            if reservation_id not in self._reservations:
                raise KeyError(reservation_id)
            remaining_reserved = sum(
                (value for key, value in self._reservations.items() if key != reservation_id),
                Decimal(0),
            )
            projected = BudgetSnapshot(
                spent_usd=self._spent_usd + actual,
                reserved_usd=remaining_reserved,
                requests=self._requests + max(1, canonical.requests),
                tool_calls=self._tool_calls + canonical.tool_calls,
                input_tokens=self._input_tokens
                + canonical.input_tokens
                + canonical.cache_write_5m_tokens
                + canonical.cache_write_1h_tokens
                + canonical.cache_read_tokens,
                output_tokens=self._output_tokens + canonical.output_tokens,
            )
            self._check(projected)
            self._reservations.pop(reservation_id)
            self._spent_usd = projected.spent_usd
            self._requests = projected.requests
            self._tool_calls = projected.tool_calls
            self._input_tokens = projected.input_tokens
            self._output_tokens = projected.output_tokens
            return actual

    def record_tool_call(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be non-negative")
        with self._lock:
            projected = self.snapshot()
            projected = BudgetSnapshot(
                spent_usd=projected.spent_usd,
                reserved_usd=projected.reserved_usd,
                requests=projected.requests,
                tool_calls=projected.tool_calls + count,
                input_tokens=projected.input_tokens,
                output_tokens=projected.output_tokens,
            )
            self._check(projected)
            self._tool_calls = projected.tool_calls
__DT_V03_0034__
