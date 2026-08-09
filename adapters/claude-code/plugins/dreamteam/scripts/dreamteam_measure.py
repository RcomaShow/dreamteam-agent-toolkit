#!/usr/bin/env python3
"""Run the non-spending DreamTeam 0.5 benchmark summary from the plugin."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))
from dreamteam.benchmark import load_results, pair_results
from dreamteam.benchmark_v05 import load_normalized_measurements, summarize_v05


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, nargs="?")
    parser.add_argument("--normalized-measurements", type=Path)
    parser.add_argument("--minimum-savings-margin", type=Decimal, default=Decimal("0.30"))
    parser.add_argument("--minimum-total-token-savings", type=Decimal, default=Decimal("0.05"))
    parser.add_argument("--minimum-main-token-savings", type=Decimal, default=Decimal("0.15"))
    parser.add_argument("--minimum-samples", type=int, default=20)
    args = parser.parse_args()
    if args.results is None:
        print("preflight: paid inference disabled")
        return 0
    data = json.loads(args.results.read_text(encoding="utf-8"))
    normalized = None
    if args.normalized_measurements is not None:
        normalized = load_normalized_measurements(
            json.loads(args.normalized_measurements.read_text(encoding="utf-8"))
        )
    result = summarize_v05(
        pair_results(load_results(data)),
        normalized_measurements=normalized,
        minimum_cost_savings_margin=args.minimum_savings_margin,
        minimum_total_token_savings=args.minimum_total_token_savings,
        minimum_main_token_savings=args.minimum_main_token_savings,
        minimum_samples=args.minimum_samples,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
