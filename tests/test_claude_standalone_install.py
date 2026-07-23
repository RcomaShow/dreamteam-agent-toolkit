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



class StandaloneInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.plugin = self.root / "plugin"
        write_fixture_plugin(self.plugin)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_install_doctor_and_uninstall_with_hooks(self) -> None:
        settings_path = self.project / ".claude/settings.json"
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(
            json.dumps({"permissions": {"allow": ["Read"]}, "hooks": {"Stop": []}}),
            encoding="utf-8",
        )

        result = installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=True,
            python_command="python-test",
        )
        self.assertEqual(result.action, "installed")
        skill = self.project / ".claude/skills/dreamteam-init/SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertIn("name: dreamteam-init", text)
        self.assertIn("/dreamteam-doctor", text)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)
        self.assertIn("python-test", text)
        self.assertTrue(
            (self.project / ".claude/dreamteam/.claude-plugin/plugin.json").is_file()
        )
        runtime_text = (
            self.project / ".claude/dreamteam/lib/dreamteam/runtime.py"
        ).read_text(encoding="utf-8")
        self.assertIn("/dreamteam-doctor", runtime_text)
        self.assertNotIn("/dreamteam:doctor", runtime_text)
        doctor_skill = self.project / ".claude/skills/dreamteam-doctor/SKILL.md"
        doctor_text = doctor_skill.read_text(encoding="utf-8")
        self.assertIn("--hooks-available", doctor_text)
        self.assertIn("--plugin-root", doctor_text)

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["permissions"], {"allow": ["Read"]})
        self.assertEqual(settings["hooks"]["Stop"], [])
        self.assertEqual(len(settings["hooks"]["PreToolUse"]), 1)
        command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("python-test", command)
        self.assertIn("/.claude/dreamteam/scripts/hook.py", command)

        report = installer.doctor(scope="project", project_root=self.project)
        self.assertTrue(report.ready)
        self.assertTrue(report.hooks_enabled)

        removed = installer.uninstall(scope="project", project_root=self.project)
        self.assertEqual(removed.action, "uninstalled")
        self.assertFalse(skill.exists())
        self.assertFalse((self.project / ".claude/dreamteam/install-state.json").exists())
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings, {"hooks": {"Stop": []}, "permissions": {"allow": ["Read"]}})

    def test_reinstall_is_idempotent_and_does_not_duplicate_hooks(self) -> None:
        for _ in range(2):
            installer.install(
                scope="project",
                project_root=self.project,
                source_plugin_root=self.plugin,
                enable_hooks=True,
                python_command="python-test",
            )
        settings = json.loads(
            (self.project / ".claude/settings.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(settings["hooks"]["PreToolUse"]), 1)

    def test_uninstall_blocks_modified_tracked_file(self) -> None:
        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
        )
        skill = self.project / ".claude/skills/dreamteam-init/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "modified\n", encoding="utf-8")
        with self.assertRaises(installer.StandaloneInstallError):
            installer.uninstall(scope="project", project_root=self.project)
        installer.uninstall(scope="project", project_root=self.project, force=True)


    def test_install_rejects_non_directory_claude_root(self) -> None:
        (self.project / ".claude").write_text("not a directory", encoding="utf-8")
        with self.assertRaises(installer.StandaloneInstallError):
            installer.install(
                scope="project",
                project_root=self.project,
                source_plugin_root=self.plugin,
            )

    def test_install_blocks_untracked_collision(self) -> None:
        skill = self.project / ".claude/skills/dreamteam-init/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("custom\n", encoding="utf-8")
        with self.assertRaises(installer.StandaloneInstallError):
            installer.install(
                scope="project",
                project_root=self.project,
                source_plugin_root=self.plugin,
            )


    def test_install_blocks_identical_untracked_file(self) -> None:
        agent = self.project / ".claude/agents/dreamteam-discovery-symbol-locator.md"
        agent.parent.mkdir(parents=True)
        agent.write_bytes(
            (self.plugin / "agents/discovery-symbol-locator.md").read_bytes()
        )
        with self.assertRaises(installer.StandaloneInstallError):
            installer.install(
                scope="project",
                project_root=self.project,
                source_plugin_root=self.plugin,
            )

    def test_install_without_hooks_leaves_settings_untouched(self) -> None:
        settings_path = self.project / ".claude/settings.json"
        settings_path.parent.mkdir(parents=True)
        original = '{"theme":"dark"}\n'
        settings_path.write_text(original, encoding="utf-8")
        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=False,
        )
        self.assertEqual(settings_path.read_text(encoding="utf-8"), original)
        doctor_text = (
            self.project / ".claude/skills/dreamteam-doctor/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("--hooks-available", doctor_text)
        self.assertNotIn("--plugin-root", doctor_text)
        report = installer.doctor(scope="project", project_root=self.project)
        self.assertTrue(report.ready)
        self.assertFalse(report.hooks_enabled)


    def test_disabling_hooks_removes_adapter_created_empty_settings(self) -> None:
        settings_path = self.project / ".claude/settings.json"
        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=True,
            python_command="python-test",
        )
        self.assertTrue(settings_path.is_file())

        installer.install(
            scope="project",
            project_root=self.project,
            source_plugin_root=self.plugin,
            enable_hooks=False,
            python_command="python-test",
        )
        self.assertFalse(settings_path.exists())
        report = installer.doctor(scope="project", project_root=self.project)
        self.assertTrue(report.ready)
        self.assertFalse(report.hooks_enabled)




if __name__ == "__main__":
    unittest.main()
