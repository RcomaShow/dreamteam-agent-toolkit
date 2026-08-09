from datetime import date
from decimal import Decimal
import unittest

from dreamteam.benchmark import load_results, pair_results
from dreamteam.benchmark_v05 import load_normalized_measurements, summarize_v05
from dreamteam.pricing import PriceBook, TokenUsage, estimate_cost


def usage(model, input_tokens, output_tokens):
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


def cost(model, input_tokens, output_tokens):
    return str(
        estimate_cost(
            model,
            TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            price_book=PriceBook(date(2026, 7, 17)),
        ).total_usd
    )


def row(arm, *, input_tokens=None, output_tokens=None, pair="p"):
    direct = arm == "direct"
    model = "sonnet" if direct else "haiku"
    input_tokens = (100_000 if direct else 20_000) if input_tokens is None else input_tokens
    output_tokens = (10_000 if direct else 1_000) if output_tokens is None else output_tokens
    return {
        "run_id": f"{pair}-{arm}",
        "pair_id": pair,
        "task_id": "t",
        "replicate_id": "1",
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
        "quality_pass": True,
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
        "adapter_version": "0.5.0",
        "config_hash": "cfg",
        "environment_id": "ubuntu-python312",
        "timeout_seconds": 60.0,
        "model_usage": [usage(model, input_tokens, output_tokens)],
    }


def pairs(dream_input=20_000, dream_output=1_000):
    return pair_results(
        load_results(
            [
                row("direct"),
                row("dreamteam", input_tokens=dream_input, output_tokens=dream_output),
            ]
        )
    )


def measurements(*, direct_handoff=0, dream_handoff=1_000):
    return load_normalized_measurements(
        [
            {
                "run_id": "p-direct",
                "normalized_payload_bytes": 10_000,
                "handoff_tokens": direct_handoff,
            },
            {
                "run_id": "p-dreamteam",
                "normalized_payload_bytes": 5_000,
                "handoff_tokens": dream_handoff,
            },
        ]
    )


class BenchmarkV05Tests(unittest.TestCase):
    def test_cost_token_and_payload_claims_are_separate(self):
        summary = summarize_v05(
            pairs(),
            normalized_measurements=measurements(),
            minimum_samples=1,
        )
        self.assertEqual(summary["benchmark_version"], "0.5")
        self.assertTrue(summary["cost_claim_allowed_v05"])
        self.assertTrue(summary["token_claim_allowed"])
        self.assertTrue(summary["payload_claim_allowed"])
        self.assertTrue(summary["efficiency_claim_allowed"])
        self.assertGreater(summary["median_total_token_savings_ratio"], 0)
        self.assertGreater(summary["median_main_token_savings_ratio"], 0)

    def test_cheaper_but_token_heavier_pair_cannot_claim_token_efficiency(self):
        summary = summarize_v05(
            pairs(dream_input=120_000, dream_output=1_000),
            minimum_samples=1,
        )
        self.assertTrue(summary["cost_claim_allowed_v05"])
        self.assertFalse(summary["token_claim_allowed"])
        self.assertFalse(summary["efficiency_claim_allowed"])
        self.assertLess(summary["median_total_token_savings_ratio"], 0)

    def test_missing_normalized_measurements_fail_closed_for_payload_claim(self):
        summary = summarize_v05(pairs(), minimum_samples=1)
        self.assertTrue(summary["token_claim_allowed"])
        self.assertFalse(summary["payload_claim_allowed"])
        self.assertFalse(summary["normalized_measurement_complete"])

    def test_direct_arm_cannot_report_dreamteam_handoff_tokens(self):
        with self.assertRaises(ValueError):
            summarize_v05(
                pairs(),
                normalized_measurements=measurements(direct_handoff=1),
                minimum_samples=1,
            )

    def test_handoff_tokens_cannot_exceed_dreamteam_total(self):
        with self.assertRaises(ValueError):
            summarize_v05(
                pairs(),
                normalized_measurements=measurements(dream_handoff=21_001),
                minimum_samples=1,
            )

    def test_normalized_measurements_reject_duplicates_and_unknown_fields(self):
        duplicate = [
            {"run_id": "x", "normalized_payload_bytes": 1, "handoff_tokens": 0},
            {"run_id": "x", "normalized_payload_bytes": 2, "handoff_tokens": 0},
        ]
        with self.assertRaises(ValueError):
            load_normalized_measurements(duplicate)
        with self.assertRaises(ValueError):
            load_normalized_measurements(
                [
                    {
                        "run_id": "x",
                        "normalized_payload_bytes": 1,
                        "handoff_tokens": 0,
                        "extra": 1,
                    }
                ]
            )

    def test_token_sample_gate_is_bucket_specific(self):
        summary = summarize_v05(pairs(), minimum_samples=2)
        self.assertFalse(summary["token_claim_allowed"])
        self.assertTrue(summary["token_buckets"])


if __name__ == "__main__":
    unittest.main()
