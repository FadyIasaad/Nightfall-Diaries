"""Offline tests for evidence-only inference timing and no paid fallback."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot import e01_capacity_audit as audit

class CapacityAuditTests(unittest.TestCase):
    def test_old_pilot_fails_required_minimum(self):
        x = audit.summarize({
            "episode": "S01_the_last_little_fox_E01",
            "target_seconds": 150,
            "expected_distinct_shots": 36,
            "completed": [{"seconds": 5.04}, {"seconds": 4.97}],
        })
        self.assertEqual(x["real_shots_completed"], 2)
        self.assertFalse(x["pilot_meets_owner_minimum"])
        self.assertIsNone(x["median_observed_quota_delta_seconds"])
        self.assertFalse(x["candidate_engines_qualified"])
        self.assertFalse(x["paid_fallback_enabled"])

    def test_optional_telemetry_does_not_convert_to_an_approved_engine(self):
        x = audit.summarize({
            "completed": [
                {"seconds": 5, "gpu_telemetry": {
                    "inference_wall_seconds": 60, "quota_delta_observed_seconds": 120}},
                {"seconds": 5, "gpu_telemetry": {
                    "inference_wall_seconds": 80, "quota_delta_observed_seconds": 140}},
            ]
        })
        self.assertEqual(x["median_inference_wall_seconds"], 70)
        self.assertEqual(x["median_observed_quota_delta_seconds"], 130)
        self.assertEqual(x["quota_delta_samples"], 2)
        self.assertFalse(x["kaggle_gpu_proven_for_this_account"])
        self.assertFalse(x["completed_film_approved_by_audit"])

    def test_read_only_does_not_change_original_state(self):
        with tempfile.TemporaryDirectory() as d:
            s = Path(d) / "progress.json"
            o = Path(d) / "audit.json"
            original = '{"completed":[{"seconds":3.0}],"target_seconds":150}'
            s.write_text(original)
            with patch("sys.argv", ["capacity", "--input", str(s), "--output", str(o)]):
                self.assertEqual(audit.main(), 0)
            self.assertEqual(s.read_text(), original)
            self.assertTrue(o.is_file())
            self.assertFalse(json.loads(o.read_text())["public_publishing_enabled_by_audit"])

if __name__ == "__main__":
    unittest.main()
