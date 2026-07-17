#!/usr/bin/env python3
"""Route a JSON request using the bundled DreamTeam runtime."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))

from dreamteam.config import RuntimeCapabilities, RuntimeConfig
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, RouteRequest, TaskKind, choose_route


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
    for name, value in (("requested_role", requested_role), ("requested_worker_role", requested_worker_role)):
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--batch-executor-available", action="store_true")
    parser.add_argument("--hooks-available", action="store_true")
    parser.add_argument("--resume-available", action="store_true")
    parser.add_argument("--shadow", action="store_true", help="do not enforce minimum calibration samples")
    args = parser.parse_args()
    data = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("request must be a JSON object")
    decision = choose_route(
        parse_request(data),
        config=RuntimeConfig.from_file(args.config),
        capabilities=RuntimeCapabilities(
            batch_executor_available=args.batch_executor_available,
            hooks_available=args.hooks_available,
            resume_available=args.resume_available,
        ),
        enforce_calibration=not args.shadow,
    )
    payload = asdict(decision)
    payload["selected_route"] = decision.selected_route.value
    payload["savings_ratio"] = str(decision.savings_ratio)
    payload["selected_route_usd"] = str(decision.selected_route_usd)
    payload["direct_baseline_usd"] = str(decision.direct_baseline_usd)
    payload["candidate_delegated_usd"] = (
        None
        if decision.candidate_delegated_usd is None
        else str(decision.candidate_delegated_usd)
    )
    payload.pop("direct_forecast", None)
    payload.pop("candidate_forecast", None)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
