import unittest
from studio.auto_prepare import prepare

class AutomaticPreparationTests(unittest.TestCase):
    def test_ember_prepares_whole_cast_without_signoffs(self):
        p = prepare("S01_the_last_little_fox_E01")
        self.assertEqual(len(p["character_jobs"]), 4)
        self.assertEqual(len(p["voice_jobs"]), 5)
        self.assertEqual(len(p["shot_jobs"]), 3)
        self.assertFalse(p["per_character_manual_approval_required"])
        self.assertTrue(p["first_actual_cinematic_mp4_requires_owner_approval"])
        self.assertFalse(p["auto_publish_enabled"])
        self.assertEqual(p["status"], "PREPRODUCTION_ONLY_NO_MP4")
    def test_second_original_series(self):
        p = prepare("S02_the_boy_who_forgot_tomorrow_E01")
        self.assertEqual(len(p["shot_jobs"]), 4)
    def test_unapproved_story_is_blocked(self):
        with self.assertRaises(ValueError):
            prepare("S03_other_series_E01")
        with self.assertRaises(ValueError):
            prepare("../../secrets")
