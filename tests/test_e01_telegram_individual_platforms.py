"""Partially successful publishing must notify truthfully without waiting for TikTok."""
import os
import unittest
from unittest.mock import Mock, patch

from pilot import e01_telegram_notify as t


def completed_film():
    return {"completed": [{} for _ in range(36)],
            "voices": [{} for _ in range(14)],
            "technical_full_mp4": True,
            "assembled_video_sha256": "a" * 64}


def destination(verified=False, name="youtube"):
    if verified:
        return {"phase": "confirmed_public", "public_confirmed": True,
                "public_url": ("https://www.youtube.com/watch?v=example"
                               if name == "youtube" else
                               "https://www.instagram.com/reel/example")}
    return {"phase": "blocked", "public_confirmed": False}


class TestIndependentPlatformNotifications(unittest.TestCase):
    def test_partial_platform_success_sent_once_then_new_platform_only(self):
        receipts = {"destinations": {
            n: destination(n == "youtube", n) for n in t.TARGETS}}
        text_messages = []

        def send(_token, _chat, message):
            text_messages.append(message)
            return len(text_messages)

        env = {"TELEGRAM_BOT_TOKEN": "fake", "TELEGRAM_CHAT_ID": "123"}
        with patch.dict(os.environ, env, clear=True):
            first = t.notify_once(state=completed_film(), receipts=receipts,
                                  save=Mock(), sender=send)
            same = t.notify_once(state=completed_film(), receipts=receipts,
                                 save=Mock(), sender=send)
            receipts["destinations"]["instagram"] = destination(True, "instagram")
            next_one = t.notify_once(state=completed_film(), receipts=receipts,
                                     save=Mock(), sender=send)
            receipts["destinations"]["facebook"] = destination(True, "facebook")
            receipts["destinations"]["tiktok"] = destination(True, "tiktok")
            final = t.notify_once(state=completed_film(), receipts=receipts,
                                  save=Mock(), sender=send)
            again = t.notify_once(state=completed_film(), receipts=receipts,
                                  save=Mock(), sender=send)
        self.assertEqual(first["messages_sent"], 2)  # completion + YouTube
        self.assertEqual(same["messages_sent"], 0)
        self.assertEqual(next_one["messages_sent"], 1)  # Instagram only
        self.assertEqual(final["messages_sent"], 1)  # all four verified
        self.assertEqual(again["messages_sent"], 0)
        self.assertEqual(len(text_messages), 4)
        self.assertIn("YouTube", text_messages[1])
        self.assertIn("https://www.youtube.com/watch?v=example", text_messages[1])
        self.assertIn("Instagram", text_messages[2])
        self.assertIn("تأكيد نشرها على المنصات الأربع", text_messages[3])

    def test_cannot_announce_unverified_platform(self):
        data = {"destinations": {n: destination() for n in t.TARGETS}}
        with self.assertRaisesRegex(ValueError, "unconfirmed"):
            t.format_message("platform_youtube", completed_film(), data)


if __name__ == "__main__":
    unittest.main()
