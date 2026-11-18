"""Genuine E01 one-shot/day proof and $0 storage safety contract."""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from pilot import e01_free_ai_studio as s


class FreeAIStudioTests(TestCase):
    def test_story_real_motion_shot_plan_uses_all_15_scenes_once(self):
        shots=s.plan()
        self.assertEqual(len(shots),45)
        self.assertEqual(len({x["id"] for x in shots}),45)
        self.assertEqual([x["scene"] for x in shots],[
            i for i in range(1,16) for _ in range(3)])
        self.assertEqual([x["shot"] for x in shots],[1,2,3]*15)
        self.assertEqual(sum(x["seconds"] for x in shots),180)
        self.assertIn("NO social-media overlays",shots[0]["prompt"])
        self.assertIn("exactly ONE GOLD STAR",shots[0]["prompt"])
        self.assertIn("Full cinematic FOREST WORLD",shots[0]["prompt"])

    def test_source_image_sha_and_no_paid_provider(self):
        self.assertTrue(s.EMBER.exists())
        self.assertEqual(s.sha(s.EMBER),s.EMBER_SHA)
        with patch.dict(os.environ, {"GITHUB_REF":"refs/heads/main",
                                     "HF_TOKEN":"unsafe-billed-token"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"BILLABLE_OR_ACCOUNT_AUTH"):
                s.guarantee_zero_paid_inference()
        with patch.dict(os.environ, {"GITHUB_REF":"refs/heads/main"},clear=True):
            s.guarantee_zero_paid_inference()

    def test_if_quota_exhausted_no_repeat_same_day(self):
        snapshots=[]
        with tempfile.TemporaryDirectory() as td, \
             patch.object(s,"OUT",Path(td)), \
             patch.object(s,"ensure_private_draft"), \
             patch.object(s,"read_state",return_value=s.empty_state()), \
             patch.object(s,"draft_release_available",return_value=True), \
             patch.object(s,"clip_in_draft",return_value=False), \
             patch.object(s,"persist_state",
                          side_effect=lambda state:snapshots.append(json.loads(json.dumps(state)))), \
             patch.object(s,"generate_once",
                          side_effect=RuntimeError("You have exceeded your ZeroGPU runs limit")) as generator, \
             patch.dict(os.environ,{"GITHUB_REF":"refs/heads/main","GH_TOKEN":"fake_test_only"},
                        clear=True):
            actual=s.run("generate")
            self.assertEqual(generator.call_count,1)
            self.assertEqual(actual["status"],"BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY")
            self.assertEqual(actual["last_attempt_cairo_date"],s.now_cairo().date().isoformat())
            self.assertEqual(actual["completed_technical_shots"],[])
            self.assertFalse(actual["public_uploads"])
            self.assertEqual(actual["paid_inference_requests"],0)
            self.assertGreaterEqual(len(snapshots),2)
            self.assertEqual(snapshots[0]["status"],"FREE_GPU_REQUEST_SUBMITTED")

    def test_saved_daily_attempt_is_never_retried(self):
        state=s.empty_state()
        state["last_attempt_cairo_date"]=s.now_cairo().date().isoformat()
        with tempfile.TemporaryDirectory() as td, \
             patch.object(s,"OUT",Path(td)), \
             patch.object(s,"ensure_private_draft"), \
             patch.object(s,"read_state",return_value=state), \
             patch.object(s,"generate_once") as gpu, \
             patch.dict(os.environ,{"GITHUB_REF":"refs/heads/main","GH_TOKEN":"fake_test_only"},
                        clear=True):
            out=s.run("generate")
            self.assertEqual(out["status"],"ALREADY_TRIED_ONE_FREE_GPU_CALL_TODAY")
            gpu.assert_not_called()

    def test_audit_does_not_touch_gpu_or_github_draft(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(s,"OUT",Path(td)), \
             patch.object(s,"generate_once") as model, \
             patch.object(s,"ensure_private_draft") as drafts:
            r=s.run("audit")
            self.assertIn("PLAN_VALIDATED",r["status"])
            self.assertTrue((Path(td)/"studio_state.json").is_file())
            model.assert_not_called()
            drafts.assert_not_called()

    def test_no_shot_fake_approval_or_social_upload(self):
        script=Path(s.__file__).read_text(encoding="utf-8")
        self.assertIn('"human_visual_approval":False',script)
        self.assertIn('"original_Kokoro_speech_lipsync_approved":False',script)
        self.assertIn('"public_uploads":False',script)
        self.assertIn("--draft",script)
        self.assertIn("REFUSE_NON_DRAFT_RELEASE_PUBLIC_EXPOSURE",script)
        for forbidden in ("youtube.videos().insert","facebook.com/v25.0","instagram_content_publish",
                          "ElevenLabsClient(", "gen_4_video(", "bpy.ops.render"):
            self.assertNotIn(forbidden,script)
