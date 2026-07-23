from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from standalone_fixture import write_fixture_plugin

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "adapters/claude-code/standalone/installer.py"
)
SPEC = importlib.util.spec_from_file_location("dreamteam_standalone_installer", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class StandaloneScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.plugin = self.root / "plugin"
        write_fixture_plugin(self.plugin)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_python_command_rejects_shell_control_characters(self) -> None:
        with self.assertRaises(installer.StandaloneInstallError):
            installer.install(
                scope="project",
                project_root=self.project,
                source_plugin_root=self.plugin,
                python_command="python\nbad",
            )

    def test_scope_mismatch_is_rejected_for_same_claude_root(self) -> None:
        base = self.root / "shared"
        base.mkdir()
        installer.install(
            scope="user",
            home=base,
            source_plugin_root=self.plugin,
        )
        report = installer.doctor(scope="project", project_root=base)
        self.assertFalse(report.ready)
        self.assertIn("STATE_UNAVAILABLE", {item.code for item in report.diagnostics})

    def test_user_scope_uses_home_claude_directory(self) -> None:
        home = self.root / "home"
        home.mkdir()
        result = installer.install(
            scope="user",
            home=home,
            source_plugin_root=self.plugin,
        )
        self.assertEqual(Path(result.claude_root), home / ".claude")
        self.assertTrue((home / ".claude/skills/dreamteam-init/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
