"""Fresh E01 216-second Agnes screenplay, identity locks, no fake progress."""
import unittest

from pilot import e01_agnes_full_episode_plan as agnes

REV = "d235d66f5f17e19b2020623a5cba0ff78caf2321"


class FreshAgnesPlan(unittest.TestCase):
    def test_new_film_216_seconds_exactly(self):
        m = agnes.make_plan(REV)
        self.assertEqual(m["model"], "agnes-video-2.5-flash")
        self.assertEqual(m["target_seconds"], 216)
        self.assertEqual(len(m["shots"]), 18)
        self.assertEqual({s["scene"] for s in m["shots"]}, set(range(1, 15)))
        self.assertEqual(sum(s["duration_seconds"] for s in m["shots"]), 216)
        self.assertEqual(m["existing_old_hf_clips_reused"], 0)
        self.assertEqual(m["voice_scene_count"], 14)
        self.assertTrue(all(s["images"] and len(s["images"]) <= 5 for s in m["shots"]))
        self.assertTrue(all(s["prompt"].find("still-camera zoom") >= 0 for s in m["shots"]))
        self.assertTrue(all("/" + REV + "/" in url for shot in m["shots"]
                            for url in shot["images"]))
        self.assertEqual(m["api_generation_requests_made"], 0)
        self.assertFalse(m["cinematic_quality_approved"])
        self.assertFalse(m["true_lipsync_approved"])
        self.assertFalse(m["automatic_public_publishing_authorized"])

    def test_any_source_commit_change_changes_plan_hash(self):
        p1 = agnes.make_plan(REV)
        p2 = agnes.make_plan("a"*40)
        self.assertNotEqual(p1["plan_sha256"], p2["plan_sha256"])

    def test_immutable_urls_only_no_path_traversal(self):
        self.assertTrue(agnes.pinned_url("assets/ember.webp", REV).endswith("ember.webp"))
        with self.assertRaises(ValueError):
            agnes.pinned_url("../../secrets.txt", REV)
        with self.assertRaises(ValueError):
            agnes.pinned_url("assets/ember.webp", "main")

    def test_ref_shas_match_disk_assets(self):
        m = agnes.make_plan(REV)
        for shot in m["shots"]:
            for r in shot["reference_hashes"]:
                self.assertEqual(len(r["sha256"]), 64)

    def test_second_shots_are_independent_story_beats(self):
        m = agnes.make_plan(REV)
        for shot in m["shots"]:
            if shot["part"] == 2:
                self.assertIn("Different original action beat", shot["prompt"])


if __name__ == "__main__":
    unittest.main()
