"""Offline tests for all-scene Nightfall storyboards (no publishing)."""
import tempfile
import unittest
from pathlib import Path

from importlib.util import find_spec

# Generic repository CI intentionally does not install heavyweight art packages.
# Dedicated V3 render CI installs Pillow and executes the full visual tests.
PIL_AVAILABLE = find_spec("PIL") is not None
if PIL_AVAILABLE:
    from PIL import Image, ImageDraw
    from studio.e01_visual_review import audit
else:
    Image = ImageDraw = audit = None


@unittest.skipUnless(PIL_AVAILABLE, "Pillow not installed in lightweight repository CI")
class VisualReviewTests(unittest.TestCase):
    def make_stills(self, folder):
        for n in range(1, 15):
            im = Image.new("RGB", (360, 640))
            d = ImageDraw.Draw(im)
            for y in range(640):
                d.line((0, y, 359, y), fill=((n * 17 + y) % 256,
                       (n * 23 + y // 2) % 256, (n * 31 + y // 3) % 256))
            im.save(folder / f"scene_{n:02d}_still.png")

    def test_complete_board_and_conservative_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_stills(root)
            r = audit(root)
            self.assertEqual(r["found_scenes"], 14)
            self.assertFalse(r["ember_reference_quality_equivalence_verified"])
            self.assertFalse(r["public_publishing_authorized"])
            self.assertTrue((root / "e01_all_14_scenes_storyboard.jpg").exists())

    def test_missing_scene_blocks_full_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_stills(root)
            (root / "scene_14_still.png").unlink()
            with self.assertRaisesRegex(RuntimeError, "INCOMPLETE_STORYBOARD"):
                audit(root)


if __name__ == "__main__":
    unittest.main()
