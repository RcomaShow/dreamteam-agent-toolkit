import unittest
from decimal import Decimal

from dreamteam.config import RuntimeConfig, Topology
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, Route, RouteRequest, TaskKind
from dreamteam.routing_v05 import V05RoutingPolicy, choose_route_v05


def cfg():
    return RuntimeConfig.from_mapping(
        {
            "version": 2,
            "topology": Topology.LEAN.value,
            "pricingAsOf": "2026-07-17",
            "routing": {
                "minimumSavingsMargin": 0.30,
                "maxEscalationProbability": 0.25,
                "maxMainRereadRatio": 0.35,
                "minSamplesForEnforcement": 20,
                "allowClosedContextBatch": False,
                "allowParallelIndependent": False,
            },
            "budgets": {
                "maxRunUsd": 10,
                "maxActiveWorkers": 1,
                "maxRetries": 1,
                "maxWorkerTurns": 10,
            },
            "verification": {
                "requireIndependentWriterReview": True,
                "requireAnchorValidation": True,
            },
            "telemetry": {
                "enabled": False,
                "storeSourceContent": False,
                "ledger": "off",
                "enforcement": "advisory",
            },
        }
    )


def discovery(**overrides):
    values = dict(
        criticality=Criticality.M0,
        task_kind=TaskKind.DISCOVERY,
        direct_usage=TokenUsage(input_tokens=100_000, output_tokens=2_000),
        worker_usage=TokenUsage(input_tokens=50_000, output_tokens=500),
        executive_usage=TokenUsage(),
        retry_probability=Decimal("0.02"),
        escalation_probability=Decimal("0.02"),
        calibration_samples=20,
    )
    values.update(overrides)
    return RouteRequest(**values)


class RoutingV05Tests(unittest.TestCase):
    def test_lean_delegation_requires_executive_forecast(self):
        result = choose_route_v05(discovery(), config=cfg())
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn("LEAN_EXECUTIVE_USAGE_REQUIRED", result.reason_codes)

    def test_lean_rejects_non_sonnet_executive_model(self):
        mapping = cfg().effective_mapping()
        mapping["models"]["executive"] = "opus"
        invalid_topology = RuntimeConfig.from_mapping(mapping)
        result = choose_route_v05(
            discovery(executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500)),
            config=invalid_topology,
        )
        self.assertEqual(result.selected_route, Route.BLOCKED)
        self.assertEqual(result.reason_codes, ("LEAN_EXECUTIVE_MODEL_MUST_BE_SONNET",))
        self.assertFalse(result.cost_gate_pass)

    def test_lean_executive_overhead_is_accounted(self):
        result = choose_route_v05(
            discovery(executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500)),
            config=cfg(),
        )
        self.assertEqual(result.selected_route, Route.HAIKU_DISCOVERY)
        self.assertGreater(result.lean_executive_overhead_usd, Decimal("0"))
        self.assertIn("LEAN_EXECUTIVE_OVERHEAD_ACCOUNTED", result.reason_codes)
        self.assertIsNotNone(result.efficiency)
        self.assertFalse(result.empirical_claim_allowed)

    def test_executive_overhead_can_reverse_a_legacy_cost_decision(self):
        request = discovery(
            task_kind=TaskKind.IMPLEMENTATION,
            executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500),
            verifier_usage=TokenUsage(input_tokens=20_000, output_tokens=5_000),
            independent_verifier_available=True,
        )
        result = choose_route_v05(request, config=cfg())
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn(
            "LEAN_EXECUTIVE_OVERHEAD_MARGIN_NOT_CLEARED", result.reason_codes
        )
        self.assertFalse(result.cost_gate_pass)

    def test_token_gates_are_shadow_only_by_default(self):
        request = discovery(
            executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500)
        )
        result = choose_route_v05(
            request,
            config=cfg(),
            policy=V05RoutingPolicy(
                minimum_total_token_savings=Decimal("0.90"),
                minimum_main_token_savings=Decimal("0.90"),
                enforce_token_gates=False,
            ),
        )
        self.assertEqual(result.selected_route, Route.HAIKU_DISCOVERY)
        self.assertFalse(result.token_gate_pass)
        self.assertFalse(result.token_gates_enforced)

    def test_token_gates_can_be_enforced_explicitly(self):
        request = discovery(
            executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500)
        )
        result = choose_route_v05(
            request,
            config=cfg(),
            policy=V05RoutingPolicy(
                minimum_total_token_savings=Decimal("0.90"),
                minimum_main_token_savings=Decimal("0.90"),
                enforce_token_gates=True,
            ),
        )
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn("V05_TOKEN_SAVINGS_GATE_NOT_CLEARED", result.reason_codes)

    def test_mapping_separates_cost_and_token_forecasts(self):
        result = choose_route_v05(
            discovery(executive_usage=TokenUsage(input_tokens=10_000, output_tokens=500)),
            config=cfg(),
        )
        payload = result.to_mapping()
        self.assertEqual(payload["router_version"], "0.5")
        self.assertIn("cost_savings_ratio", payload)
        self.assertIn("token_forecast", payload)
        self.assertIn("total_token_savings_ratio", payload["token_forecast"])
        self.assertIn("main_token_savings_ratio", payload["token_forecast"])


if __name__ == "__main__":
    unittest.main()
