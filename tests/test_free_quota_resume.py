"""No-cost regression checks: the free quota pause must be resumable, not a fake success."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

from studio.free_video import QuotaExhausted, quota_retry_seconds
from studio.pending import enqueue, load, next_due, set_status, write_report


class FreeQuotaTests(unittest.TestCase):
    def test_real_provider_retry_window_is_understood(self):
        seconds=quota_retry_seconds("You have exceeded your ZeroGPU quota (126s requested vs. 90s left). Try again in 23:58:25.")
        self.assertGreaterEqual(seconds,86400)
        self.assertLessEqual(seconds,87000)

    def test_unstructured_quota_error_waits_a_day(self):
        self.assertEqual(quota_retry_seconds("quota exhausted"),86400)
        exc=QuotaExhausted("quota",retry_seconds=86400)
        self.assertEqual(exc.retry_seconds,86400)

    def test_pending_specific_episode_and_safe_automatic_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"episode_queue.json"
            ep="S01_the_last_little_fox_E02"
            enqueue(ep,"full",path)
            self.assertEqual(next_due(path)["episode_id"],ep)
            state=set_status(ep,"full","PAUSED_FREE_QUOTA",retry_seconds=86400,
                             details="126 requested, 90 left",path=path)
            self.assertIsNone(next_due(path))
            after=datetime.fromisoformat(state["retry_after_utc"])+timedelta(seconds=1)
            self.assertEqual(next_due(path,at=after)["episode_id"],ep)
            self.assertFalse(any(x["status"]=="RENDERED_NOT_VISUALLY_APPROVED"
                                 for x in load(path)["episodes"]))

    def test_multiple_real_episodes_queue_without_character_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"episode_queue.json"
            a="S01_the_last_little_fox_E01"
            b="S01_the_last_little_fox_E02"
            enqueue(a,"proof",path)
            enqueue(b,"full",path)
            enqueue(b,"full",path)
            self.assertEqual(len(load(path)["episodes"]),2)
            with self.assertRaises(ValueError):
                enqueue("S03_unapproved_E01","full",path)
            with self.assertRaises(ValueError):
                enqueue("S01_the_last_little_fox_E13","full",path)
            set_status(a,"proof","RENDERED_NOT_VISUALLY_APPROVED",path=path)
            self.assertEqual(next_due(path)["episode_id"],b)

    def test_status_report_explicitly_denies_public_posting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"report.json"
            # This is a fixture, NOT a real E02 production run. Never write
            # a fake quota-pause status into the real GitHub job summary.
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": ""}):
                report=write_report("S01_the_last_little_fox_E02","full",
                                    "PAUSED_FREE_QUOTA","waiting",path=path)
            self.assertFalse(report["completed_full_episode"])
            self.assertFalse(report["publicly_published"])
            self.assertTrue(path.is_file())

    def test_actions_schedules_resume_only_with_valid_queue(self):
        from studio.restore import ROOT
        wf=(ROOT/".github/workflows/nightfall.yml").read_text(encoding="utf-8")
        self.assertIn("id: pending_scan",wf)
        self.assertIn("python -m studio.pending --detect",wf)
        self.assertIn("steps.pending_scan.outputs.has_pending == 'true'",wf)
        self.assertIn("python -m studio.run_free --action resume_pending",wf)
        self.assertIn("nightfall-render-status",wf)
        self.assertIn("output/checkpoints/episode_queue.json",wf)
        self.assertIn("NIGHTFALL_LIVE",wf)
