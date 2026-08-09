import unittest
from decimal import Decimal

from dreamteam.measurement import EfficiencyGate, EfficiencyMetrics, savings_ratio


class MeasurementV05Tests(unittest.TestCase):
    def test_cost_and_token_savings_are_independent(self):
        metrics = EfficiencyMetrics(
            direct_cost_usd=Decimal("1.00"),
            candidate_cost_usd=Decimal("0.50"),
            direct_total_tokens=Decimal("100"),
            candidate_total_tokens=Decimal("120"),
            direct_main_tokens=Decimal("100"),
            candidate_main_tokens=Decimal("20"),
        )
        self.assertEqual(metrics.cost_savings_ratio, Decimal("0.5"))
        self.assertEqual(metrics.total_token_savings_ratio, Decimal("-0.2"))
        self.assertEqual(metrics.main_token_savings_ratio, Decimal("0.8"))

    def test_payload_and_handoff_metrics_are_normalized_separately(self):
        metrics = EfficiencyMetrics(
            direct_cost_usd=Decimal("1"),
            candidate_cost_usd=Decimal("0.5"),
            direct_total_tokens=Decimal("100"),
            candidate_total_tokens=Decimal("80"),
            direct_main_tokens=Decimal("100"),
            candidate_main_tokens=Decimal("40"),
            direct_payload_bytes=1000,
            candidate_payload_bytes=600,
            handoff_tokens=Decimal("8"),
        )
        self.assertEqual(metrics.payload_savings_ratio, Decimal("0.4"))
        self.assertEqual(metrics.handoff_overhead_ratio, Decimal("0.1"))

    def test_gate_rejects_cheaper_but_token_heavier_candidate(self):
        metrics = EfficiencyMetrics(
            direct_cost_usd=Decimal("1"),
            candidate_cost_usd=Decimal("0.5"),
            direct_total_tokens=Decimal("100"),
            candidate_total_tokens=Decimal("110"),
            direct_main_tokens=Decimal("100"),
            candidate_main_tokens=Decimal("30"),
        )
        result = EfficiencyGate(
            minimum_cost_savings=Decimal("0.20"),
            minimum_total_token_savings=Decimal("0.05"),
            minimum_main_token_savings=Decimal("0.20"),
        ).evaluate(metrics)
        self.assertFalse(result.passed)
        self.assertIn("TOTAL_TOKEN_SAVINGS_GATE_FAILED", result.reason_codes)

    def test_quality_parity_is_required_for_efficiency_claim(self):
        metrics = EfficiencyMetrics(
            direct_cost_usd=Decimal("1"),
            candidate_cost_usd=Decimal("0.5"),
            direct_total_tokens=Decimal("100"),
            candidate_total_tokens=Decimal("50"),
            direct_main_tokens=Decimal("100"),
            candidate_main_tokens=Decimal("20"),
            quality_parity=False,
        )
        result = EfficiencyGate().evaluate(metrics)
        self.assertFalse(result.passed)
        self.assertIn("QUALITY_PARITY_REQUIRED", result.reason_codes)

    def test_zero_baseline_never_creates_fake_savings(self):
        self.assertEqual(savings_ratio(0, 0), Decimal("0"))
        self.assertEqual(savings_ratio(0, 10), Decimal("0"))

    def test_main_tokens_cannot_exceed_total(self):
        with self.assertRaises(ValueError):
            EfficiencyMetrics(
                direct_cost_usd=Decimal("1"),
                candidate_cost_usd=Decimal("1"),
                direct_total_tokens=Decimal("10"),
                candidate_total_tokens=Decimal("10"),
                direct_main_tokens=Decimal("11"),
                candidate_main_tokens=Decimal("10"),
            )


if __name__ == "__main__":
    unittest.main()
