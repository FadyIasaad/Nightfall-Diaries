"""No-spam daily Cairo Telegram health and single owner-facing production schedule."""
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from pilot import e01_daily_telegram_status as daily
from pilot import e01_telegram_notify as clips
from studio.restore import ROOT


def state(*, status="PAUSED_FREE_QUOTA_INSUFFICIENT", run="previous"):
    return {
        "status": status,
        "last_real_motion_run_id": run,
        "completed": [
            {"scene": 1, "part": 1, "seconds": 5.04},
            {"scene": 1, "part": 2, "seconds": 5.04},
        ],
    }


def env(event="schedule"):
    return {"GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": event,
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": "123456",
            "TELEGRAM_BOT_TOKEN": "safe-test-token",
            "TELEGRAM_CHAT_ID": "123"}


class DailyTelegramTests(unittest.TestCase):
    def test_daily_status_reports_real_saved_count_and_does_not_claim_public(self):
        message = daily.status_text(state(), date="2026-11-13")
        self.assertIn("2 من 36", message)
        self.assertIn("10.08", message)
        self.assertIn("حصة توليد الفيديو المجانية", message)
        self.assertIn("لم يتم إثبات نشر", message)

    def test_one_per_day_even_with_two_scheduled_slots(self):
        receipts = {}
        saved = []
        send = Mock(return_value=41)
        with patch.dict(os.environ, env(), clear=True):
            first = daily.report_once(state=state(), receipts=receipts,
                                      save=lambda r: saved.append(r.copy()),
                                      sender=send, date="2026-11-13")
            repeated = daily.report_once(state=state(), receipts=receipts,
                                         save=Mock(), sender=send, date="2026-11-13")
        self.assertEqual(first["status"], "DAILY_HEALTH_NOTICE_SENT")
        self.assertEqual(repeated["status"], "ALREADY_SENT_FOR_CAIRO_DAY")
        self.assertEqual(send.call_count, 1)
        self.assertEqual(len(saved), 2)

    def test_next_cairo_day_can_report_again(self):
        receipts = {}
        send = Mock(side_effect=[17, 18])
        with patch.dict(os.environ, env(), clear=True):
            self.assertEqual(daily.report_once(
                state=state(), receipts=receipts, save=Mock(), sender=send,
                date="2026-11-13")["messages_sent"], 1)
            self.assertEqual(daily.report_once(
                state=state(), receipts=receipts, save=Mock(), sender=send,
                date="2026-11-14")["messages_sent"], 1)
        self.assertEqual(send.call_count, 2)

    def test_real_shot_alert_suppresses_heartbeat(self):
        receipts = {"telegram_notifications": {
            "real_shots": {"scene_01_part_02": {"phase": "sent"}}}}
        send = Mock()
        with patch.dict(os.environ, env(), clear=True):
            result = daily.report_once(state=state(run="123456"), receipts=receipts,
                                       save=Mock(), sender=send,
                                       date="2026-11-13")
        self.assertEqual(result["status"], "REAL_SHOT_NOTICE_ALREADY_SENT")
        send.assert_not_called()

    def test_failed_shot_notice_still_sends_daily_fallback(self):
        receipts = {"telegram_notifications": {
            "real_shots": {"scene_01_part_02": {"phase": "uncertain"}}}}
        send = Mock(return_value=19)
        with patch.dict(os.environ, env(), clear=True):
            result = daily.report_once(state=state(run="123456"), receipts=receipts,
                                       save=Mock(), sender=send, date="2026-11-13")
        self.assertEqual(result["messages_sent"], 1)

    def test_no_manual_or_pr_notice_and_no_retry_on_ambiguous_delivery(self):
        send = Mock(side_effect=TimeoutError("unknown"))
        receipts = {}
        with patch.dict(os.environ, env(event="workflow_dispatch"), clear=True):
            result = daily.report_once(state=state(), receipts=receipts,
                                       save=Mock(), sender=send, date="2026-11-13")
        self.assertEqual(result["status"], "NOT_SCHEDULED")
        send.assert_not_called()
        with patch.dict(os.environ, env(), clear=True):
            res = daily.report_once(state=state(), receipts=receipts,
                                    save=Mock(), sender=send, date="2026-11-13")
            again = daily.report_once(state=state(), receipts=receipts,
                                      save=Mock(), sender=send, date="2026-11-13")
        self.assertEqual(res["status"], "TELEGRAM_OUTCOME_UNKNOWN_NO_AUTOMATIC_DUPLICATE")
        self.assertEqual(again["status"], "ALREADY_SENT_FOR_CAIRO_DAY")
        self.assertEqual(send.call_count, 1)

    def test_owner_now_start_gets_status_when_free_quota_prevents_new_clip(self):
        receipts = {}
        send = Mock(return_value=41)
        settings = env(event="push")
        settings["NIGHTFALL_OWNER_START_NOW"] = "YES"
        with patch.dict(os.environ, settings, clear=True):
            first = daily.report_once(state=state(), receipts=receipts,
                                      save=Mock(), sender=send, date="2026-11-13")
            again = daily.report_once(state=state(), receipts=receipts,
                                      save=Mock(), sender=send, date="2026-11-13")
        self.assertEqual(first["status"], "DAILY_HEALTH_NOTICE_SENT")
        self.assertEqual(again["status"], "ALREADY_SENT_FOR_CAIRO_DAY")
        self.assertEqual(send.call_count, 1)
        self.assertIn("owner_start_123456",
                      receipts["telegram_notifications"]["daily_health"])

    def test_remote_receipt_failure_does_not_send(self):
        send = Mock()
        with patch.dict(os.environ, env(), clear=True):
            result = daily.report_once(
                state=state(), receipts={},
                save=Mock(side_effect=RuntimeError("GitHub error")),
                sender=send, date="2026-11-13")
        self.assertIn("RECEIPT_SAVE_FAILED", result["status"])
        send.assert_not_called()

    def test_only_one_real_production_schedule_on_default_branch(self):
        new = (ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        old = (ROOT / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("  schedule:\n", new)
        self.assertNotIn("  schedule:\n", old)
        self.assertIn("cron: '7 10 * * *'", new)
        self.assertIn("cron: '27 10 * * *'", new)
        self.assertIn("python -m pilot.e01_daily_telegram_status", new)
        self.assertLess(new.index("python -m pilot.e01_telegram_notify --mode progress"),
                        new.index("python -m pilot.e01_daily_telegram_status"))
        self.assertLess(new.index("python -m pilot.e01_daily_telegram_status"),
                        new.index("python -m pilot.e01_free_resume --mode assembly-gate"))


if __name__ == "__main__":
    unittest.main()
