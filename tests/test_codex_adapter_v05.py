import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/install_codex_adapter.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_codex_adapter_v05", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CodexAdapterV05Tests(unittest.TestCase):
    def test_project_install_is_exact_and_non_destructive(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = module.install_project(root)
            self.assertEqual(
                target.read_bytes(),
                (ROOT / "adapters/codex/AGENTS.md").read_bytes(),
            )
            self.assertEqual(list(root.glob(".AGENTS.md.dreamteam-*")), [])
            target.write_text("user instructions\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                module.install_project(root)
            self.assertEqual(target.read_text(encoding="utf-8"), "user instructions\n")

    def test_force_is_explicit(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "AGENTS.md"
            target.write_text("old\n", encoding="utf-8")
            module.install_project(root, force=True)
            self.assertIn("DreamTeam 0.5", target.read_text(encoding="utf-8"))

    def test_symlink_target_is_rejected_without_touching_target(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.md"
            outside.write_text("keep\n", encoding="utf-8")
            link = root / "AGENTS.md"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable")
            with self.assertRaises(PermissionError):
                module.install_project(root, force=True)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

    def test_target_appearing_during_publish_fails_closed(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(module.os, "link", side_effect=FileExistsError):
                with self.assertRaises(FileExistsError):
                    module.install_project(root)
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertEqual(list(root.glob(".AGENTS.md.dreamteam-*")), [])

    def test_user_skill_installs_under_codex_home(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            target = module.install_user_skill(Path(tmp))
            self.assertEqual(target.relative_to(Path(tmp)).as_posix(), "skills/dreamteam-run/SKILL.md")
            self.assertIn("name: dreamteam-run", target.read_text(encoding="utf-8"))

    def test_dry_run_does_not_create_files(self):
        module = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = module.install_project(root, dry_run=True)
            self.assertFalse(target.exists())

    def test_adapter_stays_compact(self):
        agents = (ROOT / "adapters/codex/AGENTS.md").read_bytes()
        skill = (ROOT / "adapters/codex/skills/dreamteam-run/SKILL.md").read_bytes()
        self.assertLess(len(agents), 16_000)
        self.assertLess(len(skill), 8_000)


if __name__ == "__main__":
    unittest.main()
