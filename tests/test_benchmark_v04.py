from decimal import Decimal
import unittest

from dreamteam.benchmark import load_results, pair_results, summarize
from dreamteam.pricing import PriceBook, TokenUsage, estimate_cost
from datetime import date


def usage(model, input_tokens=100_000, output_tokens=10_000):
    return {
        "model": model,
        "effort": "medium",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": 0,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 0,
        "lane": "interactive",
    }


def cost(model, input_tokens=100_000, output_tokens=10_000):
    return str(
        estimate_cost(
            model,
            TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            price_book=PriceBook(date(2026, 7, 17)),
        ).total_usd
    )


def row(arm, model, *, pair="p", replicate="1", task="t", order=None, quality=True):
    direct = arm == "direct"
    input_tokens = 100_000 if direct else 20_000
    output_tokens = 10_000 if direct else 1_000
    return {
        "run_id": f"{pair}-{replicate}-{arm}",
        "pair_id": pair,
        "task_id": task,
        "replicate_id": replicate,
        "arm": arm,
        "repo_commit": "abc",
        "task_archetype": "discovery",
        "criticality": "M0",
        "task_kind": "discovery",
        "size_band": "medium",
        "topology": "lean",
        "route": "MAIN_DIRECT" if direct else "HAIKU_DISCOVERY",
        "agent_role": "direct-sonnet" if direct else "discovery-symbol-locator",
        "cache_cohort": "cold",
        "arm_order": (0 if direct else 1) if order is None else order,
        "quality_oracle_id": "oracle",
        "quality_pass": quality,
        "billed_usd": cost(model, input_tokens, output_tokens),
        "api_equivalent_usd": cost(model, input_tokens, output_tokens),
        "main_tokens": input_tokens + output_tokens if direct else 0,
        "worker_tokens": 0 if direct else input_tokens + output_tokens,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "reread_bytes": 0,
        "retries": 0,
        "escalations": 0,
        "failed_attempts": 0,
        "elapsed_seconds": 1.0,
        "pricing_catalog_id": "anthropic-api-2026-07-17",
        "adapter_version": "0.4.0",
        "config_hash": "cfg",
        "environment_id": "ubuntu-python312",
        "timeout_seconds": 60.0,
        "model_usage": [usage(model, input_tokens, output_tokens)],
    }


class BenchmarkV04Tests(unittest.TestCase):
    def test_cost_is_recomputed(self):
        data = row("direct", "sonnet")
        data["api_equivalent_usd"] = "999"
        with self.assertRaises(ValueError):
            load_results([data])

    def test_pair_task_mismatch_is_rejected(self):
        rows = [row("direct", "sonnet", task="a"), row("dreamteam", "haiku", task="b")]
        with self.assertRaises(ValueError):
            pair_results(load_results(rows))

    def test_arm_order_must_differ(self):
        rows = [row("direct", "sonnet", order=0), row("dreamteam", "haiku", order=0)]
        with self.assertRaises(ValueError):
            pair_results(load_results(rows))

    def test_bucket_sample_gate_is_fail_closed(self):
        pairs = pair_results(load_results([row("direct", "sonnet"), row("dreamteam", "haiku")]))
        summary = summarize(pairs, minimum_samples=20)
        self.assertTrue(summary["quality_claim_allowed"])
        self.assertFalse(summary["publication_claim_allowed"])
        self.assertTrue(summary["buckets"])

    def test_usage_aggregates_are_reconciled(self):
        data = row("direct", "sonnet")
        data["main_tokens"] += 1
        with self.assertRaises(ValueError):
            load_results([data])

    def test_pair_bucket_dimensions_must_match(self):
        direct = row("direct", "sonnet")
        delegated = row("dreamteam", "haiku")
        delegated["size_band"] = "large"
        with self.assertRaises(ValueError):
            pair_results(load_results([direct, delegated]))

    def test_summary_arguments_and_operational_metrics_are_strict(self):
        pairs = pair_results(
            load_results([row("direct", "sonnet"), row("dreamteam", "haiku")])
        )
        with self.assertRaises(ValueError):
            summarize(pairs, minimum_samples=0)
        with self.assertRaises(ValueError):
            summarize(pairs, minimum_savings_margin=Decimal("NaN"))
        summary = summarize(pairs, minimum_samples=1)
        self.assertEqual(summary["quality_failure_rate"], 0.0)
        self.assertIsNotNone(summary["dreamteam_api_cost_per_quality_pair"])
        self.assertEqual(summary["mean_direct_elapsed_seconds"], 1.0)
        self.assertEqual(summary["mean_dreamteam_elapsed_seconds"], 1.0)


if __name__ == "__main__":
    unittest.main()
