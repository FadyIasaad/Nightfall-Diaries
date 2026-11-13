"""Regression tests for the real one-click E01 scheduled liveness contract."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from pilot import e01_free_resume as resume
from pilot import e01_progress_health as monitor


class CairoLivenessTests(unittest.TestCase):
    def test_two_daily_cron_slots_but_not_two_hf_calls(self):
        wf = (resume.ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        self.assertIn("cron: '7 10 * * *'", wf)
        self.assertIn("cron: '27 10 * * *'", wf)
        self.assertIn("timezone: 'Africa/Cairo'", wf)
        self.assertIn("python -m pilot.e01_progress_health", wf)
        self.assertIn("python -m pilot.e01_daily_telegram_status", wf)
        self.assertNotIn("  schedule:\\n", (resume.ROOT / ".github/workflows/nightfall.yml").read_text())
        self.assertIn("nightfall-e01-cumulative-real-shots", wf)
        self.assertIn("python -m pilot.e01_free_resume --mode assemble", wf)

    def test_backup_cron_does_not_spend_extra_hf_gpu_same_day(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            quota = {
                "quota_base_seconds": 300,
                "quota_remaining_seconds": 19,
                "quota_resets_at": "tomorrow",
                "within_observed_budget": False,
            }
            env = {
                "GITHUB_EVENT_NAME": "schedule",
                "GITHUB_REF": "refs/heads/main",
                "NIGHTFALL_FREE_DAILY_ENABLED": "YES",
                "NIGHTFALL_FREE_RESUME": "YES",
                "GITHUB_RUN_ATTEMPT": "1",
                "HF_TOKEN": "fake-no-paid-hf",
            }
            with patch.dict(os.environ, env, clear=True):
                with patch.object(resume, "OUT", out), patch.object(
                    resume, "STATE", out / "progress.json"):
                    with patch.object(resume, "cairo_run_day",
                                      return_value="2026-11-13") as day:
                        with patch.object(resume, "account_preflight",
                                          return_value=quota) as preflight:
                            first = resume.resume_one_shot(
                                client_factory=MagicMock(side_effect=AssertionError("no GPU")))
                            second = resume.resume_one_shot(
                                client_factory=MagicMock(side_effect=AssertionError("backup GPU")))
                            self.assertEqual(preflight.call_count, 1)
                            self.assertEqual(first["shots_completed"], 0)
                            self.assertEqual(second["shots_completed"], 0)
                            self.assertEqual(first["state"], "PAUSED_FREE_QUOTA_INSUFFICIENT")
                            self.assertEqual(second["state"], "PAUSED_FREE_QUOTA_INSUFFICIENT")
                    with patch.object(resume, "cairo_run_day",
                                      return_value="2026-11-14"):
                        with patch.object(resume, "account_preflight",
                                          return_value=quota) as preflight:
                            third = resume.resume_one_shot(
                                client_factory=MagicMock(side_effect=AssertionError("no GPU")))
                            self.assertEqual(preflight.call_count, 1)
                            self.assertEqual(third["shots_completed"], 0)

    def test_health_distinguishes_quota_wait_from_auth_failure(self):
        _, plan = resume.film.scene_plan()
        state = resume.create_state(plan)
        state["completed"] = [{"scene": 1, "part": 1, "seconds": 5.04}]
        state["status"] = "PAUSED_FREE_QUOTA_INSUFFICIENT"
        with tempfile.TemporaryDirectory() as t:
            with patch.object(monitor.resume, "load_state", return_value=state):
                report = monitor.health()
            self.assertEqual(report["shots_completed"], 1)
            self.assertEqual(report["genuine_video_seconds"], 5.04)
            self.assertEqual(report["next_real_motion"]["part"], 2)
            with patch("sys.argv", ["progress_health", "--output", str(Path(t) / "report.json")]):
                with patch.object(monitor, "health", return_value=report):
                    self.assertEqual(monitor.main(), 0)
                report["last_execution_state"] = "BLOCKED_FREE_PROVIDER_OR_AUTH"
                with patch.object(monitor, "health", return_value=report):
                    self.assertEqual(monitor.main(), 1)

    def test_complete_36_saved_shots_never_trigger_new_paid_or_free_inference(self):
        _, plan = resume.film.scene_plan()
        state = resume.create_state(plan)
        state["completed"] = [
            {"scene": scene["scene_no"], "part": part, "seconds": secs}
            for scene in plan["scenes"]
            for part, secs in enumerate(scene["subshot_seconds"], 1)
        ]
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main",
            "NIGHTFALL_FREE_RESUME": "YES", "NIGHTFALL_FREE_DAILY_ENABLED": "YES",
            "GITHUB_RUN_ATTEMPT": "1", "HF_TOKEN": "fake",
        }, clear=True):
            with patch.object(resume, "load_state", return_value=state):
                with patch.object(resume, "_save"):
                    with patch.object(resume, "account_preflight") as quota:
                        result = resume.resume_one_shot()
            quota.assert_not_called()
            self.assertEqual(result["shots_completed"], 36)
            self.assertIsNone(result["next"])


if __name__ == "__main__":
    unittest.main()
