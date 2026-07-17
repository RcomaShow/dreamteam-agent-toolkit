from datetime import date
from decimal import Decimal
import unittest

from dreamteam.benchmark import load_results, pair_results, summarize
from dreamteam.pricing import PriceBook, TokenUsage, estimate_cost


def _cost(model: str, input_tokens: int, output_tokens: int) -> str:
    return str(
        estimate_cost(
            model,
            TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            price_book=PriceBook(date(2026, 7, 17)),
        ).total_usd
    )


def row(arm, cost_multiplier=1, *, quality=True, pair="p", replicate="1"):
    direct = arm == "direct"
    model = "sonnet" if direct else "haiku"
    input_tokens = 100_000 if direct else max(1, int(20_000 * cost_multiplier))
    output_tokens = 10_000 if direct else max(1, int(1_000 * cost_multiplier))
    api_cost = _cost(model, input_tokens, output_tokens)
    return {
        "run_id": f"{pair}-{replicate}-{arm}",
        "pair_id": pair,
        "task_id": "t",
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
        "arm_order": 0 if direct else 1,
        "quality_oracle_id": "oracle",
        "quality_pass": quality,
        "billed_usd": api_cost,
        "api_equivalent_usd": api_cost,
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
        "environment_id": "env",
        "timeout_seconds": 60.0,
        "model_usage": [{
            "model": model,
            "effort": "medium",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": 0,
            "cache_write_5m_tokens": 0,
            "cache_write_1h_tokens": 0,
            "lane": "interactive",
        }],
    }


class BenchmarkCompatibilityTests(unittest.TestCase):
    def test_negative_savings_never_allows_cost_claim(self):
        summary = summarize(
            pair_results(load_results([row("direct"), row("dreamteam", 50)])),
            minimum_samples=1,
        )
        self.assertTrue(summary["quality_claim_allowed"])
        self.assertFalse(summary["positive_cost_claim_allowed"])
        self.assertFalse(summary["publication_claim_allowed"])

    def test_string_false_is_invalid(self):
        data = row("direct")
        data["quality_pass"] = "false"
        with self.assertRaises(TypeError):
            load_results([data])

    def test_duplicate_arm_is_invalid_and_replicates_are_preserved(self):
        with self.assertRaises(ValueError):
            pair_results(load_results([row("direct"), row("direct")]))
        results = [
            row("direct", replicate="1"),
            row("dreamteam", replicate="1"),
            row("direct", replicate="2"),
            row("dreamteam", replicate="2"),
        ]
        self.assertEqual(len(pair_results(load_results(results))), 2)

    def test_positive_below_margin_is_not_margin_claim(self):
        # A larger Haiku run remains cheaper but below the configured 90% margin.
        summary = summarize(
            pair_results(load_results([row("direct"), row("dreamteam", 5)])),
            minimum_savings_margin=Decimal("0.90"),
            minimum_samples=1,
        )
        self.assertTrue(summary["positive_cost_claim_allowed"])
        self.assertFalse(summary["margin_claim_allowed"])

    def test_insufficient_samples_blocks_publication(self):
        summary = summarize(
            pair_results(load_results([row("direct"), row("dreamteam")])),
            minimum_samples=20,
        )
        self.assertTrue(summary["margin_claim_allowed"])
        self.assertFalse(summary["publication_claim_allowed"])

    def test_zero_direct_cost_has_no_economic_claim(self):
        direct = row("direct")
        direct["model_usage"][0]["input_tokens"] = 0
        direct["model_usage"][0]["output_tokens"] = 0
        direct["api_equivalent_usd"] = "0"
        direct["billed_usd"] = "0"
        direct["main_tokens"] = 0
        dreamteam = row("dreamteam")
        summary = summarize(pair_results(load_results([direct, dreamteam])), minimum_samples=1)
        self.assertFalse(summary["positive_cost_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
