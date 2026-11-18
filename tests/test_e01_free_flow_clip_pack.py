"""Verify E01 Flow plan is a free browser prompt pack, NOT a generated video."""
import pathlib
import unittest

from pilot.e01_free_flow_clip_pack import build, main

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FreeFlowClipPackContract(unittest.TestCase):
    def test_exact_original_180s_30_distinct_clips(self):
        pack=build()
        self.assertEqual(pack["status"],"PROMPT_PACK_PREPARED_NO_VIDEO_GENERATED")
        self.assertEqual(pack["planned_clips"],30)
        self.assertEqual(pack["planned_duration_seconds"],180)
        self.assertEqual([x["seconds"] for x in pack["shots"]], [8,4]*15)
        self.assertEqual(len({x["clip_id"] for x in pack["shots"]}),30)
        self.assertEqual([x["scene"] for x in pack["shots"]],[n for n in range(1,16) for _ in range(2)])
        self.assertEqual(pack["actual_Flow_videos_generated"],0)
        self.assertFalse(pack["public_upload_permitted"])

    def test_real_cost_limit_and_no_unverified_auto_lipsync(self):
        pack=build()
        self.assertEqual(pack["assumed_free_credits_per_day"],50)
        self.assertEqual(pack["credits_per_clip"],10)
        self.assertEqual(pack["total_free_credits_single_successful_pass"],300)
        self.assertEqual(pack["optimistic_minimum_days_without_retakes"],6)
        self.assertTrue(pack["actual_account_credits_unverified"])
        self.assertFalse(pack["fully_unattended_generation"])
        self.assertTrue(pack["requires_flow_account_signin_and_web_operation"])
        self.assertTrue(pack["accurate_character_lipsync_UNVERIFIED"])
        for shot in pack["shots"]:
            self.assertFalse(shot["rendered"])
            self.assertFalse(shot["visual_approved"])
            self.assertFalse(shot["voice_synchronization_verified"])
            self.assertFalse(shot["USD_or_paid_API_charge_allowed"])
            self.assertIn("No captions",shot["prompt"])
            self.assertIn("EXACTLY ONE gold star",shot["prompt"])

    def test_pack_never_calls_a_paid_or_unauthorized_web_api(self):
        code=(ROOT/"pilot/e01_free_flow_clip_pack.py").read_text()
        for fragment in ("requests.post(", "Client(", "openai.OpenAI(", "httpx.post(", "publish_video("):
            self.assertNotIn(fragment,code)
        self.assertIn("Google Flow Veo 3.1 Lite",code)


if __name__=="__main__":
    unittest.main()
