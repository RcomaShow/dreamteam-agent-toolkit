import unittest
from decimal import Decimal

from dreamteam.measurement import EfficiencyGate, EfficiencyMetrics, savings_ratio


def metrics(**overrides):
    values = dict(
        direct_cost_usd=Decimal("1"),
        candidate_cost_usd=Decimal("0.5"),
        direct_total_tokens=Decimal("100"),
        candidate_total_tokens=Decimal("50"),
        direct_main_tokens=Decimal("100"),
        candidate_main_tokens=Decimal("20"),
    )
    values.update(overrides)
    return EfficiencyMetrics(**values)


class MeasurementV05Tests(unittest.TestCase):
    def test_cost_and_token_savings_are_independent(self):
        result = metrics(candidate_total_tokens=Decimal("120"))
        self.assertEqual(result.cost_savings_ratio, Decimal("0.5"))
        self.assertEqual(result.total_token_savings_ratio, Decimal("-0.2"))
        self.assertEqual(result.main_token_savings_ratio, Decimal("0.8"))

    def test_payload_and_handoff_metrics_are_normalized_separately(self):
        result = metrics(
            candidate_total_tokens=Decimal("80"),
            candidate_main_tokens=Decimal("40"),
            direct_payload_bytes=1000,
            candidate_payload_bytes=600,
            handoff_tokens=Decimal("8"),
        )
        self.assertEqual(result.payload_savings_ratio, Decimal("0.4"))
        self.assertEqual(result.handoff_overhead_ratio, Decimal("0.1"))

    def test_gate_rejects_cheaper_but_token_heavier_candidate(self):
        result = EfficiencyGate(
            minimum_cost_savings=Decimal("0.20"),
            minimum_total_token_savings=Decimal("0.05"),
            minimum_main_token_savings=Decimal("0.20"),
        ).evaluate(
            metrics(
                candidate_total_tokens=Decimal("110"),
                candidate_main_tokens=Decimal("30"),
                quality_parity=True,
            )
        )
        self.assertFalse(result.passed)
        self.assertIn("TOTAL_TOKEN_SAVINGS_GATE_FAILED", result.reason_codes)

    def test_unmeasured_quality_parity_fails_closed_by_default(self):
        result = EfficiencyGate().evaluate(metrics())
        self.assertFalse(result.passed)
        self.assertIn("QUALITY_PARITY_REQUIRED", result.reason_codes)

    def test_explicit_quality_parity_can_pass(self):
        result = EfficiencyGate(
            minimum_cost_savings=Decimal("0.20"),
            minimum_total_token_savings=Decimal("0.20"),
            minimum_main_token_savings=Decimal("0.20"),
        ).evaluate(metrics(quality_parity=True))
        self.assertTrue(result.passed)
        self.assertEqual(result.reason_codes, ())

    def test_zero_baseline_never_creates_fake_savings(self):
        self.assertEqual(savings_ratio(0, 0), Decimal("0"))
        self.assertEqual(savings_ratio(0, 10), Decimal("0"))

    def test_main_tokens_cannot_exceed_total(self):
        with self.assertRaises(ValueError):
            metrics(
                direct_total_tokens=Decimal("10"),
                candidate_total_tokens=Decimal("10"),
                direct_main_tokens=Decimal("11"),
                candidate_main_tokens=Decimal("10"),
            )


if __name__ == "__main__":
    unittest.main()
