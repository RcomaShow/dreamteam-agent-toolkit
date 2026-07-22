import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from dreamteam.ledger import RunLedger

ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "adapters/claude-code/plugins/dreamteam/scripts/dreamteam_ledger_hook.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("dreamteam_hook_v04", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def permission(result):
    return result["hookSpecificOutput"].get("permissionDecision")


class HookV04Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "src").mkdir()
        (self.root / "src/a.py").write_text("a\n" * 20, encoding="utf-8")
        config = {
            "version": 2,
            "topology": "lean",
            "profile": "balanced",
            "pricingAsOf": "2026-07-17",
            "verification": {
                "requireIndependentWriterReview": True,
                "requireAnchorValidation": True,
            },
            "telemetry": {
                "enabled": True,
                "storeSourceContent": False,
                "ledger": "sqlite",
                "enforcement": "strict",
            },
        }
        (self.root / "dreamteam.config.json").write_text(json.dumps(config), encoding="utf-8")
        self.data = self.root / "plugin-data"
        self.hook = load_hook()
        self.env = {
            "CLAUDE_PROJECT_DIR": str(self.root),
            "CLAUDE_PLUGIN_DATA": str(self.data),
            "DREAMTEAM_RUN_ID": "r",
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_config_is_loaded_from_project_root_not_cwd(self):
        result = self.hook.handle(
            {
                "cwd": str(self.root / "src"),
                "hook_event_name": "PreToolUse",
                "tool_name": "Agent",
                "tool_use_id": "tool-1",
                "tool_input": {},
                "session_id": "s",
                "agent_id": "worker",
            },
            "pre",
            self.env,
        )
        self.assertEqual(permission(result), "deny")

    def test_outside_root_read_is_denied(self):
        outside = Path(self.temp.name).parent / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_use_id": "outside-read",
                "tool_input": {"file_path": str(outside)},
                "session_id": "s",
            },
            "pre",
            self.env,
        )
        self.assertEqual(permission(result), "deny")
        outside.unlink()

    def test_git_metadata_and_plugin_data_are_denied(self):
        git_config = self.root / ".git/config"
        for tool_name, file_path in (
            ("Read", str(git_config)),
            ("Write", str(git_config)),
        ):
            result = self.hook.handle(
                {
                    "cwd": str(self.root),
                    "hook_event_name": "PreToolUse",
                    "tool_name": tool_name,
                    "tool_use_id": f"internal-{tool_name.lower()}",
                    "tool_input": {"file_path": file_path, "content": "x"},
                    "session_id": "s",
                },
                "pre",
                self.env,
            )
            self.assertEqual(permission(result), "deny")
        self.data.mkdir(parents=True, exist_ok=True)
        secret = self.data / "internal.txt"
        secret.write_text("metadata", encoding="utf-8")
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_use_id": "plugin-data-read",
                "tool_input": {"file_path": str(secret)},
                "session_id": "s",
            },
            "pre",
            self.env,
        )
        self.assertEqual(permission(result), "deny")

    def test_config_write_is_denied(self):
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_use_id": "config-write",
                "tool_input": {"file_path": "dreamteam.config.json", "content": "{}"},
                "session_id": "s",
            },
            "pre",
            self.env,
        )
        self.assertEqual(permission(result), "deny")

    def test_shell_composition_and_bash_reads_are_denied(self):
        for command in ("pytest && cat src/a.py", "git diff", "python -c 'print(1)'"):
            result = self.hook.handle(
                {
                    "cwd": str(self.root),
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "bash-" + sha256(command.encode()).hexdigest()[:8],
                    "tool_input": {"command": command},
                    "session_id": "s",
                },
                "pre",
                self.env,
            )
            self.assertEqual(permission(result), "deny", command)

    def test_missing_tool_use_id_is_denied(self):
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "src/a.py"},
                "session_id": "s",
            },
            "pre",
            self.env,
        )
        self.assertEqual(permission(result), "deny")

    def test_symlink_escape_is_denied(self):
        outside = Path(self.temp.name).parent / "outside-symlink.txt"
        outside.write_text("secret", encoding="utf-8")
        link = self.root / "src/link.txt"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        try:
            result = self.hook.handle(
                {
                    "cwd": str(self.root),
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "tool_use_id": "symlink-read",
                    "tool_input": {"file_path": "src/link.txt"},
                    "session_id": "s",
                },
                "pre",
                self.env,
            )
            self.assertEqual(permission(result), "deny")
        finally:
            outside.unlink(missing_ok=True)

    def test_reread_permit_still_stages_and_accounts_the_read(self):
        self.data.mkdir(parents=True, exist_ok=True)
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            content = (self.root / "src/a.py").read_bytes()
            blob = subprocess.run(
                ["git", "-C", str(self.root), "hash-object", "--", "src/a.py"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()
            from dreamteam.ledger import ReadEvent

            ledger.record_read(
                ReadEvent(
                    "r", "worker", "worker", "src/a.py", blob, 0, len(content), "explore"
                )
            )
            ledger.grant_permit("r", "main", "src/a.py", "decision")
        finally:
            ledger.close()

        event = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_use_id": "permitted-reread",
            "tool_input": {"file_path": "src/a.py"},
            "session_id": "s",
        }
        result = self.hook.handle(event, "pre", self.env)
        self.assertIn("permit consumed", result["hookSpecificOutput"]["additionalContext"])
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertIsNotNone(ledger.pending_read("r", "permitted-reread"))
        finally:
            ledger.close()
        event["hook_event_name"] = "PostToolUse"
        self.assertIsNone(self.hook.handle(event, "post", self.env))
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertIsNone(ledger.pending_read("r", "permitted-reread"))
            self.assertEqual(ledger.main_reread_ratio("r"), 1.0)
        finally:
            ledger.close()

    def test_read_changed_between_pre_and_post_is_invalidated(self):
        event = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_use_id": "read-changing",
            "tool_input": {"file_path": "src/a.py", "offset": 1, "limit": 2},
            "session_id": "s",
            "agent_id": "worker",
        }
        self.assertIsNone(self.hook.handle(event, "pre", self.env))
        (self.root / "src/a.py").write_text("changed\n" * 20, encoding="utf-8")
        event["hook_event_name"] = "PostToolUse"
        result = self.hook.handle(event, "post", self.env)
        self.assertIn("invalidated", result["hookSpecificOutput"]["additionalContext"])
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertIsNone(ledger.pending_read("r", "read-changing"))
            count = ledger.connection.execute(
                "SELECT COUNT(*) FROM reads WHERE run_id=?", ("r",)
            ).fetchone()[0]
            invalidations = ledger.connection.execute(
                "SELECT category FROM invalidations WHERE run_id=?", ("r",)
            ).fetchall()
            self.assertEqual(count, 0)
            self.assertIn(("read_changed_during_tool",), invalidations)
        finally:
            ledger.close()

    def test_failed_read_discards_pending_event(self):
        event = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_use_id": "read-failed",
            "tool_input": {"file_path": "src/a.py", "offset": 1, "limit": 2},
            "session_id": "s",
            "agent_id": "worker",
        }
        self.assertIsNone(self.hook.handle(event, "pre", self.env))
        event["hook_event_name"] = "PostToolUseFailure"
        self.assertIsNone(self.hook.handle(event, "failure", self.env))
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertIsNone(ledger.pending_read("r", "read-failed"))
        finally:
            ledger.close()

    def test_exact_bash_permit_allows_safe_check(self):
        command = "python -m unittest --help"
        env = dict(self.env)
        env["DREAMTEAM_ALLOWED_BASH_SHA256"] = sha256(command.encode()).hexdigest()
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_use_id": "bash-permitted",
                "tool_input": {"command": command},
                "session_id": "s",
            },
            "pre",
            env,
        )
        self.assertIsNone(result)

    def test_parallel_agent_cap_is_enforced(self):
        env = dict(self.env)
        env["DREAMTEAM_NEXT_AGENT_USD_MICROS"] = "100000"
        first = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_use_id": "parallel-1",
            "tool_input": {"description": "first"},
            "session_id": "s",
        }
        second = dict(first)
        second["tool_use_id"] = "parallel-2"
        second["tool_input"] = {"description": "second"}
        self.assertIsNone(self.hook.handle(first, "pre", env))
        self.assertEqual(permission(self.hook.handle(second, "pre", env)), "deny")

    def test_invalid_subagent_handoff_is_blocked_once(self):
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "SubagentStop",
                "agent_id": "agent-1",
                "agent_type": "discovery-symbol-locator",
                "last_assistant_message": "plain prose",
                "stop_hook_active": False,
                "session_id": "s",
            },
            "subagent-stop",
            self.env,
        )
        self.assertEqual(result["decision"], "block")

    def test_valid_subagent_handoff_is_checkpointed(self):
        contract = "sha256:" + "a" * 64
        message = "\n".join([
            "CHP|2",
            "RUN|r",
            "TASK|t",
            f"CONTRACT|{contract}",
            "S|DONE|bounded task finished",
            "N|ORCHESTRATOR|review the handoff",
            "",
        ])
        self.data.mkdir(parents=True, exist_ok=True)
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertTrue(ledger.bind_contract("r", "t", contract))
        finally:
            ledger.close()
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "SubagentStop",
                "agent_id": "agent-2",
                "agent_type": "discovery-symbol-locator",
                "last_assistant_message": message,
                "stop_hook_active": False,
                "session_id": "s",
            },
            "subagent-stop",
            self.env,
        )
        self.assertIsNone(result)
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertTrue(ledger.completed("r", "agent-2"))
        finally:
            ledger.close()

    def test_reviewer_identity_is_distinct_and_claimed(self):
        contract = "sha256:" + "d" * 64
        message = "\n".join([
            "CHP|2",
            "RUN|r",
            "TASK|reviewed",
            f"CONTRACT|{contract}",
            "S|DONE|finished",
            "N|ORCHESTRATOR|accept",
            "",
        ])
        self.data.mkdir(parents=True, exist_ok=True)
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertTrue(ledger.bind_contract("r", "reviewed", contract))
        finally:
            ledger.close()
        worker = {
            "cwd": str(self.root),
            "hook_event_name": "SubagentStop",
            "agent_id": "writer-agent",
            "agent_type": "execution-bounded-logic",
            "last_assistant_message": message,
            "stop_hook_active": False,
            "session_id": "s",
        }
        self.assertIsNone(self.hook.handle(worker, "subagent-stop", self.env))

        self_review = dict(worker)
        self_review["agent_type"] = "verification-independent-reviewer"
        result = self.hook.handle(self_review, "subagent-stop", self.env)
        self.assertEqual(result["decision"], "block")

        independent = dict(worker)
        independent["agent_id"] = "reviewer-agent"
        independent["agent_type"] = "verification-independent-reviewer"
        self.assertIsNone(self.hook.handle(independent, "subagent-stop", self.env))
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertEqual(
                ledger.contract_binding("r", "reviewed"),
                (contract, "writer-agent", "reviewer-agent"),
            )
        finally:
            ledger.close()

    def test_valid_handoff_without_registered_contract_is_blocked(self):
        contract = "sha256:" + "c" * 64
        message = "\n".join([
            "CHP|2",
            "RUN|r",
            "TASK|unbound",
            f"CONTRACT|{contract}",
            "S|DONE|finished",
            "N|ORCHESTRATOR|review",
            "",
        ])
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "SubagentStop",
                "agent_id": "agent-unbound",
                "agent_type": "discovery-symbol-locator",
                "last_assistant_message": message,
                "stop_hook_active": False,
                "session_id": "s",
            },
            "subagent-stop",
            self.env,
        )
        self.assertEqual(result["decision"], "block")
        self.assertIn("registered DCP/2 binding", result["reason"])

    def test_trusted_dreamteam_wrapper_does_not_need_generic_bash_permit(self):
        command = (
            f'python3 "{ROOT / "adapters/claude-code/plugins/dreamteam/scripts/dreamteam_protocol.py"}" --help'
        )
        env = dict(self.env)
        env["CLAUDE_PLUGIN_ROOT"] = str(
            ROOT / "adapters/claude-code/plugins/dreamteam"
        )
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_use_id": "trusted-wrapper",
                "tool_input": {"command": command},
                "session_id": "s",
            },
            "pre",
            env,
        )
        self.assertIsNone(result)

    def test_agent_reservation_is_committed_on_success(self):
        env = dict(self.env)
        env["DREAMTEAM_NEXT_AGENT_USD_MICROS"] = "400000"
        event = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_use_id": "tool-42",
            "tool_input": {"description": "worker"},
            "session_id": "s",
        }
        self.assertIsNone(self.hook.handle(event, "pre", env))
        event["hook_event_name"] = "PostToolUse"
        self.assertIsNone(self.hook.handle(event, "post", env))
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertEqual(ledger.active_reservations("r"), 0)
            self.assertEqual(ledger.charged("r"), 400000)
        finally:
            ledger.close()

    def test_agent_reservation_is_released_on_failure(self):
        env = dict(self.env)
        env["DREAMTEAM_NEXT_AGENT_USD_MICROS"] = "400000"
        event = {
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_use_id": "tool-43",
            "tool_input": {"description": "worker"},
            "session_id": "s",
        }
        self.assertIsNone(self.hook.handle(event, "pre", env))
        event["hook_event_name"] = "PostToolUseFailure"
        self.assertIsNone(self.hook.handle(event, "failure", env))
        ledger = RunLedger(self.data / "ledger.sqlite")
        try:
            self.assertEqual(ledger.active_reservations("r"), 0)
            self.assertEqual(ledger.charged("r"), 0)
        finally:
            ledger.close()


    def test_strict_mode_rejects_cwd_as_project_root_fallback(self):
        env = dict(self.env)
        env.pop("CLAUDE_PROJECT_DIR")
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_use_id": "unstable-root",
                "tool_input": {"file_path": "src/a.py"},
                "session_id": "s",
            },
            "pre",
            env,
        )
        self.assertEqual(permission(result), "deny")
        self.assertIn("cwd fallback", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_plugin_data_symlink_is_denied_before_ledger_open(self):
        target = self.root / "real-plugin-data"
        target.mkdir()
        link = self.root / "linked-plugin-data"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        env = dict(self.env)
        env["CLAUDE_PLUGIN_DATA"] = str(link)
        result = self.hook.handle(
            {
                "cwd": str(self.root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_use_id": "plugin-data-symlink",
                "tool_input": {"file_path": "src/a.py"},
                "session_id": "s",
            },
            "pre",
            env,
        )
        self.assertEqual(permission(result), "deny")
        self.assertIn("symlink", result["hookSpecificOutput"]["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
