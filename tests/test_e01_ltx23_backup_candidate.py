"""Never mix automatic paid fallbacks into the zero-budget Fox episode."""
import unittest
from unittest.mock import patch

from pilot import e01_ltx23_backup_candidate as backup


class LTX23BackupCandidateTests(unittest.TestCase):
    def test_explicit_unadmitted_agnes_queue_fallback_is_still_cost_blocked(self):
        old = {"status": "PAUSED_AGNES_QUEUE_FULL_NOT_ADMITTED", "completed": [], "pending": None}
        self.assertEqual(backup.decide(old),
                         "BACKUP_EVERYPIXEL_CLIENT_ID_AND_SECRET_NOT_CONNECTED")
        self.assertEqual(backup.decide(old, credentials_present=True),
                         "NO_VERIFIED_UNUSED_TRIAL_SECONDS")
        self.assertEqual(backup.decide(old, credentials_present=True,
                                       trial_seconds_confirmed=5),
                         "NO_PROVIDER_ENFORCED_ZERO_SPEND_CAP_NO_POST")
        self.assertEqual(backup.decide(old, credentials_present=True,
                                       trial_seconds_confirmed=5,
                                       hard_zero_spend_enforced=True),
                         "BACKUP_QUALITY_NOT_APPROVED")

    def test_ambiguous_submission_prevents_other_provider_post(self):
        old = {"status": "SUBMISSION_UNCERTAIN_DO_NOT_AUTORETRY",
               "completed": [], "pending": {"index": 1, "video_id": None}}
        with patch.object(backup, "make_plan", side_effect=AssertionError("no live generation")):
            decision = backup.decide(old, credentials_present=True,
                                     trial_seconds_confirmed=10,
                                     hard_zero_spend_enforced=True,
                                     owner_reviewed_quality=True)
        self.assertEqual(decision,
                         "BLOCKED_AGNES_TASK_PENDING_OR_AMBIGUOUS_DO_NOT_DUPLICATE")

    def test_no_fallback_on_ordinary_agnes_retryable_timeout(self):
        old = {"status": "PROVIDER_TASK_FAILED_REVIEW_REQUIRED",
               "completed": [], "pending": None}
        self.assertEqual(backup.decide(old, credentials_present=True,
                                       trial_seconds_confirmed=10,
                                       hard_zero_spend_enforced=True,
                                       owner_reviewed_quality=True),
                         "NO_OFFICIALLY_UNADMITTED_AGNES_TASK")

    def test_preview_is_5_seconds_real_image_to_video_without_post(self):
        old = {"status": "PAUSED_AGNES_QUEUE_FULL_NOT_ADMITTED",
               "completed": [], "pending": None}
        with patch("pilot.e01_ltx23_backup_candidate.os.environ", {}, create=True):
            doc = backup.preview(old)
        request = doc["request_preview"]
        self.assertEqual(request["model"], "ltx23")
        self.assertEqual(request["duration"], 5)
        self.assertEqual(request["resolution"], "720p")
        self.assertEqual(request["aspect_ratio"], "9:16")
        self.assertTrue(request["image_url"].startswith(
            "https://raw.githubusercontent.com/FadyIasaad/Nightfall-Diaries/"))
        self.assertTrue(request["image_url"].endswith(".webp"))
        self.assertFalse(doc["quality_verified"])
        self.assertFalse(doc["provider_enforced_zero_spend_limit_verified"])
        self.assertEqual(doc["provider_requests_sent"], 0)

    def test_no_paid_credits_ever_automatically(self):
        old = {"status": "PAUSED_AGNES_QUEUE_FULL_COOLDOWN",
               "completed": [], "pending": None}
        self.assertNotEqual(backup.decide(old, credentials_present=True,
                                          trial_seconds_confirmed=5,
                                          hard_zero_spend_enforced=False,
                                          owner_reviewed_quality=True),
                            "ELIGIBLE_FOR_SEPARATELY_AUDITED_API_INTEGRATION_NOT_AUTOMATIC_POST")


if __name__ == "__main__":
    unittest.main()
