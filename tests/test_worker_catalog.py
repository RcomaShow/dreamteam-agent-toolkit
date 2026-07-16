import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'adapters/claude-code/plugins/dreamteam'

class WorkerCatalogTests(unittest.TestCase):
    def test_worker_families_and_model(self):
        files=list((PLUGIN/'agents').glob('*.md'))
        self.assertGreaterEqual(len(files),10)
        families={p.stem.split('-',1)[0] for p in files}
        self.assertEqual(families,{'discovery','execution','verification'})
        for p in files:
            text=p.read_text()
            self.assertIn('model: haiku',text)
            self.assertIn('CHP/2',text)
            self.assertNotIn('Agent,',text)
    def test_offload_profile(self):
        text=(ROOT/'core/profiles/offload.md').read_text()
        self.assertIn('main_model_tokens',text)
        self.assertIn('parallelism=off',text)

if __name__=='__main__': unittest.main()
