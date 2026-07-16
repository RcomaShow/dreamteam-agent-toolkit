import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ProtocolTests(unittest.TestCase):
    def test_contract_template_prefixes(self):
        text = (ROOT / "core/templates/delegation-contract.txt").read_text()
        for prefix in ("G|", "S+|", "S-|", "T|", "R|", "V|", "B|", "O|"):
            self.assertIn(prefix, text)

    def test_handoff_template_prefixes(self):
        text = (ROOT / "core/templates/handoff.txt").read_text()
        for prefix in ("S|", "C|", "F|", "D|", "U|", "H|", "V|", "N|"):
            self.assertIn(prefix, text)

if __name__ == "__main__":
    unittest.main()
