import json
import sqlite3
from pathlib import Path
import tempfile
import unittest

from dreamteam.config import RuntimeConfig
from dreamteam.operations import (
    doctor,
    minimal_config,
    render_doctor_text,
    render_status_text,
    status,
    write_minimal_config,
)


class OperationsV041Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_minimal_advisory_config_is_valid(self):
        data = minimal_config()
        parsed = RuntimeConfig.from_mapping(data)
        self.assertEqual(parsed.topology.value, "lean")
        self.assertEqual(parsed.profile.value, "balanced")
        self.assertFalse(parsed.telemetry.enabled)
        self.assertEqual(parsed.telemetry.ledger, "off")
        self.assertEqual(parsed.telemetry.enforcement, "advisory")

    def test_minimal_strict_config_uses_sqlite(self):
        parsed = RuntimeConfig.from_mapping(minimal_config(strict=True))
        self.assertTrue(parsed.telemetry.enabled)
        self.assertEqual(parsed.telemetry.ledger, "sqlite")
        self.assertEqual(parsed.telemetry.enforcement, "strict")

    def test_init_is_atomic_and_does_not_overwrite_by_default(self):
        result = write_minimal_config(self.root)
        target = self.root / "dreamteam.config.json"
        self.assertTrue(target.is_file())
        self.assertFalse(result.replaced)
        before = target.read_bytes()
        with self.assertRaises(FileExistsError):
            write_minimal_config(self.root)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".dreamteam.config.json.*.tmp")), [])

    def test_init_force_replaces_regular_file(self):
        write_minimal_config(self.root)
        result = write_minimal_config(
            self.root,
            topology="opus-sonnet",
            profile="quality",
            strict=True,
            force=True,
        )
        self.assertTrue(result.replaced)
        parsed = RuntimeConfig.from_file(self.root / "dreamteam.config.json")
        self.assertEqual(parsed.topology.value, "opus-sonnet")
        self.assertEqual(parsed.profile.value, "quality")
        self.assertTrue(parsed.telemetry.enabled)

    def test_init_rejects_symlink_target(self):
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        target = self.root / "dreamteam.config.json"
        try:
            target.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(PermissionError):
            write_minimal_config(self.root, force=True)

    def test_doctor_missing_config_is_actionable(self):
        report = doctor(self.root)
        self.assertFalse(report.ready)
        self.assertIn("CONFIG_MISSING", {item.code for item in report.diagnostics})
        rendered = render_doctor_text(report)
        self.assertIn("STATUS|BLOCKED", rendered)
        self.assertIn("FIX|CONFIG_MISSING|Run /dreamteam:init", rendered)

    def test_doctor_advisory_config_is_ready_with_plugin_warning(self):
        write_minimal_config(self.root)
        report = doctor(self.root)
        self.assertTrue(report.ready)
        self.assertEqual(report.topology, "lean")
        self.assertIn("PLUGIN_ROOT_UNKNOWN", {item.code for item in report.diagnostics})

    def test_doctor_strict_requires_hooks(self):
        write_minimal_config(self.root, strict=True)
        report = doctor(self.root, plugin_data=self.root / "data", hooks_available=False)
        self.assertFalse(report.ready)
        self.assertIn("STRICT_HOOKS_REQUIRED", {item.code for item in report.diagnostics})

    def test_status_explains_disabled_telemetry(self):
        write_minimal_config(self.root)
        report = status(self.root)
        self.assertFalse(report.available)
        self.assertEqual(report.reason_code, "TELEMETRY_DISABLED")
        self.assertIn("STATUS|UNAVAILABLE", render_status_text(report))

    def test_status_reads_redacted_ledger_summary(self):
        write_minimal_config(self.root, strict=True)
        data = self.root / "data"
        data.mkdir()
        database = data / "ledger.sqlite"
        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE run_metadata(run_id TEXT PRIMARY KEY, config_hash TEXT NOT NULL);
                CREATE TABLE checkpoints(run_id TEXT, node_id TEXT, state TEXT, result_hash TEXT);
                CREATE TABLE reservations(run_id TEXT, node_id TEXT, usd_micros INTEGER);
                CREATE TABLE charges(run_id TEXT, node_id TEXT, usd_micros INTEGER);
                CREATE TABLE tool_events_v04(run_id TEXT, agent_id TEXT, tool_use_id TEXT, tool_name TEXT, status TEXT, metadata_hash TEXT);
                CREATE TABLE invalidations(id INTEGER PRIMARY KEY, run_id TEXT, agent_id TEXT, category TEXT, detail TEXT);
                """
            )
            connection.execute("INSERT INTO run_metadata VALUES('run-a','cfg-hash')")
            connection.execute("INSERT INTO checkpoints VALUES('run-a','worker-1','RUNNING',NULL)")
            connection.execute("INSERT INTO checkpoints VALUES('run-a','worker-2','DONE','result')")
            connection.execute("INSERT INTO reservations VALUES('run-a','worker-1',100)")
            connection.execute("INSERT INTO charges VALUES('run-a','worker-2',250)")
            connection.execute("INSERT INTO tool_events_v04 VALUES('run-a','worker-1','tool-1','Read','failed','meta')")
            connection.execute("INSERT INTO invalidations VALUES(NULL,'run-a','worker-1','tool_failure','secret-command')")
        report = status(self.root, plugin_data=data)
        self.assertTrue(report.available)
        self.assertEqual(report.run_id, "run-a")
        self.assertEqual(report.charged_usd_micros, 250)
        self.assertEqual(report.reserved_usd_micros, 100)
        self.assertEqual(report.active_workers, 1)
        self.assertEqual(report.checkpoint_counts, {"DONE": 1, "RUNNING": 1})
        self.assertEqual(report.invalidation_categories, ("tool_failure",))
        self.assertNotIn("secret-command", json.dumps(report.payload()))


if __name__ == "__main__":
    unittest.main()
