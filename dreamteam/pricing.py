"""Versioned, immutable API-equivalent USD accounting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping

MTOK = Decimal("1000000")
MODEL_CATALOG_ID = "claude-model-aliases-v1"
MODEL_ALIASES: Mapping[str, str] = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-4-8",
}


class ExecutionLane(str, Enum):
    INTERACTIVE = "interactive"
    BATCH = "batch"


@dataclass(frozen=True)
class ModelPrice:
    input_per_mtok: Decimal
    output_per_mtok: Decimal
    cache_read_multiplier: Decimal = Decimal("0.10")
    cache_write_5m_multiplier: Decimal = Decimal("1.25")
    cache_write_1h_multiplier: Decimal = Decimal("2.00")
    batch_multiplier: Decimal = Decimal("0.50")


_INTRO = {
    "claude-haiku-4-5": ModelPrice(Decimal("1"), Decimal("5")),
    "claude-sonnet-5": ModelPrice(Decimal("2"), Decimal("10")),
    "claude-opus-4-8": ModelPrice(Decimal("5"), Decimal("25")),
}
_STANDARD = {
    "claude-haiku-4-5": ModelPrice(Decimal("1"), Decimal("5")),
    "claude-sonnet-5": ModelPrice(Decimal("3"), Decimal("15")),
    "claude-opus-4-8": ModelPrice(Decimal("5"), Decimal("25")),
}
PRICE_CATALOGS: Mapping[date, Mapping[str, ModelPrice]] = {
    date(2026, 7, 17): _INTRO,
    date(2026, 8, 31): _INTRO,
    date(2026, 9, 1): _STANDARD,
}


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_5m_tokens: int = 0
    cache_write_1h_tokens: int = 0
    requests: int = 1

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.requests < 1:
            raise ValueError("requests must be at least one")

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_5m_tokens
            + self.cache_write_1h_tokens
        )


@dataclass(frozen=True)
class CostBreakdown:
    input_usd: Decimal
    output_usd: Decimal
    cache_read_usd: Decimal
    cache_write_usd: Decimal
    total_usd: Decimal
    model: str
    lane: ExecutionLane
    pricing_catalog_id: str


def resolve_model(model: str, *, inherited: str | None = None) -> str:
    if not isinstance(model, str) or not model:
        raise TypeError("model must be a non-empty string")
    if model == "inherit":
        if inherited is None:
            raise ValueError("inherit requires an explicit inherited model")
        model = inherited
    return MODEL_ALIASES.get(model, model)


class PriceBook:
    """Immutable pricing snapshot used for routing and benchmark reproducibility."""

    def __init__(self, as_of: date) -> None:
        if not isinstance(as_of, date):
            raise TypeError("as_of must be a date")
        if as_of not in PRICE_CATALOGS:
            supported = ", ".join(item.isoformat() for item in sorted(PRICE_CATALOGS))
            raise ValueError(f"unsupported pricing snapshot {as_of.isoformat()}; supported: {supported}")
        self.as_of = as_of

    @classmethod
    def from_catalog_id(cls, catalog_id: str) -> "PriceBook":
        prefix = "anthropic-api-"
        if not isinstance(catalog_id, str) or not catalog_id.startswith(prefix):
            raise ValueError("unsupported pricing catalog id")
        try:
            return cls(date.fromisoformat(catalog_id[len(prefix) :]))
        except ValueError as exc:
            raise ValueError("invalid or unsupported pricing catalog date") from exc

    @property
    def catalog_id(self) -> str:
        return f"anthropic-api-{self.as_of.isoformat()}"

    @property
    def prices(self) -> Mapping[str, ModelPrice]:
        return PRICE_CATALOGS[self.as_of]

    @property
    def catalog_hash(self) -> str:
        payload = {
            model: {
                "input_per_mtok": str(price.input_per_mtok),
                "output_per_mtok": str(price.output_per_mtok),
                "cache_read_multiplier": str(price.cache_read_multiplier),
                "cache_write_5m_multiplier": str(price.cache_write_5m_multiplier),
                "cache_write_1h_multiplier": str(price.cache_write_1h_multiplier),
                "batch_multiplier": str(price.batch_multiplier),
            }
            for model, price in sorted(self.prices.items())
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + sha256(encoded).hexdigest()

    def get(self, model: str) -> ModelPrice:
        resolved = resolve_model(model)
        try:
            return self.prices[resolved]
        except KeyError as exc:
            raise KeyError(f"unknown pricing model: {resolved}") from exc


def _usd(tokens: int, per_mtok: Decimal) -> Decimal:
    return Decimal(tokens) * per_mtok / MTOK


def estimate_cost(
    model: str,
    usage: TokenUsage,
    *,
    price_book: PriceBook,
    lane: ExecutionLane = ExecutionLane.INTERACTIVE,
) -> CostBreakdown:
    if not isinstance(lane, ExecutionLane):
        lane = ExecutionLane(lane)
    resolved = resolve_model(model)
    price = price_book.get(resolved)
    multiplier = price.batch_multiplier if lane is ExecutionLane.BATCH else Decimal("1")
    input_usd = _usd(usage.input_tokens, price.input_per_mtok) * multiplier
    output_usd = _usd(usage.output_tokens, price.output_per_mtok) * multiplier
    cache_read_usd = _usd(
        usage.cache_read_tokens,
        price.input_per_mtok * price.cache_read_multiplier,
    ) * multiplier
    cache_write_usd = (
        _usd(usage.cache_write_5m_tokens, price.input_per_mtok * price.cache_write_5m_multiplier)
        + _usd(usage.cache_write_1h_tokens, price.input_per_mtok * price.cache_write_1h_multiplier)
    ) * multiplier
    total = input_usd + output_usd + cache_read_usd + cache_write_usd
    return CostBreakdown(
        input_usd=input_usd,
        output_usd=output_usd,
        cache_read_usd=cache_read_usd,
        cache_write_usd=cache_write_usd,
        total_usd=total,
        model=resolved,
        lane=lane,
        pricing_catalog_id=price_book.catalog_id,
    )
