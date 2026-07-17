import unittest
from decimal import Decimal

from dreamteam.config import RuntimeCapabilities, RuntimeConfig, Topology
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, Route, RouteRequest, TaskKind, choose_route


def cfg(topology=Topology.LEAN, batch=False):
    data = {
        "version": 2,
        "topology": topology.value,
        "pricingAsOf": "2026-07-17",
        "routing": {
            "minimumSavingsMargin": 0.30,
            "maxEscalationProbability": 0.25,
            "maxMainRereadRatio": 0.35,
            "minSamplesForEnforcement": 20,
            "allowClosedContextBatch": batch,
            "allowParallelIndependent": False,
        },
        "budgets": {"maxRunUsd": 10, "maxActiveWorkers": 1, "maxRetries": 1, "maxWorkerTurns": 10},
        "verification": {"requireIndependentWriterReview": True, "requireAnchorValidation": True},
        "telemetry": {"storeSourceContent": False, "ledger": "off", "enforcement": "advisory"},
    }
    return RuntimeConfig.from_mapping(data)


def request(**overrides):
    values = dict(
        criticality=Criticality.M0,
        task_kind=TaskKind.DISCOVERY,
        direct_usage=TokenUsage(input_tokens=100_000, output_tokens=2_000),
        worker_usage=TokenUsage(input_tokens=100_000, output_tokens=500),
        lead_usage=TokenUsage(input_tokens=1_000, output_tokens=200),
        verifier_usage=TokenUsage(),
        executive_usage=TokenUsage(input_tokens=500, output_tokens=100),
        retry_probability=Decimal("0.02"),
        escalation_probability=Decimal("0.02"),
        independent_verifier_available=True,
        calibration_samples=20,
    )
    values.update(overrides)
    return RouteRequest(**values)


class RoutingTests(unittest.TestCase):
    def test_baseline_is_sonnet_for_frontier(self):
        decision = choose_route(request(), config=cfg(Topology.FRONTIER))
        self.assertEqual(decision.direct_forecast.components[0].model, "claude-sonnet-5")
        self.assertTrue(any(c.model == "claude-opus-4-8" for c in decision.candidate_forecast.components))

    def test_frontier_costs_more_than_lean_when_opus_is_present(self):
        lean = choose_route(request(), config=cfg(Topology.LEAN))
        frontier = choose_route(request(), config=cfg(Topology.FRONTIER))
        self.assertGreater(frontier.candidate_delegated_usd, lean.candidate_delegated_usd)

    def test_direct_output_is_independent_from_worker_output(self):
        low = choose_route(request(direct_usage=TokenUsage(input_tokens=100_000, output_tokens=100)), config=cfg())
        high = choose_route(request(direct_usage=TokenUsage(input_tokens=100_000, output_tokens=10_000)), config=cfg())
        self.assertGreater(high.direct_baseline_usd, low.direct_baseline_usd)

    def test_rejected_candidate_keeps_candidate_cost_but_selected_cost_is_direct(self):
        result = choose_route(request(worker_usage=TokenUsage(input_tokens=100_000, output_tokens=50_000)), config=cfg())
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertEqual(result.selected_route_usd, result.direct_baseline_usd)
        self.assertIsNotNone(result.candidate_delegated_usd)

    def test_writer_requires_independent_verifier(self):
        result = choose_route(request(task_kind=TaskKind.IMPLEMENTATION, independent_verifier_available=False), config=cfg())
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn("INDEPENDENT_VERIFIER_REQUIRED", result.reason_codes)

    def test_batch_requires_all_four_gates(self):
        req = request(closed_context=True, content_retention_confirmed=True)
        no_config = choose_route(req, config=cfg(batch=False), capabilities=RuntimeCapabilities(batch_executor_available=True))
        no_cap = choose_route(req, config=cfg(batch=True), capabilities=RuntimeCapabilities(batch_executor_available=False))
        yes = choose_route(req, config=cfg(batch=True), capabilities=RuntimeCapabilities(batch_executor_available=True))
        self.assertFalse(no_config.batch_eligible)
        self.assertFalse(no_cap.batch_eligible)
        self.assertTrue(yes.batch_eligible)

    def test_retry_and_verifier_can_reject_delegation(self):
        req = request(
            task_kind=TaskKind.IMPLEMENTATION,
            verifier_usage=TokenUsage(input_tokens=20_000, output_tokens=5_000),
            retry_probability=Decimal("0.50"),
        )
        result = choose_route(req, config=cfg())
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)

    def test_hot_context_and_low_samples_are_direct(self):
        self.assertEqual(choose_route(request(main_context_is_hot=True), config=cfg()).selected_route, Route.MAIN_DIRECT)
        self.assertEqual(choose_route(request(calibration_samples=0), config=cfg()).selected_route, Route.MAIN_DIRECT)


if __name__ == "__main__":
    unittest.main()
