"""Contract tests: entirely new real-video test must never accept 2.5D or publish."""
import pathlib
import unittest
from pilot import ltx23_real_scene_proof as proof


class RealVideoProofContract(unittest.TestCase):
    def test_only_free_anonymous_single_candidate(self):
        self.assertEqual(proof.SPACE,"Lightricks/LTX-2-3")
        self.assertEqual(proof.ENDPOINT,"/generate_video")
        code=pathlib.Path(proof.__file__).read_text()
        self.assertIn('REFUSE_CONNECTED_PAID_OR_AUTHENTICATED_PROVIDER_TOKENS',code)
        self.assertIn('args.mode=="generate"',code)
        self.assertNotIn("publish_youtube(",code)
        self.assertNotIn("publish_instagram(",code)
        self.assertNotIn("publish_facebook(",code)
        self.assertNotIn("publish_tiktok(",code)

    def test_full_scene_not_dialogue_card_or_cutout(self):
        p=proof.PROMPT.lower()
        for phrase in ("volumetric smoke","plants his paws",
                       "no dialogue box","no subtitles","pasted sprites",
                       "exactly one small golden star"):
            self.assertIn(phrase,p)
        self.assertNotIn("blinking png",p)

    def test_media_gate_fails_closed_without_ffprobe_or_valid_video(self):
        with self.assertRaises((FileNotFoundError,RuntimeError)):
            proof.technical_check("definitely_missing_ltx_movie.mp4")


if __name__=="__main__":
    unittest.main()
