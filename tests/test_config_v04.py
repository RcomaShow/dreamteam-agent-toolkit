import unittest

from dreamteam.config import Profile, RuntimeConfig, Topology


def config(profile="balanced", topology="lean"):
    return {
        "version": 2,
        "topology": topology,
        "profile": profile,
        "pricingAsOf": "2026-07-17",
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


class ConfigV04Tests(unittest.TestCase):
    def test_opus_sonnet_topology_is_supported(self):
        parsed = RuntimeConfig.from_mapping(config(topology="opus-sonnet"))
        self.assertEqual(parsed.topology, Topology.OPUS_SONNET)

    def test_profiles_apply_real_defaults(self):
        economy = RuntimeConfig.from_mapping(config("economy"))
        offload = RuntimeConfig.from_mapping(config("offload"))
        quality = RuntimeConfig.from_mapping(config("quality"))
        self.assertEqual(economy.profile, Profile.ECONOMY)
        self.assertEqual(str(economy.routing.minimum_savings_margin), "0.40")
        self.assertEqual(economy.budgets.max_retries, 0)
        self.assertEqual(offload.budgets.max_active_workers, 2)
        self.assertTrue(offload.routing.allow_parallel_independent)
        self.assertEqual(quality.budgets.max_worker_turns, 14)

    def test_explicit_values_override_profile(self):
        data = config("economy")
        data["routing"] = {"minimumSavingsMargin": 0.15}
        data["budgets"] = {"maxRetries": 3}
        parsed = RuntimeConfig.from_mapping(data)
        self.assertEqual(str(parsed.routing.minimum_savings_margin), "0.15")
        self.assertEqual(parsed.budgets.max_retries, 3)

    def test_strict_requires_enabled_sqlite(self):
        data = config()
        data["telemetry"]["enforcement"] = "strict"
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)
        data["telemetry"].update({"enabled": True, "ledger": "sqlite"})
        self.assertEqual(RuntimeConfig.from_mapping(data).telemetry.enforcement, "strict")

    def test_enabled_telemetry_requires_sqlite(self):
        data = config()
        data["telemetry"]["enabled"] = True
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)
        data = config()
        data["telemetry"]["ledger"] = "sqlite"
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)

    def test_non_finite_values_are_rejected(self):
        data = config()
        data["budgets"] = {"maxRunUsd": "Infinity"}
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)

    def test_runtime_capabilities_require_real_booleans(self):
        from dreamteam.config import RuntimeCapabilities

        with self.assertRaises(TypeError):
            RuntimeCapabilities(hooks_available="false")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
