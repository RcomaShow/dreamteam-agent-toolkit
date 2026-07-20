import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BUILDER = ROOT / "scripts/build_release.py"


class ReleaseBuilderV04Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(SOURCE_BUILDER, self.root / "scripts/build_release.py")
        manifest = self.root / "adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "dreamteam", "version": "0.4.0"}), encoding="utf-8")
        (self.root / "README.md").write_text("fixture\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("dist/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "DreamTeam Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_builder(self):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/build_release.py")],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

    def test_clean_tracked_tree_builds(self):
        result = self.run_builder()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((self.root / "dist/SOURCE_MANIFEST.json").read_text())
        self.assertEqual(manifest["commit"], subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip())
        self.assertTrue(all(path != ".git" and not path.startswith(".git/") for path in manifest["repository_files"]))

    def test_untracked_file_blocks_release(self):
        (self.root / ".env").write_text("SECRET=value\n", encoding="utf-8")
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("clean Git working tree", result.stderr)

    def test_tracked_symlink_blocks_release(self):
        target = self.root / "outside.txt"
        target.write_text("secret\n", encoding="utf-8")
        link = self.root / "linked-secret"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        subprocess.run(["git", "-C", str(self.root), "add", "outside.txt", "linked-secret"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "track symlink"], check=True)
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release refuses symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
