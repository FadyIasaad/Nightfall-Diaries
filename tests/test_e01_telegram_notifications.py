"""Never announce four public Nightfall posts unless all FOUR really confirmed."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from pilot import e01_telegram_notify as telegram
from pilot import e01_verify_platforms as verify
from studio.restore import ROOT


def full_state():
    return {
        "completed": [{} for _ in range(36)],
        "voices": [{} for _ in range(14)],
        "assembled_video_sha256": "a" * 64,
        "technical_full_mp4": True,
    }


def receipts(public_names=()):
    return {"destinations": {
        name: ({
            "phase": "confirmed_public", "public_confirmed": True,
            "public_url": "https://www.youtube.com/watch?v=abc"
            if name == "youtube" else "https://www.instagram.com/reel/xyz"
        } if name in public_names else {
            "phase": "accepted", "id": name + "-id", "public_confirmed": False
        }) for name in telegram.TARGETS
    }}


class TelegramCompletionTests(unittest.TestCase):
    def test_missing_secrets_does_not_send_or_require_approval(self):
        with patch.dict(os.environ, {}, clear=True):
            sender = MagicMock()
            result = telegram.notify_once(
                state=full_state(), receipts=receipts(), sender=sender,
                save=MagicMock())
        self.assertEqual(result["status"], "TELEGRAM_SETUP_REQUIRED")
        self.assertEqual(result["messages_sent"], 0)
        self.assertIn("TELEGRAM_BOT_TOKEN", result["missing_secret_names"])
        sender.assert_not_called()

    def test_cannot_claim_completion_before_actual_36_motion_clips(self):
        state = full_state()
        state["completed"].pop()
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "123"
        }, clear=True):
            send = MagicMock()
            result = telegram.notify_once(
                state=state, receipts=receipts(), save=MagicMock(), sender=send)
        self.assertEqual(result["status"], "WAITING_FOR_FULL_EPISODE")
        send.assert_not_called()

    def test_completion_alert_does_not_claim_any_unverified_platform(self):
        delivered = []
        report = receipts()
        def sender(token, chat_id, body):
            delivered.append(body)
            return 345
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "123"
        }, clear=True):
            saved = MagicMock()
            first = telegram.notify_once(state=full_state(), receipts=report,
                                         sender=sender, save=saved)
            again = telegram.notify_once(state=full_state(), receipts=report,
                                         sender=sender, save=saved)
        self.assertEqual(first["messages_sent"], 1)
        self.assertEqual(again["messages_sent"], 0)
        self.assertEqual(len(delivered), 1)
        self.assertIn("اكتمل تجميع", delivered[0])
        self.assertIn("تم قبول الرفع، بانتظار التأكيد", delivered[0])
        self.assertNotIn("تأكيد نشرها على المنصات الأربع", delivered[0])
        self.assertEqual(report["telegram_notifications"]["film_complete"]["phase"], "sent")
        self.assertGreaterEqual(saved.call_count, 2)

    def test_four_public_posts_send_final_success_exactly_once(self):
        published = receipts(telegram.TARGETS)
        sent = []
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "123"
        }, clear=True):
            fn = lambda *args: (sent.append(args[-1]) or len(sent))
            result = telegram.notify_once(state=full_state(), receipts=published,
                                          sender=fn, save=MagicMock())
            repeated = telegram.notify_once(state=full_state(), receipts=published,
                                            sender=fn, save=MagicMock())
        self.assertEqual(result["messages_sent"], 2)
        self.assertEqual(repeated["messages_sent"], 0)
        self.assertEqual(len(sent), 2)
        self.assertIn("تأكيد نشرها على المنصات الأربع", sent[1])
        self.assertTrue(all(name in sent[1] for name in
                            ("YouTube", "Facebook", "Instagram", "TikTok")))

    def test_three_public_posts_can_not_trigger_four_platform_success(self):
        three = receipts(telegram.TARGETS[:3])
        with self.assertRaisesRegex(ValueError, "four public"):
            telegram.format_message("all_public", full_state(), three)

    def test_ambiguous_bot_send_is_not_retried_to_avoid_duplicate_alert(self):
        rec = receipts()
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "123"
        }, clear=True):
            sender = MagicMock(side_effect=RuntimeError("network uncertain"))
            result = telegram.notify_once(state=full_state(), receipts=rec,
                                          sender=sender, save=MagicMock())
            again = telegram.notify_once(state=full_state(), receipts=rec,
                                         sender=sender, save=MagicMock())
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(result["messages_sent"], 0)
        self.assertEqual(again["messages_sent"], 0)
        self.assertEqual(rec["telegram_notifications"]["film_complete"]["phase"],
                         "uncertain")

    def test_official_telegram_api_is_used_with_private_chat_id(self):
        fake = MagicMock()
        fake.post.return_value.json.return_value = {
            "ok": True, "result": {"message_id": 18}}
        got = telegram._send_message("not-a-real-token", "123", "abc", session=fake)
        self.assertEqual(got, 18)
        args, kwargs = fake.post.call_args
        self.assertTrue(args[0].startswith("https://api.telegram.org/bot"))
        self.assertEqual(kwargs["json"]["chat_id"], "123")


class OfficialPublicVerificationTests(unittest.TestCase):
    def test_tiktok_moderation_must_return_publicly_available_post_id(self):
        session = MagicMock()
        entry = {"phase": "accepted", "id": "publish-id"}
        session.post.return_value.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "PROCESSING_UPLOAD", "publicaly_available_post_id": []},
        }
        with patch.dict(os.environ, {"TIKTOK_ACCESS_TOKEN": "fake"}):
            self.assertIsNone(verify.tiktok_public(entry, session))
            session.post.return_value.json.return_value = {
                "error": {"code": "ok"},
                "data": {"status": "PUBLISH_COMPLETE",
                         "publicaly_available_post_id": [123456789]},
            }
            result = verify.tiktok_public(entry, session)
        self.assertEqual(result["public_post_id"], "123456789")

    def test_unconfirmed_or_missing_ids_cannot_turn_green(self):
        data = receipts()
        fake = MagicMock()
        with patch.object(verify, "CHECKS", {
            name: (lambda entry, sess: None) for name in telegram.TARGETS
        }):
            statuses, changed = verify.reconcile_once(receipts=data, session=fake)
        self.assertFalse(changed)
        self.assertEqual(
            set(statuses.values()), {"NOT_CONFIRMED_PUBLIC_YET"})
        self.assertFalse(telegram._all_public(data))

    def test_confirmed_public_statuses_are_persisted_and_enable_alert(self):
        data = receipts()
        with patch.object(verify, "CHECKS", {
            name: (lambda entry, sess: {"public_url": "https://trusted.example/watch"})
            for name in telegram.TARGETS
        }):
            save = MagicMock()
            result = verify.poll_public_status(
                receipts=data, writer=save, max_seconds=0, session=MagicMock())
        self.assertTrue(result["all_four_confirmed_public"])
        self.assertEqual(set(result["public_confirmed"]), set(telegram.TARGETS))
        save.assert_called_once()
        self.assertTrue(telegram._all_public(data))

    def test_no_upload_status_does_not_sleep_for_two_minutes(self):
        data = {"destinations": {n: {"phase": "blocked"} for n in telegram.TARGETS}}
        sleep = MagicMock()
        result = verify.poll_public_status(receipts=data, writer=MagicMock(),
                                           session=MagicMock(), sleeper=sleep,
                                           max_seconds=180)
        self.assertFalse(result["all_four_confirmed_public"])
        sleep.assert_not_called()

    def test_telegram_step_after_official_checks_in_same_one_click_job(self):
        workflow = (ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        pos_publish = workflow.index("python -m pilot.e01_completion_publish")
        pos_verify = workflow.index("python -m pilot.e01_verify_platforms")
        pos_telegram = workflow.index("python -m pilot.e01_telegram_notify --mode completion")
        self.assertLess(pos_publish, pos_verify)
        self.assertLess(pos_verify, pos_telegram)
        self.assertIn("secrets.TELEGRAM_BOT_TOKEN", workflow)
        self.assertIn("secrets.TELEGRAM_CHAT_ID", workflow)
        self.assertNotIn("Stage a fully assembled E01 as YouTube PRIVATE", workflow)
        intent = __import__("json").loads(
            (ROOT / "pilot/owner_release_intent.json").read_text())
        self.assertTrue(intent["owner_auto_public_release_authorized"])
        self.assertFalse(intent["owner_approval_per_episode_required"])
        settings = __import__("json").loads(
            (ROOT / "studio/production_settings.json").read_text())
        self.assertFalse(settings["voice_lipsync_verified"])
        self.assertFalse(settings["cinematic_video_approved"])


if __name__ == "__main__":
    unittest.main()
