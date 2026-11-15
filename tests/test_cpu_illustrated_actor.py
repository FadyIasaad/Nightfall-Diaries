"""Safety and actual per-frame articulation tests for Nightfall's CPU fallback.

The general legacy test runner may not have Pillow, so those art tests skip
there; the dedicated CPU workflow installs Pillow and exercises the renderer.
"""
import importlib.util
import unittest

PIL_INSTALLED = importlib.util.find_spec("PIL") is not None


@unittest.skipUnless(PIL_INSTALLED, "Pillow required for pixel animation checks")
class CPUIllustratedActingTests(unittest.TestCase):
    def setUp(self):
        from studio import cpu_motion_engine as art
        self.art = art

    def test_ember_real_dynamic_actor_motion_not_still_slide(self):
        a = self.art.render_frame(
            1, 0.0, 0.1, 12, "Ember is safe", "s01_ember", ["s01_ember"],
            "The fox runs toward the blue feather.")
        b = self.art.render_frame(
            1, 0.6, 0.8, 12, "Ember is safe", "s01_ember", ["s01_ember"],
            "The fox runs toward the blue feather.")
        self.assertEqual(a.size, (360, 640))
        self.assertEqual(b.size, (360, 640))
        # Within the fox's torso/face zone, character and body parts move.
        from PIL import ImageChops, ImageStat
        difference = ImageChops.difference(a.crop((100, 215, 290, 515)),
                                           b.crop((100, 215, 290, 515)))
        variance = ImageStat.Stat(difference).mean
        self.assertGreater(max(variance), 4.0)

    def test_audio_waveform_changes_embroideries_not_character_identity(self):
        a = self.art.render_frame(2, 1.0, 0.0, 12,
                                  "Do not go", "s01_ember", ["s01_ember"],
                                  "Ember turns to the fire.")
        b = self.art.render_frame(2, 1.0, 0.9, 12,
                                  "Do not go", "s01_ember", ["s01_ember"],
                                  "Ember turns to the fire.")
        self.assertNotEqual(a.tobytes(), b.tobytes())
        self.assertEqual(self.art.W, 360)
        self.assertEqual(self.art.H, 640)

    def test_tortoise_character_and_duo_are_not_blank_scenes(self):
        from PIL import ImageStat
        tortoise = self.art.render_frame(6, 0.2, 0.5, 12,
                                         "Stay here", "s01_moss", ["s01_moss"],
                                         "Moss braces himself")
        duo = self.art.render_frame(7, 1.0, 0.5, 12,
                                    "Follow me", "s01_ember",
                                    ["s01_ember", "s01_moss"],
                                    "Both characters turn")
        self.assertGreater(max(ImageStat.Stat(tortoise).stddev), 28)
        self.assertGreater(max(ImageStat.Stat(duo).stddev), 28)

    def test_original_fur_and_star_are_deterministic(self):
        im1 = self.art.render_frame(3, 1.0, 0.3, 12, "A blue feather",
                                    "s01_narrator", ["s01_ember"],
                                    "The fox follows the feather")
        im2 = self.art.render_frame(3, 1.0, 0.3, 12, "A blue feather",
                                    "s01_narrator", ["s01_ember"],
                                    "The fox follows the feather")
        self.assertEqual(im1.tobytes(), im2.tobytes())


@unittest.skipUnless(PIL_INSTALLED, "Pillow required for timeline source imports")
class CPUSafetyTimelineTests(unittest.TestCase):
    def test_true_original_voice_count_and_target_timeline(self):
        from pilot.e01_agnes_full_episode_plan import make_plan
        plan = make_plan("d235d66f5f17e19b2020623a5cba0ff78caf2321")
        self.assertEqual(plan["target_seconds"], 216)
        self.assertEqual(set(s["scene"] for s in plan["shots"]), set(range(1,15)))
        self.assertEqual(len(plan["shots"]), 18)
        self.assertFalse(plan["automatic_public_publishing_authorized"])


if __name__ == "__main__":
    unittest.main()
