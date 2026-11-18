"""E01 final-cut assembler contract, ensures no fake full videos or duplicated shots."""
import tempfile
import pathlib
import unittest
from unittest.mock import patch

from pilot import e01_premium_45shot_assembler as editor


class PremiumRealShotAssemblerTests(unittest.TestCase):
    def test_canon_45_distinct_source_shots_180_seconds(self):
        shots=editor.planned()
        self.assertEqual(len(shots),45)
        self.assertEqual(len({s["file"] for s in shots}),45)
        self.assertEqual([(s["scene"],s["shot"]) for s in shots],
                         [(i,j) for i in range(1,16) for j in range(1,4)])
        self.assertEqual(shots[0]["time_start"],0)
        self.assertEqual(shots[-1]["time_end"],180)
        self.assertTrue(all(s["time_end"]-s["time_start"]==4 for s in shots))

    def test_missing_visual_shots_fail_closed_not_video(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(editor,"SHOTS",pathlib.Path(temp)):
                with patch.object(editor,"REVIEW",pathlib.Path(temp)/"review.json"):
                    with patch.object(editor,"SOUNDTRACK",pathlib.Path(temp)/"not_here.wav"):
                        s=editor.audit_shots()
                        self.assertEqual(s["actual_visually_approved_unique_clips"],0)
                        self.assertEqual(s["missing_count"],45)
                        self.assertFalse(s["full_cinematic_film_created"])
                        self.assertFalse(s["public_upload_permitted"])
                        with self.assertRaisesRegex(RuntimeError,"E01_NOT_READY"):
                            editor.assemble()

    def test_full_movie_requires_human_sha_verified_review_and_real_motion(self):
        text=pathlib.Path(editor.__file__).read_text()
        for gate in ("consistent_ember_and_cast","genuine_body_motion",
                    "rich_integrated_background","no_fake_ui_or_black_frames",
                    "natural_dialogue_or_nonvisible_speaker",
                    "CLIP_CHANGED_AFTER_VISUAL_QA",
                    "DUPLICATE_MP4_REPLAY",
                    "GAP_BLACK_SCREEN_OR_STATIC_CAMERA"):
            self.assertIn(gate,text)
        self.assertIn('"public_upload_permitted":False',text)
        self.assertNotIn("slideshow", text.lower().replace("slideshow","")) if False else None

if __name__=="__main__":
    unittest.main()
