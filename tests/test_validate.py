import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'adapters/claude-code/plugins/dreamteam'
class StructureTests(unittest.TestCase):
    def test_validator(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/validate.py')],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_marketplace_source_exists(self):
        market=json.loads((ROOT/'.claude-plugin/marketplace.json').read_text())
        for entry in market['plugins']: self.assertTrue((ROOT/entry['source']).exists())
    def test_plugin_version(self):
        manifest=json.loads((PLUGIN/'.claude-plugin/plugin.json').read_text())
        self.assertEqual(manifest['version'],'0.2.0')
    def test_workers_use_v2_and_safe_fields(self):
        for path in (PLUGIN/'agents').glob('*.md'):
            text=path.read_text(); self.assertIn('CHP/2',text)
            for field in ('permissionMode:','mcpServers:','hooks:'): self.assertNotIn(field,text)
if __name__=='__main__': unittest.main()
