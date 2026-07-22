from datetime import date
import tempfile
import unittest
from pathlib import Path

from dreamteam.config import RuntimeConfig
from dreamteam.ledger import LEDGER_SCHEMA_VERSION, RunLedger
from dreamteam.operations import minimal_config
from dreamteam.pricing import MODEL_CATALOG_ID, PriceBook


class ReproducibilityV043Tests(unittest.TestCase):
    def test_unknown_pricing_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            PriceBook(date(2026, 7, 18))

    def test_catalog_hash_is_stable_and_content_addressed(self):
        first = PriceBook(date(2026, 7, 17))
        second = PriceBook.from_catalog_id(first.catalog_id)
        self.assertEqual(first.catalog_hash, second.catalog_hash)
        self.assertTrue(first.catalog_hash.startswith("sha256:"))
        self.assertEqual(MODEL_CATALOG_ID, "claude-model-aliases-v1")

    def test_effective_hash_materializes_profile_defaults(self):
        first = RuntimeConfig.from_mapping(minimal_config())
        explicit = minimal_config()
        explicit["routing"]["minimumSavingsMargin"] = 0.30
        explicit["routing"]["allowParallelIndependent"] = False
        explicit["budgets"]["maxActiveWorkers"] = 1
        explicit["budgets"]["maxRetries"] = 1
        explicit["budgets"]["maxWorkerTurns"] = 10
        second = RuntimeConfig.from_mapping(explicit)
        self.assertEqual(first.effective_hash, second.effective_hash)

    def test_ledger_schema_and_run_context_are_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.sqlite"
            ledger = RunLedger(path)
            try:
                version = ledger.connection.execute("PRAGMA user_version").fetchone()[0]
                self.assertEqual(version, LEDGER_SCHEMA_VERSION)
                self.assertTrue(
                    ledger.bind_run_context(
                        "run",
                        effective_config_hash="sha256:effective",
                        runtime_version="0.4.3",
                        pricing_catalog_id="anthropic-api-2026-07-17",
                        pricing_catalog_hash="sha256:pricing",
                        model_catalog_id=MODEL_CATALOG_ID,
                    )
                )
                self.assertFalse(
                    ledger.bind_run_context(
                        "run",
                        effective_config_hash="sha256:changed",
                        runtime_version="0.4.3",
                        pricing_catalog_id="anthropic-api-2026-07-17",
                        pricing_catalog_hash="sha256:pricing",
                        model_catalog_id=MODEL_CATALOG_ID,
                    )
                )
            finally:
                ledger.close()


if __name__ == "__main__":
    unittest.main()
