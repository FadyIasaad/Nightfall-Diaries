"""Real per-shot Telegram progress from genuine new LTX motion only."""
import copy
import os
import unittest
from unittest.mock import Mock, patch

from pilot import e01_telegram_notify as telegram
from studio.restore import ROOT


def clip_state(*, shot_count=3, run="900001"):
    completed = []
    for idx in range(shot_count):
        completed.append({
            "scene": 1 + idx // 3, "part": 1 + idx % 3,
            "sha256": format(idx + 1, "064x"),
            "seconds": 5.04,
        })
    return {
        "episode": telegram.EPISODE,
        "status": "PARTIAL_REAL_MOTION_UNAPPROVED",
        "completed": completed,
        "last_real_motion_run_id": run,
    }


def env(run="900001"):
    return {
        "GITHUB_RUN_ID": run, "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_CHAT_ID": "123456",
    }


class ShotProgressNotifications(unittest.TestCase):
    def test_real_shot_sends_one_message_immediately(self):
        state = clip_state()
        ledger = {}
        saved = []
        sends = []
        def save(doc):
            saved.append(copy.deepcopy(doc))
        def send(token, chat, body):
            sends.append(body)
            self.assertEqual(saved[-1]["telegram_notifications"]["real_shots"]
                             ["scene_01_part_03"]["phase"], "initiated")
            self.assertIn("3 من 36", body)
            self.assertIn("15.12", body)
            self.assertIn("المشهد 1", body)
            self.assertIn("الجزء 3", body)
            self.assertNotIn("تم تأكيد نشرها على المنصات الأربع", body)
            return 345
        with patch.dict(os.environ, env(), clear=True):
            first = telegram.notify_progress_once(state=state, receipts=ledger,
                                                   save=save, sender=send)
            second = telegram.notify_progress_once(state=state, receipts=ledger,
                                                    save=save, sender=send)
        self.assertEqual(first["status"], "REAL_MOTION_SHOT_NOTIFICATION_SENT")
        self.assertEqual(first["messages_sent"], 1)
        self.assertEqual(second["status"], "ALREADY_REPORTED_NO_DUPLICATE")
        self.assertEqual(len(sends), 1)
        self.assertEqual(ledger["telegram_notifications"]["real_shots"]
                         ["scene_01_part_03"]["phase"], "sent")

    def test_restored_old_clip_does_not_spam_new_run(self):
        state = clip_state(run="previous-run")
        with patch.dict(os.environ, env(run="new-run"), clear=True):
            sender = Mock(side_effect=AssertionError("stale cache"))
            writer = Mock(side_effect=AssertionError("stale cache"))
            actual = telegram.notify_progress_once(state=state, receipts={},
                                                   save=writer, sender=sender)
        self.assertEqual(actual["status"], "NO_NEW_REAL_SHOT_THIS_RUN")
        sender.assert_not_called()
        writer.assert_not_called()

    def test_no_new_clip_when_quota_exhausted(self):
        state = clip_state(run="previous-run")
        state["status"] = "PAUSED_FREE_QUOTA_INSUFFICIENT"
        with patch.dict(os.environ, env(run="today"), clear=True):
            sender = Mock()
            res = telegram.notify_progress_once(state=state, receipts={},
                                                save=Mock(), sender=sender)
        self.assertEqual(res["messages_sent"], 0)
        sender.assert_not_called()

    def test_no_secrets_is_configuration_problem_not_film_failure(self):
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "900001"}, clear=True):
            sender = Mock()
            res = telegram.notify_progress_once(state=clip_state(), receipts={},
                                                save=Mock(), sender=sender)
        self.assertEqual(res["status"], "TELEGRAM_SETUP_REQUIRED")
        self.assertEqual(set(res["missing_secret_names"]),
                         {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"})
        sender.assert_not_called()

    def test_clip_receipt_write_failed_means_no_telegram_post(self):
        with patch.dict(os.environ, env(), clear=True):
            sender = Mock()
            result = telegram.notify_progress_once(
                state=clip_state(), receipts={},
                save=Mock(side_effect=RuntimeError("GitHub unavailable")),
                sender=sender)
        self.assertTrue(result["status"].startswith("RECEIPT_SAVE_FAILED"))
        sender.assert_not_called()

    def test_unknown_telegram_result_never_retries_same_clip(self):
        with patch.dict(os.environ, env(), clear=True):
            sender = Mock(side_effect=RuntimeError("Telegram response unknown"))
            ledger = {}
            one = telegram.notify_progress_once(
                state=clip_state(), receipts=ledger, save=Mock(), sender=sender)
            two = telegram.notify_progress_once(
                state=clip_state(), receipts=ledger, save=Mock(), sender=sender)
        self.assertEqual(one["messages_attempted"], 1)
        self.assertEqual(two["status"], "ALREADY_REPORTED_NO_DUPLICATE")
        self.assertEqual(sender.call_count, 1)

    def test_final_real_clip_mentions_assembly_not_publication(self):
        state = clip_state(shot_count=36)
        with patch.dict(os.environ, env(), clear=True):
            body = telegram.format_shot_message(state)
        self.assertIn("36 من 36", body)
        self.assertIn("جار تجميع الأصوات", body)
        self.assertIn("ليست حلقة منشورة بعد", body)

    def test_finishing_message_includes_only_independently_public_links(self):
        receipts = {"destinations": {
            "youtube": {"phase": "confirmed_public", "public_confirmed": True,
                        "public_url": "https://www.youtube.com/watch?v=abc"},
            "facebook": {"phase": "accepted", "public_confirmed": False},
            "instagram": {"phase": "blocked", "public_confirmed": False,
                          "public_url": "https://www.instagram.com/reel/INVALID"},
            "tiktok": {"phase": "ambiguous", "public_confirmed": False},
        }}
        body = telegram.format_message("film_complete", {}, receipts)
        self.assertIn("✅ YouTube", body)
        self.assertIn("https://www.youtube.com/watch?v=abc", body)
        self.assertIn("⏳ Facebook", body)
        self.assertIn("⚠️ TikTok", body)
        self.assertNotIn("https://www.instagram.com/reel/INVALID", body)

    def test_workflow_sends_shot_notice_after_gpu_before_assembly(self):
        content = (ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        a = content.index("python -m pilot.e01_continuous_free")
        b = content.index("python -m pilot.e01_telegram_notify --mode progress")
        c = content.index("python -m pilot.e01_free_resume --mode assembly-gate")
        d = content.index("python -m pilot.e01_telegram_notify --mode completion")
        self.assertLess(a, b)
        self.assertLess(b, c)
        self.assertLess(c, d)
        self.assertIn("TELEGRAM_BOT_TOKEN", content)
        self.assertIn("TELEGRAM_CHAT_ID", content)


if __name__ == "__main__":
    unittest.main()
