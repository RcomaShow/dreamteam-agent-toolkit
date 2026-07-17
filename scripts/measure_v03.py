#!/usr/bin/env python3
"""Summarize paired benchmark JSON without performing provider inference."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dreamteam.benchmark import load_results, pair_results, require_paid_guard, summarize


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, nargs="?")
    parser.add_argument("--minimum-savings-margin", type=Decimal, default=Decimal("0.30"))
    parser.add_argument("--minimum-samples", type=int, default=20)
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.allow_paid:
        require_paid_guard(args.allow_paid, args.confirm)
        raise SystemExit("No provider executor is bundled; this flag only verifies the guard.")
    if args.results is None:
        print("preflight: paid inference disabled")
        return 0
    data = json.loads(args.results.read_text(encoding="utf-8"))
    result = summarize(
        pair_results(load_results(data)),
        minimum_savings_margin=args.minimum_savings_margin,
        minimum_samples=args.minimum_samples,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
