from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.protocol_v2 import contract_hash, escape_field, split_record, validate
from dreamteam.anchors import make_file_anchor

DCP = """DCP|2
RUN|r1
TASK|t1
CONST|DT-C1
PROFILE|balanced
G|map status
S+|src
T|implement
B|files=2;deep_reads=2;turns=4;records=10;retries=1
O|CHP/2
"""


class ProtocolV2Tests(unittest.TestCase):
    def test_valid_dcp_and_stable_hash(self):
        self.assertEqual(validate(DCP), [])
        self.assertEqual(contract_hash(DCP), contract_hash(DCP))

    def test_escaping(self):
        value = "a|b\\c\n"
        self.assertEqual(split_record("X|" + escape_field(value))[1], value)

    def test_required_anchor_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "x.txt").write_text("a\nb\n", encoding="utf-8")
            anchor = make_file_anchor(root, "x.txt", 1, 1).encode()
            chp = f"""CHP|2
RUN|r
TASK|t
CONTRACT|UNAVAILABLE
S|DONE|ok
E|E1|FACT|{anchor}|claim
N|ORCHESTRATOR|review
"""
            self.assertEqual(validate(chp, require_anchors=True, repo_root=root), [])
            (root / "x.txt").write_text("A\nb\n", encoding="utf-8")
            self.assertTrue(any("stale" in error for error in validate(chp, require_anchors=True, repo_root=root)))

    def test_fact_without_anchor_is_rejected_in_strict_mode(self):
        chp = """CHP|2
RUN|r
TASK|t
CONTRACT|UNAVAILABLE
S|DONE|ok
E|E1|FACT|x.py|claim
N|ORCHESTRATOR|review
"""
        self.assertTrue(validate(chp, require_anchors=True, repo_root=Path(".")))


if __name__ == "__main__":
    unittest.main()
