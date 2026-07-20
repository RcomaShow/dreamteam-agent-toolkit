import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"


class WorkerCatalogTests(unittest.TestCase):
    def test_worker_families_models_and_effort(self):
        files = list((PLUGIN / "agents").glob("*.md"))
        self.assertEqual(len(files), 16)
        families = {path.stem.split("-", 1)[0] for path in files}
        self.assertEqual(families, {"coordination", "discovery", "execution", "verification"})
        haiku = sonnet = 0
        for path in files:
            text = path.read_text()
            self.assertIn("effort:", text)
            self.assertIn("CHP/2", text)
            self.assertNotIn("Agent,", text)
            if "model: haiku" in text:
                haiku += 1
            if "model: sonnet" in text:
                sonnet += 1
        self.assertEqual((haiku, sonnet), (13, 3))

    def test_frontier_roles_are_bounded(self):
        analyst = (PLUGIN / "agents/coordination-decision-analyst.md").read_text()
        reviewer = (PLUGIN / "agents/verification-independent-reviewer.md").read_text()
        lead = (PLUGIN / "agents/execution-sonnet-lead.md").read_text()
        self.assertIn("Do not perform broad repository discovery", analyst)
        self.assertIn("Reject self-review", reviewer)
        self.assertIn("Opus executive", lead)


if __name__ == "__main__":
    unittest.main()
