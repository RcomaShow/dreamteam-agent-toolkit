from __future__ import annotations

import importlib.util
import json
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


class StandaloneHookMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.plugin = self.root / "plugin"
        write_fixture_plugin(self.plugin)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def install_with_hooks(self) -> Path:
        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=True,
            python_command="python-test",
        )
        return self.project / ".claude/settings.json"

    def test_uninstall_removes_only_one_managed_hook_occurrence(self) -> None:
        settings_path = self.install_with_hooks()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        entry = settings["hooks"]["PreToolUse"][0]
        settings["hooks"]["PreToolUse"].append(entry)
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        installer.uninstall(scope="project", project_root=self.project)
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["hooks"]["PreToolUse"], [entry])

    def test_modified_hook_blocks_uninstall_without_force(self) -> None:
        settings_path = self.install_with_hooks()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["hooks"]["PreToolUse"][0]["matcher"] = "Write"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")
        with self.assertRaises(installer.StandaloneInstallError):
            installer.uninstall(scope="project", project_root=self.project)
        installer.uninstall(scope="project", project_root=self.project, force=True)
        self.assertFalse(settings_path.exists())


if __name__ == "__main__":
    unittest.main()
