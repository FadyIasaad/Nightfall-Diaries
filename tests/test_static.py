import json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RebuildTests(unittest.TestCase):
 def test_config_is_safe(self):
  c=json.loads((ROOT/'config.json').read_text());self.assertFalse(c['public_publish_enabled']);self.assertFalse(c['automatic_new_series'])
 def test_workflow_single(self):self.assertEqual(len(list((ROOT/'.github/workflows').glob('*.yml'))),1)
 def test_original_source_pinned(self):self.assertIn('02f426cb', (ROOT/'studio/restore.py').read_text())
if __name__=='__main__':unittest.main()
