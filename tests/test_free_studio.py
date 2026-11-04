"""Safeguards runnable without paying for or importing an AI rendering service."""
import json
import os
import unittest
from unittest.mock import patch

from studio.free_video import find_video
from studio.production import next_episode
from studio.restore import ROOT
from studio.run_free import EMBER_REFERENCE, publish_blockers, setup_report, screenplay_word_count

class FreeStudioTests(unittest.TestCase):
    def test_no_slideshow_fallback(self):
        self.assertIsNone(find_video({"image": "fake.png"}))
        self.assertIsNone(find_video(["still.jpg", {"path": "nothing.mp4"}]))

    def test_first_episode_is_original(self):
        self.assertEqual(next_episode(ROOT), "S01_the_last_little_fox_E01")

    def test_tracked_ember_image_is_present(self):
        self.assertTrue(EMBER_REFERENCE.is_file())

    def test_read_only_preflight_needs_no_gradio(self):
        report = setup_report()
        self.assertEqual(report["original_scripts"], 22)
        self.assertTrue(report["episode_one_full_screenplay_ready"])
        self.assertFalse(report["reference_is_approved_motion"])

    def test_publish_defaults_blocked_even_if_live_variable_set(self):
        with patch.dict(os.environ, {"NIGHTFALL_LIVE": "true"}):
            blockers = publish_blockers()
        self.assertTrue(any("cinematic_video_approved" in x for x in blockers))
        self.assertTrue(any("public_publish_enabled" in x for x in blockers))

    def test_first_screenplay_expanded_without_replacing_archived_script(self):
        words = screenplay_word_count("S01_the_last_little_fox_E01")
        self.assertGreaterEqual(words, 400)
        self.assertLessEqual(words, 750)
        original = json.loads((ROOT / "seasons/S01_the_last_little_fox/scripts/E01.json").read_text())
        self.assertEqual(len(original["scenes"]), 4)

if __name__ == "__main__":
    unittest.main()
