import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "dist/dreamteam-claude-code-plugin-0.4.3.zip"


class PluginArtifactTests(unittest.TestCase):
    def test_release_artifact_is_self_contained(self):
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if status.stdout.strip():
            self.skipTest("release builder intentionally requires a clean Git tree")
        build = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_release.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        smoke = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/smoke_plugin_artifact.py"),
                str(ARCHIVE),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)


if __name__ == "__main__":
    unittest.main()
