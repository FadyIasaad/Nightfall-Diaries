"""Safety checks for the owner's 2026-11-06 GPU blocker and new Series #3 proposal."""
import json
import unittest
from studio.restore import ROOT,validate_stories

class GpuBlockerAndProposalTests(unittest.TestCase):
    def test_kaggle_is_not_assumed_usable(self):
        status=json.loads((ROOT/"docs/gpu_access_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["gpu_gate"],"BLOCKED_ACCESS")
        self.assertFalse(status["providers"]["kaggle_p100"]["available"])
        self.assertFalse(status["providers"]["kaggle_t4x2"]["available"])
        self.assertIsNone(status["selected_gpu_provider"])
        self.assertFalse(status["enable_paid_fallback"])

    def test_series_three_remains_unapproved_and_has_no_assigned_voices(self):
        status=json.loads((ROOT/"docs/gpu_access_status.json").read_text(encoding="utf-8"))
        proposal=status["series3"]
        self.assertEqual(proposal["episode_count"],30)
        self.assertFalse(proposal["voice_ids_assigned"])
        self.assertFalse(proposal["screenplays_in_active_queue"])
        self.assertIn("PENDING",proposal["status"])
        source=(ROOT/"proposals/the-interpreters-debt/SERIES_BIBLE_DRAFT.md").read_text(encoding="utf-8")
        self.assertIn("Three Words",source)
        self.assertIn("What Is Owed",source)
        self.assertIn("Nour Haddad",source)
        self.assertIn("G3-E",source)

    def test_original_two_series_only_and_flags_still_closed(self):
        self.assertEqual(validate_stories(),22)
        status=json.loads((ROOT/"docs/gpu_access_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["active_original_series"],["S01_the_last_little_fox","S02_the_boy_who_forgot_tomorrow"])
        flags=json.loads((ROOT/"studio/production_settings.json").read_text(encoding="utf-8"))
        self.assertFalse(flags["production_enabled"])
        self.assertFalse(flags["automatic_new_series"])
        self.assertFalse(flags["publishing_implemented"])
        self.assertFalse(json.loads((ROOT/"config.json").read_text(encoding="utf-8"))["public_publish_enabled"])
