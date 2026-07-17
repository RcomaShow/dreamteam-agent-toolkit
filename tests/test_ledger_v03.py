from pathlib import Path
import tempfile
import threading
import unittest

from dreamteam.ledger import ReadEvent, RunLedger


class LedgerTests(unittest.TestCase):
    def test_unique_overlap_does_not_dilute_across_workers(self):
        ledger = RunLedger()
        try:
            for agent in ("w1", "w2", "w3"):
                ledger.record_read(ReadEvent("r", agent, "worker", "a.py", "blob", 0, 100, "explore"))
            ledger.record_read(ReadEvent("r", "main", "main", "a.py", "blob", 0, 100, "verify"))
            self.assertEqual(ledger.main_reread_ratio("r"), 1.0)
        finally:
            ledger.close()

    def test_large_main_read_counts_only_real_intersection(self):
        ledger = RunLedger()
        try:
            ledger.record_read(ReadEvent("r", "w", "worker", "a.py", "blob", 100, 110, "explore"))
            ledger.record_read(ReadEvent("r", "main", "main", "a.py", "blob", 0, 1000, "verify"))
            self.assertEqual(ledger.main_reread_ratio("r"), 1.0)
        finally:
            ledger.close()

    def test_partial_worker_spans_are_unioned(self):
        ledger = RunLedger()
        try:
            ledger.record_read(ReadEvent("r", "w1", "worker", "a", "b", 0, 100, "explore"))
            ledger.record_read(ReadEvent("r", "w2", "worker", "a", "b", 50, 150, "explore"))
            ledger.record_read(ReadEvent("r", "main", "main", "a", "b", 75, 125, "verify"))
            self.assertAlmostEqual(ledger.main_reread_ratio("r"), 50 / 150)
        finally:
            ledger.close()

    def test_replace_release_reconcile_and_remaining(self):
        ledger = RunLedger()
        try:
            self.assertTrue(ledger.reserve("r", "n1", 60, 100))
            self.assertTrue(ledger.reserve("r", "n1", 50, 100))
            self.assertEqual(ledger.remaining("r", 100), 50)
            self.assertTrue(ledger.reconcile("r", "n1", 70, 100))
            ledger.release("r", "n1")
            self.assertEqual(ledger.remaining("r", 100), 30)
        finally:
            ledger.close()

    def test_two_connections_cannot_overbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.sqlite"
            first = RunLedger(db)
            second = RunLedger(db)
            barrier = threading.Barrier(2)
            results = []
            def reserve(ledger, node):
                barrier.wait()
                results.append(ledger.reserve("r", node, 60, 100))
            threads = [threading.Thread(target=reserve, args=(first, "a")), threading.Thread(target=reserve, args=(second, "b"))]
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            self.assertEqual(sorted(results), [False, True])
            first.close(); second.close()

    def test_invalid_event_rejected(self):
        with self.assertRaises(ValueError):
            ReadEvent("r", "a", "other", "x", "b", 0, 1, "tool")
        with self.assertRaises(ValueError):
            ReadEvent("r", "a", "main", "x", "b", 1, 1, "tool")


if __name__ == "__main__":
    unittest.main()
