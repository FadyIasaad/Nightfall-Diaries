"""V4 cinematic art candidate QA (skip in lightweight CI without art packages)."""
import importlib.util
import unittest

ART_AVAILABLE = all(importlib.util.find_spec(n) is not None
                    for n in ("PIL", "numpy", "cv2"))


@unittest.skipUnless(ART_AVAILABLE, "V4 art workflow installs Pillow, NumPy and OpenCV")
class V4ArtTests(unittest.TestCase):
    def test_all_14_distinct_sets_and_editorial_staging(self):
        from studio.e01_v4_art_direction import SETS, STAGING, painted_set
        from PIL import ImageChops, ImageStat
        self.assertEqual(set(SETS), set(range(1, 15)))
        self.assertEqual(set(STAGING), set(SETS))
        self.assertEqual(len({v[0] for v in STAGING.values()}), 14)
        a = painted_set(1).convert("RGB")
        b = painted_set(12).convert("RGB")
        self.assertEqual(a.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(a,b)).mean), 12)

    def test_actor_and_feather_are_independently_moving(self):
        from studio.e01_v4_art_direction import frame
        from PIL import ImageChops, ImageStat
        first=frame(3,.20,.15,8,"This feather is glowing",
                    "s01_ember",["s01_ember"],"Ember discovers the feather")
        second=frame(3,.86,.85,8,"This feather is glowing",
                     "s01_ember",["s01_ember"],"Ember discovers the feather")
        self.assertEqual(first.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(first,second)).mean),.25)

    def test_moss_dual_shot_has_textured_visible_actor(self):
        from studio.e01_v4_art_direction import frame
        from PIL import ImageStat
        f=frame(7,.4,.6,8,"We must leave the fire",
                "s01_moss",["s01_ember","s01_moss"],"Moss warns Ember")
        self.assertEqual(f.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(f).stddev),22)

    def test_no_publication_or_legacy_renderer_overwrite(self):
        from pilot import e01_v4_cinematic
        from pathlib import Path
        p=Path(e01_v4_cinematic.__file__).read_text()
        self.assertIn("nightfall_e01_v4_cinematic",p)
        self.assertIn('"public_uploads": False',p)
        self.assertIn('"human_art_approval_pending": True',p)
        self.assertNotIn("studio.crosspost",p)


if __name__ == "__main__":
    unittest.main()
