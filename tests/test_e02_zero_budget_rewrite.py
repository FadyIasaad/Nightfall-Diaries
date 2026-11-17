"""$0 screenplay integrity and no-hidden-publishing contract."""
import json
import pathlib
import unittest
from pilot import e02_real_i2v_proof as exp

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"seasons/S01_the_last_little_fox/revised_screenplays/E02_2026-11-18.json"
STORY=ROOT/"docs/NIGHTFALL_22_EPISODE_STORY_REWRITE_2026-11-18.md"

class E02RewriteZeroBudgetTests(unittest.TestCase):
    def test_cinematic_script_is_original_complete_and_continuous(self):
        s=json.loads(SCRIPT.read_text(encoding="utf-8"))
        self.assertEqual(s["episode_id"],"S01_the_last_little_fox_E02")
        self.assertEqual(s["status"],"REWRITTEN_SCREENPLAY_NOT_RENDERED")
        self.assertEqual(len(s["scenes"]),15)
        self.assertEqual(sum(x["seconds"] for x in s["scenes"]),180)
        self.assertEqual([x["scene_no"] for x in s["scenes"]],list(range(1,16)))
        self.assertEqual(sum(len(x["clip_plan"]) for x in s["scenes"]),45)
        self.assertTrue(all(sum(c["seconds"] for c in x["clip_plan"])==x["seconds"] for x in s["scenes"]))
        self.assertTrue(all(c["must_move"] for x in s["scenes"] for c in x["clip_plan"]))
        self.assertTrue(all(x["visible"] and x["filmic_action"] and x["location"] for x in s["scenes"]))
        self.assertEqual(set(x["character_id"] for x in s["scenes"]),
                         {"s01_narrator","s01_ember","s01_moss","s01_luma"})
        self.assertFalse(s["production_rules"]["public_upload_allowed"])
        self.assertTrue(s["production_rules"]["dialogue_boxes_prohibited"])

    def test_22_episode_rewrite_preserves_canon_resolutions(self):
        txt=STORY.read_text(encoding="utf-8")
        self.assertIn("12 episodes",txt)
        self.assertIn("10 episodes",txt)
        self.assertIn("faulty signal lantern",txt)
        self.assertIn("losing future visions",txt)
        self.assertIn("no glasses",txt.lower())
        self.assertIn("single",txt.lower())

    def test_free_and_not_auto_published(self):
        self.assertEqual(exp.SPACE,"Lightricks/LTX-2-3")
        self.assertEqual(exp.API,"/generate_video")
        self.assertEqual(len(exp.REFERENCE_SHA256),64)
        self.assertTrue("NO dialogue" not in exp.PROMPT)
        code=pathlib.Path(exp.__file__).read_text()
        self.assertIn("REFUSE_PROVIDER_KEY_TO_AVOID_UNVERIFIED_CHARGES",code)
        self.assertIn("False",code)
        self.assertNotIn("publish_video(",code)

if __name__=="__main__":
    unittest.main()
