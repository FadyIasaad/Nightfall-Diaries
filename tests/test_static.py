import json
import unittest
from studio.restore import ROOT, validate_stories

class SafetyTests(unittest.TestCase):
    def test_all_original_scripts(self):
        self.assertEqual(validate_stories(ROOT), 22)
    def test_no_public_posting(self):
        cfg = json.loads((ROOT / "config.json").read_text())
        self.assertFalse(cfg["public_publish_enabled"])
        self.assertFalse(cfg["automatic_new_series"])
    def test_proof_plan_is_original_and_unrendered(self):
        plan = json.loads((ROOT / "studio/proofs/ember_E01_proof_plan.json").read_text())
        script = json.loads((ROOT / plan["source_script"]).read_text())
        cast = json.loads((ROOT / plan["cast"]).read_text())
        valid_cast = {c["id"] for c in cast["characters"]}
        self.assertEqual(plan["status"], "PLAN_ONLY_NOT_RENDERED")
        self.assertTrue(plan["approval_required"])
        self.assertIsNone(plan["cloud_video_provider"])
        self.assertFalse(plan["public_publish_enabled"])
        self.assertEqual(plan["episode_id"], script["episode_id"])
        self.assertEqual(sum(s["seconds"] for s in plan["shots"]), 13.5)
        for shot in plan["shots"]:
            original = script["scenes"][shot["script_scene_index"]]
            self.assertEqual(shot["character_id"], original["character_id"])
            self.assertIn(shot["dialogue_excerpt"], original["text"])
            self.assertTrue(set(shot["visible"]).issubset(valid_cast))
    def test_workflow_not_legacy_render(self):
        wf = (ROOT / ".github/workflows/nightfall.yml").read_text()
        self.assertNotIn("studio.preview", wf)
        self.assertIn("studio.restore", wf)
if __name__ == "__main__":
    unittest.main()
