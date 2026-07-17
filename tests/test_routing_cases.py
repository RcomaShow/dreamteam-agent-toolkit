import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RoutingCaseTests(unittest.TestCase):
    def test_cases_cover_routes_classes_and_opus_sonnet(self):
        cases = json.loads((ROOT / "evals/routing/cases.json").read_text())
        self.assertEqual({case["class"] for case in cases}, {"M0", "L1", "L2", "C3"})
        self.assertEqual(
            {case["route"] for case in cases},
            {"BLOCKED", "MAIN_DIRECT", "HAIKU_DISCOVERY", "HAIKU_EXECUTE", "SONNET_LEAD", "OPUS_DECISION"},
        )
        self.assertTrue(any(case["topology"] == "opus-sonnet" for case in cases))
        self.assertTrue(any(case["role"] == "execution-sonnet-lead" for case in cases))


if __name__ == "__main__":
    unittest.main()
