import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dreamteam.ledger import RunLedger
from dreamteam.protocol import contract_hash, validate

ROOT = Path(__file__).resolve().parents[1]

DCP = """DCP|2
RUN|r1
TASK|t1
CONST|DT-C1
PROFILE|balanced
G|map status
S+|src
T|implement
B|files=2;deep_reads=2;turns=4;records=12;retries=1
O|CHP/2
"""


class ProtocolV04Tests(unittest.TestCase):
    def test_valid_dcp_and_hash(self):
        self.assertEqual(validate(DCP), [])
        self.assertTrue(contract_hash(DCP).startswith("sha256:"))

    def test_profile_and_budget_are_validated(self):
        self.assertTrue(validate(DCP.replace("PROFILE|balanced", "PROFILE|fast")))
        self.assertTrue(validate(DCP.replace("records=12", "records=2")))

    def test_contract_binding_and_self_review(self):
        expected = contract_hash(DCP)
        chp = f"""CHP|2
RUN|r1
TASK|t1
CONTRACT|{expected}
S|DONE|ok
N|ORCHESTRATOR|review
"""
        self.assertEqual(
            validate(
                chp,
                require_contract_hash=True,
                expected_run_id="r1",
                expected_task_id="t1",
                expected_contract_hash=expected,
                author_agent_id="writer",
                reviewer_agent_id="reviewer",
            ),
            [],
        )
        errors = validate(
            chp,
            require_contract_hash=True,
            expected_contract_hash="sha256:" + "0" * 64,
            author_agent_id="same",
            reviewer_agent_id="same",
        )
        self.assertTrue(any("CONTRACT hash" in error for error in errors))
        self.assertTrue(any("different agents" in error for error in errors))

    def test_unavailable_contract_rejected_in_strict_mode(self):
        chp = """CHP|2
RUN|r
TASK|t
CONTRACT|UNAVAILABLE
S|DONE|ok
N|ORCHESTRATOR|review
"""
        self.assertTrue(validate(chp, require_contract_hash=True))

    def test_contract_hash_requires_exact_sha256(self):
        chp = """CHP|2
RUN|r
TASK|t
CONTRACT|sha256:abc
S|DONE|ok
N|ORCHESTRATOR|review
"""
        self.assertTrue(any("invalid CONTRACT hash" in error for error in validate(chp)))

    def test_output_and_next_owner_are_strict(self):
        self.assertTrue(validate(DCP.replace("O|CHP/2", "O|text")))
        expected = contract_hash(DCP)
        chp = f"""CHP|2
RUN|r1
TASK|t1
CONTRACT|{expected}
S|DONE|ok
N|WORKER:|continue
"""
        self.assertTrue(any("invalid next owner" in error for error in validate(chp)))

    def test_empty_optional_record_is_rejected(self):
        self.assertTrue(validate(DCP.replace("S+|src", "S+|")))

    def test_cli_binds_valid_dcp_to_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = root / "contract.dcp2"
            contract_path.write_text(DCP, encoding="utf-8")
            ledger_path = root / "ledger.sqlite"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/protocol_v2.py"),
                    str(contract_path),
                    "--bind",
                    "--ledger",
                    str(ledger_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            ledger = RunLedger(ledger_path)
            try:
                binding = ledger.contract_binding("r1", "t1")
                self.assertIsNotNone(binding)
                self.assertEqual(binding[0], contract_hash(DCP))
            finally:
                ledger.close()


if __name__ == "__main__":
    unittest.main()
