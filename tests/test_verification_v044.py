from datetime import date
import random
import string
import unittest

from dreamteam.benchmark import load_results
from dreamteam.pricing import PriceBook, TokenUsage, estimate_cost
from dreamteam.protocol import ProtocolError, escape_field, split_record


def model_usage(model: str, tokens: int = 1000):
    return {
        "model": model,
        "effort": "medium",
        "input_tokens": tokens,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 0,
        "lane": "interactive",
    }


def price(model: str, tokens: int = 1000) -> str:
    return str(
        estimate_cost(
            model,
            TokenUsage(input_tokens=tokens),
            price_book=PriceBook(date(2026, 7, 17)),
        ).total_usd
    )


def row(arm: str, model: str, topology: str, route: str, role: str):
    direct = arm == "direct"
    return {
        "run_id": f"{arm}-{model}",
        "pair_id": "p",
        "task_id": "t",
        "replicate_id": "1",
        "arm": arm,
        "repo_commit": "abc",
        "task_archetype": "discovery",
        "criticality": "M0",
        "task_kind": "discovery",
        "size_band": "small",
        "topology": topology,
        "route": route,
        "agent_role": role,
        "cache_cohort": "cold",
        "arm_order": 0 if direct else 1,
        "quality_oracle_id": "oracle:sha256:test",
        "quality_pass": True,
        "billed_usd": price(model),
        "api_equivalent_usd": price(model),
        "main_tokens": 1000 if direct else 0,
        "worker_tokens": 0 if direct else 1000,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "reread_bytes": 0,
        "retries": 0,
        "escalations": 0,
        "failed_attempts": 0,
        "elapsed_seconds": 1.0,
        "pricing_catalog_id": "anthropic-api-2026-07-17",
        "adapter_version": "0.4.4",
        "config_hash": "cfg",
        "environment_id": "env",
        "timeout_seconds": 60.0,
        "model_usage": [model_usage(model)],
    }


class VerificationV044Tests(unittest.TestCase):
    def test_direct_arm_rejects_non_sonnet_model(self):
        with self.assertRaises(ValueError):
            load_results([row("direct", "haiku", "lean", "MAIN_DIRECT", "direct-sonnet")])

    def test_opus_sonnet_rejects_hidden_haiku(self):
        item = row("dreamteam", "haiku", "opus-sonnet", "SONNET_LEAD", "execution-sonnet-lead")
        with self.assertRaises(ValueError):
            load_results([item])

    def test_protocol_field_round_trip_for_seeded_adversarial_values(self):
        rng = random.Random(404)
        alphabet = string.ascii_letters + string.digits + "|\\\\\n\r -_."
        for _ in range(500):
            value = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
            self.assertEqual(split_record("K|" + escape_field(value)), ["K", value])

    def test_protocol_rejects_unicode_line_separators(self):
        from dreamteam.protocol import parse

        for separator in ("\x85", "\u2028", "\u2029"):
            with self.assertRaises(ProtocolError):
                parse("DCP|2" + separator + "RUN|r")


if __name__ == "__main__":
    unittest.main()
