#!/usr/bin/env python3
"""Route requests through DreamTeam 0.5 measurement-first accounting."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any, Sequence

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))

from dreamteam.config import RuntimeCapabilities, RuntimeConfig
from dreamteam.operations import main as operations_main
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, RouteRequest, TaskKind
from dreamteam.routing_v05 import V05RoutingPolicy, choose_route_v05

_OPERATION_COMMANDS = {"doctor", "status"}


def _object(value: Any, name: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a JSON object")
    return value


def _usage(value: Any, name: str) -> TokenUsage:
    return TokenUsage(**_object(value, name))


def _json_bool(data: dict[str, object], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if type(value) is not bool:
        raise TypeError(f"{key} must be a JSON boolean")
    return value


def _json_int(data: dict[str, object], key: str, default: int = 0) -> int:
    value = data.get(key, default)
    if type(value) is not int or value < 0:
        raise TypeError(f"{key} must be a non-negative JSON integer")
    return value


def _json_decimal(data: dict[str, object], key: str, default: str = "0") -> Decimal:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError(f"{key} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{key} must be numeric") from exc
    if not result.is_finite():
        raise ValueError(f"{key} must be finite")
    return result


def _ratio_arg(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("ratio must be numeric") from exc
    if not result.is_finite() or not Decimal("0") <= result <= Decimal("1"):
        raise argparse.ArgumentTypeError("ratio must be between 0 and 1")
    return result


def parse_request(data: dict[str, object]) -> RouteRequest:
    allowed = {
        "criticality",
        "task_kind",
        "direct_usage",
        "worker_usage",
        "lead_usage",
        "verifier_usage",
        "executive_usage",
        "retry_probability",
        "escalation_probability",
        "main_context_is_hot",
        "independent_verifier_available",
        "closed_context",
        "content_retention_confirmed",
        "observed_main_reread_ratio",
        "calibration_samples",
        "requested_role",
        "requested_worker_role",
    }
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"request has unknown fields: {sorted(unknown)}")
    requested_role = data.get("requested_role")
    requested_worker_role = data.get("requested_worker_role")
    for name, value in (
        ("requested_role", requested_role),
        ("requested_worker_role", requested_worker_role),
    ):
        if value is not None and (not isinstance(value, str) or not value):
            raise TypeError(f"{name} must be a non-empty string")
    return RouteRequest(
        criticality=Criticality(data["criticality"]),
        task_kind=TaskKind(data["task_kind"]),
        direct_usage=_usage(data.get("direct_usage"), "direct_usage"),
        worker_usage=_usage(data.get("worker_usage"), "worker_usage"),
        lead_usage=_usage(data.get("lead_usage"), "lead_usage"),
        verifier_usage=_usage(data.get("verifier_usage"), "verifier_usage"),
        executive_usage=_usage(data.get("executive_usage"), "executive_usage"),
        retry_probability=_json_decimal(data, "retry_probability"),
        escalation_probability=_json_decimal(data, "escalation_probability"),
        main_context_is_hot=_json_bool(data, "main_context_is_hot"),
        independent_verifier_available=_json_bool(
            data, "independent_verifier_available"
        ),
        closed_context=_json_bool(data, "closed_context"),
        content_retention_confirmed=_json_bool(
            data, "content_retention_confirmed"
        ),
        observed_main_reread_ratio=_json_decimal(
            data, "observed_main_reread_ratio"
        ),
        calibration_samples=_json_int(data, "calibration_samples"),
        requested_role=requested_role,
        requested_worker_role=requested_worker_role,
    )


def route_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--batch-executor-available", action="store_true")
    parser.add_argument("--hooks-available", action="store_true")
    parser.add_argument("--resume-available", action="store_true")
    parser.add_argument(
        "--shadow", action="store_true", help="do not enforce minimum calibration samples"
    )
    parser.add_argument(
        "--enforce-token-gates",
        action="store_true",
        help="enforce the v0.5 token gates instead of reporting them in shadow mode",
    )
    parser.add_argument(
        "--minimum-total-token-savings",
        type=_ratio_arg,
        default=Decimal("0.05"),
    )
    parser.add_argument(
        "--minimum-main-token-savings",
        type=_ratio_arg,
        default=Decimal("0.15"),
    )
    parser.add_argument(
        "--allow-unaccounted-lean-executive",
        action="store_true",
        help="compatibility escape hatch; not valid for economic claims",
    )
    args = parser.parse_args(argv)
    data = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("request must be a JSON object")
    decision = choose_route_v05(
        parse_request(data),
        config=RuntimeConfig.from_file(args.config),
        capabilities=RuntimeCapabilities(
            batch_executor_available=args.batch_executor_available,
            hooks_available=args.hooks_available,
            resume_available=args.resume_available,
        ),
        enforce_calibration=not args.shadow,
        policy=V05RoutingPolicy(
            minimum_total_token_savings=args.minimum_total_token_savings,
            minimum_main_token_savings=args.minimum_main_token_savings,
            enforce_token_gates=args.enforce_token_gates,
            require_lean_executive_usage=not args.allow_unaccounted_lean_executive,
        ),
    )
    print(json.dumps(decision.to_mapping(), indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in _OPERATION_COMMANDS:
        return operations_main(arguments)
    return route_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
