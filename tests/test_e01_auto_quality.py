"""Regression tests for objective free E01 AI video candidate ranking."""
import unittest
from pilot import e01_auto_quality as q


def make_frame(r,g,b):
    return bytes((r,g,b))*q.PIXELS


class ObjectiveAutoRankTests(unittest.TestCase):
    def test_identical_frames_are_rejected_as_static(self):
        data=q.measure([make_frame(70,70,70)]*4)
        self.assertIn("WEAK_FRAME_MOTION",data["machine_flags"])
        self.assertFalse(data["passes_basic_machine_motion_gate"])
        self.assertFalse(data["natural_animal_lip_sync_verified"])
        self.assertFalse(data["public_publish_approved"])
    def test_all_black_frames_fail(self):
        data=q.measure([make_frame(0,0,0)]*4)
        self.assertIn("LARGE_DARK_SCREEN_FRACTION",data["machine_flags"])
        self.assertFalse(data["passes_basic_machine_motion_gate"])
    def test_requires_four_real_frames(self):
        with self.assertRaisesRegex(RuntimeError,"FOUR_REAL_VIDEO_FRAMES"):
            q.measure([make_frame(55,55,55)]*2)
    def test_quality_output_does_not_claim_semantic_approval(self):
        rows=[make_frame(i,250-i,80) for i in (10,130,220,40)]
        result=q.measure(rows)
        self.assertIn("score_0_to_100",result)
        for key in ("source_framing_or_background_story_semantics_verified",
                    "characters_and_accessories_verified",
                    "no_text_or_ui_artifacts_semantically_verified",
                    "natural_animal_lip_sync_verified","public_publish_approved"):
            self.assertFalse(result[key])
