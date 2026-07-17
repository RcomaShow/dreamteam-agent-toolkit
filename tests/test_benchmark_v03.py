from decimal import Decimal
import unittest

from dreamteam.benchmark import load_results, pair_results, summarize


def row(arm, cost, *, quality=True, pair="p", replicate="1"):
    return {
        "run_id": f"{pair}-{replicate}-{arm}", "pair_id": pair, "task_id": "t", "replicate_id": replicate,
        "arm": arm, "repo_commit": "abc", "task_archetype": "discovery", "topology": "lean",
        "route": "MAIN_DIRECT" if arm == "direct" else "HAIKU_DISCOVERY", "cache_cohort": "cold",
        "arm_order": 0 if arm == "direct" else 1, "quality_oracle_id": "oracle", "quality_pass": quality,
        "billed_usd": cost, "api_equivalent_usd": cost, "main_tokens": 10, "worker_tokens": 0,
        "cache_read_tokens": 0, "cache_write_tokens": 0, "reread_bytes": 0, "retries": 0,
        "escalations": 0, "failed_attempts": 0, "elapsed_seconds": 1.0,
        "pricing_catalog_id": "anthropic-api-2026-07-17", "model_usage": []
    }


class BenchmarkTests(unittest.TestCase):
    def test_negative_savings_never_allows_cost_claim(self):
        summary = summarize(pair_results(load_results([row("direct", 1), row("dreamteam", 2)])), minimum_samples=1)
        self.assertTrue(summary["quality_claim_allowed"])
        self.assertFalse(summary["positive_cost_claim_allowed"])
        self.assertFalse(summary["publication_claim_allowed"])

    def test_string_false_is_invalid(self):
        data = row("direct", 1); data["quality_pass"] = "false"
        with self.assertRaises(TypeError):
            load_results([data])

    def test_duplicate_arm_is_invalid_and_replicates_are_preserved(self):
        with self.assertRaises(ValueError):
            pair_results(load_results([row("direct", 1), row("direct", 1)]))
        results = [row("direct", 1, replicate="1"), row("dreamteam", 0.5, replicate="1"), row("direct", 1, replicate="2"), row("dreamteam", 0.5, replicate="2")]
        self.assertEqual(len(pair_results(load_results(results))), 2)

    def test_positive_below_margin_is_not_margin_claim(self):
        summary = summarize(pair_results(load_results([row("direct", 1), row("dreamteam", 0.8)])), minimum_samples=1)
        self.assertTrue(summary["positive_cost_claim_allowed"])
        self.assertFalse(summary["margin_claim_allowed"])

    def test_insufficient_samples_blocks_publication(self):
        summary = summarize(pair_results(load_results([row("direct", 1), row("dreamteam", 0.5)])), minimum_samples=20)
        self.assertTrue(summary["margin_claim_allowed"])
        self.assertFalse(summary["publication_claim_allowed"])

    def test_zero_direct_cost_has_no_economic_claim(self):
        summary = summarize(pair_results(load_results([row("direct", 0), row("dreamteam", 0)])), minimum_samples=1)
        self.assertFalse(summary["positive_cost_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
