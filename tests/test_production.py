import json
import unittest
from studio.production import next_episode, readiness, report
from studio.restore import ROOT

class ProductionSafetyTests(unittest.TestCase):
    def test_next_episode_starts_with_original_fox(self):
        self.assertEqual(next_episode(ROOT), "S01_the_last_little_fox_E01")

    def test_all_unverified_gates_block_release(self):
        checks = readiness(environ={}, root=ROOT)
        self.assertFalse(all(checks.values()))
        self.assertFalse(checks["production_enabled"])
        self.assertFalse(checks["publishing_integration_implemented"])

    def test_schedule_fails_closed_without_fake_success(self):
        result = report("scheduled", root=ROOT, environ={})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["rendered_video"])
        self.assertFalse(result["uploaded_to_any_platform"])
        self.assertEqual(result["scheduled_time"], "10:00 Africa/Cairo")

    def test_settings_no_unapproved_series(self):
        data = json.loads((ROOT / "studio/production_settings.json").read_text())
        self.assertFalse(data["automatic_new_series"])
