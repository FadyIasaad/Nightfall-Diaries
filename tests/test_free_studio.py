import unittest
from studio.free_video import find_video
from studio.production import next_episode
from studio.restore import ROOT

class FreeStudioTests(unittest.TestCase):
    def test_no_slideshow_fallback(self):
        self.assertIsNone(find_video({"image": "fake.png"}))
        self.assertIsNone(find_video(["still.jpg", {"path": "nothing.mp4"}]))
    def test_default_still_original_episode_one(self):
        self.assertEqual(next_episode(ROOT), "S01_the_last_little_fox_E01")
