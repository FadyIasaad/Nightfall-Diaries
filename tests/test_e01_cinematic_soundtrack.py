"""E01 complete soundtrack contract, without pretending audio is a finished film."""
import json
import pathlib
import unittest

from pilot import e01_cinematic_soundtrack as soundtrack

ROOT=pathlib.Path(__file__).resolve().parents[1]


class OriginalSoundtrackTests(unittest.TestCase):
    def test_full_canonical_180s_locked_story(self):
        scenes,cast=soundtrack.validate_story()
        self.assertEqual(len(scenes),15)
        self.assertEqual(sum(x["target_seconds"] for x in scenes),180)
        self.assertEqual([x["scene"] for x in scenes],list(range(1,16)))
        self.assertEqual(len({x["text"] for x in scenes}),15)
        self.assertTrue(all("voice" in cast[x["character_id"]] for x in scenes))
        self.assertEqual(cast["s01_ember"]["voice"]["voice_id"],"am_puck")
        self.assertEqual(cast["s01_moss"]["voice"]["voice_id"],"bm_george")
        self.assertEqual(cast["s01_narrator"]["voice"]["voice_id"],"bf_emma")
    def test_guard_no_hidden_charge_or_fake_movie(self):
        source=pathlib.Path(soundtrack.__file__).read_text(encoding="utf-8")
        self.assertIn("PAID_INFERENCE_SECRET_PRESENT_REFUSE_THIS_JOB",source)
        self.assertIn("FULL_180S_AUDIO_TRACK_READY_VISUAL_VIDEO_NOT_PRODUCED",source)
        self.assertIn('"all_45_cinematic_video_shots_rendered":False',source)
        self.assertIn('"accurate_animal_lipsync_verified":False',source)
        self.assertIn('"new_public_release":False',source)
        for bad in ("Client(", "publish_video(", "runwayml", "gradio_client"):
            self.assertNotIn(bad,source)
    def test_atmosphere_stereo_and_nonaligned_padding(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("Only tests numpy DSP on dedicated soundtrack worker")
        samples=soundtrack.atmosphere(1,2400,np)
        self.assertEqual(samples.shape,(2400,2))
        self.assertTrue(np.isfinite(samples).all())
        self.assertGreater(float(np.sqrt((samples**2).mean())),.001)

if __name__=="__main__":
    unittest.main()
