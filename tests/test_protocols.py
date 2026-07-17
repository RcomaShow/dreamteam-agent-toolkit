import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ProtocolTests(unittest.TestCase):
    def test_dcp2_template_prefixes(self):
        text=(ROOT/'core/templates/dcp2.txt').read_text()
        for prefix in ('DCP|2','RUN|','TASK|','CONST|','G|','S+|','E+|','T|','R|','V|','B|','O|CHP/2'):
            self.assertIn(prefix,text)
    def test_chp2_template_prefixes(self):
        text=(ROOT/'core/templates/chp2.txt').read_text()
        for prefix in ('CHP|2','RUN|','TASK|','CONTRACT|','S|','E|','H|','V|','N|'):
            self.assertIn(prefix,text)

if __name__=='__main__': unittest.main()
