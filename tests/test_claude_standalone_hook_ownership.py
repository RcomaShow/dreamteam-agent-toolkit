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


class StandaloneHookOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.plugin = self.root / "plugin"
        write_fixture_plugin(self.plugin)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def hook_entry(self) -> dict[str, object]:
        runtime = self.project / ".claude/dreamteam"
        return {
            "matcher": "Read",
            "hooks": [
                {
                    "type": "command",
                    "command": f'"python-test" "{runtime.as_posix()}/scripts/hook.py" pre',
                }
            ],
        }

    def test_preexisting_identical_hook_is_not_claimed_or_removed(self) -> None:
        entry = self.hook_entry()
        settings_path = self.project / ".claude/settings.json"
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(
            json.dumps({"hooks": {"PreToolUse": [entry]}}),
            encoding="utf-8",
        )
        original = settings_path.read_bytes()

        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=True,
            python_command="python-test",
        )
        state = json.loads(
            (self.project / ".claude/dreamteam/install-state.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(state["managedHooks"], {})
        self.assertEqual(state["expectedHooks"], {"PreToolUse": [entry]})
        self.assertEqual(settings_path.read_bytes(), original)
        self.assertTrue(
            installer.doctor(scope="project", project_root=self.project).ready
        )

        installer.uninstall(scope="project", project_root=self.project)
        self.assertEqual(settings_path.read_bytes(), original)

    def test_doctor_checks_expected_preexisting_hook(self) -> None:
        entry = self.hook_entry()
        settings_path = self.project / ".claude/settings.json"
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(
            json.dumps({"hooks": {"PreToolUse": [entry]}}),
            encoding="utf-8",
        )
        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=True,
            python_command="python-test",
        )
        settings_path.write_text(json.dumps({"hooks": {}}), encoding="utf-8")

        report = installer.doctor(scope="project", project_root=self.project)
        self.assertFalse(report.ready)
        self.assertIn("HOOK_MISSING", {item.code for item in report.diagnostics})


if __name__ == "__main__":
    unittest.main()
