import unittest
from scripts.protocol_v2 import parse, validate, contract_hash, split_record, escape_field

DCP = """DCP|2
RUN|r1
TASK|t1
CONST|DT-C1
PROFILE|offload
G|map status
S+|src
T|implement
B|files=2;deep_reads=2;turns=4;records=10;retries=1
O|CHP/2
"""

class ProtocolV2Tests(unittest.TestCase):
    def test_valid_dcp(self): self.assertEqual(validate(DCP), [])
    def test_hash_stable(self): self.assertEqual(contract_hash(DCP), contract_hash(DCP))
    def test_escaping(self):
        value = "a|b\\c\n"
        self.assertEqual(split_record("X|" + escape_field(value))[1], value)
    def test_done_with_handoff_is_invalid(self):
        chp = """CHP|2
RUN|r1
TASK|t1
CONTRACT|UNAVAILABLE
S|DONE|bad
H|H1|business|X#m|decide|work
N|ORCHESTRATOR|review
"""
        self.assertTrue(any("DONE" in e for e in validate(chp)))
    def test_unknown_deduction_reference(self):
        chp = """CHP|2
RUN|r1
TASK|t1
CONTRACT|UNAVAILABLE
S|PARTIAL|x
E|E2|DEDUCTION|E1|claim
N|ORCHESTRATOR|review
"""
        self.assertTrue(any("unknown supporting" in e for e in validate(chp)))

if __name__ == '__main__': unittest.main()
