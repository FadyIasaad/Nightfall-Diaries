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
        self.assertIn("Absolutely NO text",shots[0]["prompt"])
        self.assertIn("exactly ONE golden star",shots[0]["prompt"])
        self.assertIn("body length across the environment",shots[0]["prompt"])

    def test_true_approved_fire_reference_used_for_opening_scenes(self):
        shots=s.plan()
        self.assertTrue(s.FIRE_REFERENCE.is_file())
        self.assertEqual(s.sha(s.FIRE_REFERENCE),s.FIRE_REFERENCE_SHA)
        self.assertEqual({x["reference_source"] for x in shots if x["scene"]<=6},
                         {"approved_firestorm"})
        self.assertEqual({x["reference_source"] for x in shots if x["scene"]>6},
                         {"original_ember"})
        self.assertIn("KEEP THE COMPLETE FOX INSIDE THE",shots[0]["prompt"])
        self.assertIn("clearly BURNING FOREST",shots[0]["prompt"])

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
            with patch("builtins.print") as captured:
                actual=s.run("generate")
            self.assertEqual(generator.call_count,1)
            self.assertTrue(captured.called)
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
            with patch("builtins.print"):
                out=s.run("generate")
            self.assertEqual(out["status"],"ALREADY_TRIED_ONE_FREE_GPU_CALL_TODAY")
            gpu.assert_not_called()

    def test_explicit_owner_extra_one_use_only_on_nov19_no_paid_fallback(self):
        state=s.empty_state()
        state["last_attempt_cairo_date"]="2026-11-19"
        # Fixed-date authorization must be non-operational on every other date.
        with tempfile.TemporaryDirectory() as td, \
             patch.object(s,"OUT",Path(td)), \
             patch.object(s,"ensure_private_draft"), \
             patch.object(s,"read_state",return_value=state), \
             patch.object(s,"clip_in_draft",return_value=False), \
             patch.object(s,"persist_state"), \
             patch.object(s,"now_cairo") as clock, \
             patch.object(s,"generate_once",
                          side_effect=RuntimeError("not enough gpu quota")) as gpu, \
             patch.dict(os.environ,{"GITHUB_REF":"refs/heads/main",
                                    "GITHUB_EVENT_NAME":"push",
                                    "GH_TOKEN":"test_dummy",
                                    "SINGLE_USE_OWNER_EXTRA_ID":"owner_2026_11_19_one_extra_4s"},
                        clear=True):
            from datetime import datetime
            from zoneinfo import ZoneInfo
            clock.return_value=datetime(2026,11,19,0,45,tzinfo=ZoneInfo("Africa/Cairo"))
            with patch("builtins.print") as captured:
                first=s.run("generate")
            self.assertEqual(gpu.call_count,1)
            self.assertTrue(captured.called)
            self.assertEqual(first["status"],"BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY")
            self.assertEqual(first["one_time_manual_extra_ids"],["owner_2026_11_19_one_extra_4s"])
            with patch("builtins.print"):
                second=s.run("generate")
            self.assertEqual(gpu.call_count,1)
            self.assertEqual(second["status"],"ALREADY_TRIED_ONE_FREE_GPU_CALL_TODAY")
            clock.return_value=datetime(2026,11,20,0,45,tzinfo=ZoneInfo("Africa/Cairo"))
            with patch.dict(os.environ,{"SINGLE_USE_OWNER_EXTRA_ID":"invalid"},clear=False):
                # Tomorrow's normal daily allowance works independently,
                # but the expired one-time ID cannot bypass the date guard.
                self.assertFalse("invalid" in state["one_time_manual_extra_ids"])

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

    def test_known_bad_first_raw_clip_rejected_and_retry_id_is_versioned(self):
        import json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            review=Path(td)/"rejected.json"
            raw=s.empty_state()
            raw["completed_technical_shots"].append({
                "id":"scene_01_shot_01",
                "sha256":"abc123",
                "human_visual_approval":False,
            })
            review.write_text(json.dumps({"rejections":[{
                "clip_id":"scene_01_shot_01","sha256":"abc123",
                "reasons":["Inaccurate background","Unwanted onscreen text"]
            }]}))
            with patch.object(s,"VISUAL_REJECTIONS",review):
                changed=s.reconcile_visual_rejections(raw)
                self.assertTrue(changed)
                self.assertEqual(raw["completed_technical_shots"],[])
                self.assertEqual(len(raw["rejected_raw_shots"]),1)
                self.assertEqual(raw["rejected_raw_shots"][0]["visual_review"],"REJECTED")
                self.assertFalse(s.reconcile_visual_rejections(raw))
            # An already rejected clip is never mistaken for completion.

    def test_old_rejected_sha_does_not_crash_new_version_of_same_shot(self):
        with tempfile.TemporaryDirectory() as td:
            review=Path(td)/"rejected.json"
            review.write_text(json.dumps({"rejections":[
                {"clip_id":"scene_01_shot_01","sha256":"oldsha","reasons":["captions"]},
                {"clip_id":"scene_01_shot_01","sha256":"newsha","reasons":["wrong fire background"]}
            ]}))
            state=s.empty_state()
            state["completed_technical_shots"]=[{"id":"scene_01_shot_01","sha256":"newsha"}]
            with patch.object(s,"VISUAL_REJECTIONS",review):
                self.assertTrue(s.reconcile_visual_rejections(state))
                self.assertEqual(len(state["rejected_raw_shots"]),1)
                self.assertEqual(state["rejected_raw_shots"][0]["sha256"],"newsha")
                self.assertFalse(s.reconcile_visual_rejections(state))

    def test_unmatched_sha_does_not_block_daily_generation(self):
        with tempfile.TemporaryDirectory() as td:
            review=Path(td)/"rejected.json"
            review.write_text(json.dumps({"rejections":[
                {"clip_id":"scene_01_shot_01","sha256":"v1sha","reasons":["bad"]}
            ]}))
            state=s.empty_state()
            state["completed_technical_shots"]=[{"id":"scene_01_shot_01","sha256":"v2sha"}]
            with patch.object(s,"VISUAL_REJECTIONS",review):
                self.assertFalse(s.reconcile_visual_rejections(state))
            self.assertEqual(len(state["completed_technical_shots"]),1)

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
