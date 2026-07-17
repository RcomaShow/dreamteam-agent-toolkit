from pathlib import Path
import tempfile
import threading
import unittest

from dreamteam.ledger import ReadEvent, RunLedger


class LedgerV04Tests(unittest.TestCase):
    def test_charges_survive_release(self):
        ledger = RunLedger()
        try:
            self.assertTrue(ledger.reserve("r", "n", 60, 100))
            self.assertTrue(ledger.reconcile("r", "n", 70, 100))
            ledger.release("r", "n")
            self.assertEqual(ledger.charged("r"), 70)
            self.assertEqual(ledger.remaining("r", 100), 30)
        finally:
            ledger.close()

    def test_commit_reservation_moves_expected_cost(self):
        ledger = RunLedger()
        try:
            self.assertTrue(ledger.reserve("r", "tool", 40, 100))
            self.assertTrue(ledger.commit_reservation("r", "tool"))
            self.assertEqual(ledger.active_reservations("r"), 0)
            self.assertEqual(ledger.charged("r"), 40)
        finally:
            ledger.close()

    def test_run_config_is_immutable(self):
        ledger = RunLedger()
        try:
            self.assertTrue(ledger.bind_config("r", "a"))
            self.assertFalse(ledger.bind_config("r", "b"))
        finally:
            ledger.close()

    def test_active_reservation_cap_is_atomic(self):
        ledger = RunLedger()
        try:
            self.assertTrue(
                ledger.reserve(
                    "r", "a", 10, 100, max_active_reservations=1
                )
            )
            self.assertFalse(
                ledger.reserve(
                    "r", "b", 10, 100, max_active_reservations=1
                )
            )
            self.assertTrue(
                ledger.reserve(
                    "r", "a", 20, 100, max_active_reservations=1
                )
            )
        finally:
            ledger.close()

    def test_terminal_checkpoint_cannot_regress(self):
        ledger = RunLedger()
        try:
            ledger.checkpoint("r", "n", "RUNNING")
            ledger.checkpoint("r", "n", "DONE")
            with self.assertRaises(ValueError):
                ledger.checkpoint("r", "n", "RUNNING")
        finally:
            ledger.close()

    def test_tool_events_are_correlated_and_idempotent(self):
        ledger = RunLedger()
        try:
            self.assertTrue(
                ledger.record_tool_event("r", "a", "tool-1", "Read", "requested", "h")
            )
            self.assertFalse(
                ledger.record_tool_event("r", "a", "tool-1", "Read", "requested", "h")
            )
            self.assertTrue(
                ledger.record_tool_event("r", "a", "tool-1", "Read", "completed", "h")
            )
        finally:
            ledger.close()

    def test_contract_identities_are_claimed_once_and_prevent_self_review(self):
        ledger = RunLedger()
        try:
            digest = "sha256:" + "c" * 64
            self.assertTrue(ledger.bind_contract("r", "task", digest))
            self.assertTrue(
                ledger.claim_contract_identity(
                    "r", "task", role="author", agent_id="writer"
                )
            )
            self.assertFalse(
                ledger.claim_contract_identity(
                    "r", "task", role="reviewer", agent_id="writer"
                )
            )
            self.assertTrue(
                ledger.claim_contract_identity(
                    "r", "task", role="reviewer", agent_id="reviewer"
                )
            )
            self.assertFalse(
                ledger.claim_contract_identity(
                    "r", "task", role="reviewer", agent_id="other"
                )
            )
            self.assertEqual(
                ledger.contract_binding("r", "task"),
                (digest, "writer", "reviewer"),
            )
        finally:
            ledger.close()

    def test_contract_bindings_are_immutable_and_separate_reviewers(self):
        ledger = RunLedger()
        try:
            digest = "sha256:" + "a" * 64
            self.assertTrue(
                ledger.bind_contract(
                    "r", "task", digest, author_agent_id="writer", reviewer_agent_id="reviewer"
                )
            )
            self.assertEqual(
                ledger.contract_binding("r", "task"),
                (digest, "writer", "reviewer"),
            )
            self.assertFalse(
                ledger.bind_contract(
                    "r", "task", "sha256:" + "b" * 64, author_agent_id="writer", reviewer_agent_id="reviewer"
                )
            )
            with self.assertRaises(ValueError):
                ledger.bind_contract(
                    "r", "self", digest, author_agent_id="same", reviewer_agent_id="same"
                )
        finally:
            ledger.close()

    def test_staged_read_commits_only_when_blob_is_stable(self):
        ledger = RunLedger()
        try:
            event = ReadEvent(
                "r", "worker", "worker", "src/a.py", "blob-a", 0, 10, "explore"
            )
            ledger.stage_read("read-1", event)
            self.assertEqual(ledger.pending_read("r", "read-1"), event)
            self.assertTrue(
                ledger.commit_staged_read(
                    "r", "read-1", current_blob_id="blob-a"
                )
            )
            self.assertIsNone(ledger.pending_read("r", "read-1"))
            self.assertEqual(ledger.main_reread_ratio("r"), 0.0)
        finally:
            ledger.close()

    def test_staged_read_rejects_blob_change_and_can_be_discarded(self):
        ledger = RunLedger()
        try:
            event = ReadEvent(
                "r", "worker", "worker", "src/a.py", "blob-a", 0, 10, "explore"
            )
            ledger.stage_read("read-2", event)
            self.assertFalse(
                ledger.commit_staged_read(
                    "r", "read-2", current_blob_id="blob-b"
                )
            )
            self.assertIsNone(ledger.pending_read("r", "read-2"))
            ledger.stage_read("read-3", event)
            ledger.discard_staged_read("r", "read-3")
            self.assertIsNone(ledger.pending_read("r", "read-3"))
        finally:
            ledger.close()

    def test_two_connections_cannot_overbook_charged_plus_reserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            first = RunLedger(db)
            second = RunLedger(db)
            first.reconcile("r", "already", 30, 100)
            barrier = threading.Barrier(2)
            results = []

            def reserve(ledger, node):
                barrier.wait()
                results.append(ledger.reserve("r", node, 50, 100))

            threads = [
                threading.Thread(target=reserve, args=(first, "a")),
                threading.Thread(target=reserve, args=(second, "b")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(results), [False, True])
            first.close()
            second.close()


if __name__ == "__main__":
    unittest.main()
