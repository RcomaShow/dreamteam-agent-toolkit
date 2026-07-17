import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"


class StructureTests(unittest.TestCase):
    def test_validator(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_marketplace_source_exists(self):
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        for entry in market["plugins"]:
            self.assertTrue((ROOT / entry["source"]).exists())

    def test_plugin_version_and_hooks(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["version"], "0.4.0")
        self.assertFalse(manifest["defaultEnabled"])
        self.assertTrue((PLUGIN / "hooks/hooks.json").is_file())
        self.assertTrue((PLUGIN / "lib/dreamteam/routing.py").is_file())
        self.assertTrue((PLUGIN / "lib/dreamteam/protocol.py").is_file())

    def test_strict_templates_do_not_use_unavailable_contracts(self):
        for path in (ROOT / "core/templates").glob("*.txt"):
            self.assertNotIn("CONTRACT|UNAVAILABLE", path.read_text())

    def test_no_release_bootstrap(self):
        self.assertFalse((ROOT / ".dreamteam-bootstrap").exists())
        self.assertFalse((ROOT / "scripts/bootstrap_v03.py").exists())
        self.assertFalse((ROOT / ".github/workflows/bootstrap-v03.yml").exists())
        self.assertFalse((ROOT / ".github/workflows/remediate-v03.yml").exists())


if __name__ == "__main__":
    unittest.main()
