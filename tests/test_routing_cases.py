import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RoutingCaseTests(unittest.TestCase):
    def test_cases_cover_routes_and_classes(self):
        cases=json.loads((ROOT/'evals/routing/cases.json').read_text())
        self.assertEqual({c['class'] for c in cases},{'M0','L1','L2','C3'})
        self.assertEqual({c['route'] for c in cases},{'MAIN_DIRECT','WORKER_READ','WORKER_WRITE','HYBRID_EDIT','HIGH_CAPABILITY_WORKER'})
if __name__=='__main__': unittest.main()
