import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "adapters/claude-code/plugins/dreamteam/scripts/dreamteam_ledger_hook.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("dreamteam_hook", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "a.py").write_text("a\n" * 20, encoding="utf-8")
        config = json.loads((ROOT / "dreamteam.config.example.json").read_text())
        config["telemetry"].update({"enabled": True, "ledger": "sqlite", "enforcement": "strict"})
        (self.root / "dreamteam.config.json").write_text(json.dumps(config))
        self.data = self.root / "plugin-data"
        self.hook = load_hook()
        self.env = {"CLAUDE_PLUGIN_DATA": str(self.data), "DREAMTEAM_RUN_ID": "r"}

    def tearDown(self):
        self.temp.cleanup()

    def test_worker_cannot_spawn_agent(self):
        result = self.hook.handle({"cwd": str(self.root), "hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {}, "session_id": "s", "agent_id": "worker"}, "pre", self.env)
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_strict_unaccountable_bash_read_is_denied(self):
        result = self.hook.handle({"cwd": str(self.root), "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git diff | cat"}, "session_id": "s"}, "pre", self.env)
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_post_read_stores_metadata_not_content(self):
        data = {"cwd": str(self.root), "hook_event_name": "PreToolUse", "tool_name": "Read", "tool_use_id": "read-1", "tool_input": {"file_path": str(self.root / "a.py"), "offset": 1, "limit": 2}, "session_id": "s", "agent_id": "worker"}
        self.assertIsNone(self.hook.handle(data, "pre", self.env))
        data["hook_event_name"] = "PostToolUse"
        self.assertIsNone(self.hook.handle(data, "post", self.env))
        db = (self.data / "ledger.sqlite").read_bytes()
        self.assertNotIn(b"a\na\n", db)

    def test_agent_budget_requires_explicit_reservation(self):
        result = self.hook.handle({"cwd": str(self.root), "hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "agent-missing-budget", "tool_input": {"description": "worker"}, "session_id": "s"}, "pre", self.env)
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
