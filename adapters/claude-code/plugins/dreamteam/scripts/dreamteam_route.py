#!/usr/bin/env python3
"""Route a JSON request using the bundled DreamTeam runtime."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path
import sys

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))

from dreamteam.config import RuntimeCapabilities, RuntimeConfig
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, RouteRequest, TaskKind, choose_route


def _usage(value: dict[str, object] | None) -> TokenUsage:
    return TokenUsage(**(value or {}))


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
    request = RouteRequest(
        criticality=Criticality(data["criticality"]),
        task_kind=TaskKind(data["task_kind"]),
        direct_usage=_usage(data.get("direct_usage")),
        worker_usage=_usage(data.get("worker_usage")),
        lead_usage=_usage(data.get("lead_usage")),
        verifier_usage=_usage(data.get("verifier_usage")),
        executive_usage=_usage(data.get("executive_usage")),
        retry_probability=Decimal(str(data.get("retry_probability", 0))),
        escalation_probability=Decimal(str(data.get("escalation_probability", 0))),
        main_context_is_hot=bool(data.get("main_context_is_hot", False)),
        independent_verifier_available=bool(data.get("independent_verifier_available", False)),
        closed_context=bool(data.get("closed_context", False)),
        content_retention_confirmed=bool(data.get("content_retention_confirmed", False)),
        observed_main_reread_ratio=Decimal(str(data.get("observed_main_reread_ratio", 0))),
        calibration_samples=int(data.get("calibration_samples", 0)),
    )
    decision = choose_route(
        request,
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
    payload["candidate_delegated_usd"] = None if decision.candidate_delegated_usd is None else str(decision.candidate_delegated_usd)
    payload.pop("direct_forecast", None)
    payload.pop("candidate_forecast", None)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
