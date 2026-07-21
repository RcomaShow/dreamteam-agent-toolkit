import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"


def generated_files() -> list[Path]:
    files = list((PLUGIN / "agents").glob("*.md"))
    files += list((PLUGIN / "skills/run/references").glob("*.md"))
    files += [path for path in (PLUGIN / "lib/dreamteam").glob("*") if path.is_file()]
    return sorted(files)


class SyncTests(unittest.TestCase):
    def test_sync_is_deterministic_for_all_generated_files(self):
        before = {path.relative_to(ROOT): path.read_bytes() for path in generated_files()}
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sync_claude_adapter.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {path.relative_to(ROOT): path.read_bytes() for path in generated_files()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
