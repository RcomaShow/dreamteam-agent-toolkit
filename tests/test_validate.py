import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"

class StructureTests(unittest.TestCase):
    def test_validator(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate.py")],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_marketplace_source_exists(self):
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        for entry in market["plugins"]:
            source = entry["source"]
            self.assertTrue((ROOT / source).exists(), source)

    def test_plugin_version(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")

    def test_workers_have_compact_handoff(self):
        for path in (PLUGIN / "agents").glob("*.md"):
            text = path.read_text()
            self.assertIn("CHP/1", text, path.name)
            self.assertNotIn("permissionMode:", text, path.name)
            self.assertNotIn("mcpServers:", text, path.name)
            self.assertNotIn("hooks:", text, path.name)

if __name__ == "__main__":
    unittest.main()
