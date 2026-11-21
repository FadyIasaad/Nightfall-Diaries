"""Telegram progress tests: cannot report unrendered E01 as published."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pilot import e01_studio_telegram as t


class TelegramStudioTests(unittest.TestCase):
    def test_real_clip_message_does_not_claim_final_or_public_video(self):
        s={"status":"AUTO_SHORTLISTED_TECHNICAL_MOTION_NOT_SEMANTICALLY_APPROVED",
           "completed_technical_shots":[{"id":"scene_01_shot_01",
              "automatic_quality":{"score_0_to_100":71}}],
           "automatic_best_candidates":{"scene_01_shot_01":{"score":71}}}
        m=t.message_for("result",s,"12345")
        self.assertIn("1 من 45",m)
        self.assertIn("71/100",m)
        self.assertIn("لا نشر عام",m)
        self.assertIn("https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/12345",m)

    def test_real_quota_blocker_is_not_success(self):
        s={"status":"BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY"}
        m=t.message_for("result",s,"12345")
        self.assertIn("رفض المحرك المجاني",m)
        self.assertIn("0 من 45",m)

    def test_without_secret_result_is_explicit_and_safe(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(t,"OUTPUT",Path(td)/"receipt.json"), \
             patch.dict(os.environ,{"GITHUB_EVENT_NAME":"push",
                   "GITHUB_REF":"refs/heads/main","GITHUB_RUN_ATTEMPT":"1"},
                   clear=True):
            with patch("builtins.print"):
                r=t.send("result",{"status":"BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY"})
            self.assertEqual(r["status"],"TELEGRAM_SECRETS_NOT_CONFIGURED")
            self.assertFalse(r["delivered"])
            self.assertEqual(len(r["missing_secret_names"]),2)
            self.assertEqual(json.loads(t.OUTPUT.read_text())["status"],r["status"])

    def test_pull_request_never_sends_telegram(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(t,"OUTPUT",Path(td)/"receipt.json"), \
             patch.dict(os.environ,{"GITHUB_EVENT_NAME":"pull_request",
                   "GITHUB_REF":"refs/pull/88/merge","TELEGRAM_BOT_TOKEN":"mock",
                   "TELEGRAM_CHAT_ID":"mock"},clear=True):
            with patch("builtins.print"):
                r=t.send("start")
            self.assertEqual(r["status"],"NOT_MAIN_PRODUCTION_EVENT")
            self.assertFalse(r["delivered"])
