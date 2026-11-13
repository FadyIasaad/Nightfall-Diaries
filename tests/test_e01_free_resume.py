"""Safety tests for ONE free HF account and resumable non-looped motion."""
import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from pilot import e01_free_resume as m


class ResumableFreeAccountTests(TestCase):
    def test_has_exactly_36_unique_parts_adding_to_150_seconds(self):
        _cast, plan = m.film.scene_plan()
        state = m.create_state(plan)
        self.assertEqual(state["expected_distinct_shots"], 36)
        self.assertEqual(state["target_seconds"], 150)
        self.assertFalse(state["technical_full_mp4"])
        self.assertFalse(state["published_anywhere"])
        self.assertFalse(state["paid_api_calls"])
        self.assertFalse(state["true_lipsync_verified"])
        self.assertEqual(m.next_unfinished(state, plan)[0]["scene_no"], 1)

    def test_logged_out_and_pro_accounts_refused(self):
        self.assertRaisesRegex(RuntimeError, "HF_TOKEN_MISSING",
                               m.account_preflight, "", hf_api_factory=MagicMock())
        for who in ({"isPro": True, "type": "user"},
                    {"isPro": None, "type": "user"},
                    {"isPro": False, "type": "org"}):
            with self.subTest(who=who):
                api = MagicMock()
                api.whoami.return_value = who
                api.get_zero_gpu_quota.return_value = SimpleNamespace(
                    base=300, remaining=300, resets_at=None, overquota_used=0)
                with self.assertRaises(RuntimeError):
                    m.account_preflight("fake-free-token",
                                        hf_api_factory=lambda **kwargs: api)

    def test_only_registered_free_quota_without_paid_overage(self):
        api = MagicMock()
        api.whoami.return_value = {"type": "user", "isPro": False}
        api.get_zero_gpu_quota.return_value = SimpleNamespace(
            base=300, remaining=245, resets_at=None, overquota_used=0)
        q = m.account_preflight("fake-token",
                                hf_api_factory=lambda **kwargs: api)
        self.assertTrue(q["within_observed_budget"])
        self.assertEqual(q["quota_base_seconds"], 300)
        api.get_zero_gpu_quota.return_value = SimpleNamespace(
            base=300, remaining=30, resets_at=None, overquota_used=0)
        self.assertFalse(m.account_preflight(
            "fake-token", hf_api_factory=lambda **kwargs: api
        )["within_observed_budget"])
        for base, paid in ((2400, 0), (300, 10)):
            with self.subTest(base=base, paid=paid):
                api.get_zero_gpu_quota.return_value = SimpleNamespace(
                    base=base, remaining=300, resets_at=None, overquota_used=paid)
                with self.assertRaises(RuntimeError):
                    m.account_preflight("fake-token",
                                        hf_api_factory=lambda **kwargs: api)

    def test_no_inference_from_pr_or_normal_main_push(self):
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request",
                                      "GITHUB_REF": "refs/heads/main",
                                      "NIGHTFALL_FREE_RESUME": "YES",
                                      "GITHUB_RUN_ATTEMPT": "1",
                                      "HF_TOKEN": "fake"}, clear=True):
            client = MagicMock()
            with self.assertRaisesRegex(RuntimeError, "authorized manual/daily"):
                m.resume_one_shot(client_factory=client)
            client.assert_not_called()

    def test_checksum_verifies_resumed_video_and_rejects_drift(self):
        _cast, plan = m.film.scene_plan()
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            with patch.object(m, "OUT", out), patch.object(m, "STATE", out / "progress.json"):
                state = m.load_state(plan)
                self.assertEqual(len(state["completed"]), 0)
                path = out / "scene_01_part_01_generated.mp4"
                path.write_bytes(b"pretend-real-video" * 1000)
                state["completed"].append({
                    "scene": 1, "part": 1, "file": path.name,
                    "sha256": m.sha256(path), "seconds": 5, "requested_seconds": 5,
                })
                m._save(state)
                self.assertEqual(len(m.load_state(plan)["completed"]), 1)
                path.write_bytes(b"changed")
                with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                    m.load_state(plan)
                self.assertFalse(state["published_anywhere"])

    def test_one_manual_run_invokes_only_one_new_provider_request(self):
        _cast, plan = m.film.scene_plan()
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            client = MagicMock()
            client.view_api.return_value = {
                "named_endpoints": {"/run": {"parameters": [None] * 10}}
            }
            def fake_shot(client_obj, scene, number, seconds, image):
                path = out / "scene_01_part_01_generated.mp4"
                path.write_bytes(b"fresh-mp4" * 3000)
                return path, 5.05
            quota = {"quota_base_seconds": 300, "quota_remaining_seconds": 300,
                     "quota_resets_at": None, "within_observed_budget": True}
            env = {"GITHUB_EVENT_NAME": "workflow_dispatch",
                   "GITHUB_REF": "refs/heads/main", "NIGHTFALL_FREE_RESUME": "YES",
                   "GITHUB_RUN_ATTEMPT": "1", "HF_TOKEN": "safe-fake-token"}
            with patch.dict(os.environ, env, clear=True):
                with patch.object(m, "OUT", out), patch.object(m, "STATE", out / "progress.json"):
                    with patch.object(m.film, "OUT", out):
                        with patch.object(m, "account_preflight", return_value=quota):
                            with patch.object(m.film, "generate_shot", side_effect=fake_shot) as gen:
                                info = m.resume_one_shot(client_factory=lambda *a, **kw: client)
                                gen.assert_called_once()
                                self.assertEqual(info["shots_completed"], 1)
                                self.assertLess(info["real_motion_seconds"], 10)
                                self.assertFalse(info["automatic_publishing"])
                                self.assertFalse(info["paid_api_calls"])

    def test_github_workflow_starts_manual_and_daily_only_if_opted_in(self):
        wf = (m.ROOT / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("Resume E01 one free HF shot", wf)
        self.assertIn("Assemble E01 from 36 real shots (no publish)", wf)
        self.assertIn("NIGHTFALL_E01_RESUME_ENABLED == 'true'", wf)
        self.assertIn("secrets.HF_TOKEN", wf)
        self.assertIn("nightfall-e01-cumulative-real-shots", wf)
        self.assertIn("actions/cache/restore@v4", wf)
        self.assertIn("actions/cache/save@v4", wf)
        self.assertNotIn("NIGHTFALL_LIVE: true", wf)

    def test_cannot_assemble_incomplete_real_video(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            with patch.dict(os.environ, {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_REF": "refs/heads/main",
                "NIGHTFALL_FREE_ASSEMBLE": "YES",
            }):
                with patch.object(m, "OUT", out), patch.object(m, "STATE", out / "progress.json"):
                    with self.assertRaisesRegex(RuntimeError, "all 36 real motion clips"):
                        m.assemble_unapproved()
                self.assertFalse((out / "S01_the_last_little_fox_E01_full_unapproved.mp4").exists())

    def test_concat_playlist_uses_real_linefeeds(self):
        source = (m.ROOT / "pilot/e01_full_run.py").read_text()
        self.assertNotIn(r"\\n", source)
        source2 = (m.ROOT / "pilot/e01_free_resume.py").read_text()
        self.assertNotIn(r"\\n", source2)

