import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"


class SyncTests(unittest.TestCase):
    def test_sync_is_deterministic_for_all_generated_files(self):
        tracked = list((PLUGIN / "agents").glob("*.md"))
        tracked += list((PLUGIN / "skills/run/references").glob("*.md"))
        tracked += list((PLUGIN / "lib/dreamteam").glob("*.py"))
        before = {path.relative_to(ROOT): path.read_bytes() for path in tracked}
        result = subprocess.run([sys.executable, str(ROOT / "scripts/sync_claude_adapter.py")], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after_paths = list((PLUGIN / "agents").glob("*.md")) + list((PLUGIN / "skills/run/references").glob("*.md")) + list((PLUGIN / "lib/dreamteam").glob("*.py"))
        after = {path.relative_to(ROOT): path.read_bytes() for path in after_paths}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
