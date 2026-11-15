"""Offline tests of real Agnes submission, no billed default, and no duplicates."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pilot import e01_agnes_production as production
from pilot import e01_agnes_assemble as assembly


class TestAgnesZeroCostAndResume(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.out = self.root / "media"
        self.out.mkdir()
        self.fake_plan = {"schema": "fresh", "episode": "E01", "plan_sha256": "a"*64,
                          "shots": [{"index": 1, "scene": 1, "duration_seconds": 12,
                                     "images": ["https://example.org/ember.webp"],
                                     "prompt": "Ember walks", "voice_id": "am_puck"}],
                          "target_seconds": 12}
        self.patches = [
            patch.object(production, "OUT", self.out),
            patch.object(production, "PLAN", self.out / "shot_plan.json"),
            patch.object(production, "STATE", self.out / "progress.json"),
            patch.object(production, "BILLING", self.root / "billing.json"),
            patch.object(production.script, "make_plan", return_value=self.fake_plan),
        ]
        for obj in self.patches:
            obj.start()
        (self.root / "billing.json").write_text(json.dumps({
            "key_type_verified": False,
            "owner_confirmed_default_free_trial": False,
            "owner_confirmed_no_agent_plan_or_billable_key": False,
            "owner_authorized_zero_charge_generation": False,
        }))

    def tearDown(self):
        for obj in reversed(self.patches):
            obj.stop()
        self.temp.cleanup()

    def test_prepare_creates_no_api_task_and_is_idempotent(self):
        with patch.object(production, "urlopen", side_effect=AssertionError("No API")), \
             patch.object(production, "probe", side_effect=AssertionError("No model call")):
            p1 = production.prepare()
            p2 = production.prepare()
            state = production.load(p1)
            self.assertEqual(p1, p2)
            self.assertEqual(state["requests_submitted"], 0)
            self.assertEqual(state["completed"], [])

    def test_no_free_default_verification_blocks_any_api_call(self):
        with patch.object(production, "fetch_public_get",
                          side_effect=AssertionError("Unverified key cannot generate")), \
             patch.object(production, "probe",
                          side_effect=AssertionError("Unverified key cannot generate")):
            with self.assertRaisesRegex(RuntimeError, "ACCOUNT_FREE_KEY_TYPE_NOT_VERIFIED"):
                production.check_no_charge("key")

    def test_price_change_blocks_before_any_post(self):
        (self.root / "billing.json").write_text(json.dumps({
            "key_type_verified": True, "owner_confirmed_default_free_trial": True,
            "owner_confirmed_no_agent_plan_or_billable_key": True,
            "owner_authorized_zero_charge_generation": True,
        }))
        with patch.object(production, "fetch_public_get", return_value="changed"), \
             patch.object(production, "flash_public_trial_is_zero", return_value=False), \
             patch.object(production, "probe", side_effect=AssertionError("No model GET")), \
             self.assertRaisesRegex(RuntimeError, "FREE_PROMOTION_ENDED"):
            production.check_no_charge("key")

    def test_one_post_records_uncertainty_before_provider_and_saves_accepted_id(self):
        state = production.new_state(self.fake_plan)
        def fake_response(request, timeout):
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.full_url.endswith("/v1/videos"))
            data = json.loads(request.data)
            self.assertEqual(data["model"], "agnes-video-2.5-flash")
            self.assertEqual(data["seconds"], "12")
            persisted = json.loads(production.STATE.read_text())
            self.assertEqual(persisted["pending"]["status"], "SUBMISSION_UNCERTAIN")
            self.assertEqual(persisted["requests_submitted"], 1)
            return {"video_id": "task-created-123"}
        with patch.object(production, "check_no_charge", return_value=True), \
             patch.object(production, "read_response", side_effect=fake_response) as send:
            production.request_shot(self.fake_plan["shots"][0], state, "token-only-test")
        send.assert_called_once()
        self.assertEqual(state["pending"]["video_id"], "task-created-123")
        self.assertEqual(state["requests_submitted"], 1)
        with patch.object(production, "read_response", side_effect=AssertionError("Duplicate POST")):
            with self.assertRaisesRegex(RuntimeError, "NEVER_SUBMIT_DUPLICATE"):
                production.request_shot(self.fake_plan["shots"][0], state, "token-only-test")

    def test_timeout_does_not_submit_a_second_duplicate_request(self):
        state = production.new_state(self.fake_plan)
        with patch.object(production, "check_no_charge", return_value=True), \
             patch.object(production, "read_response", side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                production.request_shot(self.fake_plan["shots"][0], state, "dummy")
        restored = production.load(self.fake_plan)
        self.assertEqual(restored["pending"]["status"], "SUBMISSION_UNCERTAIN")
        self.assertEqual(restored["requests_submitted"], 1)
        with patch.object(production, "read_response", side_effect=AssertionError("Second POST")):
            with self.assertRaisesRegex(RuntimeError, "NEVER_SUBMIT_DUPLICATE"):
                production.request_shot(self.fake_plan["shots"][0], restored, "dummy")

    def test_completed_video_requires_real_file_matching_checksum(self):
        state = production.new_state(self.fake_plan)
        prod_file = self.out / "shot_001.mp4"
        prod_file.write_bytes(b"test fixture not a real MP4")
        state["completed"] = [{
            "index": 1, "file": prod_file.name,
            "sha256": hashlib.sha256(prod_file.read_bytes()).hexdigest(),
            "seconds": 12,
        }]
        production.atomic_json(production.STATE, state)
        self.assertEqual(len(production.load(self.fake_plan)["completed"]), 1)
        prod_file.write_bytes(b"corrupted")
        with self.assertRaisesRegex(RuntimeError, "TAMPERED_RENDER_CHECKPOINT"):
            production.load(self.fake_plan)

    def test_assembly_never_runs_without_all_18_real_mp4s(self):
        with patch.object(assembly.run, "prepare", return_value=self.fake_plan), \
             patch.object(assembly.run, "load",
                          return_value=production.new_state(self.fake_plan)), \
             patch.object(assembly, "voices",
                          side_effect=AssertionError("No TTS without clips")):
            with self.assertRaisesRegex(RuntimeError, "WITHOUT_18_SHA_VERIFIED_REAL_AGNES_CLIPS"):
                assembly.assemble()


if __name__ == "__main__":
    unittest.main()
