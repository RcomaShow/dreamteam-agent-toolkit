import json
from pathlib import Path
import tempfile
import unittest

from dreamteam.config import RuntimeConfig


def config():
    return {
        "version": 2,
        "topology": "lean",
        "pricingAsOf": "2026-07-17",
        "verification": {
            "requireIndependentWriterReview": True,
            "requireAnchorValidation": True,
        },
        "telemetry": {
            "storeSourceContent": False,
            "ledger": "off",
            "enforcement": "advisory",
        },
    }


class ConfigTests(unittest.TestCase):
    def test_defaults_and_snapshot(self):
        parsed = RuntimeConfig.from_mapping(config())
        self.assertEqual(parsed.pricing_as_of.isoformat(), "2026-07-17")
        self.assertEqual(str(parsed.routing.minimum_savings_margin), "0.3")

    def test_unknown_property_rejected(self):
        data = config(); data["unknown"] = 1
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)

    def test_security_fields_required(self):
        data = config(); del data["verification"]
        with self.assertRaises(TypeError):
            RuntimeConfig.from_mapping(data)
        data = config(); data["telemetry"]["storeSourceContent"] = True
        with self.assertRaises(ValueError):
            RuntimeConfig.from_mapping(data)

    def test_file_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config()))
            self.assertEqual(RuntimeConfig.from_file(path).version, 2)


if __name__ == "__main__":
    unittest.main()
