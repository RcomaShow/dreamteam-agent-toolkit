import unittest
from decimal import Decimal

from dreamteam.config import RuntimeCapabilities, RuntimeConfig
from dreamteam.pricing import TokenUsage
from dreamteam.routing import Criticality, Route, RouteRequest, TaskKind, choose_route


def cfg(topology="lean", profile="balanced", max_run=10, strict=False, models=None):
    data = {
        "version": 2,
        "topology": topology,
        "profile": profile,
        "pricingAsOf": "2026-07-17",
        "routing": {
            "minimumSavingsMargin": 0.20,
            "maxEscalationProbability": 0.25,
            "maxMainRereadRatio": 0.35,
            "minSamplesForEnforcement": 20,
            "allowClosedContextBatch": False,
        },
        "budgets": {"maxRunUsd": max_run},
        "verification": {
            "requireIndependentWriterReview": True,
            "requireAnchorValidation": True,
        },
        "telemetry": {
            "enabled": strict,
            "storeSourceContent": False,
            "ledger": "sqlite" if strict else "off",
            "enforcement": "strict" if strict else "advisory",
        },
    }
    if models is not None:
        data["models"] = models
    return RuntimeConfig.from_mapping(data)


def lean_request(**overrides):
    values = dict(
        criticality=Criticality.M0,
        task_kind=TaskKind.DISCOVERY,
        direct_usage=TokenUsage(input_tokens=1_000_000, output_tokens=100_000),
        worker_usage=TokenUsage(input_tokens=50_000, output_tokens=1_000),
        lead_usage=TokenUsage(),
        verifier_usage=TokenUsage(),
        executive_usage=TokenUsage(),
        retry_probability=Decimal("0.01"),
        escalation_probability=Decimal("0.01"),
        independent_verifier_available=False,
        calibration_samples=20,
    )
    values.update(overrides)
    return RouteRequest(**values)


def opus_sonnet_request(**overrides):
    values = dict(
        worker_usage=TokenUsage(),
        lead_usage=TokenUsage(input_tokens=50_000, output_tokens=2_000),
        executive_usage=TokenUsage(input_tokens=10_000, output_tokens=1_000),
    )
    values.update(overrides)
    return lean_request(**values)


def frontier_request(**overrides):
    values = dict(
        lead_usage=TokenUsage(input_tokens=20_000, output_tokens=1_000),
        executive_usage=TokenUsage(input_tokens=10_000, output_tokens=1_000),
    )
    values.update(overrides)
    return lean_request(**values)


class RoutingV04Tests(unittest.TestCase):
    def test_opus_sonnet_selects_concrete_sonnet_lead(self):
        decision = choose_route(opus_sonnet_request(), config=cfg("opus-sonnet"))
        self.assertEqual(decision.selected_route, Route.SONNET_LEAD)
        self.assertEqual(decision.selected_agent_role, "coordination-decision-analyst")
        self.assertEqual(decision.execution_chain, ("opus-executive", "coordination-decision-analyst"))

    def test_opus_sonnet_write_uses_lead_and_distinct_reviewer(self):
        decision = choose_route(
            opus_sonnet_request(
                criticality=Criticality.L2,
                task_kind=TaskKind.IMPLEMENTATION,
                verifier_usage=TokenUsage(input_tokens=10_000, output_tokens=1_000),
                independent_verifier_available=True,
            ),
            config=cfg("opus-sonnet", profile="quality"),
        )
        self.assertEqual(decision.selected_agent_role, "execution-sonnet-lead")
        self.assertEqual(decision.execution_chain[-1], "verification-independent-reviewer")

    def test_frontier_keeps_opus_sonnet_haiku_components_and_support_role(self):
        decision = choose_route(frontier_request(), config=cfg("frontier"))
        models = {component.model for component in decision.candidate_forecast.components}
        self.assertEqual(models, {"claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"})
        self.assertEqual(decision.support_agent_role, "discovery-context-synthesizer")

    def test_l2_read_only_uses_sonnet_role(self):
        decision = choose_route(
            lean_request(
                criticality=Criticality.L2,
                task_kind=TaskKind.REVIEW,
                worker_usage=TokenUsage(),
                lead_usage=TokenUsage(input_tokens=10_000, output_tokens=1_000),
            ),
            config=cfg("lean"),
        )
        self.assertEqual(decision.selected_route, Route.SONNET_LEAD)
        self.assertEqual(decision.selected_agent_role, "verification-independent-reviewer")

    def test_discovery_role_can_be_selected_explicitly(self):
        decision = choose_route(
            lean_request(requested_role="discovery-symbol-locator"),
            config=cfg(),
        )
        self.assertEqual(decision.selected_agent_role, "discovery-symbol-locator")

    def test_write_requires_nonzero_independent_verifier_cost(self):
        result = choose_route(
            lean_request(task_kind=TaskKind.IMPLEMENTATION),
            config=cfg(),
        )
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn("INDEPENDENT_VERIFIER_REQUIRED", result.reason_codes)

    def test_direct_and_c3_budget_are_hard_gates(self):
        direct = choose_route(lean_request(main_context_is_hot=True), config=cfg(max_run=0.01))
        self.assertEqual(direct.selected_route, Route.BLOCKED)
        c3 = choose_route(
            opus_sonnet_request(criticality=Criticality.C3),
            config=cfg("opus-sonnet", max_run=0.01),
        )
        self.assertEqual(c3.selected_route, Route.BLOCKED)

    def test_strict_mode_requires_hooks_capability(self):
        result = choose_route(lean_request(), config=cfg(strict=True))
        self.assertEqual(result.selected_route, Route.BLOCKED)
        allowed = choose_route(
            lean_request(),
            config=cfg(strict=True),
            capabilities=RuntimeCapabilities(hooks_available=True),
        )
        self.assertNotEqual(allowed.selected_route, Route.BLOCKED)

    def test_opus_sonnet_rejects_hidden_haiku_cost(self):
        result = choose_route(
            opus_sonnet_request(worker_usage=TokenUsage(input_tokens=1_000)),
            config=cfg("opus-sonnet"),
        )
        self.assertEqual(result.selected_route, Route.MAIN_DIRECT)
        self.assertIn("CANDIDATE_FORECAST_INVALID", result.reason_codes)

    def test_configured_worker_model_is_used(self):
        decision = choose_route(
            lean_request(),
            config=cfg(models={"executive": "inherit", "lead": "sonnet", "workers": "sonnet"}),
        )
        worker = next(component for component in decision.candidate_forecast.components if component.name == "haiku-worker")
        self.assertEqual(worker.model, "claude-sonnet-5")

    def test_profile_limits_are_exposed_as_execution_policy(self):
        decision = choose_route(lean_request(), config=cfg(profile="offload"))
        self.assertEqual(decision.execution_policy.max_active_workers, 2)
        self.assertTrue(decision.execution_policy.allow_parallel_independent)
        self.assertEqual(decision.execution_policy.max_retries, 1)

    def test_request_rejects_untyped_enums_and_usage(self):
        with self.assertRaises(TypeError):
            RouteRequest(  # type: ignore[arg-type]
                criticality="M0",
                task_kind=TaskKind.DISCOVERY,
                direct_usage=TokenUsage(input_tokens=2_000),
            )
        with self.assertRaises(TypeError):
            RouteRequest(  # type: ignore[arg-type]
                criticality=Criticality.M0,
                task_kind=TaskKind.DISCOVERY,
                direct_usage={"input_tokens": 2_000},
            )


if __name__ == "__main__":
    unittest.main()
